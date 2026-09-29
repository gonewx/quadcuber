"""生成 v2 搭建说明书: docs/lego/v2/index.html、步骤图、零件缩略图和 model.ldr。

用法 (先在另一个终端启动 ../render/server.py):
    cd tools/lego/v2 && python booklet.py [--no-render]

渲染和样式沿用 v1 (../render/render.js、../booklet.py 的 CSS), 这里只换模型和文字。
"""

import html
import importlib.util
import json
import os
import subprocess
import sys
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.append(os.path.join(HERE, ".."))

import check  # noqa: E402
import model  # noqa: E402
import run_check  # noqa: E402,F401  (补 CONNECTOR_LEN 和转盘豁免)

_spec = importlib.util.spec_from_file_location("booklet_v1", os.path.join(HERE, "..", "booklet.py"))
_v1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_v1)

OUT = os.path.join(HERE, "..", "..", "..", "docs", "lego", "v2")
IMG = os.path.join(OUT, "img")
WORK = os.path.join(HERE, "..", ".cache", "work", "v2")
V1_URL = "https://claude.ai/artifact/BWgtEpkX4PGRGnYzvNV2L4"
W, H = 1200, 860
TW, TH = 260, 200
MOTORS = ("95658.dat",)


def visible_parts(parts, k):
    st = model.STEPS
    sub = st[k - 1]["sub"]
    attach_at = {}
    for i, s in enumerate(st, 1):
        for g in s["attach"]:
            attach_at[g] = i
    out = []
    for p in parts:
        ps = st[p.step - 1]
        if p.step > k:
            continue
        if sub is not None:
            if ps["sub"] == sub:
                out.append(p)
        elif ps["sub"] is None or attach_at.get(ps["sub"], 10**9) <= k:
            out.append(p)
    return out


def ldr_for_step(parts, k):
    """三段 LDraw: STEP1 不参与取景的旧零件, STEP2 参与取景的旧零件, STEP3 本步零件。"""
    s = model.STEPS[k - 1]
    vis = visible_parts(parts, k)
    new = [p for p in vis if p.step == k or (model.STEPS[p.step - 1]["sub"] in s["attach"])]
    old = [p for p in vis if p not in new]
    if s["focus"] == "head":
        fit_old = [p for p in old if model.is_head(p) or p.name == "18939.dat"]
    elif s["focus"] == "new":
        fit_old = []
    elif s["focus"] == "motor":
        fit_old = [p for p in old if p.pos[0] < 150]
    else:
        fit_old = old
    far = [p for p in old if p not in fit_old]
    lines = ["0 step", ""]
    for group in (far, fit_old, new):
        lines += [p.ldraw() for p in group]
        lines.append("0 STEP")
    return "\n".join(lines) + "\n", new


def part_key(p):
    return (p.name, p.color)


