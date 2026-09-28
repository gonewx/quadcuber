"""生成脱离洞洞板的单臂接线图。运行：python3 docs/wiring/direct_wiring.py。"""
from pathlib import Path
from html import escape
import json

HERE = Path(__file__).resolve().parent
COLORS = {"power": "#cf421f", "ground": "#344454", "control": "#167f74",
          "encoder": "#236ac2", "motor": "#8842ac"}
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
    PARTS.extend([text(985, 275, "OUT− 本轮留空", 18, bold=True),
                  text(985, 304, "先确认与 IN− 内部共地", 16)])
    PARTS.extend([text(1260, 200, "9V 总电源必须开：降压模块才有 5V", 21, bold=True),
                  text(1260, 230, "Pico 由 USB 供电；5V 轨不接 Pico 供电脚。", 17),
                  text(1260, 260, "DC-005 焊脚、降压焊盘均按实物标识确认。", 17),
                  text(1260, 288, "图示为功能位置，不是这两种元件的焊脚模板。", 16),
                  text(1260, 316, "不需要分线端子；舵机本轮不接。", 17, bold=True)])
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
    left = ["VM", "NC-L", "GND-L1", "AO1", "AO2", "BO2", "BO1", "GND-L2"]
    right = ["NC-R1", "AIN2", "AIN1", "STBY", "BIN1", "BIN2", "NC-R2", "GND-R"]
    for side, x, names in [("left", 240, left), ("right", 480, right)]:
        for i, name in enumerate(names):
            y = 620+i*50
            pin("DRV."+name, x, y)
            PARTS.append(rect(x-7, y-7, 14, 14, "#dac267", "#af9133", 1))
            label = name.split("-")[0]
            PARTS.append(text(x+(17 if side=="left" else -17), y+5, label, 17,
                              "white", "start" if side=="left" else "end", True))
    # 面包板：与旧图保持 c3…c22 / h3…h22 的 Pico 坐标。
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


def make_wires():
    wire("P03","power","DC.+9V","BUCK.IN+",[(300,230),(300,190)],"DC 正极第一根线 → 降压 IN+")
    wire("P04","ground","DRV.GND-L2","BUCK.IN−",[(90,970),(90,340),(650,340),(650,290)],"驱动左排第8脚 GND → 降压 IN−")
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
                ("BB.f26","BB.h8"),("BB.g28","BB.h9"),("EV3.1","DRV.AO1"),("EV3.2","DRV.AO2")]:
        assert root(a)==root(b),(a,b)
    independent=["DC.GND","DC.+9V","BUCK.OUT+","DRV.AIN1","DRV.AIN2","DRV.STBY",
                 "EV3.1","EV3.2","EV3.5","EV3.6","BB.h8","BB.h9"]
    assert len({root(k) for k in independent})==len(independent),"不应相连的网络发生短接"
    for _,a,b,_ in RESISTORS: assert root(a)!=root(b),"电阻被导线短接"
    # 不允许在同一个面包板孔里画两个线端/元件脚。
    used=[]
    for w in WIRES: used.extend(k for k in [w["start"],w["end"]] if k.startswith("BB."))
    for _,a,b,_ in RESISTORS: used.extend([a,b])
    assert len(used)==len(set(used)),"一个孔被多个引脚占用"


def svg():
    out=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1800 1430" role="img" aria-label="Pico 单臂面包板完整接线图，DRV8833动力直连">',
         '<style>text{font-family:"Noto Sans CJK SC","Microsoft YaHei",sans-serif}svg{background:#fffdf8} [data-group]{transition:opacity .15s}</style>',
         rect(0,0,1800,1430,"#fffdf8","none",0),text(40,52,"Pico 单臂验证 · 面包板＋动力直连",34,bold=True),
         text(40,87,"无洞洞板 / 无分线端子 · DRV8833 三个 GND 引出公共地 · 9V 保持给降压模块供电 · 舵机本轮不接",19)]
    out.extend(PARTS)
    for w in WIRES:
        points=[P[w["start"]],*w["bends"],P[w["end"]]]
        color=COLORS[w["group"]]; width=5 if w["code"] in ["P03","P04","P07","P08","M01","M02"] else 3.5
        out.append(f'<g data-group="{w["group"]}" data-wire="{w["code"]}"><title>{escape(w["code"]+": "+w["note"])}</title>'+path(points,"#fffdf8",width+3)+path(points,color,width)+dot(*points[0],color,4)+dot(*points[-1],color,4)+"</g>")
    out.extend(resistor_svg(*r) for r in RESISTORS)
    # 几个主要接点旁边的编号，详细端点见下方逐线表。
    for x,y,label,color in [(120,602,"P07 · 9V",COLORS["power"]),(195,746,"P08 · GND",COLORS["ground"]),
                            (25,1014,"P04 → IN−",COLORS["ground"]),(491,999,"P10 → 地轨",COLORS["ground"]),
                            (593,715,"C01",COLORS["control"]),(540,651,"C02",COLORS["control"]),
                            (611,757,"C03 · 3V3",COLORS["control"]),(1130,1120,"E03 · A",COLORS["encoder"]),
                            (1190,1110,"E04 · B",COLORS["encoder"])]:
        out.append(text(x,y,label,15,color,bold=True))
    out.append('</svg>')
    return "\n".join(out)


