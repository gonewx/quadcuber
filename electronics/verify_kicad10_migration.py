#!/usr/bin/env python3
"""Compare A1 migration geometry with the frozen Git baseline using KiCad 10 pcbnew.

Run with the KiCad Python interpreter; writes kicad10-migration.json.
NPTH copper layer masks are normalized to through-board (native 10 conversion).
"""
import subprocess,tempfile,xml.etree.ElementTree as ET
from toolchain import require_version
import pcbnew as p
import hashlib,json
from pathlib import Path
require_version(p.GetBuildVersion())
ROOT=Path(__file__).resolve().parents[1]
BASELINE='e34395e68b175cf9a279664fd4a13fd6573d95db'
v=lambda a:[a.x,a.y]
def poly(a):
 def points(line):return [v(line.CPoint(i)) for i in range(line.PointCount())]
 return [{'outline':points(a.COutline(i)),'holes':[points(a.CHole(i,h)) for h in range(a.HoleCount(i))]} for i in range(a.OutlineCount())]
def snapshot(path):
 b=p.LoadBoard(str(path))
 footprints={}
 for f in b.GetFootprints():
  pads=[]
  for q in f.Pads():pads.append([q.GetNumber(),q.GetNetname(),v(q.GetPosition()),v(q.GetSize()),v(q.GetDrillSize()),q.GetShape(),q.GetOrientationDegrees(),('NPTH through board' if q.GetAttribute()==p.PAD_ATTRIB_NPTH else list(q.GetLayerSet().Seq()))])
  footprints[f.GetReference()]={'position':v(f.GetPosition()),'orientation':f.GetOrientationDegrees(),'layer':f.GetLayer(),'footprint':str(f.GetFPID().GetLibItemName()),'pads':sorted(pads,key=str)}
 tracks=[]
 for t in b.GetTracks():
  row=[t.GetClass(),t.GetNetname(),v(t.GetStart()),v(t.GetEnd()),t.GetLayer(),t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth()]
  if isinstance(t,p.PCB_VIA):row += [t.GetDrillValue(),t.TopLayer(),t.BottomLayer()]
  if isinstance(t,p.PCB_ARC):row += [v(t.GetMid())]
  tracks.append(row)
 zones=[]
 for z in b.Zones():zones.append([z.GetNetname(),list(z.GetLayerSet().Seq()),poly(z.Outline()),{str(l):poly(z.GetFilledPolysList(l)) for l in z.GetLayerSet().Seq()}])
 outline=[]
 for d in b.GetDrawings():
  if d.GetLayer()==p.Edge_Cuts and isinstance(d,p.PCB_SHAPE):outline.append([d.GetShape(),v(d.GetStart()),v(d.GetEnd()),d.GetWidth()])
 return {'footprints_and_pads':footprints,'tracks_and_vias':sorted(tracks,key=str),'zone_outlines_and_filled_copper':sorted(zones,key=str),'board_outline':sorted(outline,key=str),'copper_layer_count':b.GetCopperLayerCount()}
baseline_bytes=subprocess.check_output(['git','show',BASELINE+':electronics/quadcuber.kicad_pcb'],cwd=ROOT)
with tempfile.TemporaryDirectory(prefix='quadcuber-migration-') as temporary:
 old=Path(temporary)/'baseline.kicad_pcb';old.write_bytes(baseline_bytes);a=snapshot(old)
new=ROOT/'electronics/quadcuber.kicad_pcb';b=snapshot(new)
def connected_pins(root):
 return sorted((n.get('ref'),n.get('pin'),net.get('name')) for net in root.findall('./nets/net') if not net.get('name','').startswith('unconnected-') for n in net.findall('node'))
old_netlist=ET.fromstring(subprocess.check_output(['git','show',BASELINE+':generated/electronics/netlist.xml'],cwd=ROOT))
old_pins=connected_pins(old_netlist);new_pins=connected_pins(ET.parse(ROOT/'generated/electronics/netlist.xml').getroot())
digest=lambda obj:hashlib.sha256(json.dumps(obj,sort_keys=True).encode()).hexdigest()
report={'tool_version':p.GetBuildVersion(),'baseline_commit':'e34395e68b175cf9a279664fd4a13fd6573d95db','baseline_pcb_sha256':hashlib.sha256(baseline_bytes).hexdigest(),'migrated_pcb_sha256':hashlib.sha256(new.read_bytes()).hexdigest(),'geometry_comparison':{k:{'identical':a[k]==b[k],'baseline_digest':digest(a[k]),'migrated_digest':digest(b[k])} for k in a},'connected_symbol_pins':{'identical':old_pins==new_pins,'baseline_count':len(old_pins),'migrated_count':len(new_pins)}, 'native_normalization':'J5 two unnumbered 0.65 mm NPTH holes: KiCad 10 resave expands copper layer mask to *.Cu; unchanged position, drill, pad dimensions. NPTH layer masks are normalized to through-board in this physical geometry comparison.', 'limits':'Geometry comparison and current EDA checks only; not a replacement for independent review or hardware/thermal/3D validation.'}
(ROOT/'generated/electronics/kicad10-migration.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert a==b and old_pins==new_pins
