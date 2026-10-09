"""生成原 R 单臂 / 条件式 R+L 直连接线图。运行：python3 docs/wiring/direct_wiring.py。"""
from pathlib import Path
from html import escape
import json
import spec

HERE = Path(__file__).resolve().parent
COLORS = {"power": "#cf421f", "ground": "#344454", "control": "#167f74",
          "encoder": "#236ac2", "motor": "#8842ac", "servo": "#ad7418"}
P = {}
PARTS = []
WIRES = []
ROWS = {"+": 485, "-": 510, "a": 550, "b": 575, "c": 600,
        "d": 625, "e": 650, "f": 710, "g": 735, "h": 760,
        "i": 785, "j": 810, "G": 880}


def rect(x, y, w, h, fill, stroke="#ccd2d4", r=8):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}"/>'


def text(x, y, s, size=17, fill="#243545", anchor="start", bold=False):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{700 if bold else 400}">{escape(str(s))}</text>')


def path(points, color, width=4):
    d = "M" + " L".join(f"{x},{y}" for x, y in points)
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"/>'


def dot(x, y, color, r=5):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}" stroke="white" stroke-width="1.5"/>'


def pin(name, x, y):
    P[name] = (x, y)


def wire(code, group, start, end, bends=(), note=""):
    WIRES.append(dict(code=code, group=group, start=start, end=end, bends=list(bends), note=note))


def make_parts():
    PARTS.extend([rect(20, 105, 1760, 265, "#f5f3ec"),
                  text(40, 132, "① 电源区", 20, bold=True),
                  rect(45, 167, 210, 146, "#fff"),
                  rect(69, 196, 78, 70, "#26323b", "#172028"),
                  '<circle cx="108" cy="231" r="24" fill="#111" stroke="#a3a9ac" stroke-width="5"/>',
                  '<circle cx="108" cy="231" r="5" fill="#c4c8cb"/>',
                  text(161, 208, "DC-005", 18, bold=True),
                  text(161, 234, "+9V", 18, COLORS["power"]),
                  text(161, 274, "GND", 18),
                  text(60, 295, "现有 9V 电源 / 开关后", 15)])
    pin("DC.+9V", 245, 230)
    pin("DC.GND", 245, 270)
    PARTS.extend([text(350, 244, "DC-005 正极焊两根线", 21, bold=True),
                  text(350, 275, "分别接 VM 与降压 IN+", 19),
                  text(350, 305, "焊点绝缘；模块端保持可拔", 17)])
    PARTS.extend([rect(680, 161, 260, 155, "#24678b", "#19445b"),
                  rect(758, 190, 74, 74, "#333c45", "#20272d"),
                  text(795, 233, "电感", 16, "white", "middle"),
                  rect(847, 182, 43, 36, "#2683d0", "#123f71"),
                  text(809, 292, "降压模块 · 输出调为 5.0V", 17, "white", "middle")])
    for name, x, y, anchor in [("IN+", 680, 190, "start"), ("IN−", 680, 290, "start"),
                                ("OUT+", 940, 190, "end"), ("OUT−", 940, 290, "end")]:
        pin("BUCK."+name, x, y)
        PARTS.append(dot(x, y, "#dfc773", 7))
        PARTS.append(text(x+(12 if anchor=="start" else -12), y-10, name, 15, "white", anchor))
    PARTS.extend([text(985, 275, "OUT− 直连舵机地", 18, bold=True),
                  text(985, 318, "先确认与 IN− 内部共地", 16)])
    PARTS.extend([text(1260, 200, "9V 总电源必须开：降压模块才有 5V", 21, bold=True),
                  text(1260, 230, "Pico 由 USB 供电；5V 轨不接 Pico 供电脚。", 17),
                  text(1260, 260, "DC-005 焊脚、降压焊盘均按实物标识确认。", 17),
                  text(1260, 288, "图示为功能位置，不是这两种元件的焊脚模板。", 16),
                  text(1260, 316, "马达、编码器、舵机一次接齐。", 17, bold=True)])
    # 驱动模块独立放置，底部公针直接插母头线；不通过面包板弹片。
    PARTS.extend([text(230, 463, "② DRV8833 · 正面朝上", 23, bold=True),
                  text(230, 493, "放在绝缘面，母头线接模块排针", 17),
                  text(230, 521, "动力线端需满足马达启动电流", 16),
                  rect(230, 586, 260, 420, "#266d98", "#154867"),
                  rect(322, 716, 76, 128, "#27303a", "#17212c"),
                  text(361, 787, "DRV", 20, "white", "middle", True),
                  text(361, 815, "8833", 20, "white", "middle", True),
                  text(361, 871, "三个 GND", 14, "#dbeef9", "middle"),
                  text(361, 895, "模块内部相通", 14, "#dbeef9", "middle")])
    left = [name + {1: "-L", 2: "-L1", 7: "-L2"}.get(i, "")
            for i, name in enumerate(spec.DRV_LEFT)]
    right = [name + {0: "-R1", 6: "-R2", 7: "-R"}.get(i, "")
             for i, name in enumerate(spec.DRV_RIGHT)]
    for side, x, names in [("left", 240, left), ("right", 480, right)]:
        for i, name in enumerate(names):
            y = 620+i*50
            pin("DRV."+name, x, y)
            PARTS.append(rect(x-7, y-7, 14, 14, "#dac267", "#af9133", 1))
            label = name.split("-")[0]
            PARTS.append(text(x+(17 if side=="left" else -17), y+5, label, 17,
                              "white", "start" if side=="left" else "end", True))
    # 面包板：Pico 使用 c3…c22 / h3…h22 坐标。
    PARTS.extend([text(910, 417, "③ 面包板 · USB 朝左 · 仅放低电流线路", 23, bold=True),
                  rect(650, 435, 1080, 465, "#eeeae1", "#c4c0b8"),
                  rect(661, 664, 1058, 31, "#d1cbc0", "#d1cbc0", 2)])
    for row, y in ROWS.items():
        label = {"+": "+5V", "-": "GND", "G": "GND"}.get(row, row)
        PARTS.append(text(675, y+5, label, 13, anchor="end"))
        if row in "+-G":
            color = "#c74832" if row=="+" else "#596974"
            for lo, hi in [(1,20),(21,40)]:
                PARTS.append(path([(690+(lo-1)*25, y-10), (690+(hi-1)*25, y-10)], color, 2))
        for c in range(1,41):
            x = 690+(c-1)*25
            pin(f"BB.{row}{c}", x, y)
            PARTS.append(rect(x-3, y-3, 6, 6, "#77766f", "none", 1))
    for c in range(1,41):
        PARTS.append(text(690+(c-1)*25, 458, c, 12, anchor="middle"))
    PARTS.extend([rect(728, 589, 500, 182, "#26744f", "#164d32"),
                  rect(700, 650, 42, 58, "#b5bdc5", "#57636d", 3),
                  rect(908, 639, 72, 72, "#26303b", "#17212b", 3),
                  text(1085, 670, "Raspberry Pi Pico", 21, "white", "middle", True),
                  text(1085, 704, "USB 独立供电", 17, "white", "middle"),
                  text(721, 735, "USB", 13, "#142d36", "end")])
    for c in range(3,23):
        for row in ["c", "h"]:
            PARTS.append(dot(*P[f"BB.{row}{c}"], "#d8c074", 5))
    for c, row, name in [(5,"c","GND"),(7,"c","3V3"),(6,"h","GP2"),(7,"h","GP3"),
                         (8,"h","GP4"),(9,"h","GP5"),(13,"h","GP8")]:
        x,y=P[f"BB.{row}{c}"]
        PARTS.append(text(x, y+(23 if row=="c" else -16), name, 12, "white", "middle", True))
    PARTS.append(text(1020, 856, "同一数字列：a–e 相通；f–j 相通；中槽两侧不通", 15, anchor="middle"))
    # 六根引出线进入独立夹线连接器，不直接把散铜插入面包板。
    PARTS.extend([rect(45, 1090, 405, 130, "#fff", "#c7cdd0"),
                  rect(125, 1235, 242, 119, "#e0e2e5", "#7e8994", 12),
                  rect(295, 1260, 100, 70, "#ba252f", "#8b1d29", 7),
                  '<circle cx="345" cy="1295" r="22" fill="#656971" stroke="#393f44" stroke-width="3"/>',
                  text(143, 1280, "④ EV3 马达", 23, bold=True),
                  text(143, 1313, "原 EV3 插头插马达", 16),
                  path([(247,1235),(247,1212)], "#303b46", 12)])
    for i, (color, label) in enumerate([("#ececec","白 M1"),("#222","黑 M2"),("#c22","红 GND"),
                                        ("#2a944e","绿 5V"),("#dda814","黄 A"),("#206bcc","蓝 B")],1):
        x = 100+i*50
        pin(f"EV3.{i}", x, 1110)
        PARTS.extend([rect(x-16,1094,32,31,"#555d65","#313a43",2),
                      dot(x,1110,"#cfd4d5",7),path([(x,1127),(x,1198),(247,1212)],color,4),
                      text(x,1148,i,14,anchor="middle",bold=True),
                      text(x,1171,label,12,anchor="middle")])
    PARTS.extend([text(490, 1147, "加工线 → 独立夹线端子 → 带插头的引出线", 19, bold=True),
                  text(490, 1180, "六个端子互不相通；不能用同一组分线器接六根线。", 17),
                  text(50, 1390, "线色仅作已有线束参考；以已确认的 EV3 触点编号为准。", 17),
                  text(650, 1228, "两路分压：10kΩ 串联，20kΩ 从 GPIO 接点接地", 23, bold=True),
                  text(650, 1261, "A：h33 → 10kΩ → 第26列分压点 → GP4", 20, COLORS["encoder"]),
                  text(650, 1295, "B：h31 → 10kΩ → 第28列分压点 → GP5", 20, COLORS["encoder"]),
                  text(650, 1330, "供电、信号都使用带插头的线；裸绞线先接夹线端子。", 18),
                  text(650, 1363, "粗线为板外动力连接；交叉无圆点不相连。", 18),
                  text(650, 1395, "图内只画面包板前40列；字母 / 数字以本图坐标为准。", 17)])

    PARTS.extend([text(1870, 550, "⑤ Geekservo · 灰色 270°", 22, bold=True),
                  rect(1890, 600, 270, 230, "#d9dcdf", "#73818c"),
                  rect(2105, 670, 70, 80, "#697784", "#374653"),
                  text(1908, 650, "红 · +5V", 20, COLORS["power"]),
                  text(1908, 700, "棕 · GND", 20, COLORS["ground"]),
                  text(1908, 750, "黄 · 信号", 20, COLORS["servo"]),
                  text(1870, 880, "S01：OUT+ → 舵机 +5V", 18),
                  text(1870, 912, "S02：OUT− → 舵机 GND", 18),
                  text(1870, 944, "S03：j13 / GP8 → 信号", 18),
                  text(1870, 992, "电源直接接降压模块", 20, bold=True),
                  text(1870, 1024, "信号接面包板；线序按实物确认", 16),
                  text(1870, 1056, "三孔母插头配公针线端", 17)])
    for name, y in [("V+", 650), ("GND", 700), ("SIG", 750)]:
        pin("SERVO." + name, 1890, y)


