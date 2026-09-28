"""模型检查: 零件干涉 (穿模) 和 销/轴 连接。

- 干涉: 每个结构件按 2 LDU 体素实体化 (表面体素 + 从外部泛洪填充), 另一个零件的表面采样点
  落入其 "深内部" (离表面至少约 2 个体素) 就算干涉。贴合的两个面不会被误报。
- 连接: 销/轴沿轴线每隔 5 LDU 取样, 每个样点要么不在任何结构件内部, 要么正好在该零件某个孔的
  轴线上 (径向误差 < 1.5 LDU)。每个销至少要插进两个零件, 每根轴至少穿过两个零件或轴套。
"""

import itertools

import numpy as np
from scipy import ndimage

import ldraw

VOX = 2.0
# 马达输出盘上的 4 个销孔 (零件文件里是用圆柱基元画的, 提取不到), 以及舵机输出轴
EXTRA_HOLES = {
    "95658.dat": [((30, 20, 0), (1, 0, 0)), ((30, -20, 0), (1, 0, 0)), ((30, 0, 20), (1, 0, 0)),
                  ((30, 0, -20), (1, 0, 0))],
}


class Solid:
    _cache = {}

    def __init__(self, name):
        if name in Solid._cache:
            self.__dict__ = Solid._cache[name].__dict__
            return
        tris = ldraw.geometry(name)[0]
        lo, hi = tris.reshape(-1, 3).min(0) - 2 * VOX, tris.reshape(-1, 3).max(0) + 2 * VOX
        shape = np.ceil((hi - lo) / VOX).astype(int) + 1
        surf = np.zeros(shape, bool)
        pts = _sample(tris, VOX * 0.5)
        idx = np.floor((pts - lo) / VOX).astype(int)
        surf[idx[:, 0], idx[:, 1], idx[:, 2]] = True
        outside = ~surf
        lab, _ = ndimage.label(outside)
        border = set(np.unique(np.concatenate([lab[0].ravel(), lab[-1].ravel(), lab[:, 0].ravel(), lab[:, -1].ravel(),
                                               lab[:, :, 0].ravel(), lab[:, :, -1].ravel()])))
        border.discard(0)
        ext = np.isin(lab, list(border))
        solid = ~ext
        self.deep = ndimage.binary_erosion(solid, iterations=2)
        self.solid = solid
        self.lo = lo
        self.samples = pts[:: max(1, len(pts) // 4000)]
        Solid._cache[name] = self

    def inside(self, local_pts, deep=True):
        idx = np.floor((local_pts - self.lo) / VOX).astype(int)
        grid = self.deep if deep else self.solid
        ok = np.all((idx >= 0) & (idx < np.array(grid.shape)), axis=1)
        res = np.zeros(len(local_pts), bool)
        res[ok] = grid[idx[ok, 0], idx[ok, 1], idx[ok, 2]]
        return res


def _sample(tris, step):
    out = [tris.reshape(-1, 3)]
    for t in tris:
        a, b, c = t
        n = int(max(np.linalg.norm(b - a), np.linalg.norm(c - a), np.linalg.norm(c - b)) / step) + 1
        if n <= 1:
            out.append(((a + b + c) / 3)[None])
            continue
        u, v = np.meshgrid(np.linspace(0, 1, n + 1), np.linspace(0, 1, n + 1))
        m = u + v <= 1
        u, v = u[m], v[m]
        out.append(a + np.outer(u, b - a) + np.outer(v, c - a))
    return np.concatenate(out)


def _obb(p):
    lo, hi = ldraw.bbox(p.name)
    corners = np.array(list(itertools.product(*zip(lo, hi))))
    w = corners @ p.rot.T + p.pos
    return w.min(0), w.max(0)


def collisions(parts, tol_points=3):
    """返回 [(零件 a, 零件 b, 干涉点数)]。"""
    solids = [p for p in parts if p.kind in ("solid", "other")]
    boxes = [_obb(p) for p in solids]
    out = []
    for i, j in itertools.combinations(range(len(solids)), 2):
        (alo, ahi), (blo, bhi) = boxes[i], boxes[j]
        if np.any(alo > bhi - 1) or np.any(blo > ahi - 1):
            continue
        a, b = solids[i], solids[j]
        n = 0
        for x, y in ((a, b), (b, a)):
            sx, sy = Solid(x.name), Solid(y.name)
            w = sx.samples @ x.rot.T + x.pos
            local = (w - y.pos) @ y.rot  # 世界 -> y 的局部
            n += int(sy.inside(local).sum())
        if n > tol_points and not _allowed(a, b):
            out.append((a, b, n))
    return out


def _allowed(a, b):
    """有意的 "干涉": 舵机的十字输出轴插在曲柄 (3 孔细梁) 的十字孔里。
    只有当曲柄的十字孔正好套在输出轴上时才豁免。"""
    names = {a.name, b.name}
    if names != {"geekservo.dat", "6632.dat"}:
        return False
    servo, crank = (a, b) if a.name == "geekservo.dat" else (b, a)
    out_pt = servo.world((10, -43, 0))  # 输出轴上一点 (局部坐标)
    out_ax = servo.rot @ np.array([0, 1.0, 0])
    hole = crank.world((0, 0, 0))
    return np.linalg.norm(np.cross(hole - out_pt, out_ax)) < 1.0


def _hole_lines(p):
    lines = [(np.array(q, float), np.array(a, float)) for q, a in ldraw.holes(p.name)]
    lines += [(np.array(q, float), np.array(a, float)) for q, a in EXTRA_HOLES.get(p.name, [])]
    return [(p.world(q), p.rot @ a) for q, a in lines]


CONNECTOR_LEN = {"3705.dat": 80, "2780.dat": 40, "6558.dat": 60, "43093.dat": 40, "32054.dat": 60, "3708.dat": 240, "32073.dat": 100,
                 "3713.dat": 20, "32123a.dat": 10}


def connections(parts):
    """返回问题列表 (字符串)。"""
    problems = []
    solids = [p for p in parts if p.kind == "solid"]
    bushes = [p for p in parts if p.kind == "bush"]
    hole_cache = {id(p): _hole_lines(p) for p in solids}
    boxes = {id(p): _obb(p) for p in solids}
    for c in parts:
        if c.kind not in ("pin", "axle"):
            continue
        L = CONNECTOR_LEN[c.name]
        axis = c.rot[:, 0]
        engaged = set()
        bad = []
        for t in np.arange(-L / 2 + 2, L / 2 - 1, 5.0):
            pt = c.pos + t * axis
            for s in solids:
                lo, hi = boxes[id(s)]
                if np.any(pt < lo - 1) or np.any(pt > hi + 1):
                    continue
                local = (pt - s.pos) @ s.rot
                slo, shi = ldraw.bbox(s.name)
                if np.any(local < slo - 0.5) or np.any(local > shi + 0.5):
                    continue
                on_hole = any(abs(abs(a @ axis) - 1) < 1e-3 and np.linalg.norm(np.cross(pt - q, a)) < 1.5
                              for q, a in hole_cache[id(s)])
                if on_hole:
                    engaged.add(id(s))
                elif Solid(s.name).inside(local[None], deep=False)[0]:
                    bad.append((round(t), CATALOG_NAME(s)))
            for b in bushes:
                if np.linalg.norm(np.cross(pt - b.pos, axis)) < 1.5 and abs((pt - b.pos) @ axis) <= 10:
                    engaged.add(id(b))
        where = f"{CATALOG_NAME(c)} @ {np.round(c.pos, 1).tolist()}"
        if bad:
            problems.append(f"{where}: 穿过实体 {sorted(set(bad))[:4]}")
        if len(engaged) < 2:
            problems.append(f"{where}: 只连接了 {len(engaged)} 个零件")
    return problems


def CATALOG_NAME(p):
    import model

    return f"{model.CATALOG[p.name][0]}[步骤{p.step}]"


# 6558 长销的挡肩在局部 x = -10: 一侧 1 孔长 (-30..-10), 另一侧 2 孔长 (-10..+30)。挡肩过不了孔,
# 所以长销只能这样装: 两段分别插进挡肩两边的零件, 挡肩正好落在两层之间的接缝上。
LPIN_COLLAR = -10.0


def _pin_layers(c, solids, hole_cache, boxes):
    """沿销轴线, 每个与销啮合的实体零件占据的 t 区间 (销局部 x)。"""
    axis = c.rot[:, 0]
    L = CONNECTOR_LEN[c.name]
    spans = {}
    for t in np.arange(-L / 2 + 1, L / 2, 2.0):
        pt = c.pos + t * axis
        for s in solids:
            lo, hi = boxes[id(s)]
            if np.any(pt < lo - 1) or np.any(pt > hi + 1):
                continue
            local = (pt - s.pos) @ s.rot
            slo, shi = ldraw.bbox(s.name)
            if np.any(local < slo - 0.5) or np.any(local > shi + 0.5):
                continue
            if any(abs(abs(a @ axis) - 1) < 1e-3 and np.linalg.norm(np.cross(pt - q, a)) < 1.5
                   for q, a in hole_cache[id(s)]):
                sp = spans.setdefault(id(s), [s, t, t])
                sp[1], sp[2] = min(sp[1], t), max(sp[2], t)
    return [(s, lo - 1, hi + 1) for s, lo, hi in spans.values()]


def long_pins(parts):
    """检查每根 6558 长销能不能装上。返回问题列表 (字符串)。

    1. 挡肩必须落在两层零件的接缝上, 不能在某个零件的孔中间;
    2. 同一个零件不能同时出现在挡肩两侧 (例如马达两片耳朵之间夹一层: 挡肩要穿过一片耳朵才能到位);
    3. 挡肩两侧的零件不能在更早的步骤里已经用别的销/轴连成一体 (那样只能从一端穿, 挡肩过不去)。
    同一侧的几层事先连在一起没有关系: 从那一侧的外端插进去, 挡肩停在接缝上。
    """
    problems = []
    solids = [p for p in parts if p.kind == "solid"]
    hole_cache = {id(p): _hole_lines(p) for p in solids}
    boxes = {id(p): _obb(p) for p in solids}
    layers = {id(c): _pin_layers(c, solids, hole_cache, boxes) for c in parts if c.kind in ("pin", "axle")}

    def joined_before(step):
        """步骤 < step 的销/轴连成的零件分组 (并查集)。"""
        root = {}

        def find(x):
            while root.get(x, x) != x:
                x = root[x]
            return x

        for c in parts:
            if c.kind in ("pin", "axle") and c.step < step:
                ids = [id(s) for s, _, _ in layers[id(c)]]
                for a in ids[1:]:
                    root[find(a)] = find(ids[0])
        return find

    for c in parts:
        where = f"{CATALOG_NAME(c)} @ {np.round(c.pos, 1).tolist()}"
        if c.name == "32054.dat":
            # 带挡套长销: 局部 -30..-10 是挡套, 不能进孔; 2 孔长的销段 (-10..+30) 要穿在零件里。
            axis = c.rot[:, 0]
            inbush = []
            for s in solids:
                for a, b in ldraw.hole_segments(s.name):
                    a, b = s.world(a), s.world(b)
                    d = b - a
                    n = np.linalg.norm(d)
                    if n < 1 or abs(abs(d @ axis) / n - 1) > 1e-3:
                        continue
                    for t in np.arange(-29, LPIN_COLLAR - 0.5, 2.0):  # 挡套上的点
                        pt = c.pos + t * axis
                        u = (pt - a) @ d / n
                        if 0.5 < u < n - 0.5 and np.linalg.norm(np.cross(pt - a, d / n)) < 1.5:
                            inbush.append(s)
                            break
            if inbush:
                problems.append(f"{where}: 挡套落在 {CATALOG_NAME(inbush[0])} 的孔里, 方向反了")
            continue
        if c.name != "6558.dat":
            continue
        short = [s for s, lo, hi in layers[id(c)] if lo < LPIN_COLLAR - 0.5]
        long_ = [s for s, lo, hi in layers[id(c)] if hi > LPIN_COLLAR + 0.5]
        inside = [s for s, lo, hi in layers[id(c)] if lo < LPIN_COLLAR - 0.5 and hi > LPIN_COLLAR + 0.5]
        if inside:
            problems.append(f"{where}: 挡肩落在 {CATALOG_NAME(inside[0])} 的孔中间, 装不进去 (销的方向可能反了)")
            continue
        find = joined_before(c.step)
        pre = [(a, b) for a in short for b in long_ if find(id(a)) == find(id(b))]
        if pre:
            a, b = pre[0]
            problems.append(f"{where}: 挡肩两侧的 {CATALOG_NAME(a)} 和 {CATALOG_NAME(b)} 在之前的步骤里已经连成一体, "
                            "只能从一端穿过, 挡肩过不去")
    return problems
