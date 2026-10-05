"""从候选模型生成机械头小样搭建图及逐件覆盖检查。"""
from pathlib import Path
from collections import Counter
import sys,json,hashlib,html,base64,io
import numpy as np
from PIL import Image
import boxed_slider as w
sys.path.insert(0,str(w.ROOT/'tools/lego/v3'))
import assembly_instructions as ai
P=Path(__file__).parent;OUT=P/'build';OUT.mkdir(exist_ok=True)
ai.CACHE=OUT/'cache'
parts=w.head();used=set();cards=[]
def take(notes,side=None):
 if isinstance(notes,str):notes=[notes]
 ps=[p for p in parts if p.note in notes and (side is None or p.pos[side[0]]*side[1]>0)]
 assert all(id(p) not in used for p in ps),notes
 used.update(id(p) for p in ps);return ps
def add(title,new=(),old=(),tip='',delta=None,view=(40,25),moving=()):
 c=dict(n=len(cards)+1,title=title,new=list(new),old=list(old),tip=tip,delta=delta,view=view,moving=list(moving));cards.append(c);return list(old)+list(moving)+list(new)
def subset(ps,notes):return [p for p in ps if p.note in notes]
rear=add('后框：长边竖直',take('后整体框'),tip='64179的7孔方向沿上下；侧孔朝向导轨端座。',view=(65,20))
rear=add('排入两只后导轨孔座',take(['导轨固定孔座','端座内隔套']),rear,tip='两座圆孔朝前后；每排依次为整套、32184、整套、32184、整套。',view=(65,20))
rear=add('穿两根8号定位轴',take('端座贯穿定位轴'),rear,tip='从框上端穿入，两根轴分别穿过对应的五个内件与框侧孔。',delta=(0,-85,0),view=(65,20))
rear=add('后座轴端加半套',take('后端座外限位'),rear,tip='四只半轴套贴近框外侧，孔座圆孔须同轴。',delta='outY',view=(65,20))
core=add('滑块：公共轴穿后排孔',take(['承重滑块','输入公共轴']),tip='39793的两条长圆孔沿推杆；7号轴穿靠转盘一排的横孔。')
core=add('公共轴：先短接片，再上夹指杆',take('推杆短接片')+take('输入粗连杆',(1,-1)),core,tip='从滑块向两侧依次套41677、上夹指32316；两侧镜像。',delta='out')
core=add('公共轴：下夹指杆和外半套',take('输入粗连杆',(1,1))+take('输入公共轴外限位'),core,tip='下夹指两杆位于最外层；按轴向层位图检查，勿夹死转动杆。',delta='out')
for sy,label in [(-1,'上'),(1,'下')]:
 jaw=add(label+'夹指：主梁与压头支承片',take(['夹指主梁','压头支承薄梁'],(1,sy)),tip='7孔主梁第4孔为根孔；前端两片32449连接主梁第6、7孔。')
 jaw=add(label+'夹指：轮毂、轮胎与前轮轴',take(['轮毂','橡胶胎','轮毂贯穿轴'],(1,sy)),jaw,tip='轮胎套42610轮毂，2号轴穿轮毂并接两片32449最前端十字孔。')
 jaw=add(label+'夹指：锁住支承片',take(['薄梁固定轴','薄梁固定轴限位','薄梁固定挡套销'],(1,sy)),jaw,tip='后孔穿3号轴并装两半套；相邻孔装32054。轮毂应能转动。',delta='out')
 core=add(label+'夹指：接入双侧输入杆',take(['输入关节轴','输入关节间隔','输入关节内半隔套','输入关节外限位'],(1,sy)),core,tip=('上关节用5号轴；主梁两侧各半套、粗连杆、外半套。' if sy<0 else '下关节用7号轴；主梁两侧各整套、半套、粗连杆、外半套。'),moving=jaw)
