"""Rebuild the continuous 130-part support and approved 20-part lever sequence."""
from pathlib import Path
import sys,json,copy,re,hashlib
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent));import candidate as C
S=H.parent/'source/manual-inputs'
g=json.loads((S/'support-source-steps.json').read_text());old={r['index1']:r for r in C.original_rows};new={r['id']:r for r in C.rows};mapping={i:new[r['id']]['index1'] for i,r in old.items() if r['id']in new}
for i in [67,72,69,74]:mapping[i]=new['center_double_web'+str(-8 if i in [67,72]else 8)]['index1']
def mid(ids):return list(dict.fromkeys(mapping[i]for i in ids if i in mapping))
def txt(s):return re.sub(r'#(\d+)',lambda m:'#'+str(mapping[int(m[1])]) if int(m[1])in mapping else m[0],s)
steps=[]
for src in g['steps']:
 s=copy.deepcopy(src);n=s['number']
 if n==79:continue # Both working locks are removed, never fitted in R3.
 for key in ['added_part_ids','visible_part_ids','highlight_part_ids']:s[key]=mid(s[key])
 for key in ['instructions_zh','cautions_zh']:s[key]=[txt(t).replace('需手扶','需独立夹具支承') for t in s[key]]
 for side,oldidx,minimum in [('R',44,19),('L',55,25)]:
  idx=new[side+'_bridge_outer_thin']['index1']
  if n>minimum and mapping[oldidx]in s['visible_part_ids']:s['visible_part_ids'].append(idx)
  if n>minimum and mapping[oldidx]in s['highlight_part_ids']:s['highlight_part_ids'].append(idx)
 for arrow in s['insertion_vectors_mm']:
  arrow['part_ids']=mid(arrow['part_ids']);arrow['nominal_travel_mm']=None;arrow['note_zh']='方向示意；整机连续安装路径及所需行程未验证。'
 if n in [18,24]:
  pin=mapping[45 if n==18 else 56];s['title_zh']=('右'if n==18 else'左')+'桥端：8加8毫米普通销'
  s['instructions_zh']=[f'将#{pin} 2780普通2L销的一半8毫米插入上桥梁端孔，另一半8毫米留给两片11478。','本版不用旧32002半销；不能继续套用原4毫米露出端的说明。']
 if n in [19,25]:
  side='R'if n==19 else'L';idx=new[side+'_bridge_outer_thin']['index1'];s['added_part_ids']+=[idx];s['visible_part_ids']+=[idx];s['highlight_part_ids']+=[idx]
  s['title_zh']=('右'if n==19 else'左')+'桥端：双片11478形成8毫米叠层'
  s['instructions_zh']=[f'先装原内片#{mapping[44 if n==19 else 55]}，再从外侧装新薄梁#{idx}。两片各厚4毫米，2780同时占满两片圆孔。','保持两圆孔同轴；右端外片向世界-Z偏4毫米，左端向+Z偏4毫米。不得装到内侧。','保留原5L（40毫米）连接轴；轴与外侧半套随外片向外移4毫米。名义叠层40毫米，端部零余量，仍须验证转动与防脱。']
 if n in [32,33]:
  x=-8 if n==32 else 8;idx=new['center_double_web'+str(x)]['index1'];s['title_zh']=('左'if x<0 else'右')+'中央列：一件43857替代两件18654'
  s['instructions_zh']=[f'在中央腹板相邻一孔距X={x}毫米处放#{idx} 43857。上下圆孔位于Y=56和64毫米，共用一个厚8毫米实体。','将本列两根长销的长段沿+Z穿过43857和左桥梁；销肩保持同一接缝。','此处不装原两只18654；不可把43857实体中心误对到其中单孔。']
 if n==1:
  s['title_zh']='130件支承从散件开始'
  s['instructions_zh']=['20件杠杆已按前面阶段装好。先把空杠杆缓慢转到上位参数0毫米并用夹具固定，再搭130件支承。最终共150件；近侧+Z、右+X、上方-Y。','底盘和四个机械臂必须固定齐备。桥梁从横轴下方围合，H托台随后装在横轴上方；不能把已闭合130件托盘整体往下套过U架。','本版不装两枚旧工作锁销。若从旧机改装，必须先断电、移除魔方并独立托住空托盘，才一次性拆下两锁销。之后不再装回。','图中蓝色为新件或合并件；灰色为相关已装件。实例编号#1至#150来自同版模型。']
  s['cautions_zh']=['完整安装扫掠、承重、滑动和半轴套保持均未实测。']
 if 16<=n<=33:
  s['assembly_location']='off_machine'
  s['instructions_zh'].insert(0,'在机外单独装半桥；图示相对孔位，无原机背景。不要在U杠杆已经占位时就地插这些销或适配梁。')
 if n==38:
  axle=new['R_axle64']['index1'];neg=new['R_bush64_-22']['index1']
  s['title_zh']='右下轴：先穿裸轴，再从局部放半套'
  s['instructions_zh']=[f'桥保持上位0毫米，由独立夹具支承；H托台尚未装。空U杠杆从参数0轻移到1.6毫米并固定，不靠桥承受装配力。',f'先将#{axle} 32073下轴不带半套，从-Z侧沿+Z送入下排同轴孔。禁止先给该轴预装#{neg}半套再长距离穿入。',f'将松散半套#{neg}放在轴尖旁的局部Z=-26毫米平面：由+X侧横移20毫米到轴线上，再沿+Z仅滑4毫米到Z=-22。','本路径以0.1毫米间隔查过名义零件；不证明手或工具能到达。够不到时停止，不能退回会撞U臂的长距离轴向路径。']
  s['cautions_zh']=['桥0毫米与U参数1.6毫米是不同部件的装配姿态；托盘未装，不能把桥也下降1.6毫米。']
  s['lever_parameter_mm']=1.6;s['tray_drop_mm']=0.0;s['pose_label']='桥上位0；空杠杆参数1.6毫米'
  s['visible_part_ids'] += [new[i]['index1']for i in ['inner_arm_z-32','inner_arm_z32','outer_handle']]
  s['assembly_waypoints']=[{'id':'R_axle64','translations_mm':[[0,0,-40],[0,0,0]]},{'id':'R_bush64_-22','translations_mm':[[20,0,-4],[0,0,-4],[0,0,0]]}]
  s['insertion_vectors_mm']=[]
 if n==39:
  upper=new['R_bush56_14']['index1'];pos=new['R_bush64_14']['index1']
  s['title_zh']='右夹架：正侧下半套从中心侧局部放入'
  s['instructions_zh']=[f'桥仍由夹具保持0毫米，空U仍固定在参数1.6毫米。上轴半套#{upper}沿原上轴端装入，轻贴活动L。',f'下轴半套#{pos}先放到局部Z=+18毫米平面，从中心侧-X横移20毫米到轴线上，再沿-Z只滑4毫米到最终Z=+14。','下半套不能从+X靠近，该侧被原R墙连接件挡住；也不能沿原14毫米长轴向路径穿过U臂。','两轴四半套齐全后，仍独立托住桥。复查零件无移位，再缓慢把空U恢复参数0毫米并用夹具固定，后续托台装在上方。']
  s['cautions_zh']=['局部放半套路径只做名义抽样；手部接近、插入力、防脱与活动L滑动须实測。']
  s['lever_parameter_mm']=1.6;s['tray_drop_mm']=0.0;s['pose_label']='桥上位0；空杠杆参数1.6毫米'
  s['visible_part_ids'] += [new[i]['index1']for i in ['inner_arm_z-32','inner_arm_z32','outer_handle']]
  s['assembly_waypoints']=[{'id':'R_bush56_14','translations_mm':[[0,0,14],[0,0,0]]},{'id':'R_bush64_14','translations_mm':[[-20,0,4],[0,0,4],[0,0,0]]}]
  s['insertion_vectors_mm']=[]
 if n in [60,61,62]:
  s['title_zh']='机外预插座柱根销：'+('远侧四销'if n==60 else'近右两销'if n==61 else'近左下销')
  s['assembly_location']='off_machine'
  s['instructions_zh'].insert(0,'两半桥仍在机外，且中央层与提前装的长轴保持可接近。本页提前到封桥之前，不能等桥已围住U以后再从外侧长距离穿销。')
  s['cautions_zh']=['预插销肩留在桥梁表面，露出段稍后接座柱；半桥要带着这些预插销一起接入。']
 if n in [35,40]:s['instructions_zh']=[v.replace('需用手托住','需独立夹具托住')for v in s['instructions_zh']]
 if n in [39,44]:s['instructions_zh']=[v.replace('继续托住桥，工作锁销仍放在一旁。','继续用独立夹具托住桥；本版不装旧工作锁销。')for v in s['instructions_zh']]
 if n==63:s['cautions_zh']=['这是待侧向合柱的定位状态，需独立支承，尚未锁固。']
 if n==78:
  s['title_zh']='130件空托盘：独立支承下检查导轨'
  s['instructions_zh']=['不放魔方，保持断电和独立支承。先记录所有销肩、轴及半套位置，确认固定接口完整；本版没有工作锁销。','先由独立支承承担托盘，再解除U的装配夹具。外部支承缓控约40.8毫米行程，让已装杠杆同步自由跟随；不能把U固定在上位再压下托盘。头部保持无干涉，遇阻即停。','特别检查约8／32毫米处导向面越过55615销尖及孔缘时，是否挂住、翘起或推力突增。','每次移动复查半套、柱桥与黄色框销肩。不磨销、不改孔，不靠放松到明显侧晃来消除卡滞。']
  s['cautions_zh']=['这是待执行空载检查，未执行也未通过；不代表承重或自动回落能力通过。']
 if n==34:
  s['instructions_zh']=['空U由夹具保持参数0毫米。两半桥的适配梁、中央层及7枚座柱根销已经在机外预装；桥尚未承担载荷。','先独立托住左半桥，按局部名义路线从下方+Y24毫米沿-Y上移到位；输出横轴保持在桥梁上方。右半桥从远侧-Z约8毫米处沿+Z合拢。','上下两排共六孔同时对准中央长销露出短段，销肩仍留在中央接缝。不得先封闭两桥再强推长销肩穿孔。','两半桥就位后继续独立托住桥；H托台稍后从横轴上方放入，不把完整闭合130件托盘套过U。']
  s['cautions_zh']=['半桥局部引入经过名义抽样，不代表人手空间、完整前置拆装或连续扫掠通过。']
  s['visible_part_ids']+= [new[i]['index1']for i in ['end_11L_axle','end_spacer2L_-20','end_spacer2L_20','end_spacer1L_-8','end_spacer1L_8','center_roller_bush']]
 if n==63:
  s['instructions_zh'].append('U杠杆保持上位，由夹具托稳。H座从横轴上方定位，中央3713在H座下方；四柱随后从侧面闭合，不把封闭130件托盘套过U架。')
  s['visible_part_ids']+= [new[i]['index1']for i in ['end_11L_axle','end_spacer2L_-20','end_spacer2L_20','end_spacer1L_-8','end_spacer1L_8','center_roller_bush']]
 if n==80:
  s['title_zh']='130件支承完成后保持空载并检查杠杆'
  s['instructions_zh']=['确认原墙、64件四角闭合底盘及130件支承的固定接口全部到位；整个移动托盘仍由独立夹具可靠托住。','不要放魔方；20件杠杆已在R臂与支承搭建前分阶段装好，再核对三根15L梁、12L支点轴、11L横轴及4件上止挡。','本版没有水平P/Q补强6件，也没有两枚旧工作锁销。新增20件不改变原托台、横梁和导轨几何。','整机安装接近路径、摩擦、保持力、强度及寿命尚未实测。不得在完整整机中强塞U组件；U组件已经在孤立R臂阶段提前接入。']
  s['cautions_zh']=['完成几何装配不等于可以带魔方或带电运行。']
 for arrow in s['insertion_vectors_mm']:
  for side,oldidx,minimum in [('R',44,19),('L',55,25)]:
   idx=new[side+'_bridge_outer_thin']['index1']
   if n>=minimum and mapping[oldidx]in arrow['part_ids'] and idx not in arrow['part_ids']:arrow['part_ids'].append(idx)
 steps.append(s)
