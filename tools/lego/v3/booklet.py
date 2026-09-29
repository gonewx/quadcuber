"""生成 v3 (四臂整机) 搭建说明书: docs/lego/v3/index.html、步骤图、零件缩略图和 model.ldr。

用法 (先在另一个终端启动 ../render/server.py):
    cd tools/lego/v3 && python booklet.py [--no-render]

渲染和样式沿用 v1 (../render/render.js、../booklet.py 的 CSS), 这里只换模型和文字。
"""

import html
import importlib.util
import json
import math
import os
import subprocess
import sys
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.append(os.path.join(HERE, ".."))

import model  # noqa: E402
import run_check  # noqa: E402,F401  (补 CONNECTOR_LEN 和豁免规则)

_spec = importlib.util.spec_from_file_location("booklet_v1", os.path.join(HERE, "..", "booklet.py"))
_v1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_v1)

OUT = os.path.join(HERE, "..", "..", "..", "docs", "lego", "v3")
IMG = os.path.join(OUT, "img")
WORK = os.path.join(HERE, "..", ".cache", "work", "v3")
V1_URL = "https://claude.ai/artifact/BWgtEpkX4PGRGnYzvNV2L4"
V2_URL = "https://claude.ai/artifact/9yGEt1ogaxxmStkyxYWYBL"
W, H = 1200, 860
TW, TH = 260, 200


def visible_parts(parts, k):
    st = model.STEPS
    sub = st[k - 1]["sub"]
    attach_at = {}
    for i, s in enumerate(st, 1):
        for g in s["attach"]:
            attach_at.setdefault(g, i)
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
    new = [p for p in vis if p.step == k or (model.STEPS[p.step - 1]["sub"] in s["attach"] and s["sub"] is None
                                             and model.STEPS[p.step - 1]["sub"] != "底座")]
    old = [p for p in vis if p not in new]
    if s["focus"] == "module":
        fit_old = [p for p in old if p.arm == "L"]
    elif s["focus"] == "new":
        fit_old = []
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


def write(path, text):
    with open(path, "w") as f:
        f.write(text)
    return path


