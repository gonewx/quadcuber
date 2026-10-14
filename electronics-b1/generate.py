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
from circuit import C, BOARD  # noqa: E402

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


# ---- 自建封装：自恢复保险丝，径向引脚间距 5.1mm --------------------------------------
fp = p.FOOTPRINT(None)
fp.SetFPID(p.LIB_ID('B1', 'Fuse_PTC_Radial_P5.10mm'))
fp.SetReference('REF**')
fp.SetValue('PTC')
ls = p.LSET.AllCuMask()
ls.AddLayer(p.F_Mask)
ls.AddLayer(p.B_Mask)
for num, x in [('1', 0.0), ('2', 5.1)]:
    pad = p.PAD(fp)
    pad.SetNumber(num)
    pad.SetAttribute(p.PAD_ATTRIB_PTH)
    pad.SetShape(p.PAD_SHAPE_RECTANGLE if num == '1' else p.PAD_SHAPE_CIRCLE)
    pad.SetSize(mm(2.0, 2.0))
    pad.SetDrillSize(mm(1.0, 1.0))
    pad.SetLayerSet(ls)
    pad.SetPosition(mm(x, 0))
    fp.Add(pad)
for layer, (x0, y0, x1, y1) in [(p.F_SilkS, (-1.6, -2.2, 6.7, 2.2)), (p.F_CrtYd, (-1.8, -2.5, 6.9, 2.5)),
                                 (p.F_Fab, (-1.4, -2.0, 6.5, 2.0))]:
    sh = p.PCB_SHAPE(fp)
    sh.SetShape(p.SHAPE_T_RECT)
    sh.SetStart(mm(x0, y0))
    sh.SetEnd(mm(x1, y1))
    sh.SetLayer(layer)
    sh.SetWidth(p.FromMM(0.12))
    fp.Add(sh)
p.PCB_IO_KICAD_SEXPR().FootprintSave(str(LIB), fp)

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
# 与 route.py 的 DSN 网络类保持同一组线宽/间距，避免 freerouting 与 KiCad DRC 口径不一致。
NETCLASSES = [  # (名称, 线宽, 间距, 网络匹配)
    ('Default', 0.3, 0.25, None),
    ('Trunk', 2.0, 0.3, ['VIN', 'VIN_F']),
    ('Branch', 1.5, 0.3, ['BUCK_SW']),
    ('Supply', 1.0, 0.25, ['VM', 'SERVO_5V']),
    ('Motor', 0.8, 0.25, ['*_M?']),
    ('Ground', 0.6, 0.25, ['GND']),
    ('Logic5V', 0.6, 0.25, ['5V_LOGIC', 'VSYS']),
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
    o = z.Outline()
    o.NewOutline()
    for x, y in [(0.5, 0.5), (W - 0.5, 0.5), (W - 0.5, H - 0.5), (0.5, H - 0.5)]:
        o.Append(p.FromMM(OX + x), p.FromMM(OY + y))
    b.Add(z)
# 固定电源主干（锁定，自动布线器只补支线）。坐标为板框内 mm。
TRUNKS = [
    # VM：C2 正极 -> 板中竖线 x=60.8 -> 底层横条 y=57.7，横贯四臂上方
    ('VM', p.B_Cu, 2.0, [(54, 7), (54, 12), (60.8, 12), (60.8, 57.7)]),
    ('VM', p.B_Cu, 2.0, [(2.5, 57.7), (96.5, 57.7)]),
    # 舵机 5V：L1 输出端 -> 左边缘 -> 顶层横条 y=79.5，横贯四臂下方
    ('SERVO_5V', p.F_Cu, 1.5, [(22, 45), (22, 52.5), (1.8, 52.5), (1.8, 79.5), (93, 79.5)]),
]
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
p.SaveBoard(str(HERE / f'{NAME}.kicad_pcb'), b)
print(f'B1: {len(C)} footprints, {len(nets)} nets, board {W}x{H} mm')
