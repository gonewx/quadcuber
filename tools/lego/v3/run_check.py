"""v3 模型检查 (在 tools/lego/v3 目录下运行):
    python run_check.py module travel all   单模块夹紧/松开、夹指中间行程、整机
    python four_arm.py                      四臂转动干涉扫描和魔方扫掠间隙
"""
import itertools
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.append(os.path.join(HERE, ".."))

import numpy as np  # noqa: E402

import check  # noqa: E402
import model  # noqa: E402

check.CONNECTOR_LEN.update(model.CONNECTOR_LEN)


def _axis_dist(a, b_pt, b_ax):
    return np.linalg.norm(np.cross(a - b_pt, b_ax))


def _allowed(a, b):
    """有意的 "干涉":
    - 转盘上下两半本来就互相卡在一起;
    - 舵机十字输出轴插在曲柄 (2 孔细梁) 的十字孔里;
    - 36 齿齿轮和转盘上半的齿啮合 (齿轮轴线离转盘轴线 120 = 两个节圆半径之和)。"""
    names = {a.name, b.name}
    if names == {"18938.dat", "18939.dat"}:
        return True
    if names == {"geekservo.dat", "41677.dat"}:
        servo, crank = (a, b) if a.name == "geekservo.dat" else (b, a)
        out_pt = servo.world((10, -43, 0))
        out_ax = servo.rot @ np.array([0, 1.0, 0])
        return _axis_dist(crank.world((0, 0, 0)), out_pt, out_ax) < 1.0
    if names == {"32498.dat", "18938.dat"}:
        g, t = (a, b) if a.name == "32498.dat" else (b, a)
        ga, ta = g.rot[:, 2], t.rot[:, 1]
        d = _axis_dist(g.pos, t.pos, ta)
        return abs(abs(ga @ ta) - 1) < 1e-6 and abs(d - 120) < 1.0
    return False


check._allowed = _allowed


def report(parts, label):
    n = 0
    for a, b, k in check.collisions(parts):
        n += 1
        print(f"[{label}] 干涉: {check.CATALOG_NAME(a)}({a.arm}) {a.pos.round(1).tolist()} <-> "
              f"{check.CATALOG_NAME(b)}({b.arm}) {b.pos.round(1).tolist()} ({k} 点)")
    for p in check.connections(parts):
        n += 1
        print(f"[{label}] 连接: {p}")
    for p in check.long_pins(parts):
        n += 1
        print(f"[{label}] 长销: {p}")
    return n


if __name__ == "__main__":
    only = sys.argv[1:] or ["module", "travel", "all"]
    total = 0
    if "module" in only:
        model.STEPS.clear()
        ps = model.module(0.0, 0.0)
        for p in ps:
            p.arm = "L"
        total += report(ps, "单模块 夹紧")
        model.STEPS.clear()
        ps = model.module(model.OPEN_S, 0.0)
        for p in ps:
            p.arm = "L"
        total += report(ps, "单模块 松开")
    if "travel" in only:
        # 夹指从夹紧到松开的中间位置 (只查干涉)
        for k in range(1, 8):
            s = model.OPEN_S * k / 8
            model.STEPS.clear()
            ps = model.module(s, 0.0)
            for a, b, n in check.collisions(ps):
                total += 1
                print(f"[行程 s={s:.1f}] 干涉: {check.CATALOG_NAME(a)} <-> {check.CATALOG_NAME(b)} ({n} 点)")
    if "all" in only:
        ps = model.build()
        total += report(ps, "整机 夹紧")
    print("问题数:", total)
    sys.exit(1 if total else 0)
