"""轮胎转 90° 压头：轮轴与夹指中心线共线，从魔方外侧伸入。

旧压头：42610 轮毂＋50945 轮胎套在沿 Z 的 2 号轴上，两侧各一片 32449 薄梁，合宽 16mm，
拧邻层时每侧只余 1.33mm。新压头：轮胎轴线沿夹指长度方向（与机械臂转轴平行），
支承件全部退到魔方 L 面之外（x < -28mm）：

  * 夹指两侧各一片 32056（3x3 L 形薄梁，两端与弯角为十字孔，中间两孔为圆孔）：
    一臂沿夹指贴住侧面，端部十字孔对夹指第 6 孔、中间圆孔对第 7 孔；弯角在夹指尖前方 1 孔；
    另一臂背离魔方伸出 2 孔。
  * 夹指尖前方放一个 42003（十字块 1x3，轴/销/销）：十字孔沿夹指方向、正好在夹指中心线上，
    两个销孔沿 Z，对准两片 L 梁外伸臂的中孔（圆）和端孔（十字）。
  * 四处连接（夹指第 6、7 孔，外伸臂第 2、3 孔）都用 3 号轴贯穿，两端各一个半轴套。
  * 2 号轴插进 42003 十字孔，另一段套 42610 轮毂＋50945 轮胎；轮毂贴住 42003，轴端与轮毂外侧齐平，
    轴内端离夹指尖 0.4mm。轮毂靠十字孔锁死在轴上，轴靠十字孔锁死在 42003 上，轮胎不能滚动。

轮胎中心与旧方案完全相同（夹指第 4 孔前 5 孔距，即 CLAMP_BETA 的定义点），夹紧角、舵机行程不变。
零件序号：旧压头的 9 件原位替换（序号 137–154 不变），新增 9×2 件追加在 168–185。
"""
import numpy as np

# 每个夹指（A=+Y 先、B=-Y 后）旧压头 9 件的备注 → 新角色（原位替换，序号不变）
OLD_NOTES = ['压头支承薄梁', '压头支承薄梁', '薄梁固定轴', '薄梁固定轴限位', '薄梁固定轴限位',
             '薄梁固定挡套销', '轮毂贯穿轴', '轮毂', '橡胶胎']
PER_JAW_ADDED = 9
EXTRA_ASSETS = ['npeghol6c.dat', '42003.dat']  # 官方 LDraw 库原文件，见 review/parts/（仅核算用）
C_PLATE = 71  # 浅灰 32056
C_BLOCK = 0   # 黑 42003


def jaw_frames(m, open_s, angle):
    """返回 [(sy, piv, R, place)]；place(local) 把夹指坐标系（未回转、未平移）里的点变到模块坐标。"""
    beta = m.jaw_beta(open_s)
    Rr = m.rot_x(angle) if angle else np.eye(3)
    shift = np.array([m.MODULE_DX, 0, 0], float)
    out = []
    for sy in (1, -1):
        piv = np.array([m.PIVOT_X, m.JAW_Y * sy, 0.0])
        R = m.rot_z(beta * sy)
        out.append((sy, piv, R, Rr, shift))
    return out


def front_parts(m, open_s=0.0, angle=0.0):
    """两个夹指的新压头：返回 (replacements[18], added[18])，顺序与旧件、追加件一一对应。"""
    replacements, added = [], []
    for sy, piv, R, Rr, shift in jaw_frames(m, open_s, angle):
        ex, ey = R[:, 0], R[:, 1]
        out_dir = sy * ey  # 背离魔方
        def part(name, color, along_jaw, outward, z, rot, note):
            local = piv + along_jaw * ex + outward * out_dir + np.array([0, 0, z], float)
            p = m.Part(name, color, Rr @ local + shift, Rr @ rot, 0, note)
            p.head = True
            return p
        def plate_rot(zs):
            a, c = -ex, out_dir  # 局部 x 臂朝夹指根部，局部 z 臂背离魔方
            return np.stack([a, np.cross(c, a), c], axis=1)
        along_z = R @ m.ALONG_Z
        bush = R @ m.BUSH_Z
        block_rot = np.stack([ex, out_dir, np.cross(ex, out_dir)], axis=1)
        wheel_rot = np.stack([R[:, 1], R[:, 2], R[:, 0]], axis=1)  # 轮毂/轮胎局部 z（轴线）沿夹指
        replacements += [
            part('32056.dat', C_PLATE, 80, 0, -15, plate_rot(-1), '压头L梁-Z'),
            part('32056.dat', C_PLATE, 80, 0, 15, plate_rot(1), '压头L梁+Z'),
            part('4519.dat', m.C_AXLE, 40, 0, 0, along_z, '压头第6孔轴'),
            part('32123a.dat', m.C_BUSH, 40, 0, -25, bush, '压头第6孔轴半套'),
            part('32123a.dat', m.C_BUSH, 40, 0, 25, bush, '压头第6孔轴半套'),
            part('4519.dat', m.C_AXLE, 60, 0, 0, along_z, '压头第7孔轴'),
            part('32062.dat', m.C_AXLE, 90, 0, 0, R, '轮胎轴（沿夹指）'),
            part('42610.dat', 71, 100, 0, 0, wheel_rot, '轮毂'),
            part('50945_nominal.dat', 0, 100, 0, 0, wheel_rot, '橡胶胎'),
        ]
        added += [
            part('32123a.dat', m.C_BUSH, 60, 0, -25, bush, '压头第7孔轴半套'),
            part('32123a.dat', m.C_BUSH, 60, 0, 25, bush, '压头第7孔轴半套'),
            part('42003.dat', C_BLOCK, 80, 20, 0, block_rot, '轮胎轴座42003'),
            part('4519.dat', m.C_AXLE, 80, 20, 0, along_z, '轴座内销轴'),
            part('32123a.dat', m.C_BUSH, 80, 20, -25, bush, '轴座内销轴半套'),
            part('32123a.dat', m.C_BUSH, 80, 20, 25, bush, '轴座内销轴半套'),
            part('4519.dat', m.C_AXLE, 80, 40, 0, along_z, '轴座外销轴'),
            part('32123a.dat', m.C_BUSH, 80, 40, -25, bush, '轴座外销轴半套'),
            part('32123a.dat', m.C_BUSH, 80, 40, 25, bush, '轴座外销轴半套'),
        ]
    return replacements, added


def apply(m, pp, open_s=0.0, angle=0.0):
    """在 candidate 模块零件表上原位替换旧压头并追加新增件；其余零件不动。"""
    idx = [i for i, p in enumerate(pp) if p.note in set(OLD_NOTES)]
    assert [pp[i].note for i in idx] == OLD_NOTES * 2, [pp[i].note for i in idx]
    rep, add = front_parts(m, open_s, angle)
    out = list(pp)
    for i, p in zip(idx, rep):
        out[i] = p
    return out + add
