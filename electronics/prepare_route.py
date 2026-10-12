#!/usr/bin/env python3
"""Export DSN from current PCB with a dedicated inner GND plane and explicit widths."""
from pathlib import Path
import re,sys,pcbnew as p
HERE=Path(__file__).resolve().parent
b=p.LoadBoard(str(HERE/'quadcuber.kicad_pcb'))
def vec(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
# One uninterrupted ground layer is a reserved reference plane, not a routing layer.
if not len(b.Zones()):
    z=p.ZONE(b);z.SetLayer(p.In1_Cu);z.SetNetCode(b.GetNetcodeFromNetname('GND'));z.SetLocalClearance(p.FromMM(.25));z.SetPadConnection(p.ZONE_CONNECTION_FULL);z.SetMinThickness(p.FromMM(.2));z.Outline().NewOutline()
    for x,y in [(50.4,50.4),(193.6,50.4),(193.6,161.6),(50.4,161.6)]:z.Outline().Append(int(p.FromMM(x)),int(p.FromMM(y)))
    b.Add(z)
    z=p.ZONE(b);z.SetLayer(p.In2_Cu);z.SetNetCode(b.GetNetcodeFromNetname('VM'));z.SetLocalClearance(p.FromMM(.25));z.SetPadConnection(p.ZONE_CONNECTION_FULL);z.SetMinThickness(p.FromMM(.2));z.Outline().NewOutline()
    for x,y in [(50.4,50.4),(193.6,50.4),(193.6,161.6),(50.4,161.6)]:z.Outline().Append(int(p.FromMM(x)),int(p.FromMM(y)))
    b.Add(z)
p.SaveBoard(str(HERE/'quadcuber.kicad_pcb'),b)
dest=Path(sys.argv[1] if len(sys.argv)>1 else '/tmp/eda/quadcuber.dsn')
p.ExportSpecctraDSN(b,str(dest));s=dest.read_text()
# Normalize all exported classes to explicit widths and via rules.
nets=[str(n.GetNetname()) for n in b.GetNetsByNetcode().values() if n.GetNetname()]
def klass(n):
    if n in ['VIN','VIN_FUSED','VM']:return 'PowerBus'
    if n=='GND':return 'Ground'
    if n in ['5V_A','5V_B','5V_ENC'] or n.endswith('_SERVO_5V') or n.endswith('_SW'):return 'PowerBranch'
    if re.fullmatch('[RLFB]_M[12]',n):return 'Motor'
    if re.match(r'^(GP|QSPI_|USB_|XIN|XOUT|1V1$|3V3$|RUN$|SWD|SWCLK$|BOOT_BUTTON$|LED_ANODE$)',n):return 'LogicFine'
    return 'Default'
# KiCad may export project classes as well as kicad_default. Remove every class
# before adding one authoritative assignment; duplicate classes override via rules.
spans=[]
for match in re.finditer(r'    \(class ',s):
    start=match.start();depth=0
    for i in range(start,len(s)):
        if s[i]=='(':depth+=1
        elif s[i]==')':
            depth-=1
            if depth==0:spans.append((start,i+1));break
assert spans,'No DSN network classes exported'
start=spans[0][0]
for aa,bb in reversed(spans):s=s[:aa]+s[bb:]
replacement=''
for name,w in [('Default',250),('LogicFine',150),('Motor',1000),('PowerBranch',1000),('PowerBus',1000),('Ground',300)]:
    ns=' '.join(n for n in nets if klass(n)==name)
    replacement+=f'    (class {name} {ns} (circuit (use_via "Via[0-3]_600:300_um"))(rule(width {w})(clearance {150 if name=='LogicFine' else 220})))\n'
s=s[:start]+replacement+s[start:]
assert len(re.findall(r"    \(class ",s))==6
# Layer is exclusively a plane; all signal/VM tracks remain on other layers.
s=s.replace('(layer In1.Cu\n      (type signal)','(layer In1.Cu\n      (type power)').replace('(layer In2.Cu\n      (type signal)','(layer In2.Cu\n      (type power)')
dest.write_text(s);print(dest)
