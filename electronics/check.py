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
# Independent RP2040 datasheet mapping: package pad number != GPIO number.
gpio_pads={**{i:i+2 for i in range(8)},**{i:i+3 for i in range(8,16)},**{i:i+11 for i in range(16,22)},24:36,25:37}
for gpio,pin in gpio_pads.items():check('U1',pin,f'GP{gpio}')
for pin in [1,10,22,33,42,43,44,48,49]:check('U1',pin,'3V3')
for pin in [23,45,50]:check('U1',pin,'1V1')
for pin in [19,57]:check('U1',pin,'GND')
for pin,net in {20:'XIN',21:'XOUT',24:'SWCLK',25:'SWDIO',26:'RUN',46:'USB_DM_MCU',47:'USB_DP_MCU',51:'QSPI_SD3',52:'QSPI_SCLK',53:'QSPI_SD0',54:'QSPI_SD2',55:'QSPI_SD1',56:'QSPI_SS'}.items():check('U1',pin,net)
for ref,pp in {
 'U7':{1:'QSPI_SS',2:'QSPI_SD1',3:'QSPI_SD2',4:'GND',5:'QSPI_SD0',6:'QSPI_SCLK',7:'QSPI_SD3',8:'3V3'},
 'U5':{1:'VSYS',2:'GND',3:'VSYS',5:'3V3'},
 'D2':{1:'VSYS',2:'5V_A'},'D5':{1:'VSYS',2:'USB_FUSED'},
 'F3':{1:'USB_VBUS',2:'USB_FUSED'},'U6':{1:'USB_DP',2:'GND',3:'USB_DM',4:'USB_DM',5:'VSYS',6:'USB_DP'},
 'R401':{1:'USB_CC1',2:'GND'},'R402':{1:'USB_CC2',2:'GND'},
 'R403':{1:'USB_DM',2:'USB_DM_MCU'},'R404':{1:'USB_DP',2:'USB_DP_MCU'},
 'R408':{1:'QSPI_SS',2:'BOOT_BUTTON'},'S1':{1:'BOOT_BUTTON',2:'GND'},
 'J4':{1:'3V3',2:'SWDIO',3:'GND',4:'SWCLK'},
 'J5':{'A5':'USB_CC1','B5':'USB_CC2','A6':'USB_DP','B6':'USB_DP','A7':'USB_DM','B7':'USB_DM','A4':'USB_VBUS','A9':'USB_VBUS','B4':'USB_VBUS','B9':'USB_VBUS','A1':'GND','A12':'GND','B1':'GND','B12':'GND','S1':'GND'}
}.items():
    for pin,net in pp.items():check(ref,pin,net)
for pin in [34,35,38,39,40,41]:
    if pads.get(('U1',str(pin)),'') and not pads[('U1',str(pin))].startswith('unconnected-'):errors.append(f'Unused U1 pad {pin} unexpectedly connected')
for key,net in xmlnets.items():
    if not key[0].startswith('#') and pads.get(key)!=net:errors.append(f'Netlist mismatch {key}: {net} vs {pads.get(key)}')
for key,net in pads.items():
    if net and not net.startswith('unconnected-') and key not in xmlnets:errors.append(f'PCB-only connected pad {key}')
# Independently verify supplied drawing geometry; electrical mapping remains explicit HOLD.
for idx in range(4):
    f=next(f for f in b.GetFootprints() if f.GetReference()==f'J{10+idx}')
    expected=[(2.55,-4.84),(1.53,-2.30),(.51,-4.84),(-.51,-2.30),(-1.53,-4.84),(-2.55,-2.30)]
    for num,(dx,dy) in enumerate(expected,1):
        pa=next(pa for pa in f.Pads() if pa.GetNumber()==str(num))
        local=pa.GetPosition()-f.GetPosition()
        if abs(p.ToMM(local.x)-dx)>.001 or abs(p.ToMM(local.y)-dy)>.001 or abs(p.ToMM(pa.GetDrillSize().x)-.79)>.001:
            errors.append(f'{f.GetReference()}.{num}: drawing geometry mismatch')
    mounts=[pa for pa in f.Pads() if not pa.GetNumber()]
    if len(mounts)!=2 or any(abs(p.ToMM(pa.GetDrillSize().x)-2.3)>.001 for pa in mounts):errors.append(f'{f.GetReference()}: locator geometry mismatch')
for t in b.GetTracks():
    if t.GetNetname().startswith('unconnected-'):errors.append('Copper routed on a schematic NC net')
# Polarity and architecture checks use raw pin data, independent of diagram labels.
for i in [2,3]:
    check(f'U{i}',1,'GND');check(f'U{i}',3,'VM')
    check(f'U{i}',2,f'B{i-1}_SW');check(f'L{i-1}',1,f'B{i-1}_SW')
# Inspect geometry / current routes without claiming simulation or thermal proof.
widths={}
for t in b.GetTracks():
    net=str(t.GetNetname());widths.setdefault(net,[]).append(round(p.ToMM(t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth()),3))
report={'contract_errors':errors,'connected_pad_count':len(xmlnets),'footprints':len(b.GetFootprints()),'tracks_and_vias':len(b.GetTracks()),'copper_layers':b.GetCopperLayerCount(),'outline_mm':[144,112],'minimum_trace_or_via_width_mm':{k:min(v) for k,v in widths.items()},'manufacturing_release':False,'not_verified':['EV3 MPN, pinmap/view, contact rating and full ear envelope (nominal holes follow user drawing)','Board prototype thermal and regenerative tests','Mechanical bracket and cable clearances']}
(O/'contract-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(f'Contract checks: {len(errors)} errors; {len(xmlnets)} connected symbol pins compared with PCB')
for e in errors:print(e)
sys.exit(bool(errors))
