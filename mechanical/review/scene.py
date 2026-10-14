"""整机场景：按状态组装各零件的世界三角网格（mm），并计算零件集之间的最小间隙。"""
import functools
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import candidate as C  # noqa: E402

# 原型新增零件（官方 LDraw 原文件）只给核算用，不进入发布模型的资产表。
for _p in (Path(__file__).resolve().parent / 'parts').glob('*.dat'):
    C.files.setdefault(_p.name, _p.read_text().splitlines())
from review.meshdist import TriGrid, edge_samples, seg_tri_cross  # noqa: E402

H = 0.3  # 边采样间距 mm；最小距离误差约 H/2


@functools.lru_cache(None)
def local_samples(name):
    return edge_samples(C.mesh(name) * .4, H)


def tris(p):
    return C.world(p)


def samples(p):
    return local_samples(p.name) @ p.rot.T + p.pos * .4


class Item:
    __slots__ = ('part', 'group', 'label', 'T', 'lo', 'hi')

    def __init__(self, part, group, label):
        self.part, self.group, self.label = part, group, label
        self.T = tris(part)
        self.lo, self.hi = self.T.reshape(-1, 3).min(0), self.T.reshape(-1, 3).max(0)


def arm_items(state, front='previous'):
    """state: {arm: (open_s, angle_deg)}。返回四臂零件（含编号，1 起，与 candidate.module 一致）。"""
    out = []
    for arm in C.m.ARMS:
        s, a = state.get(arm, (0., 0.))
        mm = C.module(s, a, front=front)
        for i, p in enumerate(mm, 1):
            q = p.moved(C.m.ARM_ROT[arm])
            out.append(Item(q, f'{arm}:{"head" if p.head else "fixed"}', f'{arm}#{i} {p.name} {p.note}'.strip()))
    return out


def support_items(drop):
    return [Item(p, 'support', f'support {p.name} {p.note}') for p in C.core_parts(drop)]


def base_items():
    return [Item(p, 'base', f'base {p.name} {p.note}') for p in C.retained_base()]


def pair_clearance(a, b, rmax=6.0):
    """两个零件的最小间隙（mm）与是否穿透。超过 rmax 记为 inf。"""
    if np.any(a.lo - rmax > b.hi) or np.any(b.lo - rmax > a.hi):
        return np.inf, False
    best = np.inf
    cross = False
    for x, y in ((a, b), (b, a)):
        lo, hi = y.lo - rmax, y.hi + rmax
        P = samples(x.part)
        P = P[np.all((P >= lo) & (P <= hi), axis=1)]
        T = y.T[np.all((y.T.max(1) >= x.lo - rmax) & (y.T.min(1) <= x.hi + rmax), axis=1)]
        if not len(P) or not len(T):
            continue
        d, _ = TriGrid(T, rmax).query(P)
        best = min(best, float(d.min()))
    if best < 0.2:
        cross = penetrates(a, b) or penetrates(b, a)
    return best, cross