def make_wires():
    wire("P03","power","DC.+9V","BUCK.IN+",[(300,230),(300,190)],"DC 正极第一根线 → 降压 IN+")
    wire("P04","ground","DC.GND","BUCK.IN−",[(285,270),(285,340),(650,340),(650,290)],"DC 负极 → 降压 IN−（独立回流）")
    wire("P07","power","DC.+9V","DRV.VM",[(270,230),(270,380),(120,380),(120,620)],"DC 正极第二根线 → 驱动 VM（直接线）")
    wire("P08","ground","DC.GND","DRV.GND-L1",[(260,270),(260,410),(180,410),(180,720)],"DC 负极 → 驱动左排第3脚 GND（直接线）")
    wire("P09","power","BUCK.OUT+","BB.+38",[(1040,190),(1040,147),(1735,147),(1735,450),(1615,450)],"降压 OUT+ 直接接面包板上 + 第38孔")
    wire("P10","ground","DRV.GND-R","BB.-38",[(520,970),(520,360),(1770,360),(1770,510)],"驱动右排第8脚 GND → 面包板上 − 第38孔")
    wire("G01","ground","BB.a5","BB.-5",[],"Pico GND：a5 → 上 − 第5孔")
    wire("G02","ground","BB.-40","BB.G40",[(1745,510),(1745,880)],"上下地轨相连")
    for code,row in [("G03","-"),("G04","G"),("P11","+")]:
        x,y=P[f"BB.{row}20"]
        wire(code,"power" if row=="+" else "ground",f"BB.{row}20",f"BB.{row}21",[(x,y-17),(x+25,y-17)],"跨接该电源轨中间断口（有断口时）")
    wire("C01","control","BB.j6","DRV.AIN1",[(815,926),(580,926),(580,720)],"GP2 / 物理4脚：j6 → AIN1")
    wire("C02","control","BB.j7","DRV.AIN2",[(840,951),(555,951),(555,670)],"GP3 / 物理5脚：j7 → AIN2")
    wire("C03","control","BB.a7","DRV.STBY",[(840,390),(600,390),(600,770)],"Pico 3V3 / 物理36脚：a7 → STBY")
    wire("M01","motor","DRV.AO1","EV3.1",[(150,770)],"AO1 → EV3 1脚（直接线）")
    wire("M02","motor","DRV.AO2","EV3.2",[(200,820)],"AO2 → EV3 2脚（直接线）")
    wire("E01","ground","EV3.3","BB.-37",[(250,1029),(1755,1029),(1755,510)],"EV3 3脚 → 面包板 GND")
    wire("E02","power","EV3.4","BB.+40",[(300,1044),(1700,1044),(1700,485)],"EV3 4脚 → 面包板 5V")
    wire("E03","encoder","EV3.5","BB.h33",[(350,1059),(1490,1059)],"EV3 5脚 → h33，进入 A组10kΩ")
    wire("E04","encoder","EV3.6","BB.h31",[(400,1085),(1440,1085)],"EV3 6脚 → h31，进入 B组10kΩ")
    wire("E05","encoder","BB.i26","BB.i8",[(1285,785),(1285,981),(865,981)],"A分压点 i26 → GP4 i8（物理6脚）")
    wire("E06","encoder","BB.i28","BB.i9",[(1395,785),(1395,1006),(890,1006)],"B分压点 i28 → GP5 i9（物理7脚）")

    wire("S01","power","BUCK.OUT+","SERVO.V+",[(1100,190),(1100,125),(1820,125),(1820,650)],"降压 OUT+ → 舵机红线 +5V（独立动力线）")
    wire("S02","ground","BUCK.OUT−","SERVO.GND",[(1170,290),(1170,340),(1840,340),(1840,700)],"降压 OUT− → 舵机棕线 GND（独立回流）")
    wire("S03","servo","BB.j13","SERVO.SIG",[(990,915),(1800,915),(1800,750)],"GP8 / 物理11脚：j13 → 舵机黄线信号")


