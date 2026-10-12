#!/usr/bin/env python3
"""Cross-check direct-bootstrap source, exported native netlist, and assembly BOM."""
import csv,hashlib,json,runpy,xml.etree.ElementTree as ET
from pathlib import Path
H=Path(__file__).resolve().parent;O=H.parent/'generated/electronics'
C={p['ref']:p for p in runpy.run_path(str(H/'circuit.py'))['C']}
J={p['ref']:p for p in json.loads((O/'circuit.json').read_text())}
with (O/'bom.csv').open() as f:B={p['Reference']:p for p in csv.DictReader(f)}
T=ET.parse(O/'netlist.xml');S={p.get('ref'):p for p in T.findall('./components/comp')}
N={(p.get('ref'),p.get('pin')):n.get('name') for n in T.findall('./nets/net') for p in n.findall('node')}
for refs in (C,J,B,S):assert not {'R20','R30'}&refs.keys()
assert not any(n.endswith('_BOOT_CAP') for n in N.values())
for ch,cap,top,bot in [(1,'C22','R21','R22'),(2,'C32','R31','R32')]:
    for ref,pins in [(cap,{'1':f'B{ch}_BOOT','2':f'B{ch}_SW'}),(f'U{ch+1}',{'6':f'B{ch}_BOOT','2':f'B{ch}_SW'})]:
        for pin,net in pins.items():assert C[ref]['pins'][pin]==J[ref]['pins'][pin]==N[(ref,pin)]==net,(ref,pin)
    for ref,value,mpn in [(top,'100k','RT0603BRD07100KL'),(bot,'13.3k','RT0603BRD0713K3L')]:
        assert C[ref]['value']==J[ref]['value']==B[ref]['Value']==S[ref].findtext('value')==value
        assert C[ref]['mpn']==J[ref]['mpn']==B[ref]['MPN']==S[ref].findtext('./fields/field[@name="MPN"]')==mpn
        assert B[ref]['Quantity']=='1'
        assert 'R_0603_1608Metric' in B[ref]['Footprint']
report={'state':'PASS','scope':'Source + generated circuit JSON + assembly BOM + KiCad-exported netlist; geometry/ERC/DRC separate',
        'removed':['R20','R30'],'feedback':{r:{k:C[r][k] for k in ['value','mpn']} for r in ['R21','R22','R31','R32']},
        'hashes':{str(p.relative_to(H.parent)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [H/'circuit.py',H/'quadcuber.kicad_pcb',O/'bom.csv',O/'netlist.xml']}}
(O/'boot-direct-revision').mkdir(exist_ok=True)
(O/'boot-direct-revision/cross-check.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
