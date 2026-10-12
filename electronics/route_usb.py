#!/usr/bin/env python3
"""A1 USB2 manual topology. Run after controller placement, before general routing.
Main pair: 0.20mm tracks/0.20mm gap, F.Cu over uninterrupted In1 GND.
USB-C duplicate D- contacts cross via B.Cu locally, no vias on main ESD-to-MCU path.
"""
from pathlib import Path
import pcbnew as p
H=Path(__file__).resolve().parent;b=p.LoadBoard(str(H/'quadcuber.kicad_pcb'))
def v(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
names=['USB_DP','USB_DM','USB_DP_MCU','USB_DM_MCU']
for t in list(b.GetTracks()):
 if t.GetNetname() in names:b.Delete(t)
fs={f.GetReference():f for f in b.GetFootprints()}
for ref in ['R403','R404']:fs[ref].SetOrientationDegrees(270)
def route(net,pts,w=.2,ly=p.F_Cu):
 for a,bb in zip(pts,pts[1:]):
  t=p.PCB_TRACK(b);t.SetStart(v(*a));t.SetEnd(v(*bb));t.SetWidth(p.FromMM(w));t.SetLayer(ly);t.SetNetCode(b.GetNetcodeFromNetname(net));t.SetLocked(True);b.Add(t)
def via(net,x,y):
 t=p.PCB_VIA(b);t.SetPosition(v(x,y));t.SetWidth(p.F_Cu,p.FromMM(.6));t.SetDrill(p.FromMM(.3));t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetViaType(p.VIATYPE_THROUGH);t.SetNetCode(b.GetNetcodeFromNetname(net));t.SetLocked(True);b.Add(t)
# Connector mirror contacts: keep polarity exact; ground reference via below shell.
route('USB_DP',[(69.25,57.355),(69.25,59.3),(69.05,59.5),(69.05,63.1375)])
route('USB_DP',[(70.25,57.355),(70.25,58.3),(69.25,58.3)])
route('USB_DM',[(70.75,56.3),(70.75,59.3),(70.95,59.5),(70.95,63.1375)])
route('USB_DM',[(69.75,57.355),(69.75,56.3)])
via('USB_DM',69.75,56.3);via('USB_DM',70.75,56.3)
route('USB_DM',[(69.75,56.3),(70.75,56.3)],ly=p.B_Cu)
# Symmetric total ESD-to-resistor lengths despite SOT-23 breakout.
route('USB_DP',[(69.05,63.1375),(69.05,63.55),(70.1,64.6),(70.1,69.3),(70.4,69.6),(70.4,70.49)])
route('USB_DM',[(70.95,63.1375),(70.95,64.15),(70.5,64.6),(70.5,69.0),(71.4,69.9),(71.4,70.49)])
# Short 0.15mm QFN escapes around VREG_OUT via, series resistors adjacent to MCU.
route('USB_DP_MCU',[(70.4,71.51),(71,72.11),(71,73.3625),(71,73.5625)],.15)
route('USB_DM_MCU',[(71.4,71.51),(71.4,73.5625)],.15)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(H/'quadcuber.kicad_pcb'),b)
print('Manual USB pair complete; run DRC and inspect all layer returns.')