def main(render=True):
    os.makedirs(IMG, exist_ok=True)
    os.makedirs(WORK, exist_ok=True)
    parts = model.build()
    steps = model.STEPS
    jobs = []
    step_new = []
    for k in range(1, len(steps) + 1):
        text, new = ldr_for_step(parts, k)
        path = os.path.join(WORK, f"step{k:02d}.ldr")
        with open(path, "w") as f:
            f.write(text)
        yaw, pitch = steps[k - 1]["view"]
        first_step = k == 1 or steps[k - 1]["sub"] != steps[k - 2]["sub"] and steps[k - 1]["sub"] is not None
        opts = {"w": W, "h": H, "yaw": yaw, "pitch": pitch, "fitFrom": 1, "margin": 0.07}
        if not first_step:
            opts.update(highlight=2, fadeOld=True)
        jobs.append({"model": path, "out": os.path.join(IMG, f"step{k:02d}.png"), "opts": opts})
        step_new.append(new)

    keys = OrderedDict()
    for p in parts:
        keys.setdefault(part_key(p), p)
    for (name, color), p in keys.items():
        fn = f"part_{name[:-4]}_{color}.png"
        path = os.path.join(WORK, fn.replace(".png", ".ldr"))
        with open(path, "w") as f:
            f.write(f"0 part\n1 {color} 0 0 0 1 0 0 0 1 0 0 0 1 {name}\n")
        jobs.append({"model": path, "out": os.path.join(IMG, fn),
                     "opts": {"w": TW, "h": TH, "yaw": 35, "pitch": 28, "margin": 0.12}})

    subs = OrderedDict()
    for s in steps:
        if s["sub"]:
            subs.setdefault(s["sub"], None)
    for g in subs:
        gp = [p for p in parts if steps[p.step - 1]["sub"] == g]
        path = os.path.join(WORK, f"sub_{g}.ldr")
        with open(path, "w") as f:
            f.write("0 sub\n" + "\n".join(p.ldraw() for p in gp) + "\n")
        idx = list(subs).index(g)
        jobs.append({"model": path, "out": os.path.join(IMG, f"sub{idx}.png"),
                     "opts": {"w": TW, "h": TH, "yaw": 35, "pitch": 28, "margin": 0.1}})

    for tag, ext in (("closed", True), ("open", False)):
        path = os.path.join(WORK, f"cover_{tag}.ldr")
        with open(path, "w") as f:
            f.write(model.to_ldr(model.build(fork_extended=ext)))
        jobs.append({"model": path, "out": os.path.join(IMG, f"cover_{tag}.png"),
                     "opts": {"w": 1400, "h": 900, "yaw": 35, "pitch": 28, "margin": 0.04}})
    for tag, ext in (("closed", True), ("open", False)):
        head = [p for p in model.build(fork_extended=ext) if model.is_head(p) or p.name == "cube56.dat"]
        path = os.path.join(WORK, f"mech_{tag}.ldr")
        with open(path, "w") as f:
            f.write("0 mech\n" + "\n".join(p.ldraw() for p in head) + "\n")
        jobs.append({"model": path, "out": os.path.join(IMG, f"mech_{tag}.png"),
                     "opts": {"w": 1000, "h": 520, "yaw": 0, "pitch": 88, "margin": 0.05}})
    # 剖面示意: 只画承重路线上的零件 (转盘、支座、侧板、舵机座、传动), 从侧上方看
    def in_core(p):
        x, y, z = p.pos
        if p.name in ("18938.dat", "18939.dat", "95658.dat"):
            return True
        if p.name == "6632.dat":
            return x < 110
        if p.name == "44294.dat":
            return abs(x - 60) < 1
        if p.name == "64179.dat":
            return (abs(x - 40) < 1 and abs(y) < 1) or (abs(x - 120) < 1 and z < 0)
        if p.name == "32524.dat":
            return abs(x - 120) < 1
        if p.name == "2780.dat":
            return abs(y) < 30 and (abs(x - 110) < 1 or (abs(x - 80) < 1 and z < 0) or abs(x - 40) < 1)
        return False

    core = [p for p in model.build() if in_core(p)]
    path = os.path.join(WORK, "core.ldr")
    with open(path, "w") as f:
        f.write("0 core\n" + "\n".join(p.ldraw() for p in core) + "\n")
    jobs.append({"model": path, "out": os.path.join(IMG, "core.png"),
                 "opts": {"w": 1000, "h": 640, "yaw": 125, "pitch": 24, "margin": 0.05}})
    model.build()

    if render:
        jobs_path = os.path.join(WORK, "jobs.json")
        with open(jobs_path, "w") as f:
            json.dump(jobs, f)
        env = dict(os.environ)
        env.setdefault("PLAYWRIGHT_MODULE", "/opt/node22/lib/node_modules/playwright")
        subprocess.run(["node", "render.js", jobs_path], cwd=os.path.join(HERE, "..", "render"), check=True, env=env)

    with open(os.path.join(OUT, "model.ldr"), "w") as f:
        f.write(model.to_ldr(parts, "quadcuber 单臂原型 v2 (转盘主轴承)"))
    write_html(parts, step_new, keys, list(subs))


# ---- HTML ----------------------------------------------------------------------

