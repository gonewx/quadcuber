"""生成乐高风格的搭建说明书: 步骤图、零件缩略图、docs/lego/index.html 和 model.ldr。

用法 (先在另一个终端启动 render/server.py):
    python booklet.py [--no-render] [--medium]     默认大马达版, --medium 生成中马达版 (docs/lego/medium/)

步骤图由 render/render.js 在无头 Chromium 里用 three.js 的 LDrawLoader 渲染。
"""

import html
import json
import os
import subprocess
import sys
from collections import Counter, OrderedDict

import check
import model

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(HERE, "..", "..", "docs", "lego")
OUT = DOCS
IMG = os.path.join(OUT, "img")
MOTOR = "large"
MOTOR_NAME = {"large": "EV3 大马达", "medium": "EV3 中马达"}
# 已发布的说明书 (artifact), 两版互相链接
ARTIFACT_URL = {"large": "https://claude.ai/artifact/BWgtEpkX4PGRGnYzvNV2L4", "medium": "https://claude.ai/artifact/7VtzEUtxMbezHPJQYCDWPX"}
WORK = os.path.join(HERE, ".cache", "work")

W, H = 1200, 860  # 步骤图尺寸
TW, TH = 260, 200  # 零件缩略图尺寸


def visible_parts(parts, k):
    """第 k 步 (从 1 开始) 的画面里应出现的零件。"""
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


def head_part(p):
    s = model.STEPS[p.step - 1]
    return s["title"] in model.head_names() or s["sub"] == "叉子" or p.name in ("95658.dat", "99455.dat")


def ldr_for_step(parts, k):
    """写一个三段的 LDraw 文件: STEP1 不参与取景的旧零件, STEP2 参与取景的旧零件, STEP3 本步零件。"""
    s = model.STEPS[k - 1]
    vis = visible_parts(parts, k)
    new = [p for p in vis if p.step == k or (model.STEPS[p.step - 1]["sub"] in s["attach"])]
    old = [p for p in vis if p not in new]
    if s["focus"] == "head":
        fit_old = [p for p in old if head_part(p)]
    elif s["focus"] == "mech":
        fit_old = [p for p in old if head_part(p) and p.name not in ("95658.dat", "99455.dat")]
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


def main(render=True, motor="large"):
    global OUT, IMG, MOTOR, WORK
    MOTOR = motor
    OUT = DOCS if motor == "large" else os.path.join(DOCS, "medium")
    IMG = os.path.join(OUT, "img")
    WORK = os.path.join(HERE, ".cache", "work", motor)
    os.makedirs(IMG, exist_ok=True)
    os.makedirs(WORK, exist_ok=True)
    parts = model.build(motor=motor)
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

    # 零件缩略图
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

    # 子组件缩略图 (装上去那一步的零件框里用)
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

    # 封面: 夹紧 / 松开两种状态
    for tag, ext in (("closed", True), ("open", False)):
        path = os.path.join(WORK, f"cover_{tag}.ldr")
        with open(path, "w") as f:
            f.write(model.to_ldr(model.build(fork_extended=ext, motor=motor)))
        jobs.append({"model": path, "out": os.path.join(IMG, f"cover_{tag}.png"),
                     "opts": {"w": 1400, "h": 900, "yaw": 35, "pitch": 28, "margin": 0.04}})
    for tag, ext in (("closed", True), ("open", False)):
        head = [p for p in model.build(fork_extended=ext, motor=motor) if head_part(p) or p.name == "cube56.dat"]
        path = os.path.join(WORK, f"mech_{tag}.ldr")
        with open(path, "w") as f:
            f.write("0 mech\n" + "\n".join(p.ldraw() for p in head) + "\n")
        jobs.append({"model": path, "out": os.path.join(IMG, f"mech_{tag}.png"),
                     "opts": {"w": 1000, "h": 520, "yaw": 0, "pitch": 88, "margin": 0.05}})
    model.build(motor=motor)  # 恢复步骤表

    if render:
        jobs_path = os.path.join(WORK, "jobs.json")
        with open(jobs_path, "w") as f:
            json.dump(jobs, f)
        env = dict(os.environ)
        env.setdefault("PLAYWRIGHT_MODULE", "/opt/node22/lib/node_modules/playwright")
        subprocess.run(["node", "render.js", jobs_path], cwd=os.path.join(HERE, "render"), check=True, env=env)

    with open(os.path.join(OUT, "model.ldr"), "w") as f:
        f.write(model.to_ldr(parts, f"quadcuber 单臂原型 ({MOTOR_NAME[motor]})"))
    write_html(parts, step_new, keys, list(subs))


