"""LDraw 零件库访问: 下载 (带本地缓存)、几何展开、孔位提取。

零件库来源: GitHub 上的 LDraw 官方库镜像 (gkjohnson/ldraw-parts-library, 2023-01 版本)。
本项目自定义的零件 (Geekservo、魔方) 放在 tools/lego/parts/, 优先于零件库。

单位是 LDU: 1 LDU = 0.4mm, 1 个孔距 = 20 LDU = 8mm。LDraw 坐标系 -Y 向上。
"""

import os
import urllib.parse
import urllib.request

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, ".cache", "ldraw")
CUSTOM = os.path.join(HERE, "parts")
MIRROR = "https://raw.githubusercontent.com/gkjohnson/ldraw-parts-library/master/"
SEARCH = ("parts/", "p/", "parts/s/", "p/48/")


def fetch_rel(rel):
    """按库内相对路径 (如 complete/ldraw/parts/3001.dat) 取文件内容, 不存在返回 None。"""
    path = os.path.join(CACHE, rel)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    if os.path.exists(path + ".404"):
        return None
    try:
        data = urllib.request.urlopen(MIRROR + urllib.parse.quote(rel), timeout=30).read()
    except Exception:  # noqa: BLE001 - 404 或网络错误都当作不存在
        data = None
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if data is None:
        open(path + ".404", "w").close()
        return None
    with open(path, "wb") as f:
        f.write(data)
    return data


def get(name):
    """按零件文件名取文本 (先找自定义零件, 再在库的各目录里找)。"""
    name = name.replace("\\", "/").lower()
    custom = os.path.join(CUSTOM, name)
    if os.path.exists(custom):
        with open(custom, encoding="utf-8") as f:
            return f.read()
    # 完整零件库已缓存在本地时，先查完所有目录，避免为基元先请求不存在的 parts/ 路径。
    for pre in SEARCH:
        cached = os.path.join(CACHE, "complete/ldraw/" + pre + name)
        if os.path.exists(cached):
            with open(cached, encoding="utf-8", errors="replace") as f:
                return f.read()
    for pre in SEARCH:
        data = fetch_rel("complete/ldraw/" + pre + name)
        if data is not None:
            return data.decode("utf-8", "replace")
    raise FileNotFoundError(name)


def title(name):
    return get(name).splitlines()[0][2:].strip()


_geom = {}


def geometry(name):
    """展开后的 (三角形 Nx3x3, 颜色 N, 线段 Mx2x3), 零件局部坐标; 颜色 16 表示继承。"""
    key = name.lower().replace("\\", "/")
    if key in _geom:
        return _geom[key]
    tris, cols, lines = [], [], []
    for raw in get(key).splitlines():
        p = raw.split()
        if not p:
            continue
        if p[0] == "1":
            c = int(p[1])
            v = list(map(float, p[2:14]))
            pos = np.array(v[0:3])
            m = np.array(v[3:12]).reshape(3, 3)
            st, sc, sl = geometry(" ".join(p[14:]))
            if len(st):
                tris.append(st @ m.T + pos)
                cc = sc.copy()
                if c != 16:
                    cc[cc == 16] = c
                cols.append(cc)
            if len(sl):
                lines.append(sl @ m.T + pos)
        elif p[0] == "3":
            tris.append(np.array(list(map(float, p[2:11]))).reshape(1, 3, 3))
            cols.append(np.array([int(p[1])]))
        elif p[0] == "4":
            v = np.array(list(map(float, p[2:14]))).reshape(4, 3)
            tris.append(np.stack([v[[0, 1, 2]], v[[0, 2, 3]]]))
            cols.append(np.array([int(p[1])] * 2))
        elif p[0] == "2":
            lines.append(np.array(list(map(float, p[2:8]))).reshape(1, 2, 3))
    t = np.concatenate(tris) if tris else np.zeros((0, 3, 3))
    c = np.concatenate(cols) if cols else np.zeros(0, int)
    l = np.concatenate(lines) if lines else np.zeros((0, 2, 3))
    _geom[key] = (t, c, l)
    return _geom[key]


def bbox(name):
    t = geometry(name)[0].reshape(-1, 3)
    return t.min(0), t.max(0)


# ---- 孔位 --------------------------------------------------------------------

_HOLE_KEYS = ("connhole", "peghole", "beamhole", "axlehol", "axl2hol", "axl3hol", "confric", "axlhol")
_SKIP = ("npeghol", "4-4", "1-4", "2-4", "3-4", "1-8", "3-8", "5-8", "7-8", "box", "rect", "edge", "stud", "t0", "t1",
         "8-8", "ring", "ndis", "di", "cyl", "con0", "con1", "con2", "con3", "con4", "con5", "con6", "con7", "con8",
         "con9", "48/", "tri", "tooth", "sphe", "chrd", "quad", "tnd", "tang", "filstr")
_holes = {}


def _walk_holes(name, m, pos, depth, out):
    for line in get(name).splitlines():
        p = line.split()
        if len(p) < 15 or p[0] != "1":
            continue
        v = list(map(float, p[2:14]))
        sub = " ".join(p[14:]).lower().replace("\\", "/")
        gp = m @ np.array(v[:3]) + pos
        gm = m @ np.array(v[3:12]).reshape(3, 3)
        if any(k in sub for k in _HOLE_KEYS) and not sub.startswith(_SKIP):
            ax = gm[:, 1]
            out.append((gp, ax / np.linalg.norm(ax)))
        elif depth < 4 and not sub.startswith(_SKIP):
            _walk_holes(sub, gm, gp, depth + 1, out)


def holes(name):
    """零件的孔: [(轴线上一点, 单位方向)], 同一直线上的孔合并为一条。"""
    key = name.lower()
    if key in _holes:
        return _holes[key]
    raw = []
    _walk_holes(key, np.eye(3), np.zeros(3), 0, raw)
    lines = []
    for p, a in raw:
        a = a if a[np.argmax(np.abs(a))] > 0 else -a
        for q, b in lines:
            if abs(abs(a @ b) - 1) < 1e-6 and np.linalg.norm(np.cross(p - q, b)) < 0.5:
                break
        else:
            lines.append((p, a))
    _holes[key] = lines
    return lines


_segs = {}


def hole_segments(name):
    """零件的每一段孔: [(起点, 终点)], 零件局部坐标。和 holes() 不同, 不合并成无限长的直线,
    可以用来判断某一点是不是真的在孔里 (例如挡套、挡肩有没有伸进孔)。"""
    key = name.lower()
    if key in _segs:
        return _segs[key]
    out = []

    def walk(n, m, pos, depth):
        for line in get(n).splitlines():
            p = line.split()
            if len(p) < 15 or p[0] != "1":
                continue
            v = list(map(float, p[2:14]))
            sub = " ".join(p[14:]).lower().replace("\\", "/")
            gp = m @ np.array(v[:3]) + pos
            gm = m @ np.array(v[3:12]).reshape(3, 3)
            if any(k in sub for k in _HOLE_KEYS) and not sub.startswith(_SKIP):
                t = geometry(sub)[0]
                ys = t[..., 1] if len(t) else np.array([0.0, 1.0])
                out.append((gp + gm[:, 1] * ys.min(), gp + gm[:, 1] * ys.max()))
            elif depth < 4 and not sub.startswith(_SKIP):
                walk(sub, gm, gp, depth + 1)

    walk(key, np.eye(3), np.zeros(3), 0)
    _segs[key] = out
    return out
