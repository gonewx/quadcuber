#!/usr/bin/env python3
"""Add close ground returns for A1 logic pads, using actual PCB clearance geometry.
Candidate vias avoid copper and drilled holes. Native DRC remains authoritative.
"""
from pathlib import Path
import math,pcbnew as p
H=Path(__file__).resolve().parent;b=p.LoadBoard(str(H/'quadcuber.kicad_pcb'))
def v(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def xy(a):return p.ToMM(a.x),p.ToMM(a.y)
obs=[pa for f in b.GetFootprints() for pa in f.Pads()]+list(b.GetTracks())
def shape(ob,ly):
 if isinstance(ob,p.PAD):return ob.GetEffectiveShape(ly) if ob.IsOnLayer(ly) else None
 return ob.GetEffectiveShape(ly) if isinstance(ob,p.PCB_VIA) or ob.GetLayer()==ly else None
def free(sh,ly,net='GND'):
 for ob in obs:
  if ob.GetNetname()==net:continue
  other=shape(ob,ly)
  if other and p.SHAPE.Collide(sh,other,p.FromMM(.22)):return False
 return True
def hole_free(pos):
 for ob in obs:
  if isinstance(ob,p.PCB_VIA):dr=ob.GetDrill()
  elif isinstance(ob,p.PAD):dr=ob.GetDrillSize().x
  else:continue
  if dr and (ob.GetPosition()-pos).EuclideanNorm() < (p.FromMM(.3)+dr)/2+p.FromMM(.26):return False
 return True
def nearest(pos):
 holes=[ob.GetPosition() for ob in obs if ob.GetNetname()=='GND' and (isinstance(ob,p.PCB_VIA) or isinstance(ob,p.PAD) and ob.GetDrillSize().x)]
 return min((h-pos).EuclideanNorm() for h in holes)/1e6
count=0;unplaced=[]
for f in b.GetFootprints():
 x,y=xy(f.GetPosition())
 if x>90 or y>112 or f.GetReference()=='U1':continue
 for pad in f.Pads():
  if pad.GetNetname()!='GND' or pad.GetDrillSize().x:continue
  pos=pad.GetPosition();x,y=xy(pos)
  if nearest(pos)<=1.7:continue
  ly=p.B_Cu if f.IsFlipped() else p.F_Cu;found=False
  for radius in [.9,1.1,1.3,1.5,1.7,1.9,2.1,2.3,2.5]:
   for angle in range(0,360,30):
    dest=v(x+radius*math.cos(math.radians(angle)),y+radius*math.sin(math.radians(angle)))
    if not hole_free(dest):continue
    circle=p.SHAPE_CIRCLE(dest,p.FromMM(.3))
    if not all(free(circle,ll) for ll in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]):continue
    if not free(p.SHAPE_SEGMENT(pos,dest,p.FromMM(.25)),ly):continue
    via=p.PCB_VIA(b);via.SetPosition(dest);via.SetWidth(p.F_Cu,p.FromMM(.6));via.SetDrill(p.FromMM(.3));via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetViaType(p.VIATYPE_THROUGH);via.SetNetCode(b.GetNetcodeFromNetname('GND'));b.Add(via);obs.append(via)
    t=p.PCB_TRACK(b);t.SetStart(pos);t.SetEnd(dest);t.SetWidth(p.FromMM(.25));t.SetLayer(ly);t.SetNetCode(b.GetNetcodeFromNetname('GND'));b.Add(t);obs.append(t)
    found=True;count+=1;break
   if found:break
  if not found:unplaced.append((f.GetReference(),pad.GetNumber(),round(nearest(pos),2)))
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(H/'quadcuber.kicad_pcb'),b)
print('Added ground stitches:',count,'pads without close new stitch:',unplaced)
