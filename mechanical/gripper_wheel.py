"""外偏大轮压头：轮轴仍沿 Z（轮胎沿径向滚动，不需要锁死），轮轴从夹指中心线向外偏 1 孔。

问题本质：拧邻层时，邻层整圈扫过 ρ = √(x²+y²) < √2·28 = 39.6mm、|z| > 9.33mm 的区域。
现方案轮轴就在夹指中心线上（离魔方面 6.7mm），夹住轮轴的两片 32449 薄梁端部（半径 3.6mm 的孔环）
有一块落在 ρ<39.6mm 以内，又在 |z| = 4~8mm 处，所以余量只有 1.33mm，且随零位误差、装料偏移线性减小。

本方案：
  * 轮子换成官方经典组合 4185 皮带轮（十字孔，宽 4mm）＋2815 皮带轮胎（外径 30.4mm，宽 3.2mm），两组并排，
    合宽 8mm，正好占满夹指两侧薄梁之间的槽；
  * 轮轴放在夹指第 4 孔前 5 孔、向外 1 孔处（夹指坐标 (5,1)）。外径 30.4mm 的轮胎底部仍压在原接触点附近，
    而轮轴、孔环、支承梁全部在 ρ ≥ 45mm 处，远离扫掠区；扫掠区内只剩 |z| ≤ 4mm 的轮胎和轮毂下缘；
  * 夹指由 7 孔粗梁 32524 换成 5 孔粗梁 32316（根轴仍在中孔、连杆仍在第 1 孔），否则轮胎会碰 7 孔梁的梁尖；
  * 支承：每侧两根 41677 两孔薄梁（两端十字孔）从夹指第 4、5 孔竖向外伸 1 孔，外层一根 11478 五孔薄梁
    （两端十字孔、中间三孔圆孔）沿夹指方向连到轮轴。四个十字孔连接点＋夹指两孔，构成不能转动的框。

零件序号：旧压头 9 件与夹指原位替换（序号不变），每个夹指新增 8 件追加在 168 之后。
"""
import numpy as np

OLD_NOTES = ['压头支承薄梁', '压头支承薄梁', '薄梁固定轴', '薄梁固定轴限位', '薄梁固定轴限位',
             '薄梁固定挡套销', '轮毂贯穿轴', '轮毂', '橡胶胎']
L = 20.0  # 1 孔 = 20 LDU
C_LINK = 0
C_ROW = 4
C_WHEEL = 71
C_TYRE = 0


def front_parts(m, open_s=0.0, angle=0.0):
    beta = m.jaw_beta(open_s)
    Rr = m.rot_x(angle) if angle else np.eye(3)
    shift = np.array([m.MODULE_DX, 0, 0], float)
    replacements, added = [], []
    for sy in (1, -1):
        piv = np.array([m.PIVOT_X, m.JAW_Y * sy, 0.0])
        R = m.rot_z(beta * sy)
        ex, out_dir, ez = R[:, 0], sy * R[:, 1], np.array([0, 0, 1.0])

        def part(name, color, a, b, z, rot, note):
            local = piv + a * L * ex + b * L * out_dir + np.array([0, 0, z], float)
            p = m.Part(name, color, Rr @ local + shift, Rr @ rot, 0, note)
            p.head = True
            return p
        along_z = R @ m.ALONG_Z
        bush = R @ m.BUSH_Z
        link_rot = np.stack([np.cross(ez, out_dir), ez, out_dir], axis=1)  # 41677：局部 z 为长度，孔在 z=0、20
        row_rot = R @ m.BEAM_X_HOLES_Z
        A, W = 4, 6  # 外梁中孔、轮轴的夹指坐标 a
        replacements += [
            part('11478.dat', C_ROW, A, 1, -25, row_rot, '轮架外梁-Z'),
            part('11478.dat', C_ROW, A, 1, 25, row_rot, '轮架外梁+Z'),
            part('4519.dat', m.C_AXLE, 2, 1, 0, along_z, '轮架上轴(2,1)'),
            part('32123a.dat', m.C_BUSH, W, 1, -15, bush, '轮轴半套'),
            part('32123a.dat', m.C_BUSH, W, 1, 15, bush, '轮轴半套'),
            part('4519.dat', m.C_AXLE, 3, 1, 0, along_z, '轮架上轴(3,1)'),
            part('32062.dat', m.C_AXLE, 2, 0, 0, along_z, '夹指第6孔轴'),
            part('4185a.dat', C_WHEEL, W, 1, -5, R, '皮带轮-Z'),
            part('2815.dat', C_TYRE, W, 1, -5, R, '皮带轮胎-Z'),
        ]
        added += [
            part('32062.dat', m.C_AXLE, 3, 0, 0, along_z, '夹指第7孔轴'),
            part('41677.dat', C_LINK, 2, 0, -15, link_rot, '竖连杆-Z(6)'),
            part('41677.dat', C_LINK, 2, 0, 15, link_rot, '竖连杆+Z(6)'),
            part('41677.dat', C_LINK, 3, 0, -15, link_rot, '竖连杆-Z(7)'),
            part('41677.dat', C_LINK, 3, 0, 15, link_rot, '竖连杆+Z(7)'),
            part('4519.dat', m.C_AXLE, W, 1, 0, along_z, '轮轴'),
            part('4185a.dat', C_WHEEL, W, 1, 5, R, '皮带轮+Z'),
            part('2815.dat', C_TYRE, W, 1, 5, R, '皮带轮胎+Z'),
        ]
    return replacements, added


def apply(m, pp, open_s=0.0, angle=0.0):
    idx = [i for i, p in enumerate(pp) if p.note in set(OLD_NOTES)]
    assert [pp[i].note for i in idx] == OLD_NOTES * 2
    rep, add = front_parts(m, open_s, angle)
    out = list(pp)
    for i, p in zip(idx, rep):
        out[i] = p
    return out + add
