#!/usr/bin/env python3
"""Add only R500/R501 and four short plane connections; preserve existing routing."""
from pathlib import Path
import uuid,runpy,json
import pcbnew as p
H=Path(__file__).resolve().parent
b=p.LoadBoard(str(H/'quadcuber.kicad_pcb'));C=runpy.run_path(str(H/'circuit.py'))['C']
def v(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def uid(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,'https://github.com/gonewx/quadcuber/pcb/'+s))
existing={f.GetReference() for f in b.GetFootprints()}
assert not existing.intersection(['R500','R501']),'already installed; do not duplicate'
for c in C:
 if c['ref'] not in ['R500','R501']:continue
 name=c['fp'].split(':')[1];f=p.PCB_IO_KICAD_SEXPR().FootprintLoad(str(H/'lib/Quadcuber.pretty'),name)
 f.SetFPID(p.LIB_ID('Quadcuber',name));f.SetReference(c['ref']);f.SetValue(c['value']);f.SetPath(p.KIID_PATH('/'+uid('root')+'/'+uid('sheet-power')+'/'+uid(c['ref'])))
 f.SetPosition(v(c['xy'][0]+50,c['xy'][1]+50));f.Value().SetVisible(False)
 f.Reference().SetLayer(p.F_Fab);f.Reference().SetTextSize(v(.8,.8));f.Reference().SetTextThickness(p.FromMM(.12))
 b.Add(f)
 for pad in f.Pads():
  net=b.FindNet(c['pins'][pad.GetNumber()]);pad.SetNet(net)
  end=pad.GetPosition()+v(-1.8 if pad.GetNumber()=='1' else 1.8,0)
  t=p.PCB_TRACK(b);t.SetStart(pad.GetPosition());t.SetEnd(end);t.SetWidth(p.FromMM(.6));t.SetLayer(p.F_Cu);t.SetNet(net);b.Add(t)
  via=p.PCB_VIA(b);via.SetPosition(end);via.SetWidth(p.F_Cu,p.FromMM(.7));via.SetDrill(p.FromMM(.3));via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(net);b.Add(via)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(H/'quadcuber.kicad_pcb'),b)
print('Added two 300R VM bleed resistors and four trace/via plane fanouts')
