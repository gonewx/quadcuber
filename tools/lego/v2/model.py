"""单臂原型 v2 (专业重设计版) 的乐高模型: 每个零件的位置、朝向和所属搭建步骤。

和 v1 (tools/lego/model.py) 的根本区别: **承重和传扭分开**。
- 机械臂整体装在一个 60 齿转盘 (18938 上半 + 18939 下半) 上, 由转盘承受机械臂的重量和弯矩;
- 马达只负责转动: 输出盘中间的十字孔插一根 6 号轴, 穿过转盘中孔, 插进 36 齿齿轮的十字孔,
  齿轮再用两个销带动机械臂。马达输出轴不再承受机械臂的弯矩。
- 转盘的固定方式照搬 LEGO 官方起重机 42082 / 42100 (LDraw 官方模型库几何核实): 7x5 框架和转盘的耳朵
  在同一平面, 框架开口正好套住耳朵, 销沿径向穿过 "耳朵 - 框架短边"。上下两半各一块这样的框架。

坐标 (LDU, LDraw 约定 -Y 向上, 1 孔距 = 20 LDU = 8mm):
- EV3 大马达在原点, 输出盘轴线沿 +X, 输出盘端面在 x = 30 (和 v1 相同);
- 转盘中心在 (60, 0, 0), 轴线沿 X; 下半 (固定) 占 x 30~65, 上半 (转动) 占 x 50~90;
- 魔方中心在 (520, 0, 0), 机械手从 -X 方向夹住魔方的 L 面; 固定叉从 -Z 方向卡住 B 面的中间一列;
- 桌面在 y = 150。

所有尺寸推导见 docs/lego/v2/README.md。
"""

import math
import os
import sys

import numpy as np

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

# ---- 朝向 --------------------------------------------------------------------

_AX = {"+x": (1, 0, 0), "-x": (-1, 0, 0), "+y": (0, 1, 0), "-y": (0, -1, 0), "+z": (0, 0, 1), "-z": (0, 0, -1)}


def orient(lx, ly, lz=None):
    """零件局部 x/y/z 轴在世界坐标中的方向 (lz 省略时按右手系补全)。"""
    a = np.array(_AX[lx] if isinstance(lx, str) else lx, float)
    b = np.array(_AX[ly] if isinstance(ly, str) else ly, float)
    c = np.cross(a, b) if lz is None else np.array(_AX[lz] if isinstance(lz, str) else lz, float)
    m = np.stack([a, b, c], axis=1)
    assert abs(np.linalg.det(m) - 1) < 1e-9, "朝向必须是右手系"
    return m


I = np.eye(3)
ALONG_X = I  # 销、轴 (局部 x 为轴线)
ALONG_Y = orient("+y", "-x")
ALONG_Z = orient("+z", "+y")
# 6558 长销的挡肩在局部 x = -10 (1 孔长一段在局部 -x 侧)。下面三个朝向把 1 孔长的一段朝向 +X/+Y/+Z。
LPIN_SHORT_X = orient("-x", "+y")
LPIN_SHORT_Y = orient("-y", "+x")
LPIN_SHORT_Z = orient("-z", "+y")
# 梁: 局部 z 为梁长方向, 局部 y 为孔轴
BEAM_X_HOLES_Z = orient("+y", "+z")
BEAM_X_HOLES_Y = orient("-z", "+y")
BEAM_Y_HOLES_Z = orient("-x", "+z")
BEAM_Y_HOLES_X = orient("+z", "+x")
BEAM_Z_HOLES_X = orient("-y", "+x")
BEAM_Z_HOLES_Y = I
# 7x5 框架: 局部 x 为 5 孔方向, 局部 z 为 7 孔方向, 局部 y 为厚度 (正面孔)
FRAME_XY_LONG_X = orient("+y", "+z")  # 竖放在 XY 平面, 长边沿 X
FRAME_YZ_LONG_Z = orient("+y", "-x")  # 竖放在 YZ 平面, 长边沿 Z
FRAME_XZ_LONG_X = orient("-z", "+y")  # 水平放, 长边沿 X
FRAME_XY_LONG_Y_5X = orient("+x", "+z")  # 竖放在 XY 平面, 长边沿 Y, 5 孔方向沿 X (机械臂侧板)
BUSH_X = orient("-z", "+y")  # 轴套 (局部 z 为轴线) 沿 X
BUSH_Y = orient("+x", "-z")
BUSH_Z = I
# 转盘: 局部 y 为转轴, 耳朵在局部 ±x。这样放: 转轴沿世界 X, 耳朵在 ±Z 两侧 (销孔沿 Z)。
TT_ROT = orient("+z", "-x")
# 36 齿齿轮: 局部 z 为转轴, 局部 (0, ±20) 两个销孔。这样放: 转轴沿 X, 销孔在 z = ±20。
GEAR_X = orient("+y", "+z")

