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

# 销中间的挡环 (销局部 x): 挡环过不了孔, 所以销只能先插进一边的零件, 再把另一边的零件沿销轴压上去。
COLLAR = {"2780.dat": 0.0, "3673.dat": 0.0, "3749.dat": 0.0, "6558.dat": -10.0, "32556a.dat": -10.0}


def collar_pins(parts):
    """按搭建步骤模拟装配, 检查带挡环的销能不能装上。返回问题列表。

    两组已经各自连成一体的零件, 用带挡环的销连接时, 只能沿销轴把一组压到另一组上。
    所以两组之间的全部销必须同轴向、同方向 (从 A 组指向 B 组); 否则 (比如一个零件夹在同一个零件的
    两条边之间、两头都要插销) 从外面插, 销只能进一半, 装不上。
    同一步骤里的零件按能装的顺序尝试 (贪心): 先合并方向一致的组, 最后剩下的就是装不上的。
    轴没有挡环, 可以事后穿进去, 不参与方向判断。
    """
    solids = [p for p in parts if p.kind == "solid"]
    boxes = {id(p): check._obb(p) for p in solids}
    root = {}

    def find(x):
        while root.get(x, x) != x:
            x = root[x]
        return x

    def union(a, b):
        root[find(a)] = find(b)

    problems = []
    info = []  # (步骤, 销, [(A 侧零件)], [(B 侧零件)])
    axles = []
    for c in parts:
        if c.kind not in ("pin", "axle"):
            continue
        layers = check._pin_layers(c, solids, None, boxes)
        if c.name in COLLAR:
            k = COLLAR[c.name]
            a = [s for s, lo, hi in layers if hi <= k + 0.5]
            b = [s for s, lo, hi in layers if lo >= k - 0.5]
            mid = [s for s, lo, hi in layers if lo < k - 0.5 and hi > k + 0.5]
            if mid:
                problems.append(f"{check.CATALOG_NAME(c)} @ {np.round(c.pos, 1).tolist()}: 挡环落在 "
                                f"{check.CATALOG_NAME(mid[0])} 的孔中间")
                continue
            info.append((c.step, c, a, b))
        else:
            axles.append((c.step, [s for s, _, _ in layers]))
    for step in sorted({i[0] for i in info} | {a[0] for a in axles}):
        todo = [i for i in info if i[0] == step and i[2] and i[3]]
        while todo:
            pairs = {}
            for st, c, a, b in todo:
                ga, gb = find(id(a[0])), find(id(b[0]))
                for s in a[1:] + b[1:]:
                    pass
                if ga == gb:
                    continue
                u = c.rot[:, 0]
                key, d = ((ga, gb), u) if ga < gb else ((gb, ga), -u)
                pairs.setdefault(key, []).append((d, c))
            todo = [i for i in todo if find(id(i[2][0])) != find(id(i[3][0]))]
            if not pairs:
                break
            ok = [k for k, v in pairs.items() if all(np.allclose(d, v[0][0]) for d, _ in v)]
            if ok:
                union(*ok[0])
                continue
            for k, v in pairs.items():
                dirs = sorted({tuple(np.round(d, 2)) for d, _ in v})
                c = v[0][1]
                problems.append(f"{check.CATALOG_NAME(c)} @ {np.round(c.pos, 1).tolist()} 等 {len(v)} 个销: "
                                f"两组零件之间的销方向不一致 {dirs}, 只能从外面插, 挡环挡住插不到位")
                union(*k)
        # 同一个销两侧各自的多层, 以及轴, 在这一步结束时并进去
        for st, c, a, b in info:
            if st == step:
                for s in a[1:]:
                    union(id(s), id(a[0]))
                for s in b[1:]:
                    union(id(s), id(b[0]))
                if a and b:
                    union(id(a[0]), id(b[0]))
        for st, ss in axles:
            if st == step:
                for s in ss[1:]:
                    union(id(s), id(ss[0]))
    return problems


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
    for p in collar_pins(parts):
        n += 1
        print(f"[{label}] 插销: {p}")
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
