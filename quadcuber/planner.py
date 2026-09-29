"""动作规划器: 把求解得到的转动序列翻译成耗时最短的机械手动作序列。

做法: 在 (已完成的转动, 机器状态) 上做 A* 搜索, 代价为总耗时。
每一步是一组同时执行的动作 (见 machine.Machine.check 中的规则), 例如:
- 拧一个面, 或同时拧两个相对的面;
- 一对机械手整体翻转魔方 (把 U/D 面换到有机械手的位置);
- 一个或多个机械手松开 / 夹紧;
- 松开的机械手空转以恢复夹条方向, 可与上述任何动作同时进行。

连续的同轴转动 (例如 R L', U D2) 互相可交换, 会合并成一组, 组内可以任意顺序执行或同时执行。
"""

from __future__ import annotations

import dataclasses
import heapq
import itertools
from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Optional, Sequence, Tuple

from .cube import Move, axis_sign, format_moves, normalize_k
from .machine import (
    AXIS_PAIR,
    POSITIONS,
    Action,
    Close,
    CubeRotate,
    Gripper,
    InvalidStep,
    Machine,
    Open,
    Rotate,
    State,
    Step,
    Turn,
    format_step,
    initial_state,
    rotate_orientation,
)

Group = Tuple[Move, ...]


@dataclass
class PlannerOptions:
    allow_double_turns: bool = True  # 相对的两个面同时拧
    allow_parallel_rotate: bool = True  # 空转与其他动作同时进行
    allow_multi_grip: bool = True  # 多个机械手同时松开 / 夹紧


@dataclass
class Plan:
    moves: List[Move]
    steps: List[Step]
    states: List[State]  # 比 steps 多一个 (初始状态)
    durations: List[float]
    expanded: int = 0  # 搜索展开的节点数

    @property
    def total_time(self) -> float:
        return sum(self.durations)

    def stats(self) -> Dict[str, int]:
        s = {"steps": len(self.steps), "turn_steps": 0, "double_turns": 0,
             "cube_rotations": 0, "grip_steps": 0, "rotate_only_steps": 0}
        for step in self.steps:
            kinds = {type(a) for a in step}
            n_turn = sum(isinstance(a, Turn) for a in step)
            if n_turn:
                s["turn_steps"] += 1
                if n_turn == 2:
                    s["double_turns"] += 1
            elif CubeRotate in kinds:
                s["cube_rotations"] += 1
            elif kinds & {Open, Close}:
                s["grip_steps"] += 1
            else:
                s["rotate_only_steps"] += 1
        return s

    def format(self) -> str:
        lines = [f"转动序列: {format_moves(self.moves)}"]
        t = 0.0
        for i, (step, d) in enumerate(zip(self.steps, self.durations), 1):
            lines.append(f"{i:3d}. t={t:6.2f}s  (+{d:.2f}s)  {format_step(step)}")
            t += d
        lines.append(f"总耗时 {t:.2f}s, 共 {len(self.steps)} 步")
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        out = []
        for step, d in zip(self.steps, self.durations):
            actions = []
            for a in step:
                item = {"type": type(a).__name__}
                item.update(dataclasses.asdict(a))
                actions.append(item)
            out.append({"duration": round(d, 4), "actions": actions})
        return {"moves": format_moves(self.moves), "total_time": round(self.total_time, 4), "steps": out}


def group_moves(moves: Sequence[Move]) -> List[Group]:
    """合并连续的同轴转动; 同一个面的转动相加, 抵消为 0 的去掉。"""
    groups: List[Dict[str, int]] = []
    for face, k in moves:
        axis = axis_sign(face)[0]
        if groups and axis_sign(next(iter(groups[-1])))[0] == axis:
            groups[-1][face] = groups[-1].get(face, 0) + k
        else:
            groups.append({face: k})
        # 抵消后可能为空, 空组会让前后两组相邻, 需要再合并
        groups[-1] = {f: kk for f, kk in groups[-1].items() if normalize_k(kk) != 0}
        if not groups[-1]:
            groups.pop()
    return [tuple((f, normalize_k(k)) for f, k in sorted(g.items())) for g in groups]