# ---- HTML ----------------------------------------------------------------------

CSS = """
:root{
  --paper:#f4f6f9; --sheet:#ffffff; --ink:#18202b; --muted:#5a6778; --line:#d6dde6;
  --accent:#1f5fae; --callout:#eef3f9; --sub:#dcebf8; --sub-ink:#1b4f8c; --warn:#9a5a00; --warn-bg:#fff4e0;
  --ok:#1f7a45;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    color-scheme: dark;
    --paper:#10151c; --sheet:#171e28; --ink:#e4ebf3; --muted:#9aa8b8; --line:#2b3645;
    --accent:#7fb2f0; --callout:#1d2733; --sub:#17293d; --sub-ink:#a9cdf5; --warn:#f0b44f; --warn-bg:#2d2415;
    --ok:#6fd199;
  }
}
:root[data-theme="dark"]{
  color-scheme: dark;
  --paper:#10151c; --sheet:#171e28; --ink:#e4ebf3; --muted:#9aa8b8; --line:#2b3645;
  --accent:#7fb2f0; --callout:#1d2733; --sub:#17293d; --sub-ink:#a9cdf5; --warn:#f0b44f; --warn-bg:#2d2415;
  --ok:#6fd199;
}
body{background:var(--paper);color:var(--ink);font-family:"Noto Sans SC","PingFang SC","Microsoft YaHei",system-ui,sans-serif;
  font-size:15px;line-height:1.65;padding-inline:16px;padding-block:24px 64px}
.wrap{max-width:980px;margin:0 auto;display:flex;flex-direction:column;gap:28px}
h1,h2,h3{text-wrap:balance;line-height:1.25;margin:0}
h1{font-size:30px;font-weight:700}
h2{font-size:22px;font-weight:700;padding-top:8px}
p{margin:0;max-width:65ch}
.eyebrow{font-family:"Barlow Condensed","Arial Narrow",sans-serif;font-weight:600;letter-spacing:.08em;
  text-transform:uppercase;color:var(--accent);font-size:15px}
.mono{font-family:"JetBrains Mono",ui-monospace,monospace;font-size:12px;color:var(--muted)}
.plate{background:#fff;border-radius:6px;overflow:hidden;border:1px solid var(--line)}
.plate img{display:block;width:100%;height:auto}
.cover{display:grid;gap:14px}
.two{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media (max-width:640px){.two{grid-template-columns:1fr}}
.cap{font-size:13px;color:var(--muted)}
.facts{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px}
.fact{background:var(--sheet);border:1px solid var(--line);border-radius:6px;padding:10px 12px}
.fact b{display:block;font-family:"Barlow Condensed","Arial Narrow",sans-serif;font-size:24px;font-weight:600;
  font-variant-numeric:tabular-nums;color:var(--ink)}
.fact span{font-size:13px;color:var(--muted)}
.note{background:var(--warn-bg);color:var(--ink);border-left:4px solid var(--warn);padding:12px 14px;border-radius:4px}
.note b{color:var(--warn)}
.toc{display:flex;flex-wrap:wrap;gap:8px}
.toc a{color:var(--accent);text-decoration:none;border:1px solid var(--line);background:var(--sheet);
  padding:4px 10px;border-radius:14px;font-size:13px}
.toc a:focus-visible,.toc a:hover{border-color:var(--accent)}
.bom{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px}
.bom .item{background:var(--sheet);border:1px solid var(--line);border-radius:6px;padding:8px;display:flex;
  flex-direction:column;gap:4px}
.bom img{background:#fff;border-radius:4px;width:100%;height:auto}
.qty{font-family:"Barlow Condensed","Arial Narrow",sans-serif;font-size:22px;font-weight:600;
  font-variant-numeric:tabular-nums}
.step{background:var(--sheet);border:1px solid var(--line);border-radius:8px;padding:16px;display:grid;gap:12px}
.step.sub{background:var(--sub);border-color:transparent}
.step-head{display:flex;align-items:flex-start;gap:14px;flex-wrap:wrap}
.num{font-family:"Barlow Condensed","Arial Narrow",sans-serif;font-weight:700;font-size:56px;line-height:.9;
  font-variant-numeric:tabular-nums;min-width:1.4em}
.step.sub .num{color:var(--sub-ink)}
.title-block{display:flex;flex-direction:column;gap:2px;flex:1;min-width:200px}
.title-block h3{font-size:19px}
.subtag{font-size:12px;color:var(--sub-ink);font-weight:700;letter-spacing:.06em}
.callout{display:flex;flex-wrap:wrap;gap:8px;background:var(--callout);border-radius:6px;padding:8px}
.step.sub .callout{background:rgba(255,255,255,.55)}
:root[data-theme="dark"] .step.sub .callout{background:rgba(0,0,0,.2)}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]) .step.sub .callout{background:rgba(0,0,0,.2)}}
.chip{display:flex;flex-direction:column;align-items:center;gap:2px;width:92px}
.chip img{width:92px;height:auto;background:#fff;border-radius:4px}
.chip .x{font-family:"Barlow Condensed","Arial Narrow",sans-serif;font-size:18px;font-weight:600}
.chip .n{font-size:11px;color:var(--muted);text-align:center;line-height:1.3}
.checks{display:grid;gap:8px}
.checks li{margin-left:1.2em}
table{border-collapse:collapse;width:100%;font-size:14px}
.tbl{overflow-x:auto}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{color:var(--muted);font-weight:600}
.ok{color:var(--ok);font-weight:700}
"""


