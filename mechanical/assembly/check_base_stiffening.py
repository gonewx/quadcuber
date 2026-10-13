"""Independent native-hole and interference checks for the integrated lower frame."""
import sys,json,math
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));import candidate as c
from base_stiffening import reinforce,REPLACED_PIN_IDS
from paths import OUTPUT
OUT=OUTPUT/'base-stiffening';OUT.mkdir(parents=True,exist_ok=True)
base=c.retained_base_r4();final,new,connections=reinforce(c.m,base);removed=REPLACED_PIN_IDS
assert [p.ldraw() for p in final]==[p.ldraw() for p in c.retained_base()]
# Pull nominal round-hole ports from native primitives, not guessed pitch alone.
def ports(name,R=np.eye(3),v=np.zeros(3)):
 out=[]
 for line in c.files[c.resolve(name)]:
  s=line.split()
  if s and s[0]=='1':
   a=np.array(s[2:14],float);r=a[3:].reshape(3,3);p=a[:3];n=' '.join(s[14:]);rr=R@r;vv=R@p+v
   if n=='peghole.dat':
    axis=rr@np.array([0.,1.,0.]);axis=axis/np.linalg.norm(axis);out.append((vv*.4+axis*4,axis))
   elif n in ['beamhole.dat','connhole.dat']:
    axis=rr@np.array([0.,1.,0.]);out.append((vv*.4,axis/np.linalg.norm(axis)))
   elif n in c.files or 's/' in n.replace('\\','/'):
    out+=ports(n,rr,vv)
 return out
hosts={f'B{i}':p for i,p in []}
hosts={f'B{i:02d}':p for i,p in enumerate(base,1) if p.name not in ['2780.dat','6558.dat']}
hosts.update({p.note:p for p in new if p.name not in ['2780.dat','6558.dat']})
worldports={k:[(p.rot@v+p.pos*.4,p.rot@a) for v,a in ports(p.name)] for k,p in hosts.items()}
pins={p.note:p for p in new if p.name in ['2780.dat','6558.dat']}
for con in connections:
 p=pins[con['id']]
 local=[[-4,0,0],[12,0,0],[-12,0,0]] if p.name=='6558.dat' else [[0,0,0],[8,0,0],[-8,0,0]]
 actual=[p.rot@np.array(v)+p.pos*.4 for v in local]
 x,z=con['xz_mm'];collar=con['collar_y_mm']
 expected=[[x,collar,z],[x,con['long_end_interval_y_mm'][0],z],[x,con['short_end_interval_y_mm'][1],z]]
 assert np.allclose(actual,expected,atol=1e-8),(con['id'],actual,expected)
 assert np.allclose(p.rot@np.array([1,0,0]),[0,-1,0]),con['id']
 con['actual_pin_shoulder_and_endpoints_mm']=[v.tolist() for v in actual]
 x,z=con['xz_mm'];ys=con['long_end_interval_y_mm']+con['short_end_interval_y_mm'];ymin,ymax=min(ys),max(ys)
 hits=[]
 for k,ps in worldports.items():
  for v,a in ps:
   if abs(abs(a[1])-1)<1e-6 and np.linalg.norm(v[[0,2]]-[x,z])<1e-6 and ymin+3.999<v[1]<ymax-3.999:hits.append({'host':k,'hole_center_mm':v.tolist()})
 hits=list({(h['host'],tuple(round(x,6) for x in h['hole_center_mm'])):h for h in hits}.values())
 con['verified_hosts']=hits
 assert len(hits)==(2 if con['id'].startswith('REUSED') else 3),(con,hits)
 if con['host_ids']:assert set(con['host_ids'])=={h['host'] for h in hits}
# Existing retained pins must not occupy new hole segments; removed corner pins are excluded.
allold=c.core_parts(40.8)+base+c.state_parts({a:(0,0) for a in c.m.ARMS})
oldpinclashes=[]
for p in new:
 if p.name not in ['2780.dat','6558.dat']:continue
 v=c.world(p).reshape(-1,3);lo,hi=v.min(0),v.max(0)
 for j,q in enumerate(allold):
  if q.name not in ['2780.dat','6558.dat']:continue
  # Object identity of removed entries from base survives in allold list.
  if any(q is base[i-1] for i in removed):continue
  w=c.world(q).reshape(-1,3);a,b=w.min(0),w.max(0)
  if np.all(np.minimum(hi,b)-np.maximum(lo,a)>.001):oldpinclashes.append([p.note,j,q.name])
