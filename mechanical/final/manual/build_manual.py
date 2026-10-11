from pathlib import Path
import json,copy,shutil,hashlib,sys,io
from xml.sax.saxutils import escape
from reportlab import rl_config
rl_config.useA85=False
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from PIL import Image
from reportlab.lib.utils import ImageReader
H=Path(__file__).resolve().parent;ROOT=H.parent
base=json.loads((H/'base-steps.json').read_text());support=json.loads((H/'support-steps.json').read_text())
(H/'head-diagrams').mkdir(exist_ok=True)
steps=[]
def add(title,parts,image,instructions,check,phase,**kw):
 s=dict(id=len(steps)+1,title=title,parts=parts,image=image,instructions=instructions,check=check,phase=phase,**kw);steps.append(s);return s
add('最终结构与装配范围','整机882件：底盘64＋四臂668＋支承150','diagrams/integrated-whole.png',['按最终结构准备64件闭合底盘、四个167件机械臂和150件支承总成。支承总成包含130件托座导向结构与20件重力回落杠杆。','底盘、四臂支架与传动、夹头及支承均从清单单件逐步搭建。电机和舵机作为成品采购件，不拆内部；没有预装核心前提。','本册直接覆盖882个清单实例，各件只在首次取用时计数。先搭完整墙架、舵机架及竖支脚，再装转盘下半和输出传动。先在机外完成模块，再按顺序接入底盘，81号侧梁和84号销留至臂就位后安装。','按住外把手使托盘保持上位，夹头可靠接管重量后缓松回落。本设计无自动保持和阻尼。'],'同一882件模型对应本册、最终零件表及全部动作姿态。实体装配与安全验收仍未通过。','准备')
add('断电空载与独立支承','外部支承夹具不计入模型BOM','diagrams/integrated-whole.png',['装配时不放魔方，断开电机电源和驱动连接，固定底盘，并用独立夹具支承机械臂、夹指及移动托盘。','一次只装一个头部和一根根轴。未装好端部保持件前，夹指和根轴均须独立支承。','先确认工作台稳定、零件可从指定方向接近，再插入销轴。不可用手指代替夹具，不靠软件停止代替断电。','图示为名义装配姿态，不能证明人手接近空间、连续装配路径或实际插入力。'],'没有可靠支承、无接近空间或需要强推销肩穿孔时立即停止。','准备')
add('最终组件与零件盘点','底盘64件；四臂668件；支承150件','diagrams/integrated-whole.png',['每臂167件，含4件60483根部支架；四臂合计668件。根轴、定位轴套、夹指和连接销按所在位置分组，不能仅凭相同型号互换位置。','支承总成150件包含130件托座导向结构与20件杠杆。杠杆20件已包含4件上止挡。','按本册组装双11478桥端、中央43857及32316五孔厚梁，并核对托面、导轨和下止挡。','底盘为四框闭环，每处L形转角双销连接。每臂墙脚用两枚2780，共8枚。颜色是模型展示信息，采购配色未核实。'],'882件是全部动作状态的固定数量，不因托盘上下或夹指开合变化。','准备')
for s in base['steps']:
 add(s['title'],'；'.join(str(p['count'])+'×'+p['part_number']for p in s['parts']),s['image_relative'],s['instructions']+s.get('technical_instructions',[]),s['check'],'底盘64件',source_step_id=s['id'],layout='source-page',added_part_ids=s['added_part_ids'],visible_part_ids=s['visible_part_ids'],r4_changed=s.get('r4_changed',False),geometry_records=s.get('geometry_records'))
add('墙脚连接销与底盘接口定位参照','共8×2780；每臂2枚','diagrams/wallfoot-detail.png',['局部图为L臂实际墙64179、底盘39790和两枚2780。其余三臂绕竖直Y轴变换，向下均为+Y；图中省略不相关零件。','销中心位于Y100毫米。墙孔占Y92至100毫米，底盘孔占Y100至108毫米，销两侧各配合8毫米，挡环位于Y100接缝。','此页为接口定位参照。后续逐件搭墙时将半插这两枚墙脚销；在后续臂接入底盘时核对接缝。最终孔位已做名义核对，实际接近空间、插入力及保持力仍待验证。'],'R、L、F、B各两枚，共8枚；够不到或需要强推挡环过孔即停。','四臂接口')
final_head=json.loads((H/'final-head-steps.json').read_text())
for arm,label in [('R','右臂'),('L','左臂'),('F','前臂'),('B','后臂')]:
 for original in final_head['steps']:
  s=copy.deepcopy(original)
  add(arm+' '+s['title'],s['parts'],s['image'],[f'本页组装尚未接底盘的{arm} {label}，用独立夹具托稳。A/B和±Z为本头局部坐标。']+s['instructions'],s['check'],(arm+' 转盘下半固定' if s['id'].startswith('HEAD-TT-') else (arm+' 墙架／舵机架逐件搭建' if s['id'].startswith('CORE-') or s['id']=='HEAD-FINAL-01' else '机械臂组件装配')),source_step_id='HEAD-'+arm+'-'+str(s.get('source_step_id',s.get('id'))),arm=arm,**{k:s[k] for k in ['added_part_ids','visible_part_ids','geometry_records'] if k in s})
