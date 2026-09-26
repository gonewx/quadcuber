"""运行全部检查: python run_check.py"""
import sys

import check
import model


def report(parts, label):
    n = 0
    for a, b, k in check.collisions(parts):
        n += 1
        print(f"[{label}] 干涉: {check.CATALOG_NAME(a)} {a.pos.round(1).tolist()} <-> "
              f"{check.CATALOG_NAME(b)} {b.pos.round(1).tolist()} ({k} 点)")
    for p in check.connections(parts):
        n += 1
        print(f"[{label}] 连接: {p}")
    return n


if __name__ == "__main__":
    total = report(model.build(), "夹紧")
    total += report(model.build(fork_extended=False), "松开")
    print("问题数:", total)
    sys.exit(1 if total else 0)
