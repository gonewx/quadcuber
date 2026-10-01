"""四臂整机 v3 (按 CubeStormer 3 的思路重新设计) 的乐高模型。

v1 (tools/lego/model.py)、v2 (tools/lego/v2/) 都不改; v3 自成一体, 只复用上一级的 ldraw.py / check.py。

研究分支的平行夹块版:
1. 每片夹指由一根 7 孔粗主臂、两根 5 孔薄从动臂和两片 3x3 L 形薄梁组成。
   主、从动臂有效长度均为四孔, 从动轴在主轴后两孔、外一孔; 平行四边形约束夹块方向。
2. 3x5 L 形粗梁 32526 的长边末孔与短边中孔作为输入连杆, 有效孔距保持不变。
3. 接触垫图示含胶厚度 0.4mm, 闭合时每侧名义压缩 0.14mm; 夹紧力与摩擦需实物验证。
4. 舵机、平台、转盘、马达及底座的布置沿用父分支; 舵机连杆改为薄梁以避开推杆。齿轮比 24:60。
5. 四臂转动和魔方扫掠检查包括轴、轴套与销, 一层厚度为完整边长的三分之一。

模块坐标 (LDU, LDraw 约定 -Y 向上, 1 孔距 = 20 LDU = 8mm): 魔方中心在原点, 这个模块从 -X 方向夹住 L 面,
轴线就是 X 轴。其他三个模块由它绕 Y 轴转 90° / 180° / 270° 得到。桌面在 y = 290 (底座是两层梁)。
下面的尺寸常数是模块自身的坐标, 最后整体往魔方方向挪 MODULE_DX = 10 (半个孔距): 这样竖墙落在 x = -240 的整孔位上,
四个模块转 90° 之后孔位仍然对得上, 底座才能用同一套孔格把它们连成一体 (墙在 -250 时, 相邻模块的孔位差半个孔距)。

所有推导见 docs/lego/v3/README.md。
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
    "41239.dat": ("13 孔粗梁", "solid"),
    "32449.dat": ("4 孔薄梁 (两端十字孔)", "solid"),
    "43857.dat": ("2 孔粗梁", "solid"),
    "32063.dat": ("6 孔薄梁 (圆孔)", "solid"),
    "32017.dat": ("5 孔薄梁 (圆孔)", "solid"),
    "2905.dat": ("5x3 三角薄梁", "solid"),
    "11478.dat": ("5 孔薄梁 (两端十字孔)", "solid"),
    "3737.dat": ("10 号轴", "axle"),
    "3707.dat": ("8 号轴", "axle"),
    "32056.dat": ("3x3 L 形薄梁", "solid"),
    "80286.dat": ("2x5 弯梁", "solid"),
    "3705.dat": ("4 号轴", "axle"),
    "jaw_pad.dat": ("接触垫一对 (每条 12.8×3.2×0.4mm, 含胶, 非乐高)", "solid"),
    "32524.dat": ("7 孔粗梁", "solid"),
    "32316.dat": ("5 孔粗梁", "solid"),
    "32278.dat": ("15 孔粗梁", "solid"),
    "32525.dat": ("11 孔粗梁", "solid"),
    "32523.dat": ("3 孔粗梁", "solid"),
    "32526.dat": ("3x5 L 形粗梁", "solid"),
    "41677.dat": ("2 孔细梁 (两端十字孔)", "solid"),
    "32013.dat": ("角度连接器 1 号 (一头十字孔, 一头横圆孔)", "solid"),
    "6536.dat": ("十字块 1x2 (十字孔 + 圆孔)", "solid"),
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
    "44294.dat": ("7 号轴", "axle"),
    "3708.dat": ("12 号轴", "axle"),
    "50451.dat": ("16 号轴", "axle"),
    "59443.dat": ("轴连接器 (光面, 两头十字孔)", "solid"),
    "3713.dat": ("轴套", "bush"),
    "32123a.dat": ("半轴套", "bush"),
    "rubberband.dat": ("乐高 15mm 皮带 x37 (绕夹指 2 圈)", "solid"),
    "cube56.dat": ("56mm 魔方 (示意)", "other"),
}
# 检查用的销/轴长度 (LDU), 补到 check.CONNECTOR_LEN 里
CONNECTOR_LEN = {"3673.dat": 40, "32556a.dat": 60, "3749.dat": 40, "32062.dat": 40, "32073.dat": 100,
                 "44294.dat": 140, "4519.dat": 60, "3705.dat": 80, "3706.dat": 120, "3707.dat": 160, "3737.dat": 200, "50451.dat": 320}

C_FRAME = 71  # 浅灰
C_BASE = 72  # 深灰: 底座
C_BEAM = 0  # 黑
C_JAW = 4  # 红: 主摆臂
C_AUX = 1  # 蓝: 从动臂
C_PAD = 25  # 橙: 平行夹块
C_BAND = 10  # 绿: 薄弹性接触垫
C_LINK = 14  # 黄: 连杆 (醒目)
C_PIN = 0
C_FPIN = 71  # 浅灰: 无摩擦销
C_LPIN = 1  # 蓝: 长销
C_TPIN = 19  # 米色: 无摩擦长销、轴销
C_SPIN = 4  # 红: 带挡套长销
C_AXLE = 0
C_ROD = 71  # 浅灰: 推杆 (16 号轴)
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
MODULE_DX = 10.0  # 模块整体往魔方方向挪半个孔距 (见文件开头)

# 平行四边形: 有效臂长 80 LDU; 从动轴相对主轴后移 40、向外移 20 LDU。
JAW_Y = 80.0
PIVOT_X = -130.0
JOINT_X = -150.0
JAW_A = PIVOT_X - JOINT_X
JAW_REACH = 80.0
PARALLEL_DX = -40.0
PARALLEL_DY = 20.0
# 32526: 长边末孔 (0, 0, 0) 接主臂, 短边中孔 (20, 0, 80) 接十字接头, 均为圆孔。
LINK_L = math.hypot(80.0, 20.0)
CLAMP_BETA = math.radians(-0.25)
OPEN_BETA = math.radians(16.5)
PAD_T = 1.0  # LDU = 0.4mm, 含胶总厚度; 实物标定预压, 不把厚度当成夹紧力。
JAW_TIP_X = -40.0


def cross_x_for_beta(beta):
    """主摆臂角度对应的十字接头 X, 取接头在输入关节后方的工作支路。"""
    jy = JAW_Y - JAW_A * math.sin(beta)
    return PIVOT_X - JAW_A * math.cos(beta) - math.sqrt(LINK_L ** 2 - jy ** 2)


CROSS_CLOSED_X = cross_x_for_beta(CLAMP_BETA)

# 推杆 (3 号轴 + 连接器 + 12 号轴): 前端插进十字接头 32013 的十字孔
ROD_FRONT_IN = 20.0  # 插进十字孔的深度: 插到底 (2026-09-29 用户实物: 原来只插一半, 实际会插到底, 十字接头就差半个孔到不了死点)

# 舵机 (固定在底座平台上): 输出轴沿 Z, 在十字块后面; 夹紧时曲柄和连杆拉成一条直线 (死点)
SERVO_C = np.array([-470.0, 30.0, 80.0])  # 舵机本体中心
CRANK_C = np.array([-480.0, 30.0])  # 输出轴 (x, y)
CRANK_R = 20.0
LINK2_L = 80.0  # 舵机连杆 = 5 孔圆孔薄梁 32017
BLOCK_Y = 20.0  # 十字块上连杆轴的高度 (推杆在 y = 0)


def jaw_beta(s):
    """推杆后退 s 时主摆臂角度。闭合为小内收角, 前端夹块由四连杆保持平行。"""
    if s < 0:
        raise ValueError("不能越过已设定的夹紧端点")
    dx = PIVOT_X - (CROSS_CLOSED_X - s)
    r = math.hypot(dx, JAW_Y)
    q = (r * r + JAW_A * JAW_A - LINK_L * LINK_L) / (2 * JAW_A * r)
    if not -1.0 <= q <= 1.0:
        raise ValueError(f"夹指行程不可达: {s:.3f} LDU")
    return math.atan2(JAW_Y, dx) - math.acos(q)


def servo_theta_for(s):
    """推杆从夹紧位置后退 s 时曲柄的角度 (相对 +X, 向上为负) 和夹紧时十字块连杆轴的 x。"""

    def rod_x(th):
        p = CRANK_C + CRANK_R * np.array([math.cos(th), math.sin(th)])
        return p[0] + math.sqrt(LINK2_L ** 2 - (p[1] - BLOCK_Y) ** 2)

    th0 = -math.atan2(CRANK_C[1] - BLOCK_Y, math.sqrt((LINK2_L + CRANK_R) ** 2 - (CRANK_C[1] - BLOCK_Y) ** 2))
    x0 = rod_x(th0)
    h = CRANK_C[1] - BLOCK_Y
    max_stroke = math.sqrt((LINK2_L + CRANK_R) ** 2 - h * h) - math.sqrt((LINK2_L - CRANK_R) ** 2 - h * h)
    if not 0 <= s <= max_stroke:
        raise ValueError(f"舵机曲柄行程不可达: {s:.3f} LDU, 最大 {max_stroke:.3f}")
    if s == 0:
        return th0, x0
    lo, hi = -math.pi - math.asin(h / (LINK2_L - CRANK_R)), th0
    for _ in range(60):
        m = (lo + hi) / 2
        if x0 - rod_x(m) > s:
            lo = m
        else:
            hi = m
    return (lo + hi) / 2, x0


OPEN_S = CROSS_CLOSED_X - cross_x_for_beta(OPEN_BETA)
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
        q.arm, q.head = self.arm, self.head
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
    """一个机械手模块 (模块坐标)。open_s: 推杆从标称夹紧位置后退的距离; angle: 机械手转过的角度 (度),
    0 表示夹指在竖直平面 (夹指一上一下)。steps=False 时不登记搭建步骤 (其余三个模块)。
    on_base=True 时加上竖墙、马达底块和底座之间的销 (单独检查模块时没有底座, 不加)。"""
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
           "长边沿框架的长边, 圆盘的边沿贴住框架正面。然后从转盘中孔里面插 2 根红色带挡套长销: 把销平放进凸台里面 "
           "(凸台两端壁之间正好放下一根, 很紧), 再往外推, 销穿过凸台端壁插进框架短边, 挡套留在凸台里面。"
           "一根用上排孔, 另一根用另一头的下排孔 (同一排两根的挡套会互相挡住)。", sub="竖墙", view=(60, 20))
    add("18939.dat", C_TT, TT_C, TT_ROT, s)
    add("32054.dat", C_SPIN, (WALL_X, -20, -40), orient("-z", "+y"), s)
    add("32054.dat", C_SPIN, (WALL_X, 20, 40), ALONG_Z, s)

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
           "6 个摩擦销竖着连起来 (框架正面孔: 一根梁 4 个, 另一根梁靠前的 2 个孔各插 1 个, 靠后的 2 个孔留给导向框架的长销)。"
           "梁的后段上面, 舵机那一侧压一根 7 孔粗梁当舵机垫块: 从平台后端向魔方数, 第 1、3、5 孔用 3 个黑色摩擦销接下面的 15 孔梁; 第 2、6 孔留给舵机耳朵的蓝色长销; 第 4、7 孔不插销。第 2、4 孔下方梁孔由 55615 占用, 第 2 孔的蓝销短端只进入垫梁, 不能贯穿下面的梁。两根梁的最后一个孔上横压一根 5 孔粗梁, 2 个摩擦销, 让后段也连成封闭的长方形。"
           "两根梁后段的下面各挂一个 55615 (90° 弯角销连接器): 横臂顺着梁、竖臂朝下, 横臂上朝上的 2 个销从下面插进梁孔: 马达那一侧的梁插倒数第 2、4 个孔; 舵机那一侧的梁插倒数第 3、5 个孔 (倒数第 5 个孔就在垫块空着的第 4 个孔正下方); "
           "竖臂上的 2 个孔朝外 (朝平台两侧)。平台前段上面竖立一块框架当推杆导向: 它长边沿推杆方向, 框架比原版后移两孔, 底边用 2 根蓝色长摩擦销竖着插进平台: 1 孔长的一段朝上插进导向框架, 2 孔长的一段穿过平台框架, 一直插进下面那根 15 孔梁; "
           "原来最前面的蓝销改为黑销, 只连接平台框架与下方梁。导向框架两条短边上正中的侧孔 (圆孔) 就是推杆的两个轴承。", sub="平台", view=(30, 40))
    add("64179.dat", C_FRAME, (-330, 60, 40), FRAME_XZ_LONG_X, s)
    for z in (0, 80):
        add("32278.dat", C_BEAM, (-410, 80, z), BASE_BEAM_X, s)
    for x in (-390, -350, -310, -270):
        add("2780.dat", C_PIN, (x, 70, 80), ALONG_Y, s)
    add("2780.dat", C_PIN, (-270, 70, 0), ALONG_Y, s)
    add("32524.dat", C_BEAM, (-470, 60, 80), BASE_BEAM_X, s)
    # 7 孔垫梁第 1/3/5 孔接平台, 第 2/6 孔接后移一孔的舵机。
    # 第 2/4 孔下方 (x=-510/-470) 由 55615 从下方占用, 不加贯穿销。
    for x in (-530, -490, -450):
        add("2780.dat", C_PIN, (x, 70, 80), ALONG_Y, s)
    gf_c = np.array([-390.0, 0.0, 0.0])
    add("64179.dat", C_FRAME, gf_c, FRAME_XY_LONG_X, s)
    # 导向框架底边的 2 个销用蓝色长销, 一直穿过平台框架插进下面那根 15 孔梁 (否则这根梁只有 1 个销, 用户 2026-09-29 指出):
    # 1 孔长的一段朝上插进导向框架, 挡肩压在平台框架上面, 2 孔长的一段穿过平台框架和梁
    for x in (-390, -350):
        add("6558.dat", C_LPIN, (x, 60, 0), orient("+y", "+x"), s)
    add("2780.dat", C_PIN, (-310, 70, 0), ALONG_Y, s)
    # 两根 15 孔梁的后端用一根 5 孔梁横着连起来, 和前面的框架围成一个封闭的长方形
    add("32316.dat", C_BEAM, (-550, 60, 40), BEAM_Z_HOLES_Y, s)
    for z in (0, 80):
        add("2780.dat", C_PIN, (-550, 70, z), ALONG_Y, s)
    # 55615: 局部 z 为横臂方向 (横臂上的销朝局部 +y), 局部 -y 为竖臂方向 (竖臂上的销朝局部 -z), 孔沿局部 x。
    # 平台下的两个: 横臂沿 +x 贴在梁下面, 销朝上; 竖臂朝下; 孔沿 z。竖臂上多出的 2 个销朝后, 空着。
    for (x, z) in ((-530, 0), (-510, 80)):
        add("55615.dat", C_BEAM, (x, 100, z), BENT_UNDER_BEAM, s)
    s = st("舵机", "舵机平放在平台后端的垫块上, 输出轴朝推杆那一侧。2 根蓝色长摩擦销从上面插进舵机两只耳朵, "
           "1 孔长的那段朝下插进垫块第 2、6 孔 (从平台后端向魔方数), 避开垫块的 3 个黑色摩擦销。", sub="平台", view=(30, 40))
    add("geekservo.dat", C_SERVO, SERVO_C, SERVO_ROT, s)
    for dx in (-40, 40):
        add("6558.dat", C_LPIN, (SERVO_C[0] + dx, 40, SERVO_C[2]), LPIN_SHORT_Y, s)
    s = st("装平台", "先在大框后短边 (离竖墙最远的那条短边) 上放一个 55615: 横臂顺着短边, 朝下的 2 个销插进短边第 1、2 个竖孔 (从马达那一侧数, 看图), 竖臂朝上, 竖臂上的 2 个销朝马达那一侧。"
           "然后平台前端顶住竖墙背面, 2 个摩擦销沿推杆方向穿进墙的孔。检查导向框架的两个轴承孔、转盘中孔在一条直线上。"
           "最后装两根竖梁 (9 孔粗梁), 都从外侧压上去: 马达那一侧, 先在平台下 55615 的 2 个孔里插摩擦销, 竖梁上端 2 个孔套这 2 个销、下端 2 个孔套底座上 55615 的 2 个销; "
           "另一侧, 在平台下 55615 的 2 个孔和大框长边外侧的侧孔 (看图) 各插 1 个摩擦销, 竖梁压上去, 下端最后一个孔接大框。",
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

    # 推杆 + 曲柄滑块 (舵机侧)
    th, x0 = servo_theta_for(open_s)
    crank_pin = CRANK_C + CRANK_R * np.array([math.cos(th), math.sin(th)])
    bx = crank_pin[0] + math.sqrt(LINK2_L ** 2 - (crank_pin[1] - BLOCK_Y) ** 2)  # 十字块上连杆轴的 x
    s = st("十字块和舵机连杆", "十字块圆孔在上, 放进导向框架的开口里, 圆孔对准推杆轴承孔; 两侧各放一个半轴套, 推杆后面穿入。"
           "3 号轴穿过十字块下面的十字孔: 背离舵机的一端露半孔, 套一个半轴套; 朝舵机的一端露一孔半, 依次套半轴套、黄色 5 孔圆孔薄梁 32017、半轴套。"
           "图示是最终夹紧位置, 首次装配先让薄连杆的曲柄端脱开。按单臂标定步骤, 用 servo 1500 空载定位, 断电后在行程中间调整曲柄方向并连接。"
           "曲柄端用 3 号轴, 轴头与曲柄外侧齐平, 穿过薄连杆后只套一个半轴套。保留朝推杆一侧的细轴余段, 不在那里再加第二个轴套。"
           "不要换回粗连杆加两个半轴套的叠法, 该叠法在松开时会蹭旋转推杆。连接后手转推杆核对间隙。不要带连杆直接首次定位, 也不要硬拉连杆对孔。", view=(30, 30))
    add("6536.dat", C_BEAM, (bx, BLOCK_Y, 0), BLOCK_ROT, s)
    rod_bushes = []
    for dx in (-15, 15):
        rod_bushes.append(add("32123a.dat", C_BUSH, (bx + dx, 0, 0), BUSH_X, s, head=True))
    # 十字块占 z=-10..10, 内半轴套 10..20, 薄连杆 20..30, 外半轴套 30..40。
    add("4519.dat", C_AXLE, (bx, BLOCK_Y, 10), ALONG_Z, s)
    for z in (-15, 15, 35):
        add("32123a.dat", C_BUSH, (bx, BLOCK_Y, z), BUSH_Z, s)
    cdir = np.array([math.cos(th), math.sin(th), 0.0])
    add("41677.dat", C_BEAM, (CRANK_C[0], CRANK_C[1], 35), orient(np.cross([0, 0, 1.0], cdir), "+z", cdir), s)
    # 3 号轴固定在曲柄十字孔里。薄连杆在 z=20..30, 内侧半轴套在 10..20。
    # 原粗连杆 + z=±5 的轴套会蹭旋转推杆; 留在负 Z 侧的细轴段与推杆有间隙。
    add("4519.dat", C_AXLE, (crank_pin[0], crank_pin[1], 10), ALONG_Z, s)
    add("32123a.dat", C_BUSH, (crank_pin[0], crank_pin[1], 15), BUSH_Z, s)
    e = np.array([crank_pin[0] - bx, crank_pin[1] - BLOCK_Y, 0.0])
    e /= np.linalg.norm(e)
    mid = (np.array([bx, BLOCK_Y]) + crank_pin) / 2
    add("32017.dat", C_LINK, (mid[0], mid[1], 25), orient(np.cross([0, 0, 1.0], e), "+z", e), s)

    # ================= 4. 转动部分 (机械头) =================
    xc = CROSS_CLOSED_X - open_s  # 十字接头横轴的 x
    beta = jaw_beta(open_s)
    head = rod_bushes.copy()

    def hadd(name, color, pos, rot, s, note=""):
        p = add(name, color, pos, rot, s, head=True, note=note)
        head.append(p)
        return p

    s = st("后部夹指架", "两侧各做一套支架。后列为 9 孔粗梁, 前列为 11 孔粗梁, 两根中心对齐, 沿推杆方向相隔一孔。"
           "在中心上、下第 3 孔和第 4 孔的位置各装一组横梁: 每组由两根 4 孔薄梁 32449 贴合, 位于竖梁内侧。"
           "横梁后端十字孔用 2 号轴接 9 孔竖梁, 从后数第 2 个圆孔用黑销接 11 孔竖梁。横梁继续向魔方伸出两孔, 前端十字孔留给主轴座。", sub="机械头", view=(40, 25))
    for sz in (1, -1):
        hadd("32525.dat", C_BEAM, (PIVOT_X + PARALLEL_DX, 0, 80 * sz), BEAM_Y_HOLES_Z, s)
        hadd("40490.dat", C_FRAME, (-190, 0, 80 * sz), BEAM_Y_HOLES_Z, s)
        for y in (-80, -60, 60, 80):
            for z in (55, 65):
                hadd("32449.dat", C_FRAME, (-160, y, z * sz), BEAM_X_HOLES_Z, s)
            hadd("32062.dat", C_AXLE, (-190, y, 70 * sz), ALONG_Z, s)
            hadd("2780.dat", C_PIN, (-170, y, 70 * sz), ALONG_Z, s)
    s = st("前端主轴座", "两侧各加上、下两根 3 孔粗梁, 贴在横梁内侧。中孔用 2 号轴接靠中心的横梁前端十字孔, 外端孔暂时留空, 随后由主摆臂的贯穿轴固定。"
           "先完成上一页后部支架, 再从内侧放上这四根短梁并穿轴。", sub="机械头", view=(40, 25))
    for sz in (1, -1):
        for sy in (-1, 1):
            hadd("32523.dat", C_BEAM, (PIVOT_X, sy * 60, 40 * sz), BEAM_Y_HOLES_Z, s)
            hadd("32062.dat", C_AXLE, (PIVOT_X, sy * 60, 50 * sz), ALONG_Z, s)
    s = st("转盘连接短梁", "在每侧后部 9 孔竖梁的中心上下各一孔处, 从内侧装一根 2 孔粗梁。"
           "短梁沿推杆方向向后伸出一孔, 前端用黑色摩擦销接竖梁, 后端留给转盘安装耳。先完成这一页, 再安装转盘。", sub="机械头", view=(40, 25))
    for sz in (1, -1):
        for y in (-20, 20):
            hadd("43857.dat", C_FRAME, (-200, y, 60 * sz), BEAM_X_HOLES_Z, s)
            hadd("2780.dat", C_PIN, (-190, y, 70 * sz), ALONG_Z, s)
    s = st("转盘上半", "转盘有齿的一面朝后。两只安装耳各插两个黑色摩擦销。"
           "再把两套侧架从左右压上去, 2 孔连接短梁的后端圆孔对准转盘安装耳上的销。", sub="机械头", view=(40, 25))
    hadd("18938.dat", C_TT, TT_C, TT_ROT, s)
    for sz in (1, -1):
        for y in (-20, 20):
            hadd("2780.dat", C_PIN, (-210, y, 50 * sz), ALONG_Z, s)
    s = st("主摆臂", "每片夹指改用一根 7 孔粗梁 32524。从后端数第 2 孔接输入连杆, 第 3 孔为主转轴, 第 7 孔接前端夹块; 最后面的第 1 孔留空。"
           "7 号轴穿过两侧主轴座和横梁。粗梁居中, 左右各放一个整轴套, 再穿过 3 孔主轴座和两片 4 孔薄横梁。"
           "横梁端部十字孔固定轴, 粗梁的圆孔绕轴转动。轴端与横梁外侧齐平, 不加外侧轴套。", sub="机械头", view=(40, 25))
    for sy in (1, -1):
        piv = np.array([PIVOT_X, JAW_Y * sy, 0.0])
        R = rot_z(beta * sy)
        hadd("32524.dat", C_JAW, piv + R @ np.array([20.0, 0, 0]), R @ BEAM_X_HOLES_Z, s)
        hadd("44294.dat", C_AXLE, piv, ALONG_Z, s)
        for z in (-20, 20):
            hadd("3713.dat", C_BUSH, piv + [0, 0, z], BUSH_Z, s)
    s = st("平行从动臂", "每片夹指装两根 5 孔薄梁 11478, 两端为十字孔。根部装在后列 11 孔支架的最外端孔, 使用 10 号轴。"
           "相对主轴, 从动轴向后两孔、向外一孔。沿轴从中央往两边依次为: 中央整轴套的半边、半轴套、蓝色薄梁、两个整轴套、11 孔支架、外侧半轴套。"
           "轴随蓝色薄梁一起转, 在支架圆孔里转动。", sub="机械头", view=(40, 25))
    for sy in (1, -1):
        piv = np.array([PIVOT_X + PARALLEL_DX, (JAW_Y + PARALLEL_DY) * sy, 0.0])
        R = rot_z(beta * sy)
        for z in (-25, 25):
            hadd("11478.dat", C_AUX, piv + R @ np.array([40.0, 0, z]), R @ BEAM_X_HOLES_Z, s)
        hadd("3737.dat", C_AXLE, piv, R @ ALONG_Z, s)
        hadd("3713.dat", C_BUSH, piv, R @ BUSH_Z, s)
        for z in (-95, -15, 15, 95):
            hadd("32123a.dat", C_BUSH, piv + [0, 0, z], R @ BUSH_Z, s)
        for z in (-60, -40, 40, 60):
            hadd("3713.dat", C_BUSH, piv + [0, 0, z], R @ BUSH_Z, s)
    s = st("平行夹块", "每个夹块用两片 32056（3x3 L 形薄梁）分列粗主臂两侧, 中间留一孔厚的空档。L 的一边沿推杆方向, 另一边在后端朝夹指外侧伸出。不能再用 2905 三角梁, 其后端会撞主根轴和轴套。"
           "先将两片 L 梁从前端滑入红色粗主臂与蓝色薄从动臂之间的空档, 再穿前端两根轴。靠魔方一端的端部十字孔用 2 号轴连接红色粗主臂前端圆孔, 轴端与 L 梁外侧齐平。"
           "L 梁朝外那一边的中间圆孔用 3 号轴连接蓝色从动臂前端十字孔。两片 L 梁之间放一个整轴套, 蓝梁贴在 L 梁外侧, 轴端与蓝梁外侧齐平。"
           "这里轴固定在蓝梁里, L 梁绕轴转动。L 的拐角和朝外末端十字孔留空。装完后手动开合, 夹块接触边应始终平行。", sub="机械头", view=(40, 25))
    for sy in (1, -1):
        piv = np.array([PIVOT_X, JAW_Y * sy, 0.0])
        R = rot_z(beta * sy)
        front = piv + R @ np.array([JAW_REACH, 0, 0])
        pad_rot = orient([1, 0, 0], [0, 0, -sy], [0, sy, 0])
        for z in (-15, 15):
            hadd("32056.dat", C_PAD, front + [-40, 0, z], pad_rot, s)
        hadd("32062.dat", C_AXLE, front, ALONG_Z, s)
        outer = front + [PARALLEL_DX, PARALLEL_DY * sy, 0]
        hadd("4519.dat", C_AXLE, outer, R @ ALONG_Z, s)
        hadd("3713.dat", C_BUSH, outer, R @ BUSH_Z, s)
    s = st("接触垫", "在每片 L 形薄梁朝魔方的平直边各贴一条薄弹性垫, 图中按含胶总厚度 0.4mm 表示。"
           "每条垫片尺寸 12.8×3.2mm, 沿底边从前端孔向后 1.6mm 开始贴, 不包住转轴或伸到相邻层。厚度和压紧量以实测为准; 先手动确认夹块能贴平, "
           "再标定闭合位置, 不用加大舵机行程去硬压塑料。", sub="机械头", view=(40, 25))
    for sy in (1, -1):
        piv = np.array([PIVOT_X, JAW_Y * sy, 0.0])
        front = piv + rot_z(beta * sy) @ np.array([JAW_REACH, 0, 0])
        hadd("jaw_pad.dat", C_BAND, front, orient([1, 0, 0], [0, sy, 0], [0, 0, sy]), s)
    s = st("L 形输入连杆", "上下各用一根 32526（3x5 L 形粗梁）。长边远离拐角的末孔接红色主臂从后数第 2 孔; 短边中孔（从拐角数第 2 孔）接十字接头。短边的拐角孔与末孔留空。上下两根按图镜像安装。"
           "先不穿轴: 保持图示朝向, 从两夹指之间的空档放入 L 梁, 向后移到接头位置, 再向对应主臂平移对孔。两根梁就位后再穿轴, 不要越过主根轴硬推。"
           "十字接头圆孔穿 4 号轴: 接头居中, 两侧直接贴 L 梁, 最外侧各放一个半轴套。这里不再放接头与连杆之间的半轴套。"
           "L 梁另一端直接贴粗主臂外侧, 用 3 号轴穿过两根粗梁, 两端各一个半轴套。原 4 号轴、内侧半轴套和背面的整轴套不沿用。"
           "两处都要转动顺畅, 半轴套贴近但不要挤紧。有效孔距和开合行程保持原值; 不用改变前端夹块角度。", sub="机械头", view=(40, 25))
    hadd("32013.dat", C_BEAM, (xc, 0, 0), CROSSHEAD_ROT, s)
    hadd("3705.dat", C_AXLE, (xc, 0, 0), ALONG_Z, s)
    for z in (-35, 35):
        hadd("32123a.dat", C_BUSH, (xc, 0, z), BUSH_Z, s)
    for sy in (1, -1):
        piv = np.array([PIVOT_X, JAW_Y * sy, 0.0])
        j = piv + rot_z(beta * sy) @ np.array([-JAW_A, 0, 0])
        c = np.array([xc, 0.0, 0.0])
        # 局部短边中孔 -> 长边末孔的向量为 (-20, 0, -80)。
        theta = math.atan2(abs(j[1]), j[0] - xc) - math.atan2(-20, -80)
        mirror = np.diag([1, sy, sy])
        link_rot = mirror @ rot_z(theta) @ BEAM_X_HOLES_Z
        hadd("32526.dat", C_LINK, c + [0, 0, 20 * sy] - link_rot @ np.array([20, 0, 80]), link_rot, s)
        hadd("4519.dat", C_AXLE, j + [0, 0, 10 * sy], ALONG_Z, s)
        for z in (-15 * sy, 35 * sy):
            hadd("32123a.dat", C_BUSH, j + [0, 0, z], BUSH_Z, s)
    # 导向框后移两孔, 十字接头后移一孔: 推杆短轴从 2 号改成 3 号, 保持后轴承穿入量。
    # 两轴各插入连接器半长, 总长 15 孔; 短轴中间露出一孔, 不把连接器顶到十字接头上。
    s = st("推杆", "推杆用 3 号轴 + 光面轴连接器 + 12 号轴接成 15 孔长: 3 号轴的一端插进十字接头到底, "
           "另一端插进连接器半长, 再把 12 号轴从另一头插入到底 (两根轴在连接器中间顶住)。"
           "3 号轴中间有一孔露在外面, 不要强推连接器去贴十字接头。", sub="机械头", view=(40, 25))
    rod_front = xc - 30 + ROD_FRONT_IN
    hadd("4519.dat", C_ROD, (rod_front - 30, 0, 0), ALONG_X, s)
    hadd("59443.dat", C_BEAM, (rod_front - 60, 0, 0), BUSH_X, s)
    hadd("3708.dat", C_ROD, (rod_front - 180, 0, 0), ALONG_X, s)
    st("装机械头", "推杆从转盘下半的中孔往后穿, 依次穿过导向框架前面的轴承孔、半轴套、十字块、半轴套、后面的轴承孔。"
       "转盘上半对准下半扣上 (两半本身卡在一起, 不用销)。安装全程断电, 舵机曲柄与黄色连杆暂不连接。"
       "先让推杆和夹指在无负载下平顺活动, 十字块两边半轴套不要夹得过紧。随后按 docs/single_arm.md 第 3 步进行空载定位、中间位置连接和小步标定。"
       "确认夹紧位置后再断电调整十字块在推杆上的位置, 以接触垫轻微压缩、夹块保持平行为准, 并将两侧半轴套贴近十字块。前端弯梁连杆不要求与推杆垂直。"
       "图示是标称夹紧状态。实物夹紧力、厚度和销孔间隙仍需单臂验证, 不能用舵机强推对孔。", attach=("机械头",), view=(40, 25), focus="module")


    if angle:
        R = rot_x(angle)
        for p in head:
            p.pos = R @ p.pos
            p.rot = R @ p.rot
    for p in parts:
        p.pos = p.pos + [MODULE_DX, 0, 0]
    return parts


# ---- 底座: 每个模块一块 15x11 大框 (39790, 用户的 SPIKE Prime 扩展套装 45680 里有 4 块; 2026-09-29) --------------
# 两层: 大框在上层 (和原来网格底座的上层同高), 竖墙立在大框靠魔方的短边上, 马达底块 (两层 5 孔梁) 销在大框的一条长边上;
# 下层是贴着桌面的 15 孔梁。四块大框之间在角上隔着空当, 每个角: 两根 15 孔梁分别垫在两块大框的长边下面
# (各 4 个销), 一直伸到角上; 一根 3x5 L 形梁放在上层 (和大框同一层) 的空当里, 压在两根梁的末端上, 每根梁 2 个销,
# 所以这个角是刚性的 (两根梁只用一个销交叉会变成铰链, 四个角都是铰链时底座能被推成菱形)。
# 梁放在大框下面而不是上面: 上面会从竖墙底下和马达底块底下穿过。
BASE_Y = TABLE_Y - 30  # 上层 (大框、角上的 L 形梁) 中心; 下层梁在 TABLE_Y - 10, 放在桌面上
FRAME15_LONG_X = orient("+z", "+y")  # 39790: 局部 z 为 15 孔方向, 局部 x 为 11 孔方向, 局部 y 为厚度


def base_blade(s):
    """L 一侧的大框和它与 F 之间的角 (世界坐标, 其余三份由它转出)。"""
    # 大框的孔是竖孔和侧孔交替, 竖孔离中心是 20 的奇数倍; 竖墙底边的侧孔在 z = 0、±40,
    # 所以大框往 -z 偏 20 (半个孔距): 两条长边在 z = -120 (正好在马达底面那排销孔下面) 和 80, 竖孔 x = -520 ... -240。
    out = [Part("39790.dat", C_BASE, (-380, BASE_Y, -20), FRAME15_LONG_X, s)]
    yd, yp = BASE_Y + 20, BASE_Y + 10
    out.append(Part("32278.dat", C_BASE, (-260, yd, 80), BASE_BEAM_X, s))  # 垫在本框长边 (z = 80) 下面: x = -400 ... -120
    for x in (-360, -320, -280, -240):
        out.append(Part("2780.dat", C_PIN, (x, yp, 80), ALONG_Y, s))
    out.append(Part("32278.dat", C_BASE, (-120, yd, 240), BEAM_Z_HOLES_Y, s))  # 垫在 F 那块框的长边 (x = -120) 下面: z = 100 ... 380
    # 这条长边正上方是 F 的马达底块, 马达底块要销在 z = 280、320 这两个竖孔上, 可这两个孔已经被这根梁的销占满了
    # (用户 2026-09-29 实物发现)。所以这两个位置改用蓝色长销 6558: 1 孔长的一段朝下插进梁, 挡肩在梁和大框之间,
    # 2 孔长的一段穿过大框再往上露出 1 孔, 装竖墙时马达底块直接压上去。
    for z in (240, 360):
        out.append(Part("2780.dat", C_PIN, (-120, yp, z), ALONG_Y, s))
    for z in (280, 320):
        out.append(Part("6558.dat", C_LPIN, (-120, BASE_Y, z), orient("-y", "+x"), s))
    out.append(Part("32526.dat", C_BASE, (-120, BASE_Y, 160), orient("-x", "+y", "-z"), s))  # 拐角在 (-120, 80)
    for (x, z) in ((-120, 80), (-160, 80), (-120, 120), (-120, 160)):
        out.append(Part("2780.dat", C_PIN, (x, yp, z), ALONG_Y, s))
    return out


def build(state=None, with_cube=True):
    """整机 (世界坐标)。state: {位置: (open_s, angle)}, 缺省为全部夹紧、夹指竖直。
    搭建步骤按 L 模块登记; 其余三个模块在 "装另外三个机械手" 那一步整体出现。"""
    STEPS.clear()
    state = state or {}
    parts = []
    s = step("底座", "4 块 15x11 大框 (45680 套装里的) 摆成十字形, 每块的长边朝外, 靠里的短边就是竖墙的位置, "
             "相对两块的短边相距 24 个孔; 大框偏在长边中线的一侧半个孔 (看图)。大框下面垫 15 孔梁, 梁贴着桌面: "
             "每块大框的两条长边下面各一根: 长边上的竖孔是隔一个一个的, 最靠里的 4 个竖孔各插 1 个销, 其中马达那一侧长边的第 2、3 个用蓝色长销 (1 孔长的一段朝下插进梁, 上面露出 1 孔, 以后接马达底块; 看图), 其余用摩擦销, "
             "梁的一头伸出大框、到角上 (伸出多少看图)。"
             "相邻两块大框的梁在角上一横一竖挨着, 最后在角上 (和大框同一层) 放一根 3x5 L 形梁, 拐角对准横梁末端的孔, "
             "4 个摩擦销 (每根梁 2 个)。四个角做法一样。", sub="底座", view=(35, 60))
    for arm in ARMS:
        for p in base_blade(s):
            parts.append(p.moved(ARM_ROT[arm]))
    rest = []
    order = ["L"] + [a for a in ARMS if a != "L"]
    for k, arm in enumerate(order):
        o, a = state.get(arm, (0.0, 0.0))
        for p in module(o, a, steps=(k == 0), on_base=True):
            q = p.moved(ARM_ROT[arm])
            q.arm = arm
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
