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
import shutil
import subprocess
import sys
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.append(os.path.join(HERE, ".."))

import ldraw  # noqa: E402
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


def _attach_info():
    """子组件 -> (第几步装上去, 装进哪个子组件; None 表示主线)。"""
    info = {}
    for i, s in enumerate(model.STEPS, 1):
        for g in s["attach"]:
            info.setdefault(g, (i, s["sub"]))
    return info


def _in_group(g, target, k, info, depth=0):
    """到第 k 步时, 子组件 g 的零件是否已经在 target 里 (子组件可以先装进另一个子组件, 如马达先装到竖墙上)。"""
    if g == target:
        return True
    if g is None or depth > 8 or g not in info:
        return False
    i, into = info[g]
    return i <= k and _in_group(into, target, k, info, depth + 1)


def visible_parts(parts, k, sub=False):
    """第 k 步图里能看到的零件; sub 默认用第 k 步所属的子组件。"""
    info = _attach_info()
    if sub is False:
        sub = model.STEPS[k - 1]["sub"]
    return [p for p in parts if p.step <= k and _in_group(model.STEPS[p.step - 1]["sub"], sub, k, info)]


def ldr_for_step(parts, k):
    """三段 LDraw: STEP1 不参与取景的旧零件, STEP2 参与取景的旧零件, STEP3 本步零件。"""
    s = model.STEPS[k - 1]
    vis = visible_parts(parts, k)
    # 本步新出现的: 本步的零件, 以及本步刚装进来的子组件 (底座除外, 它太大, 高亮反而看不清)
    before = set(map(id, visible_parts(parts, k - 1, s["sub"]))) if k > 1 else set()
    new = [p for p in vis if p.step == k or (id(p) not in before and model.STEPS[p.step - 1]["sub"] != "底座")]
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
    write(os.path.join(OUT, "model.mpd"), pack_mpd(parts, len(steps)))
    with open(os.path.join(HERE, "viewer.js"), encoding="utf-8") as f:
        write(os.path.join(OUT, "viewer.js"), f.read())
    # three.js 0.170.0 (MIT) 从渲染用的 node_modules 复制到说明书目录, 页面本地加载
    three = os.path.join(HERE, "..", "render", "node_modules", "three")
    for src, dst in THREE_FILES:
        os.makedirs(os.path.dirname(os.path.join(OUT, "three", dst)), exist_ok=True)
        shutil.copyfile(os.path.join(three, src), os.path.join(OUT, "three", dst))
    write_html(parts, step_new, keys, list(subs))


# ---- 可旋转的 3D 模型: 把整机和用到的全部零件、基元打包成一个 MPD 文件 ---------------------------------------

def pack_mpd(parts, n_steps):
    """网页里的 3D 视图用: 主模型按说明书的步骤分段 (每步后面一个 0 STEP, 空步骤也保留, 这样 buildingStep 和步骤号对齐),
    后面用 0 FILE 附上所有被引用的零件和基元, 开头附上颜色定义, 网页不需要再访问零件库。"""
    colors = [ln for ln in ldraw.fetch_rel("colors/ldcfgalt.ldr").decode("utf-8", "replace").splitlines()
              if ln.startswith("0 !COLOUR")]
    main_lines = ["0 FILE quadcuber_v3.ldr", "0 quadcuber 四臂整机 v3", "0 Name: quadcuber_v3.ldr"] + colors
    for k in range(1, n_steps + 1):
        main_lines += [p.ldraw() for p in parts if p.step == k]
        main_lines.append("0 STEP")
    files, order, todo = {}, [], sorted({p.name.lower() for p in parts})
    while todo:
        name = todo.pop()
        if name in files:
            continue
        text = ldraw.get(name)
        files[name] = text
        order.append(name)
        for ln in text.splitlines():
            f = ln.split()
            if len(f) >= 15 and f[0] == "1":
                sub = " ".join(f[14:]).replace("\\", "/").lower()
                if sub not in files:
                    todo.append(sub)
    out = main_lines
    for name in order:
        # LDrawLoader 把 s/ 开头的引用改成 parts/s/, 48/ 开头的改成 p/48/ 再查缓存, 打包的文件名要跟着改
        key = "parts/" + name if name.startswith("s/") else "p/" + name if name.startswith("48/") else name
        out.append(f"0 FILE {key}")
        out += [ln for ln in files[name].splitlines() if not ln.startswith("0 FILE")]
    return "\n".join(out) + "\n"


