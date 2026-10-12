#!/usr/bin/env python3
"""Local GP8/GP9 clearance repair for wider, verified Style2 PTC lands."""
from pathlib import Path
import pcbnew as p
H=Path(__file__).resolve().parent;b=p.LoadBoard(str(H/'quadcuber.kicad_pcb'))
def v(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
changes={'GP8':{(81.5921,134.0):(81.2,134.0)},'GP9':{(114.276,134.0):(114.0,134.0),(114.276,140.134):(114.0,140.134)}}
count=0
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA) or t.GetNetname() not in changes:continue
 for getter,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
  pt=getter();xy=(round(p.ToMM(pt.x),4),round(p.ToMM(pt.y),4))
  if xy in changes[t.GetNetname()]:setter(v(*changes[t.GetNetname()][xy]));count+=1
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(H/'quadcuber.kicad_pcb'),b)
print('Moved',count,'local segment endpoints; no net changes')
