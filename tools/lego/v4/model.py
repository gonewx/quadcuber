"""四臂整机 v4：反向连杆＋机械头推杆导向。

基准为双侧轮胎压头＋防翻折限位版 (提交 b9aa5d5)。改动: 十字接头移到连杆前方, 往后拉夹紧、往前推张开;
推杆导向为一个 32034, 卡在转盘上半两个凸耳之间, 两根 2 号轴挂在凸耳中间孔上;
侧板内侧梁中段让给连杆; 舵机侧往后拉夹紧, 名义夹紧点在曲柄折叠死点前 25°, 舵机连杆为 7 孔粗梁第 1、7 孔。
机械头长度、底座、竖墙、马达和舵机位置都不变。说明见 docs/lego/v4/README.md。"""

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


def rot_x(deg):
    a = math.radians(deg)
    return np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])


def rot_z(rad):
    return np.array([[math.cos(rad), -math.sin(rad), 0], [math.sin(rad), math.cos(rad), 0], [0, 0, 1]])


I = np.eye(3)
ALONG_X = I  # 销、轴 (局部 x 为轴线)
ALONG_Y = orient("+y", "-x")
ALONG_Z = orient("+z", "+y")
# 6558 长销的挡肩在局部 x = -10 (1 孔长一段在局部 -x 侧)。LPIN_SHORT_* 把 1 孔长的一段朝向 +X/+Y/+Z。
LPIN_SHORT_X = orient("-x", "+y")
LPIN_SHORT_Y = orient("-y", "+x")
LPIN_SHORT_Z = orient("-z", "+y")
LPIN_SHORT_MZ = orient("+z", "+y")  # 1 孔长一段朝 -Z
# 梁: 局部 z 为梁长方向, 局部 y 为孔轴
BEAM_X_HOLES_Z = orient("+y", "+z")
BEAM_Y_HOLES_Z = orient("-x", "+z")
BEAM_Z_HOLES_X = orient("-y", "+x")
BEAM_Z_HOLES_Y = I
BEAM_Y_HOLES_X = orient("+z", "+x", "+y")
BASE_BEAM_X = orient("-z", "+y", "+x")  # 平放的梁 (孔竖直) 沿 X
# 7x5 框架: 局部 x 为 5 孔方向, 局部 z 为 7 孔方向, 局部 y 为厚度 (正面孔)
FRAME_YZ_LONG_Z = orient("+y", "-x")  # 竖放在 YZ 平面, 长边沿 Z
FRAME_YZ_LONG_Y = orient("+z", "+x")  # 竖放在 YZ 平面, 长边沿 Y
FRAME_XY_LONG_X = orient("+y", "+z")  # 竖放在 XY 平面, 长边沿 X
FRAME_XY_LONG_Y_5X = orient("+x", "+z")  # 竖放在 XY 平面, 长边沿 Y
FRAME_XZ_LONG_X = orient("-z", "+y")  # 水平放, 长边沿 X
FRAME_XZ_LONG_Z = orient("+x", "+y")  # 水平放, 长边沿 Z
BUSH_X = orient("-z", "+y")  # 轴套 (局部 z 为轴线)
# 55615 弯角销连接器: 挂在平台梁下面 (横臂沿 +x, 横臂的销朝上, 孔沿 z) / 放在底座后短边上 (横臂沿 +z, 销朝下, 孔沿 x)
BENT_UNDER_BEAM = orient("+z", "-y")
BENT_ON_BASE = I
BUSH_Z = I
# 转盘: 局部 y 为转轴, 耳朵在局部 ±x。转轴沿世界 X, 耳朵在 ±Z 两侧 (销孔沿 Z); 上半 (转动) 朝 +X。
TT_ROT = orient("+z", "-x")
# 齿轮: 局部 z 为转轴
GEAR_X = orient("+y", "+z")
# 马达: 输出轴 (局部 x) 沿 +X, 本体 (局部 -z) 朝下, 高的一侧 (局部 -y) 朝 -Z (背离魔方中心那一侧)
MOTOR_ROT = orient("+x", "+z", "-y")
# 舵机: 输出轴 (局部 -y) 朝 -Z, 长度方向 (局部 x) 沿 -X (输出轴偏在本体前半), 耳朵销孔 (局部 z) 竖直
SERVO_ROT = orient("-x", "+z", "+y")
# 十字接头 32013 (角度连接器 1 号): 圆孔在原点 (局部 x) 沿 Z, 十字孔那一头 (局部 -z) 沿 -X 朝后接推杆
CROSSHEAD_ROT = orient("-z", "+y", "+x")
# 十字块 6536: 圆孔 (局部 z) 沿 X 套在推杆上, 十字孔 (局部 x) 沿 Z, 十字孔在圆孔下方 20 (局部 y 朝 -Y)
BLOCK_ROT = orient("+z", "-y", "+x")

# ---- 零件目录 -----------------------------------------------------------------

CATALOG = {
    "95658.dat": ("EV3 大马达", "solid"),
    "geekservo.dat": ("Geekservo 舵机 (灰色, 270°)", "solid"),
    "18938.dat": ("60 齿转盘 上半", "solid"),
    "18939.dat": ("60 齿转盘 下半", "solid"),
    "32498.dat": ("36 齿双面锥齿轮", "solid"),
    "32269.dat": ("20 齿双面锥齿轮", "solid"),
    "3648b.dat": ("24 齿直齿轮", "solid"),
    "64179.dat": ("7x5 框架", "solid"),
    "39790.dat": ("15x11 大框 (45680 套装)", "solid"),
    "40490.dat": ("9 孔粗梁", "solid"),
    "32524.dat": ("7 孔粗梁", "solid"),
    "32316.dat": ("5 孔粗梁", "solid"),
    "32278.dat": ("15 孔粗梁", "solid"),
    "32525.dat": ("11 孔粗梁", "solid"),
    "32523.dat": ("3 孔粗梁", "solid"),
    "32526.dat": ("3x5 L 形粗梁", "solid"),
    "32056.dat": ("3x3 L 形薄梁（端孔及弯角十字孔）", "solid"),
    "6632.dat": ("3 孔薄梁（两端十字孔）", "solid"),
    "50945_nominal.dat": ("50945 橡胶胎（名义 14×6mm）", "solid"),
    "42610.dat": ("42610 轮毂（11×8mm）", "solid"),
    "42003.dat": ("3 孔直角连接块", "solid"),
    "6587.dat": ("带凸点 3L 轴", "axle"),
    "32002.dat": ("3/4 销", "pin"),
    "11478.dat": ("5 孔薄梁（两端十字孔）", "solid"),
    "32449.dat": ("4 孔薄梁（两端十字孔）", "solid"),
    "41677.dat": ("2 孔细梁 (两端十字孔)", "solid"),
    "32013.dat": ("角度连接器 1 号 (一头十字孔, 一头横圆孔)", "solid"),
    "32034.dat": ("角度连接器 2 号 180° (两头十字孔, 中间横圆孔)", "solid"),
    "6536.dat": ("十字块 1x2 (十字孔 + 圆孔)", "solid"),
    "32184.dat": ("十字块 1x3 (十字孔/圆孔/十字孔)", "solid"),
    "39793.dat": ("3x3 连接块 (正面 5 孔、侧面两条贯穿孔)", "solid"),
    "55615.dat": ("90° 弯角销连接器 3x3 (带 4 个销)", "solid"),
    "2780.dat": ("摩擦销 (2 孔长)", "pin"),
    "3673.dat": ("无摩擦销 (2 孔长, 灰色)", "pin"),
    "32556a.dat": ("无摩擦长销 (3 孔长, 米色)", "pin"),
    "6558.dat": ("长摩擦销 (3 孔长)", "pin"),
    "32054.dat": ("带挡套长销 (3 孔长, 红色)", "pin"),
    "3749.dat": ("轴销 (半销半轴, 米色)", "pin"),
    "32062.dat": ("2 号轴", "axle"),
    "4519.dat": ("3 号轴", "axle"),
    "32073.dat": ("5 号轴", "axle"),
    "3706.dat": ("6 号轴", "axle"),
    "3705.dat": ("4 号轴", "axle"),
    "3707.dat": ("8 号轴", "axle"),
    "44294.dat": ("7 号轴", "axle"),
    "3708.dat": ("12 号轴", "axle"),
    "50451.dat": ("16 号轴", "axle"),
    "59443.dat": ("轴连接器 (光面, 两头十字孔)", "solid"),
    "3713.dat": ("轴套", "bush"),
    "32123a.dat": ("半轴套", "bush"),
    "cube56.dat": ("56mm 魔方 (示意)", "other"),
}
# 检查用的销/轴长度 (LDU), 补到 check.CONNECTOR_LEN 里
CONNECTOR_LEN = {"3705.dat": 80, "3673.dat": 40, "32556a.dat": 60, "3749.dat": 40, "32062.dat": 40, "32073.dat": 100,
                 "44294.dat": 140, "4519.dat": 60, "3706.dat": 120, "3707.dat": 160, "50451.dat": 320, "6587.dat": 63.5, "32002.dat": 30}


