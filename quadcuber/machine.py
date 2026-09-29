"""四机械手机器的状态、动作和物理约束。

机器结构 (俯视, 魔方悬空夹在中间):

                 B
                 |
           L --[魔方]-- R          U 面朝上 (摄像头), D 面朝下, 这两个面没有机械手
                 |
                 F

- 4 个机械手分别位于世界坐标的 R(+x) / L(-x) / F(+z) / B(-z) 方向。
- 每个机械手有两个动作: 夹紧/松开, 以及绕自身轴线旋转 (90 度的整数倍)。
- 夹爪是一根横跨面中间一行/一列的 "夹条"。角度为偶数 (含 0) 时夹条竖直 (平行于 y 轴),
  为奇数时水平。

约束 (详见 Machine.check):
1. 支撑: 任何时刻 L、R 都夹紧, 或 F、B 都夹紧, 否则魔方会掉落。
   同时有松开和夹紧的步骤, 按 "先松开、后夹紧" 的中间状态检查。
   注意: 这里假设夹条水平时这一对也能托住魔方。按现在的 U 形叉结构, 水平叉子
   只能靠摩擦力, 几乎没有压紧力, 这个假设**尚未验证** (见 docs/arm_concept.md 第 7 节)。
2. 拧面: 转动机械手 P 所夹的面时, 与 P 垂直且夹紧的机械手的夹条必须竖直
   (水平夹条会压住被转动的那一层); 并且至少有一个这样的机械手夹紧,
   用来固定中间层, 否则中间层会被带着一起转。
   两个相对的面可以在同一步里同时拧。
3. 整体翻转: 一对相对的机械手夹紧并同向旋转, 使整个魔方绕该轴转动;
   此时另一对必须松开。
4. 松开的机械手可以自由旋转 (用于把夹条恢复到竖直), 可与其他动作同时进行。
5. 若设置了角度限制 (夹爪上的舵机线缆不能无限缠绕), 每个机械手的累计角度
   必须在 [-limit, +limit] 个 90 度之内。
6. 若开启 no_adjacent_horizontal (v3 四臂结构, 见 tools/lego/v3/four_arm.py):
   相邻两个机械手的夹指同时处于水平附近 (约 80° 以上) 时会在魔方棱边外相撞。
   因此正在转动的机械手 (拧面、空转、整体翻转), 它两侧相邻的机械手必须竖直且不在同一步里转动。
   转 180° 也会经过水平, 同样适用。初始状态全部竖直, 按此规则永远不会出现相邻两个都水平。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, NamedTuple, Optional, Sequence, Tuple, Union

from .cube import FACE_NORMALS, NORMAL_FACE, axis_sign, rotate

POSITIONS: Tuple[str, ...] = ("R", "L", "F", "B")
POS_INDEX: Dict[str, int] = {p: i for i, p in enumerate(POSITIONS)}
OPPOSITE: Dict[str, str] = {"R": "L", "L": "R", "F": "B", "B": "F"}
PAIRS: Tuple[Tuple[str, str], ...] = (("R", "L"), ("F", "B"))
AXIS_PAIR: Dict[int, Tuple[str, str]] = {0: ("R", "L"), 2: ("F", "B")}

# 世界方向的固定顺序, orientation[i] 表示当前处在 WORLD[i] 方向的是魔方的哪个面
WORLD = "URFDLB"


def perpendicular(pos: str) -> Tuple[str, str]:
    return ("F", "B") if pos in ("R", "L") else ("R", "L")


# 注意: 动作类型用 frozen dataclass 而不是 NamedTuple。NamedTuple 按元组比较,
# Turn("F", 1) 会等于 Rotate("F", 1), 用作缓存键时会混淆不同动作。


class Gripper(NamedTuple):
    closed: bool
    angle: int  # 从机械手一侧看顺时针的 90 度个数

    @property
    def vertical(self) -> bool:
        return self.angle % 2 == 0


class State(NamedTuple):
    grippers: Tuple[Gripper, Gripper, Gripper, Gripper]  # 顺序同 POSITIONS
    orientation: str  # 长度 6, 与 WORLD 对应

    def gripper(self, pos: str) -> Gripper:
        return self.grippers[POS_INDEX[pos]]

    def world_of(self, face: str) -> str:
        """魔方的某个面当前朝向哪个世界方向。"""
        return WORLD[self.orientation.index(face)]


def initial_state() -> State:
    return State(tuple(Gripper(True, 0) for _ in POSITIONS), WORLD)


# ---------------------------------------------------------------------------
# 动作
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Turn:
    """夹紧的机械手旋转, 拧动它夹着的那一面。k 为顺时针 90 度个数 (1, 2, -1, -2)。"""

    pos: str
    k: int

    def __str__(self) -> str:
        return f"{self.pos}拧{_deg(self.k)}"


@dataclass(frozen=True)
class Open:
    pos: str

    def __str__(self) -> str:
        return f"{self.pos}松开"


@dataclass(frozen=True)
class Close:
    pos: str

    def __str__(self) -> str:
        return f"{self.pos}夹紧"


@dataclass(frozen=True)
class Rotate:
    """松开的机械手空转 (调整夹条方向)。"""

    pos: str
    k: int

    def __str__(self) -> str:
        return f"{self.pos}空转{_deg(self.k)}"


@dataclass(frozen=True)
class CubeRotate:
    """一对机械手同步旋转, 使整个魔方绕 +axis 轴转 q 个 90 度 (axis: 0=x, 2=z)。"""

    axis: int
    q: int

    def __str__(self) -> str:
        a, b = AXIS_PAIR[self.axis]
        return f"整体翻转(绕{a}{b}轴 {_deg(self.q)})"


Action = Union[Turn, Open, Close, Rotate, CubeRotate]
Step = Tuple[Action, ...]


def _deg(k: int) -> str:
    return f"{k * 90:+d}°"


def format_step(step: Step) -> str:
    return " + ".join(str(a) for a in step)


# ---------------------------------------------------------------------------
# 耗时参数
# ---------------------------------------------------------------------------


@dataclass
class Timing:
    """各动作耗时 (秒)。默认值是估算值, 需要在实机上测量后替换。"""

    turn90: float = 0.18
    turn180: float = 0.30
    open: float = 0.10
    close: float = 0.10
    rotate90: float = 0.15  # 松开状态下空转
    rotate180: float = 0.25
    cube90: float = 0.22  # 整体翻转
    cube180: float = 0.35

    def turn(self, k: int) -> float:
        return self.turn90 if abs(k) == 1 else self.turn180

    def rotate(self, k: int) -> float:
        return self.rotate90 if abs(k) == 1 else self.rotate180

    def cube(self, q: int) -> float:
        return self.cube90 if abs(q) == 1 else self.cube180

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "Timing":
        unknown = set(data) - set(cls.__dataclass_fields__)
        if unknown:
            raise ValueError(f"未知的耗时参数: {sorted(unknown)}")
        return cls(**data)


class InvalidStep(Exception):
    pass


@dataclass
class Machine:
    timing: Timing = field(default_factory=Timing)
    angle_limit: Optional[int] = None  # None 表示机械手可以无限旋转
    no_adjacent_horizontal: bool = False  # 约束 6: 相邻机械手不能同时经过水平 (v3 结构需要)

    # -- 基础工具 -----------------------------------------------------------

    def _norm_angle(self, angle: int) -> int:
        # 不限角度时只有夹条方向 (奇偶) 有意义, 统一取 0/1 以缩小搜索空间
        return angle % 2 if self.angle_limit is None else angle

    def _angle_ok(self, angle: int) -> bool:
        return self.angle_limit is None or abs(angle) <= self.angle_limit

    @staticmethod
    def supported(closed: Dict[str, bool]) -> bool:
        return any(closed[a] and closed[b] for a, b in PAIRS)

    # -- 校验 ---------------------------------------------------------------

    def check(self, state: State, step: Sequence[Action]) -> None:
        """检查一步 (一组同时执行的动作) 是否合法, 不合法时抛出 InvalidStep。"""
        if not step:
            raise InvalidStep("空步骤")

        g = {p: state.gripper(p) for p in POSITIONS}
        used: Dict[str, Action] = {}
        turns: List[Turn] = []
        cube_rots: List[CubeRotate] = []
        grips: List[Action] = []
        rotates: List[Rotate] = []

        def claim(pos: str, action: Action) -> None:
            if pos in used:
                raise InvalidStep(f"{pos} 在同一步中有多个动作")
            used[pos] = action

        for a in step:
            if isinstance(a, Turn):
                claim(a.pos, a)
                turns.append(a)
            elif isinstance(a, CubeRotate):
                if a.axis not in AXIS_PAIR:
                    raise InvalidStep(f"不支持绕轴 {a.axis} 整体翻转")
                for p in AXIS_PAIR[a.axis]:
                    claim(p, a)
                cube_rots.append(a)
            elif isinstance(a, (Open, Close)):
                claim(a.pos, a)
                grips.append(a)
            elif isinstance(a, Rotate):
                claim(a.pos, a)
                rotates.append(a)
            else:
                raise InvalidStep(f"未知动作 {a!r}")

        if sum(bool(x) for x in (turns, cube_rots, grips)) > 1:
            raise InvalidStep("拧面、整体翻转、夹紧/松开不能在同一步中混合")

        # 松开的机械手空转
        for r in rotates:
            if g[r.pos].closed:
                raise InvalidStep(f"{r.pos} 夹紧状态下不能空转")
            if r.k % 4 == 0:
                raise InvalidStep("空转角度为 0")
            if not self._angle_ok(g[r.pos].angle + r.k):
                raise InvalidStep(f"{r.pos} 超出角度限制")

        # 夹紧 / 松开
        if grips:
            for a in grips:
                if isinstance(a, Open) and not g[a.pos].closed:
                    raise InvalidStep(f"{a.pos} 已经是松开状态")
                if isinstance(a, Close) and g[a.pos].closed:
                    raise InvalidStep(f"{a.pos} 已经是夹紧状态")
            after_open = {p: g[p].closed for p in POSITIONS}
            for a in grips:
                if isinstance(a, Open):
                    after_open[a.pos] = False
            if not self.supported(after_open):
                raise InvalidStep("松开后魔方失去支撑")

        # 拧面
        if turns:
            if len(turns) == 2 and OPPOSITE[turns[0].pos] != turns[1].pos:
                raise InvalidStep("同一步只能同时拧两个相对的面")
            if len(turns) > 2:
                raise InvalidStep("同一步最多拧两个面")
            for t in turns:
                if t.k % 4 == 0:
                    raise InvalidStep("拧面角度为 0")
                if not g[t.pos].closed:
                    raise InvalidStep(f"{t.pos} 没有夹紧, 不能拧面")
                if not self._angle_ok(g[t.pos].angle + t.k):
                    raise InvalidStep(f"{t.pos} 超出角度限制")
            anchors = 0
            for p in perpendicular(turns[0].pos):
                if g[p].closed:
                    if not g[p].vertical:
                        raise InvalidStep(f"{p} 的夹条是水平的, 会挡住 {turns[0].pos} 的转动")
                    anchors += 1
            if anchors == 0:
                raise InvalidStep("没有垂直方向的机械手固定中间层")

        # 整体翻转
        for c in cube_rots:
            if c.q % 4 == 0:
                raise InvalidStep("翻转角度为 0")
            a, b = AXIS_PAIR[c.axis]
            if not (g[a].closed and g[b].closed):
                raise InvalidStep(f"整体翻转需要 {a}、{b} 都夹紧")
            for p in perpendicular(a):
                if g[p].closed:
                    raise InvalidStep(f"整体翻转时 {p} 必须松开")
            for p in (a, b):
                if not self._angle_ok(g[p].angle + self._cube_angle_delta(p, c.q)):
                    raise InvalidStep(f"{p} 超出角度限制")

        # 相邻机械手防碰撞
        if self.no_adjacent_horizontal:
            movers = [a.pos for a in turns] + [r.pos for r in rotates]
            for c in cube_rots:
                movers.extend(AXIS_PAIR[c.axis])
            for p in movers:
                for n in perpendicular(p):
                    if n in movers:
                        raise InvalidStep(f"相邻的 {p}、{n} 不能在同一步里转动")
                    if not g[n].vertical:
                        raise InvalidStep(f"{n} 的夹指是水平的, {p} 转动时会和它相撞")

    @staticmethod
    def _cube_angle_delta(pos: str, q: int) -> int:
        # 魔方绕 +axis 转 q, 对位于 sign 一侧的机械手来说是顺时针 -sign*q
        _, sign = axis_sign(pos)
        return -sign * q

    # -- 执行 ---------------------------------------------------------------

    def apply(self, state: State, step: Sequence[Action]) -> State:
        self.check(state, step)
        return self.apply_unchecked(state, step)

    def apply_unchecked(self, state: State, step: Sequence[Action]) -> State:
        grippers = list(state.grippers)
        orientation = state.orientation

        def update(pos: str, closed: Optional[bool] = None, dangle: int = 0) -> None:
            i = POS_INDEX[pos]
            old = grippers[i]
            grippers[i] = Gripper(
                old.closed if closed is None else closed,
                self._norm_angle(old.angle + dangle),
            )

        for a in step:
            if isinstance(a, Turn):
                update(a.pos, dangle=a.k)
            elif isinstance(a, Rotate):
                update(a.pos, dangle=a.k)
            elif isinstance(a, Open):
                update(a.pos, closed=False)
            elif isinstance(a, Close):
                update(a.pos, closed=True)
            elif isinstance(a, CubeRotate):
                for p in AXIS_PAIR[a.axis]:
                    update(p, dangle=self._cube_angle_delta(p, a.q))
                orientation = rotate_orientation(orientation, a.axis, a.q)
        return State(tuple(grippers), orientation)

    def duration(self, step: Sequence[Action]) -> float:
        t = self.timing
        d = 0.0
        for a in step:
            if isinstance(a, Turn):
                d = max(d, t.turn(a.k))
            elif isinstance(a, Rotate):
                d = max(d, t.rotate(a.k))
            elif isinstance(a, Open):
                d = max(d, t.open)
            elif isinstance(a, Close):
                d = max(d, t.close)
            elif isinstance(a, CubeRotate):
                d = max(d, t.cube(a.q))
        return d


def rotate_orientation(orientation: str, axis: int, q: int) -> str:
    """整个魔方绕 +axis 转 q 后, 各世界方向上的魔方面。"""
    new = list(orientation)
    for i, world in enumerate(WORLD):
        target = NORMAL_FACE[rotate(FACE_NORMALS[world], axis, q)]
        new[WORLD.index(target)] = orientation[i]
    return "".join(new)
