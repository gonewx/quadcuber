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
        s = step("马达固定板", "7x5 框架竖着插进马达底部两片耳朵之间的缝里, 用两根长销穿过 耳朵-框架-耳朵。", sub="马达",
                 view=(60, -20))
        add("95658.dat", C_MOTOR, (0, 0, 0), I, s)
        add("64179.dat", C_FRAME, (0, 40, -200), FRAME_YZ_LONG_Z, s)
        for z in (-180, -140):
            add("6558.dat", C_LPIN, (0, 0, z), ALONG_X, s)
        s = step("装马达", "马达固定板的尾端对准左边立板, 两根长销穿过 固定板-横梁-立板。", attach=("马达",))
        for y in (20, 60):
            add("6558.dat", C_LPIN, (0, y, -280), ALONG_Z, s)
    else:
        s = step("马达支架", "7x5 框架竖着装在左边立板前面, 两根长销穿过 框架-横梁-立板。")
        add("64179.dat", C_FRAME, (0, 40, -200), FRAME_YZ_LONG_Z, s)
        for y in (20, 60):
            add("6558.dat", C_LPIN, (0, y, -280), ALONG_Z, s)
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

    # ========== 三、固定叉 ==========
    fb = np.array([480.0 + D, 0.0, -200.0])
    s = step("固定叉 1", "7x5 框架两侧各用两根长销夹上 3 孔梁。", sub="固定叉", view=(120, 30))
    add("64179.dat", C_FRAME, fb, FRAME_YZ_LONG_Z, s)
    for sy in (1, -1):
        for z in (-180, -140):
            for x in (460 + D, 500 + D):
                add("32523.dat", C_BEAM, (x, 60 * sy, z), BEAM_Y_HOLES_X, s)
            add("6558.dat", C_LPIN, (480 + D, 40 * sy, z), ALONG_X, s)
    s = step("固定叉 2", "装上两根叉齿 (7 孔梁), 长销穿过 3 孔梁-叉齿-3 孔梁。", sub="固定叉", view=(120, 30))
    for sy in (1, -1):
        add("32524.dat", C_FORK, (480 + D, 80 * sy, -120), BEAM_Z_HOLES_X, s)
        for z in (-180, -140):
            add("6558.dat", C_LPIN, (480 + D, 80 * sy, z), ALONG_X, s)
    s = step("装固定叉", "固定叉的尾端对准右边立板, 两根长销穿过 固定叉-横梁-立板。", attach=("固定叉",),
             view=(150, 28))
    for y in (-20, 20):
        add("6558.dat", C_LPIN, (480 + D, y, -280), ALONG_Z, s)

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

    s = step("舵机", "舵机两个耳朵上的销孔对准转动座上边的第 1、3 个孔, 各插一根长销。"
             "输出轴朝向图中前方, 并且偏向魔方一侧。", view=(35, 28), focus="head")
    hadd("geekservo.dat", C_SERVO, SERVO_C + [D, 0, 0], orient("+x", "-z"), s)
    for x in (60 + D, 140 + D):
        hadd("6558.dat", C_LPIN, (x, -60, 0), ALONG_Y, s)

    xf = fork_frame_x(fork_extended)
    s = step("叉子 1", "7x5 框架两侧各用两根长销夹上 3 孔梁。", sub="叉子", view=(30, 35))
    hadd("64179.dat", C_FRAME, (xf, 0, 0), FRAME_XY_LONG_X, s)
    for sy in (1, -1):
        for dx in (-20, 20):
            for z in (-20, 20):
                hadd("32523.dat", C_BEAM, (xf + dx, 60 * sy, z), BEAM_Y_HOLES_Z, s)
            hadd("6558.dat", C_LPIN, (xf + dx, 40 * sy, 0), ALONG_Z, s)
    s = step("叉子 2", "装上两根叉齿 (9 孔梁)。叉齿内侧的间距就是夹魔方的宽度。", sub="叉子", view=(30, 35))
    for sy in (1, -1):
        hadd("40490.dat", C_FORK, (xf + 40, 80 * sy, 0), BEAM_X_HOLES_Z, s)
        for dx in (-20, 20):
            hadd("6558.dat", C_LPIN, (xf + dx, 80 * sy, 0), ALONG_Z, s)

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
