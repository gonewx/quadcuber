"""生成 v4 (四臂整机, 反向连杆＋推杆导向) 搭建说明书: docs/lego/v5/index.html、步骤图、零件缩略图和 model.ldr。

用法 (先在另一个终端启动 ../render/server.py):
    cd tools/lego/v5 && python booklet.py [--no-render]

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

OUT = os.path.join(HERE, "..", "..", "..", "docs", "lego", "v5")
IMG = os.path.join(OUT, "img")
WORK = os.path.join(HERE, "..", ".cache", "work", "v5")
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
        module_parts = model.build({"L": (s, 0.0)}, with_cube=False)
        linkage_step = next(k for k, st in enumerate(model.STEPS, 1) if st["title"] == "十字块和舵机连杆")
        ps = [p for p in module_parts if p.arm == "L" and (p.step == linkage_step or p.name in ("geekservo.dat", "3708.dat", "50451.dat"))]
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
        if os.environ.get("LDRAW_SOFTWARE_RENDER"):
            subprocess.run([sys.executable, os.path.join(HERE, "..", "render", "software.py"), jobs_path], check=True)
        else:
            subprocess.run(["node", "render.js", jobs_path, os.environ.get("LDRAW_RENDER_PORT", "8765")], cwd=os.path.join(HERE, "..", "render"), check=True, env=env)

    write(os.path.join(OUT, "model.ldr"), model.to_ldr(parts, "quadcuber 四臂整机 v5"))
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
    main_lines = ["0 FILE quadcuber_v5.ldr", "0 quadcuber 四臂整机 v5", "0 Name: quadcuber_v5.ldr"] + colors
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
    import csv
    steps = model.STEPS
    esc = html.escape
    byname = Counter(p.name for p in parts if p.name != "cube56.dat")
    one = Counter(p.name for p in model.module(steps=False))
    radius = model.TYRE_RADIUS
    gap = 2 * (model.CUBE_HALF - model.TYRE_PRELOAD) * .4
    stroke = model.OPEN_S * .4

    def img(src, alt, w=1200, h=860):
        return f'<img src="img/{src}" alt="{esc(alt)}" width="{w}" height="{h}" loading="lazy">'

    def figure(src, caption, w=1200, h=860):
        return '<figure class="cover"><div class="plate">' + img(src, caption, w, h) + f'</div><figcaption class="cap">{caption}</figcaption></figure>'

    out = ['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
           '<title>quadcuber v4 · 反向连杆</title>', f'<style>{CSS}</style><div class="wrap">',
           '<header class="cover"><div class="eyebrow">quadcuber · v4</div>',
           '<h1>v4：反向连杆与推杆导向</h1>',
           '<p class="lead">在“双侧轮胎压头＋防翻折限位”版本上改动：十字接头移到连杆前方，往后拉夹紧、往前推张开，全程不进转盘凸台；转盘正前方加一个 32184 十字块作推杆导向，推杆伸出导向 26~36mm。机械头长度、底座、竖墙、马达都不变；导向框和舵机回到最初位置（比基准版前移两孔），推杆改为一根 16 号轴，不用连接器。夹指连杆接主臂第 1 孔、长 100（7 孔粗梁），夹紧时十字接头离推杆导向约 10mm。侧板内侧梁中段让给连杆。</p>',
           '<p><b>名义 CAD 检查通过</b>（连接与装配顺序、81 个开度网格间隙、整圈回转对邻臂、四臂 576 状态、连续回转包络）。实物承重、推杆导向摩擦、侧板刚度和夹紧预压仍待实测。<a href="README.md">改装说明、计算与风险</a></p>',
           '<p><b>舵机方向反了：</b>v4 往后拉是夹紧，名义夹紧点在曲柄折叠死点前约 25°，余下的角度用来微调预压。舵机必须按新方向重新标定，不能沿用旧脉宽。</p>',
           '<div class="plate">' + img('cover.png', '整机装配总览', 1400, 900) + '</div>',
           '<div class="facts">'
           f'<div class="fact"><b>{len(steps)} 步</b><span>完整装配</span></div>'
           f'<div class="fact"><b>{gap:.2f} mm</b><span>估算自由夹口 · 魔方 56 mm</span></div>'
           f'<div class="fact"><b>{stroke:.2f} mm</b><span>推杆开合行程</span></div>'
           '<div class="fact"><b>25°</b><span>主臂松开角</span></div></div>',
           '<nav class="toc"><a href="#jaw">压头详图</a><a href="#v3d-sec">可旋转模型</a><a href="#bom">零件清单</a>'
           + ''.join(f'<a href="#s{k}">{k}. {esc(st["title"])}</a>' for k, st in enumerate(steps, 1))
           + '<a href="#checks">验证与标定</a></nav></header>',
           '<section id="jaw" class="cover"><h2>压头与传力</h2>',
           figure('jaw_detail.png', '上下均为 42610＋50945 轮胎；每只轮毂两侧各有一根 32449 薄梁。', 1400, 1000),
           '<div class="two">' + figure('mech_closed.png', f'夹紧参考：主臂外张 3.84°，每侧名义压缩约 {(56-gap)/2:.2f}mm。', 1000, 620)
           + figure('mech_open.png', f'松开参考：主臂外张 25°，推杆前推 {stroke:.2f}mm。', 1000, 620) + '</div>',
           figure('jaw_layers.svg', '孔位与轴向叠放：4mm 薄梁＋8mm 轮毂＋4mm 薄梁；二号轴两端齐平。', 1500, 1000),
           '<ul class="plain"><li>每臂前端：42610 ×2、50945 ×2、32449 ×4、32062 ×2、4519 ×2、32123a ×4、32054 ×2。</li>'
           '<li>上下均为 7 孔主臂：第 2 孔接连杆，第 4 孔作支点，第 6、7 孔接薄梁。连杆另一端接十字接头的米色长销，十字接头在连杆前方。</li>'
           '<li>32449 第 1 十字孔用三号轴贯穿主臂，两端半轴套固定；第 2 圆孔用 32054 挡套长销贯穿。第 3 孔空，第 4 十字孔用二号轴连接轮毂。</li>'
           '<li>50945 按 14×6mm 外包络；42610 标称 11×8mm，CAD 网格外缘约 11.2mm。轮胎安装内槽保留原网格。</li>'
           '<li>轮毂可以滚动；旋转魔方时需要轮胎沿轮轴方向的摩擦力。需要实测轴向滑移、拧层阻力和轮胎保持。</li></ul></section>',
           '<section class="cover"><h2>防翻折开限位</h2>' + figure('open_stop_layout.svg', '下夹指侧视与限位装配；上夹指镜像安装（沿用旧版图）。', 1500, 950) + '<p>正常开合留隙，只有异常继续张开才接触挡轴。v4 反向连杆在整个行程内离两组解的汇合位置很远，不会翻折；挡轴保留作异常保护。</p></section>',
           '<section class="cover"><h2>舵机粗连杆</h2>',
           '<div class="two">' + figure('servo_closed.png', '夹紧（往后拉）：7 孔粗连杆第 1 孔接十字块，第 7 孔接曲柄；曲柄朝后，离与连杆折叠成一线还差约 25°。', 1000, 620)
           + figure('servo_open.png', '松开（往前推）：曲柄经远离推杆的一侧向前转开约 85°，二号轴内端加半轴套。', 1000, 620) + '</div>',
           f'<p>十字块端用三号轴和两只半轴套，粗连杆直接贴十字块；曲柄端二号轴内侧加半轴套，外端齐平。v4 连杆改用 7 孔粗梁第 1、7 孔（旧版第 2、7 孔）。名义夹紧时曲柄朝后、离折叠成一线还差约 25°，这段用来微调预压，不要越过折叠死点；张开时经远离推杆的一侧向前转约 85°。推杆行程 {stroke:.2f}mm，脉宽必须重新标定。</p></section>',
           '<script type="importmap">{"imports":{"three":"./three/three.module.min.js","three/addons/":"./three/addons/"}}</script>',
           '<section id="v3d-sec" class="cover"><h2>可旋转模型</h2><p>拖动旋转、滚轮缩放、右键平移；滑块按步骤查看。</p>'
           '<div id="v3d" class="plate"><div id="v3d-status">正在加载模型…</div></div>'
           '<div class="v3d-bar"><input id="v3d-step" type="range" min="1" max="1" value="1" disabled aria-label="步骤">'
           '<span id="v3d-label"></span><button id="v3d-fit" type="button">复位</button></div>'
           f'<script>window.V3D_STEPS = {json.dumps([st["title"] for st in steps], ensure_ascii=False)};'
           f'window.V3D_STEPMAP = {json.dumps(sorted({p.step for p in parts}))};</script>'
           '<script type="module" src="viewer.js"></script>'
           '<p><a href="model.mpd" download>下载含零件库的 MPD</a> · <a href="model.ldr" download>LDraw 模型</a> · <a href="bom.csv" download>零件清单 CSV</a> · <a href="README.md">设计与验证记录</a></p></section>',
           '<section id="bom" class="cover"><h2>零件清单</h2><p>单模块不含公共底座；整机包含四个马达和四个舵机。轮胎按真实乐高编号列出，模型中使用用户给定尺寸的名义外包络。</p>',
           '<div class="tbl"><table><tr><th>零件</th><th>编号</th><th>单模块</th><th>整机</th><th>已计库存</th><th>扣除后补充</th></tr>']
    with open(os.path.join(OUT, 'bom.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(['零件', '编号', '单模块不含底座', '整机', '已计库存', '扣除后补充'])
        for name, count in sorted(byname.items()):
            available = 4 if name in {"42610.dat", "50945_nominal.dat"} else (2 if name == "95658.dat" else SET_45680.get(name, 0))
            number = '50945' if name == '50945_nominal.dat' else name[:-4]
            needed = max(0, count - available)
            row = [model.CATALOG[name][0], number, one[name], count, available, needed]
            writer.writerow(row)
            out.append('<tr>' + ''.join(f'<td>{esc(str(v))}</td>' for v in row) + '</tr>')
    out.append('</table></div><p class="cap">套装数量沿用仓库清单，大框按已有 4 块计。42610、50945 已有各 4 件，整机各需 8 件，按用户确认另补各 4 件。32449 整机需 16 根，未确认库存；原有 11478 五孔薄梁不能按同一孔位直接替换。其他未录入的零件按 0 计；补充数量需先扣除散件库存。马达已有 2 个，整机还需 2 个。</p></section>')
    for k, st in enumerate(steps, 1):
        out.append(f'<section class="cover" id="s{k}"><h2>{k:02d} · {esc(st["title"])}</h2>')
        chips = []
        for (name, color), count in Counter(part_key(p) for p in step_new[k-1]).items():
            number = '50945' if name == '50945_nominal.dat' else name[:-4]
            chips.append('<div class="chip">' + img(f'part_{name[:-4]}_{color}.png', model.CATALOG[name][0], TW, TH)
                         + f'<div class="x">{count}×</div><div class="n">{esc(model.CATALOG[name][0])} · {number}</div></div>')
        out.append('<div class="callout">' + ''.join(chips) + '</div><div class="plate">' + img(f'step{k:02d}.png', st['title']) + '</div>')
        out.append(f'<p>{esc(st["text"])}</p></section>')
    out += ['<section id="checks" class="cover"><h2>验证与单臂验收</h2><p>改装步骤、计算、检查结果与风险见 <a href="README.md">v4 说明</a>；夹紧测试见 <a href="../../clamp_test.md">clamp_test.md</a>。夹紧力、刚度、推杆导向摩擦和轮胎保持力均待实测。</p>',
            figure('flip.png', '整块翻转：L、R 夹持，F、B 松开并保持竖直。', 1400, 900),
            '<ol><li>先将 50945 套在 42610 上，用二号轴安装在两片 32449 之间；检查轮毂转动、轮轴保持及轮胎配合。</li>'
            '<li>确认薄梁第 1 十字孔装三号轴和两只半轴套、第 2 圆孔装挡套长销；轮毂装第 4 十字孔。舵机七孔粗连杆用第 1、7 孔，曲柄二号轴内侧装半轴套。</li>'
            '<li>断电手推推杆走完全行程：推杆导向处无卡点，连杆在侧梁空档里滑动、不碰侧梁；轻推确认上下挡轴有效，正常25°开度留有间隙，不能持续顶住挡轴。</li>'
            '<li>按 <a href="../../single_arm.md#servo-calibration">单臂标定步骤</a>先脱开曲柄、空载定位，再在行程中间断电连接。</li>'
            '<li>夹紧端（往后拉）：先断电把曲柄放在离折叠约 25° 处，滑动舵机侧十字块使轮胎刚好压住魔方并锁住两侧半轴套；再通电小步加脉宽到轮胎明显压缩，曲柄不要越过折叠死点。夹紧时十字接头离推杆导向约 10mm，不应再顶住。图示 3.84° 是参考值，旧版脉宽不能直接使用。检查舵机侧十字块两侧半轴套有没有沿推杆滑移。</li>'
            f'<li>开端参考推杆前推 {stroke:.2f}mm、主臂外张 25°。改变轮胎、轴长或开角后重新检查避让。</li>'
            '<li>单臂夹紧后检查横向滑动、轴向滑动和拧层阻力，再低速测试翻转。记录实测外径、脉宽、夹紧保持情况，之后再复制四臂。</li></ol>'
            '<p>相邻机械手保持竖直时才允许另一只转动；使用 <code>--no-adjacent-horizontal</code>。禁止把相邻机械手同时转到水平。</p></section></div></html>']
    write(os.path.join(OUT, 'index.html'), '\n'.join(out) + '\n')


if __name__ == "__main__":
    main("--no-render" not in sys.argv)
