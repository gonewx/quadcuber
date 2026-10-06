"""生成脱离洞洞板的单臂接线图。运行：python3 docs/wiring/direct_wiring.py。"""
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


def resistor_svg(name, a, b, value):
    ax,ay=P[a]; bx,by=P[b]; x=(ax+bx)/2; y=(ay+by)/2
    vert=ax==bx
    s=path([(ax,ay),(bx,by)],"#817664",3)
    s+=rect(x-(8 if vert else 27),y-(23 if vert else 8),16 if vert else 54,46 if vert else 16,"#ead5ab","#967c4e",4)
    if vert:
        s+=text(x+(-17 if name=="R2" else 17),y+3,"20kΩ",14,"#725224","end" if name=="R2" else "start",True)
    else:
        s+=text(x,y+(-17 if name=="R1" else 25),"10kΩ",14,"#725224","middle",True)
    s+=dot(ax,ay,"#725224",3)+dot(bx,by,"#725224",3)
    return f'<g data-group="encoder"><title>{name}: {a} → {b}, {value} Ω</title>{s}</g>'


def validate():
    """按面包板连通组和实物导线验证网络，电阻不能被导线短接。"""
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
    assert len({root(k) for k in independent})==len(independent),"不应相连的网络发生短接"
    for _,a,b,_ in RESISTORS: assert root(a)!=root(b),"电阻被导线短接"
    # 电气共地不能证明回流路径正确；这些动力支路必须直接连接。
    required = {frozenset(pair) for pair in [("DC.GND", "BUCK.IN−"),
                ("BUCK.OUT+", "SERVO.V+"), ("BUCK.OUT−", "SERVO.GND")]}
    actual = {frozenset((w["start"], w["end"])) for w in WIRES}
    assert required <= actual, "动力支路必须独立直连，不能借道驱动地脚或面包板"
    # 不允许在同一个面包板孔里画两个线端/元件脚。
    used=[f"BB.{row}{col}" for row in ("c", "h") for col in range(3, 23)]
    for w in WIRES: used.extend(k for k in [w["start"],w["end"]] if k.startswith("BB."))
    for _,a,b,_ in RESISTORS: used.extend([a,b])
    assert len(used)==len(set(used)),"一个孔被多个引脚占用"


def svg():
    out=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2200 1430" role="img" aria-label="Pico 单臂完整接线图，包含电源、DRV8833、EV3编码器分压与Geekservo">',
         '<style>text{font-family:"Noto Sans CJK SC","Microsoft YaHei",sans-serif}svg{background:#fffdf8} [data-group]{transition:opacity .15s}</style>',
         rect(0,0,2200,1430,"#fffdf8","none",0),text(40,52,"Pico 单臂完整接线 · 马达、编码器与舵机",34,bold=True),
         text(40,87,"Pico 由 USB 供电 · 马达与舵机动力独立走线 · 编码器双路分压 · 全部接齐后分项测试",19)]
    out.extend(PARTS)
    for w in WIRES:
        points=[P[w["start"]],*w["bends"],P[w["end"]]]
        color=COLORS[w["group"]]; width=5 if w["code"] in ["P03","P04","P07","P08","M01","M02","S01","S02"] else 3.5
        out.append(f'<g data-group="{w["group"]}" data-wire="{w["code"]}"><title>{escape(w["code"]+": "+w["note"])}</title>'+path(points,"#fffdf8",width+3)+path(points,color,width)+dot(*points[0],color,4)+dot(*points[-1],color,4)+"</g>")
    out.extend(resistor_svg(*r) for r in RESISTORS)
    # 几个主要接点旁边的编号，详细端点见下方逐线表。
    for x,y,label,color in [(120,602,"P07 · 9V",COLORS["power"]),(195,746,"P08 · GND",COLORS["ground"]),
                            (320,330,"P04 · 独立回流",COLORS["ground"]),(491,999,"P10 → 地轨",COLORS["ground"]),
                            (593,715,"C01",COLORS["control"]),(540,651,"C02",COLORS["control"]),
                            (611,757,"C03 · 3V3",COLORS["control"]),(1130,1120,"E03 · A",COLORS["encoder"]),
                            (1190,1110,"E04 · B",COLORS["encoder"])]:
        out.append(text(x,y,label,15,color,bold=True))
    out.append('</svg>')
    return "\n".join(out)