def penetrates(a, b):
    """a 的某条棱是否穿过 b 的某个三角形内部（排除仅接触）。"""
    lo, hi = np.maximum(a.lo, b.lo) - .01, np.minimum(a.hi, b.hi) + .01
    if np.any(lo > hi):
        return False
    Ta = a.T[np.all((a.T.max(1) >= lo) & (a.T.min(1) <= hi), axis=1)]
    Tb = b.T[np.all((b.T.max(1) >= lo) & (b.T.min(1) <= hi), axis=1)]
    if not len(Ta) or not len(Tb):
        return False
    segs = np.concatenate([Ta[:, [0, 1]], Ta[:, [1, 2]], Ta[:, [2, 0]]])
    g = TriGrid(Tb, 0.5)
    mid = segs.mean(1)
    # 候选：线段中点附近 0.5mm 网格内的三角形（线段长度一般 < 1mm，长线段另行分段）
    L = np.linalg.norm(segs[:, 1] - segs[:, 0], axis=1)
    n = np.maximum(1, np.ceil(L / 0.4).astype(int))
    reps = np.repeat(np.arange(len(segs)), n)
    k = np.arange(n.sum()) - np.repeat(np.cumsum(n) - n, n)
    t0, t1 = (k / np.repeat(n, n))[:, None], ((k + 1) / np.repeat(n, n))[:, None]
    S0 = segs[reps, 0] + t0 * (segs[reps, 1] - segs[reps, 0])
    S1 = segs[reps, 0] + t1 * (segs[reps, 1] - segs[reps, 0])
    c = np.floor(((S0 + S1) / 2 - g.origin) / g.r).astype(np.int64)
    key = g._key(c[:, 0], c[:, 1], c[:, 2])
    lo_i = np.searchsorted(g.keys, key, 'left')
    hi_i = np.searchsorted(g.keys, key, 'right')
    cnt = hi_i - lo_i
    sel = np.nonzero(cnt)[0]
    if not len(sel):
        return False
    m = cnt[sel]
    si = np.repeat(sel, m)
    off = np.arange(m.sum()) - np.repeat(np.cumsum(m) - m, m)
    ti = g.ti[np.repeat(lo_i[sel], m) + off]
    T = g.tris[ti]
    hit = seg_tri_cross(S0[si], S1[si], T[:, 0], T[:, 1], T[:, 2])
    return bool(hit.any())


def front_clearance(A, B, rmax=6.0, top=8, skip=None):
    """A 中每个零件对 B 的最小间隙：每个 A 零件只建一次网格（B 中靠近它的零件合并）。返回 [(d, 穿透, a, b)]。"""
    res = []
    for a in A:
        near = [b for b in B if b is not a and not (skip and skip(a, b))
                and not (np.any(a.lo - rmax > b.hi) or np.any(b.lo - rmax > a.hi))]
        if not near:
            continue
        lo, hi = a.lo - rmax, a.hi + rmax
        Ts, own = [], []
        for k, b in enumerate(near):
            T = b.T[np.all((b.T.max(1) >= lo) & (b.T.min(1) <= hi), axis=1)]
            Ts.append(T)
            own.append(np.full(len(T), k))
        T = np.concatenate(Ts)
        own = np.concatenate(own)
        best = np.full(len(near), np.inf)
        if len(T):
            P = samples(a.part)
            P = P[np.all((P >= T.reshape(-1, 3).min(0) - rmax) & (P <= T.reshape(-1, 3).max(0) + rmax), axis=1)]
            if len(P):
                d, ti = TriGrid(T, rmax).query(P)
                ok = np.isfinite(d)
                np.minimum.at(best, own[ti[ok]], d[ok])
        ga = TriGrid(a.T, rmax)
        for k, b in enumerate(near):
            Q = samples(b.part)
            Q = Q[np.all((Q >= lo) & (Q <= hi), axis=1)]
            if len(Q):
                best[k] = min(best[k], float(ga.query(Q)[0].min()))
        for k, b in enumerate(near):
            if np.isfinite(best[k]):
                x = bool(best[k] < 0.2 and (penetrates(a, b) or penetrates(b, a)))
                res.append((float(best[k]), x, a.label, b.label))
    res.sort(key=lambda r: r[0])
    return res[:top] if top else res


def set_clearance(A, B, rmax=6.0, top=8, skip=None):
    """零件集 A 与 B 之间最小间隙；返回按间隙排序的前 top 对。skip(a,b) 为 True 的配合对跳过。"""
    res = []
    for a in A:
        for b in B:
            if a is b or (skip and skip(a, b)):
                continue
            d, x = pair_clearance(a, b, rmax)
            if np.isfinite(d):
                res.append((d, x, a.label, b.label))
    res.sort(key=lambda r: r[0])
    return res[:top]
