"""生成 LDraw 零件库里没有的自定义零件: Geekservo 舵机、56mm 魔方、绕在夹指上的乐高皮带。

Geekservo 尺寸取自用户提供的图纸 (单位 mm, 1mm = 2.5 LDU):
- 本体 24 x 28.8 (高) x 16, 两侧耳朵连外壳总长 40;
- 耳朵高 9.6 (位于中间), 各有一个 φ4.8 的 Technic 销孔, 沿 16mm 方向贯穿, 两孔相距 32 (= 4 个孔距);
- 输出十字轴在顶面, 伸出 5.6, 与中心偏 4 (离一侧销孔 12)。
局部坐标: X 沿长度, Y 为高度 (输出朝 -Y, 即 LDraw 的 "上"), Z 沿 16mm 厚度, 原点在本体中心。
"""

import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = os.path.join(HERE, "parts")


def box(c, x0, x1, y0, y1, z0, z1):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    faces = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    out = []
    for f in faces:
        out.append(f"4 {c} " + " ".join(f"{a:g} {b:g} {d:g}" for a, b, d in (v[i] for i in f)))
    edges = [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]
    for a, b in edges:
        out.append("2 24 " + " ".join(f"{t:g}" for t in v[a] + v[b]))
    return out


def geekservo():
    s = 2.5  # LDU / mm
    bx, by, bz = 12 * s, 14.4 * s, 8 * s  # 本体半尺寸
    ear_x, ear_y = 20 * s, 4.8 * s
    lines = [
        "0 Geekservo 270 Servo (LEGO compatible, approximate)",
        "0 Name: geekservo.dat",
        "0 Author: quadcuber (按用户提供的图纸建模, 外形为近似)",
        "0 !LDRAW_ORG Unofficial_Part",
        "0 BFC NOCERTIFY",
        "",
    ]
    lines += box(16, -bx, bx, -by, by, -bz, bz)
    for sgn in (-1, 1):
        x0, x1 = sorted((sgn * bx, sgn * ear_x))
        lines += box(16, x0, x1, -ear_y, ear_y, -bz, bz)
        hx = sgn * 16 * s
        # 销孔 (沿 Z 贯穿); connhole.dat 沿局部 Y 深 20, 这里旋转到 Z 方向, 两段拼成 40 深
        lines.append(f"1 16 {hx:g} 0 {-bz:g} 1 0 0 0 0 1 0 1 0 connhole.dat")
        lines.append(f"1 16 {hx:g} 0 0 1 0 0 0 0 1 0 1 0 connhole.dat")
        for z in (-bz - 0.1, bz + 0.1):
            lines.append(f"1 0 {hx:g} 0 {z:g} 6 0 0 0 0 1 0 6 0 4-4disc.dat")
    # 输出轴: 顶面圆台 + 十字轴 (伸出 5.6mm = 14 LDU)
    ox = 4 * s
    lines.append(f"1 16 {ox:g} {-by:g} 0 12 0 0 0 -3 0 0 0 12 4-4cyli.dat")
    lines.append(f"1 16 {ox:g} {-by - 3:g} 0 12 0 0 0 1 0 0 0 12 4-4disc.dat")
    lines.append(f"1 71 {ox:g} {-by - 3:g} 0 1 0 0 0 -11 0 0 0 1 axle.dat")
    # 线缆出口 (示意)
    lines += box(0, -bx - 6, -bx, by - 14, by - 4, -5, 5)
    return "\n".join(lines) + "\n"