# ---- 零件目录 -----------------------------------------------------------------

CATALOG = {
    "95658.dat": ("EV3 大马达", "solid"),
    "geekservo.dat": ("Geekservo 舵机 (灰色, 270°)", "solid"),
    "18938.dat": ("60 齿转盘 上半", "solid"),
    "18939.dat": ("60 齿转盘 下半", "solid"),
    "32498.dat": ("36 齿双面锥齿轮", "solid"),
    "64179.dat": ("7x5 框架", "solid"),
    "32278.dat": ("15 孔粗梁", "solid"),
    "40490.dat": ("9 孔粗梁", "solid"),
    "32524.dat": ("7 孔粗梁", "solid"),
    "32523.dat": ("3 孔粗梁", "solid"),
    "32316.dat": ("5 孔粗梁", "solid"),
    "6632.dat": ("3 孔细梁 (两端十字孔)", "solid"),
    "2780.dat": ("摩擦销 (2 孔长)", "pin"),
    "3673.dat": ("无摩擦销 (2 孔长, 灰色)", "pin"),
    "6558.dat": ("长摩擦销 (3 孔长)", "pin"),
    "32054.dat": ("带挡套长销 (3 孔长, 红色)", "pin"),
    "50451.dat": ("16 号轴", "axle"),
    "44294.dat": ("7 号轴", "axle"),
    "3706.dat": ("6 号轴", "axle"),
    "3713.dat": ("轴套", "bush"),
    "32123a.dat": ("半轴套", "bush"),
    "cube56.dat": ("56mm 魔方 (示意)", "other"),
}
# 检查用的销/轴长度 (LDU), 补到 check.CONNECTOR_LEN 里
CONNECTOR_LEN = {"3673.dat": 40, "50451.dat": 320, "44294.dat": 140, "3706.dat": 120}

C_FRAME = 71  # 浅灰
C_BASE = 72  # 深灰: 底座
C_BEAM = 0  # 黑
C_FORK = 4  # 红: 叉齿
C_PIN = 0
C_FPIN = 71  # 浅灰: 无摩擦销
C_LPIN = 1  # 蓝: 长销
C_SPIN = 4  # 红: 带挡套长销
C_AXLE = 0
C_BUSH = 72
C_SERVO = 72
C_MOTOR = 15
C_TT = 71
C_GEAR = 14  # 黄: 传扭齿轮, 醒目


class Part:
    def __init__(self, name, color, pos, rot, step, note=""):
        self.name = name
        self.color = color
        self.pos = np.array(pos, float)
        self.rot = np.array(rot, float)
        self.step = step
        self.note = note

    @property
    def kind(self):
        return CATALOG[self.name][1]

    def ldraw(self):
        m = self.rot.reshape(-1)
        nums = " ".join(_fmt(v) for v in list(self.pos) + list(m))
        return f"1 {self.color} {nums} {self.name}"

    def world(self, local):
        return self.rot @ np.asarray(local, float) + self.pos


def _fmt(v):
    v = round(float(v), 4)
    return f"{v:g}" if v != 0 else "0"


