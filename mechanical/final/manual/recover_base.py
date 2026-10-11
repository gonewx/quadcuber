"""Recover frozen source steps and apply only the approved R4 R-B corner changes."""
from pathlib import Path
import sys,json,hashlib,copy,shutil,collections,re
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;INPUTS=ROOT/'source/manual-inputs'
sys.path.insert(0,str(HERE.parent));import candidate as c
SRC=INPUTS/'base-legacy219-foundation.json'
ROW=INPUTS/'base-legacy219-first59.json'
legacy=json.loads(SRC.read_text());prior=json.loads(ROW.read_text())[:59]
actual=c.retained_base();original=c.original_retained_base();rows=[]
assert len(actual)==64
for i,(a,b) in enumerate(zip(original,prior),1):
 assert a.name==b['name'] and a.color==b['color']
 assert np.array_equal(a.pos,np.array(b['position_ldu'])) and np.array_equal(a.rot,np.array(b['rotation']))
for i,a in enumerate(actual,1):
 b=prior[i-1] if i<=59 else {}
 rows.append({'index1':i,'id':f'B{i:02d}','legacy_stable_id':b.get('id'),'baseline899_index1':132+i if i<=59 else None,'name':a.name,'color':a.color,'position_ldu':a.pos.tolist(),'rotation':a.rot.tolist(),'r4_change':'replace_7L_with_15L'if i in (2,7)else'add_RB_corner'if i>=60 else None})
 for key in ['name','color','position_ldu','rotation']:
  if i<=59 and i not in (2,7):assert rows[-1][key]==b[key]
render_file=INPUTS/'base-legacy219-render.json'
render={r['id']:r for r in json.loads(render_file.read_text())}
steps=copy.deepcopy(legacy['steps']);introduced=[];image_checks=[]
(HERE/'images').mkdir(exist_ok=True)
changed=[]
for j,s in enumerate(steps,1):
 r=render[s['id']];src=HERE/'images'/f"BASE-{s['id']}.png"
 assert r['visible_part_ids']==s['visible_part_ids'] and r['added_part_ids']==sorted(s['added_part_ids'])
 introduced+=s['added_part_ids'];assert set(s['visible_part_ids'])<=set(introduced)
 assert set(s['requires_subassemblies'])<=set(t['id']for t in steps[:j-1])
 dst=HERE/'images'/f"BASE-{s['id']}.png"
 modified=bool(set(s['visible_part_ids'])&{2,7})
 if not modified:
  assert dst.exists(),f'Packaged unchanged source image missing: {dst}'
  assert hashlib.sha256(dst.read_bytes()).hexdigest()==r['sha256'],f'Unchanged legacy image differs: {dst}'
 else:
  changed.append(s['id']);s['module_title']='R4共用底盘：四翼与四处双销L形转角'
 s['image']=str(dst.resolve());s['image_relative']=str(dst.relative_to(HERE));s['highlight_part_ids']=s.get('highlight_part_ids',s['added_part_ids']);s['check']='按图核对本步孔位、销的挡圈和朝向；全部新件到位后再继续。';s['retained_ids']=[rows[i-1]['id']for i in s['added_part_ids']];s['sequence_number']=j
 s['geometry_records']=[rows[i-1]for i in s['visible_part_ids']]
 s['r4_changed']=modified
 image_checks.append({'id':s['id'],'legacy_sha256':r['sha256'],'exact_legacy219_state':not modified,'requires_R4_render':modified})
byid={s['id']:s for s in steps}
for sid,part,center,first,last in [('BAS-01',2,[104,112,-32],[48,112,-32],[160,112,-32]),('BAS-27',7,[48,112,-104],[48,112,-48],[48,112,-160])]:
 s=byid[sid];s['title']=s['title'].replace('7L','15L')
 s['instructions']=['取1根32278 15孔厚梁，按图平放，让圆孔朝上。',f'从靠底盘中心的内端{first}毫米起数至外端{last}毫米，孔序1至15。','本版以15L替换原7L；原销位不移，向中心增加8孔长度。新增转角稍后按专页装入。']
 s['parts'][0].update(name='32278 15孔厚梁',part_number='32278')
 s['technical_instructions']=[f'B{part:02d}，32278.dat，LDraw原点{center}毫米，孔轴Y。',f'保留销仍在原坐标；因内端延长，其孔号均为原7L孔号加8。']
for sid,nums in [('BAS-02',[15,13,11,9]),('BAS-28',[9,15]),('BAS-29',[11,13])]:
 s=byid[sid];s['title']=s['title'].replace('7L','15L');s['instructions'][0]=re.sub(r'第[^。]*孔','第'+'、'.join(map(str,nums))+'孔',s['instructions'][0]);s['technical_instructions']=[re.sub(r'第(\d+)孔',lambda m:'第'+str(int(m[1])+8)+'孔',t)for t in s['technical_instructions']]
 for port,n in zip(s['ports'],nums):port['hole_number_from_inner_end']=n;port['label']='从15L内端数第'+str(n)+'孔'
s=byid['BAS-36'];s['title']='接上D翼：59件临时开口底盘';s['instructions'][-1]='检查四块39790大框同高、下梁底面齐平，8根蓝销各露出1孔长。此时只有59件，R与B角尚未闭合；新增5件按后续转角专页安装。'
s['check']='本页不是底盘完成状态；必须继续装入B60至B64，最终64件四角闭合。'
assert collections.Counter(introduced)==collections.Counter(range(1,60))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result={'module_id':'foundation','title':'64件共同底盘及R-B闭合转角','revision':c.REVISION,'rows':rows,'steps':steps,'coordinate_convention':legacy['coordinate_convention'],'assembly_notes':['初始33步形成59件临时开口底盘，B02及B07已改15L。','新增B60至B64需按完整手册指定顺序安装；不得把临时开口状态误认成完成底盘。','A=R +X，B=F +Z，C=L -X，D=B -Z；字母翼名沿用来源图。'],'retained_base_mapping':[{k:r[k]for k in ['index1','id','legacy_stable_id','baseline899_index1']}for r in rows],'source_provenance':{'foundation_module':str(SRC.relative_to(ROOT)),'foundation_module_sha256':sha(SRC),'exact_placement_source':str(ROW.relative_to(ROOT)),'exact_placement_source_sha256':sha(ROW),'candidate_source':'integrated-revision/candidate.py retained_base()','baseline899_source_sha256':sha(HERE.parent/'source/baseline-machine-899.mpd'),'r4_delta':'Only B02/B07 replaced; B60 L and B61-B64 pins added. Other57 base placements exact.','step_ids_note':'Original33 source steps preserved; additional corner stages follow approved assembly order.'},'validation':{'part_count':64,'initial_step_count':33,'unchanged_placement_count':57,'changed_legacy_step_ids':changed,'image_checks':image_checks,'scope':'Nominal exact source geometry only; no physical strength or continuous assembly clearance certification.'}}
(HERE/'base-steps.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps({'rows':len(rows),'initial_steps':len(steps),'changed_steps':changed},indent=2))
