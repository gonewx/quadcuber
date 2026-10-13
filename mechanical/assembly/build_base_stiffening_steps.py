"""From-scratch recipe for the final120-part foundation, preserving stable IDs1..64."""
from pathlib import Path
import sys,json,copy,collections
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import candidate as c
from base_stiffening import REPLACED_PIN_IDS,LOWER_IDS,CORNER_IDS
from paths import INPUTS,ASSEMBLY
book=json.loads((INPUTS/'base-r4-steps.json').read_text());parts=c.retained_base()
rows=[dict(index1=i,id=f'B{i:02d}',name=p.name,color=p.color,position_ldu=p.pos.tolist(),rotation=p.rot.tolist(),note=p.note)for i,p in enumerate(parts,1)]
ids={p.note:i for i,p in enumerate(parts,1)if p.note};introduced=set()
def axis_hosts(pin_ids,pool):
 out=[]
 for i in pool:
  t=c.world(parts[i-1]);lo,hi=t.min((0,1)),t.max((0,1))
  if any(all(lo[d]-1e-6<=parts[j-1].pos[d]*.4<=hi[d]+1e-6 for d in [0,2]) for j in pin_ids):out.append(i)
 return out
for s in book['steps']:
 added=s['added_part_ids'];introduced.update(added)
 if set(added)&set(REPLACED_PIN_IDS):
  assert set(added)<=set(REPLACED_PIN_IDS)
  s['title']=s['title'].replace('黑销','A组长销').replace('预留','预装')
  s['instructions']=[f'取{len(added)}根6558长销，对准原下梁内端第1、3孔。','从下方沿−Y插入16mm长端；肩圈停在Y116。','长端向上露8mm；8mm短端朝下留给新L梁。','独立托稳；不装2780，不强推销肩穿孔。']
  s['technical_instructions']=[f'B{i:02d}轴线X={parts[i-1].pos[0]*.4:g}，Z={parts[i-1].pos[2]*.4:g}mm；长端Y100–116，短端Y116–124。'for i in added]
  s['insertion']=[dict(part_ids=added,direction=[0,-1,0],start_offset_mm=[0,32,0],label='从下方插长端；肩圈留在Y116')]
 if set(added)&set(CORNER_IDS):
  s['instructions']=['取32526上层厚L梁，对准该角四根A组长销露出的长端。','从上方沿+Y套入，L梁占Y100–108，贴合原下梁顶面。','长销肩圈在Y116，即原下梁底面；不是两梁间Y108接缝。','逐孔对齐并托稳，不强推销肩穿孔。']
  s['check']='上层L梁贴紧原下梁；A组肩圈在Y116，短端朝下。'
  s['ports']=[]
  s['technical_instructions']=['上层L梁在Y100–108，沿+Y套住原下梁上方露出的A组长端；长销肩圈仍在下梁底面Y116。']
 if s['id']=='BAS-36':s['title']='接上D翼：继续闭合第四角'
 if s['id']=='BAS-RB-03':
  s['title']='核对上层四角闭环，继续下层装配';s['instructions']=['上层64个实例已经到位，其中16个角连接件已直接使用6558长销。','四个39790经四个上层L梁闭合；A组短端向下露出，尚需安装下层框与四脚。','这只是中间装配状态，不是最终120件底盘。'];s['technical_instructions']=[]
 s['instructions']=[x.replace('角部的备用黑销保持露出','角部A组长销的长端保持露出') for x in s['instructions']]
 s['r4_changed']=True

def append(title,added,visible,instructions,hosts=()):
 introduced.update(added);n=len(book['steps'])+1
 book['steps'].append(dict(id=f'BASE64-{n:02d}',module_id='foundation',title=title,added_part_ids=added,visible_part_ids=sorted(set(visible)|set(added)|set(hosts)),instructions=instructions,technical_instructions=[],insertion=[dict(part_ids=added,direction=[0,-1,0],start_offset_mm=[0,32,0],label='下方逐件装入')],ports=[],view=dict(azim=35,elev=48),check='逐孔核对销肩；临时托稳，不能强压多个错位销。几何接合不证明刚度与保持力。',r4_changed=True))
for old in CORNER_IDS:
 n=ids[f'C{old:02d}'];p=parts[n-1]
 box=c.world(p).reshape(-1,3);lo,hi=box.min(0),box.max(0)
 pins=[i for i in REPLACED_PIN_IDS if all(lo[d]-1e-6<=parts[i-1].pos[d]*.4<=hi[d]+1e-6 for d in [0,2])]
 assert len(pins)==4
 # Display all upper corner instances to make host identity unambiguous.
 append(f'下层转角：在B{old:02d}正下方装厚L梁B{n:02d}',[n],[old,n]+pins+axis_hosts(pins,LOWER_IDS),['取32526厚L梁，与上层对应L梁同向，向下相隔16mm。','从下方沿−Y套住该转角四根A组短端；新L梁占Y116–124，贴紧四处销肩。','上层L梁与新L梁之间夹着原下梁，不能把两片L直接贴在一起。'])
