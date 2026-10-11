#!/usr/bin/env python3
"""Place checked local power-plane fanouts and short front-layer switch-node connections.
Run only on the initial un-routed placement; DRC remains the final geometric check.
"""
import pcbnew as p,math,json
from pathlib import Path
H=Path(__file__).resolve().parent; b=p.LoadBoard(str(H/'quadcuber.kicad_pcb'))
def v(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def mm(pt):return (p.ToMM(pt.x),p.ToMM(pt.y))
pads=[pd for f in b.GetFootprints() for pd in f.Pads()]; shapes=[(pd.GetNetCode(),pd.GetEffectiveShape(p.F_Cu)) for pd in pads]
tracks=[]
def clear(shape,net):return not any(n!=net and p.SHAPE.Collide(ob,shape,p.FromMM(.225)) for n,ob in shapes+tracks)
def track(a,bb,net,width=.35):
    t=p.PCB_TRACK(b);t.SetStart(a);t.SetEnd(bb);t.SetWidth(p.FromMM(width));t.SetLayer(p.F_Cu);t.SetNetCode(net);t.SetLocked(True);b.Add(t);tracks.append((net,t.GetEffectiveShape(p.F_Cu)));return t
fmap={f.GetReference():f for f in b.GetFootprints()}
def pad(ref,num):return next(pp for pp in fmap[ref].Pads() if pp.GetNumber()==str(num))
for i in [1,2]:
    a=pad(f'U{i+1}',2);bb=pad(f'L{i}',1);sh=p.SHAPE_SEGMENT(a.GetPosition(),bb.GetPosition(),p.FromMM(.8))
    assert clear(sh,a.GetNetCode()),'SW node collision';track(a.GetPosition(),bb.GetPosition(),a.GetNetCode(),.8)
# Copper-plane fanout, not via-in-pad. Ground and VM are reserved inner planes.
placed=[];unplaced=[]
for pd in pads:
    if pd.GetAttribute()!=p.PAD_ATTRIB_SMD or pd.GetNetname() not in ('GND','VM'):continue
    if pd.GetNumber()=='9':continue # driver exposed pad already contains PTH thermal vias
    if pd.GetParentFootprint().GetReference()=='Q1':continue # high-current bank below
    pos=pd.GetPosition(); x,y=mm(pos); fx,fy=mm(pd.GetParentFootprint().GetPosition());angle=math.atan2(y-fy,x-fx)
    net=pd.GetNetCode(); ok=False
    for distance in [.9,1.2,1.5,1.8,2.1,2.5,3.0]:
        for off in [0,.35,-.35,.7,-.7,1.2,-1.2,math.pi]:
            xx=x+distance*math.cos(angle+off);yy=y+distance*math.sin(angle+off);end=v(xx,yy)
            circ=p.SHAPE_CIRCLE(end,p.FromMM(.4));seg=p.SHAPE_SEGMENT(pos,end,p.FromMM(.35))
            if 50.7<xx<193.3 and 50.7<yy<161.3 and clear(circ,net) and clear(seg,net):
                via=p.PCB_VIA(b);via.SetPosition(end);via.SetWidth(p.F_Cu,p.FromMM(.8));via.SetDrill(p.FromMM(.4));via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNetCode(net);via.SetLocked(True);b.Add(via)
                tracks.append((net,circ));track(pos,end,net,.35);placed.append([pd.GetParentFootprint().GetReference(),pd.GetNumber(),round(xx,3),round(yy,3)]);ok=True;break
        if ok:break
    if not ok:unplaced.append([pd.GetParentFootprint().GetReference(),pd.GetNumber()])
# Q1 drain high-current fanout: 12 x 0.4mm plated vias outside solder land.
q=pad('Q1',5);qpos=q.GetPosition();qx,qy=mm(qpos)
for xx in [122,123,124]:
    for yy in [60.5,61.5,62.5,63.5]:
        via=p.PCB_VIA(b);via.SetPosition(v(xx,yy));via.SetWidth(p.F_Cu,p.FromMM(.8));via.SetDrill(p.FromMM(.4));via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNetCode(q.GetNetCode());via.SetLocked(True);b.Add(via)
        track(qpos,v(xx,yy),q.GetNetCode(),.8)
p.ZONE_FILLER(b).Fill(b.Zones())
p.SaveBoard(str(H/'quadcuber.kicad_pcb'),b)
(H.parent/'generated/electronics/power-fanout.json').write_text(json.dumps({'fanouts':placed,'unplaced':unplaced},indent=2))
print('Power plane local fanouts:',len(placed),'unplaced:',unplaced)