add('四个机械臂组件核对','每臂165件待安装组件＋2件侧撑预留件；共668件',final_head['steps'][-1]['image'],['逐一检查R、L、F、B两根根轴；每根轴两侧各1件60483，轴套与连接销按图全部到位。','每臂当前165件，另将81号侧梁和84号连接销两件单独预留，安装到底盘后共167件。全部组件已按本册从清单单件搭建；逐项核验完整性和姿态。墙脚49/50及底脚77随臂保留，底盘上不得重复预装。','四臂分别离机支承。R臂接U前需整头回转50°、夹指开25°；接入底盘前需名义夹紧端／整头0°。这些姿态转换须用另经验证的断电定位方法，无法安全定位就停止。'],'每头单独核对，不以一头通过代替四头核对。','组件核对')
def add_support(s):
 phase='130件支承装配' if s['module_id']!='lever' else '20件杠杆装配'
 add(s['title_zh'],'；'.join('#'+str(p['index1'])+' '+p['part'].removesuffix('.dat')for p in s['new_parts'])or'无新增件',s['image_file'],s['instructions_zh']+s['cautions_zh'],'按图核对本版实例；插拔路径、保持与承重仍待实体验证。',phase,source_step_id=s['id'],layout='source-page',added_part_ids=s['added_part_ids'],visible_part_ids=s['visible_part_ids'],geometry_records=s['geometry_records'],lever_parameter_mm=s.get('lever_parameter_mm'))
for st in support['steps'][:10]:add_support(st)
def restore_arm(arm):
 direction={'R':'世界-Z外侧沿+Z','L':'世界+Z外侧沿-Z','F':'世界+X外侧沿-X','B':'世界-X外侧沿+X'}[arm]
 add(arm+'臂先装84号销再装81号侧梁','装入预留件：1×2780（84）＋1×40490 9L梁（81）；该臂共167件','diagrams/brace-'+arm+'.png',[
  '保持该臂、底盘和U杠杆独立支承，电机断电。81/84为该臂局部实例编号，不能与B81或支承编号混用；82/83两销留在原宿主。',
  '先从'+direction+'，把84号2780只插入底框半根，让中央挡圈停在底框外侧接缝面。不要先放9L梁，也不要把销强推穿过两个闭合宿主。',
  '再把81号9L梁从同一外侧沿同方向靠拢，使三个孔同时套住82、83、84的露出销尖，均匀压至三处挡圈。图左右两幅按1、2顺序执行。',
  '核对上面两销连接原臂宿主，下面84销连接对应39790底框；三枚挡圈都留在宿主之间。预留件全部安装后，再按顺序继续。']+(['四臂全装好后，U仍固定42.4，魔方、托盘和130件支承仍未装。采用经验证的断电定位方法，按R、L、F、B逐头操作：先保持夹指在名义夹紧端（行程0），整头回转0至50度，再张开至25度；一头完成再到下一头。无法可靠定位或隔离就停；不授权带电动作。']if arm=='B'else[]),
  '没有接近空间、宿主不稳或需强推挡圈过孔即停；名义路径检查不证明插入力、保持或承载。','侧撑安装',source_step_id='ARM-'+arm+'-RESTORE',arm=arm,deferred_original_arm_indices1=[81,84],introduced_arm_part_ids=[84,81])
add('右R臂带16件杠杆分阶段接入底盘','R臂165＋杠杆16＋底盘64＝245件','diagrams/interface-R.png',[
 '先按前页在165件孤立R臂上装好U16，再于离机状态把头设为夹指位于名义夹紧端（行程0）、整头回转0度。杠杆保持42.4毫米；全程断电、独立托稳，不强扭传动。',
 '确认81号40490 9L侧梁和84号2780销仍单独预留，82/83两销在已搭组件宿主内。R臂此时165件。',
 '将R165与U16作为一组从世界-Y上方沿+Y落到已闭合64件底盘，名义高度偏移-160至0毫米。墙脚49/50和底脚77均随臂下落，底盘上不另装同件；墙脚两销肩停在Y100毫米接缝。',
 '81号侧梁和84号销待臂就位后安装。就位后按下一页先装84再装81；其余三臂与130件支承仍不装。'],
 '本图真实省去81与84；分阶段名义检查不证明连续安装、人手接近或插入力。','四臂接口',arm='R',deferred_original_arm_indices1=[81,84])
