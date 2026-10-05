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
import ldraw  # noqa: E402
import model  # noqa: E402

check.CONNECTOR_LEN.update(model.CONNECTOR_LEN)


def _axis_dist(a, b_pt, b_ax):
    return np.linalg.norm(np.cross(a - b_pt, b_ax))


def _allowed(a, b):
    """有意的 "干涉":
    - 转盘上下两半本来就互相卡在一起;
    - 舵机十字输出轴插在曲柄 (2 孔细梁) 的十字孔里;
    - 24 齿直齿轮和转盘上半的齿啮合 (齿轮轴线离转盘轴线 100; 用户实测 24 齿在这个距离咬合最好);
    - 前端轮胎压进魔方面 (名义压缩量)。"""
    names = {a.name, b.name}
    if names == {"18938.dat", "18939.dat"}:
        return True
    # 轮胎对魔方的名义压缩每侧约 0.32mm；层界与回位另由 verify_pressure_pads.py 检查。
    if names == {"50945_nominal.dat", "cube56.dat"}:
        return True
    if names == {"42610.dat", "50945_nominal.dat"}:
        return np.linalg.norm(a.pos - b.pos) < 1e-6 and abs(abs(a.rot[:, 2] @ b.rot[:, 2]) - 1) < 1e-6
    if names == {"geekservo.dat", "41677.dat"}:
        servo, crank = (a, b) if a.name == "geekservo.dat" else (b, a)
        out_pt = servo.world((10, -43, 0))
        out_ax = servo.rot @ np.array([0, 1.0, 0])
        return _axis_dist(crank.world((0, 0, 0)), out_pt, out_ax) < 1.0
    if names == {"3648b.dat", "18938.dat"}:
        g, t = (a, b) if a.name == "3648b.dat" else (b, a)
        ga, ta = g.rot[:, 2], t.rot[:, 1]
        d = _axis_dist(g.pos, t.pos, ta)
        return abs(abs(ga @ ta) - 1) < 1e-6 and abs(d - 100) < 1.0
    return False


check._allowed = _allowed

# 销中间的挡环 (销局部 x): 挡环过不了孔, 所以销只能先插进一边的零件, 再把另一边的零件沿销轴压上去。
COLLAR = {"32002.dat": 0.0, "2780.dat": 0.0, "3673.dat": 0.0, "3749.dat": 0.0, "6558.dat": -10.0, "32556a.dat": -10.0}


def pin_depth(parts):
    """按孔段的实际长度 (不是无限长的孔线) 检查每个销是否真的插进了至少两个零件。
    check.connections 用无限长的孔线判断, 销悬在空中、只是对准了远处的孔也会被当成连上 (第一版马达前板就是这样漏掉的)。"""
    solids = [p for p in parts if p.kind == "solid"]
    boxes = {id(p): check._obb(p) for p in solids}
    out = []
    for c in parts:
        if c.kind != "pin" or c.name == "32054.dat":
            continue
        layers = check._pin_layers(c, solids, None, boxes)
        if len(layers) < 2:
            out.append(f"{check.CATALOG_NAME(c)} @ {np.round(c.pos, 1).tolist()}: 按孔的实际深度只插进了 "
                       f"{len(layers)} 个零件 {[check.CATALOG_NAME(s) for s, _, _ in layers]}")
    return out


