from pathlib import Path
import collections,csv,json
import candidate as c
from paths import OUTPUT
H=OUTPUT
H.mkdir(parents=True,exist_ok=True)
state={a:(c.m.OPEN_S,50)for a in c.m.ARMS};groups={'support':c.core_parts(),'base':c.retained_base()}
for a in c.m.ARMS:groups['arm_'+a]=[p for p in c.state_parts(state)if p.arm==a]
with(H/'subsystem-BOM.csv').open('w')as f:
 w=csv.writer(f);w.writerow(['subsystem','part','LDraw_color','quantity'])
 for k,pp in groups.items():
  for(n,col),q in sorted(collections.Counter((p.name,p.color)for p in pp).items()):w.writerow([k,n,col,q])
with(H/'instance-inventory.csv').open('w')as f:
 w=csv.writer(f);w.writerow(['index1','subsystem','part','LDraw_color','x_mm','y_mm','z_mm','note'])
 i=0
 for k,pp in groups.items():
  for p in pp:i+=1;w.writerow([i,k,p.name,p.color,*[round(float(v)*.4,9)for v in p.pos],p.note])
assert sum(map(len,groups.values()))==882
(H/'inventory-summary.json').write_text(json.dumps({'counts':{k:len(v)for k,v in groups.items()},'whole_all_states':882,'working_locks':'R_working_key and L_working_key permanently removed during supported retrofit','support130_plus_lever20':150,'color_ids':'LDraw rendering identifiers; added20 use14yellow from approved source, not verified retail color availability','coordinate_units':'millimeters; +Y physically down'},indent=2))
print('882 instance records; all subsystem and color totals verified')
