#!/usr/bin/env python3
"""B1 自动布线：导出 DSN（显式线宽）→ freerouting → 导入 SES → 填充地铜。用 KiCad 10 Python 运行。

用法：route.py <freerouting.jar> [最大轮数]
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pcbnew as p

HERE = Path(__file__).resolve().parent
PCB = HERE / 'quadcuber-b1.kicad_pcb'
JAR = sys.argv[1]
PASSES = sys.argv[2] if len(sys.argv) > 2 else '60'

# 网络类（单位 µm）：线宽与 generate.py 的 NETCLASSES 一致，间距比 KiCad 规则多 0.05mm。VM/舵机 5V 主干由 generate.py 预先画好并锁定
# （VM 2mm、舵机 5V 1.5mm），这里只补 0.8mm 支线（每臂 ≤1.5A）；电机 0.8mm 才能从 DRV8871 的 1.27mm 间距引脚引出。
CLASSES = [
    ('Trunk', 2000, 300, lambda n: n in ('VIN', 'VIN_F')),
    ('Branch', 1500, 300, lambda n: n == 'BUCK_SW'),
    ('Supply', 800, 300, lambda n: n in ('VM', 'SERVO_5V')),
    ('Motor', 800, 250, lambda n: re.fullmatch(r'[RLFB]_M[12]', n)),
    ('Ground', 600, 250, lambda n: n == 'GND'),
    ('Logic5V', 600, 250, lambda n: n in ('5V_LOGIC', 'VSYS')),
    ('Signal', 250, 250, lambda n: True),
]


def klass(net):
    return next(name for name, _w, _c, match in CLASSES if match(net))


b = p.LoadBoard(str(PCB))
with tempfile.TemporaryDirectory(prefix='b1-route-') as td:
    dsn, ses = Path(td) / 'b1.dsn', Path(td) / 'b1.ses'
    assert p.ExportSpecctraDSN(b, str(dsn)), 'DSN 导出失败'
    s = dsn.read_text()
    spans = []
    for m in re.finditer(r'    \(class ', s):
        depth = 0
        for i in range(m.start(), len(s)):
            depth += {'(': 1, ')': -1}.get(s[i], 0)
            if depth == 0:
                spans.append((m.start(), i + 1))
                break
    assert spans, 'DSN 中没有网络类'
    start = spans[0][0]
    for a, z in reversed(spans):
        s = s[:a] + s[z:]
    nets = [str(n.GetNetname()) for n in b.GetNetsByNetcode().values() if n.GetNetname()]
    block = ''
    for name, width, clr, _m in CLASSES:
        members = ' '.join(f'"{n}"' for n in nets if klass(n) == name)
        if members:
            block += (f'    (class {name} {members} (circuit (use_via "Via[0-1]_800:400_um"))'
                      f'(rule (width {width}) (clearance {clr})))\n')
    s = s[:start] + block + s[start:]
    dsn.write_text(s)
    subprocess.run(['java', '-Djava.awt.headless=true', '-jar', JAR, '-de', str(dsn), '-do', str(ses), '-mp', PASSES,
                    '--gui.enabled=false'], check=True, timeout=1800)
    assert p.ImportSpecctraSES(b, str(ses)), 'SES 导入失败'
p.ZONE_FILLER(b).Fill(b.Zones())

# 地缝合过孔：在两面地铜都已覆盖、且离其他铜足够远的格点打过孔，把两面零散地铜连成一片。
gnd = b.GetNetcodeFromNetname('GND')
# 每层两份：整层地铜 all，和面积最大的主地铜 main（都向内收 0.55mm，保证过孔不碰其他铜）。
# 只在“一面是主地铜”的位置打孔：既能把另一面的碎块接回主地，又不会把两块碎块互相接成新的孤岛。
fills = {}
for z in b.Zones():
    if z.GetNetCode() == gnd:
        for layer in (p.F_Cu, p.B_Cu):
            if z.IsOnLayer(layer):
                poly = z.GetFilledPolysList(layer).CloneDropTriangulation()
                main_i = max(range(poly.OutlineCount()), key=lambda i: poly.Outline(i).Area())
                main = p.SHAPE_POLY_SET()
                main.AddPolygon(poly.Polygon(main_i))
                for s in (poly, main):
                    s.Deflate(p.FromMM(0.55), p.CORNER_STRATEGY_ROUND_ALL_CORNERS, p.FromMM(0.01))
                fills[layer] = (poly, main)
added = 0
holes = [v.GetPosition() for v in b.GetTracks() if v.GetClass() == 'PCB_VIA']
holes += [q.GetPosition() for q in b.GetPads() if q.GetDrillSize().x > 0]
bbox = b.GetBoardEdgesBoundingBox()
step = p.FromMM(4.0)
for x in range(bbox.GetLeft() + step // 2, bbox.GetRight(), step):
    for y in range(bbox.GetTop() + step // 2, bbox.GetBottom(), step):
        pt = p.VECTOR2I(x, y)
        far = all((h.x - x) ** 2 + (h.y - y) ** 2 > p.FromMM(1.5) ** 2 for h in holes)
        (f_all, f_main), (b_all, b_main) = fills[p.F_Cu], fills[p.B_Cu]
        if far and ((f_main.Contains(pt) and b_all.Contains(pt)) or (b_main.Contains(pt) and f_all.Contains(pt))):
            v = p.PCB_VIA(b)
            v.SetPosition(pt)
            v.SetWidth(p.FromMM(0.8))
            v.SetDrill(p.FromMM(0.4))
            v.SetNetCode(gnd)
            b.Add(v)
            added += 1
p.ZONE_FILLER(b).Fill(b.Zones())
print('地缝合过孔：', added)
p.SaveBoard(str(PCB), b)
print('布线完成：', len(b.GetTracks()), '段走线/过孔')
