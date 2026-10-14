"""网格间距计算（纯 numpy）：点到三角形精确距离、均匀网格加速、边线-三角形穿透判定。

两组三角网格的最小距离取在“顶点-面”或“边-边”上：本模块对两边各自的顶点和沿边等距采样点
（间距 h）求到对方三角形的精确距离，误差不超过约 h/2。若两表面相交，必有一条边穿过对方的面，
因此另做精确的线段-三角形相交判定，用来区分“贴合/接近”和“穿透”。单位 mm。
"""
import numpy as np


def edge_samples(tris, h=0.3):
    """三角形顶点＋沿三条边每隔 h 的采样点（去重前）。tris: (N,3,3)。"""
    pts = [tris.reshape(-1, 3)]
    for a, b in ((0, 1), (1, 2), (2, 0)):
        A, B = tris[:, a], tris[:, b]
        L = np.linalg.norm(B - A, axis=1)
        n = np.maximum(1, np.ceil(L / h).astype(int))
        reps = np.repeat(np.arange(len(tris)), n - 1)
        if len(reps):
            m = n - 1
            k = 1 + np.arange(m.sum()) - np.repeat(np.cumsum(m) - m, m)
            t = (k / np.repeat(n, m))[:, None]
            pts.append(A[reps] + t * (B[reps] - A[reps]))
    P = np.concatenate(pts)
    return np.unique(np.round(P, 5), axis=0)


def point_tri_dist(P, A, B, C):
    """逐对求点 P 到三角形 ABC 的距离（Ericson, Real-Time Collision Detection 5.1.5）。"""
    ab, ac, ap = B - A, C - A, P - A
    d1, d2 = (ab * ap).sum(1), (ac * ap).sum(1)
    bp = P - B
    d3, d4 = (ab * bp).sum(1), (ac * bp).sum(1)
    cp = P - C
    d5, d6 = (ab * cp).sum(1), (ac * cp).sum(1)
    vc = d1 * d4 - d3 * d2
    vb = d5 * d2 - d1 * d6
    va = d3 * d6 - d5 * d4
    Q = np.empty_like(P)
    done = np.zeros(len(P), bool)

    def put(mask, val):
        m = mask & ~done
        Q[m] = val[m] if val.ndim == 2 else val
        done[m] = True
    put((d1 <= 0) & (d2 <= 0), A)
    put((d3 >= 0) & (d4 <= d3), B)
    with np.errstate(divide='ignore', invalid='ignore'):
        v = np.where(np.abs(d1 - d3) > 1e-30, d1 / (d1 - d3), 0)
        put((vc <= 0) & (d1 >= 0) & (d3 <= 0), A + v[:, None] * ab)
        put((d6 >= 0) & (d5 <= d6), C)
        w = np.where(np.abs(d2 - d6) > 1e-30, d2 / (d2 - d6), 0)
        put((vb <= 0) & (d2 >= 0) & (d6 <= 0), A + w[:, None] * ac)
        w2 = np.where(np.abs((d4 - d3) + (d5 - d6)) > 1e-30, (d4 - d3) / ((d4 - d3) + (d5 - d6)), 0)
        put((va <= 0) & ((d4 - d3) >= 0) & ((d5 - d6) >= 0), B + w2[:, None] * (C - B))
        den = va + vb + vc
        den = np.where(np.abs(den) > 1e-30, den, 1e-30)
        vv, ww = vb / den, vc / den
    rest = ~done
    Q[rest] = (A + vv[:, None] * ab + ww[:, None] * ac)[rest]
    return np.linalg.norm(P - Q, axis=1)


class TriGrid:
    """把三角形按“包围盒外扩 rmax”登记到边长 rmax 的网格里，查询点只需看自己所在的格。"""

    def __init__(self, tris, rmax, owner=None):
        self.tris = np.asarray(tris, float)
        self.owner = np.zeros(len(self.tris), int) if owner is None else np.asarray(owner)
        self.r = float(rmax)
        lo = self.tris.min(1) - self.r
        hi = self.tris.max(1) + self.r
        self.origin = lo.min(0) if len(lo) else np.zeros(3)
        c0 = np.floor((lo - self.origin) / self.r).astype(np.int64)
        c1 = np.floor((hi - self.origin) / self.r).astype(np.int64)
        span = c1 - c0 + 1
        n = span.prod(1)
        ti = np.repeat(np.arange(len(self.tris)), n)
        k = np.arange(n.sum()) - np.repeat(np.cumsum(n) - n, n)
        sx, sy = np.repeat(span[:, 0], n), np.repeat(span[:, 1], n)
        cx = np.repeat(c0[:, 0], n) + k % sx
        cy = np.repeat(c0[:, 1], n) + (k // sx) % sy
        cz = np.repeat(c0[:, 2], n) + k // (sx * sy)
        key = self._key(cx, cy, cz)
        order = np.argsort(key, kind='stable')
        self.keys, self.ti = key[order], ti[order]

    @staticmethod
    def _key(x, y, z):
        return (x + 4096) * 1 << 26 | (y + 4096) << 13 | (z + 4096)

    def query(self, P, chunk=4_000_000):
        """返回每个点到最近三角形的距离（找不到时为 inf）与对应三角形下标。"""
        P = np.asarray(P, float)
        c = np.floor((P - self.origin) / self.r).astype(np.int64)
        key = self._key(c[:, 0], c[:, 1], c[:, 2])
        lo = np.searchsorted(self.keys, key, 'left')
        hi = np.searchsorted(self.keys, key, 'right')
        cnt = hi - lo
        best = np.full(len(P), np.inf)
        arg = np.full(len(P), -1)
        idx = np.nonzero(cnt)[0]
        if not len(idx):
            return best, arg
        # 分块展开 (点, 三角形) 对
        csum = np.cumsum(cnt[idx])
        start = 0
        while start < len(idx):
            base = csum[start - 1] if start else 0
            stop = int(np.searchsorted(csum, base + chunk, 'right'))
            stop = max(stop, start + 1)
            sel = idx[start:stop]
            m = cnt[sel]
            pi = np.repeat(sel, m)
            off = np.arange(m.sum()) - np.repeat(np.cumsum(m) - m, m)
            ti = self.ti[np.repeat(lo[sel], m) + off]
            T = self.tris[ti]
            d = point_tri_dist(P[pi], T[:, 0], T[:, 1], T[:, 2])
            order = np.lexsort((d, pi))
            pi_s, d_s, ti_s = pi[order], d[order], ti[order]
            first = np.r_[True, pi_s[1:] != pi_s[:-1]]
            upd = d_s[first] < best[pi_s[first]]
            tgt = pi_s[first][upd]
            best[tgt] = d_s[first][upd]
            arg[tgt] = ti_s[first][upd]
            start = stop
        best[best > self.r] = np.inf
        return best, arg


def seg_tri_cross(P0, P1, A, B, C, eps=1e-9):
    """逐对判定线段 P0P1 是否穿过三角形 ABC 的内部（端点恰在面上不算）。Möller–Trumbore。"""
    d = P1 - P0
    e1, e2 = B - A, C - A
    pv = np.cross(d, e2)
    det = (e1 * pv).sum(1)
    ok = np.abs(det) > eps
    inv = np.where(ok, 1 / np.where(ok, det, 1), 0)
    tv = P0 - A
    u = (tv * pv).sum(1) * inv
    qv = np.cross(tv, e1)
    v = (d * qv).sum(1) * inv
    t = (e2 * qv).sum(1) * inv
    tol = 1e-4
    return ok & (u > tol) & (v > tol) & (u + v < 1 - tol) & (t > tol) & (t < 1 - tol)
