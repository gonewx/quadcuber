"""Fixed-interface separation and full-roll bounds at sampled normal jaw openings."""
from pathlib import Path
import sys,json,math
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));import candidate as c
from base_stiffening import reinforce,REPLACED_PIN_IDS
from paths import OUTPUT
out=OUTPUT/'base-stiffening';base=c.retained_base_r4();final,new,cons=reinforce(c.m,base)
audit=json.loads((out/'geometry-check.json').read_text());hosts={r['id']:{h['host']for h in r['verified_hosts']}for r in audit['connections']}
old=[(f'B{i}',p)for i,p in []]
old=[(f'B{i:02d}',p)for i,p in enumerate(base,1)if i not in REPLACED_PIN_IDS]
old += [('support:'+p.note,p)for p in c.core_parts(40.8)]
old += [('arm:'+str(i),p)for i,p in enumerate(c.state_parts({})) if not p.head]
boxes=[(name,c.world(p).min((0,1)),c.world(p).max((0,1)))for name,p in old]
clashes=[]
for p in new:
 if p.name not in ['2780.dat','6558.dat']:continue
 t=c.world(p);lo,hi=t.min((0,1)),t.max((0,1))
 for name,a,b in boxes:
  if name in hosts[p.note]:continue
  if np.all(np.minimum(hi,b)-np.maximum(lo,a)>1e-7):clashes.append([p.note,name])
assert not clashes,clashes
maxrad=0;worst=None
for s in np.linspace(0,c.m.OPEN_S,101):
 for p in c.module(float(s)):
  if not p.head:continue
  t=c.world(p);r=float(np.linalg.norm(t[...,1:],axis=-1).max())
  if r>maxrad:maxrad=r;worst=dict(stroke_mm=float(s*.4),part=p.name,note=p.note)
# Rotation about the head X axis cannot increase a point's Y beyond its YZ radius.
# F/B use the same upward/downward Y axis, so this bound applies to all four arms.
min_added_y=min(float(c.world(p)[...,1].min())for p in new)
assert min_added_y>maxrad
r=dict(fixed_nonhost_new_pin_aabb_overlaps=clashes,normal_jaw_samples=101,jaw_interval_degrees=[math.degrees(c.m.CLAMP_BETA),25],head_roll_interval_degrees=[0,360],all_four_arms_same_Y_bound=True,max_head_YZ_radius_mm=maxrad,worst=worst,min_added_y_mm=min_added_y,head_to_all_added_vertical_bound_mm=min_added_y-maxrad,limits='Full rigid-head roll bound at101 sampled jaw openings; jaw interpolation, deformation, insertion force and whole-machine physical motion are not certified. Existing head/support geometry and motion are unchanged.')
(out/'integration-check.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