# ---- HTML ----------------------------------------------------------------------

# 3D 模型用到的 three.js 文件 (node_modules 里的路径, 说明书目录 three/ 下的路径)
THREE_FILES = [("build/three.module.min.js", "three.module.min.js"), ("LICENSE", "LICENSE"),
               ("examples/jsm/controls/OrbitControls.js", "addons/controls/OrbitControls.js"),
               ("examples/jsm/loaders/LDrawLoader.js", "addons/loaders/LDrawLoader.js"),
               ("examples/jsm/materials/LDrawConditionalLineMaterial.js", "addons/materials/LDrawConditionalLineMaterial.js")]

# SPIKE Prime 扩展套装 45680 的零件数 (Brickset 清单, 2026-09-29 查; 同一型号不同颜色合并)。
# 15x11 大框 Brickset 写 2 块, 用户实际有 4 块, 按用户的算
SET_45680 = {"18938.dat": 2, "18939.dat": 2, "32498.dat": 2, "39790.dat": 4, "64179.dat": 8, "32526.dat": 10,
             "32278.dat": 6, "32525.dat": 6, "40490.dat": 8, "32524.dat": 6, "32316.dat": 8, "32523.dat": 10,
             "2780.dat": 80, "6558.dat": 36, "32054.dat": 12}

CSS = _v1.CSS + """
#v3d{--v3d-bg:#ffffff;position:relative;height:min(70vh,560px);touch-action:none}
#v3d canvas{display:block;width:100%;height:100%}
#v3d-status[hidden]{display:none}
#v3d-status{position:absolute;inset:0;display:grid;place-items:center;color:#5a6778;font-size:14px;padding:16px;text-align:center}
kbd{font:12px "JetBrains Mono",ui-monospace,monospace;padding:1px 5px;border:1px solid var(--line);border-bottom-width:2px;border-radius:4px;background:var(--sheet);color:var(--ink)}
.v3d-bar{display:flex;flex-wrap:wrap;align-items:center;gap:10px 14px}
.v3d-bar input{flex:1 1 220px;min-width:0}
.v3d-bar span{flex:1 1 160px;min-width:0;font-weight:700}
.v3d-bar button{font:inherit;padding:6px 14px;border:1px solid var(--line);border-radius:6px;background:var(--sheet);color:var(--ink);cursor:pointer}
.cmp td:first-child{white-space:nowrap;font-weight:600}
.cmp td{min-width:9em}
.lead{font-size:16px}
ul.plain{margin:0;padding-left:1.2em;display:grid;gap:6px;max-width:70ch}
"""

