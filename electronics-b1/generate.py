#!/usr/bin/env python3
"""从 circuit.py 生成 B1 的符号库、原理图、工程文件和未布线 PCB。用 KiCad 10 自带 Python 运行。

只写 electronics-b1/ 下的文件；不加载、不改动 A1（electronics/）。
"""
import json
import math
import sys
import uuid
from pathlib import Path

import pcbnew as p

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from circuit import C, BOARD, REF_MOVES, SILK  # noqa: E402
from silk import add_labels, move_refs  # noqa: E402

LIB = HERE / 'lib/B1.pretty'
NAME = 'quadcuber-b1'
OX, OY = 50.0, 50.0   # KiCad 页面内的板框原点


def uid(s):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://github.com/gonewx/quadcuber/b1/' + s))


def q(s):
    return json.dumps(str(s), ensure_ascii=False)


def mm(x, y):
    return p.VECTOR2I(p.FromMM(x), p.FromMM(y))


def effect(sz=1.27, extra=''):
    return f'(effects (font (size {sz} {sz})) {extra})'


(HERE / 'fp-lib-table').write_text(
    '(fp_lib_table\n  (version 7)\n  (lib (name "B1")(type "KiCad")(uri "${KIPRJMOD}/lib/B1.pretty")(options "")(descr "B1 自包含封装"))\n)\n')
(HERE / 'sym-lib-table').write_text(
    '(sym_lib_table\n  (version 7)\n  (lib (name "B1")(type "KiCad")(uri "${KIPRJMOD}/lib/B1.kicad_sym")(options "")(descr "B1 符号"))\n)\n')

# ---- 符号：每个元件一个符号，引脚全部 passive，网络由全局标签连接 --------------------------


def pindefs(comp):
    pins = list(comp['pins'])
    half = math.ceil(len(pins) / 2)
    out = []
    for i, num in enumerate(pins):
        side, j = (0, i) if i < half else (1, i - half)
        out.append((num, -10.16 if side == 0 else 10.16, round((half - 1) * 1.27 - j * 2.54, 3), 0 if side == 0 else 180))
    return out


syms = {}
for comp in C:
    if not comp['pins']:
        continue
    ref = comp['ref']
    hh = max(3.81, math.ceil(len(comp['pins']) / 2) * 1.27 + 1.27)
    s = (f'(symbol "{ref}" (pin_names (offset 0.508)) (exclude_from_sim no) (in_bom yes) (on_board yes)'
         f'(property "Reference" "{ref}" (at 0 {hh + 2.54} 0) {effect()})'
         f'(property "Value" {q(comp["value"])} (at 0 {-hh - 2.54} 0) {effect()})'
         f'(property "Footprint" {q("B1:" + comp["fp"])} (at 0 0 0) {effect(extra="(hide yes)")})'
         f'(symbol "{ref}_0_1" (rectangle (start -7.62 {hh}) (end 7.62 {-hh}) (stroke (width 0.254) (type default)) (fill (type background))))'
         f'(symbol "{ref}_1_1"')
    for num, x, y, a in pindefs(comp):
        s += f'(pin passive line (at {x} {y} {a}) (length 2.54) (name {q(num)} {effect(0.8)}) (number {q(num)} {effect(0.8)}))'
    syms[ref] = s + '))'
(HERE / 'lib/B1.kicad_sym').write_text(
    '(kicad_symbol_lib (version 20241209) (generator "quadcuber_b1")' + ''.join(syms.values()) + ')')

root = uid('root')
sch = (f'(kicad_sch (version 20250114) (generator "eeschema") (uuid {root}) (paper "A2")'
       f'(title_block (title "Quadcuber B1 底板（Pico H + 4×DRV8871）") (rev "B1") (company "gonewx/quadcuber"))'
       '(lib_symbols ' + ''.join(v.replace(f'(symbol "{k}"', f'(symbol "B1:{k}"', 1) for k, v in syms.items()) + ')')