RESISTORS = [("R1","BB.f33","BB.f26",10000),("R2","BB.j26","BB.G26",20000),
             ("R3","BB.g31","BB.g28",10000),("R4","BB.j28","BB.G28",20000)]


L_RESISTORS = [("LR1", "BB.f37", "BB.f34", 10000),
               ("LR2", "BB.j34", "BB.G34", 20000),
               ("LR3", "BB.g40", "BB.g36", 10000),
               ("LR4", "BB.j36", "BB.G36", 20000)]
L_CONDITION = ("仅适用于当前健康 DRV8833 的 B 路空闲；用户尚未确认该硬件条件。"
               "电流、温升及实物尺寸未验收。现固件只有单臂控制，ARM_ID 不切换 GPIO；"
               "切换视图不意味双臂控制能力，不能据此让 R/L 同时运动。")


def resistors_for(mode):
    return RESISTORS + (L_RESISTORS if mode == "RL" else [])


def make_l_parts():
    """扩展画布，不移动原 R 元件或孔位。L 编号和琥珀色光晕表示新增。"""
    PARTS.extend([rect(20, 1480, 2160, 515, "#fff7e6", "#bf7900"),
                  text(135, 1517, "＋ 新增 L · 使用同一块健康 DRV8833 的空闲 B 路（用户尚未确认）", 26, "#805000", bold=True),
                  text(135, 1551, "当前仅单臂固件 · ARM_ID 不切换 GPIO · 电流 / 温升未验收 · 不是双臂运行说明", 20, "#805000"),
                  rect(70, 1740, 415, 145, "#fff", "#bf7900"),
                  text(90, 1780, "L · EV3 马达 / 六个独立端子", 22, bold=True),
                  text(90, 1815, "按 EV3 触点编号核对，不只看线色", 18),
                  text(90, 1850, "1 / 2 动力直连 BO1 / BO2", 18),
                  text(560, 1780, "L 编码器：两组独立 10kΩ / 20kΩ", 24, bold=True),
                  text(560, 1820, "脚5 → h37 → LR1 → 第34列 → GP12（i18）", 20),
                  text(560, 1860, "脚6 → h40 → LR3 → 第36列 → GP13（i19）", 20),
                  text(560, 1900, "LR2 / LR4 分别从第34 / 36列接下方地轨", 19),
                  text(45, 1955, "孔位为候选布局：断电核对孔距、引脚与电阻体间隙；电阻腿绝缘，跨线无圆点不连接。", 20),
                  text(45, 1984, "STBY 保持 3V3（不是 5V VCC）· ENC_PULLUP=False · Pico USB 供电 · P04 独立回流保持不变", 18),
                  rect(1890, 1720, 260, 180, "#fff", "#bf7900"),
                  text(1910, 1750, "L · Geekservo", 23, bold=True),
                  text(1910, 1800, "V+ · 5V", 19, COLORS["power"]),
                  text(1910, 1840, "GND", 19),
                  text(1910, 1880, "GP9 / j14", 19)])
    PARTS[:] = [part.replace("马达、编码器、舵机一次接齐。", "R 原接线保留；新增 L 动力先断电。")
                .replace("④ EV3 马达", "④ R · EV3 马达")
                .replace("⑤ Geekservo · 灰色 270°", "⑤ R · Geekservo 270°") for part in PARTS]
    for i in range(1, 7):
        x = 100 + i * 55
        pin(f"L.EV3.{i}", x, 1740)
        PARTS.extend([dot(x, 1740, "#805000", 6), text(x, 1730, i, 16, anchor="middle", bold=True)])
    for name, y in [("V+", 1795), ("GND", 1835), ("SIG", 1875)]:
        pin("L.SERVO." + name, 1890, y)
    for col, gpio in [(11, 6), (12, 7), (14, 9), (18, 12), (19, 13)]:
        x, y = P[f"BB.h{col}"]
        PARTS.append(text(x, y-(30 if gpio == 12 else 16), f"GP{gpio}", 12, "#ffe6a3", "middle", True))