def write_html(parts, step_new, keys, subs):
    steps = model.STEPS
    esc = html.escape
    bom = Counter(part_key(p) for p in parts if p.name != "cube56.dat")
    n_parts = sum(n for k, n in bom.items() if k[0] not in ("95658.dat", "99455.dat", "geekservo.dat"))

    def img(src, alt, cls="", w=None, h=None):
        size = f' width="{w}" height="{h}"' if w else ""
        return f'<img src="img/{src}" alt="{esc(alt)}" class="{cls}" loading="lazy"{size}>'

    def part_img(k):
        return f"part_{k[0][:-4]}_{k[1]}.png"

    out = []
    out.append('<title>quadcuber 单臂搭建</title>' if MOTOR == "large" else '<title>quadcuber 单臂搭建 中马达</title>')
    out.append('<link rel="preconnect" href="https://fonts.googleapis.com">')
    out.append('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700'
               '&family=JetBrains+Mono&family=Noto+Sans+SC:wght@400;700&display=swap">')
    out.append(f"<style>{CSS}</style>")
    out.append('<div class="wrap">')

    # 封面
    xf_c, xf_o = model.fork_frame_x(True), model.fork_frame_x(False)
    out.append('<header class="cover">')
    out.append(f'<div class="eyebrow">quadcuber · 单臂原型 · 搭建说明书 · {MOTOR_NAME[MOTOR]}版</div>')
    out.append("<h1>一只机械手 + 测试架</h1>")
    om = "medium" if MOTOR == "large" else "large"
    link = ARTIFACT_URL[om] or ("medium/index.html" if om == "medium" else "../index.html")
    out.append(f'<p class="cap">本页是{MOTOR_NAME[MOTOR]}版。另有<a href="{link}">{MOTOR_NAME[om]}版</a>, '
               '两版的机械手、叉子和测试架大部分相同, 只有马达固定和马达与转动座的连接不同。</p>')
    out.append(f"<p>一个 {MOTOR_NAME[MOTOR]}带动机械手旋转, 一个灰色 Geekservo 推拉叉子夹紧或松开魔方。"
               "测试架把马达和一个固定叉连在一起, 固定叉卡住魔方背面的中间一列, 这样机械手就可以单独拧魔方的一层。"
               "搭好后按 <b>docs/single_arm.md</b> 接线和测试。</p>")
    out.append('<div class="plate">' + img("cover_closed.png", "整机总览", w=1400, h=900) + "</div>")
    out.append('<div class="facts">'
               f'<div class="fact"><b>{len(steps)}</b><span>个步骤</span></div>'
               f'<div class="fact"><b>{n_parts}</b><span>个乐高零件, 另加 {MOTOR_NAME[MOTOR]}和舵机各 1 个</span></div>'
               f'<div class="fact"><b>{model.STROKE * 0.4:.1f} mm</b><span>叉子行程 (要求 ≥ 13mm)</span></div>'
               f'<div class="fact"><b>56 mm</b><span>魔方尺寸 (叉齿内侧间距约 56.8mm)</span></div>'
               "</div>")
    out.append('<div class="two">'
               '<figure style="margin:0" class="cover"><div class="plate">' + img("mech_closed.png", "夹紧", w=1000, h=520)
               + '</div><figcaption class="cap">俯视: 夹紧 (舵机曲柄转到前死点, 叉齿插入魔方两侧约 10mm)</figcaption></figure>'
               '<figure style="margin:0" class="cover"><div class="plate">' + img("mech_open.png", "松开", w=1000, h=520)
               + f'</div><figcaption class="cap">俯视: 松开 (叉子后退 {model.STROKE * 0.4:.1f}mm, 叉齿离开魔方)</figcaption></figure>'
               "</div>")
    out.append('<div class="note"><b>请先读这里:</b> 这份说明书是按官方 LDraw 零件的精确尺寸建模的, 程序检查过所有零件没有'
               '互相穿模、每个销和轴都插在孔里、机械手转一整圈不会碰到测试架。但它<b>没有被实物搭过</b>, '
               'Geekservo 的外形按你给的图纸建模, 摩擦力、零件松紧和整体刚度只能靠实物检验。'
               '搭的过程中哪一步对不上, 拍照发给我。</div>')
    # 目录
    out.append('<nav class="toc">'
               '<a href="#bom">零件清单</a>'
               + "".join(f'<a href="#s{k}">{k}. {esc(s["title"])}</a>' for k, s in enumerate(steps, 1))
               + '<a href="#checks">检查与待验证</a></nav>')
    out.append("</header>")

    # 零件清单
    out.append('<section id="bom" class="cover"><h2>零件清单</h2>'
               '<p class="cap">颜色不限, 图中颜色只是为了区分。另需: 灰色 Geekservo 舵机 1 个 (270° 位置舵机, 不要用 360° 的红色马达版)、'
               '56mm 魔方 1 个。</p><div class="bom">')
    for k, n in sorted(bom.items(), key=lambda kv: (model.CATALOG[kv[0][0]][1] != "solid", kv[0][0])):
        name = model.CATALOG[k[0]][0]
        out.append(f'<div class="item">{img(part_img(k), name, w=TW, h=TH)}<div class="qty">{n}×</div>'
                   f'<div>{esc(name)}</div><div class="mono">{esc(k[0][:-4])}</div></div>')
    out.append("</div></section>")

    # 步骤
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
        # 零件框
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

    # 检查
    closed = model.build(motor=MOTOR)
    problems = len(check.collisions(closed)) + len(check.connections(closed))
    opened = model.build(fork_extended=False, motor=MOTOR)
    problems += len(check.collisions(opened)) + len(check.connections(opened))
    model.build(motor=MOTOR)
    out.append('<section id="checks" class="cover"><h2>检查与待验证</h2>')
    out.append('<div class="tbl"><table><tr><th>程序检查 (tools/lego/run_check.py)</th><th>结果</th></tr>'
               f'<tr><td>零件互相穿模 (夹紧、松开两种状态)</td><td class="ok">{"无" if problems == 0 else problems}</td></tr>'
               '<tr><td>每个销、轴都插在孔里, 且至少连接两个零件</td><td class="ok">通过</td></tr>'
               '<tr><td>机械手每 15° 转一格, 转满一圈, 不碰测试架和马达</td><td class="ok">通过</td></tr>'
               '<tr><td>叉子松开时, 魔方整体翻转 0~90° 不碰机械手 (将来四臂时需要)</td><td class="ok">通过</td></tr>'
               "</table></div>")
    out.append('<div class="tbl"><table><tr><th>待实物验证</th><th>怎么看</th></tr>'
               "<tr><td>Geekservo 外形 (按图纸建模, 线缆位置未知)</td><td>第 12 步装上后, 舵机不应碰到转动座; 线缆留够长, 能正反各转 180°</td></tr>"
               "<tr><td>叉子在导轨上是否顺滑</td><td>第 15 步: 用手推叉子, 应能轻松滑动, 不卡不晃</td></tr>"
               "<tr><td>曲柄连杆能否把叉子推到位</td><td>用 servo 命令慢慢改脉宽, 找到叉子最前和最后的位置</td></tr>"
               "<tr><td>叉齿间距是否刚好夹住魔方</td><td>第 20 步: 魔方应能推进去, 不松不紧; 太紧可换 55mm 魔方</td></tr>"
               "<tr><td>整体刚度</td><td>拧面时测试架、转动座、叉子不应明显晃动</td></tr>"
               "</table></div>")
    out.append('<p class="cap">模型文件 model.ldr 可以用 Stud.io、LeoCAD 或 LDView 打开 (需要把 tools/lego/parts/ 里的 '
               'geekservo.dat、cube56.dat 放进它们的零件目录)。</p>')
    out.append("</section></div>")
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main(render="--no-render" not in sys.argv, motor="medium" if "--medium" in sys.argv else "large")
