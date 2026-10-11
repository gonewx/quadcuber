from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import MECHANICAL, ASSEMBLY, MANUAL_OUTPUT
"""Generate final-only native head assembly records and diagrams.
Usage: python manual/build_final_head.py [--data-only | --render-only] [--select 1 2 ...]
No model is changed. Instance numbers are 1-based candidate.module(0,0,False,True).
"""
from pathlib import Path
import argparse, collections, hashlib, json, sys, copy, os
import numpy as np
H=MANUAL_OUTPUT
sys.path.insert(0,str(MECHANICAL))
import candidate as C
P=C.module(0,0,False,True)
assert len(P)==167
ASSEMBLED_CORE=[i for i in range(1,97) if i not in [81,84,88,89,94,95]]
TURNTABLE_MOUNT=list(range(34,49))+[86]
DRIVE_INPUT=list(range(24,30))
FORMER_CORE=[i for i in ASSEMBLED_CORE if i not in TURNTABLE_MOUNT]
CORE=[]
MAIN_INPUT=[]
DEFER=[81,84]
ADDED=sorted(set(range(1,168))-set(CORE)-set(DEFER))
ROWS=[dict(index1=i,name=p.name,color=p.color,position_ldu=p.pos.tolist(),rotation=p.rot.tolist()) for i,p in enumerate(P,1)]
assert len(CORE)==0 and len(ADDED)==165

def bom(ids):
 return [dict(name=n,part_number=n.removesuffix('.dat'),count=k,instance_indices1=[i for i in ids if P[i-1].name==n]) for n,k in sorted(collections.Counter(P[i-1].name for i in ids).items())]
def desc(ids):return '；'.join(f'{x["count"]}×{x["part_number"]}' for x in bom(ids)) or '本步合并／核对，无新增件'
def record(ids):return [copy.deepcopy(ROWS[i-1]) for i in ids]

steps=[];introduced=set(CORE);legacy_number=0
SIDE_M=list(range(106,115));SIDE_P=list(range(97,106));TT=list(range(115,121));MAIN=[]
WARN='独立支承、断电、空载；名义图不证明连续插入路径、插入力、保持力或实体装配通过。'
def step(title,new,visible,ins,check,focus=None,view=(22,55),arrows=(),sub='head',note='',extra=None,turntable_id=None,core_id=None):
 global legacy_number
 new=list(new);visible=list(visible);focus=list(focus) if focus is not None else None
 n=len(steps)+1
 if turntable_id is None and core_id is None:legacy_number+=1
 stable_id=f'CORE-{core_id:02d}' if core_id is not None else f'HEAD-TT-{turntable_id:02d}' if turntable_id is not None else f'HEAD-FINAL-{legacy_number:02d}'
 image_id=f'CORE{core_id:02d}' if core_id is not None else f'TT{turntable_id:02d}' if turntable_id is not None else f'{legacy_number:02d}'
 assert not(set(new)&introduced),(n,new)
 introduced.update(new)
 s=dict(id=stable_id,source_step_id=stable_id,number=n,diagram_label=('支架搭建 '+str(core_id) if core_id is not None else '转盘固定 '+str(turntable_id) if turntable_id is not None else f'{legacy_number:02d}'),title=title,parts=desc(new),image=f'final-head-diagrams/{image_id}.png',instructions=ins,check=check,added_part_ids=new,new_parts=record(new),visible_part_ids=visible,highlight_part_ids=focus if focus is not None else new,geometry_records=record(visible),introduced_part_ids=sorted(introduced),cumulative_introduced_count=len(introduced),subassembly_id=sub,view=dict(elev=view[0],azim=view[1]),insertion_vectors_mm=list(arrows),diagram_note=note or '图为本步完成状态；局部省略的已装件仍在独立支承上。',review_only=True)
 if extra:s.update(extra)
 

 steps.append(s)

def arrow(ids,axis,start_mm=28):
 d=np.asarray(axis,float);center=np.mean([P[i-1].pos*.4 for i in ids],axis=0)
 return dict(part_ids=ids,direction=d.tolist(),from_mm=(center-d*start_mm).tolist(),to_mm=center.tolist())

step('从散件开始：放好竖墙下框',[3],[3],[
 '每臂从167个清单单件开始，包括成品电机和舵机；没有预装核心或隐藏轴组。逐项取件，81侧梁和84销留到底盘阶段。',
 '取第一块64179作为最下层框架，墙面在YZ平面，长边沿Z。用夹具托住，后续向−Y上方逐层搭墙。',
 '本册覆盖全部清单件的装配顺序，不拆成品电机/舵机内部；名义几何不等于实体装配通过。'],
 '本步仅1块下框#3，孔向和编号与图一致。',focus=[3],sub='core_from_parts')