def main(render=True):
    os.makedirs(IMG, exist_ok=True)
    os.makedirs(WORK, exist_ok=True)
    parts = model.build()
    steps = model.STEPS
    jobs = []
    step_new = []
    for k in range(1, len(steps) + 1):
        text, new = ldr_for_step(parts, k)
        path = write(os.path.join(WORK, f"step{k:02d}.ldr"), text)
        yaw, pitch = steps[k - 1]["view"]
        first_step = k == 1 or steps[k - 1]["sub"] != steps[k - 2]["sub"] and steps[k - 1]["sub"] is not None
        opts = {"w": W, "h": H, "yaw": yaw, "pitch": pitch, "fitFrom": 1 if steps[k - 1]["focus"] != "all" else 0,
                "margin": 0.07}
        if steps[k - 1]["focus"] == "all":
            opts["fitFrom"] = 1
        if not first_step:
            opts.update(highlight=2, fadeOld=True)
        jobs.append({"model": path, "out": os.path.join(IMG, f"step{k:02d}.png"), "opts": opts})
        step_new.append(new)

    keys = OrderedDict()
    for p in parts:
        keys.setdefault(part_key(p), p)
    for (name, color), p in keys.items():
        fn = f"part_{name[:-4]}_{color}.png"
        path = write(os.path.join(WORK, fn.replace(".png", ".ldr")),
                     f"0 part\n1 {color} 0 0 0 1 0 0 0 1 0 0 0 1 {name}\n")
        jobs.append({"model": path, "out": os.path.join(IMG, fn),
                     "opts": {"w": TW, "h": TH, "yaw": 35, "pitch": 28, "margin": 0.12}})

    subs = OrderedDict()
    for s in steps:
        if s["sub"]:
            subs.setdefault(s["sub"], None)
    for g in subs:
        gp = [p for p in parts if steps[p.step - 1]["sub"] == g and p.arm in ("L", None)]
        path = write(os.path.join(WORK, f"sub_{g}.ldr"), "0 sub\n" + "\n".join(p.ldraw() for p in gp) + "\n")
        idx = list(subs).index(g)
        jobs.append({"model": path, "out": os.path.join(IMG, f"sub{idx}.png"),
                     "opts": {"w": TW, "h": TH, "yaw": 35, "pitch": 28, "margin": 0.1}})

    # 封面: 整机 (夹紧) 和俯视
    whole = model.to_ldr(model.build())
    for tag, yaw, pitch in (("cover", 35, 28), ("top", 0, 89)):
        path = write(os.path.join(WORK, f"{tag}.ldr"), whole)
        jobs.append({"model": path, "out": os.path.join(IMG, f"{tag}.png"),
                     "opts": {"w": 1400, "h": 900 if tag == "cover" else 1100, "yaw": yaw, "pitch": pitch,
                              "margin": 0.04}})
    # 单个模块的机械头: 夹紧 / 松开, 从侧面看 (视线沿 Z)
    for tag, s in (("closed", 0.0), ("open", model.OPEN_S)):
        ps = [p for p in model.build({"L": (s, 0.0)}) if (p.arm == "L" and p.pos[0] > -330) or p.name == "cube56.dat"]
        path = write(os.path.join(WORK, f"mech_{tag}.ldr"), "0 mech\n" + "\n".join(p.ldraw() for p in ps) + "\n")
        jobs.append({"model": path, "out": os.path.join(IMG, f"mech_{tag}.png"),
                     "opts": {"w": 1000, "h": 620, "yaw": 0, "pitch": 0, "margin": 0.05}})
    # 舵机曲柄滑块: 夹紧 / 松开
    for tag, s in (("closed", 0.0), ("open", model.OPEN_S)):
        ps = [p for p in model.build({"L": (s, 0.0)}, with_cube=False) if p.arm == "L" and p.pos[0] < -250]
        path = write(os.path.join(WORK, f"servo_{tag}.ldr"), "0 servo\n" + "\n".join(p.ldraw() for p in ps) + "\n")
        jobs.append({"model": path, "out": os.path.join(IMG, f"servo_{tag}.png"),
                     "opts": {"w": 1000, "h": 620, "yaw": 20, "pitch": 30, "margin": 0.05}})
    # 翻转状态: L、R 夹紧转到一半, F、B 松开
    flip = model.build({"L": (0.0, 45.0), "R": (0.0, -45.0), "F": (model.OPEN_S, 0.0), "B": (model.OPEN_S, 0.0)})
    for p in flip:
        if p.name == "cube56.dat":
            p.rot = model.rot_x(45) @ p.rot
    path = write(os.path.join(WORK, "flip.ldr"), model.to_ldr(flip))
    jobs.append({"model": path, "out": os.path.join(IMG, "flip.png"),
                 "opts": {"w": 1400, "h": 900, "yaw": 35, "pitch": 28, "margin": 0.04}})
    model.build()

    if render:
        jobs_path = write(os.path.join(WORK, "jobs.json"), json.dumps(jobs))
        env = dict(os.environ)
        env.setdefault("PLAYWRIGHT_MODULE", "/opt/node22/lib/node_modules/playwright")
        subprocess.run(["node", "render.js", jobs_path], cwd=os.path.join(HERE, "..", "render"), check=True, env=env)

    write(os.path.join(OUT, "model.ldr"), model.to_ldr(parts, "quadcuber 四臂整机 v3"))
    write_html(parts, step_new, keys, list(subs))


# ---- HTML ----------------------------------------------------------------------

CSS = _v1.CSS + """
.cmp td:first-child{white-space:nowrap;font-weight:600}
.cmp td{min-width:9em}
.lead{font-size:16px}
ul.plain{margin:0;padding-left:1.2em;display:grid;gap:6px;max-width:70ch}
"""