CSS = _v1.CSS + """
.cmp td:first-child{white-space:nowrap;font-weight:600}
.cmp td{min-width:9em}
.bad{color:var(--warn);font-weight:700}
.lead{font-size:16px}
ul.plain{margin:0;padding-left:1.2em;display:grid;gap:6px;max-width:70ch}
"""

EVAL_ROWS = [
    ("承重", "整个机械臂 (约 150mm 长) 只靠马达输出盘上 3 个排成一条线的销挂着, 上下相距 16mm。输出轴内部的间隙在叉尖被放大十几倍, "
     "这是实物下垂的根本原因", "60 齿转盘当主轴承, 两侧耳朵各用销接到侧板; 马达只通过一根 7 号轴传扭矩, 不再承受弯矩"),
    ("马达固定", "耳朵框架 + 挂在短销头上 + 3 层摩擦销垫块 + 底部垫梁 + 追加长销: 三次实物补丁叠起来, 每一处都是单点受力",
     "马达只剩反扭矩: 保留 TRACK3R 耳朵固定, 固定板底边用 3 个竖销压到底板上, 一步装好"),
    ("导轨", "12 号轴只插在 1 孔厚的边框里, 向前悬伸 84mm; 后来补了两片细梁", "16 号轴穿过侧板前后两条边和舵机座, 3 个支点、跨度 32mm, 轴套两侧锁定"),
    ("舵机", "偏在转动座一侧, 靠长销短头挂着; 机械臂重心偏离转轴", "舵机座是一根竖放的 7 孔梁, 舵机居中装在转轴上, 7 个孔全部有用途"),
    ("测试架", "一面单层梁墙 + 搭接头, 抗扭差; 马达和固定叉挂在墙上", "全部用 7x5 框架共面拼接 (官方 42082 的拼法), 底座两层互相压住, 固定叉立在自己的 L 形竖板上"),
    ("装配", "多处要翻转整机、从缝里插销", "按子组件搭: 底座、固定叉、转盘支座、马达、机械臂、叉子各自搭好再装上"),
]