assert len(steps)==79
support_count=len(set(i for s in steps for i in s['added_part_ids']));assert support_count==130
lever_seen=[]
def lever(title,ids,instructions,check,context=False,hi=None,arrows=None):
 added=[new[i]['index1']for i in ids];lever_seen.extend(added)
 s=dict(id='GRAVITY-'+str(len(steps)-78).zfill(2),number=0,module_id='lever',title_zh=title,added_part_ids=added,visible_part_ids=list(lever_seen),highlight_part_ids=[new[i]['index1']for i in hi]if hi else added or list(lever_seen),instructions_zh=instructions,cautions_zh=[check],insertion_vectors_mm=arrows or [],external_context='root_host'if context else None)
 steps.append(s)
lever('机外负Z内臂：先预插两根重叠销',['inner_arm_z-32','root_overlap_pin_16','root_overlap_pin_32'],['先在机外搭U组件，图示下位杠杆参数42.4毫米。取32278 15L内臂，支点端为第1孔，输出端第15孔。两根2780先从-Z侧沿+Z进入内臂第3及第5孔。','内臂平面在Z=-32毫米。销肩停在Z=-36毫米接缝，各留8毫米向-Z伸出，下一步接外把手。','这两根销连接两条梁，不是工作锁销。'],'销肩必须留在两梁接缝，不能压过封闭圆孔。')
lever('外把手：从敞开侧合上两销',['outer_handle'],['把外把手远端记为第1孔，支点为第11孔。把手第13、15孔分别对准内臂第3、5孔上的露出销段。','外把手从-Z侧沿+Z直移，两个孔同时套上；最终把手平面Z=-40毫米，两销各连接8+8毫米。','支点孔对齐：内臂第1孔与把手第11孔。两根分开的销让两梁一起运动，不增握把零件。'],'销肩始终处于Z=-36毫米接缝；不得先封梁后再强推销肩穿孔。')
lever('11L横轴：先穿负Z内臂',['end_11L_axle','end_retainer_-38'],['在23948 11L轴的入轴侧预套一只32123a半套。轴为普通直轴，本身没有止挡环。','从-Z侧沿+Z把裸长端穿过负Z内臂第15孔；半套始终留在梁外。最终半套中心Z=-38毫米，轴中心Z=0。','暂不装正Z内臂；横轴的+Z裸端必须保持开放，供后续间隔件依次套入。'],'不得把预装半套、3713轴套或销肩推过闭合梁孔；不靠强压通过。')
lever('横轴负侧：依次套2L和1L间隔件',['end_spacer2L_-20','end_spacer1L_-8'],['从横轴开放的+Z端先套62462 2L间隔件，沿-Z推到负Z内臂内侧；中心最终Z=-20毫米。','再从同一端套18654 1L间隔件，沿-Z滑到前件；中心Z=-8毫米。','该侧名义次序是内臂、2L、1L；所有件均从裸露轴端进入，不横向卡入。'],'保持输出轴受夹具支承；名义贴合不代表滑动阻力和保持力已合格。')
lever('横轴中央和正侧：套滚轮与间隔件',['center_roller_bush','end_spacer1L_8','end_spacer2L_20'],['仍从开放的+Z轴端，依次套3713中央滚轮、18654 1L及62462 2L间隔件。','三件中心依次在Z=0、+8、+20毫米。中央3713位于托台H座正下方，名义托举接触半径约3.6毫米。','3713是原生带棱轴套，用作名义接触件；不是经过实测的精密滚动轴承。'],'先查装配方向和接触位置；不承诺实际滚动、阻力或自动复位。')
lever('正Z内臂：从自由轴端合上',['inner_arm_z32'],['将第二根15L内臂第15孔从横轴+Z自由端套入，沿-Z滑到2L间隔件；最终梁平面Z=+32毫米。','两根内臂均以支点为第1孔、输出为第15孔；两端名义孔距112毫米。','只闭合输出端，支点12L轴尚未插入。用夹具让两根内臂的支点孔保持同轴。'],'不能装好两端封闭架后再横向塞入整串横轴间隔件。')
lever('横轴最后：装正Z外半套',['end_retainer_38'],['从+Z轴端沿-Z装余下32123a半套，最终中心Z=+38毫米，外表面Z=+40毫米。','复核轴向叠层：半套、内臂、2L、1L、中央3713、1L、2L、内臂、半套。','11L原生轴端约Z=±43.8毫米，两端相对半套外面各余约3.8毫米。只轻贴，不额外压紧。'],'这项轴向余量只是网格几何；半套保持力、横轴挠曲和侧隙待实测。')
lever('支点定位：两处原框轴承都要承接',[],['此时右R臂已单独完成60483改装，尚未接底盘、其他三臂或130件支承。右头回转50度、夹指开25度；断电并用夹具固定。','13件U组件保持下位姿态（杠杆参数42.4毫米）。从中心一侧世界-X进入，沿+X水平平移到右臂；名义检查路径由X偏移-260毫米到0。','最终支点线X=112、Y=80毫米，沿Z；原下层64179两孔在Z=±24毫米，内臂在±32毫米，把手在-40毫米。夹具保持全部支点孔同轴。'],'该0.25毫米间隔路径仅为名义网格抽样；未验证手部空间、插入力或连续扫掠。两处原框轴承缺一不可。',context=True,hi=['inner_arm_z-32','inner_arm_z32','outer_handle'])
lever('12L支点轴：裸轴贯穿全部同轴孔',['root_12L_axle'],['保持孤立R臂与U组件由夹具定位；12L 3708裸轴从-Z侧沿+Z送入，名义检查入口轴向偏移-110毫米。两端根轴半套都尚未装。','裸轴依次通过外把手、负Z内臂、原框负Z圆孔、原框正Z圆孔及正Z内臂。不得漏过任一原框支点。','最终轴中心Z=-4毫米，原生端面约Z=-51.8到+43.8毫米。只沿孔轴推进，遇到卡滞停止。'],'在孤立R臂下0.25毫米路径抽样通过；不是连续扫掠或手部接近认证。只允许裸轴过孔。',context=True)
lever('支点最后：两端各装一只半套',['root_retainer_-46','root_retainer_38'],['分别从12L轴两端装32123a半套，中心在Z=-46及+38毫米。','负侧半套贴外把手外面；正侧贴正Z内臂外面。两处原框圆孔均留在轴上，形成双点支承。','两端相对半套外面各约3.8毫米名义露出余量。半套只轻贴，不把整串夹到转不动。'],'复核两端半套、两处框孔和两内臂；摩擦与真实防脱尚未验证。',context=True)
lever('上止挡：4L轴从把手外侧穿第4孔',['stop_4L_axle','stop_outer_retainer'],['R臂、16件杠杆和另三臂已先接入底盘，才安装这4件上止挡。外把手由远端数第4孔，距支点向外56毫米；不能误装到末端按压三孔。','先给3705 4L轴的-Z侧预套32123a半套，再从-Z沿+Z把裸长端穿过把手第4孔。','半套停在把手外面，中心Z=-46毫米；轴中心Z=-36毫米，+Z端保持可接近。'],'预装半套不能通过把手孔；必须先穿裸轴，再从开放端装内侧件。',context=True)
lever('上止挡内侧：装3713接触轴套',['stop_bush'],['从4L轴开放的+Z端套入3713，沿-Z到把手内表面，轴套中心Z=-32毫米。','名义上位时该轴套中心Y=96.4毫米，外缘接触原底盘39790的Y=100毫米实体上表面。','接触用于限制向上抬升，不会把托盘锁在上位。接触处未验证强度、磨损或冲击。'],'保持托盘独立支承；不以用力压到止挡证明工作高度正确。',context=True)
lever('上止挡最后：内半套封住轴端',['stop_inner_retainer'],['最后从+Z轴端装32123a，中心Z=-26毫米，轻贴3713。','4L轴堆叠从-Z到+Z为外半套、把手、3713、内半套；轴端Z=-52与-20毫米，名义两端各余4毫米。','新增20件全部就位：三根15L梁、两根2780、12L与11L轴、六只半套、四件间隔件、两只3713及一根4L轴。'],'上止挡4件已包含在20件内；不加锁扣、皮筋或独立握把。',context=True)
lever('150件支承总成：空载检查前复核',[],['130件原修订支承加20件杠杆，合计150件；模型各动作状态件数不变。','再核对双根部框孔、11L横轴叠层、两根重叠销肩、上止挡第4孔及全部半套；销肩与半套均不穿封闭梁孔。','仅从外把手末端第1至3孔上方按压。手指保持在把手上方，任何时候都不从下方环抱或伸入支点与托盘。','保留独立托盘支承，下一阶段才做空载操作检查。实际自重能否克服摩擦尚未证实。'],'本图省略部分原机；几何就位不等于整机装配路径、承重和带电动作通过。',context=True,hi=[r['id']for r in C.rows if r['role']=='lever'])
# Explicit approach arrows show bare-axis / exposed-end sequence, not a continuous-path certificate.
posed={p.note:p.pos*.4 for p in C.lever_parts(42.4)}
arrow_plan={
 'GRAVITY-01':[('root_overlap_pin_16',[0,0,-25],[0,0,0]),('root_overlap_pin_32',[0,0,-25],[0,0,0])],
 'GRAVITY-02':[('outer_handle',[0,0,-30],[0,0,0])],
 'GRAVITY-03':[('end_11L_axle',[0,0,-75],[0,0,-42])],
 'GRAVITY-04':[('end_spacer1L_-8',[0,0,52],[0,0,0])],
 'GRAVITY-05':[('end_spacer2L_20',[0,0,38],[0,0,0])],
 'GRAVITY-06':[('inner_arm_z32',[0,0,28],[0,0,0])],
 'GRAVITY-07':[('end_retainer_38',[0,0,22],[0,0,0])],
 'GRAVITY-08':[('outer_handle',[-85,0,0],[-30,0,0])],
 'GRAVITY-09':[('root_12L_axle',[0,0,-85],[0,0,-48])],
 'GRAVITY-10':[('root_retainer_-46',[0,0,-22],[0,0,0]),('root_retainer_38',[0,0,22],[0,0,0])],
 'GRAVITY-11':[('stop_4L_axle',[0,0,-40],[0,0,-16])],
 'GRAVITY-12':[('stop_bush',[0,0,25],[0,0,0])],
 'GRAVITY-13':[('stop_inner_retainer',[0,0,22],[0,0,0])],
}
for st in steps[79:]:
 for name,a,b in arrow_plan.get(st['id'],[]):
  import numpy as np
  aa=posed[name]+a;bb=posed[name]+b;direction=(bb-aa)/np.linalg.norm(bb-aa)
  st['insertion_vectors_mm'].append(dict(part_ids=[new[name]['index1']],direction=direction.tolist(),**{'from':aa.tolist(),'to':bb.tolist()},nominal_travel_mm=None,note_zh='方向示意，不等于完整插入力／手部空间验证。'))