def main(directory=HERE):
    spec.validate()
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    P.clear(); PARTS.clear(); WIRES.clear()
    make_parts(); make_wires(); validate()
    drawing=svg()
    (directory/"direct-breadboard.svg").write_text(drawing, encoding="utf-8")
    rows="".join(f'<tr data-group="{w["group"]}"><td>{w["code"]}</td><td>{escape(w["note"])}</td><td>{escape(w["start"]+" → "+w["end"])}</td></tr>' for w in WIRES)
    resistor_rows="".join(f'<tr><td>{n}</td><td>{v//1000}kΩ</td><td>{a.replace("BB.","")} ↔ {b.replace("BB.","")}</td></tr>' for n,a,b,v in RESISTORS)
    buttons=''.join(f'<button data-filter="{k}" style="--c:{COLORS.get(k,"#183645")}">{label}</button>' for k,label in [("all","全部接线"),("power","9V / 5V"),("ground","公共地"),("control","驱动控制"),("encoder","编码器"),("motor","马达动力"),("servo","舵机信号")])
    page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Pico 单臂 · 面包板直连接线图</title>
<style>*{box-sizing:border-box}body{margin:0;color:#243545;background:#f1f3f3;font:16px/1.65 system-ui,"Noto Sans CJK SC",sans-serif}main{max-width:1600px;margin:auto;padding:24px}h1{font-size:30px;line-height:1.3;margin:0 0 10px}h2{margin-top:0;font-size:23px}h3{font-size:19px}p{margin:8px 0 15px}.intro,section{background:white;border:1px solid #dbe0e2;border-radius:12px;padding:24px;margin-bottom:20px}.lead{font-size:18px}.status{background:#fff4d6;border-left:5px solid #c7951c;padding:12px 16px}.controls{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0}.controls button{cursor:pointer;padding:9px 16px;border:1px solid var(--c);border-radius:7px;background:white;color:var(--c);font:inherit}.controls button.active{background:var(--c);color:white}.canvas{overflow:auto;background:#fffdf8;border:1px solid #ddd;border-radius:8px}.canvas svg{display:block;width:100%;min-width:1150px;height:auto}.links{display:flex;gap:20px;flex-wrap:wrap}a{color:#1467a4}table{border-collapse:collapse;width:100%;font-size:15px}th,td{text-align:left;padding:9px 12px;border-bottom:1px solid #e0e5e7}th{background:#edf2f4}.table-scroll{overflow:auto}code,pre{font-family:ui-monospace,monospace}pre{background:#f0f4f5;padding:16px;overflow:auto}.grid{display:grid;grid-template-columns:1fr 1fr;gap:24px}.small{font-size:14px;color:#586976}.servo{background:#faf8f0;border-left:5px solid #b7a477;padding:18px}.servo svg{width:100%;max-width:700px}.state{font-size:13px;letter-spacing:.05em;color:#14766b;font-weight:700}li{margin:7px 0}button:focus-visible,a:focus-visible{outline:3px solid #f2b94d;outline-offset:3px}@media(max-width:760px){main{padding:12px}.intro,section{padding:16px}.grid{grid-template-columns:1fr}h1{font-size:25px}}@media print{.controls{display:none}main{max-width:none;padding:0}.canvas svg{min-width:0}.intro,section{break-inside:avoid;border:0}.canvas{overflow:visible}body{background:white}}</style>
<main><div class="intro"><div class="state">当前阶段：v4 完整接线与实物标定</div><h1>面包板接信号，动力线直接连接</h1><p class="lead">按图里的元件朝向和孔位接线。DRV8833 放在面包板旁边，使用母头线接模块排针；本图不使用洞洞板、分线端子或 Bricktronics。DC-005 正极分别接驱动 VM、降压 IN+；负极分别接驱动 GND、降压 IN−。马达、编码器和舵机可一次接齐，再按顺序发命令测试。</p><p class="status"><strong>9V 总电源关掉，编码器也会失去 5V。</strong> 手动计数时保持编码器供电，并先将 GP2、GP3 都置低。2026-09-28 更换驱动模块后，大马达空载闭环已通过；v4 机械头、舵机和整机供电仍待验证。</p><div class="links"><a href="direct-breadboard.svg" target="_blank">打开 SVG 大图</a><a href="direct-breadboard.png" target="_blank">打开 PNG 图片</a><a href="README.md">电路总览与验证状态</a><a href="perfboard.html">可选洞洞板方案</a></div></div>
<section id="complete-wiring"><h2>完整接线</h2><p>断开 USB 和9V，按下图及逐线表一次接齐马达、编码器与舵机。P04 从 DC-005 负极直接接降压 IN−；舵机红／棕线分别通过 S01／S02 直连降压 OUT+／OUT−，黄线通过 S03 接 j13（GP8）。Pico 由 USB 供电。</p></section>
<section><h2>完整接线图</h2><p>点按钮突出显示一组线；悬停导线可看编号。手机上横向拖动查看。交叉线没有圆点就不连接。</p><div class="controls">BUTTONS</div><div class="canvas">DRAWING</div><p class="small">面包板坐标：Pico 两排插在 c3～c22、h3～h22，USB 朝左。面包板实际通常超过40列，此处仅画使用区域；两半电源轨用图中的短跳线接通。未用的另一条正电源轨省略。</p></section>
<section><h2>先看清这些实物连接</h2><div class="grid"><div><h3>不用让动力电流经过面包板</h3><ul><li>9V → VM、驱动 GND → 电源负极，以及 AO1 / AO2 → 马达，全部用独立导线直接连接模块；马达加工线用现有普通接线端子转接。</li><li>模块公排针接母头线端，端子夹持对应线材；动力线和线端额定电流需满足马达启动电流，普通细杜邦跳线只用于信号。</li><li>DRV8833 放在绝缘面并固定，底部引脚不要碰金属或彼此短接。模块不需要焊死。</li><li>DC-005 正极焊脚引出两根线，分别接 VM 与降压 IN+，焊点用热缩管等绝缘；负极直接接 DRV8833 左排第3脚 GND。模块端仍用母头插接。</li></ul></div><div><h3>使用现有配件</h3><ul><li>9V 电源、DC-005、已有降压模块，输出调到 5.0V。此接法要求降压 IN− 与 OUT− 内部共地，完整接线时 OUT− 直接接舵机地。</li><li>Pico、DRV8833、面包板、两只10kΩ与两只20kΩ。</li><li>已修复/重新制作的 EV3 线；散铜丝先接端子，再转成面包板公头线。</li><li>本图不额外加电容；保留模块自带电容。降压模块不要求螺钉或支柱，避免裸露焊盘接触导体即可。</li></ul></div></div><p><strong>朝向说明：</strong>DRV8833 元件面朝上，左排从上到下为 VM、NC、GND、AO1、AO2、BO2、BO1、GND；右排为 NC、AIN2、AIN1、STBY、BIN1、BIN2、NC、GND。与你提供的丝印一致。DC-005 的三个焊脚形状和降压模块尺寸未确认，图中只标功能，不猜焊脚顺序；DC-005 切换脚留空绝缘。</p></section>
<section><h2>全部导线与分压孔位</h2><p><code>BB.+</code> 是上方5V轨，<code>BB.-</code> 是上方地轨，<code>BB.G</code> 是下方地轨。每个数字列的 a～e 相通、f～j 相通，中槽两侧不通。DRV.GND-L1 是左排第3脚，DRV.GND-L2 是左排第8脚，DRV.GND-R 是右排第8脚；这三个脚通过模块内部连接共地。导线编号与图中提示、网络表一致。DRV.GND-L2 留空。</p><div class="table-scroll"><table><thead><tr><th>编号</th><th>怎么接</th><th>图内端点</th></tr></thead><tbody>ROWS</tbody></table></div><h3>四只电阻</h3><table><thead><tr><th>编号</th><th>阻值</th><th>两端插孔（无正反）</th></tr></thead><tbody>RESISTORS</tbody></table><p>GP4 接第26列分压点，GP5 接第28列分压点；黄 / 蓝线接10kΩ另一端。两只20kΩ都接下方地轨。程序保持 <code>pull_up=False</code>。</p></section>

<section><h2>接齐后，按命令分项测试</h2><ol><li><strong>断电检查：</strong>降压输出已空载调到5.0V；核对 P04 直接回电源负极，舵机红／棕线直连降压输出，全部设备共地。不放魔方，确认机械头及联动机构全程自由；首次舵机定位先脱开连杆，曲柄本身也要自由活动。</li><li><strong>Pico先接USB：</strong>运行 <code>import arm_test; arm_test.main()</code>，出现 <code>arm&gt;</code> 后输入 <code>off</code>。初始化时马达滑行、舵机 PWM 关闭；这只是软件不发命令，不能保证硬件上电不抖动。</li><li><strong>再打开9V：</strong>观察异常；马达或舵机自己转、发烫就切断动力电源（含舵机5V）。输入 <code>enc</code>，轻转机械头确认计数变化。确认无魔方、机构全程自由且供电接线已核验后，输入 <code>motor_test unloaded</code>；它只授权空载测试，不会自动转动。再按单臂说明执行 check、确认方向与齿轮比。off、异常、Ctrl+C、退出或重启都会撤销模式，继续前重新检查并声明；空载模式拒绝 load/cube 等带载测试及所有舵机开合预设。</li><li><strong>标定舵机：</strong>首次必须断电脱开连杆，使用 <code>servo_cal ... detached</code> 声明后才发基准脉冲；声明会话会停止马达与 PWM，并撤销空载马达模式。断电装接且核实轴标记、基准姿态和行程后，才用 aligned 会话小步标定；500～2500µs 只是驱动包络，不是机械安全区间，首次定位不受小步保护。端点与安全工作区间默认未设置，<code>SERVO_CALIBRATED=False</code>；手动会话或未完成标定时 open、close、grip、cycle 均拒绝，详见 <a href="../single_arm.md#servo-calibration">完整舵机标定流程</a>。</li><li><strong>先测完整开合时序：</strong>默认 <code>SERVO_MOVE_MS=None</code>、<code>SERVO_TIMING_CONFIRMED=False</code>。实测端点、安全工作区间并确认 v4/R 身份后，设置端点标定标志，自行选择保守的临时等待时间（1～5000ms整数，不能沿用旧120ms），上传并 Ctrl+D 重载。只单次 open 或 close，观察完全停稳才发下条，录像测完整行程；此时 grip、cycle 和普通旋转仍被锁住，显式空载马达模式是例外。</li><li><strong>旋转与联合测试：</strong>取开／合中较慢的实测时长加余量回填 <code>SERVO_MOVE_MS</code>，设置 <code>SERVO_TIMING_CONFIRMED=True</code>，重新上传并 Ctrl+D 重载后，再按 <a href="../single_arm.md#5-测试步骤">单臂测试第0～9步</a>继续。每步通过后再做下一步，无需反复插拔舵机；机构或供电改变后重新确认时序。</li></ol><p>大马达空载闭环已通过，见<a href="../single_arm-results.md">实测记录</a>；这不代表 v4 机械头、舵机标定或整机供电已经实测通过。</p></section>
<section><h2>可选排障：暂时隔离舵机</h2><p>只有排查复位、供电跌落或驱动异常时，才需要断开 USB 和9V后暂时拔下舵机，单独检查马达和编码器。P04 保持直接接电源负极。排障后断电接回舵机。</p></section>
<section><h2>依据</h2><ul><li><a href="https://www.lego.com/cdn/cs/set/assets/blt86e79bb287a0d0b1/Appendix_LEGO_MINDSTORMS_EV3_programmable_brick_main_hardware_schematics.pdf">LEGO 官方 EV3 原理图</a>：Output 1/2为动力端、3为地、4为5V、5/6为反馈。</li><li><a href="https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf">Raspberry Pi Pico 官方数据手册</a>：物理脚位与GPIO对应。</li><li><a href="https://www.ti.com/lit/ds/symlink/drv8833.pdf">TI DRV8833 数据手册</a>：输入控制逻辑；模块丝印排列使用用户实物确认结果。</li></ul></section></main>
<script>document.querySelectorAll('[data-filter]').forEach(b=>b.addEventListener('click',()=>{const k=b.dataset.filter;document.querySelectorAll('[data-filter]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',String(x===b))});document.querySelectorAll('.canvas [data-group]').forEach(x=>x.style.opacity=(k==='all'||x.dataset.group===k)?'1':'.1')}));document.querySelector('[data-filter="all"]').click();</script></html>'''
    page=page.replace("BUTTONS",buttons).replace("DRAWING",drawing).replace("ROWS",rows).replace("RESISTORS",resistor_rows)
    (directory/"direct-breadboard.html").write_text(page, encoding="utf-8")
    (directory/"direct-breadboard-netlist.json").write_text(json.dumps({"wires":WIRES,"resistors":RESISTORS,
        "internal_connections":[["DRV.GND-L1","DRV.GND-L2","DRV.GND-R"],["BUCK.IN−","BUCK.OUT−"]],
        "precondition":"降压模块 IN− 与 OUT− 内部共地；DRV8833 三个 GND 板内相通。"},ensure_ascii=False,indent=2)+"\n", encoding="utf-8")
    print(f"生成 direct-breadboard.html / .svg / -netlist.json；{len(WIRES)}根线、4只电阻，连通与孔位检查通过。")


if __name__=="__main__":
    main()