def main():
    P.clear(); PARTS.clear(); WIRES.clear()
    make_parts(); make_wires(); validate()
    drawing=svg()
    (HERE/"direct-breadboard.svg").write_text(drawing)
    rows="".join(f'<tr data-group="{w["group"]}"><td>{w["code"]}</td><td>{escape(w["note"])}</td><td>{escape(w["start"]+" → "+w["end"])}</td></tr>' for w in WIRES)
    resistor_rows="".join(f'<tr><td>{n}</td><td>{v//1000}kΩ</td><td>{a.replace("BB.","")} ↔ {b.replace("BB.","")}</td></tr>' for n,a,b,v in RESISTORS)
    buttons=''.join(f'<button data-filter="{k}" style="--c:{COLORS.get(k,"#183645")}">{label}</button>' for k,label in [("all","全部接线"),("power","9V / 5V"),("ground","公共地"),("control","驱动控制"),("encoder","编码器"),("motor","马达动力")])
    page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Pico 单臂 · 面包板直连接线图</title>
<style>*{box-sizing:border-box}body{margin:0;color:#243545;background:#f1f3f3;font:16px/1.65 system-ui,"Noto Sans CJK SC",sans-serif}main{max-width:1600px;margin:auto;padding:24px}h1{font-size:30px;line-height:1.3;margin:0 0 10px}h2{margin-top:0;font-size:23px}h3{font-size:19px}p{margin:8px 0 15px}.intro,section{background:white;border:1px solid #dbe0e2;border-radius:12px;padding:24px;margin-bottom:20px}.lead{font-size:18px}.status{background:#fff4d6;border-left:5px solid #c7951c;padding:12px 16px}.controls{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0}.controls button{cursor:pointer;padding:9px 16px;border:1px solid var(--c);border-radius:7px;background:white;color:var(--c);font:inherit}.controls button.active{background:var(--c);color:white}.canvas{overflow:auto;background:#fffdf8;border:1px solid #ddd;border-radius:8px}.canvas svg{display:block;width:100%;min-width:1150px;height:auto}.links{display:flex;gap:20px;flex-wrap:wrap}a{color:#1467a4}table{border-collapse:collapse;width:100%;font-size:15px}th,td{text-align:left;padding:9px 12px;border-bottom:1px solid #e0e5e7}th{background:#edf2f4}.table-scroll{overflow:auto}code,pre{font-family:ui-monospace,monospace}pre{background:#f0f4f5;padding:16px;overflow:auto}.grid{display:grid;grid-template-columns:1fr 1fr;gap:24px}.small{font-size:14px;color:#586976}.servo{background:#faf8f0;border-left:5px solid #b7a477;padding:18px}.servo svg{width:100%;max-width:700px}.state{font-size:13px;letter-spacing:.05em;color:#14766b;font-weight:700}li{margin:7px 0}button:focus-visible,a:focus-visible{outline:3px solid #f2b94d;outline-offset:3px}@media(max-width:760px){main{padding:12px}.intro,section{padding:16px}.grid{grid-template-columns:1fr}h1{font-size:25px}}@media print{.controls{display:none}main{max-width:none;padding:0}.canvas svg{min-width:0}.intro,section{break-inside:avoid;border:0}.canvas{overflow:visible}body{background:white}}</style>
<main><div class="intro"><div class="state">当前阶段：验证 Pico＋DRV8833 单臂</div><h1>面包板接信号，动力线直接连接</h1><p class="lead">按图里的元件朝向和孔位接线。DRV8833 放在面包板旁边，使用母头线接模块排针；本图不使用洞洞板、分线端子或 Bricktronics。DC-005 正极直接引出两根线，三个公共地分支利用 DRV8833 的三个 GND 脚连接。</p><p class="status"><strong>9V 总电源关掉，编码器也会失去 5V。</strong> 手动计数时保持编码器供电，并先将 GP2、GP3 都置低。DRV8833 当前输出故障尚未排除，本图是核对与搭建方案，不代表已通过电动测试。</p><div class="links"><a href="direct-breadboard.svg" target="_blank">打开 SVG 大图</a><a href="direct-breadboard.png" target="_blank">打开 PNG 图片</a><a href="perfboard.html">原洞洞板方案</a></div></div>
<section><h2>完整接线图</h2><p>点按钮突出显示一组线；悬停导线可看编号。手机上横向拖动查看。交叉线没有圆点就不连接。</p><div class="controls">BUTTONS</div><div class="canvas">DRAWING</div><p class="small">面包板沿用原图坐标：Pico 两排插在 c3～c22、h3～h22，USB 朝左。电阻位置沿用旧图。面包板实际通常超过40列，此处仅画使用区域；两半电源轨用图中的短跳线接通。未用的另一条正电源轨省略。</p></section>
<section><h2>先看清这些实物连接</h2><div class="grid"><div><h3>不用让动力电流经过面包板</h3><ul><li>9V → VM、驱动 GND → 电源负极，以及 AO1 / AO2 → 马达，全部用独立导线直接连接模块；马达加工线用现有普通接线端子转接。</li><li>模块公排针接母头线端，端子夹持对应线材；动力线和线端额定电流需满足马达启动电流，普通细杜邦跳线只用于信号。</li><li>DRV8833 放在绝缘面并固定，底部引脚不要碰金属或彼此短接。模块不需要焊死。</li><li>DC-005 正极焊脚引出两根线，分别接 VM 与降压 IN+，焊点用热缩管等绝缘；负极直接接 DRV8833 左排第3脚 GND。模块端仍用母头插接。</li></ul></div><div><h3>使用现有配件</h3><ul><li>9V 电源、DC-005、已有降压模块，输出调到 5.0V。此接法要求降压 IN− 与 OUT− 内部共地，确认后 OUT− 本轮不接外线。</li><li>Pico、DRV8833、面包板、两只10kΩ与两只20kΩ。</li><li>已修复/重新制作的 EV3 线；散铜丝先接端子，再转成面包板公头线。</li><li>本图不额外加电容；保留模块自带电容。降压模块不要求螺钉或支柱，避免裸露焊盘接触导体即可。</li></ul></div></div><p><strong>朝向说明：</strong>DRV8833 元件面朝上，左排从上到下为 VM、NC、GND、AO1、AO2、BO2、BO1、GND；右排为 NC、AIN2、AIN1、STBY、BIN1、BIN2、NC、GND。与你提供的丝印一致。DC-005 的三个焊脚形状和降压模块尺寸未确认，图中只标功能，不猜焊脚顺序；DC-005 切换脚留空绝缘。</p></section>
<section><h2>面包板孔位与每根线</h2><p><code>BB.+</code> 是上方5V轨，<code>BB.-</code> 是上方地轨，<code>BB.G</code> 是下方地轨。每个数字列的 a～e 相通、f～j 相通，中槽两侧不通。DRV.GND-L1 是左排第3脚，DRV.GND-L2 是左排第8脚，DRV.GND-R 是右排第8脚；这三个脚通过模块内部连接共地。电源线编号沿用旧图，删去分线端子后不再连续。</p><div class="table-scroll"><table><thead><tr><th>编号</th><th>怎么接</th><th>图内端点</th></tr></thead><tbody>ROWS</tbody></table></div><h3>四只电阻</h3><table><thead><tr><th>编号</th><th>阻值</th><th>两端插孔（无正反）</th></tr></thead><tbody>RESISTORS</tbody></table><p>GP4 接第26列分压点，GP5 接第28列分压点；黄 / 蓝线接10kΩ另一端。两只20kΩ都接下方地轨。程序保持 <code>pull_up=False</code>。</p></section>
<section class="servo"><h2>第二阶段：舵机接法（本轮不接）</h2><p>先完成马达测试。以后接舵机时，断电将 P04 接在 DRV8833 上的一端移到 DC-005 负极焊脚，与 P08 共用该焊点；降压 IN− 的另一端不动。这样舵机的回流直接回电源，不经过 DRV8833 的地脚。三孔母插头按棕／红／黄顺序配公针线端。</p><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 190" role="img" aria-label="舵机棕线接公共地，红线接降压5V，黄线接Pico GP8"><rect x="20" y="40" width="180" height="120" rx="10" fill="#c4c7ca" stroke="#67717a"/><rect x="170" y="76" width="45" height="44" fill="#666"/><text x="45" y="105" font-size="22" fill="#243545">Geekservo</text><path d="M215 83 H445" stroke="#845738" stroke-width="7"/><path d="M215 103 H445" stroke="#c83332" stroke-width="7"/><path d="M215 123 H445" stroke="#d5ab19" stroke-width="7"/><text x="460" y="89" font-size="18" fill="#243545">棕 → 降压 OUT−</text><text x="460" y="111" font-size="18" fill="#243545">红 → 降压 OUT+（并接引线）</text><text x="460" y="139" font-size="18" fill="#243545">黄 → 面包板 j13（GP8，物理11脚）</text></svg><p>降压 OUT+ 原有一根线接面包板，再引出一根接舵机红线；可在同一焊盘制作两根引线并绝缘，舵机端保留插拔。棕线直接回 OUT−。不使用分线端子，不从面包板电源轨取舵机电流。USB 不给舵机供电。</p></section>
<section><h2>按这个顺序上电</h2><ol><li><strong>断电接线：</strong>关闭9V并拔掉USB，按图接好，舵机暂时不接。先测驱动空载输出时，马达动力两线先留空；VM、5V和公共地照图保留。</li><li><strong>Pico先接USB：</strong>进入 REPL，软重启后先输入下面的停止驱动代码。</li><li><strong>再打开9V：</strong>编码器得到降压模块的5V。手转测试使用GP4、GP5；转动之前创建 <code>Encoder</code>。</li><li><strong>驱动空载输出恢复后：</strong>断电接回马达动力线，轴空载。关闭9V，USB运行 <code>import arm_test; arm_test.main()</code>；出现 <code>arm&gt;</code> 后打开9V，再输入 <code>check</code>。方向通过后才进行闭环测试。</li></ol><pre>from machine import Pin
in1 = Pin(2, Pin.OUT, value=0)
in2 = Pin(3, Pin.OUT, value=0)

# 打开9V后，手动计数：
from encoder import Encoder
enc = Encoder(4, 5, (0, 1), pull_up=False)
print(enc.count())</pre><p class="small">编码器软件已在本次会话中通过手动双向计数；这张新布局未在实物上搭建验收。连接器和导线需满足负载电流，单臂结果不能替代四臂同时启动验证。</p></section>
<section><h2>依据</h2><ul><li><a href="https://www.lego.com/cdn/cs/set/assets/blt86e79bb287a0d0b1/Appendix_LEGO_MINDSTORMS_EV3_programmable_brick_main_hardware_schematics.pdf">LEGO 官方 EV3 原理图</a>：Output 1/2为动力端、3为地、4为5V、5/6为反馈。</li><li><a href="https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf">Raspberry Pi Pico 官方数据手册</a>：物理脚位与GPIO对应。</li><li><a href="https://www.ti.com/lit/ds/symlink/drv8833.pdf">TI DRV8833 数据手册</a>：输入控制逻辑；模块丝印排列使用用户实物确认结果。</li></ul></section></main>
<script>document.querySelectorAll('[data-filter]').forEach(b=>b.addEventListener('click',()=>{const k=b.dataset.filter;document.querySelectorAll('[data-filter]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',String(x===b))});document.querySelectorAll('.canvas [data-group]').forEach(x=>x.style.opacity=(k==='all'||x.dataset.group===k)?'1':'.1')}));document.querySelector('[data-filter="all"]').click();</script></html>'''
    page=page.replace("BUTTONS",buttons).replace("DRAWING",drawing).replace("ROWS",rows).replace("RESISTORS",resistor_rows)
    (HERE/"direct-breadboard.html").write_text(page)
    (HERE/"direct-breadboard-netlist.json").write_text(json.dumps({"wires":WIRES,"resistors":RESISTORS,
        "internal_connections":[["DRV.GND-L1","DRV.GND-L2","DRV.GND-R"],["BUCK.IN−","BUCK.OUT−"]],
        "precondition":"降压模块 IN− 与 OUT− 内部共地；DRV8833 三个 GND 板内相通。"},ensure_ascii=False,indent=2)+"\n")
    print(f"生成 direct-breadboard.html / .svg / -netlist.json；{len(WIRES)}根线、4只电阻，连通与孔位检查通过。")


if __name__=="__main__":
    main()
