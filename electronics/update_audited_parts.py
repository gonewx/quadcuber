#!/usr/bin/env python3
"""Apply exact-part audit corrections, preserving all original traces and placement."""
from pathlib import Path
import json,csv,runpy
import pcbnew as p
replacements={'GRM32ER71E106KA12L': 'GRM32DR71E106KA12L', 'MF-MSMF110-2': 'MF-MSMF110/16X-2', 'GRM155R61A105KE15D': 'GRM155R61C105KA12D', 'GRM21BR61A475KA73L': 'C0805C475K4PACTU', 'GRM1885C1H750JA01D': 'C0603C750J5GACTU', '4.7u/10V': '4.7u/16V'}
H=Path(__file__).resolve().parent;O=H.parent/'generated/electronics';lib=H/'lib/Quadcuber.pretty'
def v(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
name='Fuse_Bourns_MF_MSMF_Style2_1812'
fp=p.PCB_IO_KICAD_SEXPR().FootprintLoad(str(lib),'Fuse_1812_4532Metric')
fp.SetFPID(p.LIB_ID('Quadcuber',name));fp.SetValue('MF-MSMF110/16X-2')
fp.SetLibDescription('Bourns MF-MSMF Style2:1.5x3.2mm pads,gap2.7mm. Text dimensions reconstructed; no claimed visual-arrow certification.')
for pad in fp.Pads():
 pad.SetPosition(v(-2.1 if pad.GetNumber()=='1' else 2.1,0));pad.SetSize(v(1.5,3.2));pad.SetShape(p.PAD_SHAPE_RECT)
p.PCB_IO_KICAD_SEXPR().FootprintSave(str(lib),fp)
b=p.LoadBoard(str(H/'quadcuber.kicad_pcb'))
for f in b.GetFootprints():
 for old,new in replacements.items():
  if f.GetValue()==old:f.SetValue(new)
 if f.GetReference() in ['F10','F11','F12','F13']:
  assert abs(f.GetOrientationDegrees())<.001
  f.SetFPID(p.LIB_ID('Quadcuber',name));f.SetLibDescription(fp.GetLibDescription())
  for pad in f.Pads():
   pad.SetPosition(f.GetPosition()+v(-2.1 if pad.GetNumber()=='1' else 2.1,0));pad.SetSize(v(1.5,3.2));pad.SetShape(p.PAD_SHAPE_RECT)
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(H/'quadcuber.kicad_pcb'),b)
# Native files carry exact ordering fields; changing words never regenerates the layout.
for path in [*H.glob('*.kicad_sch'),H/'lib/Quadcuber.kicad_sym']:
 s=path.read_text()
 for old,new in replacements.items():s=s.replace(old,new)
 # Correct manufacturer in each affected instantiated symbol, never globally.
 for ref in ['C25','C35','C422']:
  marker='(symbol(lib_id "Quadcuber:'+ref+'")'
  if marker in s:
   start=s.index(marker);level=0;quoted=False;escape=False
   for j in range(start,len(s)):
    ch=s[j]
    if escape:escape=False;continue
    if quoted and ch=='\\':escape=True;continue
    if ch=='"':quoted=not quoted;continue
    if not quoted:
     level+=(ch=='(')-(ch==')')
     if level==0:end=j+1;break
   s=s[:start]+s[start:end].replace('(property "Manufacturer" "Murata"','(property "Manufacturer" "KEMET"')+s[end:]
 # Generic 1812 is also F2/F3, so change only F10-13 symbols by their blocks.
 if path.name.startswith('arm_'):
  s=s.replace('Quadcuber:Fuse_1812_4532Metric','Quadcuber:'+name)
 elif path.name=='Quadcuber.kicad_sym':
  for ref in ['F10','F11','F12','F13']:
   start=s.index('(symbol "'+ref+'"');level=0;quoted=False;escape=False;end=None
   for j in range(start,len(s)):
    ch=s[j]
    if escape:escape=False;continue
    if quoted and ch=='\\':escape=True;continue
    if ch=='"':quoted=not quoted;continue
    if not quoted:
     level+=(ch=='(')-(ch==')')
     if level==0:end=j+1;break
   s=s[:start]+s[start:end].replace('Quadcuber:Fuse_1812_4532Metric','Quadcuber:'+name)+s[end:]
 path.write_text(s)
C=runpy.run_path(str(H/'circuit.py'))['C'];byref={x['ref']:x for x in C}
cs=json.loads((O/'circuit.json').read_text())
for c in cs:
 if c['ref'] in byref:
  c.update({k:byref[c['ref']][k] for k in ['value','mpn','note','mfr']})
  if c['ref'] in ['F10','F11','F12','F13']:c['fp']=byref[c['ref']]['fp'];c.pop('source_fp',None)
(O/'circuit.json').write_text(json.dumps(cs,indent=2,ensure_ascii=False)+'\n')
with (O/'bom.csv').open() as h:r=csv.DictReader(h);fields=r.fieldnames;rows=list(r)
for row in rows:
 c=byref[row['Reference']];row.update(Value=c['value'],MPN=c['mpn'],Manufacturer=c['mfr'],Notes=c['note'])
 if c['ref'] in ['F10','F11','F12','F13']:row['Footprint']=c['fp']
with (O/'bom.csv').open('w') as h:w=csv.DictWriter(h,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
print('Updated exact audited part fields and four PTC lands; original routing preserved')
