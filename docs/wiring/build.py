"""生成单臂原型的图解接线指南: docs/wiring/index.html (纯 HTML + 内嵌 SVG, 无外部图片)。

    python docs/wiring/build.py

引脚分配以 firmware/pico/config.py 为准 (R 臂): GP2/GP3 马达, GP4/GP5 编码器, GP8 舵机。
洞洞板图由 perfboard_layout.py 按孔位生成，同时生成可独立打开的 perfboard.html。
详细接线见 ../perfboard.md。
"""

import html
import argparse
from pathlib import Path
from tempfile import TemporaryDirectory
import spec
import perfboard_layout
import direct_wiring

HERE = Path(__file__).resolve().parent

# ---- 通用绘图 -------------------------------------------------------------------


def wire(group, cls, pts, label=None, label_at=None, hop=None, anchor="start"):
    """折线导线。hop: 在该点画一个跨线的小半圆 (表示不相连)。"""
    d = f"M{pts[0][0]} {pts[0][1]}"
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if hop and x0 == x1 == hop[0] and min(y0, y1) < hop[1] < max(y0, y1):
            s = 1 if y1 > y0 else -1
            d += f" L{x0} {hop[1] - 6 * s} A6 6 0 0 {1 if s < 0 else 0} {x0} {hop[1] + 6 * s}"
        d += f" L{x1} {y1}"
    out = f'<g class="wire" data-g="{group}"><path class="w {cls}" d="{d}"/>'
    for x, y in (pts[0], pts[-1]):
        out += f'<circle class="dot {cls}" cx="{x}" cy="{y}" r="3.2"/>'
    if label:
        lx, ly = label_at
        out += f'<text class="wl {cls}t" x="{lx}" y="{ly}" text-anchor="{anchor}">{label}</text>'
    return out + "</g>"


def junction(group, cls, x, y):
    return f'<g class="wire" data-g="{group}"><circle class="dot {cls}" cx="{x}" cy="{y}" r="4"/></g>'


def ground(x, y, direction="down", label=True):
    """接地符号: 从 (x, y) 引出一小段线, 末端画三条递减横线。"""
    if direction == "down":
        stub = f'<line class="g" x1="{x}" y1="{y}" x2="{x}" y2="{y + 10}"/>'
        bars = "".join(f'<line class="g" x1="{x - w}" y1="{y + 10 + i * 4}" x2="{x + w}" y2="{y + 10 + i * 4}"/>'
                       for i, w in enumerate((9, 6, 3)))
        txt = f'<text class="gl" x="{x + 13}" y="{y + 20}">GND</text>' if label else ""
    elif direction == "left":
        stub = f'<line class="g" x1="{x}" y1="{y}" x2="{x - 12}" y2="{y}"/>'
        bars = "".join(f'<line class="g" x1="{x - 12 - i * 4}" y1="{y - w}" x2="{x - 12 - i * 4}" y2="{y + w}"/>'
                       for i, w in enumerate((9, 6, 3)))
        txt = f'<text class="gl" x="{x - 30}" y="{y + 4}" text-anchor="end">GND</text>' if label else ""
    else:  # right
        stub = f'<line class="g" x1="{x}" y1="{y}" x2="{x + 12}" y2="{y}"/>'
        bars = "".join(f'<line class="g" x1="{x + 12 + i * 4}" y1="{y - w}" x2="{x + 12 + i * 4}" y2="{y + w}"/>'
                       for i, w in enumerate((9, 6, 3)))
        txt = f'<text class="gl" x="{x + 30}" y="{y + 4}">GND</text>' if label else ""
    return f'<g class="wire" data-g="gnd">{stub}{bars}{txt}</g>'


def resistor(x, y, text, vertical=False, label_at=None, anchor="middle"):
    """画在导线上的电阻 (导线另画, 电阻体盖在上面)。(x, y) 是电阻体中心。"""
    w, h = (10, 36) if vertical else (36, 10)
    s = f'<rect class="rb" x="{x - w / 2}" y="{y - h / 2}" width="{w}" height="{h}" rx="3"/>'
    lx, ly = label_at or ((x + 10, y + 4) if vertical else (x, y - 9))
    return s + f'<text class="rl" x="{lx}" y="{ly}" text-anchor="{anchor}">{text}</text>'


def box(x, y, w, h, title, sub=None, cls="part"):
    s = f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="6"/>'
    s += f'<text class="pt" x="{x + w / 2}" y="{y + 18}" text-anchor="middle">{title}</text>'
    if sub:
        s += f'<text class="ps" x="{x + w / 2}" y="{y + 33}" text-anchor="middle">{sub}</text>'
    return s


def pin_label(x, y, text, side):
    """模块内侧的引脚名。side: 引脚在模块的哪条边。"""
    if side == "left":
        return f'<text class="pn" x="{x + 7}" y="{y + 4}">{text}</text>'
    if side == "right":
        return f'<text class="pn" x="{x - 7}" y="{y + 4}" text-anchor="end">{text}</text>'
    if side == "top":
        return f'<text class="pn" x="{x}" y="{y + 15}" text-anchor="middle">{text}</text>'
    return f'<text class="pn" x="{x}" y="{y - 7}" text-anchor="middle">{text}</text>'


# ---- 完整接线图 -----------------------------------------------------------------

def pico_pin_y(n):
    """Pico 引脚纵坐标: 左边 1~20 自上而下, 右边 40~21 自上而下。"""
    return 190 + (n - 1) * 20 if n <= 20 else 190 + (40 - n) * 20


PICO_LEFT = {1: "GP0", 2: "GP1", 3: "GND", 4: "GP2", 5: "GP3", 6: "GP4", 7: "GP5", 8: "GND", 9: "GP6", 10: "GP7",
             11: "GP8", 12: "GP9", 13: "GND", 14: "GP10", 15: "GP11", 16: "GP12", 17: "GP13", 18: "GND", 19: "GP14",
             20: "GP15"}
PICO_RIGHT = {40: "VBUS", 39: "VSYS", 38: "GND", 37: "3V3_EN", 36: "3V3", 35: "VREF", 34: "GP28", 33: "GND",
              32: "GP27", 31: "GP26", 30: "RUN", 29: "GP22", 28: "GND", 27: "GP21", 26: "GP20", 25: "GP19",
              24: "GP18", 23: "GND", 22: "GP17", 21: "GP16"}
USED = {4: "wc", 5: "wc", 6: "we", 7: "we", 11: "ws", 36: "w33", 38: "gnd"}