restore_arm('R')
for arm,label in [('L','-X左臂'),('F','+Z前臂'),('B','-Z后臂')]:
 add(label+'分阶段接入共同底盘','该臂165件；就位后安装预留81/84，共167件','diagrams/interface-'+arm+'.png',[
  f'独立托稳已完成根部装配的{arm}臂。其余已装臂的81/84均已安装；右臂U16保持下位参数42.4毫米，130件支承仍未安装。',
  '确认本臂81号9L侧梁和84号2780销仍单独预留，82/83两销在已搭组件宿主内。本步图显示待装165件组件。',
  '该臂和已安装各臂均须夹指位于名义夹紧端（行程0）、整头回转0度，将165件组件从世界-Y上方沿+Y下降，名义高度偏移-160至0毫米。墙脚49/50和底脚77均随臂下落，底盘上不另装同件；两枚墙脚销在Y100毫米接缝接合。',
  '继续独立支承该臂，并立即按下一页先装84销，再从外侧安装81侧梁。四臂均达到167件后，才安装4件上止挡并搭130件支承。'],
  '路径为名义分阶段检查；不能推导完整连续无碰、人手接近、销保持或承载能力。','四臂接口',arm=arm,deferred_original_arm_indices1=[81,84])
 restore_arm(arm)
for st in support['steps'][10:13]:add_support(st)
for st in support['steps'][13:]:add_support(st)
add('最终整机与20件杠杆核对','64＋668＋130＋20＝882件','diagrams/integrated-whole.png',['所有动作模型均882件；四个39790框通过四个双销L转角闭合。核对每个转角的两处销连接均已到位。','20件杠杆包括3×32278、2×2780、1×3708、1×23948、6×32123a、2×62462、2×18654、2×3713、1×3705。外把手需持续按住才保持上位。','12L支点轴同时穿过原64179的两处支点孔，11L横轴各层齐全；外把手第4孔为上止挡，末端第1至3孔才是上方按压区。','原托盘下落约40.8毫米到原导轨下止挡。下位图的杠杆参数42.4毫米包括1.6毫米接触转换，不能把它当托盘行程。'],'模型、逐步图、零件表同版；实体完成前仍不放行带电运行。','最终核对')
add('空载按住与缓松检查','按压区仅为把手末端三孔上方','diagrams/lever-upper.png',['保持断电、无魔方，并以独立支承作为保护。手只从把手末端第1至3孔上方施力，手指保持在把手上表面以上。','缓慢向下按把手，托盘被托到名义上位，3713上止挡接触原39790实体上表面。到位后只保持必要按压力，不能猛压止挡。','缓慢减小按压力，观察空托盘是否在自重下平顺回落到原导轨约40.8毫米下挡。出现不回落、卡滞、歪斜或突然落下，恢复独立支承并停止。','裸机构最小离桌约9毫米；此处是夹手危险区，不是可伸手的安全间隙。不从下方握住把手，不把手伸入支点、托盘或桥梁之间。'],'几何和碰撞抽样不证明重力一定复位，也不证明下降阻尼或冲击强度。','空载操作检查')
add('装料与机械头接管后再缓松','设计动作关系；不授权带电试机','diagrams/lever-upper.png',['通过另行定义的实体验收后，装料关系为：按住把手让托盘升到上位并持续保持，在三条完整托面上放56毫米魔方，轻靠两条定位边。','所有手和工具退出机械头运动范围之后，才允许另经验证的头部夹持交接。不要把手伸到正在驱动或仍带电的机械头旁。','确认机械头已可靠接管魔方的重量后，才缓慢减小把手按压力，让空托盘按重力回落。不得先松把手再等待机械头夹紧。','本册没有证明夹持力、空载自返、冲击、控制联锁或同时手动／电动操作安全；没有这些验证时，不执行带魔方或带电流程。'],'按住是持续动作；该机构没有自动保持，上止挡不能代替锁扣。','操作关系')
add('取回魔方先抬升并持续按住','托盘承接后释放夹持；取走后才松把手','diagrams/lever-upper.png',['采用另行验证的取回姿态；手、工具和其他身体部位须先避开机械头运动区，电机运动时不得伸手靠近。','按住把手抬升托盘，持续保持，直到托盘确实承接魔方重量。不能仅看几何位置就认定已承接。','托盘可靠承接后，再按经验证的控制流程解除头部夹持。确认电机停止且安全断能后，从允许的路径取走魔方，同时仍按住把手。','魔方完全取走后，才缓慢减小按压力让空托盘回落。禁止在魔方尚未取走时先松开。'],'承接、解除夹持和取走的顺序不可省略；任何不确定先恢复可靠支承。','操作关系')
add('上止挡与高度需要实测','0.14毫米仅为网格敏感性探测尺度','diagrams/lever-upper.png',['4件上止挡在名义上位接触原框实体面；原导轨提供约40.8毫米下端点。这只确定名义几何关系。','约0.14毫米来自LDraw轴套多边形网格随相位变化的保守敏感性探测。它不是实体圆轴套的周期性高度变化，也不是实际公差等级或校准误差。','实体需以同一固定基准记录空载、加载和卸载高度、左右高差、回落情况、销与半套位移，并验证止挡、根轴、框架和横轴的强度。','没有已给定或已通过的载荷、拉脱力、寿命、下降速度及冲击验收限值，不得从名义间隙推断性能合格。'],'上止挡磨损、框弯曲、半套外爬或冲击均需独立检查。','证据与限制')
add('夹指开角与整头回转分别核对','夹指名义夹紧端约3.8417°；正常张开不超过25°','final-head-diagrams/opening.png',['夹指行程0对应名义夹紧端，夹指角约3.8417°；不要把它写成夹指角0°。','夹指正常最大开角为25°。整头回转的0°、50°和90°属于另一运动轴，不能混用。','不把约30.872°自然端点当机械限位、归零基准或带电命令。','只在可靠支承和断电条件下检查，禁止硬掰夹指反驱传动。实际夹持力、保持与控制联锁另行验收。'],'角度与运动轴均已辨认；任何卡滞、异常松动或轴套爬移均须停止。','安全与试验')
add('碰撞抽样的范围与停止条件','设计审阅证据不等于连续通过或实体放行','diagrams/support-lowered.png',['杠杆41点碰撞检查属于离散名义抽样，不是全行程连续碰撞认证。后续更密抽样也不能取代公差、变形及实体检验。','12L、11L及上止挡轴的名义端部余量不证明半套保持力。60483根轴64毫米叠层与桥端40毫米叠层的零名义余量仍须验证。','任一项出现即停：销肩不能就位、轴或半套爬移、托盘卡滞或突然下落、支点仅单侧支承、框梁变形、接触件磨损、手与头部运动区域无法隔离。','保留故障照片、所在臂／轴／孔位和姿态；恢复独立支承和断电状态后再评审，不通过改孔、磨销或临时加绑带来补救。'],'完成本册不等于装配、承重、夹持交接或带电运行验收通过。','安全与试验')
manifest=json.loads((ROOT/'candidate-manifest.json').read_text())
whole_states=['loading-all50','FB0-open','FB0-held','support-held','support-down40_8','LR90-open','both-held']
assert all(manifest[k]['parts']==882 for k in whole_states),'Candidate manifest is not the882part release'
guide=dict(title='Quadcuber最终结构装配手册',revision='FINAL-ASSEMBLY-2026-10-09-FULL-PARTS',review_only=True,hold_summary='最终结构含四角闭环底盘和20件杠杆；实体装配路径、保持、载荷、自重回落与带电验收仍未通过。',coverage={'base_parts':64,'base_steps':len(base['steps']),'support_parts':150,'seat_guide_parts':130,'lever_parts':20,'support_steps':len(support['steps']),'arm_prerequisites':final_head['prerequisites'],'final_arm_parts':668,'head_steps_per_arm':len(final_head['steps']),'head_assembly_steps':4*len(final_head['steps']),'original_arm_from_scratch':True,'prebuilt_core_total_parts':4*final_head['prerequisites']['prebuilt_core_count'],'direct_assembly_parts':882-4*final_head['prerequisites']['prebuilt_core_count'],'model_count_working':882,'model_count_lowered':882},model_manifest=manifest,steps=steps)
# Every physical inventory instance has one introduction, separately from reference views.
ledger=[]
for s in steps:
 if s.get('introduced_arm_part_ids'):
  ns='arm-'+s['arm'];ids=s['introduced_arm_part_ids']
 elif s.get('arm') and s.get('source_step_id','').startswith('HEAD-'):
  ns='arm-'+s['arm'];ids=s.get('added_part_ids',[])
 elif s.get('phase')=='底盘64件':ns='base';ids=s.get('added_part_ids',[])
 elif s.get('phase') in ['130件支承装配','20件杠杆装配']:ns='support';ids=s.get('added_part_ids',[])
 else:ns=None;ids=[]
 s['introduced_instance_keys']=[ns+':'+str(i)for i in ids]
 ledger.extend(dict(instance_key=k,step_id=s['id'])for k in s['introduced_instance_keys'])