C_FRAME = 71  # 浅灰
C_BASE = 72  # 深灰: 底座
C_BEAM = 0  # 黑
C_JAW = 4  # 红: 夹指
C_BAND = 10  # 亮绿: 夹指上的皮带 (颜色不限, 只为醒目)
C_LINK = 14  # 黄: 连杆 (醒目)
C_PIN = 0
C_FPIN = 71  # 浅灰: 无摩擦销
C_LPIN = 1  # 蓝: 长销
C_TPIN = 19  # 米色: 无摩擦长销、轴销
C_SPIN = 4  # 红: 带挡套长销
C_AXLE = 0
C_ROD = 71  # 浅灰: 推杆 (12 号轴)
C_BUSH = 72
C_SERVO = 72
C_MOTOR = 15
C_TT = 71
C_GEAR = 14

# ---- 关键尺寸 (模块坐标) -----------------------------------------------------------

CUBE_HALF = 70.0
TT_C = np.array([-230.0, 0.0, 0.0])  # 转盘中心; 上半的耳朵在 x = -210, 下半的耳朵在 x = -250
WALL_X = -250.0  # 转盘支座 (竖墙) 所在平面, 和转盘下半的耳朵共面
TABLE_Y = 290.0
MODULE_DX = -30.0  # 相比上一版 +10，每个模块向外移动 40 LDU = 16mm

# 上下均为 7 孔主臂；薄梁将相同的轮胎压头延伸至支点前 5 孔。
JAW_Y = 80.0
PIVOT_X = -130.0
# 主臂第 2 孔、5 孔连杆 (长 80)。2026-10-05 实测: 推杆导向贴在转盘正面时, 夹紧后十字接头尾部离导向只有 0.25mm,
# 先顶住导向、轮胎压不紧。导向改放进转盘上半凸台内腔 (前表面与转盘正面齐平, x = -200), 十字接头尾部可以退进转盘中心孔:
# 夹紧后还能再往后拉约 8mm, 到连杆垂直 (死点) 时尾部正好碰到导向。
JOINT_X = -170.0
JAW_A = 40.0
LINK_L = 80.0
ROD_GUIDE_X = -210.0  # 推杆导向 32184 在转盘上半凸台内腔 (与侧板接转盘的孔同一平面)
JAW_REACH = 100.0
TYRE_RADIUS = 17.5  # 用户指定 50945 外径 14mm
# 每侧名义压缩 0.32mm；实际夹紧端仍需单臂标定。
TYRE_PRELOAD = 0.8
CLAMP_BETA = math.asin((CUBE_HALF + TYRE_RADIUS - TYRE_PRELOAD - JAW_Y) / JAW_REACH)
OPEN_BETA = math.radians(25.0)


def cross_x_for_beta(beta):
    jy = JAW_Y - JAW_A * math.sin(beta)
    return PIVOT_X - JAW_A * math.cos(beta) + math.sqrt(LINK_L ** 2 - jy ** 2)  # 十字接头在连杆前方


CROSS_CLOSED_X = cross_x_for_beta(CLAMP_BETA)

# 推杆 (一根 12 号轴): 前端插进十字接头 32013 的十字孔
ROD_FRONT_IN = 20.0  # 插进十字孔的深度: 插到底 (2026-09-29 用户实物: 原来只插一半, 实际会插到底, 十字接头就差半个孔到不了死点)

# 舵机 (固定在底座平台上): 输出轴沿 Z, 在十字块后面; 往后拉夹紧, 夹紧时曲柄朝后, 离与连杆折叠成一线还差 CLAMP_CRANK_DEG
SERVO_C = np.array([-450.0, 30.0, 80.0])  # v4: 回到最初位置 (比基准版前移两孔)
CRANK_C = np.array([-460.0, 30.0])  # 输出轴 (x, y)
CRANK_R = 20.0
LINK2_L = 120.0  # 7 孔粗梁的第 1、7 孔连接：6 个孔距
# 名义夹紧点设在曲柄折叠死点之前 (曲柄还差这么多度才折叠): 舵机脉宽可以继续微调预压, 折叠死点作为最大过行程。
CLAMP_CRANK_DEG = 25.0
BLOCK_Y = 20.0  # 十字块上连杆轴的高度 (推杆在 y = 0)


def jaw_beta(s):
    """十字接头从夹紧位置向前移动 s 时主臂外张角 (反向连杆, 前推张开)。"""
    if s < 0:
        raise ValueError("不能越过已设定的夹紧端点")
    xc = CROSS_CLOSED_X + s
    f = lambda b: math.hypot(PIVOT_X - JAW_A * math.cos(b) - xc, JAW_Y - JAW_A * math.sin(b)) - LINK_L
    lo, hi = CLAMP_BETA - 0.05, math.radians(40)
    if f(lo) * f(hi) > 0:
        raise ValueError(f"夹指行程不可达: {s:.3f} LDU")
    for _ in range(80):
        mid = (lo + hi) / 2
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def servo_theta_for(s):
    """推杆从夹紧位置向前移动 s 时的曲柄角, 以及夹紧时十字块连杆轴的 x。

    名义夹紧在折叠死点 (曲柄朝后, 与连杆重叠成一线) 之前 CLAMP_CRANK_DEG, 张开时曲柄经远离推杆的一侧 (+Y) 转向前方。"""

    def rod_x(th):
        p = CRANK_C + CRANK_R * np.array([math.cos(th), math.sin(th)])
        return p[0] + math.sqrt(LINK2_L ** 2 - (p[1] - BLOCK_Y) ** 2)

    h = CRANK_C[1] - BLOCK_Y
    th_fold = math.pi - math.atan2(h, math.sqrt((LINK2_L - CRANK_R) ** 2 - h * h))
    th_ext = -math.atan2(h, math.sqrt((LINK2_L + CRANK_R) ** 2 - h * h))
    th_clamp = th_fold - math.radians(CLAMP_CRANK_DEG)
    x0 = rod_x(th_clamp)
    max_stroke = rod_x(th_ext) - x0
    if not 0 <= s <= max_stroke:
        raise ValueError(f"舵机曲柄行程不可达: {s:.3f} LDU, 最大 {max_stroke:.3f}")
    if s == 0:
        return th_clamp, x0
    lo, hi = th_ext, th_clamp
    for _ in range(60):
        m = (lo + hi) / 2
        if rod_x(m) - x0 > s:
            lo = m
        else:
            hi = m
    return (lo + hi) / 2, x0


OPEN_S = cross_x_for_beta(OPEN_BETA) - CROSS_CLOSED_X  # 十字接头前移量
BLOCK_X_CLOSED = servo_theta_for(0)[1]


class Part:
    def __init__(self, name, color, pos, rot, step, note=""):
        self.name = name
        self.color = color
        self.pos = np.array(pos, float)
        self.rot = np.array(rot, float)
        self.step = step
        self.note = note
        self.arm = None  # 所属机械手 R/L/F/B (底座为 None)
        self.head = False  # 是否随机械手转动
        self.sub = None  # 另外三个机械手的零件: 对应 L 模块的原始搭建步骤 (装配顺序检查用)

    @property
    def kind(self):
        return CATALOG[self.name][1]

    def ldraw(self):
        m = self.rot.reshape(-1)
        nums = " ".join(_fmt(v) for v in list(self.pos) + list(m))
        return f"1 {self.color} {nums} {self.name}"

    def world(self, local):
        return self.rot @ np.asarray(local, float) + self.pos

    def moved(self, rot, shift=(0, 0, 0)):
        q = Part(self.name, self.color, rot @ self.pos + np.asarray(shift, float), rot @ self.rot, self.step, self.note)
        q.arm, q.head, q.sub = self.arm, self.head, self.sub
        return q


