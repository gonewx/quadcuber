"""汇总单臂测试程序 (firmware/pico/arm_test.py) 的串口日志, 生成 timing.json。

日志中每个测量结果是一行 "RESULT {json}"。对应关系:

| 日志                         | Timing 字段 |
| ---------------------------- | ----------- |
| move, tag=free, q=±1         | rotate90    |
| move, tag=free, q=±2         | rotate180   |
| move, tag=load, q=±1         | turn90      |
| move, tag=load, q=±2         | turn180     |
| grip                         | open, close |

整体翻转 (cube90 / cube180) 需要两个机械手配合, 单臂测不出来, 保持原值。
取值用成功动作到位耗时 (t_settle) 的平均值: Pico 执行时每一步都等到位反馈, 平均值就是预期耗时。
"""

from __future__ import annotations

import json
import statistics
from dataclasses import asdict
from typing import Dict, Iterable, List, Optional, Tuple

from .machine import Timing

_MOVE_FIELDS = {
    ("free", 1): "rotate90",
    ("free", 2): "rotate180",
    ("load", 1): "turn90",
    ("load", 2): "turn180",
}


def parse_results(lines: Iterable[str]) -> List[dict]:
    out = []
    for line in lines:
        i = line.find("RESULT {")
        if i < 0:
            continue
        try:
            out.append(json.loads(line[i + 7 :].strip()))
        except json.JSONDecodeError:
            continue  # 串口传输中断造成的残行
    return out


class MoveStats:
    def __init__(self, rows: List[dict]):
        ok = [r for r in rows if r.get("ok")]
        self.total = len(rows)
        self.ok = len(ok)
        self.times = sorted(r["t_settle"] for r in ok)
        self.errs = [abs(r["err"]) for r in ok]
        self.rest_errs = [abs(r["err_rest"]) for r in ok]
        self.failures: Dict[str, int] = {}
        for r in rows:
            if not r.get("ok"):
                self.failures[r["state"]] = self.failures.get(r["state"], 0) + 1

    @property
    def mean(self) -> Optional[float]:
        return statistics.mean(self.times) if self.times else None

    def percentile(self, p: float) -> Optional[float]:
        if not self.times:
            return None
        return self.times[min(len(self.times) - 1, int(len(self.times) * p))]


def group_moves(results: List[dict]) -> Dict[Tuple[str, int], MoveStats]:
    groups: Dict[Tuple[str, int], List[dict]] = {}
    for r in results:
        if r.get("type") != "move" or r.get("q") is None:
            continue
        groups.setdefault((r["tag"], abs(r["q"])), []).append(r)
    return {k: MoveStats(v) for k, v in sorted(groups.items())}


def suggest_timing(results: List[dict], base: Timing) -> Tuple[Timing, List[str]]:
    values = asdict(base)
    notes = []
    for key, stats in group_moves(results).items():
        field = _MOVE_FIELDS.get(key)
        if field and stats.mean is not None:
            values[field] = round(stats.mean, 3)
    grips = [r for r in results if r.get("type") == "grip"]
    if grips:
        values["open"] = grips[-1]["open"]
        values["close"] = grips[-1]["close"]
        notes.append("open/close 取自 SERVO_MOVE_MS 配置值, 请用录像确认舵机确实在这个时间内到位")
    missing = [f for f in _MOVE_FIELDS.values() if values[f] == getattr(base, f)]
    if missing:
        notes.append("以下字段没有测量数据, 沿用原值: " + ", ".join(missing))
    notes.append("cube90/cube180 (整体翻转) 单臂无法测量, 沿用原值")
    return Timing(**values), notes


def report(results: List[dict]) -> str:
    lines = ["| 类别 | 成功/总数 | 平均 (s) | p90 (s) | 最长 (s) | 到位误差 平均/最大 (度) | 静止后最大误差 (度) | 失败 |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for (tag, q), s in group_moves(results).items():
        if s.times:
            row = (
                f"| {tag} {q * 90}° | {s.ok}/{s.total} | {s.mean:.3f} | {s.percentile(0.9):.3f} | {s.times[-1]:.3f} | "
                f"{statistics.mean(s.errs):.2f} / {max(s.errs):.2f} | {max(s.rest_errs):.2f} | "
            )
        else:
            row = f"| {tag} {q * 90}° | 0/{s.total} | - | - | - | - | - | "
        row += ", ".join(f"{k}×{v}" for k, v in s.failures.items()) + " |"
        lines.append(row)
    cycles = [r["t_total"] for r in results if r.get("type") == "cycle"]
    if cycles:
        lines.append(f"\n夹紧-拧-松开-转回 循环: {len(cycles)} 次, 平均 {statistics.mean(cycles):.3f}s, 最长 {max(cycles):.3f}s")
    return "\n".join(lines)
