#!/usr/bin/env python3
"""Apply approved direct-bootstrap metadata locally; never regenerate PCB/layout.

Run after circuit.py is updated. Native block edits preserve unrelated sheets.
"""
from pathlib import Path
import csv,json,re,runpy,uuid
H=Path(__file__).resolve().parent;O=H.parent/'generated/electronics'
C={c['ref']:c for c in runpy.run_path(str(H/'circuit.py'))['C']}
REMOVED={'R20','R30'};FEEDBACK={'R21','R22','R31','R32'}
def uid(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,'https://github.com/gonewx/quadcuber/pcb/'+s))
def children(s):
    depth=0;quoted=False;escape=False;start=None
    for i,ch in enumerate(s):
        if escape:escape=False;continue
        if quoted and ch=='\\':escape=True;continue
        if ch=='"':quoted=not quoted;continue
        if quoted:continue
        if ch=='(':
            depth+=1
            if depth==2:start=i
        elif ch==')':
            if depth==2:yield start,i+1,s[start:i+1]
            depth-=1
    assert depth==0 and not quoted

def remove_library_symbols(s,prefix):
    for a,z,block in reversed(list(children(s))):
        if any(re.match(r'\(symbol\s+"'+prefix+ref+'"',block) for ref in REMOVED):s=s[:a]+s[z:]
    return s

for ch in (1,2):
    path=H/f'buck{ch}.kicad_sch';s=path.read_text();r='R20' if ch==1 else 'R30'
    obsolete={uid(r)}|{uid(r+n+k) for n in ('1','2') for k in ('wire','label')}
    for a,z,block in reversed(list(children(s))):
        if re.match(r'\(lib_symbols\b',block):
            block=remove_library_symbols(block,'Quadcuber:')
        elif any(re.search(r'\(uuid\s+"?'+u+r'"?\)',block) for u in obsolete):
            block=''
        elif re.match(r'\(symbol\s',block):
            ref=re.search(r'\(property\s+"Reference"\s+"([^"]+)"',block)
            if ref and ref[1] in FEEDBACK:
                block=re.sub(r'(\(property\s+"MPN"\s+)"[^"]+"',lambda m:m[1]+json.dumps(C[ref[1]]['mpn']),block)
        s=s[:a]+block+s[z:]
    s=s.replace(f'"B{ch}_BOOT_CAP"',f'"B{ch}_BOOT"')
    path.write_text("\n".join(line.rstrip() for line in s.splitlines())+"\n")
p=H/'lib/Quadcuber.kicad_sym';p.write_text(remove_library_symbols(p.read_text(),''))
p=O/'circuit.json';cs=json.loads(p.read_text());cs=[c for c in cs if c['ref'] not in REMOVED]
for c in cs:
    if c['ref'] in FEEDBACK|{'C22','C32'}:
        for key in ['value','mpn','pins','xy','rot']:c[key]=C[c['ref']][key]
p.write_text(json.dumps(cs,ensure_ascii=False,indent=2)+'\n')
p=O/'bom.csv'
with p.open() as f:r=csv.DictReader(f);fields=r.fieldnames;rows=list(r)
rows=[r for r in rows if r['Reference'] not in REMOVED]
for r in rows:
    if r['Reference'] in FEEDBACK:r['MPN']=C[r['Reference']]['mpn']
with p.open('w') as f:w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
print('Updated only buck sheets/library entries, buck source snapshot and BOM; PCB untouched.')