def _fmt(v):
    v = round(float(v), 4)
    return f"{v:g}" if v != 0 else "0"


# ---- 搭建步骤 -----------------------------------------------------------------

STEPS = []


def step(title, text, sub=None, attach=(), view=(35, 28), focus="all"):
    """sub: 所属子组件名; view: 渲染视角 (yaw, pitch); focus: 取景 "all" / "new" / "module"。"""
    STEPS.append({"title": title, "text": text, "sub": sub, "attach": tuple(attach), "view": view, "focus": focus})
    return len(STEPS)


# 四个模块的摆放: 模块坐标 -> 世界坐标 (绕 Y 轴转)。L 模块就是模块坐标本身。
ARM_ROT = {
    "L": I,
    "R": np.array([[-1, 0, 0], [0, 1, 0], [0, 0, -1]], float),
    "F": np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]], float),  # 模块的 -X 轴 -> 世界 +Z
    "B": np.array([[0, 0, -1], [0, 1, 0], [1, 0, 0]], float),
}
ARMS = ("R", "L", "F", "B")


def module(open_s=0.0, angle=0.0, steps=True, on_base=False):
    """一个机械手模块 (模块坐标)。open_s: 推杆从夹紧位置向前 (张开方向) 移动的距离; angle: 机械手转过的角度 (度),
    0 表示夹指在竖直平面 (夹指一上一下)。steps=False 时不登记搭建步骤 (其余三个模块)。
    on_base=True 时加上竖墙、马达底块和底座之间的销 (单独检查模块时没有底座, 不加)。"""
    if not math.isfinite(open_s) or not 0 <= open_s <= OPEN_S + 1e-9:
        raise ValueError("开合指令超出正常行程；机械开限位不能作为舵机工作端点")
    parts = []
    st = step if steps else (lambda *a, **k: 0)

    def add(name, color, pos, rot, s, head=False, note=""):
        p = Part(name, color, pos, rot, s, note)
        p.head = head
        parts.append(p)
        return p

    # ================= 1. 竖墙 (转盘支座) =================
    # 三块 7x5 框架竖着上下拼成 7x15 的墙。转盘下半底部的长方形凸台 (5x3 孔大小) 正好卡在最上面那块框架的开口里。
    s = st("竖墙", "三块 7x5 框架竖着上下对齐, 相邻长边各用 3 个摩擦销穿侧孔连起来, 拼成一面 7x15 的墙。",
           sub="竖墙", view=(60, 20))
    for yc in (0, 100, 200):
        add("64179.dat", C_FRAME, (WALL_X, yc, 0), FRAME_YZ_LONG_Z, s)
    for y in (50, 150):
        for z in (-40, 0, 40):
            add("2780.dat", C_PIN, (WALL_X, y, z), ALONG_Y, s)
    # ================= 2. 马达 =================
    # 马达偏在 -Z 一侧, 输出轴和转盘轴线相距 100, 本体朝下。
    # 2026-09-29 用户实测: 相距 100 时 24 齿直齿轮 3648 咬合最好 (比 20 齿双面锥齿轮更合适), 按实测改用 24 齿。
    # 按标准节圆 (24 齿半径 30 + 60 齿半径 75 = 105) 算会偏紧, 说明转盘外圈的实际节圆比 75 LDU 小, 以实测为准。
    # 2026-09-29: 原来是 36 齿、相距 120, 实物咬不上。改照官方 42100 (OMR 模型核实): 20 齿双面锥齿轮 18575/32269
    # 和转盘上半 18938 平行轴啮合, 中心距 100, 齿轮背面和转盘上半的背面平齐 (齿轮中面 = 转盘上半原点)。
    mpos = np.array([-310.0, 0.0, -100.0])

    # 马达底面 (本体最下面那一面) 有 3 个朝下的销孔 (1 孔深), 沿 X 排在 z = -120 上, 正好在底座大框长边的正上方,
    # 其中两边两个 (x = -330、-290) 对准大框长边的竖孔。马达底面离大框上面正好 2 个孔高,
    # 用两层平放的 5 孔粗梁垫满, 竖销上下连起来: 马达-上层 3 个, 上层-下层 2 个 (两头), 下层-大框 2 个。
    # 这样马达下部直接销在底座上 (用户 2026-09-29 指出原来只踩桌面, 上面受力会晃); 原来的尾脚竖梁不要了。
    s = st("马达底块", "马达平放、底面朝上 (底面就是本体最下面、离输出盘最远的那一面), 底面上一排 3 个销孔。"
           "3 个孔各插 1 个摩擦销, 压上一根 5 孔粗梁 (梁的第 2、3、4 个孔扣在这 3 个销上); 再在这根梁两头 (第 1、5 个) 的孔各插 1 个摩擦销, "
           "压上第二根 5 孔粗梁, 两根梁对齐叠在一起。", sub="马达", view=(60, -25))
    add("95658.dat", C_MOTOR, mpos, MOTOR_ROT, s)
    for x in (-330, -310, -290):
        add("2780.dat", C_PIN, (x, 210, -120), ALONG_Y, s)
    add("32316.dat", C_BEAM, (-310, 220, -120), BASE_BEAM_X, s)
    for x in (-350, -270):
        add("2780.dat", C_PIN, (x, 230, -120), ALONG_Y, s)
    add("32316.dat", C_BEAM, (-310, 240, -120), BASE_BEAM_X, s)
    # 马达前端: 输出盘和下面的方箱在同一个面上, 中间带 3 个孔的 "颈部" 缩进去 2 个孔。颈部的孔在一竖列上
    # (上圆孔 y = 40、十字孔 y = 60、下圆孔 y = 80), 所以内层用一根竖放的 3 孔粗梁同时插两个圆孔, 和马达连成一体。
    # 外层两根横梁 (孔沿 X, 沿 Z 伸向竖墙) 贴在竖墙背面, 用销接到竖墙框架的正面孔: 上面一根接顶上那块框架 (y = 40),
    # 下面一根接中间那块框架 (y = 60)。原来的马达前板和连接板 (2 块 7x5 框架) 都省掉了 (2026-09-29 框架换横梁)。
    s = st("马达前梁", "马达靠输出盘那一侧, 输出盘下面有一段缩进去 2 个孔深的 \"颈部\", 上面一竖列 3 个横穿马达的孔 "
           "(两个圆孔夹一个十字孔)。先在上圆孔插 1 根蓝色长摩擦销 (1 孔长的那段插进马达, 挡肩贴住颈部), 下圆孔插 1 个摩擦销; "
           "把一根 3 孔粗梁竖着压到这两个销上。再在 3 孔梁中间的孔插 1 个摩擦销。然后把两根横梁压上去, 都朝竖墙的方向伸出: "
           "11 孔粗梁的第 1 个孔扣在蓝色长销上, 7 孔粗梁的第 1 个孔扣在中间的摩擦销上。", sub="马达", view=(60, 20))
    add("6558.dat", C_LPIN, (-290, 40, -160), ALONG_X, s)  # 1 孔长的一段 (局部 -x) 朝 -X 插进马达
    add("2780.dat", C_PIN, (-300, 80, -160), ALONG_X, s)
    add("32523.dat", C_BEAM, (-290, 60, -160), BEAM_Y_HOLES_X, s)
    add("2780.dat", C_PIN, (-280, 60, -160), ALONG_X, s)
    add("32525.dat", C_BEAM, (-270, 40, -60), BEAM_Z_HOLES_X, s)
    add("32524.dat", C_BEAM, (-270, 60, -100), BEAM_Z_HOLES_X, s)
    # 齿轮位置照官方 42100: 齿轮背面和转盘上半的背面平齐。马达输出盘外面到齿轮背面正好 2 个孔长,
    # 用 2 个半轴套 + 1 个轴套垫满 (用户 2026-09-29 指出原来齿轮比转盘齿圈往马达那边多出半个轴套厚)。
    s = st("齿轮", "7 号轴从这一面插进马达输出盘中间的十字孔, 一直推到底: 输出盘的十字孔是贯通的 (马达两面都有输出盘), 轴的另一头和马达另一面的输出盘基本平齐 (只露出不到 1 mm)。这样马达里占 3 个孔长, 外面露出约 4 个孔长。然后依次套上 2 个半轴套、1 个轴套、24 齿直齿轮, 最前面再套 1 个半轴套, 正好套到轴头。",
           sub="马达", view=(60, 20))
    add("44294.dat", C_AXLE, (-275, 0, -100), ALONG_X, s)
    add("32123a.dat", C_BUSH, (-275, 0, -100), BUSH_X, s)
    add("32123a.dat", C_BUSH, (-265, 0, -100), BUSH_X, s)
    add("3713.dat", C_BUSH, (-250, 0, -100), BUSH_X, s)
    add("3648b.dat", C_GEAR, (-230, 0, -100), GEAR_X, s)
    add("32123a.dat", C_BUSH, (-215, 0, -100), BUSH_X, s)
    # 马达先装到竖墙上 (横着推), 竖墙和马达再一起竖着压到底座上: 竖墙底边的销和马达底块的销都是竖的, 方向一致
    s = st("装马达", "在两根横梁上对准竖墙框架正面孔的位置插摩擦销: 11 孔梁 3 个 (接最上面那块框架), 7 孔梁 1 个 (从马达数第 6 个孔, 接中间那块框架)。"
           "把整个马达组件平推到竖墙背面, 4 个销同时插进墙上的孔。马达底块的下表面和竖墙的下边平齐。"
           "装机械头时 24 齿齿轮和转盘上半的齿啮合 (两轴相距 5 个孔, 齿轮背面和转盘背面平齐; 24 齿是实测咬合最好的)。",
           sub="竖墙", attach=("马达",), view=(60, 20))
    for z in (-60, -20, 20):
        add("2780.dat", C_PIN, (WALL_X - 10, 40, z), ALONG_X, s)
    add("2780.dat", C_PIN, (WALL_X - 10, 60, -60), ALONG_X, s)
    # 转盘下半底部的长方形凸台 (5x3 孔) 正好卡在最上面那块框架的开口里, 上下左右和转动都被框架挡住。
    # 凸台两头的端壁各有 3 个销孔, 正对框架短边的 3 个侧孔。普通摩擦销中间有挡环, 从外面只能插进框架一半;
    # 用带挡套长销 32054 (挡套 1 孔 + 销 2 孔) 从转盘中孔里面往外插: 销段穿过凸台端壁再插进框架短边, 挡套留在凸台里面,
    # 装上转盘上半后看不见 (用户 2026-09-29 提出)。凸台里面两端壁之间正好 3 孔长, 两根销的挡套会互相挡住,
    # 所以一根用上排孔、一根用下排孔。
    s = st("转盘下半", "60 齿转盘的下半 (没有齿): 底部的长方形凸台从正面 (朝魔方的一面) 塞进最上面那块框架的开口, "
           "长边沿框架的长边, 圆盘的边沿贴住框架正面。凸台两头的端壁各有上中下 3 个孔, 正对框架短边的 3 个侧孔。"
           "从框架外侧往每个孔插 1 根蓝色长摩擦销, 2 孔长的一段朝里: 穿过框架短边再插进凸台端壁, 挡肩贴住框架外表面。两头共 6 根。"
           "然后竖墙两侧各竖贴一根 9 孔粗梁 (孔朝外): 先在中间那块框的短边 3 个侧孔各插 1 个黑销, 再把 9 孔梁压上去, "
           "上面 3 个孔套住蓝色长销露出的 1 孔长段, 下面 3 个孔套住黑销, 中间两个孔空着。这样上下两块框在两侧锁成一体。"
           "舵机那一侧最下面一个孔不用黑销, 改从外面插 1 根蓝色长销 (2 孔长段穿侧梁进中框), 露出的 1 孔长段留给第 11 步的斜撑。", sub="竖墙", view=(60, 20))
    add("18939.dat", C_TT, TT_C, TT_ROT, s)
    # 2026-10-05: 原来只有 2 根红色挡套销 (从凸台内腔往外插, 一头一根且上下错开), 转盘下半在框里会晃, 实测机械头下垂明显。
    # 改为从框架外侧插 6558: 2 孔长一段穿框架短边和凸台端壁, 1 孔长一段和挡肩留在外面; 6 个孔全用上, 中间一排也能用 (不进内腔, 不碰推杆)。
    for sz in (1, -1):
        for y in (-20, 0, 20):
            add("6558.dat", C_LPIN, (WALL_X, y, 60 * sz), LPIN_SHORT_Z if sz > 0 else ALONG_Z, s, note="转盘下半固定销")
    # 2026-10-05: 上框 (固定转盘) 与中框原来只靠底边 3 个竖销相连, 前倾时接缝力臂只有框厚 8mm。
    # 两侧各竖贴一根 9 孔粗梁: 上 3 孔套住转盘固定销露在外面的 1 孔段, 下 3 孔用黑销接中框短边侧孔, 把上、中两块框锁成一体。
    for sz in (1, -1):
        add("40490.dat", C_BEAM, (WALL_X, 60, 80 * sz), BEAM_Y_HOLES_Z, s, note="竖墙侧梁")
        for y in (80, 100, 120):
            if sz > 0 and y == 120:
                # 舵机侧最下面一个改用蓝色长销: 2 孔段穿侧梁进中框, 露出的 1 孔段留给第 11 步的斜撑
                add("6558.dat", C_LPIN, (WALL_X, y, 80), LPIN_SHORT_Z, s, note="竖墙侧梁销")
            else:
                add("2780.dat", C_PIN, (WALL_X, y, 70 * sz), ALONG_Z, s, note="竖墙侧梁销")
    if on_base:
        s = st("装竖墙", "竖墙和马达现在是一个整体, 一起竖着往下压到底座上: 竖墙立在大框靠魔方的那条短边正中, 墙面朝魔方; "
               "马达底块压在大框的长边上。先在大框短边上插 2 个摩擦销 (对准墙底边的侧孔); 长边上第 1 步插的 2 根蓝色长销露在上面, "
               "正好对准马达底块下层梁的第 2、4 个孔。然后整体对准压下去。", attach=("底座", "竖墙"), view=(40, 35))
        for z in (-40, 40):
            add("2780.dat", C_PIN, (WALL_X, BASE_Y - 20, z), ALONG_Y, s)

    # ================= 3. 舵机平台和推杆导向 =================
    # 平台: 前半块用 7x5 框架 (要从端面侧孔接竖墙、从正面孔接导向框架, 两个方向交汇的节点);
    # 后半块是两根 15 孔粗梁平放在框架下面。
    # 支撑 (2026-09-30 重做, 用户: 马达侧支架要系统性、实用也要专业; 能不用 7x5 框架就不用, 用 55615):
    # 平台前端挂在竖墙上, 后端两根 15 孔梁下面各挂一个 55615 (90° 弯角销连接器, 自带 4 个销: 横臂上 2 个朝上插进 15 孔梁,
    # 两个孔沿 z) 和一根 9 孔竖梁 (在 xy 平面, 孔沿 z, 2 个销接 55615)。
    # 马达一侧的梁悬在大框开口上方, 竖梁下端再用一个 55615 落到大框后短边: 横臂 2 个销朝下插进后短边的竖孔 (z = 0、40),
    # 竖臂 2 个销沿 z 插进竖梁。另一侧的梁正好在大框长边外侧, 竖梁下端 1 个销直接插进长边的侧孔。
    # 两根竖梁都在平台装好后从外侧沿 z 压上去 (销都朝外), 和平台沿推杆方向装入不冲突。
    s = st("舵机平台", "两根 15 孔粗梁平放、平行, 相距 4 个孔。一块 7x5 框架平放压在两根梁的前段上 (框架前端和梁前端对齐), "
           "6 个摩擦销竖着连起来 (框架正面孔: 一根梁 4 个; 另一根梁最前、最后两个孔各插 1 个, 中间 2 个孔留给导向框架的长销)。"
           "梁的后段上面, 舵机那一侧压一根 7 孔粗梁当舵机垫块: 从平台后端向魔方数，第 1、5、6 孔用黑销接下面的 15 孔梁，第 3、7 孔留给舵机耳朵的蓝色长销。第 2、4 孔下方由 55615 占用，不加贯穿销。两根梁的最后一个孔上横压一根 5 孔粗梁, 2 个摩擦销, 让后段也连成封闭的长方形。"
           "两根梁后段的下面各挂一个 55615 (90° 弯角销连接器): 横臂顺着梁、竖臂朝下, 横臂上朝上的 2 个销从下面插进梁孔: 马达那一侧的梁插倒数第 2、4 个孔; 舵机那一侧的梁插倒数第 3、5 个孔 (倒数第 5 个孔就在垫块空着的第 4 个孔正下方); "
           "竖臂上的 2 个孔朝外 (朝平台两侧)。平台前段上面竖立一块框架当推杆导向: 它长边沿推杆方向, v4 框架回到最初位置 (比基准版前移两孔), 底边用 2 根蓝色长摩擦销竖着插进平台: 1 孔长的一段朝上插进导向框架, 2 孔长的一段穿过平台框架, 一直插进下面那根 15 孔梁; "
           "导向框架长边最靠后的那个孔 (长销让出来的) 改插黑销, 只连接平台框架与下方梁。导向框架靠魔方那条短边正中的侧孔 (圆孔) 是推杆的轴承, 后面那条短边的孔 v4 不用。", sub="平台", view=(30, 40))
    add("64179.dat", C_FRAME, (-330, 60, 40), FRAME_XZ_LONG_X, s)
    for z in (0, 80):
        add("32278.dat", C_BEAM, (-410, 80, z), BASE_BEAM_X, s)
    for x in (-390, -350, -310, -270):
        add("2780.dat", C_PIN, (x, 70, 80), ALONG_Y, s)
    add("2780.dat", C_PIN, (-270, 70, 0), ALONG_Y, s)
    add("32524.dat", C_BEAM, (-470, 60, 80), BASE_BEAM_X, s)
    # v4 舵机回到最初位置：垫梁第 3/7 孔接舵机，第 1/5/6 孔接平台。
    # 第 2/4 孔下方 (x=-510/-470) 由 55615 从下方占用, 不加贯穿销。
    for x in (-530, -450, -430):
        add("2780.dat", C_PIN, (x, 70, 80), ALONG_Y, s)
    gf_c = np.array([-350.0, 0.0, 0.0])
    add("64179.dat", C_FRAME, gf_c, FRAME_XY_LONG_X, s)
    # 导向框架底边的 2 个销用蓝色长销, 一直穿过平台框架插进下面那根 15 孔梁 (否则这根梁只有 1 个销, 用户 2026-09-29 指出):
    # 1 孔长的一段朝上插进导向框架, 挡肩压在平台框架上面, 2 孔长的一段穿过平台框架和梁
    for x in (-350, -310):
        add("6558.dat", C_LPIN, (x, 60, 0), orient("+y", "+x"), s)
    add("2780.dat", C_PIN, (-390, 70, 0), ALONG_Y, s)
    # 两根 15 孔梁的后端用一根 5 孔梁横着连起来, 和前面的框架围成一个封闭的长方形
    add("32316.dat", C_BEAM, (-550, 60, 40), BEAM_Z_HOLES_Y, s)
    for z in (0, 80):
        add("2780.dat", C_PIN, (-550, 70, z), ALONG_Y, s)
    # 55615: 局部 z 为横臂方向 (横臂上的销朝局部 +y), 局部 -y 为竖臂方向 (竖臂上的销朝局部 -z), 孔沿局部 x。
    # 平台下的两个: 横臂沿 +x 贴在梁下面, 销朝上; 竖臂朝下; 孔沿 z。竖臂上多出的 2 个销朝后, 空着。
    for (x, z) in ((-530, 0), (-510, 80)):
        add("55615.dat", C_BEAM, (x, 100, z), BENT_UNDER_BEAM, s)
    s = st("舵机", "舵机平放在平台后端的垫块上, 输出轴朝推杆那一侧。2 根蓝色长摩擦销从上面插进舵机两只耳朵, "
           "1 孔长的那段朝下插进垫块第 3、7 孔 (从平台后端向魔方数), 避开垫块的 3 个黑色摩擦销。", sub="平台", view=(30, 40))
    add("geekservo.dat", C_SERVO, SERVO_C, SERVO_ROT, s)
    for dx in (-40, 40):
        add("6558.dat", C_LPIN, (SERVO_C[0] + dx, 40, SERVO_C[2]), LPIN_SHORT_Y, s)
    s = st("装平台", "先在大框后短边 (离竖墙最远的那条短边) 上放一个 55615: 横臂顺着短边, 朝下的 2 个销插进短边第 1、2 个竖孔 (从马达那一侧数, 看图), 竖臂朝上, 竖臂上的 2 个销朝马达那一侧。"
           "然后平台前端顶住竖墙背面, 2 个摩擦销沿推杆方向穿进墙的孔。检查导向框架的两个轴承孔、转盘中孔在一条直线上。"
           "最后装两根竖梁 (9 孔粗梁), 都从外侧压上去: 马达那一侧, 先在平台下 55615 的 2 个孔里插摩擦销, 竖梁上端 2 个孔套这 2 个销、下端 2 个孔套底座上 55615 的 2 个销; "
           "另一侧, 在平台下 55615 的 2 个孔和大框长边外侧的侧孔 (看图) 各插 1 个摩擦销, 竖梁压上去, 下端最后一个孔接大框。"
           "最后在舵机那一侧加斜撑: 平台框侧边从前数第 3 个侧孔插 1 个黑销, 7 孔粗梁第 1 孔套住竖墙侧梁下部露出的蓝色长销, 第 6 孔套住这个黑销, 第 7 孔空着。",
           attach=("平台",), view=(150, 30), focus="module")
    for z in (20, 60):
        add("2780.dat", C_PIN, (WALL_X - 10, 60, z), ALONG_X, s)
    # 马达一侧: 大框后短边上的 55615 (横臂沿 +z, 2 个销朝下插进竖孔 z = 0、40; 竖臂朝上, 2 个销朝 -z) + 9 孔竖梁 (z = -20)
    if on_base:
        add("55615.dat", C_BEAM, (-530, 240, 0), BENT_ON_BASE, s)
    add("40490.dat", C_BEAM, (-530, 160, -20), BEAM_Y_HOLES_Z, s)
    for y in (100, 140):
        add("2780.dat", C_PIN, (-530, y, -10), ALONG_Z, s)
    # 另一侧: 9 孔竖梁 (z = 100) 上端接平台下的 55615, 下端 1 个销插进大框长边 (z = 80) 的侧孔
    add("40490.dat", C_BEAM, (-510, 180, 100), BEAM_Y_HOLES_Z, s)
    for y in (100, 140):
        add("2780.dat", C_PIN, (-510, y, 90), ALONG_Z, s)
    if on_base:
        add("2780.dat", C_PIN, (-510, BASE_Y, 90), ALONG_Z, s)
    # 2026-10-05 舵机侧斜撑: 竖墙侧梁 (x=-250, y=120) 与平台框舵机侧长边侧孔 (x=-330, y=60) 之间, 水平 80、竖直 60, 相距 5 孔距 (3-4-5)。
    # 7 孔粗梁第 1 孔套侧梁露出的蓝色长销, 第 6 孔接平台框; 与平台、竖墙构成三角形, 竖墙不再只靠平台前端一排销点头。
    A, B = np.array([WALL_X, 120.0, 0]), np.array([-330.0, 60.0, 0])
    u = (B - A) / np.linalg.norm(B - A)
    add("2780.dat", C_PIN, (B[0], B[1], 90), ALONG_Z, s, note="舵机侧斜撑销")
    add("32524.dat", C_BEAM, A + 60 * u + [0, 0, 100], orient(np.cross([0, 0, 1.0], u), "+z", u), s, note="舵机侧斜撑")

    # 推杆 + 曲柄滑块 (舵机侧)
    th, x0 = servo_theta_for(open_s)
    crank_pin = CRANK_C + CRANK_R * np.array([math.cos(th), math.sin(th)])
    bx = crank_pin[0] + math.sqrt(LINK2_L ** 2 - (crank_pin[1] - BLOCK_Y) ** 2)  # 十字块上连杆轴的 x
    s = st("十字块和舵机连杆", "十字块圆孔在上，放进导向框架的开口里，圆孔对准推杆轴承孔；两侧各放一个半轴套，推杆后面穿入。"
           "3 号轴穿过十字块下面的十字孔：背离舵机的一端露半孔，套半轴套；朝舵机的一端依次套黄色 7 孔粗梁 32524、半轴套。粗梁直接贴十字块，之间不加轴套。"
           "连杆从靠魔方那端数，第 1 孔接十字块，第 7 孔接曲柄，两铰点相距 6 个孔距（48mm）。v4 往后拉是夹紧：图示夹紧位置曲柄朝后（背离魔方），离与连杆折叠成一条直线（折叠死点）还差约 25°，这段余量留给舵机微调预压，舵机不要越过折叠死点。"
           "图示是最终夹紧位置。首次装配先让连杆曲柄端脱开，按单臂标定步骤用 servo 1500 空载定位，断电后在行程中间调整曲柄方向并连接。"
           "曲柄端用 2 号轴，外端与曲柄外侧齐平；内端穿过粗连杆后装半轴套，半轴套贴住连杆。"
           "从夹紧端张开时，曲柄经远离推杆的一侧（朝下）向前转约 110°，不能走靠推杆的一侧。检查轴与半轴套不松脱，并手动走完整行程和推杆回转。不要带连杆直接首次定位或硬拉对孔。", view=(30, 30))
    add("6536.dat", C_BEAM, (bx, BLOCK_Y, 0), BLOCK_ROT, s)
    rod_bushes = []
    for dx in (-15, 15):
        rod_bushes.append(add("32123a.dat", C_BUSH, (bx + dx, 0, 0), BUSH_X, s, head=True))
    # 十字块占 z=-10..10，粗连杆直接贴在 z=10..30，外半轴套占 30..40。
    add("4519.dat", C_AXLE, (bx, BLOCK_Y, 10), ALONG_Z, s)
    for z in (-15, 35):
        add("32123a.dat", C_BUSH, (bx, BLOCK_Y, z), BUSH_Z, s)
    cdir = np.array([math.cos(th), math.sin(th), 0.0])
    add("41677.dat", C_BEAM, (CRANK_C[0], CRANK_C[1], 35), orient(np.cross([0, 0, 1.0], cdir), "+z", cdir), s)
    # 曲柄端 2L 轴占 z=0..40，粗连杆 10..30，曲柄 30..40。
    # 内半轴套占 z=0..10，粗连杆两侧分别由半轴套和曲柄面定位。
    add("32062.dat", C_AXLE, (crank_pin[0], crank_pin[1], 20), ALONG_Z, s, note="曲柄端轴")
    add("32123a.dat", C_BUSH, (crank_pin[0], crank_pin[1], 5), BUSH_Z, s, note="曲柄端内限位")
    e = np.array([crank_pin[0] - bx, crank_pin[1] - BLOCK_Y, 0.0])
    e /= np.linalg.norm(e)
    mid = (np.array([bx, BLOCK_Y]) + crank_pin) / 2
    add("32524.dat", C_LINK, np.array([mid[0], mid[1], 20]),
        orient(np.cross([0, 0, 1.0], e), "+z", e), s, note="舵机连杆")

    # ================= 4. 转动部分 (机械头) =================
    xc = CROSS_CLOSED_X + open_s  # 十字接头上销的 x (前推张开)
    beta = jaw_beta(open_s)
    head = rod_bushes.copy()

    def hadd(name, color, pos, rot, s, note=""):
        p = add(name, color, pos, rot, s, head=True, note=note)
        head.append(p)
        return p

    # 转盘上半是机械头的底座: 先把销插进它两头的孔, 再从两侧把侧板压上去 (侧板装上以后两块就连成一体了, 那时再插不进去)
    s = st("侧板与夹指架", "两根 3x5 L 形梁竖放, 长臂沿推杆方向, 两根长臂一上一下平行 (相距 2 个孔), 短臂都在靠魔方的一头, 一根朝上、一根朝下。"
           "内侧 (朝推杆) 不再用整根 11 孔梁, 改成一长一短两段竖直粗梁, 中间空出来给连杆和十字接头滑过: "
           "一侧是上段 3 孔梁、下段 5 孔梁, 另一侧反过来 (上段 5 孔、下段 3 孔), 看图。5 孔梁第 1、3 孔接 L 形梁短臂的拐角孔和末端孔 (蓝色长销), 第 4 孔是夹指根轴孔, 第 5 孔接开限位支架; "
           "3 孔梁靠推杆的那个孔接另一根 L 形梁短臂末端 (蓝色长销), 中间孔是夹指根轴孔, 外端孔接开限位支架。"
           "外侧再竖贴一根 7 孔粗梁, 把上下两根 L 形梁的短臂连起来: 内侧有梁的孔用蓝色长销 (1 孔长的一段朝内插内侧梁, 挡肩在内侧梁和 L 形梁之间), 内侧空着的那个孔用黑色摩擦销只连 L 形梁和 7 孔梁。"
           "这样做两套，左右对称 (两套的长短段上下相反)。",
           sub="机械头", view=(40, 25))
    # 侧板原来是一块 7x5 框架; 实际只用到两列孔 (转盘上半凸台的两个孔、9 孔梁的 4 个孔), 改成两根 3x5 L 形梁
    # (长臂沿推杆方向从转盘接到 9 孔梁, 短臂沿 9 孔梁再多接一个孔, 两个销在同一根梁上, 不会绕销转) (2026-09-29 框架换横梁)
    # 2026-10-04 实测: 十字接头在连杆前方后, 连杆端头和长销端面贴着整根 11 孔梁滑过 (厚度方向名义间隙 0), 摩擦严重。
    # 内侧梁改成一长一短两段, 让出连杆扫过的区域: +z 侧贴上连杆, 扫过 y = -9 ~ +46, 所以 5 孔段在 -y、3 孔段在 +y;
    # -z 侧贴下连杆, 上下相反。外侧加 7 孔梁, 补回 11 孔梁原来把上下 L 形梁连成一体的作用。
    for sz in (1, -1):
        hadd("32526.dat", C_FRAME, (-210, -20, 60 * sz), orient("-y", "-z", "+x"), s)
        hadd("32526.dat", C_FRAME, (-210, 20, 60 * sz), orient("+y", "+z", "+x"), s)
        hadd("32316.dat", C_BEAM, (PIVOT_X, -60 * sz, 40 * sz), BEAM_Y_HOLES_Z, s, note="内侧长段")
        hadd("32523.dat", C_BEAM, (PIVOT_X, 80 * sz, 40 * sz), BEAM_Y_HOLES_Z, s, note="内侧短段")
        hadd("32524.dat", C_BEAM, (PIVOT_X, 0, 80 * sz), BEAM_Y_HOLES_Z, s, note="外侧连接梁")
        lpin = ALONG_Z if sz > 0 else orient("-z", "+y")  # 6558 的 1 孔长一段朝内
        for y in (-20 * sz, -60 * sz, 60 * sz):
            hadd("6558.dat", C_LPIN, (PIVOT_X, y, 60 * sz), lpin, s, note="侧板三层销")
        hadd("2780.dat", C_PIN, (PIVOT_X, 20 * sz, 70 * sz), ALONG_Z, s, note="侧板外层销")
    s = st("转盘上半与推杆导向", "60 齿转盘的上半 (有齿), 有齿的一面朝后。正面中心孔两侧各有一个凸耳, 每个凸耳一竖排 3 个孔。"
           "把 39793 (3x3 连接块, 正面 5 孔、侧面两条贯穿孔) 从正面放进两个凸耳之间: 正面中心孔对准转盘中心, 两条侧面孔对准凸耳的上下两个孔, 方块两侧贴住凸耳。"
           "从外面往凸耳的上下孔各插 1 根蓝色长摩擦销, 2 孔长的一段朝里, 穿过凸耳插进方块的侧面孔, 挡肩贴凸耳外表面, 两侧共 4 根。"
           "再把两套侧板从左右两边压到露出的 1 孔长段上, 两根 L 形梁长臂后端的孔对准销。推杆在方块正面中心孔里前后滑动。", sub="机械头", view=(40, 25))
    hadd("18938.dat", C_TT, TT_C, TT_ROT, s)
    # 2026-10-05: 推杆导向用 39793 一个零件, 正好 3 孔宽卡在两个凸耳之间 (两侧贴凸耳内表面), 侧面两条贯穿孔与凸耳上下孔同轴。
    # 6558 从外侧插: 2 孔段穿凸耳进方块侧孔, 挡肩贴凸耳外表面, 1 孔段接 L 形梁。侧板、凸耳、导向块用同一根摩擦销串起来,
    # 两个凸耳也通过方块连成一体; 凸耳中间孔不用。
    hadd("39793.dat", C_BEAM, (ROD_GUIDE_X, 0, 0), orient("+z", "+x"), s, note="推杆导向")
    for sz in (1, -1):
        for y in (-20, 20):
            hadd("6558.dat", C_LPIN, (-210, y, 40 * sz), LPIN_SHORT_Z if sz > 0 else ALONG_Z, s, note="侧板转盘长销")
    s = st("夹指与防翻折限位", "上下各一根红色 7 孔粗梁当夹指，中间第 4 孔套 8 号根轴。根轴穿过两侧内侧梁从外端数第 2 孔 (即原 11 孔梁第 2、10 孔的位置)；夹指两侧各一个整轴套。"
           "每个夹指两侧各叠两片 32056 三乘三 L 形薄梁作限位支架（每侧总厚8mm）：竖边贴住内侧梁外侧，末端十字孔套根轴，中间圆孔用黑销接内侧梁端孔；另一边朝魔方，位于夹指外侧。"
           "根轴两端在新 L 形支架外各装一个半轴套，不要压紧夹指。根轴＋黑销两点固定支架，不能只装黑销。"
           "两侧新 L 形薄梁朝魔方的末端十字孔穿另一根 8 号轴，两端各加半轴套，作为横向开限位挡轴。上下各有一根。"
           "正常开角为 25°，不能接触挡轴；异常继续张开时约 30° 被挡住，v4 反向连杆在行程内没有翻折点，挡轴保留作异常保护。安装前把上下夹指都放回朝魔方的正常姿态，不能从错误分支直接套入。"
           "挡轴是异常行程保护，舵机不得持续顶住它。", sub="机械头", view=(40,25))
    for sy in (1, -1):
        piv = np.array([PIVOT_X, JAW_Y * sy, 0.0])
        R = rot_z(beta * sy)
        hadd("32524.dat", C_JAW, piv, R @ BEAM_X_HOLES_Z, s)
        # 8号根轴贯穿两侧内侧梁和新增L形限位支架，外侧半轴套保持。
        hadd("3707.dat", C_AXLE, piv, ALONG_Z, s)
        for z in (-20, 20):
            hadd("3713.dat", C_BUSH, piv + [0, 0, z], BUSH_Z, s)
        for z in (-75,75):
            hadd("32123a.dat", C_BUSH, piv+[0,0,z], BUSH_Z, s)
        bracket_rot = orient("+x",[0,0,sy],[0,-sy,0])
        for sz in (-1,1):
            for z in (55,65):
                hadd("32056.dat",C_FRAME,[PIVOT_X,sy*120,sz*z],bracket_rot,s,"限位支架")
            hadd("2780.dat",C_PIN,[PIVOT_X,sy*100,sz*50],ALONG_Z,s,"限位支架固定销")
        hadd("3707.dat",C_AXLE,[-90,sy*120,0],ALONG_Z,s,"开限位挡轴")
        for z in (-75,75):
            hadd("32123a.dat",C_BUSH,[-90,sy*120,z],BUSH_Z,s,"开限位挡轴轴套")
    s = st("双侧薄梁轮胎压头", "每臂上下各一组 42610 轮毂＋50945 轮胎，每组轮毂两侧各用一根 32449 四孔薄梁（两端十字孔、中间两个圆孔）。两根薄梁分别贴住主臂两侧。"
           "从后端数：主臂第 6 孔用 3 号轴贯穿两根薄梁的第 1 十字孔，外面各装一个半轴套；主臂第 7 孔用 32054 带挡套长销贯穿两根薄梁的第 2 圆孔，挡套留在第一根薄梁外侧，销端穿出另一根薄梁。"
           "两根薄梁第 3 圆孔留空。第 4 十字孔用 2 号轴贯穿，中间套轮毂，轮胎中心保持在主臂中面。2 号轴的两端与薄梁外侧齐平，不加外轴套，不换长轴。"
           "轮毂被两根薄梁限制轴向移动，仍可绕固定十字轴转动；确认没有夹死。安装好半轴套和挡套销，再检查轮轴是否会窜出。上下两组装配完全相同。", sub="机械头", view=(40,25))
    for sy in (1,-1):
        piv = np.array([PIVOT_X,JAW_Y*sy,0.])
        R = rot_z(beta*sy)
        front = piv + R @ np.array([JAW_REACH,0,0])
        for z in (-15,15):
            hadd("32449.dat",C_JAW,piv+R@[70.,0,z],R@BEAM_X_HOLES_Z,s,"压头支承薄梁")
        hadd("4519.dat",C_AXLE,piv+R@[40.,0,0],R@ALONG_Z,s,"薄梁固定轴")
        for z in (-25,25):
            hadd("32123a.dat",C_BUSH,piv+R@[40.,0,z],R@BUSH_Z,s,"薄梁固定轴限位")
        hadd("32054.dat",C_SPIN,piv+R@[60.,0,-10],R@ALONG_Z,s,"薄梁固定挡套销")
        hadd("32062.dat",C_AXLE,front,R@ALONG_Z,s,"轮毂贯穿轴")
        hadd("42610.dat",71,front,R,s,"轮毂")
        hadd("50945_nominal.dat",0,front,R,s,"橡胶胎")
    s = st("连杆与十字接头", "十字接头用角度连接器 1 号 (32013): 一头是顺着长度方向的十字孔 (下一步插推杆), 另一头是横着的圆孔。"
           "注意不要拿成外形几乎一样、两个孔都是十字孔的 32039。圆孔里穿一根 4 号轴, 两根黄色 5 孔连杆一上一下套在轴的两端, 最外面各套一个半轴套挡住连杆 (连杆要能自由转动); "
           "连杆另一端各用一个灰色无摩擦销接到上下主臂各自的第 2 孔 (从后数)。十字接头在连杆前方 (靠魔方一侧): "
           "往后拉十字接头时连杆把夹指根部往外撑, 夹指前端合拢; 往前推张开。连杆和十字接头在两侧侧梁中间的空档里滑动, 不贴侧梁。"
           "名义夹紧端点在主臂外张约 3.84°; 此时十字接头尾部离推杆导向 (转盘正面) 约 8mm, 可以继续往后拉加大预压。", sub="机械头", view=(40, 25))
    # 2026-09-29: 原先用 32039 (两个都是十字孔) 穿长销插不进; 临时改 3 号轴, 用户指出一头圆孔一头十字的 32013 更常见, 改用它
    hadd("32013.dat", C_BEAM, (xc, 0, 0), CROSSHEAD_ROT, s)
    # 2026-10-04: 侧梁中段让开后, 长销和连杆在厚度方向不再被侧梁夹住; 改用 4 号轴, 两端半轴套挡住连杆。
    hadd("3705.dat", C_AXLE, (xc, 0, 0), ALONG_Z, s, note="十字接头横轴")
    for z in (-35, 35):
        hadd("32123a.dat", C_BUSH, (xc, 0, z), BUSH_Z, s, note="十字接头横轴挡套")
    for sy in (1, -1):
        piv = np.array([PIVOT_X, JAW_Y * sy, 0.0])
        R = rot_z(beta * sy)
        j = piv + R @ (np.array([JOINT_X, JAW_Y * sy, 0]) - piv)
        c = np.array([xc, 0.0, 0.0])
        d = (j - c) / np.linalg.norm(j - c)
        zl = 20.0 * sy
        hadd("32316.dat", C_LINK, (c + j) / 2 + [0, 0, zl], orient(np.cross([0, 0, 1.0], d), "+z", d), s, note="夹指连杆")
        hadd("3673.dat", C_FPIN, j + [0, 0, 10 * sy], ALONG_Z, s)
    # 推杆为一根 12 号轴: 支承在转盘凸台里的推杆导向和导向框前孔; 导向框后孔不用。
    s = st("推杆", "推杆是一根 12 号轴, 不用连接器: 前端插进十字接头的十字孔到底, 向后依次穿过推杆导向 (转盘凸台里)、转盘下半、导向框架前孔、半轴套、舵机侧十字块、半轴套。"
           "导向框架后孔不用, 推杆后端停在后孔前面。图示是完成位置, 实际穿法见下一步。", sub="机械头", view=(40, 25))
    rod_front = xc - 30 + ROD_FRONT_IN
    hadd("3708.dat", C_ROD, (rod_front - 120, 0, 0), ALONG_X, s)  # 一体推杆 12 号轴 (不加用途标记: 穿轴承孔属有意配合, 由 mechanical_audit 单独检查)
    st("装机械头", "转盘上半对准下半扣上 (两半本身卡在一起, 不用销)。然后从平台后面把 12 号轴沿推杆轴线穿过导向框架后孔 (只是借道), 依次穿过半轴套、舵机侧十字块、半轴套、导向框架前孔、转盘中孔和推杆导向, 最后插进十字接头的十字孔到底。"
       "安装全程断电, 舵机曲柄与黄色连杆暂不连接。"
       "先让推杆和夹指在无负载下平顺活动, 十字块两边半轴套不要夹得过紧。随后按 docs/single_arm.md 第 3 步进行空载定位、中间位置连接和小步标定。"
       "先粗调: 断电把舵机曲柄放在离折叠死点约 25° (还没折叠成一线), 推杆往后拉到轮胎刚好压住魔方, 再把十字块两侧半轴套贴紧十字块。"
       "再细调: 通电后用舵机脉宽往折叠方向小步加, 直到轮胎有明显压缩, 曲柄不要越过折叠死点。十字接头离推杆导向有约 8mm 余量, 不会先顶住。", attach=("机械头",), view=(40, 25), focus="module")

    if angle:
        R = rot_x(angle)
        for p in head:
            p.pos = R @ p.pos
            p.rot = R @ p.rot
    for p in parts:
        p.pos = p.pos + [MODULE_DX, 0, 0]
    return parts