def cube56():
    """56mm 魔方 (140 LDU), 六面按 U 白 / D 黄 / F 绿 / B 蓝 / R 红 / L 橙 上色。"""
    h = 70
    pitch = 140 / 3
    st = 20  # 贴纸半宽
    lines = ["0 Rubik's Cube 56mm (display only)", "0 Name: cube56.dat", "0 Author: quadcuber", "0 BFC NOCERTIFY", ""]
    lines += box(0, -h, h, -h, h, -h, h)
    faces = {  # (颜色, 法向轴, 符号)
        "U": (15, 1, -1), "D": (14, 1, 1), "F": (2, 2, 1), "B": (1, 2, -1), "R": (4, 0, 1), "L": (25, 0, -1)}
    for col, ax, sgn in faces.values():
        others = [a for a in range(3) if a != ax]
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                lo, hi = [0.0] * 3, [0.0] * 3
                lo[ax], hi[ax] = sorted((sgn * (h - 0.5), sgn * (h + 1.0)))
                for k, c in zip(others, (i, j)):
                    lo[k], hi[k] = c * pitch - st, c * pitch + st
                lines += box(col, lo[0], hi[0], lo[1], hi[1], lo[2], hi[2])
    return "\n".join(lines) + "\n"


def rubberband_on_beam(turns=2, pitch=4.0, r=1.75, gap=0.3, corner=3.0):
    """乐高 Technic 皮带 (15mm, BrickLink x37) 横向绕在 1 孔宽粗梁上的样子 (v3 夹指预压用, 2026-09-30)。

    LDraw 库里没有皮带零件, 这里按 "绕好以后" 的形状画: 每圈是一个套在梁截面 (18 x 20 LDU) 外面的圆环管,
    截面直径 2r = 3.5 LDU (约 1.4mm, 按 15mm 皮带估计, 实物要量); turns 圈沿梁长度方向并排, 间距 pitch。
    局部坐标和 32524 粗梁一样: X 是梁的宽度方向 (±9), Y 是孔的方向 (±10), Z 沿梁长, 圈的中心在 Z = 0。
    只画面, 不画边线 (皮带是圆截面, 没有棱)。"""
    hx, hy = 9.0 + gap + r, 10.0 + gap + r  # 皮带中心线到梁轴线的距离
    rc = corner + r  # 中心线在四个角上的圆角半径
    # 中心线: 圆角矩形, 每个角 4 段, 每条直边 1 段
    path = []
    for (cx, cy, a0) in ((hx - rc, hy - rc, 0.0), (-(hx - rc), hy - rc, 90.0), (-(hx - rc), -(hy - rc), 180.0), (hx - rc, -(hy - rc), 270.0)):
        for k in range(5):
            a = math.radians(a0 + 22.5 * k)
            path.append((cx + rc * math.cos(a), cy + rc * math.sin(a)))
    n = len(path)
    lines = [
        f"0 Technic Rubber Belt 15mm wrapped {turns}x around 1-wide beam (approximate)",
        "0 Name: rubberband.dat",
        "0 Author: quadcuber (按绕好后的形状建模, 皮带截面直径按 1.4mm 估计)",
        "0 !LDRAW_ORG Unofficial_Part",
        "0 BFC NOCERTIFY",
        "",
    ]
    seg = 8
    for t in range(turns):
        z0 = (t - (turns - 1) / 2) * pitch
        ring = []
        for i in range(n):
            x, y = path[i]
            nx, ny = path[(i + 1) % n]
            px, py = path[i - 1]
            # 中心线的外法线 (相邻两段的平均方向旋转 90°)
            tx, ty = nx - px, ny - py
            L = math.hypot(tx, ty)
            ox, oy = ty / L, -tx / L
            ring.append([(x + r * math.cos(b) * ox, y + r * math.cos(b) * oy, z0 + r * math.sin(b))
                         for b in (math.radians(360 / seg * j) for j in range(seg))])
        for i in range(n):
            a, b = ring[i], ring[(i + 1) % n]
            for j in range(seg):
                p0, p1, p2, p3 = a[j], b[j], b[(j + 1) % seg], a[(j + 1) % seg]
                lines.append("4 16 " + " ".join(f"{v:.3f}" for q in (p0, p1, p2, p3) for v in q))
    return "\n".join(lines) + "\n"


def main():
    os.makedirs(PARTS, exist_ok=True)
    for name, text in (("geekservo.dat", geekservo()), ("cube56.dat", cube56()), ("rubberband.dat", rubberband_on_beam())):
        with open(os.path.join(PARTS, name), "w", encoding="utf-8") as f:
            f.write(text)


if __name__ == "__main__":
    main()