expected={ns+':'+str(i)for ns,n in [('base',64),('support',150)]+[('arm-'+a,167)for a in ['R','L','F','B']]for i in range(1,n+1)}
assert len(ledger)==882 and {x['instance_key']for x in ledger}==expected
assert len({x['instance_key']for x in ledger})==882
guide['coverage']['instance_introduction_count']=len(ledger)
guide['instance_introduction_ledger']=ledger
(H/'guide.json').write_text(json.dumps(guide,ensure_ascii=False,indent=2))
# Readable master guide for searches and source review.
md=['# '+guide['title'],'','版本：'+guide['revision'],'','设计审阅，未实体放行。','']
for s in steps:md+=['## '+str(s['id'])+' '+s['title'],s['parts'],'']+s['instructions']+['','核对：'+s['check'],'']
(H/'manual.md').write_text('\n'.join(md))
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
W,HG=864,666;c=canvas.Canvas(str(H/'manual.pdf'),pagesize=(W,HG));c.setTitle(guide['title']);c.setAuthor('dot')
P=ParagraphStyle('body',fontName='STSong-Light',fontSize=11.6,leading=17,wordWrap='CJK');T=ParagraphStyle('title',parent=P,fontSize=19,leading=26);S=ParagraphStyle('small',parent=P,fontSize=9.8,leading=14)
def para(t,x,y,width,style=P):
 t=t.translate(str.maketrans({'−':'-','–':'-','—':'-','‑':'-','‒':'-'}))
 p=Paragraph(escape(t).replace('\n','<br/>'),style);_,h=p.wrap(width,1000);p.drawOn(c,x,y-h);return y-h-7
