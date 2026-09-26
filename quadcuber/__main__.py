"""命令行入口。

    python -m quadcuber plan "R U R' U'"          规划并在模拟器中验证一个转动序列
    python -m quadcuber bench --count 20          随机生成转动序列, 统计规划结果
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
import time

from .cube import format_moves, invert, parse_moves, random_scramble
from .machine import Machine, Timing
from .planner import PlannerOptions, plan
from .simulate import verify_plan


def _machine(args: argparse.Namespace) -> Machine:
    timing = Timing()
    if args.timing:
        with open(args.timing, encoding="utf-8") as f:
            timing = Timing.from_dict(json.load(f))
    return Machine(timing, args.angle_limit)


def _window(args: argparse.Namespace):
    return None if args.full else args.window


def cmd_plan(args: argparse.Namespace) -> int:
    machine = _machine(args)
    moves = parse_moves(args.moves)
    t0 = time.perf_counter()
    p = plan(moves, machine, window=_window(args), commit=max(1, args.window // 2))
    cpu = time.perf_counter() - t0
    print(p.format())
    result = verify_plan(p, invert(moves), machine)
    print(f"模拟器验证: {'通过' if result.solved else '失败: ' + str(result.error)}")
    print(f"规划耗时 {cpu:.2f}s (CPU), 展开 {p.expanded} 个节点")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(p.to_dict(), f, ensure_ascii=False, indent=2)
        print(f"已写入 {args.json}")
    return 0 if result.solved else 1


def cmd_bench(args: argparse.Namespace) -> int:
    machine = _machine(args)
    rng = random.Random(args.seed)
    variants = [("优化", PlannerOptions())]
    if args.compare:
        variants.append(("无并行", PlannerOptions(False, False, False)))
    cases = [invert(random_scramble(args.length, rng)) for _ in range(args.count)]
    ok = True
    for name, options in variants:
        times, cpus, turns = [], [], []
        for moves in cases:
            t0 = time.perf_counter()
            p = plan(moves, machine, options, window=_window(args), commit=max(1, args.window // 2))
            cpus.append(time.perf_counter() - t0)
            r = verify_plan(p, invert(moves), machine)
            if not r.solved:
                ok = False
                print(f"[{name}] 验证失败: {format_moves(moves)}: {r.error}")
            times.append(p.total_time)
            turns.append(p.stats()["cube_rotations"])
        print(
            f"[{name}] {args.count} 个 {args.length} 步序列: 动作耗时 平均 {statistics.mean(times):.2f}s "
            f"(最短 {min(times):.2f}s, 最长 {max(times):.2f}s), 整体翻转平均 {statistics.mean(turns):.1f} 次, "
            f"规划 CPU 平均 {statistics.mean(cpus):.2f}s"
        )
    print("全部通过模拟器验证" if ok else "存在验证失败的方案")
    return 0 if ok else 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="quadcuber", description="四机械手魔方机器人 动作规划器 / 模拟器")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--angle-limit", type=int, default=None, help="机械手累计旋转限制 (90 度的个数), 默认不限")
    common.add_argument("--timing", help="动作耗时参数 JSON 文件 (字段见 machine.Timing)")
    common.add_argument("--window", type=int, default=4, help="滚动窗口大小 (组数), 默认 4")
    common.add_argument("--full", action="store_true", help="对整个序列求最优 (慢)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_plan = sub.add_parser("plan", parents=[common], help="规划一个转动序列")
    p_plan.add_argument("moves", help='转动序列, 例如 "R U R\' U\'"')
    p_plan.add_argument("--json", help="把动作序列写入 JSON 文件")
    p_plan.set_defaults(func=cmd_plan)

    p_bench = sub.add_parser("bench", parents=[common], help="随机序列统计")
    p_bench.add_argument("--count", type=int, default=20)
    p_bench.add_argument("--length", type=int, default=20)
    p_bench.add_argument("--seed", type=int, default=1)
    p_bench.add_argument("--compare", action="store_true", help="同时统计不做任何并行的基准方案")
    p_bench.set_defaults(func=cmd_bench)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