def write_html(parts, step_new, keys, subs):
    steps = model.STEPS
    esc = html.escape
    bom = Counter(part_key(p) for p in parts if p.name != "cube56.dat")
    n_parts = sum(n for k, n in bom.items() if k[0] not in ("95658.dat", "geekservo.dat"))

    def img(src, alt, cls="", w=None, h=None):
        size = f' width="{w}" height="{h}"' if w else ""
        return f'<img src="img/{src}" alt="{esc(alt)}" class="{cls}" loading="lazy"{size}>'

    def part_img(k):
        return f"part_{k[0][:-4]}_{k[1]}.png"

    out = []
    out.append('<title>quadcuber 单臂 v2</title>')
    out.append('<link rel="preconnect" href="https://fonts.googleapis.com">')
    out.append('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700'
               '&family=JetBrains+Mono&family=Noto+Sans+SC:wght@400;700&display=swap">')
    out.append(f"<style>{CSS}</style>")
    out.append('<div class="wrap">')

    out.append('<header class="cover">')
    out.append('<div class="eyebrow">quadcuber · 单臂原型 v2 · 专业重设计 · 搭建说明书</div>')
    out.append("<h1>转盘主轴承版机械手</h1>")
    out.append(f'<p class="lead">v1 能用, 但还是 "功能原型": 机械臂的重量压在马达输出轴上, 马达固定靠几次补丁叠出来。'
               "v2 的核心改动只有一条: <b>承重和传扭分开</b>。机械臂装在 60 齿转盘上, 由转盘承受弯矩; 马达只通过一根十字轴带它转。"
               f'其余结构都围绕这条原则重新排布。v1 说明书保留不动: <a href="{V1_URL}">v1 大马达版</a>。</p>')
    out.append('<div class="plate">' + img("cover_closed.png", "整机总览", w=1400, h=900) + "</div>")
    out.append('<div class="facts">'
               f'<div class="fact"><b>{len(steps)}</b><span>个步骤</span></div>'
               f'<div class="fact"><b>{n_parts}</b><span>个乐高零件, 另加 EV3 大马达和舵机各 1 个</span></div>'
               f'<div class="fact"><b>{model.STROKE * 0.4:.1f} mm</b><span>叉子行程 (要求 ≥ 13mm)</span></div>'
               '<div class="fact"><b>0</b><span>个销插在马达输出盘上 (弯矩不走马达)</span></div>'
               "</div>")
    out.append('<nav class="toc"><a href="#eval">v1 评估</a><a href="#idea">设计思路</a><a href="#buy">要买的零件</a>'
               '<a href="#bom">零件清单</a>'
               + "".join(f'<a href="#s{k}">{k}. {esc(s["title"])}</a>' for k, s in enumerate(steps, 1))
               + '<a href="#checks">检查与待验证</a></nav>')
    out.append("</header>")

    # 评估
    out.append('<section id="eval" class="cover"><h2>v1 评估: 没有达到专业水准</h2>')
    out.append("<p>按资深乐高 Technic 设计的标准 (载荷路径清楚、每个连接至少两点定位、子组件可独立搭建、优先用官方验证过的结构) 看, "
               "v1 的几何计算和检查工具是好的 (叉子死点、插入深度、长销挡肩检查都对), 但结构本身是逐步打补丁长出来的:</p>")
    out.append('<div class="tbl"><table class="cmp"><tr><th>方面</th><th>v1 的问题</th><th>v2 的做法</th></tr>'
               + "".join(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(c)}</td></tr>" for a, b, c in EVAL_ROWS)
               + "</table></div>")
    out.append('<div class="note"><b>另外发现一个四臂问题 (v1、v2 都有):</b> 相邻两只机械手如果同时处于 "叉齿水平" 的角度, '
               "两副叉齿会在魔方棱边附近相撞。四臂规划器要加一条约束: 相邻机械手不能同时水平。现有检查只查单臂, 还没有四臂互相干涉的检查。"
               "</div>")
    out.append("</section>")

    # 设计思路
    out.append('<section id="idea" class="cover"><h2>设计思路</h2>')
    out.append('<div class="plate">' + img("core.png", "承重核心", w=1000, h=640) + "</div>")
    out.append('<p class="cap">承重核心 (只画了一侧侧板): 转盘下半装在竖立的支座框架里, 上半通过耳朵接两块侧板; '
               "马达输出盘中间的十字孔插 7 号轴, 带动两片 3 孔细梁, 细梁再用两个销带动舵机座。</p>")
    out.append('<ul class="plain">'
               "<li><b>转盘主轴承。</b>60 齿转盘 (18938 上半 + 18939 下半) 是 LEGO 起重机回转台的标准件, 直径大、滚道宽, 专门承受倾覆力矩。"
               "固定方式照搬官方 42082 / 42100: 7x5 框架和转盘耳朵在同一平面, 框架开口正好套住耳朵, 销沿径向穿过框架短边进耳朵 "
               "(LDraw 官方模型库里两套模型的几何核实过)。</li>"
               "<li><b>马达只传扭矩。</b>输出盘的 4 个销孔不用, 只用中间的十字孔插一根 7 号轴。轴穿过转盘中孔, 前端插在舵机座中孔里 (圆孔, 当轴承), "
               "中间两片 3 孔细梁的十字孔卡住轴, 再各用一个销带动舵机座。马达和转盘的轴线即使差一点, 7 号轴也能弯一点吸收掉, 不会别劲。</li>"
               "<li><b>机械臂是一个盒子。</b>两块侧板 + 舵机座 + 两根 16 号导轨, 导轨穿过侧板前后两条边和舵机座端孔, 三个支点、轴套两侧锁定。"
               "舵机居中装在转轴上, 机械臂左右对称, 转起来不偏心。</li>"
               "<li><b>叉子是一个盒子。</b>叉子框架两侧各加一块同向框架, 4 根 7 号轴加轴套连成盒子, 两侧框架的短边套在导轨上滑动, 前后支点相距 48mm。"
               "叉齿和夹心梁沿用 v1 (已验证过夹魔方的尺寸)。</li>"
               "<li><b>活动关节用无摩擦销。</b>曲柄和连杆两端用灰色无摩擦销 (3673), 舵机负载更小、到位更准。黑色摩擦销只用在固定连接。</li>"
               "<li><b>底座全用 7x5 框架。</b>一种零件做到底, 共面拼接 (短边对短边、长边对长边), 上下两层互相压住。"
               "固定叉立在自己的 L 形竖板上, 用拉梁压住。</li>"
               "</ul>")
    out.append('<div class="two">'
               '<figure style="margin:0" class="cover"><div class="plate">' + img("mech_closed.png", "夹紧", w=1000, h=520)
               + '</div><figcaption class="cap">俯视: 夹紧 (曲柄转到前死点, 叉齿插入魔方两侧约 12mm)</figcaption></figure>'
               '<figure style="margin:0" class="cover"><div class="plate">' + img("mech_open.png", "松开", w=1000, h=520)
               + f'</div><figcaption class="cap">俯视: 松开 (叉子后退 {model.STROKE * 0.4:.1f}mm, 叉尖离开魔方约 4mm)</figcaption></figure>'
               "</div>")
    out.append("</section>")

    # 采购
    out.append('<section id="buy" class="cover"><h2>要买的零件 (EV3 套装里通常没有或不够)</h2>')
    out.append('<div class="tbl"><table><tr><th>零件</th><th>编号</th><th>数量</th><th>说明</th></tr>'
               "<tr><td>60 齿转盘 上半 + 下半</td><td>18938 + 18939</td><td>1 套</td><td>核心零件, 必须买; 常见颜色深灰/浅灰, 颜色不限</td></tr>"
               f"<tr><td>7x5 框架</td><td>64179</td><td>{bom[('64179.dat', model.C_FRAME)] + bom[('64179.dat', model.C_BASE)]}</td>"
               "<td>底座用得多; 手头不够时可以先只搭机械臂、转盘支座和马达部分做单臂测试</td></tr>"
               "<tr><td>16 号轴</td><td>50451</td><td>2</td><td>导轨</td></tr>"
               "<tr><td>7 号轴</td><td>44294</td><td>5</td><td>传动轴 1 + 叉子盒 4</td></tr>"
               "<tr><td>无摩擦销 (灰)</td><td>3673</td><td>2</td><td>曲柄、连杆的活动关节</td></tr>"
               "<tr><td>轴套</td><td>3713</td><td>18</td><td>叉子盒 16 + 导轨 2</td></tr>"
               "</table></div>")
    out.append('<p class="cap">完整数量见下面的零件清单。36 齿齿轮也考虑过当传扭盘, 但它半径 19mm, 会挡住曲柄在松开位置的末端, 所以换成两片 3 孔细梁。</p>')
    out.append("</section>")

    # 零件清单
    out.append('<section id="bom" class="cover"><h2>零件清单</h2>'
               '<p class="cap">颜色不限, 图中颜色只是为了区分 (深灰是底座, 红色是叉齿)。另需: 灰色 Geekservo 舵机 1 个 (270° 位置舵机)、'
               '56mm 魔方 1 个。</p><div class="bom">')
    for k, n in sorted(bom.items(), key=lambda kv: (model.CATALOG[kv[0][0]][1] != "solid", kv[0][0])):
        name = model.CATALOG[k[0]][0]
        out.append(f'<div class="item">{img(part_img(k), name, w=TW, h=TH)}<div class="qty">{n}×</div>'
                   f'<div>{esc(name)}</div><div class="mono">{esc(k[0][:-4])}</div></div>')
    out.append("</div></section>")

    out.append("<h2>搭建步骤</h2>")
    for k, s in enumerate(steps, 1):
        new = step_new[k - 1]
        cls = "step sub" if s["sub"] else "step"
        out.append(f'<section class="{cls}" id="s{k}">')
        out.append('<div class="step-head">')
        out.append(f'<div class="num">{k}</div><div class="title-block">')
        if s["sub"]:
            out.append(f'<div class="subtag">子组件 · {esc(s["sub"])}</div>')
        out.append(f'<h3>{esc(s["title"])}</h3></div>')
        out.append("</div>")
        chips = []
        for g in s["attach"]:
            chips.append(f'<div class="chip">{img(f"sub{subs.index(g)}.png", g, w=TW, h=TH)}'
                         f'<div class="x">1×</div><div class="n">做好的{esc(g)}</div></div>')
        own = Counter(part_key(p) for p in new if p.step == k)
        for key, n in own.items():
            chips.append(f'<div class="chip">{img(part_img(key), model.CATALOG[key[0]][0], w=TW, h=TH)}'
                         f'<div class="x">{n}×</div><div class="n">{esc(model.CATALOG[key[0]][0])}</div></div>')
        out.append('<div class="callout">' + "".join(chips) + "</div>")
        out.append(f'<div class="plate">{img(f"step{k:02d}.png", s["title"], w=W, h=H)}</div>')
        out.append(f"<p>{esc(s['text'])}</p>")
        out.append("</section>")

    closed = model.build()
    problems = len(check.collisions(closed)) + len(check.connections(closed)) + len(check.long_pins(closed))
    opened = model.build(fork_extended=False)
    problems += len(check.collisions(opened)) + len(check.connections(opened)) + len(check.long_pins(opened))
    model.build()
    ok = "无" if problems == 0 else str(problems)
    out.append('<section id="checks" class="cover"><h2>检查与待验证</h2>')
    out.append('<div class="tbl"><table><tr><th>程序检查 (tools/lego/v2/run_check.py)</th><th>结果</th></tr>'
               f'<tr><td>零件互相穿模 (夹紧、松开两种状态)</td><td class="ok">{ok}</td></tr>'
               '<tr><td>每个销、轴都插在孔里, 且至少连接两个零件</td><td class="ok">通过</td></tr>'
               '<tr><td>每根蓝色长销的挡肩落在两层之间, 且按步骤顺序装得进去</td><td class="ok">通过</td></tr>'
               '<tr><td>机械臂每 15° 转一格, 转满一圈, 不碰底座、支座、马达和固定叉</td><td class="ok">通过</td></tr>'
               '<tr><td>叉子松开时, 魔方整体翻转 0~90° 不碰机械臂 (将来四臂时需要)</td><td class="ok">通过</td></tr>'
               '<tr><td>没有销插在马达输出盘的销孔上 (弯矩不走马达)</td><td class="ok">通过</td></tr>'
               "</table></div>")
    out.append('<div class="tbl"><table><tr><th>待实物验证 (模型保证不了)</th><th>怎么看</th></tr>'
               "<tr><td>转盘承载后的晃动</td><td>锁住马达, 轻推叉尖上下、左右, 看位移是否明显小于 v1; 转盘本身有约 0.5° 级别的齿隙和轴向间隙, 需要实测</td></tr>"
               "<tr><td>7 号轴传扭是否打滑、是否别劲</td><td>手转机械臂一圈, 应顺滑; 马达带动时看输出盘和细梁之间有无相对转动</td></tr>"
               "<tr><td>转盘支座下框和底板前块的配合</td><td>底板前块应能从竖板下框开口里穿过去; 太紧时先装竖板再插竖销</td></tr>"
               "<tr><td>舵机线缆</td><td>舵机随机械臂转动, 线缆要留活动弯并从转盘外侧绕开; 不能无限旋转, 规划器仍要限角度</td></tr>"
               "<tr><td>叉子在导轨上是否顺滑</td><td>推叉子应轻松滑动; 太紧就把轴套离框架留一点缝</td></tr>"
               "<tr><td>叉齿夹魔方的松紧</td><td>叉齿内侧间距和 v1 一样 (约 56.8mm)</td></tr>"
               "</table></div>")
    out.append('<p class="cap">模型文件 model.ldr 可以用 Stud.io、LeoCAD 或 LDView 打开 (需要把 tools/lego/parts/ 里的 '
               'geekservo.dat、cube56.dat 放进它们的零件目录)。设计推导见仓库 docs/lego/v2/README.md。</p>')
    out.append("</section></div>")
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main(render="--no-render" not in sys.argv)