EVAL_ROWS = [
    ("整机形态", "只有单臂; 四臂怎么排、底座怎么连都没有设计, 也没有四臂之间的干涉检查",
     "四个一样的模块两两垂直, 固定在一个整体底座上", "四个相同模块 + 16 块框架的风车形底座, 孔位保证四根轴线过魔方中心、两两垂直; 四臂干涉按全部状态组合扫描过"),
    ("转动部分", "转盘上装着舵机、叉子盒、两根 16 号导轨, 从转盘端面到魔方约 144mm, 转动惯量大",
     "夹爪短而轻, 马达和舵机都不跟着转", "转动的只有转盘上半、两块侧板、夹指、连杆和推杆, 约 52mm 长, 没有舵机和马达"),
    ("夹紧", "U 形叉沿轴向插入, 水平时没有压紧力, 曲柄停在死点不等于锁紧 (外部评审 ① ②)",
     "两片夹指从两侧合拢夹住魔方", "两片会转的夹指 + 肘节连杆: 连杆推到死点时魔方的反推力沿连杆方向互相抵消, 夹指推不开, 舵机不受力"),
    ("旋转范围", "舵机随机械手转动, 线缆会缠, 规划器必须限角度 (±270° 时规划慢 20 多倍)",
     "机械手可以连续旋转", "舵机固定在后面的平台上, 经穿过转盘中孔的推杆开合夹爪; 机械手可以无限旋转, 规划器不需要角度限制"),
    ("驱动", "马达输出轴直接带机械手", "—",
     "马达偏到侧面, 36 齿齿轮带 60 齿转盘外圈, 扭矩放大 1.67 倍, 马达的回差和编码器误差在机械手上缩小 1.67 倍; 输出轴不承受弯矩"),
]


