#!/usr/bin/env python3
"""A1 local regulator/crystal layout and internal 1.1V routing.
Explicit layout edit, not part of export. General routing must follow; inspect DRC.
"""
from pathlib import Path
import uuid,pcbnew as p
from circuit import C
H=Path(__file__).resolve().parent;b=p.LoadBoard(str(H/'quadcuber.kicad_pcb'))
def v(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def xy(a):return p.ToMM(a.x),p.ToMM(a.y)
fs={f.GetReference():f for f in b.GetFootprints()}
def pad(ref,num):return next(pa for pa in fs[ref].Pads() if pa.GetNumber()==str(num))
def route(net,pts,w=.3,ly=p.F_Cu):
 pts=[v(*a) if isinstance(a,tuple) else a for a in pts]
 for a,bb in zip(pts,pts[1:]):
  if a==bb:continue
  t=p.PCB_TRACK(b);t.SetStart(a);t.SetEnd(bb);t.SetWidth(p.FromMM(w));t.SetLayer(ly);t.SetNetCode(b.GetNetcodeFromNetname(net));t.SetLocked(True);b.Add(t)
def via(net,pos):
 t=p.PCB_VIA(b);t.SetPosition(v(*pos));t.SetWidth(p.F_Cu,p.FromMM(.6));t.SetDrill(p.FromMM(.3));t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetViaType(p.VIATYPE_THROUGH);t.SetNetCode(b.GetNetcodeFromNetname(net));t.SetLocked(True);b.Add(t)
# Remove paths that are intentionally redesigned; preserve all motor/buck routing.
for t in list(b.GetTracks()):
 if t.GetNetname() in ['1V1','XIN','XOUT','XOUT_DAMPED'] or (t.IsLocked() and t.GetNetname() in ['GND','3V3','VSYS'] and p.ToMM(t.GetStart().x)<90 and p.ToMM(t.GetStart().y)<90):b.Delete(t)
for c in C:
 if c['ref'] not in ['C1','C422','Y1','R409','C425','C426']:continue
 old=fs[c['ref']];oldpos=[pa.GetPosition() for pa in old.Pads()]
 for t in list(b.GetTracks()):
  if any((t.GetStart()-a).EuclideanNorm()<p.FromMM(.02) or (t.GetEnd()-a).EuclideanNorm()<p.FromMM(.02) for a in oldpos):b.Delete(t)
 path=p.KIID_PATH(old.GetPath());b.Delete(old)
 name=c['fp'].split(':')[-1];f=p.PCB_IO_KICAD_SEXPR().FootprintLoad(str(H/'lib/Quadcuber.pretty'),name)
 f.SetReference(c['ref']);f.SetValue(c['value']);f.SetFPID(p.LIB_ID('Quadcuber',name));f.SetPath(path);b.Add(f)
 f.SetPosition(v(c['xy'][0]+50,c['xy'][1]+50));f.SetOrientationDegrees(c['rot']);f.Value().SetVisible(False);f.Reference().SetVisible(False);f.Reference().SetLayer(p.F_Fab)
 for pa in f.Pads():
  net=c['pins'].get(pa.GetNumber())
  if net:pa.SetNetCode(b.GetNetcodeFromNetname(net))
 fs[c['ref']]=f
# Dedicated internal regulator branches. In2 is a power layer; In1 ground is untouched.
for pin,ref,pos in [(45,'C421',(72.3,72.0)),(50,'C419',(69.8,72.5625)),(23,'C418',(70.6,79.4375))]:
 via('1V1',pos);route('1V1',[pad('U1',pin).GetPosition(),*(([(71.8,72.9),(72.3,72.4)]) if pin==45 else []),pos],.15);route('1V1',[pos,pad(ref,1).GetPosition()],.25,p.B_Cu)
route('1V1',[(72.3,72.0),(71.7375,72.5625),(69.8,72.5625)],.3,p.In2_Cu)
route('1V1',[(69.8,72.5625),(70.8,72.5625),(71.1,72.8625),(71.1,74.7),(70.4,75.4),(70.4,78.5),(70.6,78.5),(70.6,79.4375)],.2,p.In2_Cu)
# Move IOVDD22 via inward to free the clock escape corridor.
old=v(70.2,81.4375)
for t in list(b.GetTracks()):
 if t.GetNetname()=='3V3' and any((a-old).EuclideanNorm()<p.FromMM(.01) for a in [t.GetStart(),t.GetEnd()]):b.Delete(t)
via('3V3',(69.7,79.4));route('3V3',[pad('U1',22).GetPosition(),(70.2,79.9),(69.7,79.4)],.15)
route('3V3',[(69.7,79.4),pad('C412',1).GetPosition()],.25,p.B_Cu)
for ly in [p.F_Cu,p.B_Cu]:route('3V3',[(73.4,73.7625),(73,73.5625)],.2,ly)
# Compact LDO loops and a direct plane connection at its output.
route('VSYS',[pad('C1',1).GetPosition(),pad('U5',1).GetPosition()],.35)
route('3V3',[pad('U5',5).GetPosition(),pad('C422',1).GetPosition()],.35)
via('3V3',(84,69.2));route('3V3',[pad('C422',1).GetPosition(),(84,69.2)],.35)
for ref,pos in [('C1',(75.4,70)),('C422',(86.7,69.2))]:
 via('GND',pos);route('GND',[pad(ref,2).GetPosition(),pos],.3)
# Crystal and its load capacitors, with no signal vias.
route('XIN',[pad('U1',20).GetPosition(),(69.4,82),(67.6,82),(67.6,84.4),(68.15,84.95),pad('Y1',1).GetPosition()],.15)
route('XIN',[pad('C425',1).GetPosition(),pad('Y1',1).GetPosition()],.15)
route('XOUT',[pad('U1',21).GetPosition(),(69.8,81.0),(70.5,81.7),(70.8,82.2),(72.8,82.2),pad('R409',1).GetPosition()],.15)
route('XOUT_DAMPED',[pad('R409',2).GetPosition(),(74.51,82.7),(72.72,82.7),pad('C426',1).GetPosition(),pad('Y1',3).GetPosition()],.15)

# Ground pin19 TESTEN, inward escape to EP ground copper.
route('GND',[pad('U1',19).GetPosition(),(69,79.15),(68.65,78.8),(68.65,78.35)],.15)
for z in b.Zones():
 z.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(H/'quadcuber.kicad_pcb'),b)
print('Local controller power and clock routed; inspect DRC before general reroute.')