from core_assembly_steps import build_core,build_drive
core_groups,last_core_id=build_core(step,arrow)
# The lower mount is installed before the rotary head. Side access stays open:
# neither the +Z diagonal brace nor the motor output stack is in the way.
WALL=list(range(1,10));MOUNT=[]
def tt(n,title,new,ins,check,axis=None,focus=None,extra=None,visible_extra=(),view=(24,55)):
 MOUNT.extend(new)
 vis=list(dict.fromkeys(WALL+MOUNT+list(visible_extra)))
 step(title,new,vis,ins,check,focus=focus,view=view,arrows=[arrow(new,axis)] if axis and new else (),sub='turntable_lower_mount',extra=extra,turntable_id=n,note='仅画相关框架与本段零件；其余已搭组件独立支承，输出轴尚未装。')
tt(1,'转盘下半：凸台对准上框开口',[34],[
 '断电、空载，把刚搭好的墙架和平台可靠夹住。确认输出轴件#24–29与#86斜撑均为散件，尚未装有齿上半#115。',
 '取#34 18939无齿下半，长方形凸台朝支撑墙，从夹头一侧局部+X沿−X放入最上方64179的开口；圆盘边沿贴框架正面。',
 '凸台两端各3孔应与框架两侧的3个横孔自然同轴。不要靠长销把偏斜凸台硬拉正；暂由夹具保持。'],
 '无齿下半已就位；两侧各3孔可见，输出轴组和侧梁均未挡入口。',axis=[-1,0,0])
tt(2,'下半+Z侧：从外侧插三根蓝长销',[35,36,37],[
 '在局部+Z外侧，将#35/#36/#37三根6558分别对准上、中、下3孔；逐根沿−Z平推。',
 '每根长的2孔段朝内，依次穿框架侧壁与下半凸台端壁；挡肩停在框架外面，短的1孔段朝+Z外露。',
 '三根分别位于局部Y=-8、0、+8毫米，不省略中间销。此时不得先装#41侧梁或#86斜撑。'],
 '三销肩贴框架外侧，3个短段均外露；下半保持夹具支承。',axis=[0,0,-1])
tt(3,'下半−Z侧：从外侧插另三根蓝长销',[38,39,40],[
 '输出轴件#24–29仍未装。站到局部−Z侧，把#38/#39/#40逐根沿+Z装入另3孔。',
 '长的2孔段向内穿框架与凸台，挡肩留在框架外表面；短的1孔段向−Z外露。',
 '中间#39的直线入口原本与输出轴位置相交，不能在轴组已接电机时硬插；两侧合计使用6根6558。'],
 '两侧各3根6558均到挡肩，无销肩被推过闭合宿主；输出轴组仍未接。',axis=[0,0,1],view=(24,135))
tt(4,'中框侧孔：先预插五根黑销',[42,43,46,47,48],[
 '两根40490侧梁都暂不装。中间64179框的+Z侧只在上、中两孔预插#42/#43，沿−Z插半根；下孔对应侧梁第8孔，留给#44长销。',
 '−Z侧上、中、下3孔依次预插#46/#47/#48，沿+Z插半根。所有2780中央挡圈停在框架外面。',
 '五根销另一半朝外露出，稍后由侧梁套住。不能先封梁后把挡圈强推穿过两层孔。'],
 '2＋3共5根黑销；+Z侧最下孔仍空，挡圈全部在框架外侧。',extra={'insertion_order_groups':[[42,43],[46,47,48]],'insertion_vectors_mm':[arrow([42,43],[0,0,-1]),arrow([46,47,48],[0,0,1])]})
tt(5,'−Z侧梁：同时套住六个露出销段',[45],[
 '取#45 40490 9L梁，沿墙的上下方向摆正，孔轴沿Z。输出轴组仍在机外，给侧梁保留直线入口。',
 '从−Z外侧沿+Z平推：从上端数，第1至3孔同时套#38–40短段，第6至8孔套#46–48黑销；第4、5、9孔不接销。',
 '六孔自然对准后才均匀压到销肩；不要用梁扭转或拉拢错位的上下框。'],
 '9L梁第1–3孔接固定长销、第6–8孔接中框黑销，六处均贴合。',axis=[0,0,1],view=(24,135))
tt(6,'+Z侧梁：套上三长销和两黑销',[41],[
 '取#41另一根40490 9L梁，从+Z外侧沿−Z靠近墙体；#86斜撑尚未安装。',
 '从上端数，第1–3孔套#35–37短段，第6/7孔套#42/#43黑销，第8孔与中框空孔同轴，留给#44。',
 '先逐处核对5个销尖，再均匀压到挡肩。两侧梁第4、5、9孔均不接销。'],
 '五个连接点齐平，第8孔未被黑销占用；斜撑仍在机外。',axis=[0,0,-1])
tt(7,'+Z下端长销：留出斜撑连接段',[44],[
 '#41梁已在位后，才从+Z外侧沿−Z插入#44 6558；长的2孔段穿侧梁第8孔并接中框。',
 '挡肩停在侧梁外表面，短的1孔段朝+Z露出，专门用于#86斜撑第1孔。',
 '不能把#44提前放在框架里再强压侧梁，也不能让它的挡肩穿过已装斜撑。'],
 '#44长段接梁与中框，短段向外；#86还未装。',axis=[0,0,-1])