def wiring_svg():
    s = []
    # 电源
    s.append(box(60, 24, 130, 52, "9V 电源", "18650 升压 / PD 诱骗"))
    s.append(box(270, 24, 150, 52, "5V 降压模块", "输出 ≥ 3A"))
    s.append(pin_label(190, 40, "+", "right"))
    s.append(pin_label(270, 40, "IN+", "left"))
    s.append(pin_label(420, 40, "OUT+", "right"))
    s.append(ground(125, 76))
    s.append(ground(345, 76))
    # EV3 马达接头
    s.append(box(70, 160, 160, 166, "EV3 马达", "6 芯线"))
    ev3 = [(1, "白", "M1"), (2, "黑", "M2"), (3, "红", "GND"), (4, "绿", "5V"), (5, "黄", "A相"), (6, "蓝", "B相")]
    for i, (n, color, fn) in enumerate(ev3):
        y = 210 + i * 20
        s.append(f'<text class="pn" x="78" y="{y + 4}">{n} {color}</text>')
        s.append(f'<text class="pn" x="222" y="{y + 4}" text-anchor="end">{fn}</text>')
    # DRV8833
    s.append(box(480, 180, 140, 100, "DRV8833", "只用 A 路"))
    for y, t in ((210, "AOUT1"), (230, "AOUT2")):
        s.append(pin_label(480, y, t, "left"))
    for y, t in ((250, "AIN1"), (270, "AIN2")):
        s.append(pin_label(620, y, t, "right"))
    s.append(pin_label(496, 180, "VM", "top"))
    s.append(pin_label(600, 180, "STBY", "top"))
    s.append(f'<text class="note" x="626" y="204">STBY (nSLEEP) 接 3.3V</text>')
    s.append(f'<text class="note" x="626" y="218">使能驱动</text>')
    s.append(ground(480, 262, "left", label=False))
    # 编码器分压: 每路 10k 串联 + 20k 下拉
    s.append(f'<text class="note" x="300" y="470">每路两个电阻分压: 5V 信号 → 约 3V</text>')
    # 舵机
    s.append(box(480, 580, 140, 60, "Geekservo", "灰色 270°"))
    s.append(pin_label(530, 580, "", "top"))
    s.append(f'<text class="pn" x="538" y="574">V+</text>')
    s.append(f'<text class="pn" x="626" y="596">信号</text>')
    s.append(ground(480, 612, "left"))
    # Pico
    s.append('<rect class="usb" x="792" y="144" width="56" height="18" rx="3"/>')
    s.append('<text class="ps" x="820" y="138" text-anchor="middle">USB (调试时供电)</text>')
    s.append('<rect class="pico" x="760" y="160" width="120" height="430" rx="8"/>')
    s.append('<text class="pt ob" x="820" y="476" text-anchor="middle">Pico</text>')
    s.append('<text class="ps ob" x="820" y="492" text-anchor="middle">正面朝上</text>')
    for n in range(1, 41):
        x = 760 if n <= 20 else 880
        y = pico_pin_y(n)
        cls = "pin used" if n in USED else "pin"
        s.append(f'<circle class="{cls}" cx="{x}" cy="{y}" r="4"/>')
        name = PICO_LEFT.get(n) or PICO_RIGHT.get(n)
        if n in USED:
            if n <= 20:
                s.append(f'<text class="pu" x="{x + 9}" y="{y + 4}">{name} ({n})</text>')
            else:
                # 同一行左边也有用到的脚时, 右边只写名字, 避免两个标签挤在一起
                text = name if (41 - n) in USED else f"{name} ({n})"
                s.append(f'<text class="pu" x="{x - 9}" y="{y + 4}" text-anchor="end">{text}</text>')
    s.append(ground(880, pico_pin_y(38), "right"))

    # ---- 导线 ----
    s.append(wire("p9", "w9", [(190, 40), (270, 40)], "9V", (212, 33)))
    s.append(wire("p9", "w9", [(230, 40), (230, 120), (496, 120), (496, 180)]))
    s.append(junction("p9", "w9", 230, 40))
    s.append(wire("p5", "w5", [(420, 40), (440, 40), (440, 150), (40, 150), (40, 540), (530, 540), (530, 580)],
                  "5V", (446, 70)))
    s.append(wire("p5", "w5", [(70, 270), (40, 270)]))
    s.append(junction("p5", "w5", 40, 270))
    s.append(wire("p33", "w33", [(880, 270), (940, 270), (940, 110), (600, 110), (600, 180)], "3.3V", (760, 104)))
    # EV3 1/2 -> DRV8833 AOUT
    s.append(wire("motor", "wm", [(230, 210), (480, 210)], "M1", (330, 204)))
    s.append(wire("motor", "wm", [(230, 230), (480, 230)], "M2", (330, 225)))
    # EV3 3 -> 地
    s.append(ground(230, 250, "right", label=False))
    # EV3 5/6 -> 10k -> 分压点 (20k 到地) -> GP4/GP5
    s.append(wire("enc", "we", [(230, 290), (760, 290)], "≈3V", (720, 284), anchor="middle"))
    s.append(wire("enc", "we", [(230, 310), (760, 310)], "≈3V", (720, 326), anchor="middle"))
    s.append(wire("enc", "we", [(430, 290), (430, 420)], hop=(430, 310)))
    s.append(wire("enc", "we", [(470, 310), (470, 420)]))
    s.append(junction("enc", "we", 430, 290))
    s.append(junction("enc", "we", 470, 310))
    s.append('<g class="wire" data-g="enc">' + resistor(360, 290, "10kΩ") + resistor(360, 310, "10kΩ", label_at=(360, 328))
             + resistor(430, 380, "20kΩ", True, (422, 384), "end") + resistor(470, 380, "20kΩ", True) + "</g>")
    s.append(f'<text class="wl wet" x="262" y="284" text-anchor="middle">5V</text>')
    s.append(ground(430, 420, label=False))
    s.append(ground(470, 420, label=False))
    # Pico -> DRV8833
    s.append(wire("ctrl", "wc", [(760, 250), (620, 250)], "PWM", (690, 244), anchor="middle"))
    s.append(wire("ctrl", "wc", [(760, 270), (620, 270)]))
    # Pico -> 舵机
    s.append(wire("servo", "ws", [(760, 390), (720, 390), (720, 600), (620, 600)], "舵机信号", (712, 520), anchor="end"))
    return ('<svg class="diagram" viewBox="0 0 980 680" role="img" aria-label="单臂原型完整接线图: 9V 供给 DRV8833 和 5V 降压模块; '
            '5V 供给舵机和编码器; Pico 的 3.3V 接 DRV8833 STBY; GP2/GP3 控制 DRV8833, '
            'DRV8833 输出驱动 EV3 马达; 编码器 A/B 相各经 10k 串联、20k 下拉分压后接 GP4/GP5; GP8 接舵机信号。">'
            + "".join(s) + "</svg>")


# ---- 总览图 ---------------------------------------------------------------------

