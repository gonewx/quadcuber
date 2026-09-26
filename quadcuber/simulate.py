"""模拟器: 在贴纸魔方上逐步执行动作序列, 独立验证规划结果。

模拟器只按 "世界坐标中哪个机械手做了什么" 来转动贴纸, 不使用规划器记录的魔方朝向,
因此如果规划器的朝向跟踪出错, 最终魔方不会还原, 可以被检测出来。
每一步同时用 Machine.check 检查物理约束。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence

from .cube import Cube, Move, face_quarters
from .machine import CubeRotate, InvalidStep, Machine, State, Step, Turn, format_step, initial_state
from .planner import Plan


@dataclass
class SimResult:
    solved: bool
    total_time: float
    error: Optional[str] = None
    failed_step: Optional[int] = None
    timeline: List[str] = field(default_factory=list)


def execute_physical(cube: Cube, step: Step) -> None:
    for a in step:
        if isinstance(a, Turn):
            axis, sign, q = face_quarters(a.pos, a.k)
            cube.turn_layer(axis, sign, q)
        elif isinstance(a, CubeRotate):
            cube.rotate_all(a.axis, a.q)
        # 松开 / 夹紧 / 空转不改变魔方


def simulate(
    steps: Sequence[Step],
    scramble: Sequence[Move],
    machine: Optional[Machine] = None,
    start: Optional[State] = None,
) -> SimResult:
    """从 "打乱后的魔方 + 初始机器状态" 出发执行 steps, 返回是否还原。"""
    machine = machine or Machine()
    state = start or initial_state()
    cube = Cube().apply(scramble)
    t = 0.0
    timeline: List[str] = []
    for i, step in enumerate(steps, 1):
        try:
            state = machine.apply(state, step)
        except InvalidStep as e:
            return SimResult(False, t, f"第 {i} 步不合法: {e}", i, timeline)
        execute_physical(cube, step)
        d = machine.duration(step)
        timeline.append(f"{i:3d}. t={t:6.2f}s  {format_step(step)}")
        t += d
    return SimResult(cube.is_solved(), t, None if cube.is_solved() else "执行完毕但魔方未还原", None, timeline)


def verify_plan(plan: Plan, scramble: Sequence[Move], machine: Optional[Machine] = None) -> SimResult:
    return simulate(plan.steps, scramble, machine, plan.states[0])