placed = [c for c in C if c['pins']]
for i, comp in enumerate(placed):
    ref = comp['ref']
    cx, cy = 30.48 + (i % 9) * 60.96, 30.48 + (i // 9) * 50.8
    hh = max(3.81, math.ceil(len(comp['pins']) / 2) * 1.27 + 1.27)
    sch += f'(symbol (lib_id "B1:{ref}") (at {cx} {cy} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid {uid(ref)})'
    for prop, val, dy, hide in [('Reference', ref, -hh - 3.81, False), ('Value', comp['value'], hh + 3.81, False),
                                ('Footprint', 'B1:' + comp['fp'], 0, True)]:
        sch += f'(property {q(prop)} {q(val)} (at {cx} {cy + dy} 0) {effect(1.27, "(hide yes)" if hide else "")})'
    for num, *_ in pindefs(comp):
        sch += f'(pin {q(num)} (uuid {uid(ref + "-" + num)}))'
    sch += f'(instances (project "{NAME}" (path "/{root}" (reference "{ref}") (unit 1)))))'
    for num, xx, yy, _a in pindefs(comp):
        x, y = cx + xx, cy - yy
        net = comp['pins'][num]
        if net is None:
            sch += f'(no_connect (at {x} {y}) (uuid {uid(ref + num + "nc")}))'
            continue
        ex = x + (-5.08 if xx < 0 else 5.08)
        sch += f'(wire (pts (xy {x} {y}) (xy {ex} {y})) (stroke (width 0) (type default)) (uuid {uid(ref + num + "w")}))'
        a = 0 if xx < 0 else 180
        sch += (f'(global_label {q(net)} (shape bidirectional) (at {ex} {y} {a}) {effect(0.8)} (uuid {uid(ref + num + "l")})'
                f'(property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {ex} {y} {a}) {effect(0.8, "(hide yes)")}))')
sch += '(sheet_instances (path "/" (page "1"))) (embedded_fonts no))'
(HERE / f'{NAME}.kicad_sch').write_text(sch)

# ---- 工程文件：网络类与设计规则（2 层 1oz，规则留余量） ---------------------------------
# 与 route.py 的 DSN 网络类保持同一组线宽。
NETCLASSES = [  # (名称, 线宽, KiCad DRC 间距, 网络匹配)；route.py 给 freerouting 的间距再加 0.05mm 余量，
    # 避免 Pico 异形焊盘多边形近似造成 0.002mm 级别的 DRC 误差。
    ('Default', 0.25, 0.2, None),
    ('Trunk', 2.0, 0.25, ['VIN', 'VIN_F']),
    ('Branch', 1.5, 0.25, ['BUCK_SW']),
    ('Supply', 0.8, 0.2, ['VM', 'SERVO_5V']),
    ('Motor', 0.8, 0.2, ['*_M?']),
    ('Ground', 0.6, 0.2, ['GND']),
    ('Logic5V', 0.6, 0.2, ['5V_LOGIC', 'VSYS']),
]
classes, patterns = [], []
for name, width, clr, members in NETCLASSES:
    classes.append(dict(name=name, clearance=clr, track_width=width, via_diameter=0.8, via_drill=0.4,
                        microvia_diameter=0.3, microvia_drill=0.1, diff_pair_width=0.25, diff_pair_gap=0.25,
                        diff_pair_via_gap=0.25, pcb_color='rgba(0, 0, 0, 0.000)', schematic_color='rgba(0, 0, 0, 0.000)',
                        wire_width=6, bus_width=12, line_style=0))
    patterns += [{'netclass': name, 'pattern': m} for m in members or []]
project = {
    'meta': {'filename': f'{NAME}.kicad_pro', 'version': 1},
    'net_settings': {'classes': classes, 'meta': {'version': 3}, 'netclass_patterns': patterns},
    'board': {'design_settings': {'rules': {
        'min_clearance': 0.2, 'min_track_width': 0.2, 'min_via_diameter': 0.6, 'min_via_annular_width': 0.15,
        'min_through_hole_diameter': 0.3, 'min_copper_edge_clearance': 0.4, 'min_hole_clearance': 0.25,
        'min_hole_to_hole': 0.25, 'solder_mask_to_copper_clearance': 0.0, 'min_resolved_spokes': 1},
        'rule_severities': {'silk_over_copper': 'ignore', 'silk_overlap': 'warning', 'silk_edge_clearance': 'warning',
                            'lib_footprint_issues': 'ignore', 'lib_footprint_mismatch': 'ignore'}}},
    'erc': {'rule_severities': {'global_label_dangling': 'ignore', 'single_global_label': 'ignore'}},
}
(HERE / f'{NAME}.kicad_pro').write_text(json.dumps(project, indent=2, ensure_ascii=False) + '\n')

# ---- PCB：放置、连网、板框、两面地铜 -------------------------------------------------
b = p.BOARD()
b.SetCopperLayerCount(2)
nets = {}
for c in C:
    for k, v in c['pins'].items():
        if v is None:
            c['pins'][k] = f'unconnected-({c["ref"]}-Pad{k})'
for name in sorted({n for c in C for n in c['pins'].values() if n}):
    nets[name] = p.NETINFO_ITEM(b, name)
    b.Add(nets[name])
for comp in C:
    f = p.PCB_IO_KICAD_SEXPR().FootprintLoad(str(LIB), comp['fp'])
    if f is None:
        raise FileNotFoundError(comp['fp'])
    f.SetFPID(p.LIB_ID('B1', comp['fp']))
    f.SetReference(comp['ref'])
    f.SetValue(comp['value'])
    if comp['pins']:
        f.SetPath(p.KIID_PATH('/' + uid(comp['ref'])))
    else:
        f.SetBoardOnly(True)
        f.SetExcludedFromBOM(True)
    x, y = comp['xy']
    f.SetPosition(mm(OX + x, OY + y))
    f.SetOrientationDegrees(comp['rot'])
    f.Value().SetVisible(False)
    f.Reference().SetTextSize(mm(1.0, 1.0))
    f.Reference().SetTextThickness(p.FromMM(0.15))
    for pad in f.Pads():
        net = comp['pins'].get(pad.GetNumber())
        if net:
            pad.SetNet(nets[net])
    b.Add(f)
W, H = BOARD
for (x0, y0), (x1, y1) in [((0, 0), (W, 0)), ((W, 0), (W, H)), ((W, H), (0, H)), ((0, H), (0, 0))]:
    sh = p.PCB_SHAPE(b)
    sh.SetShape(p.SHAPE_T_SEGMENT)
    sh.SetStart(mm(OX + x0, OY + y0))
    sh.SetEnd(mm(OX + x1, OY + y1))
    sh.SetLayer(p.Edge_Cuts)
    sh.SetWidth(p.FromMM(0.05))
    b.Add(sh)
for layer in (p.F_Cu, p.B_Cu):
    z = p.ZONE(b)
    z.SetLayer(layer)
    z.SetNet(nets['GND'])
    z.SetLocalClearance(p.FromMM(0.3))
    z.SetMinThickness(p.FromMM(0.25))
    z.SetPadConnection(p.ZONE_CONNECTION_THT_THERMAL)
    z.SetThermalReliefGap(p.FromMM(0.4))
    z.SetThermalReliefSpokeWidth(p.FromMM(0.8))
    z.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS)
    o = z.Outline()
    o.NewOutline()
    for x, y in [(0.5, 0.5), (W - 0.5, 0.5), (W - 0.5, H - 0.5), (0.5, H - 0.5)]:
        o.Append(p.FromMM(OX + x), p.FromMM(OY + y))
    b.Add(z)