def overview_svg():
    s = []

    def node(x, y, w, t, sub, cls="part"):
        s.append(f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="46" rx="6"/>')
        s.append(f'<text class="pt" x="{x + w / 2}" y="{y + 20}" text-anchor="middle">{t}</text>')
        s.append(f'<text class="ps" x="{x + w / 2}" y="{y + 36}" text-anchor="middle">{sub}</text>')

    def arrow(cls, pts, label=None, at=None, anchor="middle"):
        d = "M" + " L".join(f"{x} {y}" for x, y in pts)
        s.append(f'<path class="w {cls}" d="{d}" marker-end="url(#ah-{cls})"/>')
        if label:
            s.append(f'<text class="wl {cls}t" x="{at[0]}" y="{at[1]}" text-anchor="{anchor}">{label}</text>')

    defs = "".join(f'<marker id="ah-{c}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
                   f'orient="auto-start-reverse"><path class="ah {c}f" d="M0 0 L10 5 L0 10 z"/></marker>'
                   for c in ("w9", "w5", "w33", "wc", "wm", "we", "ws"))
    s.append(f"<defs>{defs}</defs>")
    # 第一行: 电源
    node(20, 20, 130, "9V 电源", "≤ 10.8V")
    node(240, 20, 150, "5V 降压", "≥ 3A")
    node(20, 250, 130, "电脑 USB", "调试时")
    # 第二行: 模块
    node(240, 130, 150, "DRV8833", "马达驱动")
    node(480, 130, 150, "EV3 马达", "转动机械手")
    node(480, 20, 150, "Geekservo", "夹爪开合")
    node(480, 250, 150, "分压电阻", "10k + 20k ×2")
    node(240, 250, 150, "Pico", "实时控制")
    arrow("w9", [(150, 43), (240, 43)], "9V", (195, 37))
    arrow("w9", [(85, 66), (85, 153), (240, 153)], "9V", (100, 145), "start")
    arrow("w5", [(390, 36), (480, 36)], "5V", (435, 30))
    arrow("w5", [(315, 66), (315, 100), (700, 100), (700, 180), (630, 180)], "5V 编码器电源", (655, 94))
    arrow("wm", [(390, 153), (480, 153)], "M1 / M2", (435, 147))
    arrow("we", [(555, 176), (555, 250)], "A/B 相 5V", (561, 218), "start")
    arrow("we", [(480, 273), (390, 273)], "A/B 相 ≈3V", (435, 291))
    arrow("wc", [(300, 250), (300, 176)], "GP2/GP3 PWM", (306, 218), "start")
    arrow("ws", [(360, 250), (360, 210), (440, 210), (440, 56), (480, 56)], "GP8 信号", (446, 200), "start")
    arrow("w5", [(150, 273), (240, 273)], "5V", (195, 267))
    return ('<svg class="diagram" viewBox="0 0 760 320" role="img" aria-label="系统总览: 9V 电源供给马达驱动和 5V 降压; 5V 供给舵机、'
            '编码器; Pico 由 USB 供电, 通过 PWM 控制马达驱动, 经电阻分压读取编码器, 直接控制舵机。">'
            + "".join(s) + "</svg>")


# ---- Pico 引脚图 ------------------------------------------------------------------

PIN_ROLE = {4: ("wc", "马达 AIN1"), 5: ("wc", "马达 AIN2"), 6: ("we", "编码器 A"), 7: ("we", "编码器 B"),
            11: ("ws", "舵机信号"), 36: ("w33", "DRV8833 STBY"), 38: ("gnd", "公共地"), 3: ("gnd", "(也可接地)"),
            1: ("later", "UART→Zero"), 2: ("later", "UART←Zero")}


def pinout_svg():
    s = ['<rect class="usb" x="236" y="16" width="48" height="18" rx="3"/>',
         '<rect class="pico" x="200" y="32" width="120" height="420" rx="8"/>',
         '<text class="pt" x="260" y="236" text-anchor="middle">Pico</text>',
         '<text class="ps" x="260" y="252" text-anchor="middle">正面 · USB 朝上</text>']
    for n in range(1, 41):
        left = n <= 20
        x = 200 if left else 320
        y = 52 + ((n - 1) if left else (40 - n)) * 20
        name = PICO_LEFT.get(n) or PICO_RIGHT.get(n)
        role = PIN_ROLE.get(n)
        cls = "pin"
        if role and role[0] not in ("later",):
            cls = f"pin on {role[0]}"
        s.append(f'<circle class="{cls}" cx="{x}" cy="{y}" r="5"/>')
        num_x = x + 12 if left else x - 12
        s.append(f'<text class="pnum" x="{num_x}" y="{y + 4}" text-anchor="{"start" if left else "end"}">{n}</text>')
        name_x = x - 12 if left else x + 12
        s.append(f'<text class="pname{" on" if role and role[0] != "later" else ""}" x="{name_x}" y="{y + 4}" '
                 f'text-anchor="{"end" if left else "start"}">{name}</text>')
        if role:
            rx = x - 62 if left else x + 62
            s.append(f'<text class="prole {role[0]}t" x="{rx}" y="{y + 4}" text-anchor="{"end" if left else "start"}">'
                     f'{role[1]}</text>')
    return ('<svg class="diagram pinout" viewBox="0 0 520 470" role="img" aria-label="Pico 引脚图, 正面朝上 USB 在上: '
            '单臂原型用到 4 号脚 GP2、5 号脚 GP3 (马达), 6 号脚 GP4、7 号脚 GP5 (编码器), 11 号脚 GP8 (舵机), '
            '36 号脚 3V3 (接 DRV8833 STBY) 和 38 号脚 GND。">' + "".join(s) + "</svg>")


# ---- 页面 -------------------------------------------------------------------------

CSS = """
:root{
  --bg:#f3f4f1; --sheet:#ffffff; --ink:#1c232b; --muted:#5d6874; --line:#d5dad3; --panel:#fbfbf8;
  --board:#1f6f4a; --board-ink:#eaf4ee;
  --c9:#e8590c; --c5:#d6336c; --c33:#e0a100; --cm:#8f3fbf; --cc:#2b9348; --ce:#1c7ed6; --cs:#0b8a8f;
  --warn:#a15c00; --warn-bg:#fff3dd; --danger:#b42318; --danger-bg:#fde8e6; --ok:#1f7a45;
  --bb:#f4f2ea; --bbch:#e2dfd3; --hole:#a9a596;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    color-scheme:dark;
    --bg:#12161b; --sheet:#1a2027; --ink:#e3e9ef; --muted:#9aa6b2; --line:#2e3740; --panel:#20272f;
    --board:#1d5a3e; --board-ink:#dcefe4;
    --c9:#ff8a3d; --c5:#f06595; --c33:#ffd43b; --cm:#c77dff; --cc:#51cf66; --ce:#4dabf7; --cs:#3bc9db;
    --warn:#ffc261; --warn-bg:#2f2615; --danger:#ff8a80; --danger-bg:#34191a; --ok:#69db7c;
    --bb:#2a2f36; --bbch:#20242a; --hole:#5f6770;
  }
}
:root[data-theme="dark"]{
  color-scheme:dark;
  --bg:#12161b; --sheet:#1a2027; --ink:#e3e9ef; --muted:#9aa6b2; --line:#2e3740; --panel:#20272f;
  --board:#1d5a3e; --board-ink:#dcefe4;
  --c9:#ff8a3d; --c5:#f06595; --c33:#ffd43b; --cm:#c77dff; --cc:#51cf66; --ce:#4dabf7; --cs:#3bc9db;
  --warn:#ffc261; --warn-bg:#2f2615; --danger:#ff8a80; --danger-bg:#34191a; --ok:#69db7c;
  --bb:#2a2f36; --bbch:#20242a; --hole:#5f6770;
}
body{background:var(--bg);color:var(--ink);font-family:"Noto Sans SC","PingFang SC","Microsoft YaHei",system-ui,sans-serif;
  font-size:15px;line-height:1.65;padding-inline:16px;padding-block:24px 64px}
.wrap{max-width:1000px;margin:0 auto;display:flex;flex-direction:column;gap:30px}
h1,h2,h3{margin:0;line-height:1.25;text-wrap:balance}
h1{font-size:28px}
h2{font-size:21px}
h3{font-size:16px}
p{margin:0;max-width:68ch}
.eyebrow{font-family:"Barlow Condensed","Arial Narrow",sans-serif;font-weight:600;letter-spacing:.08em;text-transform:uppercase;
  color:var(--muted);font-size:14px}
section{display:flex;flex-direction:column;gap:12px}
.card{background:var(--sheet);border:1px solid var(--line);border-radius:8px;padding:14px}
.rules{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px}
.rule{background:var(--danger-bg);border-left:4px solid var(--danger);border-radius:4px;padding:10px 12px}
.rule b{display:block;color:var(--danger)}
figure{margin:0;display:flex;flex-direction:column;gap:8px}
figcaption{font-size:13px;color:var(--muted);max-width:75ch}
.scroll{overflow-x:auto;background:var(--sheet);border:1px solid var(--line);border-radius:8px;padding:8px}
.diagram{display:block;width:100%;min-width:640px;height:auto;color:var(--ink);font-family:"JetBrains Mono",ui-monospace,monospace}
.pinout{min-width:460px;max-width:620px;margin:0 auto}
.part{fill:var(--panel);stroke:currentColor;stroke-width:1.4}
.pico{fill:var(--board);stroke:none}
.usb{fill:#b8bfc6;stroke:none}
.pt{font-family:"Noto Sans SC",sans-serif;font-size:14px;font-weight:700;fill:currentColor}
.pt.ob,.pinout .pt{fill:var(--board-ink)}
.ps{font-family:"Noto Sans SC",sans-serif;font-size:11px;fill:var(--muted)}
.pinout .ps{fill:var(--board-ink);opacity:.8}
.pn{font-size:11px;fill:currentColor}
.pu{font-size:11px;fill:var(--board-ink);font-weight:700}
.note{font-family:"Noto Sans SC",sans-serif;font-size:11px;fill:var(--muted)}
.side{font-family:"Noto Sans SC",sans-serif;font-size:10.5px;fill:var(--muted)}
.pin{fill:#d9dee2;stroke:#4a555f;stroke-width:1}
.pin.used{fill:#fff;stroke:#fff;stroke-width:2}
.w{fill:none;stroke-width:3;stroke-linejoin:round;stroke-linecap:round}
.w9{stroke:var(--c9)} .w5{stroke:var(--c5)} .w33{stroke:var(--c33)} .wm{stroke:var(--cm)} .wc{stroke:var(--cc)}
.we{stroke:var(--ce)} .ws{stroke:var(--cs)}
.dot.w9{fill:var(--c9)} .dot.w5{fill:var(--c5)} .dot.w33{fill:var(--c33)} .dot.wm{fill:var(--cm)} .dot.wc{fill:var(--cc)}
.dot.we{fill:var(--ce)} .dot.ws{fill:var(--cs)}
.dot{stroke:none}
.w9f{fill:var(--c9)} .w5f{fill:var(--c5)} .w33f{fill:var(--c33)} .wmf{fill:var(--cm)} .wcf{fill:var(--cc)} .wef{fill:var(--ce)} .wsf{fill:var(--cs)}
.wl{font-family:"Noto Sans SC",sans-serif;font-size:11.5px;font-weight:700;paint-order:stroke;stroke:var(--sheet);stroke-width:4px;stroke-linejoin:round}
.w9t{fill:var(--c9)} .w5t{fill:var(--c5)} .w33t{fill:var(--c33)} .wmt{fill:var(--cm)} .wct{fill:var(--cc)} .wet{fill:var(--ce)} .wst{fill:var(--cs)}
.g{stroke:currentColor;stroke-width:2;fill:none}
.gl{font-size:10px;fill:var(--muted)}
.cap{stroke:currentColor;stroke-width:2.5}
.wire{transition:opacity .2s}
.filtered .wire{opacity:.1}
.filtered[data-show~="p9"] .wire[data-g="p9"],.filtered[data-show~="p5"] .wire[data-g="p5"],
.filtered[data-show~="p33"] .wire[data-g="p33"],.filtered[data-show~="gnd"] .wire[data-g="gnd"],
.filtered[data-show~="motor"] .wire[data-g="motor"],.filtered[data-show~="ctrl"] .wire[data-g="ctrl"],
.filtered[data-show~="enc"] .wire[data-g="enc"],.filtered[data-show~="servo"] .wire[data-g="servo"]{opacity:1}
@media (prefers-reduced-motion: reduce){.wire{transition:none}}
.filters{display:flex;flex-wrap:wrap;gap:6px}
.filters button{font:inherit;font-size:13px;border:1px solid var(--line);background:var(--sheet);color:var(--ink);
  border-radius:16px;padding:4px 12px;cursor:pointer;display:inline-flex;align-items:center;gap:6px}
.filters button[aria-pressed="true"]{border-color:var(--ink);font-weight:700}
.filters button:focus-visible,.step button:focus-visible{outline:2px solid var(--ce);outline-offset:2px}
.sw{width:18px;height:4px;border-radius:2px;display:inline-block}
.pinout .pin.on{stroke:none}
.pin.on.wc{fill:var(--cc)} .pin.on.we{fill:var(--ce)} .pin.on.ws{fill:var(--cs)} .pin.on.w33{fill:var(--c33)} .pin.on.gnd{fill:var(--ink)}
.pnum{font-size:10px;fill:var(--board-ink);opacity:.85}
.pname{font-size:11px;fill:var(--muted)}
.pname.on{fill:var(--ink);font-weight:700}
.prole{font-family:"Noto Sans SC",sans-serif;font-size:11.5px;font-weight:700}
.gndt{fill:var(--ink)} .latert{fill:var(--muted);font-weight:400}
.steps{display:flex;flex-direction:column;gap:8px;counter-reset:st}
.step{display:grid;grid-template-columns:auto 1fr auto;gap:10px;align-items:start;background:var(--sheet);
  border:1px solid var(--line);border-radius:8px;padding:10px 12px}
.step input{width:20px;height:20px;margin-top:3px;accent-color:var(--ok)}
.step.done{opacity:.6}
.step h3{font-size:15px}
.step p{font-size:14px;color:var(--muted)}
.step button{font:inherit;font-size:12.5px;border:1px solid var(--line);background:var(--panel);color:var(--ink);border-radius:6px;
  padding:4px 8px;cursor:pointer;white-space:nowrap}
.progress{font-size:13px;color:var(--muted)}
table{border-collapse:collapse;width:100%;font-size:14px}
.tbl{overflow-x:auto;background:var(--sheet);border:1px solid var(--line);border-radius:8px}
th,td{border-bottom:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}
th{color:var(--muted);font-weight:600;font-size:13px}
tr:last-child td{border-bottom:none}
.chip{display:inline-block;width:14px;height:14px;border-radius:3px;vertical-align:-2px;border:1px solid var(--muted);margin-right:6px}
.mono{font-family:"JetBrains Mono",ui-monospace,monospace;font-size:13px}
.warn{background:var(--warn-bg);border-left:4px solid var(--warn);border-radius:4px;padding:10px 12px}
.warn b{color:var(--warn)}
.opts{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:10px}
.opt h3{margin-bottom:6px}
.opt ul{margin:0;padding-left:1.2em;font-size:14px}
.badge{font-size:12px;font-weight:700;border-radius:10px;padding:1px 8px;margin-left:6px;background:var(--panel);border:1px solid var(--line)}
ol.flow{margin:0;padding-left:1.4em;display:flex;flex-direction:column;gap:8px}
ol.flow li::marker{font-weight:700}
ol.flow code,.step code,td code{font-family:"JetBrains Mono",ui-monospace,monospace;font-size:13px;background:var(--panel);
  border:1px solid var(--line);border-radius:4px;padding:0 4px}
details summary{cursor:pointer;font-weight:700}

.bb{fill:var(--bb);stroke:var(--line);stroke-width:1}
.bbch{fill:var(--bbch)}
.hole{fill:var(--hole)}
.rp{stroke:#e03131;stroke-width:1.5} .rn{stroke:#1c7ed6;stroke-width:1.5}
.bbl{font-size:10.5px;fill:var(--muted)}
.bbn{font-size:9.5px;fill:var(--muted)}
.rb{fill:#e6cfa1;stroke:#7a5b2e;stroke-width:1.4}
.rlead{stroke:#8a9097;stroke-width:2;fill:none}
.rl{font-size:10.5px;font-weight:700;fill:currentColor;paint-order:stroke;stroke:var(--sheet);stroke-width:3px}
.pt.sm{font-size:12px;fill:#fff}
.ps.ob{fill:var(--board-ink);opacity:.85}
.pu.sm{font-size:9.5px} .pu.xs{font-size:8.5px;fill:#fff}
.pn.xs{font-size:10px}
.w.jw{stroke-width:2.6}
.w.heavy{stroke-width:5.5}
.wg{stroke:var(--ink)} .dot.wg{fill:var(--ink)} .wgt{fill:var(--ink)}
.bbsvg{min-width:720px}
"""


# ---- 面包板布局 -------------------------------------------------------------------
# 标准 830 孔面包板: 列 1~63 (图中只画 1~40), 行 a~e / f~j, 上下各一对电源轨。
# Pico 横放, USB 朝左: 1~20 号脚在 h 行第 3~22 列, 40~21 号脚在 c 行第 3~22 列。

BB_X0, BB_P = 220, 16
BB_ROW = {"T+": 214, "T-": 230, "a": 256, "b": 272, "c": 288, "d": 304, "e": 320,
          "f": 352, "g": 368, "h": 384, "i": 400, "j": 416, "B+": 442, "B-": 458}
BB_COLS = 40


def hole(c, r):
    return (BB_X0 + (c - 1) * BB_P, BB_ROW[r])


def jumper(group, cls, a, b, bow=0, label=None, label_at=None, anchor="middle"):
    (x0, y0), (x1, y1) = a, b
    if bow:
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2 - bow
        d = f"M{x0} {y0} Q{mx} {my} {x1} {y1}"
    else:
        d = f"M{x0} {y0} L{x1} {y1}"
    out = f'<g class="wire" data-g="{group}"><path class="w jw {cls}" d="{d}"/>'
    out += f'<circle class="dot {cls}" cx="{x0}" cy="{y0}" r="3.6"/><circle class="dot {cls}" cx="{x1}" cy="{y1}" r="3.6"/>'
    if label:
        out += f'<text class="wl {cls}t" x="{label_at[0]}" y="{label_at[1]}" text-anchor="{anchor}">{label}</text>'
    return out + "</g>"


def stub(cls, x, y, dx, dy, text, anchor="start"):
    """板外直连的粗线头: 从 (x, y) 伸出一小段, 末端写去向。"""
    x1, y1 = x + dx, y + dy
    tx = x1 + (6 if anchor == "start" else -6) if dx else x1
    ty = y1 + 4 if dx else y1 + (14 if dy > 0 else -6)
    a = anchor if dx else "middle"
    return (f'<g class="wire" data-g="direct"><path class="w heavy {cls}" d="M{x} {y} L{x1} {y1}"/>'
            f'<text class="wl {cls}t" x="{tx}" y="{ty}" text-anchor="{a}">{text}</text></g>')


def breadboard_svg():
    s = []
    x_l, x_r = BB_X0 - 18, BB_X0 + (BB_COLS - 1) * BB_P + 18
    s.append(f'<rect class="bb" x="{x_l}" y="198" width="{x_r - x_l}" height="274" rx="6"/>')
    s.append(f'<rect class="bbch" x="{x_l}" y="330" width="{x_r - x_l}" height="12"/>')
    for r, cls in (("T+", "rp"), ("T-", "rn"), ("B+", "rp"), ("B-", "rn")):
        y = BB_ROW[r] + (-8 if r.endswith("+") else 8)
        s.append(f'<line class="{cls}" x1="{x_l + 8}" y1="{y}" x2="{x_r - 8}" y2="{y}"/>')
        s.append(f'<text class="bbl" x="{x_l - 6}" y="{BB_ROW[r] + 4}" text-anchor="end">{r[0].replace("T", "上").replace("B", "下")}{r[1]}</text>')
    for r in "abcdefghij":
        s.append(f'<text class="bbl" x="{x_l + 6}" y="{BB_ROW[r] + 4}">{r}</text>')
    for c in range(1, BB_COLS + 1):
        x = BB_X0 + (c - 1) * BB_P
        if c == 1 or c % 5 == 0:
            s.append(f'<text class="bbn" x="{x}" y="{BB_ROW["a"] - 12}" text-anchor="middle">{c}</text>')
            s.append(f'<text class="bbn" x="{x}" y="{BB_ROW["j"] + 20}" text-anchor="middle">{c}</text>')
        for r in BB_ROW:
            s.append(f'<rect class="hole" x="{x - 2.5}" y="{BB_ROW[r] - 2.5}" width="5" height="5"/>')
    s.append(f'<text class="note" x="{x_r - 4}" y="492" text-anchor="end">第 41~63 列未画出, 不用</text>')

    # Pico
    s.append('<rect class="usb" x="224" y="318" width="22" height="36" rx="3"/>')
    s.append('<rect class="pico" x="244" y="280" width="320" height="112" rx="8" opacity="0.93"/>')
    s.append('<text class="pt ob" x="420" y="334" text-anchor="middle">Pico  (USB 朝左)</text>')
    s.append('<text class="ps ob" x="420" y="350" text-anchor="middle">1~20 号脚在 h 行 · 40~21 号脚在 c 行</text>')
    for n in range(1, 41):
        c, r = (n + 2, "h") if n <= 20 else (43 - n, "c")
        x, y = hole(c, r)
        used = n in USED
        s.append(f'<circle class="pin{" used" if used else ""}" cx="{x}" cy="{y}" r="4"/>')
    for n, text in ((38, "GND"), (36, "3V3")):
        x, y = hole(43 - n, "c")
        s.append(f'<text class="pu" x="{x}" y="{y + 16}" text-anchor="middle">{text}</text>')
    for n, text in ((3, "GND"), (4, "GP2"), (5, "GP3"), (6, "GP4"), (7, "GP5"), (11, "GP8")):
        x, y = hole(n + 2, "h")
        s.append(f'<text class="pu sm" x="{x + 3.5}" y="{y - 9}" transform="rotate(-90 {x + 3.5} {y - 9})">{text}</text>')

    # 编码器分压 (下半区, 与 Pico 同侧):
    #   A 相: 分压点第 26 列 (i8→i26 接 GP4, j26 经 20k 接下排 −), 10k 跨 f26~f33, 黄线插 h33
    #   B 相: 分压点第 28 列 (i9→i28 接 GP5, j28 经 20k 接下排 −), 10k 跨 g28~g31, 蓝线插 h31
    def bb_res(a, b, text, label_at, anchor="middle"):
        (x0, y0), (x1, y1) = a, b
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        vertical = x0 == x1
        body = resistor(mx, my, text, vertical, label_at, anchor)
        return (f'<g class="wire" data-g="enc"><path class="rlead" d="M{x0} {y0} L{x1} {y1}"/>'
                f'<circle class="dot we" cx="{x0}" cy="{y0}" r="3"/><circle class="dot we" cx="{x1}" cy="{y1}" r="3"/>'
                + body + "</g>")

    s.append(jumper("gnd", "wg", hole(5, "a"), hole(5, "T-")))
    s.append(jumper("gnd", "wg", hole(5, "j"), hole(5, "B-")))
    s.append(jumper("gnd", "wg", hole(40, "T-"), hole(40, "B-"), bow=-26))
    s.append(jumper("enc", "we", hole(8, "i"), hole(26, "i"), bow=-46))
    s.append(jumper("enc", "we", hole(9, "i"), hole(28, "i"), bow=-70))
    s.append(bb_res(hole(26, "f"), hole(33, "f"), "10kΩ", (672, 345)))
    s.append(bb_res(hole(28, "g"), hole(31, "g"), "10kΩ", (656, 386)))
    s.append(bb_res(hole(26, "j"), hole(26, "B-"), "20kΩ", (612, 442), "end"))
    s.append(bb_res(hole(28, "j"), hole(28, "B-"), "20kΩ", (670, 442), "start"))
    s.append(f'<text class="note" x="{hole(29, "j")[0]}" y="502" text-anchor="middle">第 26、28 列是分压点 (≈3V)</text>')

    # EV3 线 (剪开)
    s.append(box(596, 26, 234, 58, "EV3 马达线 (剪开的 6 根芯)"))
    tails = [(612, "白", "wm"), (628, "黑", "wm"), (748, "蓝 B", "we"), (764, "黄 A", "we"), (780, "绿 5V", "w5"),
             (796, "红 GND", "wg")]
    for x, t, cls in tails:
        s.append(f'<text class="pn xs" x="{x}" y="78" text-anchor="middle">{t.split()[0]}</text>')
    s.append(jumper("enc", "we", (764, 84), hole(33, "h")))
    s.append(jumper("enc", "we", (748, 84), hole(31, "h")))
    for c, t in ((33, "黄"), (31, "蓝")):
        x, y = hole(c, "j")
        s.append(f'<text class="wl wet" x="{x}" y="{y + 16}" text-anchor="middle">{t}</text>')
    s.append(jumper("p5", "w5", (780, 84), hole(36, "T+"), label="5V", label_at=(772, 150), anchor="end"))
    s.append(jumper("gnd", "wg", (796, 84), hole(37, "T-"), label="GND", label_at=(804, 150), anchor="start"))
    s.append(stub("wm", 612, 84, 0, 34, "白"))
    s.append(stub("wm", 628, 84, 0, 34, "黑"))
    s.append('<text class="note" x="600" y="148" text-anchor="end">白、黑两根</text>')
    s.append('<text class="note" x="600" y="162" text-anchor="end">直连 DRV8833 AOUT1/2</text>')

    # 5V 降压
    s.append(box(250, 26, 150, 58, "5V 降压模块", "输出 ≥ 3A"))
    s.append(jumper("p5", "w5", (332, 84), hole(8, "T+"), label="OUT+", label_at=(326, 150), anchor="end"))
    s.append(jumper("gnd", "wg", (348, 84), hole(9, "T-"), label="GND", label_at=(354, 150), anchor="start"))
    s.append(stub("w9", 250, 44, -40, 0, "9V+", anchor="end"))
    s.append(stub("w9", 250, 66, -40, 0, "9V−", anchor="end"))
    s.append(stub("w5", 400, 44, 44, 0, "另一根直连舵机 V+"))
    s.append(stub("w5", 400, 66, 44, 0, "另一根直连舵机 GND"))

    # DRV8833 (放在板外)
    s.append(box(130, 540, 230, 80, "DRV8833 (放在面包板外)", "VM / GND / AOUT 不走面包板"))
    s.append(jumper("ctrl", "wc", hole(6, "j"), (300, 540), label="GP2→AIN1", label_at=(292, 500), anchor="end"))
    s.append(jumper("ctrl", "wc", hole(7, "j"), (316, 540), label="GP3→AIN2", label_at=(324, 520), anchor="start"))
    s.append(stub("w9", 130, 566, -40, 0, "VM ← 9V+", anchor="end"))
    s.append(stub("w9", 130, 594, -40, 0, "GND ← 9V−", anchor="end"))
    s.append(stub("wm", 190, 620, 0, 30, "AOUT1 → 白"))
    s.append(stub("wm", 270, 620, 0, 30, "AOUT2 → 黑"))

    # 舵机
    s.append(box(380, 540, 170, 70, "Geekservo 舵机"))
    s.append(jumper("servo", "ws", hole(13, "j"), (412, 540), label="GP8→信号", label_at=(420, 500), anchor="start"))
    s.append(stub("w5", 550, 566, 44, 0, "V+ ← 5V 降压 (直连)"))
    s.append(stub("w5", 550, 594, 44, 0, "GND ← 5V 降压 (直连)"))
    return ('<svg class="diagram bbsvg" viewBox="0 0 900 680" role="img" aria-label="面包板布局: Pico 横放在第 3~22 列, '
            '编码器分压电阻在第 26~33 列下半区; 上排电源轨为 5V 和地; 马达驱动和舵机电源放在面包板外直接连线。">'
            + "".join(s) + "</svg>")


BB_TABLE = [
    ("插 Pico", "c3~c22、h3~h22", "USB 朝左。1 号脚在 h3, 20 号脚在 h22; 40 号脚在 c3, 21 号脚在 c22"),
    ("地", "a5 → 上排 −", "Pico 38 号脚 GND"),
    ("地", "j5 → 下排 −", "Pico 3 号脚 GND"),
    ("地", "上排 − (第 40 列) → 下排 −", "把上下两条地线轨连起来"),
    ("编码器 A", "10kΩ: f26 ↔ f33; 20kΩ: j26 ↔ 下排 −", "第 26 列是 A 相分压点"),
    ("编码器 A", "i8 → i26", "GP4 → A 相分压点"),
    ("编码器 A", "黄线 → h33", "EV3 5 号脚 → 10kΩ 的另一端"),
    ("编码器 B", "10kΩ: g28 ↔ g31; 20kΩ: j28 ↔ 下排 −", "第 28 列是 B 相分压点"),
    ("编码器 B", "i9 → i28", "GP5 → B 相分压点"),
    ("编码器 B", "蓝线 → h31", "EV3 6 号脚 → 10kΩ 的另一端"),
    ("编码器电源", "绿线 → 上排 + (第 36 列), 红线 → 上排 − (第 37 列)", "EV3 线的红色是地线"),
    ("5V 电源", "J6.1 → 上排 + 第8孔, J6.2 → 上排 − 第9孔", "从洞洞板排母引出两根公对公线"),
    ("马达控制", "j6 → J7.1, j7 → J7.2", "经洞洞板焊线接 DRV8833 AIN1 / AIN2"),
    ("舵机信号", "j13 → J7.3", "经洞洞板接舵机信号，电源不走面包板"),
    ("驱动使能", "a7 → J7.4", "Pico 36 号脚 3V3 (c7) → STBY"),
]


STEPS = [
    ("gnd", "先接所有地线", "断电状态下, 把 9V 电源负极、5V 降压模块 GND、DRV8833 GND、舵机地线、"
     "EV3 线 3 号脚 (红色) 和 Pico 的 38 号脚连在一起。先接地, 后面任何一步接错都更不容易损坏器件。"),
    ("p9", "接 9V", "先用万用表确认电源电压在 8.5~9.5V (绝不能超过 10.8V)。9V 正极接 DRV8833 的 VM 和 5V 降压模块的输入; "
     "本版不另装电容, 保留模块自带的电容。洞洞板按用户确认的 DRV8833 脚序使用 VM 输入。"),
    ("p5", "接 5V", "单独给 5V 降压模块通电, 先把输出调到 5.0V, 断电后再接: EV3 线 4 号脚 (绿色)、舵机正极。"),
    ("p33", "接 3.3V", "Pico 的 36 号脚 (3V3 OUT) 接 DRV8833 的 STBY (有的标 nSLEEP/EEP), 让驱动处于工作状态。不要接任何 5V 的东西。"),
    ("ctrl", "接马达控制线", "Pico 的 GP2 (4 号脚) 接 DRV8833 AIN1, GP3 (5 号脚) 接 AIN2。"),
    ("motor", "接马达电源线", "DRV8833 的 AOUT1 接 EV3 线 1 号脚 (白), AOUT2 接 2 号脚 (黑)。两根线接反也不会坏, 只是方向相反, 用 check 命令能发现。"),
    ("enc", "接编码器分压", "每路两个电阻: EV3 线 5 号脚 (黄, A 相) → 10kΩ → 分压点 → GP4, 分压点再经 20kΩ 接地; "
     "6 号脚 (蓝, B 相) 同样接到 GP5。先不接 GP4/GP5 的跳线, 通电后手转马达量分压点: 应在约 0V 和 3V 之间变化, 不能超过 3.3V, 正常再接跳线。"
     "5V 信号绝不能直接接 Pico。"),
    ("servo", "接舵机信号", "Pico 的 GP8 (11 号脚) 接舵机信号线。舵机的电源和地已在第 1、3 步接好。"),
]

FILTERS = [("all", "全部", None), ("p9", "9V", "--c9"), ("p5", "5V", "--c5"), ("p33", "3.3V", "--c33"),
           ("gnd", "地线", "--ink"), ("motor", "马达", "--cm"), ("ctrl", "控制", "--cc"), ("enc", "编码器", "--ce"),
           ("servo", "舵机", "--cs")]

JS = """
(function(){
  var fig = document.getElementById('wiring');
  var buttons = document.querySelectorAll('.filters button');
  function show(g){
    buttons.forEach(function(b){ b.setAttribute('aria-pressed', String(b.dataset.g === g)); });
    if (g === 'all') { fig.classList.remove('filtered'); fig.removeAttribute('data-show'); }
    else { fig.classList.add('filtered'); fig.setAttribute('data-show', g); }
  }
  buttons.forEach(function(b){ b.addEventListener('click', function(){ show(b.dataset.g); }); });
  document.querySelectorAll('.step button').forEach(function(b){
    b.addEventListener('click', function(){
      show(b.dataset.g);
      document.getElementById('wiring-card').scrollIntoView({behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start'});
    });
  });
  var KEY = 'quadcuber-wiring-steps';
  var saved = {};
  try { saved = JSON.parse(localStorage.getItem(KEY) || '{}') || {}; } catch (e) { saved = {}; }
  var boxes = document.querySelectorAll('.step input');
  function update(){
    var n = 0;
    boxes.forEach(function(c){ c.closest('.step').classList.toggle('done', c.checked); if (c.checked) n++; });
    document.getElementById('progress').textContent = '已完成 ' + n + ' / ' + boxes.length + ' 步';
  }
  boxes.forEach(function(c){
    c.checked = !!saved[c.id];
    c.addEventListener('change', function(){
      saved[c.id] = c.checked;
      try { localStorage.setItem(KEY, JSON.stringify(saved)); } catch (e) {}
      update();
    });
  });
  update();
})();
"""


def perfboard_section():
    return perfboard_layout.section()


def perfboard_page():
    """独立页面与主指南复用章节和样式，离线打开也能显示 SVG。"""
    return ('<!doctype html>\n<html lang="zh-CN">\n<head>\n'
            '<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<title>quadcuber 洞洞板接线设计</title>\n'
            f'<style>{CSS}</style>\n</head>\n<body>\n<main class="wrap">\n'
            '<nav><a href="direct-breadboard.html">当前调试：面包板＋动力直连接线图</a> · '
            '<a href="index.html#perfboard">返回完整接线指南</a></nav>\n'
            + perfboard_section() + '\n</main>\n</body>\n</html>\n')


def page():
    esc = html.escape
    out = ['<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">',
           '<meta name="viewport" content="width=device-width, initial-scale=1">',
           '<title>quadcuber 单臂接线</title>',
           '<link rel="preconnect" href="https://fonts.googleapis.com">',
           '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600'
           '&family=JetBrains+Mono:wght@400;700&family=Noto+Sans+SC:wght@400;700&display=swap">',
           f"<style>{CSS}</style></head><body>", '<div class="wrap">']
    out.append('<header style="display:flex;flex-direction:column;gap:10px">'
               '<div class="eyebrow">quadcuber · 单臂原型 · 接线指南</div>'
               '<h1>把机械手接到 Pico 上</h1>'
               '<p>一个 EV3 马达 (大马达或中马达接法相同)、一个灰色 Geekservo、一块 DRV8833、4 个电阻 (10kΩ ×2、20kΩ ×2)。'
               '引脚按 <span class="mono">firmware/pico/config.py</span> 的 R 臂分配, 接完按 '
               '<span class="mono">docs/single_arm.md</span> 第 4、5 节刷程序和测试。</p>'
               '<p><a href="direct-breadboard.html">当前调试：面包板＋动力直连（无洞洞板）</a> · '
               '<a href="README.md">电路总览与验证状态</a> · <a href="#perfboard">可选洞洞板</a> · <a href="#breadboard">洞洞板配套面包板</a></p></header>')
    out.append('<div class="warn"><b>2026-09-27 更新：编码器改用电阻分压, 不再用电平转换模块。</b>'
               'BSS138 模块与 EV3 马达内部的串联电阻不匹配, 低电平降不下来。'
               '原因和测量依据见 <a href="../ev3-interface-verification.md">接口复核报告</a>。</div>')
    out.append('<section><h2>三条不能违反的规则</h2><div class="rules">'
               '<div class="rule"><b>马达电压不超过 10.8V</b>DRV8833 的上限。9V 可以, 12V 会烧。</div>'
               '<div class="rule"><b>编码器信号必须经过分压</b>Pico 的引脚不耐 5V, EV3 编码器输出 5V 信号; 每路 10kΩ 串联 + 20kΩ 接地, 降到约 3V。</div>'
               '<div class="rule"><b>舵机不从 Pico 取电</b>舵机用 5V 降压模块供电, 启动电流会让 Pico 复位。</div>'
               "</div></section>")

    out.append('<section><h2>总览</h2><figure><div class="scroll">' + overview_svg() + "</div>"
               "<figcaption>9V 只给马达驱动和 5V 降压模块; 5V 给舵机和编码器; Pico 由电脑 USB 供电, "
               "编码器的 5V 信号经电阻分压成约 3V 再进 Pico。所有模块的地 (GND) 连在一起, 图中没画出。</figcaption></figure></section>")

    btns = ""
    for g, label, var in FILTERS:
        sw = f'<span class="sw" style="background:var({var})"></span>' if var else ""
        btns += f'<button type="button" data-g="{g}" aria-pressed="{str(g == "all").lower()}">{sw}{label}</button>'
    out.append('<section id="wiring-card"><h2>完整接线图</h2>'
               f'<div class="filters" role="group" aria-label="按类别显示导线">{btns}</div>'
               '<figure id="wiring"><div class="scroll">' + wiring_svg() + "</div>"
               "<figcaption>点上面的按钮只看某一类线。线的颜色表示用途, 不是实际导线的颜色。所有接地符号表示连到同一个公共地。"
               "模块的排针顺序各家不同, 以板上的丝印为准。A 相下拉电阻那条竖线上的小半圆表示跨过 B 相线, 两线不相连。</figcaption>"
               "</figure></section>")

    steps = ""
    for i, (g, title, text) in enumerate(STEPS, 1):
        steps += (f'<div class="step"><input type="checkbox" id="step{i}" aria-label="第 {i} 步已完成">'
                  f'<div><h3>{i}. {esc(title)}</h3><p>{esc(text)}</p></div>'
                  f'<button type="button" data-g="{g}">在图上看</button></div>')
    out.append('<section><h2>分步接线</h2><p class="progress" id="progress"></p>'
               f'<div class="steps">{steps}</div>'
               '<p class="progress">勾选状态只保存在这台设备的浏览器里。</p></section>')

    rows = "".join(f"<tr><td>{a}</td><td class=\"mono\">{b}</td><td>{c}</td></tr>" for a, b, c in BB_TABLE)
    out.append(perfboard_section())
    out.append('<section id="breadboard"><h2>可选洞洞板配套：面包板怎么插</h2>'
               '<p>与洞洞板之间的 6 根线见 <a href="perfboard.html#bridge">④ 两板实际连接图</a>。下图的板内跳线保留，板外接线经 J6/J7 插座。</p>'
               '<p>信号线走面包板; 大电流的线 (9V、马达线、舵机电源) 不走面包板, 直接连。'
               '孔的坐标写法: 字母是行, 数字是列, 例如 <span class="mono">a5</span> 是 a 行第 5 列。</p>'
               '<figure><div class="scroll">' + breadboard_svg() + "</div>"
               "<figcaption>细线是插在面包板上的跳线, 粗线头是不走面包板、直接连到别处的线 (写了去向)。"
               "面包板每一列的 f~j 五个孔是连通的: 第 26 列 (A 相) 和第 28 列 (B 相) 就是分压点, 各插着 10kΩ 的一端、"
               "20kΩ 的一端和到 GP4/GP5 的跳线; 第 33、31 列插 10kΩ 的另一端和 EV3 的黄、蓝线。"
               "电阻没有正负, 两头可以对调。</figcaption></figure>"
               '<div class="tbl"><table><tr><th>类别</th><th>从 → 到</th><th>说明</th></tr>' + rows + "</table></div>"
               '<div class="warn"><b>先检查面包板的电源轨。</b> 有些面包板的电源轨在中间 (第 30 列左右) 是断开的, '
               "红蓝线在那里有个缺口。用万用表测一下上排 + 的第 5 列和第 40 列通不通, 不通就在断口处补一根跳线。"
               "另外, 5V 降压模块的输入地和输出地大多是相通的, 用万用表确认一下; 面包板的地只通过降压模块的 GND 这一根线接出去。</div>"
               "</section>")
    out.append('<section><h2>Pico 引脚</h2><figure><div class="scroll">' + pinout_svg() + "</div>"
               "<figcaption>从正面 (有 RP2040 芯片的一面) 看, USB 口朝上, 左上角是 1 号脚。彩色的是单臂原型要接的脚; "
               "GP0/GP1 以后接 Zero W 的串口, 现在空着。</figcaption></figure>"
               '<details class="card"><summary>四个机械手的完整引脚分配</summary><div class="tbl" style="margin-top:10px">'
               + spec.pin_table_html() + "</div></details></section>")

    ev3 = [("#f4f4f4", "1", "白", "马达 M1", "DRV8833 AOUT1"), ("#222", "2", "黑", "马达 M2", "DRV8833 AOUT2"),
           ("#d9282f", "3", "红", "地 GND", "公共地"), ("#2f9e44", "4", "绿", "编码器电源", "5V"),
           ("#f2c500", "5", "黄", "编码器 A 相", "10kΩ → GP4 (GP4 经 20kΩ 接地)"), ("#1c6fd6", "6", "蓝", "编码器 B 相", "10kΩ → GP5 (GP5 经 20kΩ 接地)")]
    rows = "".join(f'<tr><td class="mono">{n}</td><td><span class="chip" style="background:{c}"></span>{col}</td>'
                   f"<td>{fn}</td><td>{to}</td></tr>" for c, n, col, fn, to in ev3)
    out.append('<section><h2>EV3 线的 6 根芯</h2><div class="tbl"><table>'
               "<tr><th>脚</th><th>常见线色</th><th>功能</th><th>接到</th></tr>" + rows + "</table></div>"
               '<div class="warn"><b>红线是地线, 不是正极。</b> 线色只是常见配色, 不同的线可能不一样, 以万用表通断为准: '
               "1、2 脚之间是马达线圈, 电阻约几欧到十几欧; 1、2 脚和其他脚之间不通。</div></section>")

    out.append('<section><h2>编码器为什么用分压</h2>'
               '<p>LEGO 官方电路: EV3 马达里两路编码器都是推挽输出 0V/5V, 各经一个串联电阻到插头 (蓝线 3.3kΩ; '
               '黄线的电阻兼作型号识别, 大马达 3.3kΩ、中马达 6.8kΩ)。加上外接的 10kΩ 和 20kΩ, 高电平约 3.0V (中马达黄线约 2.7V), '
               '低电平约 0V；已有大马达空载计数和闭环记录，装机后仍需验收。</p>'
               '<p>BSS138 电平转换模块的上拉会和马达内部电阻分压, 低电平只能降到约 1.65V (实测 1.60~1.64V), 不能用; '
               'TXS0108E 要求信号源内阻很低, 也不能用。'
               '<a href="../ev3-interface-verification.md">详细依据</a>。</p></section>')

    checks = [("9V 电源 (空载)", "直流电压档, 红表笔接正极", "8.5~9.5V, 绝不能超过 10.8V"),
              ("5V 降压输出", "直流电压档, 接任何负载之前", "4.9~5.2V"),
              ("9V 与 GND 之间", "断电, 电阻档", "不能是 0Ω (否则短路)"),
              ("5V 与 GND 之间", "断电, 电阻档", "不能是 0Ω"),
              ("各模块的 GND 之间", "断电, 蜂鸣档", "全部相通"),
              ("EV3 线 1、2 脚之间", "断电, 电阻档", "几欧到十几欧 (马达线圈)"),
              ("DRV8833 nSLEEP 对地", "通电后, 直流电压档", "约 3.3V（本项目固定接 Pico 3V3）"),
              ("分压点 (第 26、28 列) 对地", "通电后、先不接 GP4/GP5 跳线, 手转马达, 每次转一点停下读", "在约 0V 和 3V 之间跳变, 任何时候不超过 3.3V")]
    rows = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td></tr>" for a, b, c in checks)
    out.append('<section><h2>上电前用万用表检查</h2><div class="tbl"><table>'
               "<tr><th>测什么</th><th>怎么测</th><th>应该是</th></tr>" + rows + "</table></div></section>")

    out.append('<section><h2>完整接线后的上电与分项测试</h2>'
               '<p>马达、编码器和舵机可一次接齐。当前直连方案先按 '
               '<a href="direct-breadboard.html#complete-wiring">完整接线说明</a>连接 P04 与舵机；分项测试时无需反复插拔。</p><ol class="flow">'
               "<li>先<b>只插 USB</b>。用 Thonny 或 mpremote 进入 REPL, 运行 <code>import arm_test; arm_test.main()</code>, "
               "出现 <code>arm&gt;</code> 后输入 <code>off</code>，再用 <code>help</code> 查看命令列表。</li>"
               "<li>接通 <b>9V</b>。初始化不主动发马达或舵机动作命令，但不能保证硬件上电不抖动。"
               "首次舵机定位先脱开连杆；如果马达或舵机自己转、发烫，立刻断开动力电源（含舵机 5V）并检查接线。</li>"
               "<li>输入 <code>enc</code>, 用手把马达输出轴转一圈, 再输入 <code>enc</code>。计数应变化约 720 "
               "(方向取决于转向)。没有变化就检查 5V、分压电阻、黄/蓝线通断和 GP4/GP5。</li>"
               "<li>确认无魔方、机械头和联动机构全程自由、供电接线已核验后，先输入 <code>motor_test unloaded</code>，"
               "该命令仅授权空载测试，不会转动。再输入 <code>check</code>，马达应短暂正转并显示 <b>方向正确</b>。"
               "方向相反就按提示改 <span class=\"mono\">config.py</span>，重新上传并 Ctrl+D 软重启，再核查并重开空载模式。"
               "<code>off</code>、异常、Ctrl+C、退出或重启都会撤销模式；它不允许 load/cube 等带载测试或舵机开合。方向确认之前不要运行 <code>rot</code>。</li>"
               "<li>马达方向和齿轮比确认后，按 <span class=\"mono\">docs/single_arm.md</span> "
               "第 5 节标定舵机，再做旋转及联合测试。首次定位必须脱开曲柄与连杆，使用 <code>servo_cal ... detached</code> "
               "声明会话后才发基准脉冲；断电连接并核实轴位后使用 aligned 会话。首次须等于 start，"
               "随后可指定声明区间内任意脉宽，不限制相邻命令差值；未知行程和端点附近仍建议小步观察。"
               "进入舵机会话会停止马达并撤销空载模式。端点和安全工作区间默认未设置；实测并填写匹配的 v4/R 身份、开启端点标定标志后，"
               "还需分开确认时序。默认 <code>SERVO_MOVE_MS=None</code>、<code>SERVO_TIMING_CONFIRMED=False</code>；"
               "自行选择保守的临时等待时长（1～5000ms 整数，不能沿用旧 120ms），上传并 Ctrl+D 重载后，"
               "只单次 open 或 close，观察完全停稳再发下一条，录像测完整开合时间。此时 grip、cycle 和普通旋转仍被锁住，显式空载模式是例外。"
               "取开／合较慢实测值加余量回填等待时长、设置时序确认标志，再上传重载后才做连续和联合动作；机构或供电变化后重新确认。"
               "详见 <a href=\"../single_arm.md#servo-calibration\">完整标定流程</a>。</li></ol></section>")
    out.append("</div>")
    out.append(f"<script>{JS}</script></body></html>")
    return "\n".join(out) + "\n"


def build(directory=HERE):
    """统一生成；输出目录的父级是 docs，用于 Markdown 产物。"""
    spec.validate()
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    direct_wiring.main(directory)
    perfboard_layout.write_assets(directory)
    (directory / "index.html").write_text(page(), encoding="utf-8")
    (directory / "perfboard.html").write_text(perfboard_page(), encoding="utf-8")
    (directory.parent / "single_arm.md").write_text(spec.single_arm_document(), encoding="utf-8")


def check():
    """在临时目录重建，逐字节检查产物，不修改工作区。"""
    with TemporaryDirectory() as tmp:
        docs = Path(tmp) / "docs"
        build(docs / "wiring")
        stale = []
        for generated in sorted(docs.rglob("*")):
            if not generated.is_file():
                continue
            relative = generated.relative_to(docs)
            current = HERE.parent / relative
            if not current.exists() or current.read_bytes() != generated.read_bytes():
                stale.append(str(relative))
        if stale:
            print("生成文件缺失或过期：" + "、".join(stale))
            print("请运行 python docs/wiring/build.py 并一起保存生成文件。")
            return 1
    print("电路配置、网络及生成文件一致性检查通过。")
    return 0


def main():
    parser = argparse.ArgumentParser(description="生成或检查电路文档")
    parser.add_argument("--check", action="store_true", help="只检查，不修改文件")
    args = parser.parse_args()
    if args.check:
        return check()
    build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
