#!/usr/bin/env python3
"""Add parallel power fanouts and power/ground copper after signal routing.
Run once on the imported route; check native DRC after every run.
"""
from pathlib import Path
import math,json,pcbnew as p
H=Path(__file__).resolve().parent;b=p.LoadBoard(str(H/'quadcuber.kicad_pcb'))
def v(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def xy(pt):return p.ToMM(pt.x),p.ToMM(pt.y)
def net(n):return b.GetNetcodeFromNetname(n)
pads=[pd for f in b.GetFootprints() for pd in f.Pads()]
def clear(sh,n,layer):
    for pd in pads:
        if pd.IsOnLayer(layer) and pd.GetNetCode()!=n and p.SHAPE.Collide(pd.GetEffectiveShape(layer),sh,p.FromMM(.225)):return False
    for t in b.GetTracks():
        if t.IsOnLayer(layer) and t.GetNetCode()!=n and p.SHAPE.Collide(t.GetEffectiveShape(layer),sh,p.FromMM(.225)):return False
    return True
# Remove the redundant auto-router branch identified by native DRC.
for t in list(b.GetTracks()):
    if t.GetNetname()=='B2_SW' and not isinstance(t,p.PCB_VIA) and abs(p.ToMM(t.GetLength())-1.369)<.002 and abs(p.ToMM(t.GetStart().y)-88)<.001:b.Delete(t)
# Widen short original fanout tracks where pad clearance permits.
widened=0
for t in b.GetTracks():
    if isinstance(t,p.PCB_VIA) or not t.IsLocked() or t.GetNetname() not in ['VM','GND'] or t.GetWidth()>=p.FromMM(.6):continue
    for w in [.8,.65,.5]:
        sh=p.SHAPE_SEGMENT(t.GetStart(),t.GetEnd(),p.FromMM(w))
        if clear(sh,t.GetNetCode(),p.F_Cu):t.SetWidth(p.FromMM(w));widened+=1;break
# Parallel vias on power IC pins, outside the solder lands. All copper layers checked.
report=[]
for pd in pads:
    ref=pd.GetParentFootprint().GetReference();pn=pd.GetNumber()
    if not ((ref in ['U10','U11','U12','U13'] and pn in ['5','7']) or (ref in ['U2','U3'] and pn in ['1','3'])):continue
    x,y=xy(pd.GetPosition());n=pd.GetNetCode();added=0
    width=.6 if ref not in ['U2','U3'] else .45
    for rad in [1.4,1.8,2.2,2.7,3.2,3.8]:
        if added>=2:break
        for k in range(32):
            a=2*math.pi*k/32;end=v(x+rad*math.cos(a),y+rad*math.sin(a));circ=p.SHAPE_CIRCLE(end,p.FromMM(.4))
            if any((t.GetPosition()-end).EuclideanNorm()<p.FromMM(.85) for t in b.GetTracks() if isinstance(t,p.PCB_VIA)):continue
            if any(pd2.GetAttribute()!=p.PAD_ATTRIB_SMD and p.SHAPE.Collide(pd2.GetEffectiveShape(p.F_Cu),circ,p.FromMM(.25)) for pd2 in pads):continue
            if not all(clear(circ,n,l) for l in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]):continue
            seg=p.SHAPE_SEGMENT(pd.GetPosition(),end,p.FromMM(width))
            if not clear(seg,n,p.F_Cu):continue
            via=p.PCB_VIA(b);via.SetPosition(end);via.SetWidth(p.F_Cu,p.FromMM(.8));via.SetDrill(p.FromMM(.4));via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNetCode(n);b.Add(via)
            t=p.PCB_TRACK(b);t.SetStart(pd.GetPosition());t.SetEnd(end);t.SetWidth(p.FromMM(width));t.SetLayer(p.F_Cu);t.SetNetCode(n);b.Add(t)
            added+=1
            if added==2:break
    report.append({'ref':ref,'pin':pn,'parallel_vias_added':added,'neck_mm':width})
def zone(name,layer,pts,priority=0):
    z=p.ZONE(b);z.SetNetCode(net(name));z.SetLayer(layer);z.SetAssignedPriority(priority);z.SetLocalClearance(p.FromMM(.25));z.SetMinThickness(p.FromMM(.2));z.SetPadConnection(p.ZONE_CONNECTION_FULL);z.Outline().NewOutline()
    for x,y in pts:z.Outline().Append(p.FromMM(x),p.FromMM(y))
    b.Add(z)
rect=[(50.4,50.4),(193.6,50.4),(193.6,161.6),(50.4,161.6)]
zone('GND',p.F_Cu,rect);zone('GND',p.B_Cu,rect)
zone('VIN',p.F_Cu,[(93.3,56),(96.7,56),(96.7,61),(104.5,61),(104.5,57.8),(106.6,57.8),(106.6,64.5),(93.3,64.5)],10)
zone('VIN_FUSED',p.F_Cu,[(107.4,57.5),(111.5,57.5),(115,60.5),(115,64.1),(111.5,64.1),(107.4,60.3)],10)
zone('VM',p.F_Cu,[(115.5,60),(125,60),(125,66),(115.5,66)],10)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(H/'quadcuber.kicad_pcb'),b)
(H.parent/'generated/electronics/power-copper.json').write_text(json.dumps({'widened_short_fanouts':widened,'power_pin_fanouts':report},indent=2)+'\n')
print('Widened:',widened,'power pins:',report)
