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
    import jaw_diagram
    jaw_diagram.main()
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
        ps = [p for p in model.build({"L": (s, 0.0)}) if (p.arm == "L" and p.head and p.pos[0] > -235) or p.name == "cube56.dat"]
        path = write(os.path.join(WORK, f"mech_{tag}.ldr"), "0 mech\n" + "\n".join(p.ldraw() for p in ps) + "\n")
        jobs.append({"model": path, "out": os.path.join(IMG, f"mech_{tag}.png"),
                     "opts": {"w": 1000, "h": 620, "yaw": 0, "pitch": 0, "margin": 0.05}})
    ps = [p for p in model.build() if p.arm == "L" and p.head and p.pos[0] > -235]
    path = write(os.path.join(WORK, "jaw_detail.ldr"), "0 jaw detail\n" + "\n".join(p.ldraw() for p in ps) + "\n")
    jobs.append({"model": path, "out": os.path.join(IMG, "jaw_detail.png"),
                 "opts": {"w": 1400, "h": 1000, "yaw": 28, "pitch": 23, "margin": 0.07}})
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

def write_html(parts, step_new, keys, subs):
    steps = model.STEPS
    esc = html.escape
    byname = Counter(p.name for p in parts if p.name != "cube56.dat")
    one = Counter(p.name for p in model.module(steps=False))
    stroke = model.OPEN_S * 0.4
    servo_angle = math.degrees(model.servo_theta_for(0)[0] - model.servo_theta_for(model.OPEN_S)[0])

    def img(src, alt, w=1200, h=860):
        return f'<img src="img/{src}" alt="{esc(alt)}" width="{w}" height="{h}" loading="lazy">'

    def figure(src, caption, w=1200, h=860):
        return '<figure class="cover" style="margin:0"><div class="plate">' + img(src, caption, w, h) + f'</div><figcaption class="cap">{caption}</figcaption></figure>'

    out = ['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
           '<title>quadcuber · 平行夹块搭建图（7 孔粗梁版）</title>', f'<style>{CSS}</style>', '<div class="wrap">',
           '<header class="cover"><div class="eyebrow">quadcuber · research/self-aligning-jaws · 2026-09-30</div>',
           '<h1>四连杆平行夹块 · 7 孔粗梁版</h1>',
           '<p class="lead">红色主臂向内收紧，蓝色从动臂约束橙色夹块，使接触面在开合过程中保持平行。前端有独立活动关节，夹口可小于魔方边长；薄弹性垫提供接触预压。</p>',
           '<p>第 21 步改用 32526（3×5 L 形粗梁），使用长边末孔与短边中孔；横轴改为 4 号轴，主臂接点改为 3 号轴，轴套按新图重排。</p>',
           '<p>第 19 步已修正：夹块使用 32056 L 形薄梁，原 2905 三角梁后端会撞主根轴及轴套。每只机械手需要 4 片 32056。</p>',
           '<p>本图为研究分支的几何验证版。模型通过连接与离散运动检查；实际装入路径、夹紧力、摩擦和刚度需先搭单臂验证。</p>',
           '<div class="plate">' + img('cover.png', '四臂整机装配总览', 1400, 900) + '</div>',
           '<div class="facts">'
           f'<div class="fact"><b>{len(steps)} 步</b><span>完整装配</span></div>'
           '<div class="fact"><b>55.72 mm</b><span>含垫的自由夹口 · 魔方 56 mm</span></div>'
           f'<div class="fact"><b>{stroke:.2f} mm</b><span>推杆开合行程</span></div>'
           '<div class="fact"><b>16.5°</b><span>主臂张开角</span></div></div>',
           '<nav class="toc"><a href="#jaw">夹指详图</a><a href="#layers">轴与垫片</a><a href="#v3d-sec">可旋转模型</a><a href="#bom">零件清单</a>'
           + ''.join(f'<a href="#s{k}">{k}. {esc(st["title"])}</a>' for k, st in enumerate(steps, 1))
           + '<a href="#checks">验证与标定</a></nav></header>',
           '<section id="jaw" class="cover"><h2>夹指详图</h2>',
           figure('jaw_detail.png', '红：7 孔粗主摆臂 32524；蓝：从动臂 11478；橙：L 形夹块 32056；绿：含胶 0.4mm 接触垫。', 1400, 1000),
           '<div class="two">' + figure('mech_closed.png', '夹紧：主臂内收 0.25°，L 形夹块底边保持平行。', 1000, 620)
           + figure('mech_open.png', f'松开：主臂张开 16.5°，推杆后退 {stroke:.2f}mm。', 1000, 620) + '</div>',
           '<ul class="plain"><li>主、从动臂的有效孔距均为四孔（32mm）。从动固定轴相对主轴向后两孔、向外一孔；前端两个活动轴保持同样的位置差。</li>'
           '<li>主臂前端圆孔绕 2 号轴转动，2 号轴固定在L 梁底角的十字孔中。从动臂两端是十字孔，其前端 3 号轴在L 梁朝外一边的中间圆孔中转动。</li>'
           '<li>塑料底边自由间距约 56.52mm；上下各一对垫片在夹紧方向总共占 0.8mm，含垫间距约 55.72mm。夹住 56mm 魔方时，每侧名义压缩约 0.14mm。</li>'
           '<li>每片L 梁贴一条 12.8×3.2mm 垫片，含胶总厚度 0.4mm；每个夹块共两条，中间留出粗主臂位置。模型的压缩量不能直接换算成夹紧力。</li></ul></section>',
           '<section id="layers" class="cover"><h2>轴向分层 · 输入关节按上下镜像安装</h2>',
           figure('jaw_layers.svg', '沿轴看零件叠放顺序。数值为距夹指中面的位置，单位 mm。', 1500, 1524),
           '<p>主轴用 7 号轴，端头与外侧横梁齐平。横梁端部十字孔固定轴，粗主臂居中，两侧各用一个整轴套定位；不要再在主轴外端加轴套，否则会占用相邻机械手的转动空间。</p>'
           '<p>从动根轴用 10 号轴，两侧各有两个整轴套填满从动臂与后支架之间的空档。前端 2 号轴与L 形夹块外侧齐平，3 号轴与从动薄梁外侧齐平，由十字孔固定，不能任意加长。</p></section>',
           '<script type="importmap">{"imports":{"three":"./three/three.module.min.js","three/addons/":"./three/addons/"}}</script>',
           '<section id="v3d-sec" class="cover"><h2>可旋转模型</h2><p>拖动旋转、滚轮缩放、右键平移；拖动滑块按步骤查看。用本地 HTTP 服务打开此页面以加载模型。</p>'
           '<div id="v3d" class="plate"><div id="v3d-status">正在加载模型…</div></div>'
           '<div class="v3d-bar"><input id="v3d-step" type="range" min="1" max="1" value="1" disabled aria-label="步骤">'
           '<span id="v3d-label"></span><button id="v3d-fit" type="button">复位</button></div>'
           f'<script>window.V3D_STEPS = {json.dumps([st["title"] for st in steps], ensure_ascii=False)};'
           f'window.V3D_STEPMAP = {json.dumps(sorted({p.step for p in parts}))};</script>'
           '<script type="module" src="viewer.js"></script>'
           '<p><a href="model.mpd" download>下载含零件库的 MPD</a> · <a href="model.ldr" download>下载 LDraw 模型</a> · <a href="bom.csv" download>下载零件清单 CSV</a></p></section>',
           '<section id="bom" class="cover"><h2>零件清单</h2><p>按当前模型自动统计，不分颜色。单模块列不含整机公共底座；整机列包含底座、四个马达、四个舵机和八对非乐高接触垫（共 16 条）。</p>',
           '<div class="tbl"><table><tr><th>零件</th><th>编号</th><th>单模块</th><th>整机</th><th>45680 已计数量</th><th>扣除后补充</th></tr>']
    import csv
    with open(os.path.join(OUT, 'bom.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['零件', '编号', '单模块不含底座', '整机', '45680已计数量', '扣除后补充'])
        for name, count in sorted(byname.items()):
            available = 4 if name == "32056.dat" else SET_45680.get(name, 0)
            row = [model.CATALOG[name][0], name[:-4], one[name], count, available, max(0, count - available)]
            writer.writerow(row)
            out.append('<tr>' + ''.join(f'<td>{esc(str(v))}</td>' for v in row) + '</tr>')
    out.append('</table></div><p class="cap">套装数量沿用仓库已有清单（大框按用户已有 4 块，32056 按已确认至少 4 片计）；未录入的零件按 0 计，采购前先清点实物。EV3 马达已有 2 个，因此实际还需 2 个。</p></section>')
    for k, st in enumerate(steps, 1):
        out.append(f'<section class="cover" id="s{k}"><h2>{k:02d} · {esc(st["title"])}</h2>')
        chips = []
        for (name, color), count in Counter(part_key(p) for p in step_new[k - 1]).items():
            chips.append('<div class="chip">' + img(f'part_{name[:-4]}_{color}.png', model.CATALOG[name][0], TW, TH)
                         + f'<div class="x">{count}×</div><div class="n">{esc(model.CATALOG[name][0])} · {name[:-4]}</div></div>')
        out.append('<div class="callout">' + ''.join(chips) + '</div>')
        out.append('<div class="plate">' + img(f'step{k:02d}.png', st['title']) + '</div>')
        out.append(f'<p>{esc(st["text"])}</p></section>')
    out += ['<section id="checks" class="cover"><h2>检查结果与实物标定</h2>',
            '<div class="tbl"><table><tr><th>项目</th><th>范围 / 结果</th></tr>'
            '<tr><td>连接、销孔类型、插深和装配顺序</td><td>单模块与整机检查：0 个问题</td></tr>'
            '<tr><td>夹指中间行程</td><td>检查闭合、张开及中间位置，无报告干涉</td></tr>'
            '<tr><td>四臂转动</td><td>0°～355°，每 5° 扫描，覆盖夹紧/松开与相邻臂状态；邻臂竖直时无报告干涉</td></tr>'
            '<tr><td>拧层扫掠</td><td>按完整一层厚度 56/3mm，邻臂夹紧竖直：采样余量约 7.4mm</td></tr>'
            '<tr><td>整块翻转扫掠</td><td>邻臂松开竖直：采样余量约 1.4mm</td></tr>'
            '<tr><td>运动学与本臂转动回归</td><td>7 项测试通过，含实件孔位闭环、关节类型、预压、舵机行程、本臂齿轮轴和扫掠范围</td></tr></table></div>',
            '<p>检查按 LDraw 几何采样，包含本臂固定件与相邻臂，不模拟孔隙、受力变形、摩擦或连续碰撞。相邻机械手不能同时转到水平；转动时相邻机械手保持竖直且静止，规划时使用 <code>--no-adjacent-horizontal</code>。</p>',
            figure('flip.png', '整块翻转：L、R 夹持并同步转动；F、B 松开并保持竖直。', 1400, 900),
            '<h3>先搭一只机械手验证</h3><ol><li>断电并脱开舵机曲柄与连杆，手推检查全行程。夹块应保持平行，连接轴不窜动。</li>'
            '<li>按 <a href="../../single_arm.md#servo-calibration">单臂标定步骤</a>空载定位舵机，在行程中间断电连接，再以 10～20µs 小步标定。</li>'
            '<li>闭合端以夹块贴平、垫片轻微压缩为准，再断电调整推杆十字块位置，使后端舵机曲柄与连杆接近拉直。前端弯梁不与推杆垂直。</li>'
            f'<li>开端参考推杆 {stroke:.2f}mm、舵机曲柄约 {servo_angle:.1f}°。旧版脉宽不能直接沿用，不通过强推去追求理论角度。</li>'
            '<li>先测试手动拧其他层不打滑，再低速转到水平停留 10 秒。观察主轴、从动轴、L 形夹块与后架有无晃动。最后逐步测试连续翻转。</li></ol>'
            '<p>若需要更厚的垫片、更大张开角或更长轴，修改模型后重新检查四臂间隙。夹紧效果尚未经过这套新结构的实物测试。</p></section></div></html>']
    write(os.path.join(OUT, 'index.html'), '\n'.join(out) + '\n')


if __name__ == "__main__":
    main(render="--no-render" not in sys.argv)