inner=[i for note,i in ids.items() if note.startswith('INNER-')]
for k in range(4):
 group=[i for i in inner if parts[i-1].note.startswith(f'INNER-{k}-')]
 append(f'转角{k+1}：预装两根B组长销',group,axis_hosts(group,LOWER_IDS+[ids[f'C{x:02d}']for x in CORNER_IDS]),['每翼内端第2孔装6558。16mm长端从下方沿−Y穿过新L梁和原下梁。','肩圈位于Y124，8mm短端朝下，留给新15L梁第2孔；不占A组第1、3孔。'])
for old in LOWER_IDS:
 mid=ids[f'M{old:02d}'];low=ids[f'D{old:02d}'];pins=[ids[f'OUT-{old}-{t}']for t in [120,152]]
 append(f'B{old:02d}翼：贴合中层9L厚梁',[mid],[old,mid],['取40490厚9L梁贴在原下梁下，Y116–124。','其孔5、9分别对原15L孔10、14，梁方向相同；暂用独立支承托住。'])
 append(f'B{old:02d}翼：装两根C组长销',pins,[old,mid]+pins,['从下方将两根6558的16mm长端依次穿过中层9L及原下梁。','对应原15L孔10、14／9L孔5、9；肩圈在Y124，8mm短端朝下。'])
 append(f'B{old:02d}翼：装下层15L梁B{low:02d}',[low],[old,mid,low]+pins+[i for i in inner if low in axis_hosts([i],[low])],['取32278厚15L梁，与原下梁同向；其孔2、10、14分别套住B、C、C三根短端。','从下方沿−Y均匀靠拢，最终Y124–132；逐孔就位，不强压一整圈梁。'])
for old in [2,29,13,45]:
 foot=ids[f'FOOT-{old}'];low=ids[f'D{old:02d}'];pins=[ids[f'REUSED-FOOT-PIN-{old}-{t}']for t in [144,160]]
 append(f'支脚准备：B{low:02d}孔13、15装短销',pins,[low]+pins,['取两根2780短销，核对中央肩圈和两侧8mm销段。','沿−Y插入新下梁孔13、15，中央肩圈留在梁底Y132，朝下各露8mm。','不要使用孔14：该孔上方已由C组长销占用。'])
 append(f'装支脚B{foot:02d}：厚3L梁',[foot],[low,foot]+pins,['取32523厚3L梁，孔1、3对准两根短销，从下方沿−Y套紧。','脚占Y132–140。四个脚底需共同可靠接触；不共面时用整面硬薄垫补齐，不顶弯框架。'])
append('120件双层闭合底盘完成核对',[],list(range(1,121)),['120件全部在位：上下四角闭环、八组9L中层、八根15L下梁及四脚。','四臂与托盘固定支架共用该底框；移动托盘不能当拉杆。','名义脚底Y140，较旧桌面Y116高24mm。桌面按压会变形时，四脚应落在同一块足够刚的共同承载板上。','四脚不是自动调平，尚未通过实物刚度、保持、承重及抗倾覆验收。'])
assert introduced==set(range(1,121))
for seq,s in enumerate(book['steps'],1):
 s.update(sequence_number=seq,module_step_number=seq,module_title='120件双层闭合底盘：从零装配',image_relative=f'images/BASE-{s["id"]}.png',highlight_part_ids=s['added_part_ids'] or s['visible_part_ids'],geometry_records=[rows[i-1]for i in s['visible_part_ids']])
 s.setdefault('check','核对销肩、孔位和可靠临时支承；未证明实物刚度。')
 groups=collections.defaultdict(list)
 for i in s['added_part_ids']:groups[parts[i-1].name].append(i)
 s['parts']=[dict(name=n,count=len(ii),part_number=n.removesuffix('.dat'),part_ids=ii)for n,ii in groups.items()]
book.update(title='120件双层闭合底盘从零装配',revision=c.REVISION,rows=rows,assembly_notes=['本配方直接搭最终结构，不先搭旧短销版本再拆改。','旧机加装步骤另见docs/lego/proposals/base-stiffening-64。'],validation=dict(part_count=120,step_count=len(book['steps']),introduced_exactly_once=True,final_visible_exact120=True))
(ASSEMBLY/'base-steps.json').write_text(json.dumps(book,ensure_ascii=False,indent=2));print(len(book['steps']),'steps;120 parts')
