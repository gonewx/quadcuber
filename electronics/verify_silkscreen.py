#!/usr/bin/env python3
"""Check actual visible silk and exact text-only delta from eb085ea. KiCad 10 Python."""
import json,re,subprocess,hashlib,sys
from pathlib import Path
import pcbnew as p
H=Path(__file__).resolve().parent;out=H.parent/'generated/electronics/silkscreen-revision';out.mkdir(exist_ok=True)
base=subprocess.check_output(['git','show','eb085ea:electronics/quadcuber.kicad_pcb'],cwd=H).decode()
new=(H/'quadcuber.kicad_pcb').read_text();b=p.LoadBoard(str(H/'quadcuber.kicad_pcb'))
blocks=lambda s:re.findall(r'\n\t\(gr_text\b.*?\n\t\)',s,re.S)
old=[s for s in blocks(base) if '(size 0.8 0.8)' in s and '(layer "F.SilkS")' in s]
expected=base
for s in old:expected=expected.replace(s,s.replace('(size 0.8 0.8)','(size 1 1)'))
small=[]
for f in b.GetFootprints():
 for t in [*f.GetFields(),*f.GraphicalItems()]:
  if isinstance(t,p.PCB_TEXT) and t.IsVisible() and t.GetLayer() in [p.F_SilkS,p.B_SilkS] and t.GetTextHeight()<1000000:small.append(t.GetText())
for t in b.GetDrawings():
 if isinstance(t,p.PCB_TEXT) and t.IsVisible() and t.GetLayer() in [p.F_SilkS,p.B_SilkS] and t.GetTextHeight()<1000000:small.append(t.GetText())
checks={'expected_52_original_labels':len(old)==52,'all_visible_silk_at_least_1mm':not small,'only_52_text_sizes_changed_all_other_bytes_identical':new==expected}
d={'pass':all(checks.values()),'checks':checks,'small_visible_text':small,'pcb_sha256':hashlib.sha256(new.encode()).hexdigest(),'baseline_commit':'eb085ea','scope':'Only 52 gr_text size fields .8 -> 1 mm; every other byte of PCB including hidden fields, nets, pads, copper, filled zones, orientation, positions and text unchanged.'}
label=sys.argv[1] if len(sys.argv)>1 else 'green';(out/f'{label}.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d,indent=2));sys.exit(0 if d['pass'] else 1)
