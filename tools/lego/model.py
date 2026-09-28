"""单臂原型 (机械手 + 测试架) 的乐高模型: 每个零件的位置、朝向和所属搭建步骤。

坐标 (LDU, LDraw 约定 -Y 向上):
- EV3 大马达在原点, 输出盘轴线沿 +X, 输出盘端面在 x = 30;
- 魔方中心在 (480 + DX, 0, 0), 机械手从 -X 方向夹住魔方的 L 面;
- 两种马达版本: 大马达 (DX = 0) 和中马达 (DX = 20, 中马达需要多一层联轴件, 机械手整体前移 1 个孔距);
- 固定叉从 -Z 方向卡住魔方 B 面的中间一列 (固定中间层);
- 桌面在 y = 150。

所有尺寸推导见 docs/lego/README.md 的 "设计说明"。
"""

import math

import numpy as np

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
# 常用朝向
ALONG_X = I  # 销、轴 (局部 x 为轴线)
ALONG_Y = orient("+y", "-x")
ALONG_Z = orient("+z", "+y")
# 6558 长销的挡肩在局部 x = -10 (1 孔长一段在局部 -x 侧)。下面三个朝向把 1 孔长的一段朝向 +X/+Y/+Z。
LPIN_SHORT_X = orient("-x", "+y")
LPIN_SHORT_Y = orient("-y", "+x")
LPIN_SHORT_Z = orient("-z", "+y")
BEAM_X_HOLES_Z = orient("+y", "+z")  # 梁沿 X, 孔沿 Z (局部 z 为梁长方向, 局部 y 为孔轴)
BEAM_Y_HOLES_Z = orient("-x", "+z")
BEAM_Y_HOLES_X = orient("+z", "+x")
BEAM_Z_HOLES_X = orient("-y", "+x")
BEAM_Z_HOLES_Y = I
BEAM_X_HOLES_Y = orient("-z", "+y")
FRAME_XY_LONG_X = orient("+y", "+z")  # 7x5 框架在 XY 平面, 长边沿 X
FRAME_XY_LONG_Y = orient("+x", "-z")  # 7x5 框架在 XY 平面, 长边沿 Y
FRAME_YZ_LONG_Z = orient("+y", "-x")  # 7x5 框架在 YZ 平面, 长边沿 Z
FRAME_XZ_LONG_X = orient("-z", "+y")  # 7x5 框架水平放置, 长边沿 X
BUSH_X = orient("-z", "+y")  # 轴套 (局部 z 为轴线) 沿 X
BUSH_Y = orient("+x", "-z")  # 轴套沿 Y
BUSH_Z = I

# ---- 零件目录 -----------------------------------------------------------------

# 零件号: (中文名, 类别)  类别: solid 结构件 / pin 销 / axle 轴 / bush 轴套 / other
CATALOG = {
    "95658.dat": ("EV3 大马达", "solid"),
    "99455.dat": ("EV3 中马达", "solid"),
    "geekservo.dat": ("Geekservo 舵机 (灰色, 270°)", "solid"),
    "64179.dat": ("7x5 框架", "solid"),
    "32278.dat": ("15 孔粗梁", "solid"),
    "40490.dat": ("9 孔粗梁", "solid"),
    "32524.dat": ("7 孔粗梁", "solid"),
    "32523.dat": ("3 孔粗梁", "solid"),
    "6632.dat": ("3 孔细梁 (两端十字孔)", "solid"),
    "2780.dat": ("摩擦销 (2 孔长)", "pin"),
    "6558.dat": ("长摩擦销 (3 孔长)", "pin"),
    "43093.dat": ("轴销 (一半轴一半销)", "pin"),
    "32054.dat": ("带挡套长销 (3 孔长, 红色)", "pin"),
    "3708.dat": ("12 号轴", "axle"),
    "3705.dat": ("4 号轴", "axle"),
    "32073.dat": ("5 号轴", "axle"),
    "3713.dat": ("轴套", "bush"),
    "32123a.dat": ("半轴套", "bush"),
    "cube56.dat": ("56mm 魔方 (示意)", "other"),
}

# 颜色 (LDraw 编号), 实物颜色不限
C_FRAME = 71  # 浅灰
C_BEAM = 0  # 黑
C_FORK = 4  # 红: 叉子
C_PIN = 0
C_LPIN = 1  # 蓝: 长销
C_APIN = 1
C_SPIN = 4  # 红: 带挡套长销 (EV3 套装里的颜色)
C_AXLE = 0
C_AXLE5 = 72  # 深灰, 与淡化的背景零件区分
C_BUSH = 72
C_SERVO = 72
C_MOTOR = 15


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

