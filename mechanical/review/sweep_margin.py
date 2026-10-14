"""邻层扫掠余量：L 臂夹紧时，F/B 层绕 z 轴整圈转动扫过 ρ<√2·28mm、|z|>9.33mm 的区域。

余量 = 零件表面到该区域的最短距离（mm，负值为侵入）。装料偏移 δ：魔方相对夹头沿 z 平移；
零位误差 θ：机械头绕自身转轴（x）偏转。两者都取最不利的符号。零件取真实 LDraw 网格的顶点与棱线采样。
"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from review.scene import C, samples  # noqa: E402

RC = math.sqrt(2) * 28.0
ZB = 56.0 / 6
FRONT = {'previous': list(range(137, 155)), 'rot90': list(range(137, 155)) + list(range(168, 170)),
         'wheel': list(range(137, 155)) + list(range(168, 184))}


def margin(P, delta, theta):
    th = math.radians(theta)
    c, s = math.cos(th), math.sin(th)
    y = c * P[:, 1] - s * P[:, 2]
    z = s * P[:, 1] + c * P[:, 2] - delta
    rho = np.hypot(P[:, 0], y)
    az = np.abs(z)
    outside = np.hypot(np.maximum(0, rho - RC), np.maximum(0, ZB - az))
    inside = (rho < RC) & (az > ZB)
    return float(np.where(inside, -np.minimum(RC - rho, az - ZB), outside).min())


def groups(front):
    pp = C.module(0, 0, front=front)
    g = {'rubber': [], 'hardware': []}
    for i in FRONT[front]:
        p = pp[i - 1]
        g['rubber' if p.name in ('50945_nominal.dat', '2815.dat', '59895.dat') else 'hardware'].append(samples(p))
    return {k: np.concatenate(v) for k, v in g.items()}


def table(front, deltas=(0, .5, 1, 1.5, 2), thetas=(0, 1, 2, 3)):
    out = {}
    for name, P in groups(front).items():
        out[name] = [[round(min(margin(P, sd * d, st * t) for sd in (1, -1) for st in (1, -1)), 2)
                      for t in thetas] for d in deltas]
    return dict(deltas_mm=list(deltas), thetas_deg=list(thetas), margins_mm=out)


if __name__ == '__main__':
    import json
    print(json.dumps({f: table(f) for f in FRONT}, ensure_ascii=False, indent=1))
