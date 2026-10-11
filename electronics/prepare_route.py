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
# KiCad Python exporter does not load project netclass patterns, so export explicit rules.
nets=[str(n.GetNetname()) for n in b.GetNetsByNetcode().values() if n.GetNetname()]
def klass(n):
    if n in ['VIN','VIN_FUSED','VM']:return 'PowerBus'
    if n=='GND':return 'Ground'
    if n in ['5V_A','5V_B','5V_ENC'] or n.endswith('_SERVO_5V') or n.endswith('_SW'):return 'PowerBranch'
    if re.fullmatch('[RLFB]_M[12]',n):return 'Motor'
    return 'Default'
start=s.index('    (class kicad_default');depth=0;end=start
for i in range(start,len(s)):
    if s[i]=='(':depth+=1
    elif s[i]==')':
        depth-=1
        if depth==0:end=i+1;break
replacement=''
for name,w in [('Default',250),('Motor',1000),('PowerBranch',1000),('PowerBus',1000),('Ground',300)]:
    ns=' '.join(n for n in nets if klass(n)==name)
    replacement+=f'    (class {name} {ns} (circuit (use_via "Via[0-3]_600:300_um"))(rule(width {w})(clearance 220)))\n'
s=s[:start]+replacement+s[end:]
# Layer is exclusively a plane; all signal/VM tracks remain on other layers.
s=s.replace('(layer In1.Cu\n      (type signal)','(layer In1.Cu\n      (type power)').replace('(layer In2.Cu\n      (type signal)','(layer In2.Cu\n      (type power)')
dest.write_text(s);print(dest)
