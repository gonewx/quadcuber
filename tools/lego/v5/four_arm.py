"""四臂干涉检查: python four_arm.py   (在 tools/lego/v5 目录下运行)

只检查 "L 模块的转动部分" 和 "相邻的 F、B 模块全部零件" 之间的干涉 (模块自身和底座由 run_check.py 检查,
R 模块离得远)。四个模块是同一个模块绕竖直轴转出来的, 所以只扫 L 一个就覆盖了所有相邻关系。

扫描: L 夹紧 / 松开, 转角 0°~355° 每 5° 一格; F、B 各取 4 种状态 (夹紧/松开 × 竖直/水平)。
碰撞按机械手对独立计算, 两个邻居使用同状态即可覆盖每一对关系, 混合组合不会产生额外的成对碰撞。
结论写进 docs/lego/v5/README.md: 相邻两个机械手不能同时处于水平附近。

另外按魔方的扫掠范围检查间隙 (56mm 魔方按尖角算, 截面对角线半径 99 LDU):
- 拧 L 层: L 层 (x 在 -70 ~ -23) 转一圈扫过半径 99 的圆柱, F、B 夹紧竖直时, 它们的零件不能进入这个范围;
- 整体翻转: L、R 夹着整个魔方转, F、B 松开竖直, 它们的零件不能进入 |x| <= 70、半径 99 的圆柱。
"""
import sys

import numpy as np

import run_check  # noqa: F401  (装好豁免规则和连接件长度)
import check
import model

NEI = {"closed0": (0.0, 0.0), "open0": (model.OPEN_S, 0.0), "closed90": (0.0, 90.0), "open90": (model.OPEN_S, 90.0)}


def cross_hits(parts, mover="L"):
    """转动部分与相邻机械手、以及本臂固定件的干涉。"""
    solids = [p for p in parts if p.kind in ("solid", "axle", "pin", "bush") and p.arm is not None]
    a_list = [p for p in solids if p.arm == mover and p.head]
    b_list = [p for p in solids if p.arm != mover or not p.head]
    boxes = {id(p): check._obb(p) for p in a_list + b_list}
    hits = []
    b_lo = np.array([boxes[id(b)][0] for b in b_list])
    b_hi = np.array([boxes[id(b)][1] for b in b_list])
    if not b_list:
        return hits
    for a in a_list:
        alo, ahi = boxes[id(a)]
        candidates = np.flatnonzero(np.all(alo <= b_hi - 1, axis=1) & np.all(b_lo <= ahi - 1, axis=1))
        for bi in candidates:
            b = b_list[bi]
            if a.arm == b.arm and check._allowed(a, b):
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
LAYER = 2 * model.CUBE_HALF / 3  # 一层 = 完整边长 / 3, 不能用半边长 / 3


def min_radius(parts, arms, xlo, xhi):
    """arms 的零件在 xlo <= x <= xhi 范围内离 X 轴 (L-R 轴) 的最近距离。"""
    best = 1e9
    for p in parts:
        if p.arm is None or p.arm not in arms or p.kind not in ("solid", "axle", "pin", "bush"):
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
    print(f"拧 L 层 (F、B 夹紧竖直): 最近零件离轴 {r:.1f} LDU, 魔方层扫掠半径 {CUBE_R}, 切片径向余量 {(r - CUBE_R) * 0.4:.1f}mm（非三维最小距离，完整结果见 mechanical_audit.json）")
    n += r < CUBE_R + 2
    ps = model.build({"F": (model.OPEN_S, 0.0), "B": (model.OPEN_S, 0.0)}, with_cube=False)
    r = min_radius(ps, "FB", -model.CUBE_HALF - 2, model.CUBE_HALF + 2)
    print(f"整体翻转 (F、B 松开竖直): 最近零件离轴 {r:.1f} LDU, 魔方扫掠半径 {CUBE_R}, 切片径向余量 {(r - CUBE_R) * 0.4:.1f}mm（非三维最小距离，完整结果见 mechanical_audit.json）")
    n += r < CUBE_R + 2
    return n


def main():
    unexpected = []
    horizontal = set()
    checked = 0
    for lo in (0.0, model.OPEN_S):
        for ang in range(0, 360, 5):
            for label, neighbor in NEI.items():
                parts = model.build({"L": (lo, ang), "F": neighbor, "B": neighbor, "R": (0.0, 0.0)}, with_cube=False)
                hits = cross_hits(parts)
                checked += 1
                if label.endswith("90"):
                    horizontal.update((a.arm, b.arm) for a, b, _ in hits)
                elif hits:
                    unexpected.append((lo, ang, label, hits))
    print(f"扫描 {checked} 个状态, 转角 0°～355°, 步长 5°; 按机械手对覆盖相邻状态组合。")
    for lo, ang, label, hits in unexpected:
        a, b, n = hits[0]
        print(f"意外干涉: L {'松开' if lo else '夹紧'} {ang}°, 邻居 {label}: {check.CATALOG_NAME(a)} <-> {check.CATALOG_NAME(b)}({b.arm}), {n} 点")
    print("邻居都竖直时的干涉状态数:", len(unexpected))
    print("相邻水平状态存在碰撞:", sorted(horizontal))
    return len(unexpected) + sweep_clearance()


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