MOTOR = "large"  # 当前版本: "large" / "medium", 由 build() 设置
DX = 0.0  # 机械手和测试架前端相对大马达版本的 x 偏移


def cube_c():
    return np.array([480.0 + DX, 0.0, 0.0])  # 魔方中心



CUBE_HALF = 70.0  # 56mm 魔方
SERVO_C = np.array([100.0, -70.0, 0.0])  # 舵机本体中心 (装在转动座朝上的一边)
CRANK_C = np.array([110.0, -70.0])  # 舵机输出轴 (x, y), 沿 +Z 伸出
CRANK_R = 20.0
LINK_L = 120.0
RISER_Y = -40.0  # 叉子上连杆立轴的 y


def slider_x(extended):
    """偏置曲柄滑块机构两个死点时立轴的 x。"""
    e = abs(CRANK_C[1] - RISER_Y)
    l = LINK_L + CRANK_R if extended else LINK_L - CRANK_R
    return CRANK_C[0] + DX + math.sqrt(l * l - e * e)


def fork_frame_x(extended=True):
    return slider_x(extended) + 60.0  # 立轴在叉子框架的 (x_ff - 60, 40) 孔


STROKE = slider_x(True) - slider_x(False)


# ---- 搭建步骤 -----------------------------------------------------------------
# 每步: (标题, 说明)。子组件的步骤在主步骤之前, 用 sub 标记。

STEPS = []


def step(title, text, sub=None, attach=(), view=(35, 28), focus="all"):
    """sub: 所属子组件名 (子组件单独搭, 之后在 attach 该子组件的主步骤装上去);
    view: 渲染视角 (yaw, pitch); focus: 取景范围 "all" 全部可见零件 / "head" 机械手 / "new" 本步零件。"""
    STEPS.append({"title": title, "text": text, "sub": sub, "attach": tuple(attach), "view": view, "focus": focus})
    return len(STEPS)