# ---- 关键尺寸 -----------------------------------------------------------------

CUBE_C = np.array([520.0, 0.0, 0.0])  # 魔方中心
CUBE_HALF = 70.0
TT_C = np.array([60.0, 0.0, 0.0])  # 转盘中心
TABLE_Y = 150.0

SERVO_C = np.array([150.0, 0.0, 0.0])  # 舵机本体中心 (在机械臂轴线上)
SERVO_ROT = orient("+z", "+y")  # 输出轴朝上 (-Y), 耳朵孔沿 X, 线缆出口朝 -Z
CRANK_C = np.array([150.0, 10.0])  # 舵机输出轴 (x, z), 沿 -Y 伸出
CRANK_Y = -45.0  # 曲柄 (3 孔细梁) 中面
LINK_Y = -60.0  # 连杆中面
CRANK_R = 20.0
LINK_L = 120.0
RISER_Z = 0.0  # 连杆另一头的销在叉子框架上边的 (x_ff - 40, z = 0) 孔


def slider_x(extended):
    """偏置曲柄滑块机构两个死点时连杆销 (叉子框架上) 的 x。"""
    e = abs(CRANK_C[1] - RISER_Z)
    l = LINK_L + CRANK_R if extended else LINK_L - CRANK_R
    return CRANK_C[0] + math.sqrt(l * l - e * e)


def fork_frame_x(extended=True):
    return slider_x(extended) + 40.0


STROKE = slider_x(True) - slider_x(False)
PRONG_TIP = 150.0  # 叉齿尖端相对叉子框架中心的 x


# ---- 搭建步骤 -----------------------------------------------------------------

STEPS = []
HEAD_STEPS = set()  # 随机械臂转动的步骤标题


def step(title, text, sub=None, attach=(), view=(35, 28), focus="all", head=False):
    """sub: 所属子组件名; view: 渲染视角 (yaw, pitch); focus: 取景 "all" / "head" / "new";
    head: 本步零件是否随机械臂转动。"""
    STEPS.append({"title": title, "text": text, "sub": sub, "attach": tuple(attach), "view": view, "focus": focus,
                  "head": head})
    if head:
        HEAD_STEPS.add(title)
    return len(STEPS)


def is_head(p):
    return STEPS[p.step - 1]["head"]