tt(8,'斜撑最后：两孔同时套两根销',[86],[
 '确认前面已装的平台黑销#85在位，露出段与#44短段都朝+Z。取#86 32524七孔梁，保持图示斜向。',
 '从+Z外侧沿−Z平推：第1孔套#44短段，第6孔套平台#85露出段；两孔中心距5孔距，不能误用第7孔。',
 '两点同时自然对齐后轻压到挡圈。斜撑此时才闭合；不得用它强拉框架或平台。'],
 '斜撑第1/6孔都就位，挡圈留在宿主之间；其余已搭组件继续独立支承。',axis=[0,0,-1],visible_extra=[51,85])
build_drive(step,arrow,last_core_id+1)
step('转盘与传动：完成动力底架核对',[],ASSEMBLED_CORE,[
 '前述步骤已从单件装完90件动力底架，包括墙、电机架、平台、舵机架、竖支脚、十字块与输出传动。此处不再取零件。',
 '转盘六根销、两侧梁和斜撑已到位；曲柄与连杆末端仍未连接，接口81/84仍为散件。',
 '输出轴、半套、整套、齿轮顺序逐项核对；不得将近似舵机外形或名义小间隙视为实物通过。'],
 '90件已引入且无重复；下面继续原夹头流程。',focus=DRIVE_INPUT,view=(24,135),sub='turntable_lower_mount',turntable_id=9)
step('独立搭建−Z侧板组件',SIDE_M,SIDE_M,[
 '把#108五孔内梁与#109三孔内梁分别定位；−Z侧五孔段在局部+Y，三孔段在−Y。将#111～#113三根6558的短段插入内梁，挡肩留在内梁外侧。',
 '将#106/#107两根32526压到长销的露出段上，长臂沿推杆方向、短臂朝夹指根轴。先在对应L梁孔预装#114黑销，再压上#110外侧七孔梁。',
 '三根蓝销贯穿三层；黑销仅连接外侧两层。保留根轴孔及60483固定孔，组件仍在机外夹具上。'],
 '本组件9件；长短内梁位置与图一致，所有销肩留在宿主接面。',view=(22,135),sub='side_minus')
step('独立搭建+Z侧板组件',SIDE_P,SIDE_P,[
 '+Z侧长短内梁与上一组件相反：#99五孔段在局部−Y，#100三孔段在+Y。把#102～#104三根6558短段插入内梁。',
 '将#97/#98两根32526压到长销上；先把#105黑销装在对应L梁孔，再压上#101外侧七孔梁。',
 '本组件暂存机外；先完成另一侧根轴叠层，再把本组件整体装到转盘。'],
 '本组件9件，两个组件共18件。两侧长短段不能照同一方向复制。',sub='side_plus')
step('转盘上半与中央导向块就位',[115,116],[115,116],[
 '取#115有齿转盘上半，正面凸耳朝夹指。将#116导向块从正面放进两个凸耳之间，中心孔与转盘轴线重合。',
 '导向块两条侧孔对准两侧凸耳上下孔。仅作定位并用夹具托住，下一步用销连接。'],
 '中心孔畅通；凸耳中间孔未用。',[115,116],sub='turntable')
step('先插四根转盘长销',[117,118,119,120],TT,[
 '从两侧凸耳外面各装2根6558，长的2孔段向内穿凸耳并接导向块。',
 '挡肩贴住凸耳外表面，短的1孔段向外露出，留给侧板后端。此时两侧板均未装到转盘。'],
 '四销都已到挡肩；不能先封侧板再把挡肩强推过孔。',arrows=[arrow([119,120],[0,0,1]),arrow([117,118],[0,0,-1])],sub='turntable')
MAIN=TT+SIDE_M
step('先接−Z侧板，+Z侧保持开放',[],MAIN,[
 '取已完成的−Z侧板，从局部−Z外侧沿+Z靠近转盘，使两根L梁的后端孔套住#119/#120露出的短销段。',
 '均匀压到销肩，持续独立托住侧板和转盘。+Z侧板仍单独放置，不提前封合。'],
 '本组件15件；两根根轴从+Z侧仍有装入夹指和整轴套的空间。',focus=SIDE_M,arrows=[arrow(SIDE_M,[0,0,1])])