def write_html(parts, step_new, keys, subs):
    steps = model.STEPS
    esc = html.escape
    bom = Counter(part_key(p) for p in parts if p.name != "cube56.dat")
    byname = Counter(p.name for p in parts if p.name != "cube56.dat")
    n_parts = sum(n for k, n in bom.items() if k[0] not in ("95658.dat", "geekservo.dat"))
    beta = math.degrees(model.jaw_beta(model.OPEN_S))

    def img(src, alt, cls="", w=None, h=None):
        size = f' width="{w}" height="{h}"' if w else ""
        return f'<img src="img/{src}" alt="{esc(alt)}" class="{cls}" loading="lazy"{size}>'

    def part_img(k):
        return f"part_{k[0][:-4]}_{k[1]}.png"

    out = []
    out.append("<title>quadcuber 四臂 v3</title>")
    out.append('<link rel="preconnect" href="https://fonts.googleapis.com">')
    out.append('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700'
               '&family=JetBrains+Mono&family=Noto+Sans+SC:wght@400;700&display=swap">')
    out.append(f"<style>{CSS}</style>")
    out.append('<div class="wrap">')

    out.append('<header class="cover">')
    out.append('<div class="eyebrow">quadcuber · 四臂整机 v3 · 按 CubeStormer 3 的思路重新设计 · 搭建说明书</div>')
    out.append("<h1>四臂整机: 死点锁紧夹爪 + 不随转的舵机</h1>")
    out.append('<p class="lead">v2 解决了 "机械臂挂在马达输出轴上" 的问题, 但它仍然是一只单臂, 转动部分又长又重, 舵机跟着转。'
               "CubeStormer 3 这一级别的机器, 专业性体现在整机: 四只机械手又短又轻、夹得住也松得开、能连续旋转, 四只之间互不干涉。"
               "v3 按这个目标从整机重新设计, 自成一套模型和检查。"
               f'之前的版本都保留不动: <a href="{V1_URL}">v1 大马达版</a>、<a href="{V2_URL}">v2 转盘版</a>。</p>')
    out.append('<div class="plate">' + img("cover.png", "四臂整机总览", w=1400, h=900) + "</div>")
    out.append('<div class="facts">'
               f'<div class="fact"><b>{len(steps)}</b><span>个步骤 (一个模块的完整步骤, 其余三个照做)</span></div>'
               f'<div class="fact"><b>{n_parts}</b><span>个乐高零件, 另加 EV3 大马达和 Geekservo 各 4 个</span></div>'
               '<div class="fact"><b>约 52 mm</b><span>转动部分长度 (v2 约 144mm)</span></div>'
               '<div class="fact"><b>无限</b><span>机械手旋转范围 (舵机不跟着转)</span></div>'
               "</div>")
    out.append('<nav class="toc"><a href="#eval">v2 评估</a><a href="#idea">设计思路</a><a href="#four">四臂检查</a>'
               '<a href="#buy">要买的零件</a><a href="#bom">零件清单</a>'
               + "".join(f'<a href="#s{k}">{k}. {esc(s["title"])}</a>' for k, s in enumerate(steps, 1))
               + '<a href="#checks">检查与待验证</a><a href="#safety">上电前</a></nav>')
    out.append("</header>")

    out.append('<section id="eval" class="cover"><h2>v2 评估: 离 CubeStormer 3 的专业水准还差在整机</h2>')
    out.append("<p>CubeStormer 3 没有公开图纸和源码, 下表 \"CS3 级别的做法\" 一列是从公开视频能看到的整体特征归纳出来的, "
               "不是对它内部结构的复刻。v3 的每个具体结构都是在这里重新推导、并用程序检查过的。</p>")
    out.append('<div class="tbl"><table class="cmp"><tr><th>方面</th><th>v2</th><th>CS3 级别的做法</th><th>v3</th></tr>'
               + "".join(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(c)}</td><td>{esc(d)}</td></tr>"
                         for a, b, c, d in EVAL_ROWS)
               + "</table></div>")
    out.append("</section>")

    out.append('<section id="idea" class="cover"><h2>设计思路</h2>')
    out.append('<div class="two">'
               '<figure style="margin:0" class="cover"><div class="plate">' + img("mech_closed.png", "夹紧", w=1000, h=620)
               + '</div><figcaption class="cap">侧视, 夹紧: 两根黄色连杆和推杆垂直 (死点), 夹指合拢在魔方外层上下两侧</figcaption></figure>'
               '<figure style="margin:0" class="cover"><div class="plate">' + img("mech_open.png", "松开", w=1000, h=620)
               + f'</div><figcaption class="cap">侧视, 松开: 推杆后退 {model.OPEN_S * 0.4:.0f}mm, 夹指张开约 {beta:.0f}°</figcaption></figure>'
               "</div>")
    out.append('<ul class="plain">'
               "<li><b>肘节锁紧的夹指。</b>每只机械手两片 7 孔粗梁当夹指, 绕根部的 5 号轴转动。十字接头往前推, 两根连杆把夹指根部往外撑, 前端合拢。"
               "推到连杆和推杆垂直 (死点) 时, 魔方把夹指往外推的力沿连杆传到十字接头, 上下两根互相抵消, 推杆上没有分力, 所以舵机不受力, "
               "夹指也推不开。水平姿态下同样夹得住, 不再依赖摩擦。</li>"
               "<li><b>舵机不跟着转。</b>舵机固定在机械手后面的平台上, 曲柄和连杆同样拉到死点, 通过十字块推拉一根 12 号轴。"
               "推杆穿过转盘中孔和导向框架两条边上的圆孔, 机械手转动时推杆跟着转, 十字块在推杆上一起转 (两侧半轴套锁住轴向位置)。"
               "转动部分没有任何线缆。</li>"
               "<li><b>齿轮带转盘外圈。</b>60 齿转盘仍然是主轴承 (v2 的结论保留), 但不再用马达输出轴直接带, 而是马达偏到侧面, "
               "36 齿齿轮和转盘外圈啮合。这样转盘中孔留给推杆, 马达只传扭矩, 1.67 倍减速同时缩小马达回差。</li>"
               "<li><b>模块化。</b>一个模块 = 竖墙 + 转盘 + 马达 + 舵机平台 + 机械头, 四个完全一样。底座的孔位让四根轴线严格过魔方中心、两两垂直, "
               "不用调。模块整体往魔方方向挪了半个孔距, 这是让相邻模块的孔位对得上的关键 (否则会差半个孔)。</li>"
               "</ul>")
    out.append('<div class="two">'
               '<figure style="margin:0" class="cover"><div class="plate">' + img("servo_closed.png", "舵机夹紧", w=1000, h=620)
               + '</div><figcaption class="cap">舵机侧, 夹紧: 曲柄和连杆拉成一条直线</figcaption></figure>'
               '<figure style="margin:0" class="cover"><div class="plate">' + img("servo_open.png", "舵机松开", w=1000, h=620)
               + '</div><figcaption class="cap">舵机侧, 松开: 曲柄转过约 115°, 十字块带推杆后退</figcaption></figure>'
               "</div>")
    out.append("</section>")

    out.append('<section id="four" class="cover"><h2>四臂检查 (tools/lego/v3/four_arm.py)</h2>')
    out.append('<div class="plate">' + img("flip.png", "整体翻转", w=1400, h=900) + "</div>")
    out.append('<p class="cap">整体翻转到一半: L、R 夹着魔方转, F、B 松开保持竖直。</p>')
    out.append('<div class="tbl"><table><tr><th>检查</th><th>结果</th></tr>'
               "<tr><td>一只机械手夹紧或松开, 从竖直转到水平 (每 5° 一格), 两侧邻居在 夹紧/松开 × 竖直/水平 的 16 种组合下</td>"
               "<td>邻居竖直时全部不碰; 邻居水平时, 转到 80° 左右会和邻居的夹指相撞</td></tr>"
               "<tr><td>拧一层时, 邻居 (夹紧、竖直) 的零件离转轴的最近距离</td><td class=\"ok\">110 LDU, 比魔方层的扫掠半径大 4.4mm</td></tr>"
               "<tr><td>整体翻转时, 邻居 (松开、竖直) 的零件离转轴的最近距离</td><td class=\"ok\">105 LDU, 比魔方的扫掠半径大 2.4mm (按尖角算)</td></tr>"
               "</table></div>")
    out.append('<div class="note"><b>相邻两只机械手不能同时水平。</b>这是任何从外侧夹住魔方的夹爪都有的几何限制: 两只相邻机械手都转到水平时, '
               "两副夹指会在魔方棱边外面的同一个位置相遇。v3 把它写进了规划器的可选约束 "
               "(<code>python -m quadcuber plan ... --no-adjacent-horizontal</code>): 转动中的机械手, 两侧邻居必须竖直且不同时转动。"
               "按现在的估算耗时, 20 步随机序列平均从 7.95 秒变成 9.69 秒 (约 +22%)。</div>")
    out.append("</section>")

    out.append('<section id="buy" class="cover"><h2>要买的零件</h2>')
    out.append('<div class="tbl"><table><tr><th>零件</th><th>编号</th><th>整机数量</th><th>说明</th></tr>'
               "<tr><td>60 齿转盘 上半 + 下半</td><td>18938 + 18939</td><td>4 套</td><td>每只机械手 1 套; v2 已经买了 1 套的话再买 3 套</td></tr>"
               "<tr><td>36 齿双面锥齿轮</td><td>32498</td><td>4</td><td>和转盘外圈啮合</td></tr>"
               f"<tr><td>7x5 框架</td><td>64179</td><td>{byname['64179.dat']}</td><td>底座 16 块, 每个模块 13 块</td></tr>"
               "<tr><td>十字轴接头 (带圆孔)</td><td>32039</td><td>4</td><td>夹爪的十字接头</td></tr>"
               "<tr><td>十字块 1x2</td><td>6536</td><td>4</td><td>推杆上的十字块</td></tr>"
               "<tr><td>2 孔细梁 (两端十字孔)</td><td>41677</td><td>4</td><td>舵机曲柄</td></tr>"
               "<tr><td>轴销 / 无摩擦长销 / 无摩擦销</td><td>3749 / 32556a / 3673</td><td>4 / 4 / 8</td><td>活动关节</td></tr>"
               f"<tr><td>摩擦销</td><td>2780</td><td>{byname['2780.dat']}</td><td>多买一些备用</td></tr>"
               "<tr><td>EV3 大马达 / Geekservo 灰色</td><td>—</td><td>4 / 4</td><td>现在只有 2 个大马达, 还缺 2 个</td></tr>"
               "</table></div>")
    out.append('<p class="cap">可以先只搭一个模块 (底座只要它那一排 4 块框架) 做单臂实测, 验证夹持和转速后再买齐四套。</p>')
    out.append("</section>")

    out.append('<section id="bom" class="cover"><h2>零件清单 (整机)</h2>'
               '<p class="cap">颜色不限, 图中颜色只是为了区分 (深灰是底座, 红色是夹指, 黄色是连杆)。另需 56mm 魔方 1 个。</p><div class="bom">')
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
        if s["title"] == "装另外三个机械手":
            chips.append('<div class="chip"><div class="x">3×</div><div class="n">照第 2~18 步做好的机械手模块</div></div>')
            own = Counter()
        else:
            own = Counter(part_key(p) for p in new if p.step == k)
        for key, n in own.items():
            chips.append(f'<div class="chip">{img(part_img(key), model.CATALOG[key[0]][0], w=TW, h=TH)}'
                         f'<div class="x">{n}×</div><div class="n">{esc(model.CATALOG[key[0]][0])}</div></div>')
        out.append('<div class="callout">' + "".join(chips) + "</div>")
        out.append(f'<div class="plate">{img(f"step{k:02d}.png", s["title"], w=W, h=H)}</div>')
        out.append(f"<p>{esc(s['text'])}</p>")
        out.append("</section>")

    out.append('<section id="checks" class="cover"><h2>检查与待验证</h2>')
    out.append('<div class="tbl"><table><tr><th>程序检查</th><th>结果</th></tr>'
               '<tr><td>单模块夹紧、松开, 以及夹指行程中间 7 个位置: 零件互相穿模</td><td class="ok">无</td></tr>'
               '<tr><td>整机: 每个销、轴都插在孔里且至少连接两个零件; 长销挡肩位置</td><td class="ok">通过</td></tr>'
               '<tr><td>四臂转动干涉 (上一节)</td><td class="ok">只有 "相邻两只同时水平", 已写进规划器约束</td></tr>'
               "</table></div>")
    out.append('<div class="tbl"><table><tr><th>待实物验证 (模型保证不了)</th><th>怎么看</th></tr>'
               "<tr><td>夹指预紧</td><td>死点位置按 56mm 魔方算, 实际魔方尺寸有误差。建议在两片夹指前端之间套一根橡皮筋, 或在夹指内侧贴一层薄橡胶, "
               "让死点时有一点压紧量。夹紧后用手扭魔方外层, 看夹指是否打滑</td></tr>"
               "<tr><td>舵机死点标定</td><td>装曲柄前先把舵机转到 \"夹紧\" 角度; 装好后微调角度, 让曲柄和连杆正好拉直 (过死点一点点更好, 需加限位)</td></tr>"
               "<tr><td>马达前板的销孔</td><td>模型假设马达靠近输出盘的侧面两个孔可以插摩擦销; 如果不是通孔或深度不够, 改用 TRACK3R 的耳朵固定加一根竖梁</td></tr>"
               "<tr><td>齿轮啮合和回差</td><td>36 齿和 60 齿转盘外圈中心距 3 个孔 (官方组合); 手转机械手应顺滑, 马达锁住时晃动机械手看回差</td></tr>"
               "<tr><td>舵机平台刚度</td><td>平台前端接墙、后端支腿立在桌上; 舵机开合时看平台是否弹动, 必要时后端支腿和底座之间加连接</td></tr>"
               "<tr><td>推杆在转动时的摩擦</td><td>推杆随机械手一起转, 十字块在导向框架里跟着转; 手转机械手时应不卡, 半轴套别压太紧</td></tr>"
               "<tr><td>整体翻转的间隙</td><td>按尖角算只有 2.4mm; 实际魔方有圆角, 余量更大, 但要用自己的魔方实测</td></tr>"
               "<tr><td>魔方尺寸</td><td>按 56mm 魔方设计; 57mm 魔方放不进</td></tr>"
               "</table></div>")
    out.append('<p class="cap">模型文件 model.ldr 可以用 Stud.io、LeoCAD 或 LDView 打开 (需要把 tools/lego/parts/ 里的 '
               'geekservo.dat、cube56.dat 放进它们的零件目录)。设计推导见仓库 docs/lego/v3/README.md。</p>')
    out.append("</section>")

    out.append('<section id="safety" class="cover"><h2>上电前</h2><ul class="plain">'
               "<li>4 个舵机用单独的 5V 降压电源 (DSN5000 先调到 5.0V 再接), 不要从 Pico 取电; 四个同时动作的峰值电流按 3A 以上准备。</li>"
               "<li>4 个大马达由 2 块 DRV8833 驱动, 马达电压不超过 10.8V (用 9V)。</li>"
               "<li>编码器信号照旧经 10k/20k 分压后再接 Pico, 四臂一共 8 路。</li>"
               "<li>第一次上电时先不放魔方, 单独开合每个夹爪, 确认曲柄停在死点、不顶死舵机 (舵机持续发热说明顶死了)。</li>"
               "</ul></section></div>")
    write(os.path.join(OUT, "index.html"), "\n".join(out) + "\n")


if __name__ == "__main__":
    main(render="--no-render" not in sys.argv)
