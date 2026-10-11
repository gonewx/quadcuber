"""Normalize presentation text only; preserve all frozen instances and assembly data.

Run after source preparation and before regenerating base/support illustrations.
"""
from pathlib import Path
import json,copy,hashlib
H=Path(__file__).resolve().parent
b=json.loads((H/'base-steps.json').read_text())
b['title']='64件四角闭合共同底盘'
b['assembly_notes']=['先完成前33步的59件底盘中间状态，B02及B07均使用15L厚梁。','继续按顺序安装B60至B64，形成64件四角闭合底盘；不得把中间开口状态误认成完成底盘。','A=R +X，B=F +Z，C=L -X，D=B -Z；按图中的翼名和世界方向装配。']
rep={
'本版以15L替换原7L；原销位不移，向中心增加8孔长度。新增转角稍后按专页装入。':'本梁使用15L厚梁；从内端起数，按后续各步指定孔位装销。R与B转角按后续专页闭合。',
'保留销仍在原坐标；因内端延长，其孔号均为原7L孔号加8。':'本梁的四根框连接销装在第9、11、13、15孔；第1、3孔留给R与B转角连接。',
'这根马达下梁向底盘中心多伸出1孔（8mm）；梁长仍为15孔，按后续新孔号装销。':'这根马达下梁使用15孔厚梁；内端朝底盘中心，按后续步骤指定孔号装销。',
'相对192源该梁沿自身长度向中心平移8mm；原39790及6558固定位置不动。':'按上述内外端坐标摆放15L梁；39790大框及6558长销按后续孔位装配。',
'所有6558短段及挡肩仍在原位':'所有6558短段及挡肩保持在下梁接缝位置',
'新增5件按后续转角专页安装':'后续继续安装转角的B60至B64共5件',
'原B03至B06和B08至B11的销保持原位置':'已装B03至B06和B08至B11的销保持就位',
'仍通过原下梁固定':'通过已装下梁固定',
'来源图中的A/B/C/D翼':'图中的A/B/C/D翼',
'B-R用新增B60':'B-R用B60',
'新增路径为B44框':'R与B的连接路径为B44框',
'保留57件原底盘位置；B02/B07改15L；加B60至B64共5件。四个39790与20件杠杆不增减。':'底盘共64件：四个39790框、配套下梁与销，以及四处双销L形转角。B02/B07均为15L；B60至B64构成R与B转角。',
}
for st in b['steps']:
 st['module_title']='共用底盘：R与B转角闭合' if st['id'].startswith('BAS-RB-') else '共用底盘：四翼与四处双销L形转角'
 for k in ['title','instructions','technical_instructions','check']:
  if k not in st:continue
  values=st[k] if isinstance(st[k],list)else[st[k]]
  for i,t in enumerate(values):
   for old,new in rep.items():t=t.replace(old,new)
   values[i]=t
  st[k]=values if isinstance(st[k],list)else values[0]
(H/'base-steps.json').write_text(json.dumps(b,ensure_ascii=False,indent=2))
s=json.loads((H/'support-steps.json').read_text());by={x['id']:x for x in s['steps']}
s['title_zh']='150件重力回落支承装配图解'
s['global_cautions_zh']=['仅设计审阅；未通过实体装配、载荷、保持与带电验收。','8枚墙脚销按名义中心Y100毫米装配，实体未验收。','上位必须持续按住把手或由独立夹具托稳；无自动保持。']
# Write direct assembly instructions while retaining all part and placement records.
by['GRAVITY-01']['instructions_zh'][2]='两根销用于内臂与外把手的双点连接。'
by['GRAVITY-08']['instructions_zh'][0]='此时右R臂完成165件阶段装配，头部为60483组件；81号侧梁与84号销仍为预留散件。尚未接底盘、其他三臂或130件支承。右头回转50度、夹指开25度；断电并用夹具固定。'
by['D132-001']['instructions_zh'][2]='装配时保持断电、不放魔方，并用独立夹具可靠托住空托盘。上位须持续按住把手或由夹具保持，不能依靠机构自动保持。'
for sid in ['D132-018','D132-024']:
 by[sid]['instructions_zh'][2]='使用2780普通2L销，确认销肩在接缝，露出8毫米可完整接入两片各4毫米的11478。'
for sid,inside,outside in [('D132-019',42,127),('D132-025',53,128)]:
 by[sid]['instructions_zh'][1]=f'先装内片#{inside}，再从外侧装外片#{outside}。两片均为11478、各厚4毫米，2780同时占满两片圆孔。'
 by[sid]['instructions_zh'][3]='使用5L（40毫米）连接轴，按图贯穿叠层并装外侧半套。名义叠层40毫米，端部零余量，仍须验证转动与防脱。'
for sid,side in [('D132-032','左'),('D132-033','右')]:
 by[sid]['title_zh']=f'{side}中央列：装一件43857双孔连接件'
 by[sid]['instructions_zh'][3]='43857的两个圆孔分别对准Y56和Y64毫米的销轴线；不可把实体中心误对到其中单孔。'
by['D132-062']['instructions_zh'][2]='#84为近左柱位的下排销，必须保留在本步孔位并随半桥一起接入。'
by['D132-034']['cautions_zh'][0]='半桥局部引入经过名义抽样，不代表人手空间、完整前置装配过程或连续扫掠通过。'
by['D132-039']['instructions_zh'][2]='下半套不能从+X靠近，该侧被R墙连接件挡住；也不能沿14毫米长轴向路径穿过U臂。'
by['D132-044']['instructions_zh'][1]='两根轴、四只半套齐全后这侧夹架才算合拢。继续用独立夹具托住桥，不依靠机构自动保持。'
by['D132-076']['instructions_zh'][1]='从右侧沿-X同步直压；远端十字孔保持空置。必须使用整件32140，并按图确认角撑朝向。'
by['D132-078']['instructions_zh'][0]='不放魔方，保持断电和独立支承。先记录所有销肩、轴及半套位置，确认固定接口完整；不依靠机构自动保持。'
by['D132-080']['instructions_zh'][2]='支承按130件清单搭建，杠杆按20件清单搭建，合计150件。上位须持续按住把手或由独立夹具托稳。'
by['GRAVITY-14']['instructions_zh'][0]='130件支承与20件杠杆组成150件总成；各动作姿态均保留全部零件。'
rep={
'原框':'根部框','原下层64179':'下层64179','原底盘':'底盘','原墙':'墙体','原基座':'基座','保留墙体孔':'墙体孔','原机':'整机',
'新增20件全部就位':'20件杠杆全部就位','沿原上轴端':'沿上轴端','源模型没有额外滑隙':'名义模型没有额外滑隙',
'三条托面依旧完整':'三条托面保持完整','本页提前到封桥之前':'本页在封桥之前完成',
}
for st in s['steps']:
 for k in ['title_zh','module_title_zh','instructions_zh','cautions_zh','view_note_zh']:
  if k not in st:continue
  values=st[k] if isinstance(st[k],list) else [st[k]]
  for i,t in enumerate(values):
   for old,new in rep.items():t=t.replace(old,new)
   values[i]=t
  st[k]=values if isinstance(st[k],list) else values[0]
(H/'support-steps.json').write_text(json.dumps(s,ensure_ascii=False,indent=2))
print('Cleaned user-visible text in 36 base and 93 support source steps; geometry records untouched.')