for label,root,jaw,bushm,bushp,halfm,halfp,pinm,pinp,brm,brp in [('A',122,121,123,124,125,126,127,128,164,165),('B',130,129,131,132,133,134,135,136,166,167)]:
 sy='+Y' if label=='A' else '−Y'
 MAIN += [pinm,brm]
 step(f'{label}根轴−Z侧：固定销与60483',[pinm,brm],MAIN,[
 f'{label}对应局部{sy}。先将#{pinm}黑色2780从−Z侧沿+Z插入内梁端孔半根，挡圈停在内梁外表面。',
 f'将#{brm} 60483从同侧装到黑销露出段：圆孔接2780，十字孔与相邻根轴孔同轴；两孔中心距8毫米。',
 '此时十字孔还没有根轴。夹具托住支架，不能用单销悬挂它或靠扭转对相位。'],
 '60483圆孔已接销，十字孔对根轴线；支架贴合内梁。',focus=[pinm,brm],view=(23,133),arrows=[arrow([brm],[0,0,1])])
 MAIN += [root,halfm]
 step(f'{label}根轴：建立穿轴支点',[root,halfm],MAIN,[
 f'先把#{halfm}半轴套套在#{root} 8L根轴的−Z端，再沿+Z把轴穿过60483十字孔与−Z内梁圆孔；夹具保持支架与轴同线。',
 '半套停在60483外侧；根轴伸入尚未封合的+Z侧。根轴十字相位应自然通过60483，不能旋扭支架来强行咬合。'],
 '轴穿过一侧60483和内梁，外侧半套到位；未连接端由夹具支承。',focus=[root,halfm],view=(24,133),arrows=[arrow([root],[0,0,1],42)])
 MAIN += [bushm,jaw,bushp]
 step(f'{label}根轴：依次装整套、夹指、整套',[bushm,jaw,bushp],MAIN,[
 f'从开放的+Z端，沿−Z依次套上#{bushm}整轴套、#{jaw}红色7孔夹指的第4圆孔、#{bushp}整轴套。',
 '每只整套厚8毫米；夹指圆孔厚8毫米。三件在两侧内梁之间构成24毫米叠层，先由夹具支承，不依靠摩擦锁紧。',
 '夹指朝魔方方向，保持本图的正常近闭合分支；图示约3.84°，不反向翻折。'],
 '内侧顺序为整套／夹指圆孔／整套；+Z侧板仍独立暂存。',focus=[bushm,jaw,bushp],arrows=[arrow([bushm,jaw,bushp],[0,0,-1],35)])
MAIN += SIDE_P
step('合上+Z侧板组件',[],MAIN,[
 '同时托住两根根轴、夹指与四只整轴套。把已完成的+Z侧板从+Z外侧沿−Z靠近。',
 '侧板前端两个根轴孔分别套住A/B轴；后端两根L梁孔同时套住#117/#118转盘长销短段，均匀压至销肩。',
 '四处必须自然对齐；不能用侧板把歪斜轴套硬挤进空隙。若侧板无法无强力就位，停下复核支承和孔向。'],
 '两根轴均穿过两侧内梁，四只整轴套与两夹指在位；+Z端60483与半套尚待安装。',focus=SIDE_P,arrows=[arrow(SIDE_P,[0,0,-1],40)])
for label,pin,br,half in [('A',128,165,126),('B',136,167,134)]:
 MAIN += [pin,br]
 step(f'{label}根轴+Z侧：装60483',[pin,br],MAIN,[
 f'先从+Z外侧沿−Z把#{pin}黑销插入内梁端孔半根，挡圈停在内梁与支架的接面。',
 f'将#{br} 60483十字孔对根轴、圆孔对黑销，同时平推到位；十字孔与圆孔各接合8毫米。保持根轴另一端半套在位。'],
 '两点同时贴合；没有推动根轴或把销挡肩强推穿过宿主。',focus=[pin,br],arrows=[arrow([br],[0,0,-1])])
 MAIN += [half]
 step(f'{label}根轴+Z半套与64毫米叠层',[half],MAIN,[
 f'从+Z端沿−Z套上#{half}半轴套，停在60483外侧。不要用半套压紧夹指或拉拢结构。',
 '从−Z到+Z：半套4＋60483 8＋内梁8＋整套8＋夹指8＋整套8＋内梁8＋60483 8＋半套4＝64毫米，恰好占满8L根轴。',
 '名义轴向余量为零。自由转动和可靠防脱是否兼容必须实测；任何卡死、松脱或轴端接合不足都停止。'],
 '两端半套齐全；64毫米零名义余量已记录，未把几何吻合当作实体验收。',focus=[half],arrows=[arrow([half],[0,0,-1])],extra={'root_stack_mm':[4,8,8,8,8,8,8,8,4],'nominal_axial_reserve_mm':0})
