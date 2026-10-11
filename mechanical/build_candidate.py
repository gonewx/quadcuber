from candidate import *
import json,hashlib,collections
from paths import OUTPUT, INPUTS
OUTPUT.mkdir(parents=True, exist_ok=True)
OUT=OUTPUT/'models';OUT.mkdir(exist_ok=True)
# rows provided by integrated candidate
baselines=(INPUTS/'baseline-machine-899.mpd').read_text().split('\n0 FILE ',1)[0]
base=retained_base()
assert len(base)==64
# Preserve v27 subfile order independently of filesystem directory iteration.
asset_order=json.loads((INPUTS/'asset-order.json').read_text())
assert set(asset_order)==set(files)-{'machine_working-899.ldr'}
assets='\n'.join('0 FILE '+name+'\n'+'\n'.join(files[name])for name in asset_order)+'\n'
states={
 'loading-all50':(50,50,True,True,0,False),
 'FB0-open':(50,0,True,True,0,False),
 'FB0-held':(50,0,True,False,0,False),
 'support-held':(50,0,True,False,0,False),
 'support-down40_8':(50,0,True,False,40.8,False),
 'LR90-open':(90,0,True,False,40.8,False),
 'both-held':(90,0,False,False,40.8,False)}
manifest={}
def export(name,parts):
 text='0 FILE '+name+'.ldr\n0 INTEGRATED GRAVITY R4 - NO PHYSICAL OR POWERED ACCEPTANCE\n'+'\n'.join(p.ldraw()for p in parts)+'\n'+assets
 path=OUT/(name+'.mpd');path.write_text(text);return {'file':str(path.relative_to(OUTPUT)),'parts':len(parts),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
for key,(lr,fb,lo,fo,drop,locks) in states.items():
 state={k:(m.OPEN_S if(lo if k in'LR'else fo)else 0,lr if k in'LR'else fb)for k in m.ARMS}
 head=state_parts(state);old=state_parts(state,False);retained=[p for i,p in enumerate(old) if i%177 not in [48,49] and not(p.note in ['开限位挡轴','开限位挡轴轴套']or(p.name=='32056.dat'and p.note=='限位支架'))]
 assert collections.Counter(p.ldraw()for p in retained)==collections.Counter(p.ldraw()for i,p in enumerate(head) if p.name!='60483.dat' and i%167 not in [48,49])
 core=core_parts(drop,False)
 allp=core+base+head;manifest[key]=export(key,allp);manifest[key].update(drop_mm=drop,locks=False,lever_parameter_mm=0 if drop==0 else drop+1.6,heads={k:[float(v[0]),v[1]]for k,v in state.items()},unchanged_retained_parts=len(retained),retained_parts_including_corrected_wallpins=len(retained)+8,corrected_retained_wallpins=8,removed=dict(collections.Counter(p.name for p in old)-collections.Counter(p.name for p in head)),added=dict(collections.Counter(p.name for p in head)-collections.Counter(p.name for p in old)))
 assert len(head)==668 and len(allp)==882
manifest['head-open25']=export('head-open25',module(m.OPEN_S))
manifest['head-closed']=export('head-closed',module(0))
(OUTPUT/'candidate-manifest.json').write_text(json.dumps(manifest,indent=2))
checks={'baseline_source_matches_frozen_github_snapshot':hashlib.sha256((INPUTS/'baseline_model.py').read_bytes()).hexdigest()=='ed1b9d8d71aed8f34e93dce32fcb35a33a16203360bfdbd1064282600c72d7fc','source_url':'https://github.com/gonewx/quadcuber/blob/main/tools/lego/v4/model.py','source_sha256':hashlib.sha256((INPUTS/'baseline_model.py').read_bytes()).hexdigest(),'assembly132_sha256':hashlib.sha256((INPUTS/'assembly132.json').read_bytes()).hexdigest(),'baseline_mpd_sha256':hashlib.sha256((INPUTS/'baseline-machine-899.mpd').read_bytes()).hexdigest(),'normal_open_deg':math.degrees(m.OPEN_BETA),'normal_open_stroke_mm':m.OPEN_S*.4,'natural_stroke_mm':natural_stroke()*.4,'natural_jaw_deg':math.degrees(m.jaw_beta(natural_stroke())),'preserved_retained_per_head':163,'unchanged_retained_per_head':161,'corrected_retained_wallpins_per_head':2,'removed_per_head':{'32056.dat':8,'3707.dat':2,'32123a.dat':4},'added_per_head':{'60483.dat':4},'preserved_support132':False,'integrated_support132':False,'integrated_support150':True,'horizontal_reinforcement_added':0,'gravity_lever_added':20,'working_lock_pins_removed':2,'revision':REVISION,'reference_support_baseline':'source/assembly-integrated-R1.json','horizontal_R2_explicitly_excluded':True,'changed_support_ids':changed_ids,'removed_support_ids':removed_ids,'preserved_base59':False,'closed_base64':True,'base_changes':{'replaced_32524_with_32278':2,'added_32526':1,'added_2780':4,'direct_RB_corner_restored':True},'original_8_wall_pin_authorized_correction':'Y+4mm physical down;8pins; nominal mating verified','all_7_state_unmodified_retained_parts_exact':True,'root_axles_bushes_fixing_pins':'all retained exactly','notes':'Integrated support bridge plus60483 head candidate changes no source constraints/firmware. Natural endpoint is analysis only; powered overtravel not authorized.'}
(OUTPUT/'baseline-diff.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2))

(OUTPUT/'assembly-integrated132.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False))
oldcounts=collections.Counter(p.name for p in state_parts({a:(m.OPEN_S,50)for a in m.ARMS},False)+original_retained_base())+collections.Counter(r['name']for r in original_rows)
newcounts=collections.Counter(p.name for p in full_machine({a:(m.OPEN_S,50)for a in m.ARMS}))
import csv
with (OUTPUT/'integrated-BOM.csv').open('w')as f:
 w=csv.writer(f);w.writerow(['part','quantity','baseline_quantity','delta'])
 for n in sorted(oldcounts|newcounts):w.writerow([n,newcounts[n],oldcounts[n],newcounts[n]-oldcounts[n]])
(OUTPUT/'support-change-map.json').write_text(json.dumps({'changed_ids':changed_ids,'removed_ids':removed_ids,'rows':rows},indent=2,ensure_ascii=False))
manifest['support-raised']=export('support-raised',core_parts())
manifest['support-only-down40_8']=export('support-only-down40_8',core_parts(40.8,False))
(OUTPUT/'candidate-manifest.json').write_text(json.dumps(manifest,indent=2))