def make_l_wires():
    wire("LC01", "control", "BB.j11", "DRV.BIN1", [(940, 936), (610, 936), (610, 820)], "新增 L：GP6 / 物理9脚，j11 → BIN1")
    wire("LC02", "control", "BB.j12", "DRV.BIN2", [(965, 961), (630, 961), (630, 870)], "新增 L：GP7 / 物理10脚，j12 → BIN2")
    wire("LM01", "motor", "DRV.BO1", "L.EV3.1", [(70, 920), (70, 1620), (155, 1620)], "新增 L：BO1 → L EV3 1脚（独立动力线）")
    wire("LM02", "motor", "DRV.BO2", "L.EV3.2", [(90, 870), (90, 1600), (210, 1600)], "新增 L：BO2 → L EV3 2脚（独立动力线）")
    wire("LE01", "ground", "L.EV3.3", "BB.-39", [(265, 1680), (1790, 1680), (1790, 530), (1640, 530)], "新增 L：EV3 3脚 → 上地轨 −39")
    wire("LE02", "power", "L.EV3.4", "BB.+39", [(320, 1660), (1810, 1660), (1810, 465), (1640, 465)], "新增 L：EV3 4脚 → 上5V轨 +39")
    wire("LE03", "encoder", "L.EV3.5", "BB.h37", [(375, 1640), (1715, 1640), (1715, 795), (1590, 795)], "新增 L：EV3 5脚 → h37，进入 LR1 10kΩ")
    wire("LE04", "encoder", "L.EV3.6", "BB.h40", [(430, 1620), (1725, 1620), (1725, 775), (1665, 775)], "新增 L：EV3 6脚 → h40，进入 LR3 10kΩ")
    wire("LE05", "encoder", "BB.i34", "BB.i18", [(1515, 1195), (1115, 1195)], "新增 L：A分压点 i34 → GP12 i18（物理16脚）")
    wire("LE06", "encoder", "BB.i36", "BB.i19", [(1565, 1210), (1140, 1210)], "新增 L：B分压点 i36 → GP13 i19（物理17脚）")
    wire("LS01", "power", "BUCK.OUT+", "L.SERVO.V+", [(1110, 190), (1110, 110), (2190, 110), (2190, 1700), (1830, 1700), (1830, 1795)], "新增 L：降压 OUT+ → L舵机 +5V（独立动力线）")
    wire("LS02", "ground", "BUCK.OUT−", "L.SERVO.GND", [(1180, 290), (1180, 350), (2170, 350), (2170, 1680), (1850, 1680), (1850, 1835)], "新增 L：降压 OUT− → L舵机 GND（独立回流）")
    wire("LS03", "servo", "BB.j14", "L.SERVO.SIG", [(1015, 990), (1860, 990), (1860, 1875)], "新增 L：GP9 / 物理12脚，j14 → L舵机信号")


def resistor_svg(name, a, b, value):
    ax,ay=P[a]; bx,by=P[b]; x=(ax+bx)/2; y=(ay+by)/2
    vert=ax==bx
    s = (path([(ax,ay),(bx,by)], "#f7d58a", 10) if name.startswith("L") else "")
    s+=path([(ax,ay),(bx,by)],"#817664",3)
    s+=rect(x-(8 if vert else 27),y-(23 if vert else 8),16 if vert else 54,46 if vert else 16,"#ead5ab","#967c4e",4)
    if name.startswith("L"):
        s += text(x, y-22 if not vert else y+46, name, 12, "#805000", "middle", True)
        # 垂直电阻在体内标阻值，避免相邻两路的标签互相覆盖。
        s += text(x, y+4 if vert else y+24,
                  "20k" if vert else "10kΩ", 10 if vert else 13, "#725224", "middle", True)
    elif vert:
        s+=text(x+(-17 if name=="R2" else 17),y+3,"20kΩ",14,"#725224","end" if name=="R2" else "start",True)
    else:
        s+=text(x,y+(-17 if name=="R1" else 25),"10kΩ",14,"#725224","middle",True)
    s+=dot(ax,ay,"#725224",3)+dot(bx,by,"#725224",3)
    return f'<g data-group="encoder"><title>{name}: {a} → {b}, {value} Ω</title>{s}</g>'