for label,beam0,beam1,axle,h0,h1,pin,wheelax,hub,tyre in [('A',137,138,139,140,141,142,143,144,145),('B',146,147,148,149,150,151,152,153,154)]:
 step(f'{label}轮胎与轮毂预装',[hub,tyre],[hub,tyre],[
 f'把#{tyre}轮胎套在#{hub}轮毂上，确认胎圈均匀就座。将这2件组件暂存在机外。',
 '每臂两组独立轮胎压头；轮胎网格是名义14×6毫米尺寸，实际橡胶形变和摩擦未验证。'],
 '2件组件同心，轮毂中孔保持畅通。',sub='wheel_'+label)
 MAIN += [beam0,axle,h0,pin]
 step(f'{label}压头：先装−Z薄梁与两连接点',[beam0,axle,h0,pin],MAIN,[
 f'把#{beam0}四孔薄梁贴在红色夹指−Z侧。薄梁第1十字孔对夹指第6孔，用#{axle} 3L轴贯穿，并在−Z端加#{h0}半套。',
 f'薄梁第2圆孔对夹指第7孔，从−Z侧插#{pin} 32054，挡套停在第一根薄梁外侧；露出的轴和销给另一侧薄梁使用。',
 '薄梁第3圆孔留空，第4十字孔用于轮轴；+Z侧薄梁下一步安装。'],
 '薄梁由两个连接点定位，挡套在正确外侧；轮胎组件仍单独托住。',focus=[beam0,axle,h0,pin],view=(25,132),arrows=[arrow([axle,pin],[0,0,1])])
 MAIN += [wheelax,hub,tyre,beam1,h1]
 step(f'{label}压头：轮轴、轮胎与+Z薄梁',[wheelax,beam1,h1],MAIN,[
 f'把#{wheelax} 2L轮轴穿过−Z薄梁第4十字孔，套入已准备的轮胎／轮毂组件；轮毂位于夹指中面。',
 f'把#{beam1} +Z薄梁同时对准3L轴、32054销和2L轮轴三个连接点，沿−Z平直压到位，再在3L轴+Z端套#{h1}半套。',
 '2L轮轴两端与薄梁外侧齐平，不加外轴套。检查轮毂能绕固定轴自由转动；不能靠挤压薄梁消除间隙。'],
 '本夹指轮胎压头9件齐全，两个3L轴半套和32054挡套到位。',focus=[wheelax,hub,tyre,beam1,h1],arrows=[arrow([beam1],[0,0,-1])])
MAIN += [160,162]
step('先把无摩擦销各插入夹指半根',[160,162],MAIN,[
 '两根黄色连杆尚未接到夹指。A夹指第2孔先从+Z侧沿−Z插#160灰色3673半根；B夹指第2孔从−Z侧沿+Z插#162半根。',
 '两个中央挡圈都留在夹指外表面，销的另一半露出，供下一步各自的连杆圆孔套接。',
 '夹指和已装头部由夹具支承。不能把销推穿夹指后再把挡圈强推通过连杆。'],
 'A/B两销肩分别在+Z/−Z夹指外表面，露出段方向相反。',focus=[160,162],arrows=[arrow([160],[0,0,-1]),arrow([162],[0,0,1])])
MAIN += [159,161]
step('两根黄色连杆分别从各自外侧套销',[159,161],MAIN,[
 '先从+Z外侧沿−Z把#159连杆一端套到A销#160的露出段，直到与夹指之间的销肩接触。',
 '再从−Z外侧沿+Z把#161连杆一端套到B销#162的露出段。两根连杆分别装入，不把它们预先连成刚性组件一起硬推。',
 '两连杆自由端由夹具托在十字接头位置。保持正常近闭合分支；下一步用横轴连接中间三个孔。'],
 '两销肩停在各自的夹指与连杆接面，连杆可绕无摩擦销转动。',focus=[159,161],arrows=[arrow([159],[0,0,-1]),arrow([161],[0,0,1])])
MAIN += [155,156,157,158]
step('连接十字接头横轴与两端半套',[155,156,157,158],MAIN,[
 '用夹具保持两连杆自由端同轴，在中间放#155 32013，横圆孔对准两个连杆端孔，纵向十字孔朝后接推杆。',
 '在#156 4L横轴−Z端预套#157半套；从−Z沿+Z依次穿过#161连杆、32013横圆孔和#159连杆，再从+Z端套#158半套。',
 '轴本体穿圆孔，无销挡肩经过闭合孔。两半套停在连杆外侧，不能压死连杆；十字接头在两连杆朝魔方的一端。'],
 '横轴与两端半套齐全，三处圆孔自然同轴；纵向十字孔仍畅通。',focus=[155,156,157,158],arrows=[arrow([156],[0,0,1])])
step('离机接合机械头与90件动力核心',[],sorted(set(MAIN+ASSEMBLED_CORE)),[
 '转盘下半固定及轴组接入已按前述步骤完成，90件动力底架、机械头及未闭合的曲柄／连杆分别独立支承。将转盘上半对准核心的下半扣合；同时保持齿轮与转盘的名义啮合位置。',
 '#94曲柄端轴和#95半套尚未安装，因此黄色舵机连杆不会把推杆强制锁在舵机角度上。',
 '此时整臂仍在底盘外，#81侧梁和#84底框销仍在专格。扣合所需空间、卡扣力及实体啮合必须另行验证。'],
 '转盘上下半及导向孔同轴；曲柄与连杆未连接，推杆通道未封闭。',focus=TT,sub='merge_core')
