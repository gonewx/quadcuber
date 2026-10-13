#!/usr/bin/env python3
"""Compare physical scope and pin assignments against the exact J1 baseline.

Run with KiCad 10.0.7 Python. This never writes PCB/project/source files.
"""
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
import xml.etree.ElementTree as ET
import pcbnew as p
from toolchain import require_version

require_version(p.GetBuildVersion())
ROOT = Path(__file__).resolve().parents[1]
BASE = 'cf614f3de777b39048b341b3983abcfe7e7962f3'
OUT = ROOT/'generated/electronics/j1-raspc722x-revision'
old_bytes = subprocess.check_output(['git', 'show', BASE+':electronics/quadcuber.kicad_pcb'], cwd=ROOT)
new_bytes = (ROOT/'electronics/quadcuber.kicad_pcb').read_bytes()
v = lambda q: [q.x, q.y]


def snapshot(board):
    fps = {}
    for f in board.GetFootprints():
        fps[f.GetReference()] = [v(f.GetPosition()), f.GetOrientationDegrees(),
            [f.GetFPID().GetLibNickname(), f.GetFPID().GetLibItemName()],
            sorted([[a.GetNumber(), a.GetNetname(), v(a.GetPosition()), v(a.GetSize()),
                     v(a.GetDrillSize()), a.GetShape(), a.GetOrientationDegrees(),
                     list(a.GetLayerSet().Seq())] for a in f.Pads()], key=str)]
    tracks = {t.m_Uuid.AsString(): [t.GetClass(), t.GetNetname(), v(t.GetStart()), v(t.GetEnd()),
              t.GetLayer(), t.GetWidth(p.F_Cu) if isinstance(t, p.PCB_VIA) else t.GetWidth(),
              t.GetDrillValue() if isinstance(t, p.PCB_VIA) else None] for t in board.GetTracks()}
    zones = {}
    for z in board.Zones():
        poly = z.Outline()
        points = [[v(poly.COutline(i).CPoint(j)) for j in range(poly.COutline(i).PointCount())]
                  for i in range(poly.OutlineCount())]
        zones[z.m_Uuid.AsString()] = [z.GetNetname(), list(z.GetLayerSet().Seq()), points,
                                    z.GetAssignedPriority(), z.GetPadConnection(), z.GetLocalClearance()]
    edge = sorted([[d.GetShape(), v(d.GetStart()), v(d.GetEnd()), d.GetWidth()]
                   for d in board.GetDrawings() if isinstance(d, p.PCB_SHAPE) and d.GetLayer() == p.Edge_Cuts])
    return fps, tracks, zones, edge


with tempfile.TemporaryDirectory() as directory:
    file = Path(directory)/'baseline.kicad_pcb'; file.write_bytes(old_bytes)
    a = snapshot(p.LoadBoard(str(file)))
b = snapshot(p.LoadBoard(str(ROOT/'electronics/quadcuber.kicad_pcb')))
changed_fps = sorted(k for k in a[0] if a[0][k] != b[0][k])
assert a[0].keys() == b[0].keys() and changed_fps == ['J1']
shared = a[1].keys() & b[1].keys()
assert all(a[1][k] == b[1][k] for k in shared)
removed = [a[1][k] for k in a[1].keys()-b[1].keys()]
added = [b[1][k] for k in b[1].keys()-a[1].keys()]
assert len(removed) == 3 and all(t[1] == 'VIN' and t[5] == 1000000 for t in removed)
assert len(added) == 2 and all(t[1] == 'VIN' and t[5] == 1800000 for t in added)
assert a[2].keys() == b[2].keys()
changed_zones = [k for k in a[2] if a[2][k] != b[2][k]]
assert len(changed_zones) == 1 and a[2][changed_zones[0]][0] == 'VIN'
assert a[3] == b[3]
for ext in ['pro', 'dru']:
    rel = 'electronics/quadcuber.kicad_'+ext
    assert (ROOT/rel).read_bytes() == subprocess.check_output(['git', 'show', BASE+':'+rel], cwd=ROOT)
oldxml = ET.fromstring(subprocess.check_output(['git', 'show', BASE+':generated/electronics/netlist.xml'], cwd=ROOT))
newxml = ET.parse(ROOT/'generated/electronics/netlist.xml').getroot()
nodes = lambda root: {(n.get('ref'), n.get('pin')): net.get('name') for net in root.findall('./nets/net') for n in net.findall('node')}
an, bn = nodes(oldxml), nodes(newxml)
assert an.keys() <= bn.keys() and all(an[k] == bn[k] for k in an)
assert bn.keys()-an.keys() == {('J1', '3')}
assert bn[('J1', '3')] == 'unconnected-(J1-SLEEVE_SHUNT_NC-Pad3)'
report = {'pass': True, 'kicad': p.GetBuildVersion(), 'baseline_commit': BASE,
          'baseline_sha256': hashlib.sha256(old_bytes).hexdigest(),
          'candidate_sha256': hashlib.sha256(new_bytes).hexdigest(),
          'changed_footprints': changed_fps, 'unchanged_footprints': len(a[0])-1,
          'unchanged_tracks_and_vias': len(shared), 'removed_VIN_segments': 3, 'added_VIN_segments': 2,
          'only_VIN_zone_definition_changed': True, 'board_outline_and_project_rules_unchanged': True,
          'all_existing_pin_networks_unchanged': True, 'new_pin': 'J1.3 NC',
          'zone_fill_note': 'Zones refilled natively. This scope comparison excludes fill caches.',
          'original_Switchcraft_PDF_viewed_in_this_executor': False}
(OUT/'scope-check.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