class _Searcher:
    def __init__(self, machine: Machine, options: PlannerOptions, weight: float = 1.0) -> None:
        self.m = machine
        self.o = options
        self.w = weight
        self._free_cache: Dict[Tuple[Gripper, ...], List[Tuple[Step, float]]] = {}
        self._turn_cache: Dict[Tuple[Tuple[Gripper, ...], Step], Optional[Tuple[Gripper, ...]]] = {}
        self._orient_cache: Dict[Tuple[str, int, int], str] = {}

    # -- 动作候选 -------------------------------------------------------------

    def _rotate_options(self, g: Gripper) -> List[int]:
        if self.m.angle_limit is None:
            return [1]  # 不限角度时 +90 / -90 / 180 对夹条方向的效果只有 "翻转" 和 "不变"
        # 空转只为调整夹条方向或退绕线缆, ±90 度足够 (180 度可以分两步完成), 可大幅减少分支
        return [k for k in (1, -1) if abs(g.angle + k) <= self.m.angle_limit]

    def _rotation_combos(self, grippers: Tuple[Gripper, ...], busy: Sequence[str]) -> Iterator[Tuple[Action, ...]]:
        """给没有其他动作的松开机械手附加空转 (包括什么都不附加)。"""
        if not self.o.allow_parallel_rotate:
            yield ()
            return
        choices = []
        for p, g in zip(POSITIONS, grippers):
            if p in busy or g.closed:
                continue
            choices.append([None] + [Rotate(p, k) for k in self._rotate_options(g)])
        for combo in itertools.product(*choices):
            yield tuple(a for a in combo if a is not None)

    def _free_steps(self, grippers: Tuple[Gripper, ...]) -> List[Tuple[Step, float, Tuple[Gripper, ...], Optional[CubeRotate]]]:
        """与当前要拧的面无关的动作: 夹紧/松开、空转、整体翻转。只取决于机械手状态, 可缓存。

        返回 (步骤, 耗时, 执行后的机械手状态, 其中的整体翻转或 None)。
        """
        cached = self._free_cache.get(grippers)
        if cached is not None:
            return cached

        dummy = State(grippers, "URFDLB")
        steps: List[Step] = []

        # 夹紧 / 松开 (可附带其他松开机械手的空转)
        max_n = len(POSITIONS) if self.o.allow_multi_grip else 1
        for n in range(1, max_n + 1):
            for subset in itertools.combinations(POSITIONS, n):
                base = tuple(
                    Open(p) if grippers[POSITIONS.index(p)].closed else Close(p) for p in subset
                )
                for extra in self._rotation_combos(grippers, subset):
                    steps.append(base + extra)

        # 单独空转
        if self.o.allow_parallel_rotate:
            for extra in self._rotation_combos(grippers, ()):
                if extra:
                    steps.append(extra)
        else:
            for p, g in zip(POSITIONS, grippers):
                if not g.closed:
                    steps.extend((Rotate(p, k),) for k in self._rotate_options(g))

        # 整体翻转 (另一对机械手松开, 可同时空转)
        qs = (1, -1, 2) if self.m.angle_limit is None else (1, -1, 2, -2)
        for axis, pair in AXIS_PAIR.items():
            for q in qs:
                for extra in self._rotation_combos(grippers, pair):
                    steps.append((CubeRotate(axis, q),) + extra)

        result = []
        for step in steps:
            try:
                self.m.check(dummy, step)
            except InvalidStep:
                continue
            rot = next((a for a in step if isinstance(a, CubeRotate)), None)
            after = self.m.apply_unchecked(dummy, step).grippers
            result.append((step, self.m.duration(step), after, rot))
        self._free_cache[grippers] = result
        return result

    def _turn_ks(self, k: int) -> List[int]:
        if abs(k) == 1 or self.m.angle_limit is None:
            return [k]
        return [2, -2]

    def _turn_steps(self, state: State, group: Group, mask: int) -> Iterator[Tuple[Step, int]]:
        """拧当前组里还没完成的面; 返回 (步骤, 完成后的 mask)。"""
        remaining = [(i, f, k) for i, (f, k) in enumerate(group) if not mask & (1 << i)]
        candidates: List[Tuple[Tuple[Turn, ...], int]] = []
        for i, f, k in remaining:
            w = state.world_of(f)
            if w in POSITIONS:
                for kk in self._turn_ks(k):
                    candidates.append(((Turn(w, kk),), mask | (1 << i)))
        if self.o.allow_double_turns and len(remaining) == 2:
            (i1, f1, k1), (i2, f2, k2) = remaining
            w1, w2 = state.world_of(f1), state.world_of(f2)
            if w1 in POSITIONS and w2 in POSITIONS:
                for a in self._turn_ks(k1):
                    for b in self._turn_ks(k2):
                        candidates.append(((Turn(w1, a), Turn(w2, b)), mask | (1 << i1) | (1 << i2)))
        for turns, new_mask in candidates:
            busy = [t.pos for t in turns]
            for extra in self._rotation_combos(state.grippers, busy):
                yield turns + extra, new_mask

    def _turn_result(self, grippers: Tuple[Gripper, ...], step: Step) -> Optional[Tuple[Gripper, ...]]:
        """拧面步骤执行后的机械手状态; 不合法时返回 None。只取决于机械手状态, 可缓存。"""
        key = (grippers, step)
        if key in self._turn_cache:
            return self._turn_cache[key]
        dummy = State(grippers, "URFDLB")
        try:
            self.m.check(dummy, step)
            after: Optional[Tuple[Gripper, ...]] = self.m.apply_unchecked(dummy, step).grippers
        except InvalidStep:
            after = None
        self._turn_cache[key] = after
        return after

    def _orient(self, orientation: str, rot: CubeRotate) -> str:
        key = (orientation, rot.axis, rot.q)
        out = self._orient_cache.get(key)
        if out is None:
            out = rotate_orientation(orientation, rot.axis, rot.q)
            self._orient_cache[key] = out
        return out

    # -- A* -------------------------------------------------------------------

    def search(self, groups: Sequence[Group], start: State) -> Tuple[List[Step], List[State], List[float], List[int], int]:
        """返回 (steps, states, durations, 每个状态对应的已完成组数, 展开节点数)。"""
        t = self.m.timing
        n = len(groups)
        pair_open = t.open
        min_regrip = t.cube90 + t.close

        def group_bound(g: Group, mask: int = 0) -> float:
            ks = [k for i, (_, k) in enumerate(g) if not mask & (1 << i)]
            return max(t.turn(k) for k in ks) if ks else 0.0

        suffix = [0.0] * (n + 1)
        for i in range(n - 1, -1, -1):
            suffix[i] = suffix[i + 1] + group_bound(groups[i])

        def h(gi: int, mask: int, state: State) -> float:
            if gi >= n:
                return 0.0
            base = group_bound(groups[gi], mask) + suffix[gi + 1]
            # 当前组剩下的面都在 U/D (没有机械手) 时, 至少要整体翻转一次, 之后还要夹紧才能拧;
            # 若垂直方向的机械手都夹紧着, 翻转前还得先松开
            group = groups[gi]
            worlds = [state.world_of(f) for i, (f, _) in enumerate(group) if not mask & (1 << i)]
            if worlds and all(w in "UD" for w in worlds):
                g = state.grippers
                both_pairs_closed = all(x.closed for x in g)
                base += min_regrip + (pair_open if both_pairs_closed else 0.0)
            return base

        Node = Tuple[int, int, State]
        start_node: Node = (0, 0, start)
        best: Dict[Node, float] = {start_node: 0.0}
        parent: Dict[Node, Tuple[Optional[Node], Optional[Step], float]] = {start_node: (None, None, 0.0)}
        counter = itertools.count()
        w = self.w
        heap = [(w * h(0, 0, start), 0.0, next(counter), start_node)]
        expanded = 0

        while heap:
            f, g, _, node = heapq.heappop(heap)
            if g > best.get(node, float("inf")):
                continue
            gi, mask, state = node
            if gi >= n:
                return self._reconstruct(node, parent, expanded)
            expanded += 1

            def push(step: Step, cost: float, new_node: Node) -> None:
                ng = g + cost
                if ng < best.get(new_node, float("inf")) - 1e-12:
                    best[new_node] = ng
                    parent[new_node] = (node, step, cost)
                    heapq.heappush(heap, (ng + w * h(*new_node), ng, next(counter), new_node))

            for step, cost, after, rot in self._free_steps(state.grippers):
                orientation = self._orient(state.orientation, rot) if rot else state.orientation
                push(step, cost, (gi, mask, State(after, orientation)))

            group = groups[gi]
            full = (1 << len(group)) - 1
            for step, new_mask in self._turn_steps(state, group, mask):
                after = self._turn_result(state.grippers, step)
                if after is None:
                    continue
                new_state = State(after, state.orientation)
                if new_mask == full:
                    push(step, self.m.duration(step), (gi + 1, 0, new_state))
                else:
                    push(step, self.m.duration(step), (gi, new_mask, new_state))

        raise RuntimeError("找不到可行的动作序列 (机器约束可能过严)")

    def _reconstruct(self, node, parent, expanded):
        steps: List[Step] = []
        states: List[State] = []
        durations: List[float] = []
        done: List[int] = []
        cur = node
        while True:
            prev, step, cost = parent[cur]
            states.append(cur[2])
            done.append(cur[0])
            if prev is None:
                break
            steps.append(step)
            durations.append(cost)
            cur = prev
        for lst in (steps, states, durations, done):
            lst.reverse()
        return steps, states, durations, done, expanded


