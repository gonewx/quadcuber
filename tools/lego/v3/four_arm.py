"""四臂干涉检查: python four_arm.py   (在 tools/lego/v3 目录下运行)

只检查 "L 模块的转动部分" 和 "相邻的 F、B 模块全部零件" 之间的干涉 (模块自身和底座由 run_check.py 检查,
R 模块离得远)。四个模块是同一个模块绕竖直轴转出来的, 所以只扫 L 一个就覆盖了所有相邻关系。

扫描: L 夹紧 / 松开, 转角 0°~90° 每 5° 一格; F、B 各取 4 种状态 (夹紧/松开 × 竖直/水平)。
结论写进 docs/lego/v3/README.md: 相邻两个机械手不能同时处于水平附近。

另外按魔方的扫掠范围检查间隙 (56mm 魔方按尖角算, 截面对角线半径 99 LDU):
- 拧 L 层: L 层 (x 在 -70 ~ -23) 转一圈扫过半径 99 的圆柱, F、B 夹紧竖直时, 它们的零件不能进入这个范围;
- 整体翻转: L、R 夹着整个魔方转, F、B 松开竖直, 它们的零件不能进入 |x| <= 70、半径 99 的圆柱。
"""
import itertools
import sys

import numpy as np

import run_check  # noqa: F401  (装好豁免规则和连接件长度)
import check
import model

NEI = {"closed0": (0.0, 0.0), "open0": (model.OPEN_S, 0.0), "closed90": (0.0, 90.0), "open90": (model.OPEN_S, 90.0)}


def cross_hits(parts, mover="L"):
    """mover 的转动部分和其他机械手零件之间的干涉。"""
    solids = [p for p in parts if p.kind == "solid" and p.arm is not None]
    a_list = [p for p in solids if p.arm == mover and p.head]
    b_list = [p for p in solids if p.arm != mover]
    boxes = {id(p): check._obb(p) for p in a_list + b_list}
    hits = []
    for a in a_list:
        alo, ahi = boxes[id(a)]
        for b in b_list:
            blo, bhi = boxes[id(b)]
            if np.any(alo > bhi - 1) or np.any(blo > ahi - 1):
                continue
            n = 0
            for x, y in ((a, b), (b, a)):
                sx, sy = check.Solid(x.name), check.Solid(y.name)
                w = sx.samples @ x.rot.T + x.pos
                n += int(sy.inside((w - y.pos) @ y.rot).sum())
            if n > 3:
                hits.append((a, b, n))
    return hits


CUBE_R = 99.0  # 56mm 魔方截面对角线的一半 (尖角, 实际魔方有圆角, 更小)
LAYER = 23.3  # 一层的厚度 (70 / 3 的 1 倍)


def min_radius(parts, arms, xlo, xhi):
    """arms 的零件在 xlo <= x <= xhi 范围内离 X 轴 (L-R 轴) 的最近距离。"""
    best = 1e9
    for p in parts:
        if p.arm is None or p.arm not in arms or p.kind != "solid":
            continue
        w = check.Solid(p.name).samples @ p.rot.T + p.pos
        sel = (w[:, 0] >= xlo) & (w[:, 0] <= xhi)
        if sel.any():
            best = min(best, float(np.hypot(w[sel, 1], w[sel, 2]).min()))
    return best


def sweep_clearance():
    n = 0
    ps = model.build({"F": (0.0, 0.0), "B": (0.0, 0.0)}, with_cube=False)
    r = min_radius(ps, "FB", -model.CUBE_HALF - 2, -model.CUBE_HALF + LAYER + 2)
    print(f"拧 L 层 (F、B 夹紧竖直): 最近零件离轴 {r:.1f} LDU, 魔方层扫掠半径 {CUBE_R}, 余量 {(r - CUBE_R) * 0.4:.1f}mm")
    n += r < CUBE_R + 2
    ps = model.build({"F": (model.OPEN_S, 0.0), "B": (model.OPEN_S, 0.0)}, with_cube=False)
    r = min_radius(ps, "FB", -model.CUBE_HALF - 2, model.CUBE_HALF + 2)
    print(f"整体翻转 (F、B 松开竖直): 最近零件离轴 {r:.1f} LDU, 魔方扫掠半径 {CUBE_R}, 余量 {(r - CUBE_R) * 0.4:.1f}mm")
    n += r < CUBE_R + 2
    return n


def main():
    bad = []  # (L 状态, 角度, F 状态, B 状态, 干涉)
    for lo in (0.0, model.OPEN_S):
        for ang in range(0, 91, 5):
            for fs, bs in itertools.product(NEI, NEI):
                parts = model.build({"L": (lo, ang), "F": NEI[fs], "B": NEI[bs], "R": (0.0, 0.0)}, with_cube=False)
                h = cross_hits(parts)
                if h:
                    bad.append(("松开" if lo else "夹紧", ang, fs, bs, h))
    # 期望: 只有邻居是水平 (…90) 且 L 转到水平附近时才干涉
    unexpected = [b for b in bad if not (b[2].endswith("90") or b[3].endswith("90"))]
    first = {}
    for st, ang, fs, bs, h in bad:
        for side, s in (("F", fs), ("B", bs)):
            if s.endswith("90") and any(y.arm == side for _, y, _ in h):
                key = (st, side, s)
                first[key] = min(first.get(key, 999), ang)
    print("会干涉的组合 (L 从竖直转向水平, 从这个角度开始碰到水平的邻居):")
    for k in sorted(first):
        print(f"  L {k[0]}, 邻居 {k[1]} = {k[2]}: 从 {first[k]}° 起")
    free = sorted({ang for st, ang, fs, bs, h in bad} ^ set(range(0, 91, 5)))
    for st, ang, fs, bs, h in unexpected:
        a, b, n = h[0]
        print(f"意外干涉: L {st} {ang}° F={fs} B={bs}: {check.CATALOG_NAME(a)} <-> {check.CATALOG_NAME(b)}({b.arm}) {n} 点")
    # 邻居都竖直时, L 在任何角度 (含水平) 都不能碰到邻居
    print("邻居都竖直时的干涉组合数:", len(unexpected))
    return len(unexpected) + sweep_clearance()


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