def build(fork_extended=True, head_angle=0.0, with_cube=True):
    """返回零件列表。head_angle: 机械臂绕 X 轴转过的角度 (度)。"""
    STEPS.clear()
    HEAD_STEPS.clear()
    parts = []

    def add(name, color, pos, rot, s, note=""):
        parts.append(Part(name, color, pos, rot, s, note))

    # ========== 一、底座 ==========
    # 底层 (y = 140, 贴桌面): 4 块 7x5 框架水平放, 长边沿 X, 首尾用短边侧孔各 3 个销连成 "脊梁"。
    # 做法同官方 42082: 框架共面拼接, 销穿短边侧孔。脊梁在机械臂转动范围之外 (z -250 ~ -150)。
    s = step("脊梁", "4 块 7x5 框架平放排成一排, 短边首尾相接。每个接头用 3 个摩擦销穿过两块框架短边的侧孔连起来。",
             view=(25, 50))
    for xc in (20, 160, 300, 440):
        add("64179.dat", C_BASE, (xc, 140, -200), FRAME_XZ_LONG_X, s)
    for x in (90, 230, 370):
        for z in (-220, -200, -180):
            add("2780.dat", C_PIN, (x, 140, z), ALONG_X, s)

    # 上层 (y = 120): 马达区前后两块框架。后块压在脊梁第一块上; 前块将来穿过转盘支座下框的开口。
    # 两块之间不能再放框架 (会撞转盘支座下框的短边), 用上面一根 15 孔梁把前后两块连起来。
    s = step("马达区底板", "两块 7x5 框架平放, 长边沿左右方向, 前后相隔 5 个孔距。一根 15 孔梁平放在两块框架上面 "
             "(左数第 1 列孔), 两头各用 2 个摩擦销竖着插进框架的正面孔。", sub="马达区底板", view=(30, 50))
    for zc in (-200, 0):
        add("64179.dat", C_BASE, (20, 120, zc), FRAME_XZ_LONG_X, s)
    add("32278.dat", C_BASE, (-40, 100, -100), BEAM_Z_HOLES_Y, s)
    for z in (-240, -160, -40, 40):
        add("2780.dat", C_PIN, (-40, 110, z), ALONG_Y, s)
    s = step("底脚", "把底板翻过来。一根 5 孔梁贴在前块框架下面 (左数第 2 列孔), 用 2 个摩擦销竖着插进框架正面孔。"
             "底脚和脊梁一样高, 让底板前块也落在桌面上。", sub="马达区底板", view=(30, -40))
    add("32316.dat", C_BASE, (0, 140, 0), BEAM_Z_HOLES_Y, s)
    for z in (-40, 40):
        add("2780.dat", C_PIN, (0, 130, z), ALONG_Y, s)
    s = step("装底板", "底板的后块压在脊梁第一块框架上, 两块框架的孔对齐, 4 个摩擦销竖着插进上下两层框架的正面孔"
             " (左数第 3、4 列; 第 1 列已被 15 孔梁的销占用, 第 2 列留给马达垫梁)。",
             attach=("马达区底板",), view=(30, 50))
    for x in (40, 80):
        for z in (-240, -160):
            add("2780.dat", C_PIN, (x, 130, z), ALONG_Y, s)

    # ========== 二、固定叉 ==========
    fb = np.array([CUBE_C[0], 0.0, -200.0])
    # 3 孔梁-框架/叉齿-3 孔梁三层夹心 (同 v1): 先在第一层插好全部长销, 再套中间层, 最后盖第三层。
    s = step("固定叉 1", "4 根 3 孔梁平放, 每根两端的孔各插一根蓝色长销的 1 孔长短头, 挡肩贴住梁, 共 8 根。"
             "7x5 框架套在靠里的 4 根长销上。", sub="固定叉", view=(120, 30))
    add("64179.dat", C_FRAME, fb, FRAME_YZ_LONG_Z, s)
    for sy in (1, -1):
        for z in (-180, -140):
            add("32523.dat", C_BEAM, (fb[0] - 20, 60 * sy, z), BEAM_Y_HOLES_X, s)
            for y in (40, 80):
                add("6558.dat", C_LPIN, (fb[0], y * sy, z), ALONG_X, s)
    s = step("固定叉 2", "两根叉齿 (7 孔梁) 套在靠外的 4 根长销上, 最后盖上另外 4 根 3 孔梁, 把框架和叉齿夹在中间。",
             sub="固定叉", view=(120, 30))
    for sy in (1, -1):
        add("32524.dat", C_FORK, (fb[0], 80 * sy, -120), BEAM_Z_HOLES_X, s)
        for z in (-180, -140):
            add("32523.dat", C_BEAM, (fb[0] + 20, 60 * sy, z), BEAM_Y_HOLES_X, s)
    # 固定叉框架正下方有下叉齿和夹心梁, 不能在下面直接垫框架。改在它后面同一平面接一块框架 (短边侧孔 3 个销),
    # 再在这块下面接一块落地 (长边侧孔 3 个销): 三块框架在同一竖直平面里拼成 L 形, 做法同转盘支座。
    s = step("固定叉立柱", "两块 7x5 框架和固定叉框架同向竖放: 一块接在固定叉框架后面 (短边对短边, 3 个摩擦销穿侧孔), "
             "另一块接在这块正下方 (长边对长边, 3 个摩擦销穿侧孔)。三块拼成一个 L 形竖板。",
             sub="固定叉", view=(120, 20))
    add("64179.dat", C_FRAME, fb + [0, 0, -140], FRAME_YZ_LONG_Z, s)
    add("64179.dat", C_FRAME, fb + [0, 100, -140], FRAME_YZ_LONG_Z, s)
    for y in (-20, 0, 20):
        add("2780.dat", C_PIN, (fb[0], y, fb[2] - 70), ALONG_Z, s)
    for z in (-40, 0, 40):
        add("2780.dat", C_PIN, (fb[0], 50, fb[2] - 140 + z), ALONG_Y, s)
    # 脊梁末端旁边再并一块框架 (长边侧孔 3 个销), 立柱底边夹在它和第 6 块框架之间:
    # 两根蓝色长销的 1 孔长一段在脊梁框架短边里, 挡肩落在脊梁和立柱之间。
    zb = -300.0  # 脊梁加宽那一排框架的中心 z (立柱底边的正面孔 z = -320、-280 正对它短边的侧孔)
    s = step("脊梁加宽", "第 5 块 7x5 框架平放, 并排接在脊梁最后一块框架的后面 (长边对长边, 3 个摩擦销穿侧孔)。",
             view=(140, 45))
    add("64179.dat", C_BASE, (440, 140, zb), FRAME_XZ_LONG_X, s)
    for x in (400, 440, 480):
        add("2780.dat", C_PIN, (x, 140, -250), ALONG_Z, s)
    s = step("装固定叉", "第 6 块 7x5 框架平放。两根蓝色长销从立柱内侧 (朝脊梁的一面) 把 2 孔长一段插进立柱底边的正面孔, "
             "穿过立柱, 再插进第 6 块框架短边的侧孔, 挡肩贴住立柱; 1 孔长的短头朝脊梁露出。把这一组推到第 5 块框架的末端, "
             "短头插进它短边的侧孔。", attach=("固定叉",), view=(140, 30))
    add("64179.dat", C_BASE, (fb[0] + 80, 140, zb), FRAME_XZ_LONG_X, s)
    for z in (zb - 20, zb + 20):
        add("6558.dat", C_LPIN, (fb[0], 140, z), ALONG_X, s)
    # 拉梁: 一根 9 孔梁穿过立柱下框的开口, 同时压住第 5 块框架、立柱底边和第 6 块框架, 立柱就不会前后晃。
    s = step("固定叉拉梁", "一根 9 孔梁平放, 从侧面穿过立柱下框的开口, 贴在底边上面。用 6 个摩擦销竖着向下插: "
             "2 个进第 5 块框架, 1 个进立柱底边的侧孔, 3 个进第 6 块框架。", view=(150, 45))
    add("40490.dat", C_BEAM, (fb[0] + 20, 120, fb[2] - 140), BEAM_X_HOLES_Y, s)
    for x in (-60, -20, 0, 20, 60, 100):
        add("2780.dat", C_PIN, (fb[0] + x, 130, fb[2] - 140), ALONG_Y, s)

    # ========== 三、转盘支座 ==========
    # 转盘下半和一块 7x5 框架在同一平面: 框架开口 (长 5 孔) 正好套住转盘两侧的耳朵,
    # 3+3 个摩擦销沿径向穿过 "框架短边 - 耳朵" (LEGO 42082 / 42100 的原厂做法)。
    s = step("转盘支座框架", "两块 7x5 框架竖着上下对齐, 3 个摩擦销竖着穿过相邻长边的侧孔, 拼成一块 7x10 的竖板。",
             sub="转盘支座", view=(60, 20))
    add("64179.dat", C_FRAME, (40, 0, 0), FRAME_YZ_LONG_Z, s)
    add("64179.dat", C_FRAME, (40, 100, 0), FRAME_YZ_LONG_Z, s)
    for z in (-40, 0, 40):
        add("2780.dat", C_PIN, (40, 50, z), ALONG_Y, s)
    s = step("转盘下半", "60 齿转盘的下半 (没有齿的一半) 放进上框的开口, 两侧的耳朵对准框架两条短边。"
             "每侧 3 个摩擦销从框架外面沿短边的侧孔插进耳朵, 共 6 个。", sub="转盘支座", view=(60, 20))
    add("18939.dat", C_TT, TT_C, TT_ROT, s)
    for sz in (1, -1):
        for y in (-20, 0, 20):
            add("2780.dat", C_PIN, (40, y, 50 * sz), ALONG_Z, s)
    s = step("装转盘支座", "转盘支座竖板从前面 (+X) 套进底板: 底板最前面那块框架从竖板下框的开口穿过去, 竖板底边落在桌面上, "
             "停在底板第 3 列孔 (从后往前数) 的位置。2 个摩擦销从下往上穿过竖板底边的侧孔, 插进底板。",
             attach=("转盘支座",), view=(-35, 25), focus="motor")
    for z in (-40, 40):
        add("2780.dat", C_PIN, (40, 130, z), ALONG_Y, s)

    # ========== 四、马达 ==========
    # 做法取自 LEGO 官方 EV3 模型 TRACK3R (31313): 框架插进马达尾部两片耳朵之间的缝, 两根红色带挡套长销
    # 从同一侧穿 耳朵-框架, 挡套留在耳朵外面 (蓝色长销的挡肩穿不过耳朵)。
    s = step("马达固定板", "7x5 框架竖着插进马达尾部两片耳朵之间的缝里。两根红色带挡套长销从没有输出盘的一侧"
             "插进耳朵的第 1、3 个孔, 穿过耳朵和框架, 推到挡套贴住耳朵。", sub="马达", view=(60, -20))
    add("95658.dat", C_MOTOR, (0, 0, 0), I, s)
    add("64179.dat", C_FRAME, (0, 40, -200), FRAME_YZ_LONG_Z, s)
    for z in (-180, -140):
        add("32054.dat", C_SPIN, (-20, 0, z), ALONG_X, s)
    # 马达现在只传扭矩, 固定板底边经一根垫梁用 3 个竖销压到底板上 (两根蓝色长销贯穿 固定板-垫梁-底板)。
    s = step("马达垫梁", "两根蓝色长销的 2 孔长一段从上往下插进 7 孔梁的第 2、6 个孔, 挡肩贴住梁的上面, 下面露出 1 孔。"
             "把这根梁放到底板后块上 (左数第 2 列), 露出的销头插进底板。", view=(-35, 30), focus="motor")
    add("32524.dat", C_BEAM, (0, 100, -200), BEAM_Z_HOLES_Y, s)
    for z in (-240, -160):
        add("6558.dat", C_LPIN, (0, 100, z), ALONG_Y, s)
    s = step("装马达", "马达固定板底边的中孔先插一个摩擦销。马达从上往下放: 固定板底边的 3 个孔同时套上两根蓝色短头和这个摩擦销, "
             "马达输出盘朝前, 正对转盘中孔。", attach=("马达",), view=(-35, 25), focus="motor")
    add("2780.dat", C_PIN, (0, 90, -200), ALONG_Y, s)

    # ========== 五、机械臂 ==========
    head = []  # 随机械臂转动的零件

    def hadd(name, color, pos, rot, s, note=""):
        head.append(Part(name, color, pos, rot, s, note))

    s = step("转盘上半与传动轴", "转盘上半 (有齿的一半) 压到下半上, 听到卡住的声音。7 号轴从前面穿过转盘中孔, "
             "插进马达输出盘中间的十字孔, 插到底 (前端露出转盘约 5 个孔距)。", view=(60, 25), focus="head", head=True)
    hadd("18938.dat", C_TT, TT_C, TT_ROT, s)
    hadd("44294.dat", C_AXLE, (60, 0, 0), ALONG_X, s)

    # 舵机座: 一根竖放的 7 孔梁 (孔沿 X), 7 个孔全部用上:
    #   z = 0 传动轴 (圆孔, 兼作轴承), ±20 传扭销, ±40 舵机长销, ±60 导轨。
    s = step("舵机座", "7 孔梁立起来 (孔朝前后)。两片 3 孔细梁一端的十字孔对齐梁的中孔, 一片朝上一片朝下, 贴在梁的后面; "
             "两个摩擦销穿过细梁中间的圆孔插进梁的第 3、5 孔。再把两根蓝色长销的 1 孔长短头插进梁的第 2、6 孔 "
             "(挡肩在梁前面), 舵机两个耳朵套上长销的 2 孔长一段, 输出轴朝上。", sub="机械臂", view=(215, 25), head=True)
    hadd("32524.dat", C_BEAM, (120, 0, 0), BEAM_Z_HOLES_X, s)
    hadd("6632.dat", C_BEAM, (95, 0, 0), orient("-y", "+x", "+z"), s)
    hadd("6632.dat", C_BEAM, (105, 0, 0), orient("+y", "+x", "-z"), s)
    for z in (-20, 20):
        hadd("2780.dat", C_PIN, (110, 0, z), ALONG_X, s)
    hadd("geekservo.dat", C_SERVO, SERVO_C, SERVO_ROT, s)
    for z in (-40, 40):
        hadd("6558.dat", C_LPIN, (140, 0, z), ALONG_X, s)

    # 侧板 + 导轨: 两块 7x5 框架竖放 (长边沿 Y), 导轨穿过侧板前后两条短边和舵机座两端: 3 个支点, 跨度 80。
    s = step("侧板与导轨", "两块 7x5 框架竖着放在舵机座两侧 (5 孔的方向朝前)。16 号轴从前往后依次穿过: 侧板前边中孔 → "
             "半轴套 → 舵机座端孔 → 轴套 → 侧板后边中孔, 后端和侧板后面齐平。最后在侧板前面再套一个半轴套。两边一样。",
             sub="机械臂", view=(40, 25), head=True)
    for sz in (1, -1):
        hadd("64179.dat", C_FRAME, (120, 0, 60 * sz), FRAME_XY_LONG_Y_5X, s)
        hadd("50451.dat", C_AXLE, (235, 0, 60 * sz), ALONG_X, s)
        hadd("3713.dat", C_BUSH, (100, 0, 60 * sz), BUSH_X, s)
        for x in (135, 175):
            hadd("32123a.dat", C_BUSH, (x, 0, 60 * sz), BUSH_X, s)
    s = step("装机械臂", "机械臂从前面套上转盘: 两块侧板夹住转盘上半的两个耳朵, 细梁的十字孔套进传动轴。"
             "每侧 2 个摩擦销从侧板外面穿进耳朵的上、下两个孔。", attach=("机械臂",), view=(40, 25), focus="head", head=True)
    for sz in (1, -1):
        for y in (-20, 20):
            hadd("2780.dat", C_PIN, (80, y, 50 * sz), ALONG_Z, s)

    # ========== 六、叉子 (滑块) ==========
    xf = fork_frame_x(fork_extended)
    s = step("叉子 1", "4 根 3 孔梁平放, 每根两端的孔各插一根蓝色长销的 1 孔长短头, 挡肩贴住梁, 共 8 根。"
             "7x5 框架套在靠里的 4 根长销上, 两根叉齿 (9 孔梁) 套在靠外的 4 根长销上。", sub="叉子", view=(30, 35),
             head=True)
    hadd("64179.dat", C_FRAME, (xf, 0, 0), FRAME_XY_LONG_X, s)
    for sy in (1, -1):
        hadd("40490.dat", C_FORK, (xf + 60, 80 * sy, 0), BEAM_X_HOLES_Z, s)
        for dx in (-20, 20):
            hadd("32523.dat", C_BEAM, (xf + dx, 60 * sy, -20), BEAM_Y_HOLES_Z, s)
            for y in (40, 80):
                hadd("6558.dat", C_LPIN, (xf + dx, y * sy, 0), ALONG_Z, s)
    s = step("叉子 2", "盖上另外 4 根 3 孔梁, 把框架和叉齿夹在中间。叉齿内侧的间距就是夹魔方的宽度。", sub="叉子",
             view=(30, 35), head=True)
    for sy in (1, -1):
        for dx in (-20, 20):
            hadd("32523.dat", C_BEAM, (xf + dx, 60 * sy, 20), BEAM_Y_HOLES_Z, s)
    # 滑块: 叉子框架两侧各一块同向框架, 4 根 7 号轴 + 轴套把三块框架连成一个盒子; 两侧框架的短边套在导轨上。
    s = step("滑块", "4 根 7 号轴依次穿过: 左框架 → 两个轴套 → 叉子框架 (四角的正面孔) → 两个轴套 → 右框架。"
             "三块框架平行、相距 3 个孔距, 组成一个盒子。", sub="叉子", view=(30, 35), head=True)
    for sz in (1, -1):
        hadd("64179.dat", C_FRAME, (xf, 0, 60 * sz), FRAME_XY_LONG_X, s)
    for dx in (-60, 60):
        for y in (-40, 40):
            hadd("44294.dat", C_AXLE, (xf + dx, y, 0), ALONG_Z, s)
            for z in (-40, -20, 20, 40):
                hadd("3713.dat", C_BUSH, (xf + dx, y, z), BUSH_Z, s)
    s = step("装叉子", "两根导轨的前端插进滑块两侧框架前后短边的中孔, 把叉子推到导轨上。叉子应能在导轨上顺滑地前后滑动。",
             attach=("叉子",), view=(40, 30), focus="head", head=True)

    # ========== 七、曲柄连杆 ==========
    # 死点时 曲柄中心 - 曲柄销 - 连杆销 共线。活动关节用无摩擦销 (灰色), 转动更顺, 舵机负载更小。
    rx = slider_x(fork_extended)
    crank_c = CRANK_C
    riser = np.array([rx, RISER_Z])
    d = riser - crank_c if fork_extended else crank_c - riser
    d = d / np.linalg.norm(d)
    pin = crank_c + CRANK_R * d
    d3 = np.array([d[0], 0.0, d[1]])
    s = step("曲柄与连杆", "3 孔细梁一端的十字孔套在舵机输出轴上当曲柄, 停在轴的最外端。7 孔梁当连杆: 一头用灰色无摩擦销接曲柄"
             "中间的圆孔, 另一头用灰色无摩擦销接叉子框架上边从后数第 1 个侧孔。"
             + ("(图中为夹紧位置, 曲柄指向前方)" if fork_extended else ""), view=(25, 40), focus="head", head=True)
    hadd("6632.dat", C_BEAM, (crank_c[0], CRANK_Y, crank_c[1]), orient(np.cross([0, 1, 0], d3), "+y", d3), s)
    e = riser - pin
    e3 = np.array([e[0], 0.0, e[1]]) / np.linalg.norm(e)
    mid = (pin + riser) / 2
    hadd("32524.dat", C_BEAM, (mid[0], LINK_Y, mid[1]), orient(np.cross([0, 1, 0], e3), "+y", e3), s)
    hadd("3673.dat", C_FPIN, (pin[0], LINK_Y, pin[1]), ALONG_Y, s)
    hadd("3673.dat", C_FPIN, (rx, -50, RISER_Z), ALONG_Y, s)

    if head_angle:
        a = math.radians(head_angle)
        rot = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
        for p in head:
            p.pos = rot @ p.pos
            p.rot = rot @ p.rot
    parts += head

    if with_cube:
        s = step("放入魔方", "舵机松开 (叉子退后), 从前方把魔方推进去, 直到背面卡进固定叉; 再让舵机夹紧。", view=(35, 28))
        add("cube56.dat", 16, CUBE_C, I, s)
    return parts


def to_ldr(parts, title="quadcuber single arm v2"):
    lines = [f"0 {title}", "0 Name: model.ldr", "0 Author: quadcuber", ""]
    cur = parts[0].step if parts else 1
    for p in sorted(parts, key=lambda p: p.step):
        if p.step != cur:
            lines.append("0 STEP")
            cur = p.step
        lines.append(p.ldraw())
    lines.append("0 STEP")
    return "\n".join(lines) + "\n"
