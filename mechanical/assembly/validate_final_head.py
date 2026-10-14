from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import MECHANICAL, ASSEMBLY, MANUAL_OUTPUT
"""Read-only final-head coverage/geometry validation; writes one audit report."""
from pathlib import Path
import collections, hashlib, json, sys
import numpy as np
H=MANUAL_OUTPUT
sys.path.insert(0,str(MECHANICAL));import candidate as C
b=json.loads((ASSEMBLY/'final-head-steps.json').read_text());p=C.module(0,0,False,True)
core=set(b['prerequisites']['prebuilt_core_part_ids']);defer=set(b['prerequisites']['deferred_interface_part_ids'])
added=[i for s in b['steps'] for i in s['added_part_ids']]
checks={}
def check(name,condition):
 checks[name]=bool(condition)
 assert condition,name
check('zero_prebuilt_inputs',len(core)==0 and len(b['prerequisites']['prebuilt_input_groups'])==0)
check('added167_once',len(added)==167 and len(set(added))==167)
check('deferred81_84',defer=={81,84})
check('disjoint_exact_final169',not(core&set(added) or core&defer or set(added)&defer) and core|set(added)|defer==set(range(1,170)))
check('four_arms676',4*len(p)==676)
check('source_sha_matches',hashlib.sha256((MECHANICAL/'candidate.py').read_bytes()).hexdigest()==b['source']['model_sha256'])
check('rows_exact169',len(b['rows'])==169)
for r,q in zip(b['rows'],p):
 check(f'row_{r["index1"]}_matches_frozen_geometry',r['name']==q.name and r['color']==q.color and np.allclose(r['position_ldu'],q.pos,rtol=0,atol=1e-12) and np.allclose(r['rotation'],q.rot,rtol=0,atol=1e-12))
introduced=set(core)
for s in b['steps']:
 introduced.update(s['added_part_ids']);vis=s['visible_part_ids']
 check(s['id']+'_no_future_instances',set(vis)<=introduced)
 check(s['id']+'_snapshot_ids_match',vis==[r['index1'] for r in s['geometry_records']])
 check(s['id']+'_cumulative_exact',introduced==set(s['introduced_part_ids']))
 check(s['id']+'_no_deferred_interface_parts',not(set(vis)&defer))
 for r in s['geometry_records']:check(s['id']+f'_instance_{r["index1"]}_exact',r==b['rows'][r['index1']-1])
check('final_visible167',set(b['steps'][-1]['visible_part_ids'])==set(range(1,170))-defer)
check('tyre90_locked_wheels',sum(p[i-1].name=='59895.dat' for i in introduced)==2 and sum(p[i-1].name=='10197.dat' for i in introduced)==2)
check('four60483_final',sum(p[i-1].name=='60483.dat' for i in introduced)==4)
check('two_root_axles_final',sum(p[i-1].name=='3707.dat' for i in introduced)==2)
check('core_crank_initially_open',not({94,95}&core))
check('pushrod_before_crank_closure',next(s['number'] for s in b['steps'] if 163 in s['added_part_ids'])<next(s['number'] for s in b['steps'] if 94 in s['added_part_ids']))
check('jaw_pins_before_links',max(s['number'] for s in b['steps'] if set(s['added_part_ids'])&{160,162})<min(s['number'] for s in b['steps'] if set(s['added_part_ids'])&{159,161}))
check('crosshead_after_independent_links',max(s['number'] for s in b['steps'] if set(s['added_part_ids'])&{159,161})<next(s['number'] for s in b['steps'] if 155 in s['added_part_ids']))
check('zero_nominal_root_axial_reserve',all(s['nominal_axial_reserve_mm']==0 and sum(s['root_stack_mm'])==64 for s in b['steps'] if 'root_stack_mm' in s))
missing=[s['image'] for s in b['steps'] if not(H/s['image']).exists()]
check('all_images_exist',not missing)
render_audit={r['step_id']:r for r in json.loads((H/'final-head-render-audit.json').read_text())}
for step in b['steps']:
 a=render_audit[step['id']]
 check(step['id']+'_rendered_ids_match',a['rendered_instance_indices1']==step['visible_part_ids'])
 check(step['id']+'_image_hash_match',a['sha256']==hashlib.sha256((H/step['image']).read_bytes()).hexdigest())
complete_image=H/b['steps'][-1]['image']
check('complete_image_is_last_staged167',complete_image==H/'final-head-diagrams/34.png' and render_audit[b['steps'][-1]['id']]['sha256']==hashlib.sha256(complete_image.read_bytes()).hexdigest())
# Older rerenders may emit this redundant alias; the frozen delivery does not contain it.
if (H/'final-head-diagrams/complete.png').exists():
 check('complete_alias_equals_staged167',(H/'final-head-diagrams/complete.png').read_bytes()==complete_image.read_bytes())
opening=json.loads((H/'final-head-opening-audit.json').read_text())
check('opening_image_hash_matches',opening['sha256']==hashlib.sha256((H/opening['image']).read_bytes()).hexdigest())
report=dict(result='PASS',assertion_count=len(checks),mechanical_geometry_changed=True,prebuilt0_added167_deferred2=True,local_steps=len(b['steps']),missing_images=missing,physical_validation=False,continuous_insertion_validation=False,checks=checks)
(H/'final-head-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False))