MAIN=sorted(set(MAIN+ASSEMBLED_CORE+[88,89,163]))
step('从后方穿12L推杆及两只半套',[88,89,163],MAIN,[
 '把#88/#89两只半套分别用夹具定位在十字块#87的前后，孔轴线对准导向框前孔；曲柄端仍不连接。',
 '#163 12L轴从平台后方沿+X穿入：导向框后孔只借道，再依次通过后半套、十字块圆孔、前半套、导向框前孔、转盘中心及#116导向块，最后插进#155十字孔到底。',
 '图示为完成位置，后导向孔不承载推杆。自然移动未连接的十字块／连杆帮助对孔，不反驱舵机；两半套不把滑动机构夹死。'],
 '推杆前端名义进入十字接头8毫米；两个导向处畅通、两半套就位。',focus=[88,89,163],arrows=[arrow([163],[1,0,0],62)],sub='pushrod')
MAIN += [94,95];MAIN=sorted(MAIN)
step('匹配名义姿态后连接曲柄端',[94,95],MAIN,[
 '先核对舵机曲柄#93已由另行验证的定位流程处于所需姿态。本页仅表达断电、空载、孔位自然对齐时的机械连接；不提供上电归零或脉宽标定。',
 '保持夹指和推杆在图示正常近闭合分支，让#96连杆端孔与曲柄末端孔自然同轴，再插#94 2L轴：外端与曲柄外面齐平；内端装#95半套贴住连杆。',
 '孔位不自然重合、需要硬拉连杆或反驱舵机时立即停止，保持分离和支承，等待专门定位／标定；不能把本页当作定位已完成的证据。'],
 '只有预先满足自然对孔条件才记录此步完成；否则整臂仍标为待验证。',focus=[93,94,95,96],sub='crank_close',extra={'conditional_step':True,'requires_independently_validated_servo_pose':True})
step('单臂165件待接底盘，2件留待接口',[],MAIN,[
 '核对已完成的90件动力底架与75件夹头件共165件；每头4件60483、2根8L根轴、4只根轴整套、4只根轴外半套和4枚支架固定销齐全。',
 '#81 40490侧梁与#84 2780销保持散件状态，待整臂落到底盘后先装#84、再装#81，使每臂达到167件；不要提前装这两件。',
 'R、L、F、B四臂分别在机外完成同一局部流程。各臂独立记录；四臂最终合计668件，不以一个臂通过代替其余三臂。',
 '64毫米根轴叠层零名义余量；夹指正常约3.84°～25°。装配路径、保持、载荷、控制联锁和实体开合均未放行。'],
 '165件在位＋2件专格＝167件／臂；不插电、不带魔方，仍需实体验证。',focus=[122,125,126,130,133,134,164,165,166,167],sub='staged_complete',extra={'ready_for_base_mount_part_count':165,'deferred_interface_part_ids':DEFER})
assert all(set(s['visible_part_ids'])<=set(s['introduced_part_ids']) for s in steps)
assert all(s['visible_part_ids']==[r['index1'] for r in s['geometry_records']] for s in steps)
assert introduced==set(range(1,168))-set(DEFER)
assert collections.Counter(i for s in steps for i in s['added_part_ids'])==collections.Counter(ADDED)
assert set(steps[-1]['visible_part_ids'])==introduced
BOOK=dict(title='60483机械头最终版直接装配',revision='FINAL-ASSEMBLY-2026-10-09-FULL-PARTS',review_only=True,units='LDraw: 1 LDU = 0.4 mm',local_frame='L module frame; A=+Y, B=-Y; each arm uses its corresponding ARM_ROT without mirroring',prerequisites=dict(prebuilt_core_count=0,prebuilt_core_part_ids=CORE,prebuilt_core_bom=bom(CORE),prebuilt_core_geometry_records=record(CORE),prebuilt_input_groups=[],turntable_mount_loose_part_ids=TURNTABLE_MOUNT,explicitly_loose_head_and_transmission_count=165,explicitly_loose_head_and_transmission_part_ids=ADDED,explicitly_loose_head_and_transmission_bom=bom(ADDED),deferred_interface_count=2,deferred_interface_part_ids=DEFER,deferred_interface_bom=bom(DEFER),deferred_interface_geometry_records=record(DEFER),total_parts_per_arm=167,arms=['R','L','F','B'],four_arms_total=668,independent_offline_assembly=True,original_core_from_scratch_covered=True,initial_crank_and_servo_link_connected=False,core_input_condition_zh='无预装输入：按步骤从清单单件搭建。成品电机和舵机作为采购件，内部不拆解。曲柄定位、真实舵机接口与实体装配须另行验证。'),rows=ROWS,steps=steps,validation=dict(step_count=len(steps),core_count=0,introduced_count=165,deferred_count=2,staged_count=165,final_arm_count=167,four_arms_count=668,added_instances_exactly_once=True,final_staged_set_exact=True,mechanical_geometry_changed=False,physical_verification=False,continuous_insertion_verification=False),reference_images={'opening':'final-head-diagrams/opening.png'},source=dict(model_file='candidate.py',model_sha256=hashlib.sha256((MECHANICAL/'candidate.py').read_bytes()).hexdigest(),native_source_file='source/baseline_model.py',native_source_sha256=hashlib.sha256((MECHANICAL/'inputs/baseline_model.py').read_bytes()).hexdigest(),native_source_steps_used=list(range(1,19)),pose=dict(open_s=0,whole_head_angle_deg=0),source_instance_numbering='candidate.module(0,0,False,True), indices 1..167',generator='manual/build_final_head.py'))