front=add('前导轨块：预插两根长销',take(['前固定导轨块','前导轨块固定销']),tip='两销在中排相邻横孔；挡肩均位于同一侧，见右侧完成图。',view=(55,25))
core=add('对齐后座、滑块与前固定块',take('转盘上半'),rear,tip='摆放已完成的滑块组件与前块，长圆孔同轴；转盘有齿半片放后端。',moving=core+front,view=(45,20))
core=add('穿两根11号导轨',take(['承重导轨','导轨内限位']),core,tip='从后向前穿：后座、后半套、滑块、前半套、前固定块。',delta=(-95,0,0),view=(35,25))
core=add('根孔两侧各备一个整轴套',take('夹指根轴内隔套'),core,tip='四只整套先放根孔两侧，合拢侧架时扶住；稍后贯穿10号根轴。',delta='out')
panels=[]
for sz,label,view in [(-1,'背侧',(-140,22)),(1,'正侧',(40,22))]:
 side=(2,sz)
 panel=add(label+'根架：内立梁、T支板、垫梁',take(['根轴内侧支承梁','前导轨T支板','根架间隔梁','导轨支板固定销'],side),tip='内立梁11孔；T梁横边接第5、7孔，两个2孔垫梁接向外露出的长销。',view=view)
 panel=add(label+'根架：预放限位片与中间延长梁',take(['防翻折限位架','限位架固定销','中梁延长梁','中梁根架长销'],side),panel,tip='上下各两片32056，夹在内外立梁之间；中央3孔梁朝后。',delta=(0,0,55*sz),view=view)
 panel=add(label+'根架：外立梁合拢',take('夹指根立梁',side),panel,tip='外立梁压上端部长销及中央长销；根孔保持空置。',delta=(0,0,70*sz),view=view)
 panel=add(label+'中梁：连接转盘T梁与延长梁',take(['转盘T形接口梁','中间承重直梁','中梁延长固定销','T梁中梁固定销'],side),panel,tip='7孔中梁前两孔接3孔延长梁；后端两孔接转盘T梁。',view=view)
 panel=add(label+'侧框：摆入短承重梁和后垫梁',take(['侧整体框','侧承重直梁','后框侧垫梁'],side),panel,tip='7×5侧框长边朝前后；两根5孔梁在内面，两根2孔垫梁再向内一层。',view=view)
 panel=add(label+'侧框：装长销与黑销',take(['后框侧垫梁销','侧框固定销'],side),panel,tip='后端长销穿2孔垫梁、5孔梁、侧框；前端黑销接5孔梁和侧框。',delta=(0,0,70*sz),view=view)
 panel=add(label+'根架：穿两根5号轴并限位',take(['根架贯穿轴','根架贯穿轴限位'],side),panel,tip='两轴穿内立梁、垫梁、外立梁及侧框；内外各半套。',view=view)
 panel=add(label+'接口：预插转盘和后框连接销',take(['转盘接口销','后框连接销','后框中梁长销'],side),panel,tip='四个黑销接转盘和后框；中间长销短段朝后框，长段穿T梁与中梁。',view=view)
 panels.append(panel)
for panel,label,sz in zip(panels,['背侧','正侧'],[-1,1]):
 core=add('合拢'+label+'骨架',old=core,moving=panel,delta=(0,0,100*sz),tip='同时对齐转盘、后框和前固定块；根孔轴套扶稳。不要靠挤压零件对孔。',view=(-140,22) if sz<0 else (40,22))
