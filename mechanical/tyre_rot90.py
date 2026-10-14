"""轮胎转 90° 压头（定型版）：轮轴与夹指中心线共线，从魔方外侧伸入；轮子靠十字孔锁死。

为什么是这个结构（详见 docs/lego/proposals/tyre-rot90/README.md）：
  * 轮轴沿夹指后，转面切向力沿轮胎滚动方向，轮子必须锁死。42610 中心为圆孔，锁不住；改用官方组合
    32123 半轴套（十字孔）＋59895 小轮胎（外径 14.4mm，LDraw 快捷件 32123ac01）。
  * 下侧夹指背离魔方只有约 8mm 空间（再往外是托座 U 形杠杆内臂和 11L 端轴）。因此支承件不能向外伸，
    全部放在夹指自身的厚度带内（中心线 ±4mm）。
  * 轮子必须留在原接触点附近：往魔方中心移 6mm 时，装料姿态（LR 50°）轮胎会撞托座 +Z 定位 L 梁。

结构（每个夹指；夹指坐标 a 为沿夹指的孔数，根轴为 a=0）：
  * 夹指两侧各一片 32449 四孔薄梁（两端十字孔、中间两孔圆孔），沿夹指中心线占 a=1~4：
    a=1 十字孔对夹指第 5 孔，a=3 圆孔对夹指第 7 孔，a=4 十字孔在夹指尖前 1 孔。
  * a=1：2 号轴贯穿两片薄梁十字孔与夹指圆孔，两端齐平；a=3：3 号轴贯穿（夹指第 7 孔），两端半轴套。
  * a=4：夹指尖前放 10197 轴销连接器（中间横圆孔，带两根互成 90° 的十字轴头）。一根轴头沿 −Z 穿过 −Z 侧
    薄梁的十字端孔（外露 3.8mm）；另一根轴头沿夹指中心线朝魔方。连接器夹在两片薄梁之间（−Z 面贴住薄梁，
    +Z 面间隙 0.4mm），不能沿 Z 窜动；十字轴头锁住转动。中间横圆孔沿“背离魔方”方向，不使用。连接器后缘离夹指尖 0.8mm。
  * 朝魔方的轴头依次套 32123 半轴套（垫距）和轮子（32123 半轴套＋59895 轮胎）。轮胎中心在 a=5.25，
    比现方案往魔方中心移 2mm。

零件序号：旧压头 9 件原位替换（序号 137–154 不变），每个夹指新增 1 件（轮子半套）追加在 168 之后。
"""
import numpy as np

OLD_NOTES = ['压头支承薄梁', '压头支承薄梁', '薄梁固定轴', '薄梁固定轴限位', '薄梁固定轴限位',
             '薄梁固定挡套销', '轮毂贯穿轴', '轮毂', '橡胶胎']
PER_JAW_ADDED = 1
# 发布模型新增的 LDraw 官方原文件（mechanical/parts/，a__b.dat 表示 a/b.dat），按此顺序追加在冻结资产表之后
EXTRA_ASSETS = ['axleconnect.dat', 'axleend20.dat', '10197.dat', '5-16cyli.dat', '5-16edge.dat', '5-16ring12.dat',
                '4-4ring15.dat', '4-4ring6.dat', '4-4con35.dat', '4-4con4.dat', '59895.dat']
L = 20.0
HUB_A = 4.0
STUB_END = HUB_A + 29.5 / L      # 朝魔方轴头的端部
SPACER_A = HUB_A + 0.5 + 0.25   # 垫距半套中心
WHEEL_A = HUB_A + 0.5 + 0.75    # 轮子紧贴垫距；轴头只有 7.8mm 外露，轮子半套套入 3.8mm、外侧悬出 0.2mm
C_HUB = 0


def front_parts(m, open_s=0.0, angle=0.0):
    """两个夹指的新压头：返回 (replacements[18], added[2])，顺序与旧件、追加件一一对应。"""
    beta = m.jaw_beta(open_s)
    Rr = m.rot_x(angle) if angle else np.eye(3)
    shift = np.array([m.MODULE_DX, 0, 0], float)
    replacements, added = [], []
    for sy in (1, -1):
        piv = np.array([m.PIVOT_X, m.JAW_Y * sy, 0.0])
        R = m.rot_z(beta * sy)
        ex, ey, ez = R[:, 0], R[:, 1], R[:, 2]
        out_dir = sy * ey

        def part(name, color, a, z, rot, note):
            pos = piv + a * L * ex + np.array([0, 0, z], float)
            p = m.Part(name, color, Rr @ pos + shift, Rr @ rot, 0, note)
            p.head = True
            return p
        beam = R @ m.BEAM_X_HOLES_Z
        along_z = R @ m.ALONG_Z
        bush_z = R @ m.BUSH_Z
        wheel = np.stack([ey, ez, ex], axis=1)  # 半轴套/轮胎局部 z（轴线）沿夹指
        # 10197：局部 −Y 轴头 → 朝魔方（+a），局部 −Z 轴头 → −Z，局部 X（横圆孔）→ Y×Z
        hub = np.stack([np.cross(-ex, ez), -ex, ez], axis=1)
        replacements += [
            part('32449.dat', m.C_JAW, 2.5, -15, beam, '压头薄梁-Z'),
            part('32449.dat', m.C_JAW, 2.5, 15, beam, '压头薄梁+Z'),
            part('4519.dat', m.C_AXLE, 3, 0, along_z, '夹指第7孔轴'),
            part('32123a.dat', m.C_BUSH, 3, -25, bush_z, '夹指第7孔轴半套'),
            part('32123a.dat', m.C_BUSH, 3, 25, bush_z, '夹指第7孔轴半套'),
            part('32062.dat', m.C_AXLE, 1, 0, along_z, '夹指第5孔轴'),
            part('32123a.dat', m.C_BUSH, SPACER_A, 0, wheel, '轮子垫距半套'),
            part('10197.dat', C_HUB, HUB_A, 0, hub, '轮座10197'),
            part('59895.dat', 0, WHEEL_A, 0, wheel, '轮胎59895'),
        ]
        added += [
            part('32123a.dat', m.C_BUSH, WHEEL_A, 0, wheel, '轮子半套'),
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