def validate(mode="R"):
    """按面包板连通组和实物导线验证网络，电阻不能被导线短接。"""
    assert mode in ("R", "RL"), "未知接线模式"
    if mode == "RL":
        assert spec.ARMS['L'] == ((6, 7), (12, 13), (9,), (2, 3)), "L 臂分配与固定孔位图不符"
    parent={k:k for k in P}
    def root(k):
        while parent[k]!=k:
            parent[k]=parent[parent[k]]; k=parent[k]
        return k
    def join(a,b): parent[root(a)]=root(b)
    for c in range(1,41):
        for letters in ["abcde","fghij"]:
            for r in letters[1:]: join(f"BB.{letters[0]}{c}",f"BB.{r}{c}")
    for r in ["+","-","G"]:
        for lo,hi in [(1,20),(21,40)]:
            for c in range(lo+1,hi+1): join(f"BB.{r}{lo}",f"BB.{r}{c}")
    # 模块内部共地是本方案的前提；这两组不是外部导线。
    join("DRV.GND-L1", "DRV.GND-L2")
    join("DRV.GND-L1", "DRV.GND-R")
    join("BUCK.IN−", "BUCK.OUT−")
    for w in WIRES: join(w["start"],w["end"])
    for a,b in [("DC.GND","DRV.GND-L1"),("DC.GND","BB.a5"),("DC.GND","EV3.3"),
                ("DC.GND","BB.G26"),("DC.GND","BB.G28"),("DC.+9V","DRV.VM"),
                ("DC.+9V","BUCK.IN+"),("DC.GND","BUCK.IN−"),("DC.GND","BUCK.OUT−"),
                ("BUCK.OUT+","EV3.4"),("DRV.AIN1","BB.h6"),("DRV.AIN2","BB.h7"),
                ("DRV.STBY","BB.c7"),("EV3.5","BB.f33"),("EV3.6","BB.g31"),
                ("BUCK.OUT+","SERVO.V+"),("BUCK.OUT−","SERVO.GND"),("BB.h13","SERVO.SIG"),
                ("BB.f26","BB.h8"),("BB.g28","BB.h9"),("EV3.1","DRV.AO1"),("EV3.2","DRV.AO2")]:
        assert root(a)==root(b),(a,b)
    independent=["DC.GND","DC.+9V","BUCK.OUT+","DRV.AIN1","DRV.AIN2","DRV.STBY",
                 "EV3.1","EV3.2","EV3.5","EV3.6","BB.h8","BB.h9","SERVO.SIG"]
    if mode == "RL":
        for a, b in [("DRV.BIN1", "BB.h11"), ("DRV.BIN2", "BB.h12"),
                     ("DRV.BO1", "L.EV3.1"), ("DRV.BO2", "L.EV3.2"),
                     ("DC.GND", "L.EV3.3"), ("BUCK.OUT+", "L.EV3.4"),
                     ("L.EV3.5", "BB.f37"), ("L.EV3.6", "BB.g40"),
                     ("BB.f34", "BB.h18"), ("BB.g36", "BB.h19"),
                     ("BB.G34", "DC.GND"), ("BB.G36", "DC.GND"),
                     ("BUCK.OUT+", "L.SERVO.V+"), ("DC.GND", "L.SERVO.GND"),
                     ("BB.h14", "L.SERVO.SIG")]:
            assert root(a) == root(b), (a, b)
        independent += ["DRV.BIN1", "DRV.BIN2", "L.EV3.1", "L.EV3.2",
                        "L.EV3.5", "L.EV3.6", "BB.h18", "BB.h19", "L.SERVO.SIG"]
    assert len({root(k) for k in independent})==len(independent),"不应相连的网络发生短接"
    for _,a,b,_ in resistors_for(mode): assert root(a)!=root(b),"电阻被导线短接"
    # 电气共地不能证明回流路径正确；这些动力支路必须直接连接。
    required = {frozenset(pair) for pair in [("DC.GND", "BUCK.IN−"),
                ("BUCK.OUT+", "SERVO.V+"), ("BUCK.OUT−", "SERVO.GND")]}
    if mode == "RL":
        required.update(frozenset(pair) for pair in [("BUCK.OUT+", "L.SERVO.V+"),
                                                   ("BUCK.OUT−", "L.SERVO.GND")])
        assert L_RESISTORS == [("LR1", "BB.f37", "BB.f34", 10000),
                               ("LR2", "BB.j34", "BB.G34", 20000),
                               ("LR3", "BB.g40", "BB.g36", 10000),
                               ("LR4", "BB.j36", "BB.G36", 20000)], "L 分压电阻端点或阻值错误"
    actual = {frozenset((w["start"], w["end"])) for w in WIRES}
    assert required <= actual, "动力支路必须独立直连，不能借道驱动地脚或面包板"
    # 不允许在同一个面包板孔里画两个线端/元件脚。
    used=[f"BB.{row}{col}" for row in ("c", "h") for col in range(3, 23)]
    for w in WIRES: used.extend(k for k in [w["start"],w["end"]] if k.startswith("BB."))
    for _,a,b,_ in resistors_for(mode): used.extend([a,b])
    assert len(used)==len(set(used)),"一个孔被多个引脚占用"


def svg(mode="R"):
    out=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2200 1430" role="img" aria-label="Pico 单臂完整接线图，包含电源、DRV8833、EV3编码器分压与Geekservo">',
         '<style>text{font-family:"Noto Sans CJK SC","Microsoft YaHei",sans-serif}svg{background:#fffdf8} [data-group]{transition:opacity .15s}</style>',
         rect(0,0,2200,1430,"#fffdf8","none",0),text(40,52,"Pico 单臂完整接线 · 马达、编码器与舵机",34,bold=True),
         text(40,87,"Pico 由 USB 供电 · 马达与舵机动力独立走线 · 编码器双路分压 · 全部接齐后分项测试",19)]
    if mode == "RL":
        out[0] = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2200 2020" role="img" aria-label="R+L 条件式接线图；同板健康 B 路须空闲，尚未确认；当前仅单臂固件">'
        out[2] = rect(0, 0, 2200, 2020, "#fffdf8", "none", 0)
        out[3] = text(40, 52, "R+L 接线候选 · 原 R 保留，琥珀色光晕 / L 编号为新增", 31, bold=True)
        out[4] = text(40, 87, "同板健康 B 路须空闲（尚未确认）· ARM_ID 不切换 GPIO · 切换视图不意味双臂控制能力", 20, "#805000")
    out.extend(PARTS)
    for w in WIRES:
        points=[P[w["start"]],*w["bends"],P[w["end"]]]
        color=COLORS[w["group"]]; width=5 if w["code"] in ["P03","P04","P07","P08","M01","M02","S01","S02"] else 3.5
        added = w["code"].startswith("L")
        if added and w["code"][:2] in ("LM", "LS") and w["code"] != "LS03":
            width = 5
        halo = path(points, "#f7d58a", width+7) if added else ""
        out.append(f'<g data-group="{w["group"]}" data-wire="{w["code"]}" data-added="{str(added).lower()}"><title>{escape(w["code"]+": "+w["note"])}</title>'+halo+path(points,"#fffdf8",width+3)+path(points,color,width)+dot(*points[0],color,4)+dot(*points[-1],color,4)+"</g>")
    out.extend(resistor_svg(*r) for r in resistors_for(mode))
    # 几个主要接点旁边的编号，详细端点见下方逐线表。
    for x,y,label,color in [(120,602,"P07 · 9V",COLORS["power"]),(195,746,"P08 · GND",COLORS["ground"]),
                            (320,330,"P04 · 独立回流",COLORS["ground"]),(491,999,"P10 → 地轨",COLORS["ground"]),
                            (593,715,"C01",COLORS["control"]),(540,651,"C02",COLORS["control"]),
                            (611,757,"C03 · 3V3",COLORS["control"]),(1130,1120,"E03 · A",COLORS["encoder"]),
                            (1190,1110,"E04 · B",COLORS["encoder"])]:
        out.append(text(x,y,label,15,color,bold=True))
    if mode == "RL":
        # PNG 也能读到新增线号；把标牌放在线路附近，并在导线之后绘制。
        labels = [(505, 810, "LC01"), (505, 860, "LC02"),
                  (1135, 1150, "LE05"), (1160, 1175, "LE06")]
        for i, code in enumerate(("LM01", "LM02", "LE01", "LE02", "LE03", "LE04"), 1):
            x = 100 + i*55
            labels.append((x-20, 1722, code))
            out.append(text(x, 1761, i, 14, "#805000", "middle", True))
        for x, y, code in labels:
            out.append(rect(x-2, y-14, 48, 19, "#fff7e6", "none", 2))
            out.append(text(x, y, code, 14, "#805000", bold=True))
        for code, y in [("LS01", 1798), ("LS02", 1838), ("LS03", 1878)]:
            out.append(text(2088, y, code, 13, "#805000", bold=True))
    out.append('</svg>')
    return "\n".join(out)