# 贴片件接地扇出：每个贴片 GND 焊盘就近打孔到底层地铜（freerouting 把地当平面，不布地线）。
# DRV8871 的 1、7 脚直接用短线并到散热焊盘，散热焊盘本身已有过孔。
def gnd_fanout(f):
    pads = list(f.Pads())
    smd = [q for q in pads if q.GetAttribute() == p.PAD_ATTRIB_SMD]
    if not smd:
        return
    c = f.GetPosition()
    for q in smd:
        if q.GetNetname() != 'GND' or not q.GetNumber():
            continue
        if any(o is not q and o.GetNumber() == q.GetNumber() and o.GetSize().x > p.FromMM(4) for o in pads):
            continue   # 与大散热焊盘同号的小脚（LM2596 的 3 脚）经散热焊盘接地
        pos = q.GetPosition()
        if f.GetReference().startswith('U') and f.GetValue() == 'DRV8871':
            if q.GetNumber() in ('1', '7'):
                ep = next(e for e in pads if e.GetNumber() == '9' and e.GetAttribute() == p.PAD_ATTRIB_SMD)
                epp = ep.GetPosition()
                end = p.VECTOR2I(pos.x, epp.y + (p.FromMM(1.2) if pos.y > epp.y else -p.FromMM(1.2)))
                if abs(pos.x - epp.x) > abs(pos.y - epp.y):
                    end = p.VECTOR2I(epp.x + (p.FromMM(1.2) if pos.x > epp.x else -p.FromMM(1.2)), pos.y)
                t = p.PCB_TRACK(b)
                t.SetStart(pos)
                t.SetEnd(end)
                t.SetWidth(p.FromMM(0.5))
                t.SetLayer(p.F_Cu)
                t.SetNet(nets['GND'])
                t.SetLocked(True)
                b.Add(t)
            continue
        others = [o.GetPosition() for o in smd if o is not q and o.GetNetname() != 'GND']
        ref = others[0] if others else c
        dx, dy = pos.x - ref.x, pos.y - ref.y
        if dx == 0 and dy == 0:
            dx = 1
        n = (dx * dx + dy * dy) ** 0.5
        size = q.GetSize()
        reach = max(size.x, size.y) / 2 + p.FromMM(0.9)
        via_at = p.VECTOR2I(int(pos.x + dx / n * reach), int(pos.y + dy / n * reach))
        if q.GetSize().x > p.FromMM(4) and q.GetSize().y > p.FromMM(4):
            via_at = pos   # 大散热焊盘（LM2596 散热片）直接在焊盘内打孔
        t = p.PCB_TRACK(b)
        t.SetStart(pos)
        t.SetEnd(via_at)
        t.SetWidth(p.FromMM(0.6))
        t.SetLayer(p.F_Cu)
        t.SetNet(nets['GND'])
        t.SetLocked(True)
        b.Add(t)
        v = p.PCB_VIA(b)
        v.SetPosition(via_at)
        v.SetWidth(p.FromMM(0.8))
        v.SetDrill(p.FromMM(0.4))
        v.SetNet(nets['GND'])
        v.SetLocked(True)
        b.Add(v)


