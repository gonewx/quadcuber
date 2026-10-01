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
        ps = [p for p in model.build({"L": (s, 0.0)}) if (p.arm == "L" and p.head and p.pos[0] > -370) or p.name == "cube56.dat"]
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
        ps = [p for p in module_parts if p.arm == "L" and (p.step == linkage_step or p.name in ("geekservo.dat", "3708.dat"))]
        path = write(os.path.join(WORK, f"servo_{tag}.ldr"), "0 servo\n" + "\n".join(p.ldraw() for p in ps) + "\n")
        jobs.append({"model": path, "out": os.path.join(IMG, f"servo_{tag}.png"),
                     "opts": {"w": 1000, "h": 620, "yaw": 20, "pitch": 30, "margin": 0.05}})
    # 承重导向特写：完整显示前后铰点、固定侧架和转盘安装耳。
    for tag, stroke in (("closed", 0.), ("open", model.OPEN_S)):
        ps = [p for p in model.build({"L": (stroke, 0.)}, with_cube=False)
              if p.arm == "L" and p.head and p.pos[0] > -370 and p.name != "3708.dat"]
        path = write(os.path.join(WORK, f"guide_{tag}.ldr"), "0 guide\n" + "\n".join(p.ldraw() for p in ps) + "\n")
        jobs.append({"model": path, "out": os.path.join(IMG, f"guide_{tag}.png"),
                     "opts": {"w": 1400, "h": 1000, "yaw": 28, "pitch": 25, "margin": .06}})
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
           '<title>quadcuber · Watt 承重导向与轮胎压头</title>', f'<style>{CSS}</style><div class="wrap">',
           '<header class="cover"><div class="eyebrow">quadcuber · research/self-aligning-jaws</div>',
           '<h1>Watt 承重导向与轮胎压头</h1>',
           '<p class="lead">公共接头两侧增加 Watt 承重导向，通过铰接薄梁连接直推杆；输入杆改用 32017 五孔薄梁。转盘及固定支座后移32mm，底座增加后端落地梁。每臂上下各一组 42610＋50945，四臂共需八组轮胎。</p>',
           '<p>每个轮毂由两根 32449 四孔薄梁夹持，用 32062 二号轴贯穿；轮毂圆孔可以绕轴转动。舵机后移 8mm，使用 32524 七孔粗连杆的第 1、6 孔。</p>',
           '<p><b>承重闭环与侧架连接已落实，名义 CAD 检查通过。</b>公共接头的上翘反力经 Watt 摆杆传到侧架。<a href="load_path.md">承重结构、静力与限制</a>。实物刚度、保持力和带载间隙仍待单臂验收。<a href="mechanical_audit.md">完整审查、刚度计算与测试指标</a> · <a href="load_test_template.csv">实测记录表</a></p>',
           '<p><b>当前图、模型与清单包含独立开限位。</b>邻臂单层连续回转间隙下界 1.333mm；后部旋转半轴套对连杆的下界约2.577mm（81个开度）；活动轴对驱动组件连续开合下界约2.0mm。导向内部另有约0.800～0.977mm运动间隙，仍需实测，不能据 CAD 通过认定带载合格。</p>',
           '<p><b>实物曾出现后拉翻折：</b>本版新增上下独立挡轴，正常开端上25°、下24.65°，名义约29.8°挡止。必须手动核对并重标舵机开端。<a href="open_stops.md">失效原因、改装清单与验收步骤</a> · <a href="open_stop_checks.json">限位检查数据</a></p>',
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
           + figure('mech_open.png', f'松开参考：上夹指25°、下夹指24.65°，推杆后退 {stroke:.2f}mm。', 1000, 620) + '</div>',
           figure('jaw_layers.svg', '孔位与轴向叠放：4mm 薄梁＋8mm 轮毂＋4mm 薄梁；二号轴两端齐平。', 1500, 1000),
           '<ul class="plain"><li>每臂前端：42610 ×2、50945 ×2、32449 ×4、32062 ×2、4519 ×2、32123a ×4、32054 ×2。</li>'
           '<li>上下均为 7 孔主臂：第 2 孔接连杆，第 4 孔作支点，第 6、7 孔接薄梁。</li>'
           '<li>32449 第 1 十字孔用三号轴贯穿主臂，两端半轴套固定；第 2 圆孔用 32054 挡套长销贯穿。第 3 孔空，第 4 十字孔用二号轴连接轮毂。</li>'
           '<li>50945 按 14×6mm 外包络；42610 标称 11×8mm，CAD 网格外缘约 11.2mm。轮胎安装内槽保留原网格。</li>'
           '<li>轮毂可以滚动；旋转魔方时需要轮胎沿轮轴方向的摩擦力。需要实测轴向滑移、拧层阻力和轮胎保持。</li></ul></section>',
           '<section class="cover"><h2>防翻折开限位</h2>' + figure('open_stop_layout.svg', '下夹指侧视与限位装配；上夹指镜像安装。', 1500, 950) + '<p><a href="open_stops.md">改装步骤与限位检查</a>。正常开合留隙，只有异常继续张开才接触挡轴。</p></section>',
           '<section class="cover"><h2>公共接头承重导向</h2>',
           figure('guide_closed.png', '夹紧：Watt 摆杆支承公共接头；32140 根支架用两点接入侧架。', 1400, 1000),
           figure('guide_open.png', '松开：公共接头横移约0.0284mm，铰接驱动保持真实杆长闭合。', 1400, 1000),
           '<p>侧架前角两点固定，后部6632与41677通过3749十字轴段锁定相对角度；87083止挡轴穿过间隔套和外侧梁。按步骤保留装轴方向和止挡位置。横梁使用11478，活动轴随端部十字孔转动，摆杆用全圆孔32017。活动轴只装外半轴套，两端各露约2mm；检查十字配合的保持力和轴向迁移。两侧装配完成后确认活动铰点自由转动。<a href="load_path.md">轴向叠层与承重说明</a></p></section>',
           '<section class="cover"><h2>舵机粗连杆</h2>',
           '<div class="two">' + figure('servo_closed.png', '夹紧：7 孔粗连杆第 1 孔接十字块，第 6 孔接曲柄。', 1000, 620)
           + figure('servo_open.png', '松开：曲柄沿远离推杆的一侧转开，二号轴内端加半轴套。', 1000, 620) + '</div>',
           '<p>舵机相对旧版后移一孔（8mm），垫梁的黑销孔位也已调整。十字块端用三号轴和两只半轴套；粗连杆直接贴十字块。曲柄端二号轴内侧加半轴套，外端齐平。连杆第 7 孔在曲柄一端留空，不能反装；曲柄总行程约 96.83°。</p></section>',
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
    out.append('</table></div><p class="cap">套装数量沿用仓库清单，大框按已有 4 块计。42610、50945 已有各 4 件，整机各需 8 件，按用户确认另补各 4 件。32449 整机需 24 根（轮端16根、驱动8根），未确认库存；11478五孔薄梁用于Watt横梁，整机需8根；不能替换轮端四孔32449或全圆孔32017。其他未录入的零件按 0 计；补充数量需先扣除散件库存。马达已有 2 个，整机还需 2 个。</p></section>')
    for k, st in enumerate(steps, 1):
        out.append(f'<section class="cover" id="s{k}"><h2>{k:02d} · {esc(st["title"])}</h2>')
        chips = []
        for (name, color), count in Counter(part_key(p) for p in step_new[k-1]).items():
            number = '50945' if name == '50945_nominal.dat' else name[:-4]
            chips.append('<div class="chip">' + img(f'part_{name[:-4]}_{color}.png', model.CATALOG[name][0], TW, TH)
                         + f'<div class="x">{count}×</div><div class="n">{esc(model.CATALOG[name][0])} · {number}</div></div>')
        out.append('<div class="callout">' + ''.join(chips) + '</div><div class="plate">' + img(f'step{k:02d}.png', st['title']) + '</div>')
        out.append(f'<p>{esc(st["text"])}</p></section>')
    out += ['<section id="checks" class="cover"><h2>验证与单臂验收</h2><p><a href="gravity_test.md">重力承重与下沉测试</a> · <a href="gravity_test.csv">承重记录表</a>：先测整头倾斜、上下轮端位移和魔方中心下沉，再进行交接与翻转。</p>',
            '<p>以下为承重导向版的实物试装与标定步骤。检查范围和结果见 <a href="mechanical_audit.md">完整机械审查</a>。夹紧力、刚度和轮胎保持力均待实测。</p>',
            figure('flip.png', '整块翻转：L、R 夹持，F、B 松开并保持竖直。', 1400, 900),
            '<ol><li>先将 50945 套在 42610 上，用二号轴安装在两片 32449 之间；检查轮毂转动、轮轴保持及轮胎配合。</li>'
            '<li>确认薄梁第 1 十字孔装三号轴和两只半轴套、第 2 圆孔装挡套长销；轮毂装第 4 十字孔。舵机七孔粗连杆用第 1、6 孔，曲柄二号轴内侧装半轴套。</li>'
            '<li>先按 <a href="open_stops.md">防翻折试装步骤</a>轻推确认上下挡轴有效，正常25°开度留有间隙，不能持续顶住挡轴。</li>'
            '<li>按 <a href="../../single_arm.md#servo-calibration">单臂标定步骤</a>先脱开曲柄、空载定位，再在行程中间断电连接。</li>'
            '<li>夹紧端以接触和轻微压缩为准，小步推进；图示 3.84° 是参考值，旧版脉宽不能直接使用。检查推杆十字块两侧半轴套有没有沿轴滑移。</li>'
            f'<li>开端参考推杆后退 {stroke:.2f}mm、主臂外张 25°。改变轮胎、轴长或开角后重新检查避让。</li>'
            '<li>单臂夹紧后检查横向滑动、轴向滑动和拧层阻力，再低速测试翻转。记录实测外径、脉宽、夹紧保持情况，之后再复制四臂。</li></ol>'
            '<p>相邻机械手保持竖直时才允许另一只转动；使用 <code>--no-adjacent-horizontal</code>。禁止把相邻机械手同时转到水平。</p></section></div></html>']
    write(os.path.join(OUT, 'index.html'), '\n'.join(out) + '\n')


if __name__ == "__main__":
    main("--no-render" not in sys.argv)