# Earliest feasible local order; master guide inserts R-to-base and remaining-arm interfaces.
lever_steps=steps[79:];ordinary=steps[:79];prepins=[q for q in ordinary if q['id']in ['D132-060','D132-061','D132-062']];ordinary=[q for q in ordinary if q not in prepins];at=next(i for i,q in enumerate(ordinary)if q['id']=='D132-034');ordinary[at:at]=prepins
steps=lever_steps[:13]+ordinary+lever_steps[13:]
lever_steps[13]['visible_part_ids']=[r['index1']for r in C.rows]
seen=[]
for n,s in enumerate(steps,1):
 if s['id']in ['D132-078','D132-080']:
  s['visible_part_ids']=list(dict.fromkeys(s['visible_part_ids']+[r['index1']for r in C.rows if r['role']=='lever']))
 if s['id']=='D132-034':
  pins=[r['index1']for r in C.rows if r['id'].startswith('seat_column_pin_')]
  s['visible_part_ids']=list(dict.fromkeys(s['visible_part_ids']+pins))
  rightpins=[r['index1']for r in C.rows if r['id'].startswith('seat_column_pin_') and r['position_ldu'][2]<0]
  for a in s['insertion_vectors_mm']:a['part_ids']=list(dict.fromkeys(a['part_ids']+rightpins))
 s['number']=n;s['prerequisite_step_ids']=[steps[n-2]['id']]if n>1 else [];s['new_parts']=[{'index1':i,'part':C.rows[i-1]['name'],'id':C.rows[i-1]['id']}for i in s['added_part_ids']]
 seen+=s['added_part_ids'];s['cumulative_introduced_count']=len(set(seen));s['image_file']=f'support-diagrams/{n:03d}.png';s['geometry_records']=[copy.deepcopy(C.rows[i-1])for i in s['visible_part_ids']]
 if s['module_id']=='lever' and s['id']!='GRAVITY-14':
  s['lever_parameter_mm']=42.4;s['tray_drop_mm']=None;
  if n<=10 and s.get('external_context'):s['external_context']='isolated_root'
  s['pose_label']='机外／安装下位姿态，杠杆参数42.4毫米'
  posed={p.note:p for p in C.lever_parts(42.4)}
  for r in s['geometry_records']:
   if r['id']in posed:r['position_ldu']=posed[r['id']].pos.tolist();r['rotation']=posed[r['id']].rot.tolist()
 elif s.get('lever_parameter_mm') is not None:
  posed={p.note:p for p in C.lever_parts(s['lever_parameter_mm'])}
  for r in s['geometry_records']:
   if r['id']in posed:r['position_ldu']=posed[r['id']].pos.tolist();r['rotation']=posed[r['id']].rot.tolist()
 else:
  s['lever_parameter_mm']=0.0;s['tray_drop_mm']=0.0
 # Assembly waypoints are explicit part translations from their displayed final poses.
 for path in s.get('assembly_waypoints',[]):
  row=new[path['id']];origin=np.array(row['position_ldu'])*.4;ways=path['translations_mm']
  for a,b in zip(ways,ways[1:]):
   aa=origin+a;bb=origin+b;direction=(bb-aa)/np.linalg.norm(bb-aa)
   s['insertion_vectors_mm'].append(dict(part_ids=[row['index1']],direction=direction.tolist(),**{'from':aa.tolist(),'to':bb.tolist()},nominal_travel_mm=None,note_zh='名义局部路径；手部接近和插入力未验证。'))

assert len(seen)==len(set(seen))==150,(len(seen),len(set(seen)))
canonical=json.dumps(C.rows,ensure_ascii=False,indent=2).encode()
g['external_host_requirement']['retained_foundation_count']=64
g.update(steps=steps,title_zh='整合重力回落版150件支承装配图解',revision=C.REVISION,source_assembly='../assembly-integrated132.json',source_geometry_sha256=hashlib.sha256(canonical).hexdigest(),global_cautions_zh=['仅设计审阅；未通过实体装配、载荷、保持与带电验收。','8墙脚销名义纠正已批准，实体未验收。','无工作锁销、无水平P/Q补强、无自动保持。'],coverage={'expected_count':150,'support_count':130,'lever_count':20,'introduced_count':150,'unique_count':150,'all_instances_once':True,'step_count':len(steps),'support_steps':79,'lever_steps':len(steps)-79})
g.pop('source_assembly_sha256',None);g.pop('verification',None);g.pop('part_catalog',None)
(H/'support-steps.json').write_text(json.dumps(g,ensure_ascii=False,indent=2));(H/'support-instance-map.json').write_text(json.dumps(mapping,indent=2))
print('Support mapped',len(steps),'steps;150 unique instances')