def main(directory=HERE):
    spec.validate()
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    modes = {}
    for mode in ("R", "RL"):
        P.clear(); PARTS.clear(); WIRES.clear()
        make_parts(); make_wires()
        if mode == "RL":
            make_l_parts(); make_l_wires()
        validate(mode)
        drawing = svg(mode)
        stem = "direct-breadboard" + ("-rl" if mode == "RL" else "")
        (directory / (stem + ".svg")).write_text(drawing, encoding="utf-8")
        netlist = {"wires": WIRES, "resistors": resistors_for(mode),
                   "internal_connections": [["DRV.GND-L1", "DRV.GND-L2", "DRV.GND-R"], ["BUCK.IN−", "BUCK.OUT−"]],
                   "precondition": "降压模块 IN− 与 OUT− 内部共地；DRV8833 三个 GND 板内相通。"}
        if mode == "RL":
            netlist["precondition"] += L_CONDITION
        (directory / (stem + "-netlist.json")).write_text(json.dumps(netlist, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        rows = "".join(f'<tr data-group="{w["group"]}" data-added="{str(w["code"].startswith("L")).lower()}"><td>{w["code"]}</td><td>{escape(w["note"])}</td><td>{escape(w["start"]+" → "+w["end"])}</td></tr>' for w in WIRES)
        resistor_rows = "".join(f'<tr data-group="encoder" data-added="{str(n.startswith("L")).lower()}"><td>{n}</td><td>{v//1000}kΩ</td><td>{a.replace("BB.", "")} ↔ {b.replace("BB.", "")}</td></tr>' for n,a,b,v in resistors_for(mode))
        modes[mode] = dict(drawing=drawing, rows=rows, resistors=resistor_rows)
        print(f"生成 {stem}.svg / -netlist.json；{len(WIRES)}根线、{len(resistors_for(mode))}只电阻，连通与孔位检查通过。")

    def hidden_attr(mode):
        return " hidden" if mode == "RL" else ""

    def panels(key):
        return "".join(f'<div data-mode-only="{mode}"{hidden_attr(mode)}>{data[key]}</div>' for mode, data in modes.items())

    buttons=''.join(f'<button type="button" data-filter="{k}" style="--c:{COLORS.get(k,"#183645")}">{label}</button>' for k,label in [("all","全部接线"),("power","9V / 5V"),("ground","公共地"),("control","驱动控制"),("encoder","编码器"),("motor","马达动力"),("servo","舵机信号")])
    page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Pico 原 R / 新 R+L · 面包板直连接线图</title>
<style>[hidden]{display:none!important}tr[data-added="true"]{background:#fff4d6}tr[data-added="true"] td:first-child{font-weight:700;color:#805000}.mode-note{border-left:5px solid #bf7900;padding:12px 16px;background:#fff7e6}*{box-sizing:border-box}body{margin:0;color:#243545;background:#f1f3f3;font:16px/1.65 system-ui,"Noto Sans CJK SC",sans-serif}main{max-width:1600px;margin:auto;padding:24px}h1{font-size:30px;line-height:1.3;margin:0 0 10px}h2{margin-top:0;font-size:23px}h3{font-size:19px}p{margin:8px 0 15px}.intro,section{background:white;border:1px solid #dbe0e2;border-radius:12px;padding:24px;margin-bottom:20px}.lead{font-size:18px}.status{background:#fff4d6;border-left:5px solid #c7951c;padding:12px 16px}.controls{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0}.controls button{cursor:pointer;padding:9px 16px;border:1px solid var(--c);border-radius:7px;background:white;color:var(--c);font:inherit}.controls button.active{background:var(--c);color:white}.canvas{overflow:auto;background:#fffdf8;border:1px solid #ddd;border-radius:8px}.canvas svg{display:block;width:100%;min-width:1150px;height:auto}.links{display:flex;gap:20px;flex-wrap:wrap}a{color:#1467a4}table{border-collapse:collapse;width:100%;font-size:15px}th,td{text-align:left;padding:9px 12px;border-bottom:1px solid #e0e5e7}th{background:#edf2f4}.table-scroll{overflow:auto}code,pre{font-family:ui-monospace,monospace}pre{background:#f0f4f5;padding:16px;overflow:auto}.grid{display:grid;grid-template-columns:1fr 1fr;gap:24px}.small{font-size:14px;color:#586976}.servo{background:#faf8f0;border-left:5px solid #b7a477;padding:18px}.servo svg{width:100%;max-width:700px}.state{font-size:13px;letter-spacing:.05em;color:#14766b;font-weight:700}li{margin:7px 0}button:focus-visible,a:focus-visible{outline:3px solid #f2b94d;outline-offset:3px}@media(max-width:760px){main{padding:12px}.intro,section{padding:16px}.grid{grid-template-columns:1fr}h1{font-size:25px}}@media print{.controls{display:none}main{max-width:none;padding:0}.canvas svg{min-width:0}.intro,section{break-inside:avoid;border:0}.canvas{overflow:visible}body{background:white}}</style>
<main><div class="intro"><div class="state">原说明页 · 保留 R 线路 · 条件式新增 L</div><h1>面包板接信号，动力线直接连接</h1><p class="lead">按图里的元件朝向和孔位接线。DRV8833 放在面包板旁边，使用母头线接模块排针；本图不使用洞洞板、分线端子或 Bricktronics。DC-005 正极分别接驱动 VM、降压 IN+；负极分别接驱动 GND、降压 IN−。下方切换接线视图，图、逐线表、电阻表和下载同步更新。</p><p class="status" data-mode-only="R"><strong>9V 总电源关掉，编码器也会失去 5V。</strong> 手动计数时保持编码器供电，并先将 GP2、GP3 都置低。2026-09-28 更换驱动模块后，大马达空载闭环已通过；v3 机械头、舵机和整机供电仍待验证。</p><div class="controls" role="group" aria-label="接线模式"><button type="button" data-mode="R" aria-pressed="true" class="active" style="--c:#183645">原 R 单臂</button><button type="button" data-mode="RL" aria-pressed="false" style="--c:#805000">新 R+L（条件式）</button></div><p class="small">切换仅改变说明，不改实物接线或固件；若已接新增 L，不能通过切回 R 视图套用单臂上电步骤。</p><p id="mode-status" aria-live="polite">原 R 单臂 · 25 根线 / 4 只电阻</p><div class="mode-note" data-mode-only="RL" hidden><strong>先确认：当前健康 DRV8833 的 B 路空闲。</strong> 用户尚未确认该硬件条件；若 B 路已占用或板子有故障，本方案不适用。电流、温升与实物尺寸未验收。现固件只有单臂控制，<code>ARM_ID</code> 不切换 GPIO；切换视图不意味双臂控制能力，不能据此让 R/L 同时运动。</div><div class="links"><a data-download="svg" href="direct-breadboard.svg" target="_blank">原 R · SVG 大图</a><a data-download="png" href="direct-breadboard.png" target="_blank">原 R · PNG 图片</a><a data-download="netlist.json" href="direct-breadboard-netlist.json" download>原 R · 网络表 JSON</a><a href="README.md">电路总览与验证状态</a><a href="perfboard.html">可选洞洞板方案</a></div></div>
<section id="complete-wiring"><h2>完整接线</h2><p data-mode-only="R">断开 USB 和9V，按下图及逐线表一次接齐马达、编码器与舵机。P04 从 DC-005 负极直接接降压 IN−；舵机红／棕线分别通过 S01／S02 直连降压 OUT+／OUT−，黄线通过 S03 接 j13（GP8）。Pico 由 USB 供电。</p><div data-mode-only="RL" hidden><p>原 R 的 25 根线与 4 只电阻全部保留；新增 L 为 13 根线与 4 只电阻，使用 <code>L</code> 前缀和琥珀色高亮。仅在确认同板健康 B 路空闲后考虑此候选接法。</p><p>GP6 / GP7 → BIN1 / BIN2，BO1 / BO2 → L EV3 1 / 2脚；GP12 / GP13 分别读取 L 编码器独立分压点；GP9 接 L 舵机信号。LS01 / LS02 从降压 OUT+ / OUT− 独立接 L 舵机电源和地，不借道 R 舵机或面包板。P04 独立回流、Pico USB 供电和 STBY 接 3V3 都不变；STBY 不是 5V VCC。</p><p><strong>此视图只说明接线，不能照搬原 R 命令给 L 上电。</strong>现固件没有初始化 L 的 GPIO，<code>off</code> 不能保证 L 输入为低。硬件条件、独立 GPIO 初始化与控制方案验证之前，保持新增 L 动力断电。</p></div></section>
<section><h2>完整接线图 · <span data-mode-label>原 R</span></h2><p>点按钮突出显示一组线及对应表行（下载始终为所选模式的完整接线）；悬停导线可看编号。手机上横向拖动查看。交叉线没有圆点就不连接。</p><div class="controls" role="group" aria-label="按用途突出导线">BUTTONS</div><div class="canvas">DRAWING</div><p class="small">面包板坐标：Pico 两排插在 c3～c22、h3～h22，USB 朝左。面包板实际通常超过40列，此处仅画使用区域；两半电源轨用图中的短跳线接通。未用的另一条正电源轨省略。</p></section>
<section><h2>先看清这些实物连接</h2><div class="grid"><div><h3>不用让动力电流经过面包板</h3><ul><li>9V → VM、驱动 GND → 电源负极，以及驱动输出 → 马达，全部用独立导线直接连接模块；马达加工线用现有普通接线端子转接。</li><li>模块公排针接母头线端，端子夹持对应线材；动力线和线端额定电流需满足马达启动电流，普通细杜邦跳线只用于信号。</li><li>DRV8833 放在绝缘面并固定，底部引脚不要碰金属或彼此短接。模块不需要焊死。</li><li>DC-005 正极焊脚引出两根线，分别接 VM 与降压 IN+，焊点用热缩管等绝缘；负极直接接 DRV8833 左排第3脚 GND。模块端仍用母头插接。</li></ul></div><div><h3>使用现有配件</h3><ul><li>9V 电源、DC-005、已有降压模块，输出调到 5.0V。此接法要求降压 IN− 与 OUT− 内部共地，完整接线时 OUT− 直接接舵机地。</li><li>Pico、DRV8833、面包板、<span data-mode-only="R">两只10kΩ与两只20kΩ。</span><span data-mode-only="RL" hidden>共四只10kΩ与四只20kΩ；L 另需一套马达、舵机和独立线束。</span></li><li>已修复/重新制作的 EV3 线；散铜丝先接端子，再转成面包板公头线。</li><li>本图不额外加电容；保留模块自带电容。降压模块不要求螺钉或支柱，避免裸露焊盘接触导体即可。</li></ul></div></div><p><strong>朝向说明：</strong>DRV8833 元件面朝上，左排从上到下为 VM、NC、GND、AO1、AO2、BO2、BO1、GND；右排为 NC、AIN2、AIN1、STBY、BIN1、BIN2、NC、GND。与你提供的丝印一致。DC-005 的三个焊脚形状和降压模块尺寸未确认，图中只标功能，不猜焊脚顺序；DC-005 切换脚留空绝缘。</p></section>
<section><h2>全部导线与分压孔位 · <span data-mode-label>原 R</span></h2><p><code>BB.+</code> 是上方5V轨，<code>BB.-</code> 是上方地轨，<code>BB.G</code> 是下方地轨。每个数字列的 a～e 相通、f～j 相通，中槽两侧不通。DRV.GND-L1 是左排第3脚，DRV.GND-L2 是左排第8脚，DRV.GND-R 是右排第8脚；这三个脚通过模块内部连接共地。导线编号与图中提示、网络表一致。DRV.GND-L2 留空。</p><div class="table-scroll"><table><thead><tr><th>编号</th><th>怎么接</th><th>图内端点</th></tr></thead><tbody>ROWS</tbody></table></div><h3>分压电阻 · <span id="resistor-count">4 只</span></h3><table><thead><tr><th>编号</th><th>阻值</th><th>两端插孔（无正反）</th></tr></thead><tbody>RESISTORS</tbody></table><p>GP4 接第26列分压点，GP5 接第28列分压点；黄 / 蓝线接10kΩ另一端。R 的两只20kΩ都接下方地轨。程序保持 <code>ENC_PULLUP=False</code>（编码器构造参数 <code>pull_up=False</code>）。</p><div data-mode-only="RL" hidden><p>L：EV3 5脚 → h37 → LR1（10kΩ，f37–f34）→ 第34列 → i18 / GP12，LR2（20kΩ，j34–G34）接地；EV3 6脚 → h40 → LR3（10kΩ，g40–g36）→ 第36列 → i19 / GP13，LR4（20kΩ，j36–G36）接地。R / L 四个编码器输入与分压节点各自独立，不能并联，也不能直连 5V。</p><p>几何核对采用 2.54mm 孔距：LR1 横跨 3 格（7.62mm），LR3 横跨 4 格（10.16mm）；它们位于 Pico 末端第22列之外。20kΩ 接下地轨的跨度依实际面包板而定；尚未收到电阻体尺寸，须断电确认引脚可达、无挤压且裸腿不相碰。图中的轨断口仅为模型，需核对实物通断。</p></div></section>

<section data-mode-only="R"><h2>R 单臂接齐后，按命令分项测试</h2><ol><li><strong>断电检查：</strong>降压输出已空载调到5.0V；核对 P04 直接回电源负极，舵机红／棕线直连降压输出，全部设备共地。不放魔方，夹爪留出活动空间。</li><li><strong>Pico先接USB：</strong>运行 <code>import arm_test; arm_test.main()</code>，出现 <code>arm&gt;</code> 后输入 <code>off</code>。程序初始化时马达滑行、舵机 PWM 关闭。</li><li><strong>再打开9V：</strong>观察有无异常动作。输入 <code>enc</code>，轻转机械头确认计数变化；然后按单臂说明确认马达方向与齿轮比。</li><li><strong>标定舵机：</strong>舵机电线可保持接好；首次定位必须断电脱开曲柄与连杆，空载定位后断电连接，再小步标定，见 <a href="../single_arm.md#servo-calibration">舵机定位与连杆装配</a>。当前开合参数是旧值，标定前不要运行 <code>open</code>、<code>close</code>、<code>grip</code> 或 <code>cycle</code>。</li><li><strong>旋转与联合测试：</strong>按 <a href="../single_arm.md#5-测试步骤">单臂测试第0～9步</a>继续；每一步通过后再做下一步，无需重新插拔舵机。</li></ol><p>大马达空载闭环已通过，见<a href="../single_arm-results.md">实测记录</a>；v3 机械头、舵机标定和整机供电仍需实测。</p></section>
<section data-mode-only="R"><h2>可选排障：暂时隔离舵机</h2><p>只有排查复位、供电跌落或驱动异常时，才需要断开 USB 和9V后暂时拔下舵机，单独检查马达和编码器。P04 保持直接接电源负极。排障后断电接回舵机。</p></section>
<section data-mode-only="RL" hidden><h2>R+L 的验收边界</h2><p>先断开 USB 与9V，确认健康 B 路确实空闲、每个孔只占一个端点、四组分压独立且每路为10kΩ串联＋20kΩ对地。确认各设备共地，舵机正负线独立直达降压输出，保留 P04 直接回 DC-005 负极。</p><p>后续受控电气验收需先将分压点与 Pico 断开，分别测量四路输出高低电平，再断电接回；分压点不可超过3.3V。电源启动瞬态、两路电机电流、驱动温升和线端承载仍待实际验收。本页没有双臂上电或运动测试步骤；原 R 的空载验证不覆盖新增 L。</p></section><section><h2>依据</h2><ul><li><a href="https://www.lego.com/cdn/cs/set/assets/blt86e79bb287a0d0b1/Appendix_LEGO_MINDSTORMS_EV3_programmable_brick_main_hardware_schematics.pdf">LEGO 官方 EV3 原理图</a>：Output 1/2为动力端、3为地、4为5V、5/6为反馈。</li><li><a href="https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf">Raspberry Pi Pico 官方数据手册</a>：物理脚位与GPIO对应。</li><li><a href="https://www.ti.com/lit/ds/symlink/drv8833.pdf">TI DRV8833 数据手册</a>：输入控制逻辑；模块丝印排列使用用户实物确认结果。</li></ul></section></main>
<script>
let mode='R', filter='all';
function applyFilter(){
  document.querySelectorAll('[data-filter]').forEach(b=>{
    const active=b.dataset.filter===filter;
    b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active));
  });
  document.querySelectorAll('.canvas [data-group]').forEach(x=>x.style.opacity=(filter==='all'||x.dataset.group===filter)?'1':'.1');
  document.querySelectorAll('tr[data-group]').forEach(x=>x.style.opacity=(filter==='all'||x.dataset.group===filter)?'1':'.3');
}
function setMode(next){
  mode=next;
  document.querySelectorAll('[data-mode-only]').forEach(x=>x.hidden=x.dataset.modeOnly!==mode);
  document.querySelectorAll('[data-mode]').forEach(b=>{
    const active=b.dataset.mode===mode;
    b.classList.toggle('active',active);b.setAttribute('aria-pressed',String(active));
  });
  const label=mode==='R'?'原 R':'新 R+L（条件式）';
  document.querySelectorAll('[data-mode-label]').forEach(x=>x.textContent=label);
  document.getElementById('mode-status').textContent=label+(mode==='R'?' 单臂 · 25 根线 / 4 只电阻':' · 38 根线 / 8 只电阻 · 新增 L 高亮，硬件条件尚未确认');
  document.getElementById('resistor-count').textContent=mode==='R'?'4 只':'8 只（新增 L 4 只）';
  document.querySelectorAll('[data-download]').forEach(a=>{
    const ext=a.dataset.download, stem='direct-breadboard'+(mode==='RL'?'-rl':'');
    a.href=stem+(ext==='netlist.json'?'-':'.')+ext;
    a.textContent=label+' · '+({'svg':'SVG 大图','png':'PNG 图片','netlist.json':'网络表 JSON'}[ext]);
  });
  applyFilter();
}
document.querySelectorAll('[data-mode]').forEach(b=>b.addEventListener('click',()=>setMode(b.dataset.mode)));
document.querySelectorAll('[data-filter]').forEach(b=>b.addEventListener('click',()=>{filter=b.dataset.filter;applyFilter()}));
setMode('R');
</script></html>'''
    page = page.replace("BUTTONS", buttons).replace("DRAWING", panels("drawing"))
    # tbody 不能嵌 div；分别生成完整、可隐藏的表格，避免浏览器纠正 DOM。
    for placeholder, key in [("ROWS", "rows"), ("RESISTORS", "resistors")]:
        table_start = page.rfind("<table", 0, page.index(placeholder))
        table_end = page.index("</table>", page.index(placeholder)) + len("</table>")
        template = page[table_start:table_end]
        tables = "".join(f'<div data-mode-only="{mode}"{hidden_attr(mode)}>'
                         + template.replace(placeholder, data[key]) + '</div>' for mode, data in modes.items())
        page = page[:table_start] + tables + page[table_end:]
    (directory / "direct-breadboard.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    main()
