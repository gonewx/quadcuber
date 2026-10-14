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

# 网络类（单位 µm）与 generate.py 的 NETCLASSES 一致。VM/舵机 5V 主干由 generate.py 预先画好并锁定
# （VM 2mm、舵机 5V 1.5mm），这里只补 1mm 支线；电机 0.8mm 才能从 DRV8871 的 1.27mm 间距引脚引出。
CLASSES = [
    ('Trunk', 2000, 300, lambda n: n in ('VIN', 'VIN_F')),
    ('Branch', 1500, 300, lambda n: n == 'BUCK_SW'),
    ('Supply', 1000, 250, lambda n: n in ('VM', 'SERVO_5V')),
    ('Motor', 800, 250, lambda n: re.fullmatch(r'[RLFB]_M[12]', n)),
    ('Ground', 600, 250, lambda n: n == 'GND'),
    ('Logic5V', 600, 250, lambda n: n in ('5V_LOGIC', 'VSYS')),
    ('Signal', 300, 250, lambda n: True),
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
p.SaveBoard(str(PCB), b)
print('布线完成：', len(b.GetTracks()), '段走线/过孔')