core=add('贯穿两根10号根轴',take('夹指根轴'),core,tip='穿外立梁、双限位片、内立梁、整套、夹指，再穿另一侧；夹指须自由转动。',delta=(0,0,120),view=(40,22))
core=add('根轴两端加半套',take('夹指根轴外限位'),core,tip='四只半套靠近外立梁；不要用压紧轴套消除夹指间隙。',delta='out')
core=add('装8号开限位挡轴及半套',take(['开限位挡轴','开限位挡轴轴套']),core,tip='挡轴穿两侧限位片前端十字孔，轴端各半套；正常松开角25°。')
core=add('装推杆接头、3号轴与半套',take(['推杆铰接头','推杆铰轴','推杆铰轴外限位']),core,tip='32013放在两片41677之间；3号轴贯穿两片十字孔和接头圆孔。')
core=add('从后方插入16号一体推杆',take('一体推杆'),core,tip='50451穿转盘中央，再插入32013后端十字孔。先手动验证，暂不接舵机。',delta=(-110,0,0))
add('小样完成：翻面检查，再手动开合',old=core,tip='核对两侧轴套和双杆层位；先测导轨阻力，再加载验证。',view=(-140,25))
assert len(used)==len(parts),(len(used),len(parts),[(p.note,p.pos.tolist()) for p in parts if id(p) not in used])
assert len(core)==len(parts) and len(set(map(id,core)))==len(parts)

def render(c):
 n=c['n'];new=c['new']+c['moving'];delta=c['delta'];ds={}
 for p in new:
  if delta=='out' if isinstance(delta,str) else False:d=(0,0,75*np.sign(p.pos[2]))
  elif delta=='outY' if isinstance(delta,str) else False:d=(0,70*np.sign(p.pos[1]),0)
  elif delta is None:d=(0,0,0)
  else:d=delta
  ds[id(p)]=np.array(d,float)
 exploded=[p.moved(w.m.I,ds[id(p)]) for p in new]
 large,project=ai.render_scene(c['old'],exploded,c['view'],str(n),880,545)
 small,_=ai.render_scene(c['old'],new,c['view'],str(n)+'done',310,290)
 e=html.escape
 svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="900" viewBox="0 0 1280 900">', '<defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="4" orient="auto"><path d="M0 0L8 4L0 8Z" fill="#087bbb"/></marker></defs>','<rect width="1280" height="900" fill="white"/><g font-family="Noto Sans CJK SC, sans-serif" fill="#203142">',f'<text x="32" y="58" font-size="32" font-weight="700">{n:02d}　{e(c["title"])}</text>','<rect x="24" y="84" width="1232" height="142" rx="10" fill="#f0f4f7"/>']
 tally=Counter((p.name,p.color) for p in c['new'])
 if not tally:svg.append('<text x="45" y="154" font-size="25">使用前面已完成的组件；本步不增加零件</text>')
 for j,((name,color),qty) in enumerate(tally.items()):
  part=w.m.Part(name,color,[0,0,0],w.m.I,1)
  data,_=ai.render_scene([], [part], (35,25),name,135,95)
  x=35+j*min(245,1190/max(len(tally),1))
  svg += [ai.picture(data,x,88,135,95),f'<text x="{x+142}" y="142" font-size="26">×{qty}</text>',f'<text x="{x+15}" y="208" font-size="21">{e(name.replace(".dat","").replace("_nominal",""))}</text>']
 svg += [ai.picture(large,10,230,880,545),'<path d="M910 250V754" stroke="#d5dfe6"/>','<text x="946" y="302" font-size="24">装好后的位置</text>',ai.picture(small,930,330,310,290)]
 groups={}
 for p in new:
  d=ds[id(p)]
  if np.linalg.norm(d):groups.setdefault(tuple(d),[]).append(p)
 for d,ps in groups.items():
  mid=np.mean([p.pos for p in ps],axis=0);d=np.array(d);a=project(mid+d*.78)+[10,230];b=project(mid+d*.15)+[10,230]
  if np.linalg.norm(b-a)>8:svg += [f'<path d="M{a[0]} {a[1]}L{b[0]} {b[1]}" stroke="white" stroke-width="10"/>',f'<path d="M{a[0]} {a[1]}L{b[0]} {b[1]}" stroke="#087bbb" stroke-width="5" marker-end="url(#a)"/>']
 tip=c['tip'];lines=[tip[i:i+47] for i in range(0,len(tip),47)]
 svg.append('<rect x="24" y="780" width="1232" height="98" rx="10" fill="#f0f4f7"/>')
 for i,line in enumerate(lines):svg.append(f'<text x="43" y="{816+i*32}" font-size="23">{e(line)}</text>')
 svg += ['<text x="949" y="706" font-size="18" fill="#60717f">浅色：已装件</text><text x="949" y="738" font-size="18" fill="#60717f">原色：本步零件／组件</text>','</g></svg>']
 (OUT/f'{n:02d}.svg').write_text('\n'.join(svg))
 return {'步骤':n,'标题':c['title'],'新增数量':len(c['new']),'图':f'{n:02d}.svg','说明':tip,'零件':[{'编号':name,'颜色':color,'数量':qty} for (name,color),qty in tally.items()]}

