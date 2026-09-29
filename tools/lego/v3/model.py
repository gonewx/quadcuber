"""四臂整机 v3 (按 CubeStormer 3 的思路重新设计) 的乐高模型。

v1 (tools/lego/model.py)、v2 (tools/lego/v2/) 都不改; v3 自成一体, 只复用上一级的 ldraw.py / check.py。

和 v2 相比的根本变化:
1. **夹爪改成两片会转的夹指 + 死点锁紧**: 夹指绕根部的轴转动, 推杆把中间的十字接头往前推,
   两根连杆推到和轴线垂直 (死点) 时夹指合拢。魔方把夹指往外推的力沿连杆方向传到中间, 两边互相抵消,
   舵机不受力, 夹指也推不开 (外部评审指出的 "叉子水平时没有压紧力、曲柄停在死点不等于锁紧" 由此解决)。
2. **舵机不跟着转**: 舵机装在固定的底座上, 通过一根穿过转盘中孔的推杆开合夹爪。转动部分没有线缆,
   机械手可以无限旋转, 规划器不再需要角度限制。
3. **转动部分又短又轻**: 转动的只有转盘上半、两块侧板、两根夹指架、两片夹指、两根连杆和推杆,
   从转盘端面到魔方表面只有 13 个孔距 (约 52mm, v2 约 144mm), 没有舵机和马达。
4. **马达经齿轮带动转盘外圈** (36 齿 : 60 齿, 减速 1.67 倍): 马达偏到侧面, 让出轴线给推杆;
   输出轴不承受机械臂的重量; 扭矩放大 1.67 倍, 马达自身的回差和编码器分辨率在机械手上都缩小 1.67 倍。
5. **四个一样的模块**, 放在 R / L / F / B 四个方向, 底座连成一个整体。

模块坐标 (LDU, LDraw 约定 -Y 向上, 1 孔距 = 20 LDU = 8mm): 魔方中心在原点, 这个模块从 -X 方向夹住 L 面,
轴线就是 X 轴。其他三个模块由它绕 Y 轴转 90° / 180° / 270° 得到。桌面在 y = 270。
下面的尺寸常数是模块自身的坐标, 最后整体往魔方方向挪 MODULE_DX = 10 (半个孔距): 这样竖墙落在 x = -240 的整孔位上,
四个模块转 90° 之后孔位仍然对得上, 底座才能用同一套 7x5 框架把它们连成一体 (墙在 -250 时, 相邻模块的孔位差半个孔距)。

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
# 7x5 框架: 局部 x 为 5 孔方向, 局部 z 为 7 孔方向, 局部 y 为厚度 (正面孔)
FRAME_YZ_LONG_Z = orient("+y", "-x")  # 竖放在 YZ 平面, 长边沿 Z
FRAME_YZ_LONG_Y = orient("+z", "+x")  # 竖放在 YZ 平面, 长边沿 Y
FRAME_XY_LONG_X = orient("+y", "+z")  # 竖放在 XY 平面, 长边沿 X
FRAME_XY_LONG_Y_5X = orient("+x", "+z")  # 竖放在 XY 平面, 长边沿 Y
FRAME_XZ_LONG_X = orient("-z", "+y")  # 水平放, 长边沿 X
FRAME_XZ_LONG_Z = orient("+x", "+y")  # 水平放, 长边沿 Z
BUSH_X = orient("-z", "+y")  # 轴套 (局部 z 为轴线)
BUSH_Z = I
# 转盘: 局部 y 为转轴, 耳朵在局部 ±x。转轴沿世界 X, 耳朵在 ±Z 两侧 (销孔沿 Z); 上半 (转动) 朝 +X。
TT_ROT = orient("+z", "-x")
# 36 齿齿轮: 局部 z 为转轴
GEAR_X = orient("+y", "+z")
# 马达: 输出轴 (局部 x) 沿 +X, 本体 (局部 -z) 朝下, 高的一侧 (局部 -y) 朝 -Z (背离魔方中心那一侧)
MOTOR_ROT = orient("+x", "+z", "-y")
# 舵机: 输出轴 (局部 -y) 朝 -Z, 长度方向 (局部 x) 沿 -X (输出轴偏在本体前半), 耳朵销孔 (局部 z) 竖直
SERVO_ROT = orient("-x", "+z", "+y")
# 十字接头 32039: 十字孔 (局部 z) 沿 -X 朝后接推杆, 前端圆孔 (局部 x) 沿 Z
CROSSHEAD_ROT = orient("+z", "+y", "-x")
# 十字块 6536: 圆孔 (局部 z) 沿 X 套在推杆上, 十字孔 (局部 x) 沿 Z, 十字孔在圆孔下方 20 (局部 y 朝 -Y)
BLOCK_ROT = orient("+z", "-y", "+x")

# ---- 零件目录 -----------------------------------------------------------------

CATALOG = {
    "95658.dat": ("EV3 大马达", "solid"),
    "geekservo.dat": ("Geekservo 舵机 (灰色, 270°)", "solid"),
    "18938.dat": ("60 齿转盘 上半", "solid"),
    "18939.dat": ("60 齿转盘 下半", "solid"),
    "32498.dat": ("36 齿双面锥齿轮", "solid"),
    "64179.dat": ("7x5 框架", "solid"),
    "40490.dat": ("9 孔粗梁", "solid"),
    "32524.dat": ("7 孔粗梁", "solid"),
    "32316.dat": ("5 孔粗梁", "solid"),
    "32278.dat": ("15 孔粗梁", "solid"),
    "41677.dat": ("2 孔细梁 (两端十字孔)", "solid"),
    "32039.dat": ("十字轴接头 (带圆孔)", "solid"),
    "6536.dat": ("十字块 1x2 (十字孔 + 圆孔)", "solid"),
    "2780.dat": ("摩擦销 (2 孔长)", "pin"),
    "3673.dat": ("无摩擦销 (2 孔长, 灰色)", "pin"),
    "32556a.dat": ("无摩擦长销 (3 孔长, 米色)", "pin"),
    "6558.dat": ("长摩擦销 (3 孔长)", "pin"),
    "32054.dat": ("带挡套长销 (3 孔长, 红色)", "pin"),
    "3749.dat": ("轴销 (半销半轴, 米色)", "pin"),
    "32062.dat": ("2 号轴", "axle"),
    "32073.dat": ("5 号轴", "axle"),
    "44294.dat": ("7 号轴", "axle"),
    "3708.dat": ("12 号轴", "axle"),
    "3713.dat": ("轴套", "bush"),
    "32123a.dat": ("半轴套", "bush"),
    "cube56.dat": ("56mm 魔方 (示意)", "other"),
}
# 检查用的销/轴长度 (LDU), 补到 check.CONNECTOR_LEN 里
CONNECTOR_LEN = {"3673.dat": 40, "32556a.dat": 60, "3749.dat": 40, "32062.dat": 40, "32073.dat": 100,
                 "44294.dat": 140}

C_FRAME = 71  # 浅灰
C_BASE = 72  # 深灰: 底座
C_BEAM = 0  # 黑
C_JAW = 4  # 红: 夹指
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
TABLE_Y = 270.0
MODULE_DX = 10.0  # 模块整体往魔方方向挪半个孔距 (见文件开头)

# 夹指 (7 孔粗梁, 孔沿 Z): 孔在 x = -170 ... -50, 前端圆头到 x = -40
JAW_Y = 80.0  # 夹指中心线离轴线的距离; 内侧面在 71 (间距 56.8mm, 同 v1)
PIVOT_X = -130.0  # 夹指转轴 (夹指从前数第 5 个孔)
JOINT_X = -150.0  # 夹指上接连杆的孔 (第 6 个孔), 在转轴后面 20
JAW_A = PIVOT_X - JOINT_X  # 20
LINK_L = 80.0  # 连杆 = 5 孔粗梁两端孔距
CROSS_CLOSED_X = JOINT_X  # 夹紧时十字接头的销正好在两个连杆孔的连线上 (连杆垂直于轴线 = 死点)
JAW_TIP_X = -40.0

# 推杆 (16 号轴): 前端插进十字接头 32039 的十字孔
ROD_FRONT_IN = 10.0  # 插进十字孔的深度

# 舵机 (固定在底座平台上): 输出轴沿 Z, 在十字块后面; 夹紧时曲柄和连杆拉成一条直线 (死点)
SERVO_C = np.array([-450.0, 30.0, 80.0])  # 舵机本体中心
CRANK_C = np.array([-460.0, 30.0])  # 输出轴 (x, y)
CRANK_R = 20.0
LINK2_L = 80.0  # 舵机连杆 = 5 孔粗梁
BLOCK_Y = 20.0  # 十字块上连杆轴的高度 (推杆在 y = 0)


def jaw_beta(s):
    """十字接头从死点后退 s 时, 夹指张开的角度 (弧度)。"""
    lo, hi = 0.0, math.radians(60)
    xc = CROSS_CLOSED_X - s
    for _ in range(60):
        b = (lo + hi) / 2
        jx = PIVOT_X - JAW_A * math.cos(b)
        jy = JAW_Y - JAW_A * math.sin(b)
        d = math.hypot(jx - xc, jy)
        # b 越大, J 越往里, 离十字接头越近
        if d > LINK_L:
            lo = b
        else:
            hi = b
    return (lo + hi) / 2


def servo_theta_for(s):
    """推杆从夹紧位置后退 s 时曲柄的角度 (相对 +X, 向上为负) 和夹紧时十字块连杆轴的 x。"""

    def rod_x(th):
        p = CRANK_C + CRANK_R * np.array([math.cos(th), math.sin(th)])
        return p[0] + math.sqrt(LINK2_L ** 2 - (p[1] - BLOCK_Y) ** 2)

    th0 = -math.atan2(CRANK_C[1] - BLOCK_Y, math.sqrt((LINK2_L + CRANK_R) ** 2 - (CRANK_C[1] - BLOCK_Y) ** 2))
    x0 = rod_x(th0)
    if s <= 0:
        return th0, x0
    lo, hi = th0 - math.pi, th0
    for _ in range(60):
        m = (lo + hi) / 2
        if x0 - rod_x(m) > s:
            lo = m
        else:
            hi = m
    return (lo + hi) / 2, x0


OPEN_S = 30.0  # 松开时推杆后退的距离 (夹指张开约 18°; 见 README "夹指张开量")
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
    """一个机械手模块 (模块坐标)。open_s: 推杆从夹紧死点后退的距离; angle: 机械手转过的角度 (度),
    0 表示夹指在竖直平面 (夹指一上一下)。steps=False 时不登记搭建步骤 (其余三个模块)。
    on_base=True 时加上马达固定板和底座之间的销 (单独检查模块时没有底座, 不加)。"""
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
    # 凸台两头的销孔不用: 框架把凸台四面围住, 摩擦销中间有挡环, 从外面只能插进一半 (用户实物反馈, 2026-09-29)。
    # 凸台卡在开口里, 上下左右和转动都被框架挡住; 圆盘的边沿贴住框架正面, 背面用两根 7 孔粗梁压住, 前后也固定了。
    s = st("转盘下半", "60 齿转盘的下半 (没有齿): 底部的长方形凸台从正面 (朝魔方的一面) 塞进最上面那块框架的开口, "
           "长边沿框架的长边, 圆盘的边沿贴住框架正面。凸台两头的销孔不用插销。", sub="竖墙", view=(60, 20))
    add("18939.dat", C_TT, TT_C, TT_ROT, s)
    s = st("压住转盘", "在墙的背面, 两根 5 孔粗梁竖着贴在转盘凸台背面, 推杆位置左右各一根 (中间留出推杆)。"
           "每根两端各用 1 个摩擦销插进框架长边上的正面孔: 先把销插进框架, 再把梁压上去。转盘下半这样就前后都卡住了。",
           sub="竖墙", view=(240, 20))
    for sz in (1, -1):
        add("32316.dat", C_BEAM, (WALL_X - 20, 0, 20 * sz), orient("+z", "+x", "+y"), s)
        for sy in (1, -1):
            add("2780.dat", C_PIN, (WALL_X - 10, 40 * sy, 20 * sz), ALONG_X, s)

    # ================= 2. 马达 =================
    # 马达偏在 -Z 一侧, 输出轴和转盘轴线相距 120 (= 36 齿和 60 齿的节圆半径之和), 本体朝下。
    mpos = np.array([-310.0, 0.0, -120.0])

    def madd(name, color, lpos, lrot, s, note=""):
        return add(name, color, MOTOR_ROT @ np.asarray(lpos, float) + mpos, MOTOR_ROT @ lrot, s, note=note)

    s = st("马达固定板", "7x5 框架插进马达尾部两片耳朵之间的缝里, 两根红色带挡套长销从同一侧穿过耳朵和框架 "
           "(TRACK3R 的做法)。", sub="马达", view=(60, -20))
    add("95658.dat", C_MOTOR, mpos, MOTOR_ROT, s)
    madd("64179.dat", C_FRAME, (0, 40, -200), FRAME_YZ_LONG_Z, s)
    for z in (-180, -140):
        madd("32054.dat", C_SPIN, (-20, 0, z), ALONG_X, s)
    s = st("马达前板", "另一块 7x5 框架竖着贴在马达靠输出盘的那一端 (长边竖直), 2 个摩擦销插进马达侧面靠近输出盘的两个孔 "
           "(这两个孔是不是通孔要按实物确认, 见说明书末尾)。",
           sub="马达", view=(60, 20))
    add("64179.dat", C_FRAME, (WALL_X, 100, -220), FRAME_YZ_LONG_Y, s)
    for y in (40, 80):
        add("2780.dat", C_PIN, (WALL_X - 10, y, -180), ALONG_X, s)
    s = st("齿轮", "7 号轴插进马达输出盘中间的十字孔, 依次套上半轴套、轴套、36 齿齿轮, 最前面再套一个半轴套。",
           sub="马达", view=(60, 20))
    add("44294.dat", C_AXLE, (-275, 0, -120), ALONG_X, s)
    add("32123a.dat", C_BUSH, (-270, 0, -120), BUSH_X, s)
    add("3713.dat", C_BUSH, (-255, 0, -120), BUSH_X, s)
    add("32498.dat", C_GEAR, (-235, 0, -120), GEAR_X, s)
    add("32123a.dat", C_BUSH, (-220, 0, -120), BUSH_X, s)
    if on_base:
        s = st("装竖墙", "做好的竖墙立在底座这一排的第 2 块框架上, 墙面朝魔方。2 个摩擦销竖着从墙底边的侧孔插进底座框架。",
               attach=("底座", "竖墙"), view=(40, 35))
        for z in (-40, 40):
            add("2780.dat", C_PIN, (WALL_X, BASE_Y - 20, z), ALONG_Y, s)
    # 马达前板和墙之间: 一块 7x5 框架横着接在两者之间 (共面, 长边对短边), 避开齿轮
    s = st("装马达", "马达组件放到竖墙旁边, 36 齿齿轮和转盘上半的齿啮合 (两轴相距 3 个孔 = 两个节圆半径之和)。"
           "再用一块 7x5 框架接在马达前板和竖墙之间, 4 个摩擦销穿侧孔连起来。"
           + ("最后 1 个摩擦销把马达固定板的底边和底座连起来。" if on_base else ""), attach=("马达",), view=(60, 20))
    add("64179.dat", C_FRAME, (WALL_X, 140, -120), FRAME_YZ_LONG_Y, s)
    for y in (100, 140):
        add("2780.dat", C_PIN, (WALL_X, y, -170), ALONG_Z, s)
    for y in (100, 180):
        add("2780.dat", C_PIN, (WALL_X, y, -70), ALONG_Z, s)
    if on_base:  # 马达尾部的固定板落在底座上
        add("2780.dat", C_PIN, (-300, TABLE_Y - 10, -120), ALONG_X, s)

    # ================= 3. 舵机平台和推杆导向 =================
    s = st("舵机平台", "两块 7x5 框架平放, 短边对短边, 3 个摩擦销沿长度方向连成一条平台。平台后端下面竖着上下拼两块框架当支腿 "
           "(立在桌面上)。平台前半段上面竖立一块框架当推杆导向: 它长边沿推杆方向, 底边用 3 个摩擦销竖着插进平台; "
           "两条短边上正中的侧孔 (圆孔) 就是推杆的两个轴承。", sub="平台", view=(30, 40))
    for xc in (-330, -470):
        add("64179.dat", C_FRAME, (xc, 60, 40), FRAME_XZ_LONG_X, s)
    for z in (20, 40, 60):
        add("2780.dat", C_PIN, (-400, 60, z), ALONG_X, s)
    for yc in (120, 220):
        add("64179.dat", C_FRAME, (-530, yc, 40), FRAME_YZ_LONG_Z, s)
    for z in (0, 80):
        add("2780.dat", C_PIN, (-530, 70, z), ALONG_Y, s)
    for z in (0, 40, 80):
        add("2780.dat", C_PIN, (-530, 170, z), ALONG_Y, s)
    gf_c = np.array([-350.0, 0.0, 0.0])
    add("64179.dat", C_FRAME, gf_c, FRAME_XY_LONG_X, s)
    for x in (-390, -350, -310):
        add("2780.dat", C_PIN, (x, 50, 0), ALONG_Y, s)
    s = st("舵机", "舵机平放在平台后端, 输出轴朝推杆那一侧。2 根蓝色长摩擦销从上面插进舵机两只耳朵, "
           "1 孔长的那段朝下插进平台框架。", sub="平台", view=(30, 40))
    add("geekservo.dat", C_SERVO, SERVO_C, SERVO_ROT, s)
    for dx in (-40, 40):
        add("6558.dat", C_LPIN, (SERVO_C[0] + dx, 40, SERVO_C[2]), LPIN_SHORT_Y, s)
    s = st("装平台", "平台前端顶住竖墙背面, 2 个摩擦销沿推杆方向穿进墙的孔。检查导向框架的两个轴承孔、转盘中孔在一条直线上。",
           attach=("平台",), view=(30, 40))
    for z in (20, 60):
        add("2780.dat", C_PIN, (WALL_X - 10, 60, z), ALONG_X, s)

    # 推杆 + 曲柄滑块 (舵机侧)
    th, x0 = servo_theta_for(open_s)
    crank_pin = CRANK_C + CRANK_R * np.array([math.cos(th), math.sin(th)])
    bx = crank_pin[0] + math.sqrt(LINK2_L ** 2 - (crank_pin[1] - BLOCK_Y) ** 2)  # 十字块上连杆轴的 x
    s = st("十字块和舵机连杆", "十字块 (圆孔在上) 两边各贴一个半轴套, 放进导向框架的开口里, 圆孔对准两个轴承孔 "
           "(推杆最后从前面穿进来)。2 号轴插进十字块下面的十字孔, 黄色 5 孔连杆的一端套在 2 号轴上。"
           "先让舵机转到 \"夹紧\" 角度, 再把曲柄 (2 孔细梁) 的十字孔套到舵机输出轴上, 让曲柄指向十字块、和连杆拉成一条直线 "
           "(死点); 最后用一根 2 号轴穿过连杆另一端的圆孔, 插进曲柄另一头的十字孔。", view=(30, 30))
    add("6536.dat", C_BEAM, (bx, BLOCK_Y, 0), BLOCK_ROT, s)
    for dx in (-15, 15):
        add("32123a.dat", C_BUSH, (bx + dx, 0, 0), BUSH_X, s)
    add("32062.dat", C_AXLE, (bx, BLOCK_Y, 10), ALONG_Z, s)
    cdir = np.array([math.cos(th), math.sin(th), 0.0])
    add("41677.dat", C_BEAM, (CRANK_C[0], CRANK_C[1], 35), orient(np.cross([0, 0, 1.0], cdir), "+z", cdir), s)
    # 曲柄 (十字孔) 和连杆 (圆孔) 之间用 2 号轴: 轴卡在曲柄里, 连杆绕轴转
    add("32062.dat", C_AXLE, (crank_pin[0], crank_pin[1], 20), ALONG_Z, s)
    e = np.array([crank_pin[0] - bx, crank_pin[1] - BLOCK_Y, 0.0])
    e /= np.linalg.norm(e)
    mid = (np.array([bx, BLOCK_Y]) + crank_pin) / 2
    add("32316.dat", C_LINK, (mid[0], mid[1], 20), orient(np.cross([0, 0, 1.0], e), "+z", e), s)

    # ================= 4. 转动部分 (机械头) =================
    xc = CROSS_CLOSED_X - open_s  # 十字接头上销的 x
    beta = jaw_beta(open_s)
    head = []

    def hadd(name, color, pos, rot, s, note=""):
        p = add(name, color, pos, rot, s, head=True, note=note)
        head.append(p)
        return p

    # 转盘上半是机械头的底座: 先把销插进它两头的孔, 再从两侧把侧板压上去 (侧板装上以后两块就连成一体了, 那时再插不进去)
    s = st("侧板与夹指架", "两块 7x5 框架竖放 (5 孔方向沿推杆), 各在内侧贴一根 9 孔粗梁 (竖直), 每根用 4 个摩擦销连起来。"
           "粗梁贴在框架靠魔方的那条短边上, 它上下两端的孔就是夹指的转轴孔。这样做两套, 左右对称。",
           sub="机械头", view=(40, 25))
    for sz in (1, -1):
        hadd("64179.dat", C_FRAME, (-170, 0, 60 * sz), FRAME_XY_LONG_Y_5X, s)
        hadd("40490.dat", C_BEAM, (PIVOT_X, 0, 40 * sz), BEAM_Y_HOLES_Z, s)
        for y in (-60, -20, 20, 60):
            hadd("2780.dat", C_PIN, (PIVOT_X, y, 50 * sz), ALONG_Z, s)
    s = st("转盘上半", "60 齿转盘的上半 (有齿): 先在底部凸台两头各插 2 个摩擦销 (上下两个孔, 挡环贴住凸台端面), "
           "有齿的一面朝后。再把两套侧板从左右两边压到销上, 侧板后端的孔对准销, 粗梁在内侧朝魔方。",
           sub="机械头", view=(40, 25))
    hadd("18938.dat", C_TT, TT_C, TT_ROT, s)
    for sz in (1, -1):
        for y in (-20, 20):
            hadd("2780.dat", C_PIN, (-210, y, 50 * sz), ALONG_Z, s)
    s = st("夹指", "两根红色 7 孔粗梁当夹指, 一上一下。每根从前数第 5 个孔套在一根 5 号轴上, "
           "5 号轴两端穿过两根 9 孔粗梁最外面的孔, 夹指两侧各套一个轴套定位。夹指应能绕 5 号轴自由摆动。",
           sub="机械头", view=(40, 25))
    for sy in (1, -1):
        piv = np.array([PIVOT_X, JAW_Y * sy, 0.0])
        R = rot_z(beta * sy)
        hadd("32524.dat", C_JAW, piv + R @ (np.array([-110.0, JAW_Y * sy, 0]) - piv), R @ BEAM_X_HOLES_Z, s)
        hadd("32073.dat", C_AXLE, piv, ALONG_Z, s)
        for z in (-20, 20):
            hadd("3713.dat", C_BUSH, piv + [0, 0, z], BUSH_Z, s)
    s = st("连杆与十字接头", "十字接头的圆孔里穿一根米色无摩擦长销, 两根黄色 5 孔连杆一上一下套在长销两端; "
           "连杆另一端各用一个灰色无摩擦销接到夹指从前数第 6 个孔。十字接头往前推时连杆把夹指根部往外撑, 夹指前端合拢; "
           "推到两根连杆和推杆垂直时就是死点, 魔方把夹指往外推的力传不回推杆。", sub="机械头", view=(40, 25))
    hadd("32039.dat", C_BEAM, (xc - 20, 0, 0), CROSSHEAD_ROT, s)
    hadd("32556a.dat", C_TPIN, (xc, 0, 0), ALONG_Z, s)
    for sy in (1, -1):
        piv = np.array([PIVOT_X, JAW_Y * sy, 0.0])
        R = rot_z(beta * sy)
        j = piv + R @ (np.array([JOINT_X, JAW_Y * sy, 0]) - piv)
        c = np.array([xc, 0.0, 0.0])
        d = (j - c) / np.linalg.norm(j - c)
        zl = 20.0 * sy
        hadd("32316.dat", C_LINK, (c + j) / 2 + [0, 0, zl], orient(np.cross([0, 0, 1.0], d), "+z", d), s)
        hadd("3673.dat", C_FPIN, j + [0, 0, 10 * sy], ALONG_Z, s)
    s = st("推杆", "12 号轴插进十字接头后端的十字孔。", sub="机械头", view=(40, 25))
    rod_front = xc - 30 + ROD_FRONT_IN
    hadd("3708.dat", C_ROD, (rod_front - 120, 0, 0), ALONG_X, s)
    st("装机械头", "推杆从转盘下半的中孔往后穿, 依次穿过导向框架前面的轴承孔、半轴套、十字块、半轴套、后面的轴承孔。"
       "转盘上半对准下半扣上 (两半本身卡在一起, 不用销)。最后把两个半轴套推到贴住十字块, "
       "让十字块和推杆一起前后移动。", attach=("机械头",), view=(40, 25), focus="module")

    if angle:
        R = rot_x(angle)
        for p in head:
            p.pos = R @ p.pos
            p.rot = R @ p.rot
    for p in parts:
        p.pos = p.pos + [MODULE_DX, 0, 0]
    return parts


# ---- 底座: 16 块 7x5 框架拼成风车形的方框 -------------------------------------------
# 每个方向一排 4 块框架 (长边沿 X, 沿 Z 方向长边对长边拼接), 四排绕中心转 90° 首尾相接:
# 一排的最后一块用短边顶住下一排第一块的长边, 2 个摩擦销穿侧孔。竖墙压在每排的第 2 块上。
BASE_CX = -220.0
BASE_CZ = (-100.0, 0.0, 100.0, 200.0)
BASE_Y = TABLE_Y - 10


def base_blade(s, seam=True):
    """L 一侧的一排 (世界坐标, 其余三排由它转出)。seam=False: 不插和下一排之间的销。
    四排围成一圈, 最后一条缝的两边已经分别连在别的排上, 两组销方向垂直, 带挡环的销插不进去, 所以最后一条缝不插销。"""
    out = []
    for cz in BASE_CZ:
        out.append(Part("64179.dat", C_BASE, (BASE_CX, BASE_Y, cz), FRAME_XZ_LONG_X, s))
    for cz in BASE_CZ[:-1]:
        for dx in (-40, 0, 40):
            out.append(Part("2780.dat", C_PIN, (BASE_CX + dx, BASE_Y, cz + 50), ALONG_Z, s))
    # 和下一排 (F 一侧) 的接缝: 本排最后一块的短边 (x = -150) 对下一排第一块的长边
    if seam:
        for z in (180, 220):
            out.append(Part("2780.dat", C_PIN, (BASE_CX + 70, BASE_Y, z), ALONG_X, s))
    return out


def build(state=None, with_cube=True):
    """整机 (世界坐标)。state: {位置: (open_s, angle)}, 缺省为全部夹紧、夹指竖直。
    搭建步骤按 L 模块登记; 其余三个模块在 "装另外三个机械手" 那一步整体出现。"""
    STEPS.clear()
    state = state or {}
    parts = []
    s = step("底座", "16 块 7x5 框架平放, 拼成风车形的方框: 每一排 4 块长边对长边, 每条缝 3 个摩擦销; "
             "一排的最后一块用短边顶住下一排第一块的长边, 2 个摩擦销。四排绕中心转 90° 首尾相接, 中间留出放魔方的空间。"
             "最后合拢的那条缝不插销 (两边已经各自连成一体, 销插不进去), 只是顶住; 其余三条缝已经让底座连成一个整体。", sub="底座", view=(35, 60))
    for arm in ARMS:
        for p in base_blade(s, seam=(arm != ARMS[-1])):
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