# ---- 底座：四个 15x11 大框向外移 16mm，四角以 7x5 框架连接 --------------------
# 角框与大框同层；下面两根 15 孔梁各用两个销接角框，形成刚性连接。
BASE_Y = TABLE_Y - 30  # 上层 (大框、角上的 L 形梁) 中心; 下层梁在 TABLE_Y - 10, 放在桌面上
FRAME15_LONG_X = orient("+z", "+y")  # 39790: 局部 z 为 15 孔方向, 局部 x 为 11 孔方向, 局部 y 为厚度


def base_blade(s):
    """L 一侧的大框和它与 F 之间的角 (世界坐标, 其余三份由它转出)。"""
    # 本侧大框中心 x=-420；邻侧的长边仍在 x=-120，只沿 z 向外移动40。
    # 第一根下梁保留原位置，连接点改到 x=-400,-360,-320,-280。
    out = [Part("39790.dat", C_BASE, (-420, BASE_Y, -20), FRAME15_LONG_X, s)]
    yd, yp = BASE_Y + 20, BASE_Y + 10
    out.append(Part("32278.dat", C_BASE, (-260, yd, 80), BASE_BEAM_X, s))  # 垫在本框长边 (z = 80) 下面: x = -400 ... -120
    for x in (-400, -360, -320, -280):
        out.append(Part("2780.dat", C_PIN, (x, yp, 80), ALONG_Y, s))
    out.append(Part("32278.dat", C_BASE, (-120, yd, 280), BEAM_Z_HOLES_Y, s))  # 垫在 F 那块框的长边 (x = -120) 下面: z = 100 ... 380
    # 邻模块马达底块位于 z=320、360：长销穿大框后再进入底块。
    for z in (280, 400):
        out.append(Part("2780.dat", C_PIN, (-120, yp, z), ALONG_Y, s))
    for z in (320, 360):
        out.append(Part("6558.dat", C_LPIN, (-120, BASE_Y, z), orient("-y", "+x"), s))
    # 角框跨过扩大的间隔；两条下梁各接两个销，形成刚性连接。
    out.append(Part("64179.dat", C_BASE, (-160, BASE_Y, 140), FRAME_XZ_LONG_Z, s))
    for (x, z) in ((-120, 80), (-200, 80), (-120, 160), (-120, 200)):
        out.append(Part("2780.dat", C_PIN, (x, yp, z), ALONG_Y, s))
    return out