def layers():
 rows=[('公共轴 44294 · 7号轴 · 总长56mm',[("半套",4),("下杆",8),("上杆",8),("41677",4),("滑块",8),("41677",4),("上杆",8),("下杆",8),("半套",4)]),
 ('上夹指关节 32073 · 5号轴 · 总长40mm',[("半套",4),("上杆",8),("半套",4),("主梁",8),("半套",4),("上杆",8),("半套",4)]),
 ('下夹指关节 44294 · 7号轴 · 总长56mm',[("半套",4),("下杆",8),("半套",4),("整套",8),("主梁",8),("整套",8),("半套",4),("下杆",8),("半套",4)]),
 ('夹指根轴 3737 · 10号轴 · 总长80mm',[("半套",4),("外柱",8),("限位片",4),("限位片",4),("内柱",8),("整套",8),("主梁",8),("整套",8),("内柱",8),("限位片",4),("限位片",4),("外柱",8),("半套",4)])]
 # 根轴叠层总厚84? 实际外半套中心95，外柱80，薄片55/65，内柱40、整套20、主梁0 -> 总80。
 assert sum(v for _,v in rows[0][1])==56
 assert sum(v for _,v in rows[1][1])==40
 assert sum(v for _,v in rows[2][1])==56
 assert sum(v for _,v in rows[3][1])==80
 svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="1000"><rect width="1280" height="1000" fill="white"/><g font-family="Noto Sans CJK SC,sans-serif" fill="#203142"><text x="35" y="48" font-size="30" font-weight="700">轴向层位核对 · 从背侧到正侧</text><text x="35" y="87" font-size="22">尺寸为名义厚度；轴套贴近，不把圆孔转动件夹紧。</text>']
 for ri,(title,ls) in enumerate(rows):
  y=140+ri*210;svg.append(f'<text x="35" y="{y}" font-size="25" font-weight="700">{title}</text>');x=50;scale=1180/sum(mm for _,mm in ls)
  for label,mm in ls:
   width=mm*scale;color='#e7a759' if '杆' in label else '#d3dde5' if '套' in label else '#8da9c3' if '柱' in label else '#ecc858' if label=='滑块' else '#d78475'
   svg += [f'<rect x="{x}" y="{y+23}" width="{width}" height="63" fill="{color}" stroke="white" stroke-width="2"/>',f'<text x="{x+width/2}" y="{y+64}" text-anchor="middle" font-size="20">{label}</text>',f'<text x="{x+width/2}" y="{y+123}" text-anchor="middle" font-size="20">{mm}mm</text>'];x+=width
 svg.append('</g></svg>');(OUT/'layers.svg').write_text('\n'.join(svg))

