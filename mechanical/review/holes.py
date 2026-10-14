"""按真实网格判定孔型：沿连接轴线投射直线，检查宿主零件在该处是否开孔，以及是十字孔还是圆孔。

十字孔：臂宽 1.8mm、臂长到半径 2.4mm；圆孔半径约 2.4mm。在离轴 2.0mm 处，
  * 沿十字臂方向（0°/90°）——十字孔、圆孔都是空的；
  * 45° 方向——十字孔处有材料，圆孔处为空。
十字方向取轴自身网格的局部坐标，因此同时核对了十字相位。单位 mm。
"""
import numpy as np


def line_hits(T, P0, d, half=60.0):
    """直线 P0 + t d（|t|<=half）与三角形的交点参数 t。"""
    e1, e2 = T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]
    pv = np.cross(np.broadcast_to(d, e2.shape), e2)
    det = (e1 * pv).sum(1)
    ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1 / np.where(ok, det, 1), 0)
    tv = P0 - T[:, 0]
    u = (tv * pv).sum(1) * inv
    qv = np.cross(tv, e1)
    v = (qv * d).sum(1) * inv
    t = (e2 * qv).sum(1) * inv
    m = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9) & (np.abs(t) <= half)
    return np.sort(t[m])


def classify(T, P0, d, e1, e2, span):
    """返回宿主在这条轴线上的孔型：'axle'、'pin'、'blocked'（轴线处有材料）或 'none'（不在宿主内）。
    span=(t0,t1)：只看轴线上这一段（宿主厚度范围内）。实心处的直线只在宿主两端面有交点，故含端点。"""
    def solid(off):
        t = line_hits(T, P0 + off, d)
        t = t[(t >= span[0] - 0.05) & (t <= span[1] + 0.05)]
        return len(t) > 0
    if solid(np.zeros(3)):
        return 'blocked'
    r = 2.0
    diag = any(solid(r * (np.cos(a) * e1 + np.sin(a) * e2)) for a in np.radians([45, 135, 225, 315]))
    arm = any(solid(r * (np.cos(a) * e1 + np.sin(a) * e2)) for a in np.radians([0, 90, 180, 270]))
    if arm:
        return 'blocked'
    # 宿主必须真的包住这段轴：离轴 3.0mm 一圈应有材料（孔壁）。网格接缝处直线可能恰好擦过棱线，
    # 故 12 个方向中至少 9 个命中即可。
    wall = sum(solid(3.0 * (np.cos(a) * e1 + np.sin(a) * e2)) for a in np.radians(range(7, 360, 30))) >= 9
    if not wall:
        return 'none'
    return 'axle' if diag else 'pin'