for f in b.GetFootprints():
    gnd_fanout(f)

# 固定电源主干（锁定，自动布线器只补支线）。坐标为板框内 mm。
TRUNKS = [
    # VM：过孔 (36,27) -> 底层竖线 x=36 -> 底层横条 y=57.4（x 13~86，只覆盖四颗 DRV8871 的范围）。
    # 横条两端留空，Pico 右列和左侧的信号可以在底层绕过主干下到各臂。
    ('VM', p.B_Cu, 2.0, [(36, 27), (36, 57.4)]),
    ('VM', p.B_Cu, 2.0, [(13, 57.4), (86, 57.4)]),
    # 舵机 5V：L1 输出端 -> 左边缘 -> 顶层横条 y=79.5，横贯四臂下方
    ('SERVO_5V', p.F_Cu, 1.5, [(4.05, 45), (4.05, 52.5), (1.8, 52.5), (1.8, 79.5), (93, 79.5)]),
]
v = p.PCB_VIA(b)
v.SetPosition(mm(OX + 36, OY + 27))
v.SetWidth(p.FromMM(1.2))
v.SetDrill(p.FromMM(0.6))
v.SetNet(nets['VM'])
v.SetLocked(True)
b.Add(v)
for net, layer, width, pts in TRUNKS:
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        t = p.PCB_TRACK(b)
        t.SetStart(mm(OX + x0, OY + y0))
        t.SetEnd(mm(OX + x1, OY + y1))
        t.SetWidth(p.FromMM(width))
        t.SetLayer(layer)
        t.SetNet(nets[net])
        t.SetLocked(True)
        b.Add(t)


def text(s, x, y, size=1.0, layer=p.F_SilkS):
    t = p.PCB_TEXT(b)
    t.SetText(s)
    t.SetPosition(mm(OX + x, OY + y))
    t.SetTextSize(mm(size, size))
    t.SetTextThickness(p.FromMM(0.15))
    t.SetLayer(layer)
    b.Add(t)


for arm, x in {'R': 16, 'L': 38, 'F': 60, 'B': 82}.items():
    text(arm, x - 10, 82, 1.5)
text('QUADCUBER B1', 48, 50, 1.2)
text('9V ONLY', 48, 52.5, 1.0)
add_labels(b, SILK, OX, OY)
move_refs(b, REF_MOVES, OX, OY)
p.SaveBoard(str(HERE / f'{NAME}.kicad_pcb'), b)
print(f'B1: {len(C)} footprints, {len(nets)} nets, board {W}x{H} mm')
