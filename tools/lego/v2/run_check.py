"""v2 全部检查: python run_check.py   (在 tools/lego/v2 目录下运行)

复用上一级的 check.py / ldraw.py (不改它们), 只在运行时补充 v2 用到的新零件:
1. 夹紧、松开两种状态: 零件干涉 + 销/轴连接 + 蓝色长销能否装上 (挡肩位置和装配顺序);
2. 转动扫描: 机械臂每 15° 一格转满一圈, 转动部分不能碰到底座、转盘支座、马达和固定叉;
3. 松开时魔方整体翻转 0~90° (将来四臂时), 不能碰到机械臂;
4. 两种状态的结构统计: 机械臂的弯矩走转盘 (不走马达输出盘)。
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # check.CATALOG_NAME 里的 "import model" 要找到 v2 的 model
sys.path.append(os.path.join(HERE, ".."))

import numpy as np  # noqa: E402

import check  # noqa: E402
import model  # noqa: E402

check.CONNECTOR_LEN.update(model.CONNECTOR_LEN)
_allowed_v1 = check._allowed


def _allowed(a, b):
    """转盘上下两半在官方模型里就是同一个原点、互相卡在一起, 不算干涉。"""
    if {a.name, b.name} == {"18938.dat", "18939.dat"}:
        return True
    return _allowed_v1(a, b)


check._allowed = _allowed


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


def rotation_sweep():
    n = 0
    for ang in range(15, 360, 15):
        ps = model.build(head_angle=ang, with_cube=False)
        for a, b, k in check.collisions(ps):
            if model.is_head(a) != model.is_head(b):
                n += 1
                print(f"[转 {ang}°] 干涉: {check.CATALOG_NAME(a)} <-> {check.CATALOG_NAME(b)} ({k} 点)")
    return n


def cube_flip():
    n = 0
    for ang in range(10, 91, 10):
        ps = model.build(fork_extended=False)
        head = [p for p in ps if model.is_head(p)]
        cube = [p for p in ps if p.name == "cube56.dat"][0]
        a = math.radians(ang)
        cube.rot = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
        for x, y, k in check.collisions(head + [cube]):
            n += 1
            print(f"[魔方翻转 {ang}°] 干涉: {check.CATALOG_NAME(x)} <-> {check.CATALOG_NAME(y)} ({k} 点)")
    return n


def load_path():
    """机械臂和马达之间只有传动轴 (十字轴) 相连: 输出盘的 4 个销孔不用, 马达不承受机械臂的弯矩。"""
    ps = model.build()
    motor = [p for p in ps if p.name == "95658.dat"][0]
    hub_pins = [q for q, _ in check.EXTRA_HOLES["95658.dat"]]
    n = 0
    for c in ps:
        if c.kind != "pin":
            continue
        for q in hub_pins:
            w = motor.world(q)
            if np.linalg.norm(c.pos - w) < 25:
                n += 1
                print(f"[传力] {check.CATALOG_NAME(c)} 插在马达输出盘销孔上, 机械臂弯矩会走马达")
    return n


if __name__ == "__main__":
    total = 0
    total += report(model.build(), "夹紧")
    total += report(model.build(fork_extended=False), "松开")
    total += rotation_sweep()
    total += cube_flip()
    total += load_path()
    print("问题数:", total)
    sys.exit(1 if total else 0)