EVAL_ROWS = [
    ("整机形态", "只有单臂; 四臂怎么排、底座怎么连都没有设计, 也没有四臂之间的干涉检查",
     "四个一样的模块两两垂直, 固定在一个整体底座上", "四个相同模块 + 横梁两层交叉搭成的网格底座, 孔位保证四根轴线过魔方中心、两两垂直; 四臂干涉按全部状态组合扫描过"),
    ("转动部分", "转盘上装着舵机、叉子盒、两根 16 号导轨, 从转盘端面到魔方约 144mm, 转动惯量大",
     "夹爪短而轻, 马达和舵机都不跟着转", "转动的只有转盘上半、两块侧板、夹指、连杆和推杆, 约 52mm 长, 没有舵机和马达"),
    ("夹紧", "U 形叉沿轴向插入, 水平时没有压紧力, 曲柄停在死点不等于锁紧 (外部评审 ① ②)",
     "两片夹指从两侧合拢夹住魔方", "两片会转的夹指 + 肘节连杆: 连杆推到死点时魔方的反推力沿连杆方向互相抵消, 理想对称时推杆轴向载荷降低; 实物夹紧仍需预压和刚度"),
    ("旋转范围", "舵机随机械手转动, 线缆会缠, 规划器必须限角度 (±270° 时规划慢 20 多倍)",
     "机械手可以连续旋转", "舵机固定在后面的平台上, 经穿过转盘中孔的推杆开合夹爪; 机械手可以无限旋转, 规划器不需要角度限制"),
    ("驱动", "马达输出轴直接带机械手", "—",
     "马达偏到侧面, 24 齿直齿轮带 60 齿转盘外圈 (中心距 5 个孔, 用户实测咬合最好), 扭矩放大 2.5 倍, 马达的回差和编码器误差在机械手上缩小 2.5 倍; 输出轴不承受弯矩"),
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
    # 可旋转的 3D 模型 (viewer.js + model.mpd + 本地的 three.js, 不需要联网拉脚本)
    out.append('<script type="importmap">{"imports":{"three":"./three/three.module.min.js","three/addons/":"./three/addons/"}}</script>')
    out.append('<section id="v3d-sec" class="cover"><h2>3D 模型 (可旋转)</h2>'
               '<p class="cap">拖动旋转, 滚轮或双指缩放, 右键或双指拖动平移。滑块选到第几步, 就显示到那一步为止的零件, 这一步新加的零件会提亮。键盘: <kbd>←</kbd> <kbd>→</kbd> 上一步/下一步, <kbd>Home</kbd> <kbd>End</kbd> 第一步/全部, <kbd>A</kbd> <kbd>D</kbd> 左右转, <kbd>W</kbd> <kbd>S</kbd> 上下转, <kbd>+</kbd> <kbd>-</kbd> 缩放, <kbd>R</kbd> 复位 (3D 区域在屏幕上时有效)。</p>'
               '<div id="v3d" class="plate"><div id="v3d-status">正在加载 3D 模型 (约 0.6 MB)…</div></div>'
               '<div class="v3d-bar"><input id="v3d-step" type="range" min="1" max="1" value="1" disabled aria-label="步骤">'
               '<span id="v3d-label"></span><button id="v3d-fit" type="button">复位</button></div>'
               f'<script>window.V3D_STEPS = {json.dumps([st["title"] for st in steps], ensure_ascii=False)};'
               f'window.V3D_STEPMAP = {json.dumps(sorted({p.step for p in parts}))};</script>'
               '<script type="module" src="viewer.js"></script></section>')
    out.append('<nav class="toc"><a href="#v3d-sec">3D 模型</a><a href="#eval">v2 评估</a><a href="#idea">设计思路</a><a href="#four">四臂检查</a>'
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
               "<li><b>肘节锁紧的夹指。</b>每只机械手两片 7 孔粗梁当夹指, 绕根部的 6 号轴转动。十字接头往前推, 两根连杆把夹指根部往外撑, 前端合拢。"
               "推到连杆和推杆垂直 (死点) 时, 魔方把夹指往外推的力沿连杆传到十字接头, 理想对称时上下两根互相抵消, 推杆轴向载荷减小。"
               "闭合夹口仍为 56.8mm, 改成两孔力臂不会自动产生预压; 实际夹紧需检查魔方尺寸、接触垫和销孔间隙。</li>"
               "<li><b>舵机不跟着转。</b>舵机固定在机械手后面的平台上, 曲柄和连杆同样拉到死点, 通过十字块推拉由 3 号轴、光面连接器和 12 号轴组成的推杆。"
               "推杆穿过转盘中孔和导向框架两条边上的圆孔, 机械手转动时推杆跟着转, 十字块在推杆上一起转 (两侧半轴套锁住轴向位置)。"
               "转动部分没有任何线缆。</li>"
               "<li><b>齿轮带转盘外圈。</b>60 齿转盘仍然是主轴承 (v2 的结论保留), 但不再用马达输出轴直接带, 而是马达偏到侧面, "
               "24 齿直齿轮和转盘外圈啮合 (中心距 5 个孔, 用户实测)。这样转盘中孔留给推杆, 马达只传扭矩, 2.5 倍减速同时缩小马达回差。</li>"
               "<li><b>模块化。</b>一个模块 = 竖墙 + 转盘 + 马达 + 舵机平台 + 机械头, 四个完全一样。底座的孔位让四根轴线严格过魔方中心、两两垂直, "
               "不用调。模块整体往魔方方向挪了半个孔距, 这是让相邻模块的孔位对得上的关键 (否则会差半个孔)。</li>"
               "</ul>")
    out.append('<div class="two">'
               '<figure style="margin:0" class="cover"><div class="plate">' + img("ref42082.png", "官方 42082", w=1000, h=700)
               + '</div><figcaption class="cap">官方 42082 (利勃海尔 R 9800) 原件, 从背面看: 转盘下半的凸台卡在 7x5 框架开口里, '
               '两根 5 孔粗梁压住背面 (LDraw 官方模型库)。这种做法也可以用</figcaption></figure>'
               '<figure style="margin:0" class="cover"><div class="plate">' + img("step03.png", "v3 转盘下半", w=1200, h=860)
               + '</div><figcaption class="cap">v3 第 3 步: 同样卡在框架开口里, 2 根红色带挡套长销 32054 从转盘中孔里面往外插, 穿过凸台端壁进框架, 一上一下错开, 挡套藏在里面</figcaption></figure>'
               "</div>")
    out.append('<div class="two">'
               '<figure style="margin:0" class="cover"><div class="plate">' + img("servo_closed.png", "舵机夹紧", w=1000, h=620)
               + '</div><figcaption class="cap">舵机侧, 夹紧: 曲柄和连杆拉成一条直线</figcaption></figure>'
               '<figure style="margin:0" class="cover"><div class="plate">' + img("servo_open.png", "舵机松开", w=1000, h=620)
               + '</div><figcaption class="cap">舵机侧, 松开: 曲柄转过约 172°, 十字块带推杆后退</figcaption></figure>'
               "</div>")
    out.append("</section>")

    out.append('<section id="four" class="cover"><h2>四臂检查 (tools/lego/v3/four_arm.py)</h2>')
    out.append('<div class="plate">' + img("flip.png", "整体翻转", w=1400, h=900) + "</div>")
    out.append('<p class="cap">整体翻转到一半: L、R 夹着魔方转, F、B 松开保持竖直。</p>')
    out.append('<div class="tbl"><table><tr><th>检查</th><th>结果</th></tr>'
               "<tr><td>一只机械手夹紧或松开, 从竖直转到水平 (每 5° 一格), 两侧邻居在 夹紧/松开 × 竖直/水平 的 16 种组合下</td>"
               "<td>邻居竖直时全部不碰; 邻居水平时, 转到 80° 左右会和邻居的夹指相撞</td></tr>"
               "<tr><td>拧一层时, 邻居 (夹紧、竖直) 的零件离转轴的最近距离</td><td class=\"ok\">111 LDU, 比魔方层的扫掠半径大 4.8mm</td></tr>"
               "<tr><td>整体翻转时, 邻居 (松开、竖直) 的零件离转轴的最近距离</td><td class=\"ok\">103.4 LDU, 比魔方的扫掠半径大 1.7mm (按尖角算)</td></tr>"
               "</table></div>")
    out.append('<div class="note"><b>相邻两只机械手不能同时水平。</b>这是任何从外侧夹住魔方的夹爪都有的几何限制: 两只相邻机械手都转到水平时, '
               "两副夹指会在魔方棱边外面的同一个位置相遇。v3 把它写进了规划器的可选约束 "
               "(<code>python -m quadcuber plan ... --no-adjacent-horizontal</code>): 转动中的机械手, 两侧邻居必须竖直且不同时转动。"
               "按现在的估算耗时, 20 步随机序列平均从 7.95 秒变成 9.69 秒 (约 +22%)。</div>")
    out.append("</section>")

    out.append('<section id="buy" class="cover"><h2>要买的零件</h2>')
    # (名称, 编号, 零件文件 (数量从模型里数) 或固定数量, 说明)
    buy = [("60 齿转盘 上半 + 下半 (套)", "18938 + 18939", "18938.dat", "每只机械手 1 套"),
           ("24 齿直齿轮", "3648", "3648b.dat", "和转盘外圈啮合"),
           ("15x11 大框", "39790", "39790.dat", "底座, 每个模块 1 块"),
           ("7x5 框架", "64179", "64179.dat", "每个模块 5 块 (竖墙 3、推杆导向 1、平台前半 1)"),
           ("3x5 L 形粗梁", "32526", "32526.dat", "机械头侧板每侧 2 根, 底座每个角 1 根"),
           ("15 孔粗梁", "32278", "32278.dat", "平台下 2 根, 底座每个角 2 根"),
           ("11 孔粗梁", "32525", "32525.dat", "马达前端"),
           ("9 孔粗梁", "40490", "40490.dat", "马达前端、机械头、平台后端竖梁"),
           ("7 孔粗梁", "32524", "32524.dat", "夹指、马达尾脚"),
           ("5 孔粗梁", "32316", "32316.dat", "连杆、平台后横梁"),
           ("3 孔粗梁", "32523", "32523.dat", "马达颈部"),
           ("90° 弯角销连接器 3x3 (带 4 个销)", "55615", "55615.dat", "平台后端支撑, 每个模块 3 个"),
           ("摩擦销", "2780", "2780.dat", "多买一些备用"),
           ("蓝色长摩擦销", "6558", "6558.dat", ""),
           ("带挡套长销", "32054", "32054.dat", "转盘下半和马达耳朵"),
           ("无摩擦销 / 无摩擦长销", "3673 / 32556a", None, "夹爪的活动关节: 8 / 4"),
           ("3 号 / 6 号 / 7 号 / 12 号轴", "4519 / 3706 / 44294 / 3708", None, "12 / 8 / 4 / 4; 45680 里有 3 号轴 14 根"),
           ("轴连接器 (光面)", "59443", "59443.dat", "推杆接长, 4"),
           ("轴套 / 半轴套", "3713 / 32123", None, "20 / 52"),
           ("角度连接器 1 号 (一头十字孔一头圆孔) / 十字块 1x2 / 2 孔细梁", "32013 / 6536 / 41677", None, "各 4"),
           ("EV3 大马达 / Geekservo 灰色", "—", None, "4 / 4; 现在只有 2 个大马达, 还缺 2 个")]
    rows = []
    for name, num, f, note in buy:
        need = byname[f] if f else None
        have = SET_45680.get(f, 0) if f else None
        if f is None:
            cells = ["—", "—", "—"]
        else:
            cells = [str(need), str(have) if have else "—", str(max(need - have, 0)) if need > have else "不用买"]
        rows.append(f"<tr><td>{esc(name)}</td><td>{num}</td>" + "".join(f"<td>{c}</td>" for c in cells)
                    + f"<td>{esc(note)}</td></tr>")
    out.append('<div class="tbl"><table><tr><th>零件</th><th>编号</th><th>整机</th><th>45680 里有</th><th>还要买</th><th>说明</th></tr>'
               + "".join(rows) + "</table></div>")
    out.append('<p class="cap">"45680 里有" 按 Brickset 的 45680 (SPIKE Prime 扩展套装) 零件清单, 不分颜色; '
               "最后几行 45680 里没有或数量对不上型号的, 按 \"说明\" 里的数量买。你手上其他零件没算进去。</p>")
    out.append('<p class="cap">可以先只搭一个模块 (底座只要它那一块大框) 做单臂实测, 验证夹持和转速后再买齐四套。</p>')
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

    out.append('<p class="cap">舵机首次装配与定位请按 <a href="../../single_arm.md#servo-calibration">单臂测试第3步</a>执行。</p>')
    out.append('<section id="checks" class="cover"><h2>检查与待验证</h2>')
    out.append('<div class="tbl"><table><tr><th>程序检查</th><th>结果</th></tr>'
               '<tr><td>单模块夹紧、松开, 以及夹指行程中间 7 个位置: 零件互相穿模</td><td class="ok">无</td></tr>'
               '<tr><td>整机: 每个销、轴都插在孔里且至少连接两个零件; 长销挡肩位置</td><td class="ok">通过</td></tr>'
               '<tr><td>按搭建顺序模拟插销: 带挡环的销两侧零件能沿销轴压上去 (不会出现 "两头都要插、只能插进一半")</td>'
               '<td class="ok">通过</td></tr>'
               '<tr><td>四臂转动干涉 (上一节)</td><td class="ok">只有 "相邻两只同时水平", 已写进规划器约束</td></tr>'
               "</table></div>")
    out.append('<div class="tbl"><table><tr><th>待实物验证 (模型保证不了)</th><th>怎么看</th></tr>'
               "<tr><td>夹指预紧</td><td>闭合夹口为 56.8mm, 需实测魔方尺寸。若用可压缩垫片补足间隙, 厚度须让闭合时有少量预压, "
               "并重新检查翻转间隙。夹紧后用手试外张夹指, 检查连杆销、转轴及支架的游隙</td></tr>"
               "<tr><td>舵机死点标定</td><td>首次定位必须脱开连杆；空载 servo 1500 后断电，在机构行程中间连接，再以 10～20µs 小步标定。没有实物限位时不尝试越过死点</td></tr>"
               "<tr><td>转盘下半卡在框架开口里</td><td>按零件尺寸凸台正好是 5x3 孔大小; 如果实物偏松, 在凸台和框架之间垫一层胶带, 或在凸台两头的孔里各插一根 2 号轴 (没有挡环, 可以从框架外面推进去) 加固</td></tr>"
               "<tr><td>马达前板的销孔</td><td>模型假设马达靠近输出盘的侧面两个孔可以插摩擦销; 如果不是通孔或深度不够, 改用 TRACK3R 的耳朵固定加一根竖梁</td></tr>"
               "<tr><td>齿轮啮合和回差</td><td>24 齿和 60 齿转盘外圈中心距 5 个孔 (用户实测咬合最好); 手转机械手应顺滑, 马达锁住时晃动机械手看回差</td></tr>"
               "<tr><td>舵机平台刚度</td><td>平台前端接竖墙、后端经 55615 和竖梁接底座；断电轻推舵机本体，分别检查安装耳、7 孔垫梁和平台支撑是否松动</td></tr>"
               "<tr><td>推杆在转动时的摩擦</td><td>推杆随机械手一起转, 十字块在导向框架里跟着转; 手转机械手时应不卡, 半轴套别压太紧</td></tr>"
               "<tr><td>整体翻转的间隙</td><td>未贴垫片时按尖角算约 1.7mm; 实际魔方有圆角, 余量更大, 但要用自己的魔方实测</td></tr>"
               "<tr><td>魔方尺寸</td><td>按 56mm 魔方设计; 57mm 魔方放不进</td></tr>"
               "</table></div>")
    out.append('<p class="cap">模型文件 model.ldr 可以用 Stud.io、LeoCAD 或 LDView 打开 (需要把 tools/lego/parts/ 里的 '
               'geekservo.dat、cube56.dat 放进它们的零件目录)。设计推导见仓库 docs/lego/v3/README.md。</p>')
    out.append("</section>")

    out.append('<section id="safety" class="cover"><h2>上电前</h2><ul class="plain">'
               "<li>4 个舵机用单独的 5V 降压电源 (DSN5000 先调到 5.0V 再接), 不要从 Pico 取电; 四个同时动作的峰值电流按 3A 以上准备。</li>"
               "<li>4 个大马达由 2 块 DRV8833 驱动, 马达电压不超过 10.8V (用 9V)。</li>"
               "<li>编码器信号照旧经 10k/20k 分压后再接 Pico, 四臂一共 8 路。</li>"
               "<li>首次舵机定位不放魔方，曲柄与连杆必须脱开；定位后断电连接，再小步标定。底座抬起、销退出或机构顶住时立即关闭9V。完整步骤见 docs/single_arm.md 第3步。</li>"
               "</ul></section></div>")
    write(os.path.join(OUT, "index.html"), "\n".join(out) + "\n")


if __name__ == "__main__":
    main(render="--no-render" not in sys.argv)
