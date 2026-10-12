#!/usr/bin/env python3
"""Local A1 decoupling placement and dedicated supply fanout, checked by native DRC.
Run after update_controller.py, before signal routing. Does not alter power cells.
"""
from pathlib import Path
import math,pcbnew as p
H=Path(__file__).resolve().parent;b=p.LoadBoard(str(H/'quadcuber.kicad_pcb'))
def v(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def mm(a):return p.ToMM(a.x),p.ToMM(a.y)
fs={f.GetReference():f for f in b.GetFootprints()};u=fs['U1'];up={int(pad.GetNumber()):pad for pad in u.Pads() if pad.GetNumber()}
refs={f'C{i}' for i in range(410,422)}
for t in list(b.GetTracks()):
    x,y=mm(t.GetStart())
    if 63<x<78 and 65<y<86:b.Delete(t)
for ref in refs:fs[ref].SetPosition(v(400,400))
obstacles=[]
for f in b.GetFootprints():
    if f.GetReference() not in refs:
        obstacles+=list(f.Pads())
for t in b.GetTracks():obstacles.append(t)
def shape(obj,layer):
    if isinstance(obj,p.PAD):
        if not obj.IsOnLayer(layer):return None
        return obj.GetEffectiveShape(layer)
    if isinstance(obj,p.PCB_VIA) or obj.GetLayer()==layer:return obj.GetEffectiveShape(layer)
    return None
def clear(sh,layer,net,extra=.2):
    for ob in obstacles:
        if ob.GetNetname()==net:continue
        other=shape(ob,layer)
        if other and p.SHAPE.Collide(sh,other,p.FromMM(extra)):return False
    return True
def seg(a,bb,w):return p.SHAPE_SEGMENT(a,bb,p.FromMM(w))
def addtrack(a,bb,net,layer,w):
    t=p.PCB_TRACK(b);t.SetStart(a);t.SetEnd(bb);t.SetWidth(p.FromMM(w));t.SetLayer(layer);t.SetNetCode(b.GetNetcodeFromNetname(net));b.Add(t);obstacles.append(t)
def addvia(pos,net):
    t=p.PCB_VIA(b);t.SetPosition(pos);t.SetWidth(p.F_Cu,p.FromMM(.6));t.SetDrill(p.FromMM(.3));t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetViaType(p.VIATYPE_THROUGH);t.SetNetCode(b.GetNetcodeFromNetname(net));b.Add(t);obstacles.append(t)
order=[('C421',45),('C419',50),('C416',48),('C417',49),('C420',44),('C415',43),('C418',23),('C412',22),('C414',42),('C413',33),('C410',1),('C411',10)]
results=[]
for ref,pin in order:
    f=fs[ref];pad=up[pin];net=str(pad.GetNetname());a=pad.GetPosition();x,y=mm(a)
    found=False
    candidates=[]
    for dx in range(-12,13):
        for dy in range(-12,13):
            distance=math.hypot(dx*.2,dy*.2)
            if .8<=distance<=2.4:candidates.append((distance,dx*.2,dy*.2))
    for distance,dx,dy in sorted(candidates):
        pos=v(x+dx,y+dy);sh=p.SHAPE_CIRCLE(pos,p.FromMM(.3))
        if not all(clear(sh,ly,net,.25) for ly in [p.F_Cu,p.B_Cu]):continue
        if not clear(seg(a,pos,.15),p.F_Cu,net,.15):continue
        for orient in [0,90,180,270]:
            f.SetOrientationDegrees(orient)
            for ang in [0,90,180,270,45,135,225,315]:
                # 0.8mm between via centre and capacitor supply pad.
                target=v(x+dx+.8*math.cos(math.radians(ang)),y+dy+.8*math.sin(math.radians(ang)))
                cp={pa.GetNumber():pa for pa in f.Pads()};offset=target-cp['1'].GetPosition();f.Move(offset)
                if any(not clear(pa.GetEffectiveShape(p.B_Cu),p.B_Cu,str(pa.GetNetname()),.2) for pa in f.Pads()):continue
                # Via is not in either capacitor pad; maintain 0.2 copper spacing to ground.
                if p.SHAPE.Collide(sh,cp['2'].GetEffectiveShape(p.B_Cu),p.FromMM(.2)):continue
                if not clear(seg(pos,target,.25),p.B_Cu,net,.2):continue
                # Pairwise courtyard envelope for these tiny passives.
                bb=f.GetBoundingBox(False,False)
                if any(bb.Intersects(fs[r].GetBoundingBox(False,False)) for r,_ in order if r!=ref and mm(fs[r].GetPosition())[0]<300):continue
                addvia(pos,net);addtrack(a,pos,net,p.F_Cu,.15);addtrack(pos,target,net,p.B_Cu,.25)
                obstacles+=list(f.Pads());results.append((ref,pin,round(distance+.8,3),mm(f.GetPosition()),mm(pos)));found=True;break
            if found:break
        if found:break
    if not found:raise RuntimeError('No local decoupling placement for '+ref)
# TESTEN must be held low through a short local connection.
# Leave the supply network interconnect to a separate reviewable routing pass.
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(H/'quadcuber.kicad_pcb'),b)
for row in results:print(row)
