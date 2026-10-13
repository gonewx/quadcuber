#!/usr/bin/env python3
"""Reproduce the local RASPC722X PCB candidate from the frozen baseline.

Only J1, its three VIN tracks, the VIN zone outline and two input labels change.
Source/schematic/BOM are maintained separately; never call the full generator.
"""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import pcbnew as p
from toolchain import require_version

require_version(p.GetBuildVersion())
H = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--baseline', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
assert args.baseline.with_suffix('.kicad_pro').exists(), 'Baseline needs its matching project rules'
assert args.baseline.with_suffix('.kicad_dru').exists(), 'Baseline needs its matching custom rules'
b = p.LoadBoard(str(args.baseline))
old = next(f for f in b.GetFootprints() if f.GetReference() == 'J1')
assert str(old.GetFPID().GetLibItemName()).startswith('TerminalBlock_Phoenix_')
assert (old.GetPosition().x, old.GetPosition().y) == (95000000, 58000000)
vec = lambda x, y: p.VECTOR2I(round(x * 1e6), round(y * 1e6))
fp = p.PCB_IO_KICAD_SEXPR().FootprintLoad(str(H/'lib/Quadcuber.pretty'), 'Jack_DC_Switchcraft_RASPC722X')
fp.SetFPID(p.LIB_ID('Quadcuber', 'Jack_DC_Switchcraft_RASPC722X'))
fp.SetUuid(old.m_Uuid)
fp.SetPath(old.GetPath())
fp.SetReference('J1')
fp.SetValue('9V DC center-positive')
fp.SetPosition(vec(95.5, 50))
fp.SetField('MPN', 'RASPC722X')
fp.SetField('Manufacturer', 'Switchcraft')
for field in fp.GetFields():
    field.SetLayer(p.F_Fab)
    field.SetVisible(False)
fp.Reference().SetVisible(True)
fp.Reference().SetPosition(vec(95.5, 53))
tree = ET.parse(H.parent/'generated/electronics/netlist.xml')
nc = next(net.get('name') for net in tree.findall('./nets/net')
          if any(n.get('ref') == 'J1' and n.get('pin') == '3' for n in net.findall('node')))
assert nc.startswith('unconnected-')
net = p.NETINFO_ITEM(b, nc)
b.Add(net)
for pad in fp.Pads():
    pad.SetNet(b.FindNet({'1': 'VIN', '2': 'GND', '3': nc}[pad.GetNumber()]))
    # Solid plane connections preserve the high-current inlet; no thin thermals.
    if pad.GetNumber() in ['1', '2']:
        pad.SetLocalZoneConnection(p.ZONE_CONNECTION_FULL)
b.Remove(old)
b.Add(fp)
tracks = [t for t in b.GetTracks() if t.GetNetname() == 'VIN']
assert len(tracks) == 3 and all(t.GetWidth() == 1000000 for t in tracks)
for t in tracks:
    b.Remove(t)
route = [(95.5, 63.7414), (101.0086, 63.7414), (105.75, 59)]
for a, c in zip(route, route[1:]):
    t = p.PCB_TRACK(b)
    t.SetStart(vec(*a)); t.SetEnd(vec(*c)); t.SetWidth(1800000)
    t.SetLayer(p.F_Cu); t.SetNet(b.FindNet('VIN')); b.Add(t)
zone = next(z for z in b.Zones() if z.GetNetname() == 'VIN')
zone.Outline().RemoveAllContours()
zone.Outline().NewOutline()
for x, y in [(92.7, 62.5), (99.5, 62.5), (104.5, 57.8), (106.6, 57.8),
             (106.6, 60.2), (101.5, 65.2), (92.7, 65.2)]:
    zone.Outline().Append(round(x*1e6), round(y*1e6))
for text in list(b.GetDrawings()):
    if isinstance(text, p.PCB_TEXT):
        if text.GetText() == '+9V' and text.GetPosition() == vec(95, 66):
            text.SetText('9V CENTER +'); text.SetPosition(vec(95.5, 67))
        elif text.GetText() == 'GND' and text.GetPosition() == vec(100.08, 66):
            b.Remove(text)
p.ZONE_FILLER(b).Fill(b.Zones())
p.SaveBoard(str(args.output), b)
print(json.dumps({'kicad': p.GetBuildVersion(), 'output': str(args.output),
                  'baseline_sha256': hashlib.sha256(args.baseline.read_bytes()).hexdigest(),
                  'output_sha256': hashlib.sha256(args.output.read_bytes()).hexdigest(),
                  'vin_track_width_mm': 1.8, 'vin_route_mm': route, 'shunt_net': nc}, indent=2))
