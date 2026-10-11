#!/usr/bin/env python3
"""Independent net-contract checks; compare EDA-exported XML and physical PCB pads."""
import json,runpy,sys,xml.etree.ElementTree as ET
from pathlib import Path
import pcbnew as p
H=Path(__file__).resolve().parent;R=H.parent;O=R/'generated/electronics'
arms=runpy.run_path(str(R/'wiring/spec.py'))['ARMS']
tree=ET.parse(O/'netlist.xml'); xmlnets={}
for net in tree.findall('./nets/net'):
    if net.get('name','').startswith('unconnected-'):continue
    for node in net.findall('node'):xmlnets[(node.get('ref'),node.get('pin'))]=net.get('name')
b=p.LoadBoard(str(H/'quadcuber.kicad_pcb')); pads={}
for f in b.GetFootprints():
    for pad in f.Pads():
        if pad.GetNumber():pads[(f.GetReference(),pad.GetNumber())]=str(pad.GetNetname())
errors=[]
def check(ref,pin,net):
    for src,nets in [('schematic',xmlnets),('pcb',pads)]:
        if nets.get((ref,str(pin)))!=net:errors.append(f'{src} {ref}.{pin}: {nets.get((ref,str(pin)))} != {net}')
for i,(arm,(motor,enc,servo,sm)) in enumerate(arms.items()):
    for pin,net in {1:'GND',2:f'GP{motor[1]}',3:f'GP{motor[0]}',5:'VM',6:arm+'_M1',7:'GND',8:arm+'_M2',9:'GND'}.items():check(f'U{10+i}',pin,net)
    for pin,net in {1:arm+'_M1',2:arm+'_M2',3:'GND',4:'5V_ENC',5:arm+'_ENC_A_RAW',6:arm+'_ENC_B_RAW'}.items():check(f'J{10+i}',pin,net)
    check(f'U{20+i}',6,f'GP{enc[0]}');check(f'U{20+i}',4,f'GP{enc[1]}');check(f'U{20+i}',5,'3V3')
    check(f'U{30+i}',2,f'GP{servo[0]}');check(f'U{30+i}',5,arm+'_SERVO_5V')
    check(f'J{20+i}',1,'GND');check(f'J{20+i}',2,arm+'_SERVO_5V');check(f'J{20+i}',3,arm+'_SERVO_PWM')
check('U1',1,'GP0');check('U1',2,'GP1');check('U1',39,'VSYS');check('U1',36,'3V3');check('D2',1,'VSYS');check('D2',2,'5V_A')
assert pads.get(('U1','40'),'')=='','VBUS must not be connected'
for key,net in xmlnets.items():
    if not key[0].startswith('#') and pads.get(key)!=net:errors.append(f'Netlist mismatch {key}: {net} vs {pads.get(key)}')
for key,net in pads.items():
    if net and key not in xmlnets:errors.append(f'PCB-only connected pad {key}')
# Polarity and architecture checks use raw pin data, independent of diagram labels.
for i in [2,3]:
    check(f'U{i}',1,'GND');check(f'U{i}',3,'VM')
    check(f'U{i}',2,f'B{i-1}_SW');check(f'L{i-1}',1,f'B{i-1}_SW')
# Inspect geometry / current routes without claiming simulation or thermal proof.
widths={}
for t in b.GetTracks():
    net=str(t.GetNetname());widths.setdefault(net,[]).append(round(p.ToMM(t.GetWidth()),3))
report={'contract_errors':errors,'connected_pad_count':len(xmlnets),'footprints':len(b.GetFootprints()),'tracks_and_vias':len(b.GetTracks()),'copper_layers':b.GetCopperLayerCount(),'outline_mm':[144,112],'minimum_trace_or_via_width_mm':{k:min(v) for k,v in widths.items()},'manufacturing_release':False,'not_verified':['EV3 tail geometry and contact rating','Board prototype thermal and regenerative tests','Mechanical bracket and cable clearances']}
(O/'contract-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(f'Contract checks: {len(errors)} errors; {len(xmlnets)} connected symbol pins compared with PCB')
for e in errors:print(e)
sys.exit(bool(errors))
