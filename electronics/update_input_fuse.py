#!/usr/bin/env python3
"""F1 correction only: verified 407 8A/24V time-lag part and local land pattern.
Does not regenerate the board or alter any trace. Requires system pcbnew.
"""
from pathlib import Path
import json,csv,runpy
import pcbnew as p
H=Path(__file__).resolve().parent;O=H.parent/'generated/electronics'
def v(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
name='Fuse_Littelfuse_407_1206';lib=H/'lib/Quadcuber.pretty'
fp=p.PCB_IO_KICAD_SEXPR().FootprintLoad(str(lib),'Fuse_1206_3216Metric')
fp.SetFPID(p.LIB_ID('Quadcuber',name));fp.SetValue('0407008.WR')
fp.SetLibDescription('Littelfuse407 datasheet2020-09-14: land1.0x1.8mm, gap1.5mm, total3.5mm')
for pad in fp.Pads():
 pad.SetPosition(v(-1.25 if pad.GetNumber()=='1' else 1.25,0));pad.SetSize(v(1,1.8));pad.SetShape(p.PAD_SHAPE_RECT)
p.PCB_IO_KICAD_SEXPR().FootprintSave(str(lib),fp)
b=p.LoadBoard(str(H/'quadcuber.kicad_pcb'))
f=next(f for f in b.GetFootprints() if f.GetReference()=='F1')
assert abs(f.GetOrientationDegrees())<.001, f.GetOrientationDegrees()
f.SetFPID(p.LIB_ID('Quadcuber',name));f.SetValue('8A 24V time-lag fuse')
f.SetLibDescription(fp.GetLibDescription())
for pad in f.Pads():
 pad.SetPosition(f.GetPosition()+v(-1.25 if pad.GetNumber()=='1' else 1.25,0));pad.SetSize(v(1,1.8));pad.SetShape(p.PAD_SHAPE_RECT)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(H/'quadcuber.kicad_pcb'),b)
# Surgical text change retains existing native symbol UUIDs, geometry and project rules.
for path in [H/'power.kicad_sch',H/'lib/Quadcuber.kicad_sym']:
 s=path.read_text().replace('0467008.NR','0407008.WR').replace('8A 32V fuse','8A 24V time-lag fuse').replace('Quadcuber:Fuse_1206_3216Metric','Quadcuber:'+name)
 path.write_text(s)
# Synchronize actual source/BOM; preserve unrelated metadata and original package names.
C=runpy.run_path(str(H/'circuit.py'))['C'];f1=next(c for c in C if c['ref']=='F1')
cs=json.loads((O/'circuit.json').read_text())
for c in cs:
 if c['ref']=='F1':c.update({k:f1[k] for k in ['value','mpn','fp','note']});c.pop('source_fp',None)
(O/'circuit.json').write_text(json.dumps(cs,indent=2,ensure_ascii=False)+'\n')
with (O/'bom.csv').open() as h:r=csv.DictReader(h);fields=r.fieldnames;rows=list(r)
for row in rows:
 if row['Reference']=='F1':row.update(Value=f1['value'],MPN=f1['mpn'],Footprint=f1['fp'],Notes=f1['note'])
with (O/'bom.csv').open('w') as h:w=csv.DictWriter(h,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
print('Updated F1 only; no track or via edits')
