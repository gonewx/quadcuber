#!/usr/bin/env python3
"""Place the A1 controller while preserving routed motor/power cells.
Destructive layout operation: run only when intentionally restarting controller routing.
The checked-in .kicad_pcb remains the authoritative final layout.
"""
from pathlib import Path
import uuid,pcbnew as p
from circuit import C
H=Path(__file__).resolve().parent
b=p.LoadBoard(str(H/'quadcuber.kicad_pcb'))
def v(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def uid(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,'https://github.com/gonewx/quadcuber/pcb/'+s))
new=[c for c in C if c['section'] in ['controller_power','usb','flash_clock'] or c['ref'] in ['U1','J4','R400','S2','C400','R405','R406','D7','R410']]
refs={c['ref'] for c in new}
for t in list(b.GetTracks()):
    bb=t.GetBoundingBox();lo=bb.GetPosition();hi=bb.GetEnd()
    if lo.x<p.FromMM(90) and hi.x>p.FromMM(50) and lo.y<p.FromMM(111) and hi.y>p.FromMM(50):b.Delete(t)
for f in list(b.GetFootprints()):
    if f.GetReference() in refs:b.Delete(f)
for z in list(b.Zones()):
    if z.GetLayer()==p.In2_Cu and z.GetNetname()=='3V3':b.Delete(z)
nets={str(n.GetNetname()):n for n in b.GetNetsByNetcode().values()}
for c in C:
    for n in c['pins'].values():
        if n and n not in nets:
            ni=p.NETINFO_ITEM(b,n);b.Add(ni);nets[n]=ni
locs={'C410':(15,24.4),'C411':(15,28),'C412':(19.2,33),'C413':(25,28),'C414':(25,24.4),'C415':(26,20),'C416':(21,17),'C417':(18.8,19),'C418':(22.5,32),'C419':(16.5,19),'C420':(24,18),'C421':(23,21)}
for c in new:
    name=c['fp'].split(':')[-1];f=p.PCB_IO_KICAD_SEXPR().FootprintLoad(str(H/'lib/Quadcuber.pretty'),name)
    f.SetReference(c['ref']);f.SetValue(c['value']);f.SetFPID(p.LIB_ID('Quadcuber',name));f.SetPath(p.KIID_PATH('/'+uid('root')+'/'+uid('sheet-'+c['section'])+'/'+uid(c['ref'])))
    x,y=locs.get(c['ref'],c['xy']);f.SetPosition(v(x+50,y+50));f.SetOrientationDegrees(c['rot'])
    b.Add(f)
    if c.get('side')=='B.Cu':f.Flip(f.GetPosition(),False)
    f.Value().SetVisible(False);f.Reference().SetVisible(False);f.Reference().SetLayer(p.B_Fab if c.get('side')=='B.Cu' else p.F_Fab)
    f.Reference().SetTextSize(v(.8,.8));f.Reference().SetTextThickness(p.FromMM(.12))
    for pad in f.Pads():
        n=c['pins'].get(pad.GetNumber())
        if n:pad.SetNet(nets[n])

# Replace motor plane beneath logic island; In1 GND remains uninterrupted.
z=p.ZONE(b);z.SetLayer(p.In2_Cu);z.SetNet(nets['3V3']);z.SetAssignedPriority(20);z.SetLocalClearance(p.FromMM(.25));z.SetMinThickness(p.FromMM(.15));z.SetPadConnection(p.ZONE_CONNECTION_FULL);z.Outline().NewOutline()
for x,y in [(50.4,50.4),(89,50.4),(89,110),(50.4,110)]:z.Outline().Append(int(p.FromMM(x)),int(p.FromMM(y)))
b.Add(z)
# Decoupling ground/3V3 vias, each adjacent to its capacitor; 1V1 remains an isolated routed net.
def track(a,bb,net,layer=p.B_Cu,w=.2):
    t=p.PCB_TRACK(b);t.SetStart(a);t.SetEnd(bb);t.SetLayer(layer);t.SetWidth(p.FromMM(w));t.SetNet(nets[net]);b.Add(t)
def via(pos,net):
    t=p.PCB_VIA(b);t.SetPosition(pos);t.SetWidth(p.F_Cu,p.FromMM(.6));t.SetDrill(p.FromMM(.3));t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetViaType(p.VIATYPE_THROUGH);t.SetNet(nets[net]);b.Add(t)
for f in b.GetFootprints():
    if f.GetReference() in locs:
        for pad in f.Pads():
            if pad.GetNetname() in ['GND','3V3']:
                pos=pad.GetPosition();dst=v(p.ToMM(pos.x),p.ToMM(pos.y)+(.8 if pad.GetNumber()=='2' else -.8))
                via(dst,pad.GetNetname());track(pos,dst,pad.GetNetname())
for t in b.GetDrawings():
    if isinstance(t,p.PCB_TEXT):
        t.SetText(t.GetText().replace('A0','A1').replace('PICO ONLY','LOGIC ONLY').replace('RP2040 ONLY','LOGIC ONLY'))
for t in b.GetDrawings():
    if isinstance(t,p.PCB_TEXT) and '9V ONLY' in t.GetText():t.SetTextSize(v(.9,.9))
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(H/'quadcuber.kicad_pcb'),b)
print('Placed A1 controller; regenerate routes before release checks.')