checks=[]
for s in steps:
 c.bookmarkPage('STEP-'+str(s['id']));c.addOutlineEntry(str(s['id'])+' '+s['title'],'STEP-'+str(s['id']),0,False)
 y=para(f'{s["id"]:03d} / {len(steps)}   {s["phase"]}   {s["title"]}',28,HG-18,808,T)
 ip=H/s['image'];assert ip.exists(),ip
 if s.get('layout')=='source-page':
  im=Image.open(ip);wi=832;he=wi*im.height/im.width
  max_image_height=min(565,y-68)
  if he>max_image_height:he=max_image_height;wi=he*im.width/im.height
  c.drawImage(str(ip),(W-wi)/2,56,width=wi,height=he)
  bottom=47
 else:
  y=para(s['parts'],30,y,804,S)
  im=Image.open(ip);wi=495;he=min(350,wi*im.height/im.width);wi=he*im.width/im.height
  # Final-head diagrams are downsampled only in PDF to about145dpi; source PNGs remain full resolution.
  if 'final-head-diagrams/' in s['image']:
   pdfimage=im.convert('RGB');pdfimage.thumbnail((1000,1000),Image.Resampling.LANCZOS);encoded=io.BytesIO();pdfimage.save(encoded,format='JPEG',quality=94,subsampling=0,optimize=True);encoded.seek(0);c.drawImage(ImageReader(encoded),25,HG-115-he,width=wi,height=he)
  else:c.drawImage(str(ip),25,HG-115-he,width=wi,height=he)
  yy=HG-112
  for i,line in enumerate(s['instructions'],1):yy=para(str(i)+'. '+line,535,yy,302,P)
  yy=para('核对：'+s['check'],535,yy,302,P);bottom=yy
  if bottom<45:raise RuntimeError(f'Overflow step{s["id"]}: {bottom}')
  para('真实LDraw网格；爆炸间距仅用于识别，不代表装配间隙或已验证路径。',30,160,475,S)
 c.setFont('STSong-Light',9);c.drawString(28,22,'FINAL ASSEMBLY | 设计审阅；实体装配／保持／强度／重力回落／带电动作未放行');c.drawRightString(W-28,22,str(s['id']))
 checks.append({'page':s['id'],'bottom_text_y':bottom,'image':s['image']});c.showPage()
c.save();(H/'pdf-layout-check.json').write_text(json.dumps(checks,indent=2));print('PDF',len(steps),'pages')