def render(book,select=None):
 os.environ.setdefault('MPLCONFIGDIR','/tmp/mpl-final-head')
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 from matplotlib.colors import to_rgb
 from matplotlib import font_manager
 from mpl_toolkits.mplot3d.art3d import Poly3DCollection
 from mpl_toolkits.mplot3d import proj3d
 font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
 font_manager.fontManager.addfont(font)
 plt.rcParams['font.family']=font_manager.FontProperties(fname=font).get_name()
 plt.rcParams['axes.unicode_minus']=False
 out=H/'final-head-diagrams';out.mkdir(exist_ok=True)
 mesh={i:C.world(p)[:, :,[2,0,1]].copy() for i,p in enumerate(P,1)}
 for t in mesh.values():t[:,:,2]*=-1
 light=np.array([.38,-.53,.76]);light/=np.linalg.norm(light)
 ink='#183b4d';teal='#008f8b';gold='#d29326';gray='#a5b0ba';bg='#fafbf9'
 def xyz(v):v=np.array(v)[[2,0,1]].copy();v[2]*=-1;return v
 def draw(ax,ids,focus,view,arrows=(),limits_ids=None):
  ax.set_facecolor(bg)
  for i in ids:
   t=mesh[i];norm=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);norm/=np.maximum(np.linalg.norm(norm,axis=1,keepdims=True),1e-10)
   base=teal if P[i-1].name=='60483.dat' else gold if i in focus else gray
   rgb=np.array(to_rgb(base))[None,:]*(.46+.53*np.abs(norm@light))[:,None]
   ax.add_collection3d(Poly3DCollection(t,facecolors=rgb,edgecolors='none',linewidth=0,rasterized=True,zsort='average'))
  pts=np.concatenate([mesh[i].reshape(-1,3) for i in (limits_ids or ids)])
  if arrows:pts=np.concatenate([pts,np.array([xyz(a[k]) for a in arrows for k in ['from_mm','to_mm']])])
  lo=pts.min(0);hi=pts.max(0);mid=(lo+hi)/2;span=np.maximum(hi-lo,16)*1.13
  ax.set(xlim=(mid[0]-span[0]/2,mid[0]+span[0]/2),ylim=(mid[1]-span[1]/2,mid[1]+span[1]/2),zlim=(mid[2]-span[2]/2,mid[2]+span[2]/2))
  ax.set_box_aspect(span,zoom=1.14);ax.view_init(view['elev'],view['azim']);ax.set_proj_type('ortho');ax.axis('off')
  for a in arrows:
   u=proj3d.proj_transform(*xyz(a['from_mm']),ax.get_proj());v=proj3d.proj_transform(*xyz(a['to_mm']),ax.get_proj())
   ax.annotate('',xy=v[:2],xytext=u[:2],arrowprops=dict(arrowstyle='-|>',lw=2.1,color='#2672a4',mutation_scale=15),zorder=1000)
 audits=[]
 for s in book['steps']:
  if select and s['number'] not in select:continue
  fig=plt.figure(figsize=(10,6.3),facecolor=bg)
  fig.text(.035,.948,f'{s["diagram_label"]}  {s["title"]}',size=16.5,color=ink,weight='bold')
  fig.text(.035,.903,'最终版直接装配  |  青绿：60483；金色：本步件；灰色：相关已装件',size=10,color=ink)
  ids=s['visible_part_ids'];focus=s['highlight_part_ids'] or ids
  ax=fig.add_axes([.00,.115,.70,.75],projection='3d');draw(ax,ids,focus,s['view'],s['insertion_vectors_mm'])
  fig.text(.72,.83,'本步件／接口局部',size=10.5,color=ink)
  ax2=fig.add_axes([.685,.285,.315,.48],projection='3d')
  draw(ax2,focus,focus,s['view'])
  inventory=' / '.join(f'#{i} {P[i-1].name.removesuffix(".dat")}' for i in focus)
  if len(focus)>12:inventory=f'{len(focus)}件组件；编号见对应零件表'
  import textwrap
  fig.text(.708,.25,'\n'.join(textwrap.wrap(inventory,29)),size=8.2,color=ink,va='top')
  fig.text(.035,.075,s['diagram_note'],size=9.2,color=ink)
  fig.text(.035,.032,'真实LDraw零件网格；方向箭头为示意；连续路径／插入力／保持／实体装配未验证。',size=8.6,color='#64787c')
  path=H/s['image'];fig.savefig(path,dpi=140,facecolor=bg);plt.close(fig)
  audits.append(dict(step_id=s['id'],image=s['image'],sha256=hashlib.sha256(path.read_bytes()).hexdigest(),rendered_instance_indices1=ids,focus_indices1=focus,geometry_record_count=len(s['geometry_records']),rendering_source='candidate.world() native LDraw triangles',model_pose='open_s=0, angle=0',step_data_sha256=hashlib.sha256(json.dumps(s,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),no_mesh_substitutes=True))
  
  if s['number']==len(book['steps']):
   import shutil
   shutil.copyfile(path,out/'complete.png')
  print(f'Rendered {s["number"]:02d}/{len(book["steps"])}',flush=True)
 ap=H/'final-head-render-audit.json'
 prior=json.loads(ap.read_text()) if ap.exists() and select else []
 by={x['step_id']:x for x in prior}
 by.update({x['step_id']:x for x in audits})
 ap.write_text(json.dumps(list(by.values()),ensure_ascii=False,indent=2))

def render_references():
 os.environ.setdefault('MPLCONFIGDIR','/tmp/mpl-final-head')
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 from matplotlib import font_manager
 from matplotlib.colors import to_rgb
 from mpl_toolkits.mplot3d.art3d import Poly3DCollection
 font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
 font_manager.fontManager.addfont(font);plt.rcParams['font.family']=font_manager.FontProperties(fname=font).get_name()
 fig=plt.figure(figsize=(10,6.3),facecolor='#fafbf9')
 fig.text(.035,.94,'最终版夹指开合参考',fontsize=18,color='#183b4d',weight='bold')
 fig.text(.035,.895,'仅改变夹指开角；两幅整头回转角均为0°。',fontsize=11,color='#183b4d')
 records=[]
 for k,o in enumerate([0,C.m.OPEN_S]):
  pp=C.module(o,0,False,True);ids=list(range(97,163))+list(range(164,168))
  ax=fig.add_axes([.01+.5*k,.145,.49,.66],projection='3d');ax.set_facecolor('#fafbf9')
  ts=[]
  for i in ids:
   p=pp[i-1];t=C.world(p)[:,:,[2,0,1]].copy();t[:,:,2]*=-1;ts.append(t)
   n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);n/=np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-10)
   col='#008f8b' if p.name=='60483.dat' else '#ce6060' if p.color==4 else '#a5b0ba'
   colors=np.array(to_rgb(col))[None,:]*(.46+.53*np.abs(n@np.array([.38,-.53,.76])))[:,None]
   ax.add_collection3d(Poly3DCollection(t,facecolors=colors,edgecolors='none',linewidth=0,rasterized=True))
  pts=np.concatenate([t.reshape(-1,3) for t in ts]);lo=pts.min(0);hi=pts.max(0);mid=(lo+hi)/2;span=np.maximum(hi-lo,10)*1.13
  ax.set(xlim=(mid[0]-span[0]/2,mid[0]+span[0]/2),ylim=(mid[1]-span[1]/2,mid[1]+span[1]/2),zlim=(mid[2]-span[2]/2,mid[2]+span[2]/2))
  ax.set_box_aspect(span,zoom=1.1);ax.view_init(21,55);ax.set_proj_type('ortho');ax.axis('off')
  fig.text(.25+.5*k,.815,['名义近闭合 ≈3.8417°','正常最大开角 25°'][k],ha='center',fontsize=13,color='#183b4d')
  records.append(dict(open_s=float(o),whole_head_angle_deg=0,visible_part_ids=ids,geometry_records=[dict(index1=i,name=pp[i-1].name,color=pp[i-1].color,position_ldu=pp[i-1].pos.tolist(),rotation=pp[i-1].rot.tolist()) for i in ids]))
 fig.text(.035,.083,'夹指开合与整个机械头回转分别定义；不把自然端点当归零点或工作上限。',fontsize=10,color='#183b4d')
 fig.text(.035,.034,'64毫米根轴叠层零名义余量；保持力、实体开合及控制联锁仍未验证。',fontsize=9.5,color='#64787c')
 path=H/'final-head-diagrams/opening.png';path.parent.mkdir(exist_ok=True);fig.savefig(path,dpi=140,facecolor='#fafbf9');plt.close(fig)
 (H/'final-head-opening-audit.json').write_text(json.dumps(dict(image='final-head-diagrams/opening.png',sha256=hashlib.sha256(path.read_bytes()).hexdigest(),states=records),ensure_ascii=False,indent=2))
 print('Rendered final opening reference',flush=True)

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--data-only',action='store_true');ap.add_argument('--render-only',action='store_true');ap.add_argument('--select',type=int,nargs='*');ap.add_argument('--references-only',action='store_true');args=ap.parse_args()
 if not args.render_only:
  (ASSEMBLY/'final-head-steps.json').write_text(json.dumps(BOOK,ensure_ascii=False,indent=2))
  print(f'Final head: {len(steps)} steps; prebuilt0 +165 =165, deferred2 =>167',flush=True)
 if not args.data_only and not args.references_only:render(BOOK,set(args.select) if args.select else None)
 if not args.data_only and (args.references_only or not args.select):render_references()