def pins_in_axle_holes(parts):
    """圆销 (摩擦销、无摩擦销、长销) 插进了十字孔: 插不进去。连接检查只看孔的轴线, 分不出圆孔和十字孔
    (第 16 步把无摩擦长销穿进 32039 横着的十字孔就是这样漏掉的, 2026-09-29 用户实物发现)。
    判断方法: 在销插进这个零件的那一段, 离轴线 3.5 LDU 取一圈点。十字孔的四个斜角方向是实体、四个正方向是空的;
    圆孔 (半径 6) 各方向都是空的。"""
    solids = [p for p in parts if p.kind == "solid"]
    boxes = {id(p): check._obb(p) for p in solids}
    out = []
    for c in parts:
        if c.kind != "pin" or c.name == "3749.dat":  # 3749 半销半轴, 轴那一半本来就插十字孔
            continue
        u = c.rot[:, 0]
        for s, lo, hi in check._pin_layers(c, solids, None, boxes):
            S = check.Solid(s.name)
            hits = 0
            for t in np.linspace(lo + 3, hi - 3, 3):
                ctr = s.rot.T @ (c.pos + t * u - s.pos)
                ax = s.rot.T @ u
                e1 = np.cross(ax, [0, 1, 0] if abs(ax[1]) < 0.9 else [1, 0, 0])
                e1 /= np.linalg.norm(e1)
                e2 = np.cross(ax, e1)
                # 十字的方向不知道, 取 8 个方向: 十字孔有 4 个实体 4 个空, 圆孔全空
                pts = np.array([ctr + 3.5 * (math.cos(a) * e1 + math.sin(a) * e2) for a in np.radians(np.arange(0, 360, 45))])
                inside = S.inside(pts, deep=False)
                if inside.sum() == 4 and all(inside[k] != inside[k + 1] for k in range(7)):
                    hits += 1
            if hits >= 2:
                out.append(f"{check.CATALOG_NAME(c)} @ {np.round(c.pos, 1).tolist()}: 插在 {check.CATALOG_NAME(s)} 的十字孔里")
    return out


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


def shared_holes(parts):
    """两个销/轴插在同一个孔里、长度上重叠 (比如底座梁的销已经占满大框的竖孔, 后面的步骤又要往这个孔里插销;
    2026-09-29 用户第 8 步实物发现)。碰撞检查不管销和销之间, 所以单独查: 轴线重合且重叠超过 2 LDU 就报。"""
    # (名字, 中心, 轴线, 长度); 零件自带的销 (55615 的 4 个销) 也算进来 (2026-09-30 用户发现 55615 的销插进了垫块销占着的孔)
    cs = [(check.CATALOG_NAME(c), c.pos + sum(check.connector_bounds(c.name)) / 2 * c.rot[:, 0], c.rot[:, 0], check.connector_bounds(c.name)[1] - check.connector_bounds(c.name)[0]) for c in parts if c.name in check.CONNECTOR_LEN]
    for c in parts:
        for (cpt, cax) in BUILTIN_PINS.get(c.name, ()):
            cs.append((check.CATALOG_NAME(c) + " 自带的销", c.world(cpt), c.rot @ np.array(cax, float), 20.0))
    problems = []
    for i, (na, pa, ax, La) in enumerate(cs):
        for (nb, pb, bx, Lb) in cs[i + 1:]:
            if abs(abs(ax @ bx) - 1) > 1e-3 or np.linalg.norm(np.cross(pb - pa, ax)) > 1.5:
                continue
            t = (pb - pa) @ ax
            overlap = min(La / 2, t + Lb / 2) - max(-La / 2, t - Lb / 2)
            if overlap > 2:
                problems.append(f"{na} {np.round(pa, 1).tolist()} 和 {nb} {np.round(pb, 1).tolist()} 在同一个孔里重叠 {overlap:.0f} LDU")
    return problems


# 零件自带的销: 零件局部坐标里销段的中点和轴线 (销长 20)。55615 的销从本体表面伸出 1 孔 (LDraw 55615.dat 的 connect7 位置)。
BUILTIN_PINS = {"55615.dat": [((0, 0, -20), (0, 0, 1)), ((0, -40, -20), (0, 0, 1)),
                              ((0, 20, 0), (0, 1, 0)), ((0, 20, 40), (0, 1, 0))]}


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
    for p in pin_depth(parts):
        n += 1
        print(f"[{label}] 插深: {p}")
    for p in collar_pins(parts):
        n += 1
        print(f"[{label}] 插销: {p}")
    for p in pins_in_axle_holes(parts):
        n += 1
        print(f"[{label}] 十字孔: {p}")
    for p in shared_holes(parts):
        n += 1
        print(f"[{label}] 同孔: {p}")
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
    # 体素侵蚀会漏掉浅穿入；该轴与推杆必须另查连续回转包络。
    from mechanical_audit import rod_check
    rod_result = rod_check()
    if rod_result['状态'] == '失败':
        total += 1
        worst = rod_result['最差']
        print(f"[连续回转] 32062 曲柄轴侵入 3708 推杆回转包络："
              f"余量 {worst['回转包络径向余量_mm']:.3f}mm，"
              f"行程 {worst['行程比例']:.3%}。见 mechanical_audit.py。")
    print("问题数:", total)
    sys.exit(1 if total else 0)
