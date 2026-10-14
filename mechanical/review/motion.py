"""整机运动干涉：静态姿态、夹指开合、机械头部分回转（逐角度＋局部加密）、整圈回转（子午面法，精确）。

整圈回转：零件绕机械臂轴线转一整圈扫出的实体是回转体。障碍点到回转体的距离等于它在子午面 (a, ρ) 内
到运动零件表面点集的二维距离（a 为沿轴坐标、ρ 为离轴距离），因此只需二维最近点搜索。
"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from review.scene import C, Item, samples, support_items, base_items, front_clearance  # noqa: E402

OPEN_S = C.m.OPEN_S
AXIS = {'L': np.array([1., 0, 0]), 'R': np.array([1., 0, 0]), 'F': np.array([0, 0, 1.]), 'B': np.array([0, 0, 1.])}
ADJ = {'L': 'FB', 'R': 'FB', 'F': 'LR', 'B': 'LR'}


def front_ids(front):
    if front == 'wheel':
        return set(range(137, 155)) | set(range(168, 184))
    if front == 'rot90':
        return set(range(137, 155)) | set(range(168, 170))
    return set(range(137, 155))


def machine(state, drop, front):
    """返回 [(arm, index1, Item)]；arm 为 None 表示底盘/支承。"""
    out = []
    for arm in C.m.ARMS:
        s, a = state.get(arm, (0., 0.))
        for i, p in enumerate(C.module(s, a, front=front), 1):
            q = p.moved(C.m.ARM_ROT[arm])
            q.arm = arm
            out.append((arm, i, Item(q, f'{arm}:{"head" if p.head else "fixed"}', f'{arm}#{i} {p.name} {p.note}'.strip())))
    out += [(None, 0, it) for it in support_items(drop)]
    out += [(None, 0, it) for it in base_items()]
    return out


class PointGrid2:
    """二维点集最近距离（网格加速）。"""

    def __init__(self, P, r):
        self.P, self.r = P, r
        self.o = P.min(0) - r
        c = np.floor((P - self.o) / r).astype(np.int64)
        self.key = c[:, 0] * 1_000_003 + c[:, 1]
        order = np.argsort(self.key)
        self.key, self.P = self.key[order], self.P[order]

    def query(self, Q):
        c = np.floor((Q - self.o) / self.r).astype(np.int64)
        best = np.full(len(Q), np.inf)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                k = (c[:, 0] + dx) * 1_000_003 + (c[:, 1] + dy)
                lo = np.searchsorted(self.key, k, 'left')
                hi = np.searchsorted(self.key, k, 'right')
                n = hi - lo
                sel = np.nonzero(n)[0]
                if not len(sel):
                    continue
                m = n[sel]
                qi = np.repeat(sel, m)
                off = np.arange(m.sum()) - np.repeat(np.cumsum(m) - m, m)
                pj = np.repeat(lo[sel], m) + off
                d = np.linalg.norm(Q[qi] - self.P[pj], axis=1)
                np.minimum.at(best, qi, d)
        best[best > self.r] = np.inf
        return best


def meridian(P, axis):
    a = P @ axis
    rho = np.linalg.norm(P - np.outer(a, axis), axis=1)
    return np.stack([a, rho], 1)


def full_turn_clearance(moving, obstacles, axis, rmax=6.0, top=6):
    """moving 绕 axis 整圈回转扫出的回转体与各障碍零件的最小距离。返回 [(d, moving 最近件, 障碍件)]。"""
    M = [(it, meridian(samples(it.part), axis)) for it in moving]
    allM = np.concatenate([m for _, m in M])
    own = np.concatenate([np.full(len(m), k) for k, (_, m) in enumerate(M)])
    lo, hi = allM.min(0) - rmax, allM.max(0) + rmax
    g = PointGrid2(allM, rmax)
    # 记录每个运动点的归属，便于报告是哪一件
    g_own = own[np.argsort(np.floor((allM - g.o) / rmax).astype(np.int64)[:, 0] * 1_000_003 +
                           np.floor((allM - g.o) / rmax).astype(np.int64)[:, 1])]
    res = []
    for ob in obstacles:
        Q = meridian(samples(ob.part), axis)
        Q = Q[np.all((Q >= lo) & (Q <= hi), axis=1)]
        if not len(Q):
            continue
        d = g.query(Q)
        k = int(np.argmin(d))
        if np.isfinite(d[k]):
            # 找最近运动点的归属件
            j = int(np.argmin(np.linalg.norm(g.P - Q[k], axis=1)))
            res.append((float(d[k]), moving[int(g_own[j])].label, ob.label))
    res.sort(key=lambda r: r[0])
    return res[:top] if top else res


def roll_sweep(make_state, angles, movers, front, drop, others_filter=None, rmax=6.0, refine=0.25):
    """机械头按 angles 逐角度回转（其余姿态固定），返回每个角度的最小间隙与全程最小值；
    在粗扫最小值附近按 refine 度加密。movers：转动的机械臂（只取其压头新件作为运动件）。"""
    F = front_ids(front)

    def at(ang):
        mach = machine(make_state(ang), drop, front)
        A = [it for arm, i, it in mach if arm in movers and it.group.endswith('head') and i in F]
        B = [it for arm, i, it in mach if not (arm in movers and it.group.endswith('head') and i in F)]
        if others_filter:
            B = [b for b in B if others_filter(b)]
        r = front_clearance(A, B, rmax=rmax, top=3, skip=designed_contact)
        return r
    coarse = [(ang, at(ang)) for ang in angles]
    best = min(coarse, key=lambda x: x[1][0][0] if x[1] else np.inf)
    fine = []
    if best[1]:
        step = abs(angles[1] - angles[0]) if len(angles) > 1 else 1
        a0 = best[0]
        for ang in np.arange(a0 - step, a0 + step + 1e-9, refine):
            if min(angles) - 1e-9 <= ang <= max(angles) + 1e-9:
                fine.append((float(ang), at(float(ang))))
    return coarse, fine


def designed_contact(a, b):
    """同一臂内按设计相互接触/穿孔的零件对（轴在孔中、薄梁贴面等），不计入间隙。"""
    la, lb = a.label.split('#'), b.label.split('#')
    if len(la) < 2 or len(lb) < 2 or la[0] != lb[0]:
        return False
    ia, ib = int(la[1].split()[0]), int(lb[1].split()[0])
    return frozenset((ia, ib)) in DESIGNED


def _designed():
    # 每个夹指：零件编号（A 夹指，B 夹指偏移见下）
    pairs = set()
    for jaw, rep, add in ((121, 137, 168), (129, 146, 176)):
        rowm, rowp, ax21, bm, bp, ax31, ax20, wm, tm = range(rep, rep + 9)
        ax30, l2m, l2p, l3m, l3p, wax, wp, tp = range(add, add + 8)
        groups = [
            (ax20, [l2m, jaw, l2p]), (ax30, [l3m, jaw, l3p]),
            (ax21, [rowm, l2m, l2p, rowp]), (ax31, [rowm, l3m, l3p, rowp]),
            (wax, [rowm, bm, wm, wp, bp, rowp]),
        ]
        for axle, hosts in groups:
            for h in hosts:
                pairs.add(frozenset((axle, h)))
            for h1, h2 in zip(hosts, hosts[1:]):
                pairs.add(frozenset((h1, h2)))  # 叠层相邻件贴面
        for x, y in ((wm, tm), (wp, tp), (tm, tp), (l2m, rowm), (l3m, rowm), (l2p, rowp), (l3p, rowp),
                     (l2m, jaw), (l2p, jaw), (l3m, jaw), (l3p, jaw)):
            pairs.add(frozenset((x, y)))
    return pairs


DESIGNED = _designed()