def build(state=None, with_cube=True):
    """整机 (世界坐标)。state: {位置: (open_s, angle)}, 缺省为全部夹紧、夹指竖直。
    搭建步骤按 L 模块登记; 其余三个模块在 "装另外三个机械手" 那一步整体出现。"""
    STEPS.clear()
    state = state or {}
    parts = []
    s = step("底座", "4 块 15x11 大框 (45680 套装里的) 摆成十字形, 每块的长边朝外, 靠里的短边就是竖墙的位置, "
             "相对两块的短边相距 28 个孔; 大框偏在长边中线的一侧半个孔 (看图)。大框下面垫 15 孔梁, 梁贴着桌面: "
             "每块大框的两条长边下面各一根: 长边上的竖孔是隔一个一个的, 最靠里的 4 个竖孔各插 1 个销, 其中马达那一侧长边的第 2、3 个用蓝色长销 (1 孔长的一段朝下插进梁, 上面露出 1 孔, 以后接马达底块; 看图), 其余用摩擦销, "
             "梁的一头伸出大框、到角上 (伸出多少看图)。"
             "相邻两块大框的梁在角上一横一竖摆放，角上放一块 7x5 框架（与大框同层），跨过两根下梁，"
             "4 个摩擦销（每根下梁 2 个）；短边两端孔接本侧下梁，长边第 5、7 孔接邻侧下梁。四个角做法一样。", sub="底座", view=(35, 60))
    for arm in ARMS:
        for p in base_blade(s):
            parts.append(p.moved(ARM_ROT[arm]))
    rest = []
    order = ["L"] + [a for a in ARMS if a != "L"]
    l_steps = []
    for k, arm in enumerate(order):
        o, a = state.get(arm, (0.0, 0.0))
        mparts = module(o, a, steps=(k == 0), on_base=True)
        if k == 0:
            l_steps = [p.step for p in mparts]
        for i, p in enumerate(mparts):
            q = p.moved(ARM_ROT[arm])
            q.arm = arm
            q.sub = l_steps[i]  # 四个模块零件生成顺序相同, 按序号对应 L 模块的步骤
            parts.append(q)
            if k:
                rest.append(q)
    s = step("装另外三个机械手", "照上面的步骤再做三个一样的机械手, 装到底座的另外三排上。四根推杆的轴线都过魔方中心, "
             "两两垂直 (底座的孔位保证了这一点, 不用调)。", view=(35, 35))
    for q in rest:
        q.step = s
    if with_cube:
        s = step("放入魔方", "四个舵机都转到 \"松开\", 四个机械手都转到竖直 (夹指一上一下)。魔方放在中间, "
                 "先夹紧 L、R, 再夹紧 F、B。", view=(35, 30))
        parts.append(Part("cube56.dat", 16, (0, 0, 0), I, s))
    return parts


def to_ldr(parts, title="quadcuber v3"):
    lines = [f"0 {title}", "0 Name: model.ldr", "0 Author: quadcuber", ""]
    cur = parts[0].step if parts else 1
    for p in sorted(parts, key=lambda p: p.step):
        if p.step != cur:
            lines.append("0 STEP")
            cur = p.step
        lines.append(p.ldraw())
    lines.append("0 STEP")
    return "\n".join(lines) + "\n"