def _step_variants(step: Step, state: State, machine: Machine) -> List[Step]:
    """同一步动作的等价写法, 只影响机械手的累计角度, 不影响夹条方向 (奇偶) 和魔方:
    - 空转 ±90 度、拧 180 度、整体翻转 180 度可以换方向;
    - 松开且本步空闲的机械手可以顺带空转 ±180 度来退绕 (可能延长这一步的耗时)。
    """
    options: List[List[Optional[Action]]] = []
    used = set()
    for a in step:
        if isinstance(a, CubeRotate):
            used.update(AXIS_PAIR[a.axis])
        else:
            used.add(a.pos)
        if isinstance(a, Rotate):
            options.append([Rotate(a.pos, k) for k in ((1, -1) if abs(a.k) == 1 else (2, -2))])
        elif isinstance(a, Turn) and abs(a.k) == 2:
            options.append([Turn(a.pos, 2), Turn(a.pos, -2)])
        elif isinstance(a, CubeRotate) and abs(a.q) == 2:
            options.append([CubeRotate(a.axis, 2), CubeRotate(a.axis, -2)])
        else:
            options.append([a])
    for p, g in zip(POSITIONS, state.grippers):
        if p not in used and not g.closed:
            options.append([None, Rotate(p, 2), Rotate(p, -2)])
    return [tuple(x for x in v if x is not None) for v in itertools.product(*options)]