def write_page(results):
 sourcehash=hashlib.sha256((P/'boxed_slider.py').read_bytes()).hexdigest()
 payload={'模型SHA256':sourcehash,'机械头零件数':len(parts),'步骤数':len(cards),'覆盖检查':'每件只在一个步骤首次增加；最终组件与head()逐件一致','步骤':results}
 (OUT/'steps.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2))
 listing=''.join(f'<a href="#s{r["步骤"]}">{r["步骤"]:02d} {html.escape(r["标题"])}</a>' for r in results)
 sections=''.join(f'<section id="s{r["步骤"]}"><img src="{r["图"]}" alt="第{r["步骤"]}步 {html.escape(r["标题"])}"></section>' for r in results)
 page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>机械头小样搭建图</title><style>body{font:16px/1.65 system-ui,sans-serif;background:#eaf0f4;color:#203142;margin:0}main{max-width:1280px;margin:auto;padding:20px}h1{font-size:28px}a{color:#176299}nav{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}section{margin:22px 0;background:white;scroll-margin-top:10px}img{width:100%;display:block}.box{background:white;padding:20px;margin:20px 0}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccd7df;padding:10px;text-align:left}@media(max-width:700px){nav{grid-template-columns:1fr}main{padding:10px}}@media print{@page{size:A4 landscape;margin:6mm}header,nav,.box,details{display:none}main{padding:0}body{background:white}section{margin:0;break-after:page}section img{height:190mm;width:100%;object-fit:contain}}</style><main><header><h1>新机械头 · 单臂结构小样搭建图</h1><p>43步／168件 · 真实候选零件模型 · 先手动验证结构，再接舵机</p><p><a href="../review.html">可旋转整体模型</a> · <a href="layers.svg">轴向层位图</a> · <a href="steps.json">各步零件表</a> · <a href="../../../docs/lego/v3/design/boxed-slider.md">设计与承重说明</a></p></header><div class="box"><h2>先看这四点</h2><ol><li>范围是转盘有齿半片到夹指的机械头本体，含一体推杆；后部马达、舵机和底座本次不搭。</li><li>前19步有待合拢的松散组件，需扶住轴套；第20—35步左右侧架分别预装，第36—37步合拢。</li><li>上、下夹指关节轴长与隔套不同；公共轴两侧顺序完全镜像。薄梁只能用图示含十字孔的型号。</li><li>箭头为装入方向示意，右图为完成位置；手指操作空间、真实销紧度和滑动阻力还需小样验证。</li></ol></div><details><summary>步骤目录</summary><nav>__NAV__</nav></details><section><img src="layers.svg" alt="公共轴、上下夹指关节、根轴层位图"></section>__SECTIONS__<div class="box"><h2>小样验证记录</h2><p>先空载，后加载。不要用挤紧轴套或弯曲框架解决卡滞。</p><table><tr><th>检查</th><th>方法</th><th>记录</th></tr><tr><td>连接是否完整</td><td>核对43步、168件；检查所有长销挡肩、轴端半套及左右镜像。</td><td>漏件／错孔：</td></tr><tr><td>空载开合</td><td>未接舵机时手推全行程约10mm，检查双杆、导轨是否卡滞。</td><td>阻力峰值／位置：</td></tr><tr><td>导轨侧载</td><td>固定骨架，向滑块施加约2.50N横向力，比较有载与空载启动阻力。</td><td>启动／往返阻力：</td></tr><tr><td>骨架与根轴</td><td>安装到真实转盘固定支座后，施加100g试重；分别测0°、45°、90°轮端、根架和转盘位移。</td><td>各点位移：</td></tr><tr><td>轴向保持</td><td>重复开合、卸载后检查轴套迁移、残余变形和反向间隙。</td><td>移位／回零：</td></tr></table><p>0.5mm轮端偏移仅作初次比较目标。几何和理想约束检查不能替代实物承载验证。</p></div></main></html>'''
 (OUT/'index.html').write_text(page.replace('__NAV__',listing).replace('__SECTIONS__',sections))

if __name__=='__main__':
 import argparse,concurrent.futures,multiprocessing
 parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
 layers()
 if args.check:print(f'{len(cards)}步覆盖全部{len(parts)}件，无重复或遗漏；四类轴向叠层长度吻合。');sys.exit()
 with concurrent.futures.ProcessPoolExecutor(max_workers=3,mp_context=multiprocessing.get_context('fork')) as pool:
  results=[]
  for r in pool.map(render,cards):results.append(r);print(r['步骤'],r['标题'],flush=True)
 write_page(results)
