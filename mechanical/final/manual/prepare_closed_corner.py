"""Add the authorized native-geometry R-B closure instruction pages to base source."""
from pathlib import Path
import copy,json,collections
H=Path(__file__).resolve().parent
b=json.loads((H/'base-steps.json').read_text());rows=b['rows'];b['steps']=b['steps'][:33]

def add(id,title,new,visible,instructions,technical,insertion,ports,view=None):
 seq=len(b['steps'])+1
 st=dict(id=id,module_id='foundation',module_step_number=seq,sequence_number=seq,title=title,module_title='R4共用底盘：R与B直接闭合',instructions=instructions,technical_instructions=technical,added_part_ids=new,visible_part_ids=visible,highlight_part_ids=new if new else [2,7,60,61,62,63,64],parts=[],assembly_action='add_parts'if new else'verify_closed_loop',requires_subassemblies=[b['steps'][-1]['id']],insertion=insertion,ports=ports,view=view or {'azim':35,'elev':48},check='四角各两腿、每腿两销；名义孔口连接不等于保持、刚度或承载验收。',retained_ids=[f'B{i:02d}'for i in new],geometry_records=[rows[i-1]for i in visible],r4_changed=True,image_relative=f'images/BASE-{id}.png')
 st['image']=str((H/st['image_relative']).resolve())
 for name in dict.fromkeys(rows[i-1]['name']for i in new):
  ids=[i for i in new if rows[i-1]['name']==name];st['parts'].append(dict(name=name,count=len(ids),part_number=name.removesuffix('.dat'),part_ids=ids))
 b['steps'].append(st)

ports=[]
for pin,host,n in [(61,2,1),(62,2,3),(63,7,3),(64,7,1)]:
 p=[q*.4 for q in rows[pin-1]['position_ldu']];p[1]=112
 ports.append(dict(center_mm=p,axis=[0,1,0],part_ids=[host,pin],host_part_id=host,pin_part_id=pin,hole_number_from_inner_end=n,label=f'B{host:02d}内端第{n}孔'))
add('BAS-RB-01','R与B转角：预装四根黑销',[61,62,63,64],[2,7,61,62,63,64],[
 '本页仅画R、B角局部；59件临时底盘仍在位并独立托稳。此时尚不装机械臂、U杠杆或130件支承。',
 '取4根2780。B02梁从内端数第1、3孔装B61、B62；B07梁从内端数第3、1孔装B63、B64。',
 '销由上方沿+Y压入下梁半根，挡圈留在Y108毫米上表面；上半段露出8毫米，供下一步L梁套接。'],[
 'B61/B62销中心分别为[48,108,-32]、[64,108,-32]毫米；B63/B64为[48,108,-64]、[48,108,-48]毫米。',
 '4枚销轴均平行Y；原B03至B06和B08至B11的销保持原位置。'],
 [dict(part_ids=[61,62,63,64],direction=[0,1,0],start_offset_mm=[0,-32,0],label='上方预装销，挡圈留在梁面')],ports)
ports=[]
for pin,label in [(63,'长腿独立端第1孔'),(64,'长腿第3孔'),(61,'短腿弯角端孔'),(62,'短腿另一端孔')]:
 p=[q*.4 for q in rows[pin-1]['position_ldu']];p[1]=104
 ports.append(dict(center_mm=p,axis=[0,1,0],part_ids=[60,pin],host_part_id=60,pin_part_id=pin,label=label))
add('BAS-RB-02','R与B转角：装入第四根L梁',[60],[2,7,60,61,62,63,64],[
 '取1件32526 3×5厚L梁B60；长腿从独立端数用第1、3孔，短腿用两端孔。四孔对准刚装好的B61至B64。',
 '仅把L梁从上方沿+Y平直放下，先套住四个销尖，再均匀压到下梁上。禁止强推挡圈过孔。',
 '本页为局部图；R、B两个39790框仍通过原下梁固定。四根新销的挡圈都停在L梁与下梁之间Y108毫米接缝。'],[
 'B60 LDraw原点[48,104,-64]毫米、单位旋转矩阵；原点不是弯角。',
 'B63/B64接B07，B61/B62接B02；每腿两销、孔距16毫米。B60从Y偏移-40毫米沿+Y装入。'],
 [dict(part_ids=[60],direction=[0,1,0],start_offset_mm=[0,-40,0],label='只有L梁下降，两根下梁与四翼不动')],ports)
add('BAS-RB-03','四个39790框闭合：64件底盘核对',[],list(range(1,65)),[
 '四个框分别为R +X的B01、F +Z的B28、L -X的B12、B -Z的B44；来源图中的A/B/C/D翼依次对应R/F/L/B。',
 '逐角核对：R-F用B39，F-L用B23，L-B用B55，B-R用新增B60。每个L角两腿各两根2780，不留开口角。',
 '新增路径为B44框、B07下梁、B60 L梁、B02下梁、B01框；8枚墙脚销稍后将四臂分别接到各自底框。',
 '此时底盘64件全部在位，尚无机械臂、U杠杆或130件支承。闭环仅指名义销孔拓扑；不说明足够刚度、保持力或承载能力。'],[
 '保留57件原底盘位置；B02/B07改15L；加B60至B64共5件。四个39790与20件杠杆不增减。'],[],[],{'azim':-90,'elev':88})
b['validation'].update(step_count=len(b['steps']),introduced_exactly_once=True,final_visible_exact64=True,maximum_new_parts_per_step=max(len(s['added_part_ids'])for s in b['steps']),new_corner_step_ids=[s['id']for s in b['steps'][33:]])
assert collections.Counter(i for s in b['steps']for i in s['added_part_ids'])==collections.Counter(range(1,65))
assert b['steps'][-1]['visible_part_ids']==list(range(1,65))
(H/'base-steps.json').write_text(json.dumps(b,ensure_ascii=False,indent=2));print('Base source:36 steps,64 parts; pins then L before arm installation')