def fit_angle_limit(steps: Sequence[Step], machine: Machine, start: State) -> Optional[List[Step]]:
    """为不限角度的动作序列选择旋转方向 (必要时顺带退绕), 使每个机械手的累计角度
    不超过 machine.angle_limit, 并使总耗时最短。

    动态规划, 状态为 4 个机械手的累计角度 (最多 (2*limit+1)^4 个)。找不到时返回 None。
    """
    layer: Dict[State, Tuple[float, Optional[State], Optional[Step]]] = {start: (0.0, None, None)}
    history = [layer]
    for step in steps:
        nxt: Dict[State, Tuple[float, Optional[State], Optional[Step]]] = {}
        for st, (cost, _, _) in layer.items():
            for variant in _step_variants(step, st, machine):
                try:
                    new = machine.apply(st, variant)
                except InvalidStep:
                    continue
                c = cost + machine.duration(variant)
                if new not in nxt or c < nxt[new][0] - 1e-12:
                    nxt[new] = (c, st, variant)
        if not nxt:
            return None
        history.append(nxt)
        layer = nxt
    st = min(layer, key=lambda k: layer[k][0])
    out: List[Step] = []
    for i in range(len(steps), 0, -1):
        _, prev, variant = history[i][st]
        out.append(variant)
        st = prev
    out.reverse()
    return out


def plan(
    moves: Sequence[Move],
    machine: Optional[Machine] = None,
    options: Optional[PlannerOptions] = None,
    start: Optional[State] = None,
    window: Optional[int] = 4,
    commit: int = 2,
    weight: float = 1.0,
) -> Plan:
    """为转动序列生成机械手动作序列。

    - window 为 None 时对整个序列做 A* 搜索, 结果是 (在机器模型和耗时参数下) 总耗时最短的方案,
      但序列较长时很慢。默认用滚动窗口: 每次对接下来 window 组转动求最优, 只采用前 commit 组的
      动作, 再从新状态继续。实测比全局最优只慢 1~2%。
    - weight > 1 时为加权 A*: 搜索更快, 结果略差。
    - 有角度限制时, 每个窗口先按不限角度规划 (快得多), 再用 fit_angle_limit 选择旋转方向;
      只有选不出来的窗口才做完整的受限搜索。
    """
    machine = machine or Machine()
    options = options or PlannerOptions()
    state = start or initial_state()
    groups = group_moves(moves)
    limited = machine.angle_limit is not None
    exact = _Searcher(machine, options, weight)
    free = _Searcher(Machine(machine.timing, None, machine.no_adjacent_horizontal), options, weight) if limited else exact

    steps: List[Step] = []
    states: List[State] = [state]
    durations: List[float] = []
    expanded = 0
    i = 0
    while True:
        chunk = groups[i:] if window is None else groups[i : i + window]
        last = window is None or i + len(chunk) >= len(groups)
        need = len(chunk) if last else commit

        chosen: Optional[List[Step]] = None
        if limited:
            start_free = State(tuple(Gripper(g.closed, g.angle % 2) for g in state.grippers), state.orientation)
            f_steps, _, _, f_done, f_exp = free.search(chunk, start_free)
            expanded += f_exp
            cut = len(f_steps) if last else next(k for k, d in enumerate(f_done) if d >= need)
            chosen = fit_angle_limit(f_steps[:cut], machine, state)
        if chosen is None:
            s_steps, _, _, s_done, s_exp = exact.search(chunk, state)
            expanded += s_exp
            cut = len(s_steps) if last else next(k for k, d in enumerate(s_done) if d >= need)
            chosen = s_steps[:cut]

        for step in chosen:
            state = machine.apply(state, step)
            steps.append(step)
            states.append(state)
            durations.append(machine.duration(step))
        if last:
            break
        i += commit
    return Plan(list(moves), steps, states, durations, expanded)