def build(fork_extended=True, head_angle=0.0, with_cube=True, motor="large"):
    """返回零件列表。head_angle: 机械手绕 X 轴转过的角度 (度), 用于检查转动时的干涉。
    motor: "large" EV3 大马达 / "medium" EV3 中马达。"""
    global MOTOR, DX
    MOTOR = motor
    DX = 0.0 if motor == "large" else 20.0
    D = DX
    STEPS.clear()
    parts = []

    def add(name, color, pos, rot, s, note=""):
        parts.append(Part(name, color, pos, rot, s, note))

    # ========== 一、底座 ==========
    s = step("底座 1", "7x5 框架平放, 下面垫两根 15 孔梁作为脚。", sub="底座")
    add("64179.dat", C_FRAME, (40, 120, -260), FRAME_XZ_LONG_X, s)
    for x in (-20, 100):
        add("32278.dat", C_BEAM, (x, 140, -160), BEAM_Z_HOLES_Y, s)
        for z in (-300, -220):
            add("2780.dat", C_PIN, (x, 130, z), ALONG_Y, s)

    s = step("底座 2", "同样再做一组脚。", sub="底座")
    add("64179.dat", C_FRAME, (520 + D, 120, -260), FRAME_XZ_LONG_X, s)
    for x in (460 + D, 580 + D):
        add("32278.dat", C_BEAM, (x, 140, -160), BEAM_Z_HOLES_Y, s)
        for z in (-300, -220):
            add("2780.dat", C_PIN, (x, 130, z), ALONG_Y, s)

    s = step("立板", "两块 7x5 框架竖着插在两组脚上。", attach=("底座",))
    add("64179.dat", C_FRAME, (40, 40, -300), FRAME_XY_LONG_Y, s)  # P0
    for x in (20, 60):
        add("2780.dat", C_PIN, (x, 110, -300), ALONG_Y, s)
    add("64179.dat", C_FRAME, (520 + D, 40, -300), FRAME_XY_LONG_Y, s)  # P480
    for x in (500 + D, 540 + D):
        add("2780.dat", C_PIN, (x, 110, -300), ALONG_Y, s)

    s = step("横梁", "三排横梁装在两块立板的前面。每排由两根 15 孔梁接成, 接头处先空着。")
    for y in (-20, 20, 60):
        add("32278.dat", C_BEAM, (140, y, -280), BEAM_X_HOLES_Z, s)
        add("32278.dat", C_BEAM, (440, y, -280), BEAM_X_HOLES_Z, s)
        add("2780.dat", C_PIN, (80, y, -290), ALONG_Z, s)
        add("2780.dat", C_PIN, (560 + D, y, -290), ALONG_Z, s)
        if y == -20:
            add("2780.dat", C_PIN, (0, y, -290), ALONG_Z, s)
        if y == 60:
            add("2780.dat", C_PIN, (480 + D, y, -290), ALONG_Z, s)

    s = step("接头", "用一块 7x5 框架盖住三排横梁的接头。")
    add("64179.dat", C_FRAME, (300, 40, -260), FRAME_XY_LONG_Y, s)
    for x in (260, 340):
        for y in (-20, 20, 60):
            add("2780.dat", C_PIN, (x, y, -270), ALONG_Z, s)

    # ========== 二、马达 ==========
    if motor == "large":
        # 第二个固定点: 马达尾端面下排 3 个销孔 (y=-20, 孔深 z -210..-190) 正对横梁上排, 中间空 3 个孔距。
        # 填 3 层 7 孔梁做垫块, 层间错开插摩擦销; 抗机械手下垂的力矩 (绕 z 轴) 时,
        # 垫块和尾部耳朵在竖直方向相距约 1 个孔距, 比只靠耳朵里两根销牢靠。马达方箱挡住了颈部鳍片往后的路。
        s = step("后垫块", "三根 7 孔梁叠在一起: 前两层用两个摩擦销连 (第 4、6 孔), "
                 "后两层用两个摩擦销连 (第 1、3 孔)。", sub="后垫块", view=(150, 25))
        for z in (-220, -240, -260):
            add("32524.dat", C_BEAM, (40, -20, z), BEAM_X_HOLES_Z, s)
        for x in (40, 80):
            add("2780.dat", C_PIN, (x, -20, -230), ALONG_Z, s)
        for x in (-20, 20):
            add("2780.dat", C_PIN, (x, -20, -250), ALONG_Z, s)
        s = step("装后垫块", "先在最上排横梁的第 3、4 孔各插一个摩擦销, 露出半截; 把后垫块的后层第 4、5 孔"
                 "套上去, 垫块左端比横梁多出一个孔。", attach=("后垫块",), view=(150, 25))
        for x in (40, 60):
            add("2780.dat", C_PIN, (x, -20, -270), ALONG_Z, s)
        # 做法取自 LEGO 官方 EV3 模型 TRACK3R (31313, LDraw 官方模型库): 框架一端插进马达尾部两片耳朵之间的缝,
        # 两根红色带挡套长销 (32054) 从同一侧插入, 2 孔长的销段穿过 耳朵-框架, 挡套留在耳朵外面。
        # 两片耳朵是马达上的同一个零件: 蓝色长销 (6558) 的挡肩要穿过一片耳朵才能到位, 装不上。
        s = step("马达固定板", "7x5 框架竖着插进马达尾部两片耳朵之间的缝里。两根红色带挡套长销从没有输出盘的一侧"
                 "插进耳朵的第 1、3 个孔, 穿过耳朵和框架, 推到挡套贴住耳朵。本步不用蓝色长销 (它的挡肩穿不过耳朵)。",
                 sub="马达", view=(60, -20))
        add("95658.dat", C_MOTOR, (0, 0, 0), I, s)
        add("64179.dat", C_FRAME, (0, 40, -200), FRAME_YZ_LONG_Z, s)
        for z in (-180, -140):
            add("32054.dat", C_SPIN, (-20, 0, z), ALONG_X, s)
        s = step("装马达", "两根蓝色长销从前面把 2 孔长的一段插进横梁和左边立板, 挡肩贴住横梁, 1 孔长的一段朝前露出。"
                 "后垫块前层的第 1、2、3 孔各插一个摩擦销, 露出半截。马达整体往后推: 固定板尾端的两个孔套上蓝色短头, "
                 "同时马达尾端面下排三个孔套上三个黑色销, 推到贴紧。", attach=("马达",))
        for y in (20, 60):
            add("6558.dat", C_LPIN, (0, y, -280), LPIN_SHORT_Z, s)
        for x in (-20, 0, 20):
            add("2780.dat", C_PIN, (x, -20, -210), ALONG_Z, s)
    else:
        s = step("马达支架", "两根蓝色长销从前面把 2 孔长的一段插进横梁和左边立板, 挡肩贴住横梁; "
                 "7x5 框架竖着套在露出的短头上。")
        add("64179.dat", C_FRAME, (0, 40, -200), FRAME_YZ_LONG_Z, s)
        for y in (20, 60):
            add("6558.dat", C_LPIN, (0, y, -280), LPIN_SHORT_Z, s)
        s = step("马达面板", "15 孔梁贴在中马达正面 (有红色输出孔的一面): 两个摩擦销插进输出孔左右两侧的孔, "
                 "梁中间的孔正对输出孔。再把 4 号轴穿过这个孔插进输出孔, 轴应能跟着马达自由转动。", sub="马达",
                 view=(75, 20))
        add("99455.dat", C_MOTOR, (10, 0, 0), orient("+z", "+y"), s)
        add("32278.dat", C_BEAM, (20, 0, -120), BEAM_Z_HOLES_X, s)
        for z in (-20, 20):
            add("2780.dat", C_PIN, (10, 0, z), ALONG_X, s)
        add("3705.dat", C_AXLE, (30, 0, 0), ALONG_X, s)
        s = step("装马达", "15 孔梁的另一头贴在马达支架侧面下排的 4 个孔上, 用 4 个摩擦销固定。", attach=("马达",),
                 view=(60, 30), focus="new")
        for z in (-260, -220, -180, -140):
            add("2780.dat", C_PIN, (10, 0, z), ALONG_X, s)

        s = step("承重横梁", "中马达固定端补强：在原有两根底脚上横放两根 7 孔梁，"
                 "每根梁两端各用一个摩擦销连接底脚。两根横梁相距 4 个孔距，"
                 "靠近马达的一根位于底脚前端向内第 4 孔。无需拆卸机械手。",
                 view=(125, 25), focus="mount")
        for z in (-160, -80):
            add("32524.dat", C_BEAM, (40, 120, z), BEAM_X_HOLES_Y, s)
            for x in (-20, 100):
                add("2780.dat", C_PIN, (x, 130, z), ALONG_Y, s)

        s = step("承重垫梁", "在两根新横梁的正中间纵放一根 9 孔梁。先对齐不插销："
                 "先完成上方横销连接，最后用无挡肩的 4 号轴和半轴套连接底部三层。",
                 view=(125, 25), focus="mount")
        add("40490.dat", C_BEAM, (40, 100, -120), BEAM_Z_HOLES_Y, s)

        s = step("先装上方横销", "本步不要插底部贯穿轴。先把两根 2 孔长摩擦销各插半截到"
                 "原 15 孔马达固定梁的对应孔，另一半朝新框架一侧伸出。托住马达固定端，"
                 "将竖框上边两孔对准横销，横向推入到位。框架7孔长边水平，底边对准垫梁；"
                 "底部此时保持未锁定，不要强扳框架同时套两种方向的销。",
                 view=(125, 25), focus="mount")
        add("64179.dat", C_FRAME, (40, 40, -120), FRAME_YZ_LONG_Z, s)
        for z in (-100, -60):
            add("2780.dat", C_PIN, (30, 0, z), ALONG_X, s)

        s = step("底部穿轴并限位", "本步不用蓝色长销。上方横销装好后，托住机械手，将整套底座侧放，"
                 "露出底部。两根无挡肩的 4 号轴分别从底下向上穿过横梁、垫梁、竖框底边，"
                 "两端各露出半个孔距。每端套一个半轴套，共 4 个，贴住结构即可，不要夹变形。"
                 "上端半轴套从竖框中央开口安装，下端从底座下方安装。再平放底座，检查下垂和转动间隙。",
                 view=(125, 25), focus="mount")
        for z in (-160, -80):
            add("3705.dat", C_AXLE, (40, 100, z), ALONG_Y, s)
            for y in (65, 135):
                add("32123a.dat", C_BUSH, (40, y, z), BUSH_Y, s)

    # ========== 三、固定叉 ==========
    fb = np.array([480.0 + D, 0.0, -200.0])
    # 3 孔梁-框架/叉齿-3 孔梁三层夹心: 长销挡肩在第一层和中间层之间, 所以先在第一层插好全部长销,
    # 再套中间层, 最后盖第三层 (两边 3 孔梁一旦连住, 就不能再往中间穿长销)。
    s = step("固定叉 1", "4 根 3 孔梁平放, 每根两端的孔各插一根蓝色长销的 1 孔长短头, 挡肩贴住梁, 共 8 根。"
             "7x5 框架套在靠里的 4 根长销上。", sub="固定叉", view=(120, 30))
    add("64179.dat", C_FRAME, fb, FRAME_YZ_LONG_Z, s)
    for sy in (1, -1):
        for z in (-180, -140):
            add("32523.dat", C_BEAM, (460 + D, 60 * sy, z), BEAM_Y_HOLES_X, s)
            for y in (40, 80):
                add("6558.dat", C_LPIN, (480 + D, y * sy, z), ALONG_X, s)
    s = step("固定叉 2", "两根叉齿 (7 孔梁) 套在靠外的 4 根长销上, 最后盖上另外 4 根 3 孔梁, 把框架和叉齿夹在中间。",
             sub="固定叉", view=(120, 30))
    for sy in (1, -1):
        add("32524.dat", C_FORK, (480 + D, 80 * sy, -120), BEAM_Z_HOLES_X, s)
        for z in (-180, -140):
            add("32523.dat", C_BEAM, (500 + D, 60 * sy, z), BEAM_Y_HOLES_X, s)
    s = step("装固定叉", "两根蓝色长销从前面把 2 孔长的一段插进横梁和右边立板, 挡肩贴住横梁; "
             "固定叉的尾端套在露出的短头上。", attach=("固定叉",), view=(150, 28))
    for y in (-20, 20):
        add("6558.dat", C_LPIN, (480 + D, y, -280), LPIN_SHORT_Z, s)

    # ========== 四、机械手 ==========
    head = []  # 随机械手转动的零件

    def hadd(name, color, pos, rot, s, note=""):
        head.append(Part(name, color, pos, rot, s, note))

    if motor == "large":
        s = step("转动座", "7x5 框架的短边插在马达输出盘上: 上下两个摩擦销, 中间一个轴销 (轴的一头插进输出盘)。",
                 view=(60, 25), focus="head")
        for y in (-20, 20):
            hadd("2780.dat", C_PIN, (30, y, 0), ALONG_X, s)
        hadd("43093.dat", C_APIN, (30, 0, 0), orient("-x", "+y"), s)
    else:
        s = step("联轴", "两片 3 孔细梁用一端的十字孔套在 4 号轴上, 一片朝上、一片朝下, 各插一个摩擦销。",
                 view=(60, 25), focus="head")
        hadd("6632.dat", C_BEAM, (35, 0, 0), orient("+z", "+x"), s)
        hadd("6632.dat", C_BEAM, (45, 0, 0), orient("-z", "+x"), s)
        hadd("2780.dat", C_PIN, (50, 20, 0), ALONG_X, s)
        hadd("2780.dat", C_PIN, (60, -20, 0), ALONG_X, s)
        s = step("转动座", "7x5 框架的短边对准两个摩擦销和 4 号轴插上去: 销进上下两个孔, 轴进中间的孔。",
                 view=(60, 25), focus="head")
    hadd("64179.dat", C_FRAME, (100 + D, 0, 0), FRAME_XY_LONG_X, s)

    s = step("舵机", "两根蓝色长销的 2 孔长一段插满舵机两个耳朵的销孔 (耳朵厚 2 孔), 挡肩贴住耳朵, "
             "1 孔长的短头插进转动座上边的第 1、3 个孔。输出轴朝向图中前方, 并且偏向魔方一侧。",
             view=(35, 28), focus="head")
    hadd("geekservo.dat", C_SERVO, SERVO_C + [D, 0, 0], orient("+x", "-z"), s)
    for x in (60 + D, 140 + D):
        hadd("6558.dat", C_LPIN, (x, -60, 0), LPIN_SHORT_Y, s)

    xf = fork_frame_x(fork_extended)
    s = step("叉子 1", "4 根 3 孔梁平放, 每根两端的孔各插一根蓝色长销的 1 孔长短头, 挡肩贴住梁, 共 8 根。"
             "7x5 框架套在靠里的 4 根长销上。", sub="叉子", view=(30, 35))
    hadd("64179.dat", C_FRAME, (xf, 0, 0), FRAME_XY_LONG_X, s)
    for sy in (1, -1):
        for dx in (-20, 20):
            hadd("32523.dat", C_BEAM, (xf + dx, 60 * sy, -20), BEAM_Y_HOLES_Z, s)
            for y in (40, 80):
                hadd("6558.dat", C_LPIN, (xf + dx, y * sy, 0), ALONG_Z, s)
    s = step("叉子 2", "两根叉齿 (9 孔梁) 套在靠外的 4 根长销上, 最后盖上另外 4 根 3 孔梁, 把框架和叉齿夹在中间。"
             "叉齿内侧的间距就是夹魔方的宽度。", sub="叉子", view=(30, 35))
    for sy in (1, -1):
        hadd("40490.dat", C_FORK, (xf + 40, 80 * sy, 0), BEAM_X_HOLES_Z, s)
        for dx in (-20, 20):
            hadd("32523.dat", C_BEAM, (xf + dx, 60 * sy, 20), BEAM_Y_HOLES_Z, s)

    s = step("导轨", "两根 12 号轴穿过叉子框架两端的孔, 再在叉子后面套上半轴套。叉子应能在轴上顺滑地前后滑动。",
             sub="叉子", view=(30, 35))
    for y in (-20, 20):
        hadd("3708.dat", C_AXLE, (250 + D, y, 0), ALONG_X, s)
        hadd("32123a.dat", C_BUSH, (175 + D, y, 0), BUSH_X, s)

    s = step("装叉子", "导轨的另一头插进转动座远端的两个孔, 从框架中间的空档里给每根轴套上一个轴套, 把导轨卡住。",
             attach=("叉子",), view=(40, 30), focus="head")
    for y in (-20, 20):
        hadd("3713.dat", C_BUSH, (140 + D, y, 0), BUSH_X, s)

    rx = slider_x(fork_extended)
    s = step("立轴", "5 号轴竖着穿过叉子框架后部的孔: 框架下面一个半轴套, 上面两个轴套。", view=(25, 35), focus="mech")
    hadd("32073.dat", C_AXLE5, (rx, RISER_Y, 30), ALONG_Z, s)
    hadd("32123a.dat", C_BUSH, (rx, RISER_Y, -15), BUSH_Z, s)
    for z in (20, 40):
        hadd("3713.dat", C_BUSH, (rx, RISER_Y, z), BUSH_Z, s)

    # 曲柄与连杆: 死点时 曲柄中心 - 曲柄销 - 立轴 共线
    crank_c = CRANK_C + [D, 0]
    riser = np.array([rx, RISER_Y])
    d = riser - crank_c if fork_extended else crank_c - riser
    d = d / np.linalg.norm(d)
    pin = crank_c + CRANK_R * d
    s = step("曲柄", "3 孔细梁一端的十字孔套在舵机输出轴上, 当作曲柄。曲柄停在输出轴的最外端、和轴端齐平, "
             "和舵机外壳之间留约 1.6mm 空隙是正常的 (这样连杆两头一样高); 不要推到底。" + ("(图中为夹紧位置)" if fork_extended else ""),
             view=(25, 35), focus="mech")
    dz = np.array([d[0], d[1], 0.0])
    hadd("6632.dat", C_BEAM, (crank_c[0], crank_c[1], 45), orient(np.cross([0, 0, 1], dz), "+z", dz), s)

    e = riser - pin
    e3 = np.array([e[0], e[1], 0.0]) / np.linalg.norm(e)
    mid = (pin + riser) / 2
    s = step("连杆", "7 孔梁当连杆: 一头套在立轴上, 另一头用摩擦销接曲柄, 最后在立轴顶上套一个半轴套。",
             view=(25, 35), focus="mech")
    hadd("32524.dat", C_BEAM, (mid[0], mid[1], 60), orient(np.cross([0, 0, 1], e3), "+z", e3), s)
    hadd("2780.dat", C_PIN, (pin[0], pin[1], 60), ALONG_Z, s)
    hadd("32123a.dat", C_BUSH, (rx, RISER_Y, 75), BUSH_Z, s)

    if head_angle:
        a = math.radians(head_angle)
        rot = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
        for p in head:
            p.pos = rot @ p.pos
            p.rot = rot @ p.rot
    parts += head

    if with_cube:
        s = step("放入魔方", "舵机松开 (叉子退后), 从前方把魔方推进去, 直到背面卡进固定叉; 再让舵机夹紧。",
                 view=(35, 28))
        add("cube56.dat", 16, cube_c(), I, s)
    return parts


def head_names():
    return {"联轴", "转动座", "舵机", "叉子 1", "叉子 2", "导轨", "装叉子", "立轴", "曲柄", "连杆"}


def to_ldr(parts, title="quadcuber single arm"):
    lines = [f"0 {title}", "0 Name: model.ldr", "0 Author: quadcuber", ""]
    cur = parts[0].step if parts else 1
    for p in sorted(parts, key=lambda p: p.step):
        if p.step != cur:
            lines.append("0 STEP")
            cur = p.step
        lines.append(p.ldraw())
    lines.append("0 STEP")
    return "\n".join(lines) + "\n"
