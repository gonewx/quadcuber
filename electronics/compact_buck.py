#!/usr/bin/env python3
"""Place two input MLCCs on the rear beside VIN/GND, with short paired via paths."""
import pcbnew as p,math,json
from pathlib import Path
H=Path(__file__).resolve().parent;b=p.LoadBoard(str(H/'quadcuber.kicad_pcb'))
def v(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def clear(sh,net):
 for t in b.GetTracks():
  if t.IsOnLayer(p.B_Cu) and t.GetNetCode()!=net and p.SHAPE.Collide(t.GetEffectiveShape(p.B_Cu),sh,p.FromMM(.225)):return False
 for ff in b.GetFootprints():
  if ff.GetReference() in ['C20','C30']:continue
  for d in ff.Pads():
   if d.IsOnLayer(p.B_Cu) and d.GetNetCode()!=net and p.SHAPE.Collide(d.GetEffectiveShape(p.B_Cu),sh,p.FromMM(.225)):return False
 return True
report=[]
for f in b.GetFootprints():
 if f.GetReference() not in ['C20','C30']:continue
 x=99 if f.GetReference()=='C20' else 148
 if f.GetLayer()==p.F_Cu:f.Flip(f.GetPosition(),False)
 f.SetOrientationDegrees(270)
 candidates=[]
 for dx in [i*.2 for i in range(-5,36)]:
  for dy in [i*.2 for i in range(-10,11)]:
   f.SetPosition(v(x+dx,88+dy));valid=True
   for d in f.Pads():
    sh=d.GetEffectiveShape(p.B_Cu)
    if not clear(sh,d.GetNetCode()):valid=False;break
    if any(p.SHAPE.Collide(sh,p.SHAPE_CIRCLE(t.GetPosition(),int(t.GetDrill()/2)),p.FromMM(.25)) for t in b.GetTracks() if isinstance(t,p.PCB_VIA)):valid=False;break
   if valid:candidates.append((abs(dx-1.1375)+abs(dy),dx,dy))
 assert candidates,'No clear compact MLCC placement'
 _,dx,dy=min(candidates);f.SetPosition(v(x+dx,88+dy));connections=[]
 for d in f.Pads():
  vi=sorted([t for t in b.GetTracks() if isinstance(t,p.PCB_VIA) and t.GetNetCode()==d.GetNetCode()],key=lambda t:(t.GetPosition()-d.GetPosition()).EuclideanNorm())
  for vv in vi:
   sh=p.SHAPE_SEGMENT(d.GetPosition(),vv.GetPosition(),p.FromMM(.8))
   if clear(sh,d.GetNetCode()):
    t=p.PCB_TRACK(b);t.SetStart(d.GetPosition());t.SetEnd(vv.GetPosition());t.SetWidth(p.FromMM(.8));t.SetLayer(p.B_Cu);t.SetNetCode(d.GetNetCode());b.Add(t)
    connections.append({'pin':d.GetNumber(),'via_mm':[p.ToMM(vv.GetPosition().x),p.ToMM(vv.GetPosition().y)],'trace_mm':round(p.ToMM(t.GetLength()),3)});break
  else:raise RuntimeError('No direct local via path')
 report.append({'ref':f.GetReference(),'position_mm':[x+dx,88+dy],'side':'B.Cu','connections':connections})
for t in list(b.GetTracks()):
 if not isinstance(t,p.PCB_VIA) and t.GetNetname()=='VM' and abs(p.ToMM(t.GetStart().y)-95.025)<.002 and abs(p.ToMM(t.GetLength())-.9)<.002:b.Delete(t)
for t in list(b.GetTracks()):
 if isinstance(t,p.PCB_VIA) and t.GetNetname()=='VM' and abs(p.ToMM(t.GetPosition().y)-94.1796)<.002 and any(abs(p.ToMM(t.GetPosition().x)-x)<.002 for x in [101.6914,150.6914]):b.Delete(t)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(H/'quadcuber.kicad_pcb'),b)
(H.parent/'generated/electronics/buck-loop.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