assert not oldpinclashes,oldpinclashes
# Full existing solid parts never extend below116mm in nominal working states; added solids start116.
new_solids=[p for p in new if p.name not in ['2780.dat','6558.dat']]
assert min(c.world(p)[...,1].min() for p in new_solids)>=116-1e-8
new_overlaps=[]
for i,p in enumerate(new_solids):
 v=c.world(p).reshape(-1,3);lo,hi=v.min(0),v.max(0)
 for q in new_solids[i+1:]:
  w=c.world(q).reshape(-1,3);a,b=w.min(0),w.max(0)
  if np.all(np.minimum(hi,b)-np.maximum(lo,a)>.001):new_overlaps.append([p.note,q.note])
assert not new_overlaps,new_overlaps
moving=[];handles=[]
for d in np.linspace(0,40.8,409):
 for p in c.core_parts(float(d),lever_parameter_mm=float(d)*42.4/40.8):
  if p.note=='outer_handle':handles.append((float(d),float(c.world(p)[...,1].max())))
  if p.note in {r['id'] for r in c.rows if r['role']=='moving'}:moving.append(float(c.world(p)[...,1].max()))
# Lever extreme follows its endpoint angles, so maxY across all mesh vertices occurs at ends or stationary point.
R0=np.array([112.,80.,0.]);basep=c.lever_parts(0)
maxlever=0
for par in np.linspace(0,42.4,425):
 maxlever=max(maxlever,max(float(c.world(p)[...,1].max()) for p in c.lever_parts(float(par))))
from collections import Counter
report={'status':'GEOMETRY_VERIFIED_NOT_PHYSICALLY_VALIDATED','baseline_main_commit':'d6bda1d7c7be800161ae366a072e22fdf10a1728','added_instances':len(new),'remove_original_pins':removed,'net_instance_increase':len(new)-len(removed),'new_assembly_bom':dict(Counter(p.name for p in new)),'reuse_2780_from_removed':8,'connections':connections,'new_solid_aabb_overlap_pairs':new_overlaps,'new_pin_old_pin_aabb_overlap_pairs':oldpinclashes,'tray_max_y_mm_sampled':max(moving),'lever_max_y_mm_sampled':maxlever,'outer_handle_max_y_mm_sampled':max(y for d,y in handles),'clearance_to_new_solids_y116_mm':116-maxlever,'clearance_to_old_table_y116_mm':116-max(y for d,y in handles),'clearance_to_new_table_y140_mm':140-max(y for d,y in handles),'samples':{'tray':409,'lever':425},'limits':'Native faceted geometry and primitive hole centers. Axial engagement verified; insertion force, continuous whole-machine motion, real pin friction, deflection, tolerances, stiffness, stability and tipping not certified. Four feet need non-rocking contact; not self-leveling.'}
report['parts']=[{'id':p.note,'name':p.name,'position_mm':(p.pos*.4).tolist(),'rotation':p.rot.tolist(),'bbox_mm':[c.world(p).reshape(-1,3).min(0).tolist(),c.world(p).reshape(-1,3).max(0).tolist()]} for p in new]
(OUT/'geometry-check.json').write_text(json.dumps(report,indent=2,default=lambda x:x.item()))
print(json.dumps({k:v for k,v in report.items() if k not in ['connections','parts']},indent=2))
# Geometry preview is a separate proposal, not a standard deliverable/model replacement.
lines=['0 Independent base reinforcement proposal; NOT stiffness validated','0 Name: base-reinforcement-proposal.ldr']
for p in [q for i,q in enumerate(base,1) if i not in removed]+new:
 vals=[*p.pos,*p.rot.reshape(-1)];lines.append('1 '+str(p.color)+' '+' '.join(f'{v:.8g}' for v in vals)+' '+p.name)
(OUT/'proposal-base.ldr').write_text('\n'.join(lines)+'\n')
