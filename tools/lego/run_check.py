"""运行全部检查: python run_check.py [large|medium ...]   (默认两种马达都检查)

1. 夹紧、松开两种状态: 零件干涉 + 销/轴连接 + 蓝色长销能否装上 (挡肩位置和装配顺序);
2. 转动扫描: 机械手每 15° 一格转满一圈, 转动部分不能碰到测试架和马达;
3. 松开时魔方整体翻转 0~90° (将来四臂时), 不能碰到机械手。
"""
import math
import sys

import numpy as np

import check
import model


def is_head(p):
    return model.STEPS[p.step - 1]["title"] in model.head_names()


def report(parts, label):
    n = 0
    for a, b, k in check.collisions(parts):
        n += 1
        print(f"[{label}] 干涉: {check.CATALOG_NAME(a)} {a.pos.round(1).tolist()} <-> "
              f"{check.CATALOG_NAME(b)} {b.pos.round(1).tolist()} ({k} 点)")
    for p in check.connections(parts):
        n += 1
        print(f"[{label}] 连接: {p}")
    for p in check.long_pins(parts):
        n += 1
        print(f"[{label}] 长销: {p}")
    return n


def rotation_sweep(motor):
    n = 0
    for ang in range(15, 360, 15):
        ps = model.build(head_angle=ang, with_cube=False, motor=motor)
        for a, b, k in check.collisions(ps):
            if is_head(a) != is_head(b):
                n += 1
                print(f"[{motor} 转 {ang}°] 干涉: {check.CATALOG_NAME(a)} <-> {check.CATALOG_NAME(b)} ({k} 点)")
    return n


def cube_flip(motor):
    n = 0
    for ang in range(10, 91, 10):
        ps = model.build(fork_extended=False, motor=motor)
        head = [p for p in ps if is_head(p)]
        cube = [p for p in ps if p.name == "cube56.dat"][0]
        a = math.radians(ang)
        cube.rot = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
        for x, y, k in check.collisions(head + [cube]):
            n += 1
            print(f"[{motor} 魔方翻转 {ang}°] 干涉: {check.CATALOG_NAME(x)} <-> {check.CATALOG_NAME(y)} ({k} 点)")
    return n


if __name__ == "__main__":
    motors = sys.argv[1:] or ["large", "medium"]
    total = 0
    for m in motors:
        total += report(model.build(motor=m), f"{m} 夹紧")
        total += report(model.build(fork_extended=False, motor=m), f"{m} 松开")
        total += rotation_sweep(m)
        total += cube_flip(m)
    print("问题数:", total)
    sys.exit(1 if total else 0)
