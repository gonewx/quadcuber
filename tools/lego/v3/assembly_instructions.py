"""用模型中的真实零件生成分步装配图；不修改机构、BOM 或24个主步骤。

python assembly_instructions.py [--step 19] [--check]
蓝色箭头表示插入方向；浅色为已装件。分步图中的平移仅用于爆炸展示。
"""
from pathlib import Path
from collections import Counter
import argparse
import base64
import hashlib
import html
import io
import json
import math
import multiprocessing
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'render'))
import model
import ldraw
import software

OUT = HERE.parents[2] / 'docs/lego/v3'
CACHE = HERE.parent / '.cache/assembly'
CARDS = OUT / 'img/assembly'


def recipes():
    parts = model.build()
    steps = {k: [p for p in parts if p.step == k] for k in range(1, 25)}
    cards = []
    counts = Counter()
    used = Counter()

    def add(k, title, new=(), old=(), delta=None, tip='', view=(42, 22), repeat=1, moving=(), tray=True):
        new, old, moving = list(new), list(old), list(moving)
        number = 1 + sum(c['step'] == k for c in cards)
        card = dict(step=k, number=number, title=title, new=new, old=old, delta=delta,
                    tip=tip, view=view, repeat=repeat, moving=moving, tray=tray)
        cards.append(card)
        used.update(id(p) for p in new)
        counts.update({(k, n, c): qty * repeat for (n, c), qty in Counter((p.name, p.color) for p in new).items()})
        return old + new

    def seq(k, groups, context=(), view=(42, 22), repeat=1, source=None):
        ps = steps[k] if source is None else source
        old = list(context)
        for title, indices, delta, tip in groups:
            old = add(k, title, [ps[i] for i in indices], old, delta, tip, view, repeat)
        return old

    # 底座先铺梁与连接销，再扣框；四角重复，最后检查闭环。
    seq(1, [
        ('铺好两根底梁 · 做4组', [1,4], None, '两根15孔梁成直角；每根留两个角桥连接点。'),
        ('底梁插销', [2,3,5,9,10,11,12], (0,-65,0), '黑销按图占孔；另一孔留蓝色长销。'),
        ('压上大框与角桥', [0,8], (0,-85,0), '大框与7×5角框同层；邻侧大框在最后合拢。'),
        ('补上马达连接销', [6,7], (0,-65,0), '蓝色长销穿两层，向上露出一孔。'),
        ('后端落地梁插销', [14,15,16], (0,65,0), '三个销；保留以后安装55615的孔。'),
        ('装后端落地梁', [13], (0,85,0), '11孔梁贴在大框后短边下面。')], view=(25,60), repeat=4, source=steps[1][17:34])
    add(1, '四组旋转合拢', old=steps[1], tip='四角各四个黑销连接下方底梁；检查底面落地。', view=(25,75))
    seq(2, [('下框', [2],None,''),('三销向上', [6,7,8],(0,-60,0),''),
            ('接中框',[1],(0,-90,0),''),('再插三销',[3,4,5],(0,-60,0),''),('接上框',[0],(0,-90,0),'三个框上下对齐。')], view=(62,20))
    seq(3, [('马达底面朝上',[0],None,''),('底面三个销',[1,2,3],(0,65,0),'三销对应垫梁第2、3、4孔。'),
            ('第一层垫梁',[4],(0,85,0),''),('两端各一销',[5,6],(0,65,0),''),('第二层垫梁',[7],(0,85,0),'两层5孔梁对齐。')], view=(55,-35))
    seq(4, [('颈部上长销、下黑销',[0,1],(65,0,0),''),('装3孔竖梁',[2],(65,0,0),''),
            ('中孔补黑销',[3],(65,0,0),''),('接两根横梁',[4,5],(85,0,0),'11孔在上、7孔在下，都朝竖墙伸出。')],context=steps[3][:1],view=(65,20))
    seq(5, [('7号轴插到底',[0],(100,0,0),'另一端与背面输出盘基本齐平。'),
            ('第一只半轴套',[1],(85,0,0),''),('第二只半轴套',[2],(85,0,0),''),('再加整轴套',[3],(85,0,0),''),
            ('24齿齿轮',[4],(85,0,0),''),('外端半轴套',[5],(65,0,0),'半套靠近齿轮，轴端齐平。')],context=steps[3][:1],view=(50,20))
    motor = sum((steps[k] for k in (3,4,5)), [])
    seq(6,[('横梁插四个销',list(range(4)),(55,0,0),'上横梁3个；下横梁1个。')],context=steps[4],view=(65,20))
    add(6,'马达整体平推到竖墙',old=steps[2],moving=motor+steps[6],delta=(-100,0,0),tip='四个销同时对孔，底块与墙底齐平。',view=(65,20))
    seq(7,[('凸台塞进上框',[0],(75,0,0),'无齿的下半转盘，凸台长边对框长边。'),
           ('内侧向外插第一根销',[1],(0,0,30),'从中孔放入；使用这一端的上排孔。'),
           ('另一端用下排孔',[2],(0,0,-30),'两根挡套错开，留在凸台里面。')],context=steps[2][:1],view=(70,18))
    base = steps[1][17:34]
    seq(8,[('底座短边插两销',[0,1],(0,-60,0),'长边的马达销已在第1步装好。')],context=base,view=(40,40))
    wall = sum((steps[k] for k in range(2,8)),[])
    add(8,'竖墙与马达一起下压',old=base+steps[8],moving=wall,delta=(0,-140,0),tip='墙底和马达底块同时对孔。',view=(40,30))
    platform = seq(9,[('两根15孔梁平行',[1,2],None,'两梁间距4孔。'),
         ('插六个连接销',[3,4,5,6,7,14],(0,-60,0),'蓝色长销的两个位置留空。'),('扣前平台框',[0],(0,-90,0),''),
         ('垫梁下插两销',[9,10],(0,-65,0),''),('装5孔垫梁',[8],(0,-70,0),'第1、5孔留给舵机；第2孔留空。'),
         ('后横梁下插两销',[16,17],(0,-60,0),''),('接后横梁',[15],(0,-70,0),''),
         ('导向框下插长销',[12,13],(0,-65,0),'长段向下，穿平台框和15孔梁。'),('装竖直导向框',[11],(0,-100,0),'轴承孔朝前后。')],view=(30,40))
    add(9,'翻看底面：挂两个55615',steps[9][18:20],platform,(0,75,0),'两个支撑前后错一孔，按图对位。',view=(30,-35))
    seq(10,[('舵机落到垫梁',[0],(0,-75,0),'输出轴朝向推杆侧。'),('插两根耳朵长销',[1,2],(0,-60,0),'短段朝下，进入垫梁第1、5孔。')],context=steps[9],view=(30,40))
    seq(11,[('底座后端插55615',[2],(0,-70,0),'两个向下的销插后短边。')],context=[base[i] for i in (0,13)],view=(40,30))
    seq(11,[('平台前端两销',[0,1],(-60,0,0),'沿推杆方向对准竖墙。')],context=steps[9][:1],view=(130,25))
    add(11,'平台整体向前推',old=steps[2],moving=steps[9]+steps[10]+steps[11][:2],delta=(-100,0,0),tip='导向框两轴承孔与转盘中孔同轴。',view=(130,25))
    for ids, context, sign, title in [([4,5,3],[steps[9][18],steps[11][2]],-1,'马达侧'),([7,8,9,6],[steps[9][19],base[0]],1,'舵机侧')]:
        seq(11,[(title+'：先插销',ids[:-1],(0,0,60*sign),''),(title+'：压上9孔支柱',ids[-1:],(0,0,90*sign),'下端连接点两侧不同，按图安装。')],context=context,view=(40 if sign>0 else -140,22))
    seq(12,[('十字块圆孔朝上',[0],None,'圆孔稍后穿推杆；下十字孔接连杆轴。'),
            ('穿3号轴',[3],(0,0,70),''),('背面半轴套',[4],(0,0,-65),''),
            ('7孔粗连杆第1孔',[9],(0,0,75),'第7孔留在曲柄端；粗梁直接贴十字块。'),
            ('外端半轴套',[5],(0,0,65),'不要夹死圆孔连杆。')],view=(42,22))
    seq(12,[('曲柄与2号轴',[6,7],(0,0,65),'图示为最终夹紧角度；首次先空载定位。'),
            ('曲柄内端半轴套',[8],(0,0,-65),'连杆第6孔接曲柄，第7孔留空。')],context=[steps[12][9]],view=(42,22))
    add(12,'暂放十字块两侧半套',steps[12][1:3],old=[steps[12][0],steps[9][11]],tip='两半套先备好；第22步随推杆穿入，暂不固定。',view=(30,25))
    for offset, sign in [(0,-1),(7,1)]:
        side='背侧' if sign<0 else '正侧'
        seq(13,[(side+'：摆好上下角梁',[offset,offset+4],None,'短边朝前，上下各朝外。'),
                (side+'：插三个黑销',[offset+2,offset+3,offset+6],(0,0,60*sign),'下排第二连接点留给下一步长销。'),
                (side+'：压上两根侧梁',[offset+1,offset+5],(0,0,85*sign),'前角梁比侧梁向前多露一个孔。')],view=(140 if sign>0 else 40,20))
    for offset, sign in [(0,-1),(7,1)]:
        context=[p for p in steps[13] if p.pos[2]*sign>0]
        seq(14,[('垫梁连接销',[offset+3],(0,0,-60*sign),''),('上侧2孔垫梁',[offset+2],(0,0,-70*sign),''),
                ('放上下导向支架',[offset,offset+1],(0,0,-90*sign),'长边末端十字孔留给摆杆根轴。'),
                ('三根长销固定',[offset+4,offset+5,offset+6],(0,0,-90*sign),'下支架另一孔将在第15步共同固定。')],context=context,view=(140 if sign<0 else 40,20))
    for offset, sign in [(0,-1),(8,1)]:
        context=[p for p in steps[13]+steps[14] if p.pos[2]*sign>0]
        seq(15,[('上3孔、下2孔垫梁',[offset+1,offset+2],(0,0,-70*sign),''),
                ('从内侧装五根长销',list(range(offset+3,offset+8)),(0,0,-90*sign),'长段穿垫层和前角梁；短段朝中心。'),
                ('压上11孔根架',[offset],(0,0,-90*sign),'第2、10孔留根轴；第1、11孔留限位销。')],context=context,view=(140 if sign<0 else 40,20))
    add(16,'取转盘上半',[steps[16][0]],tip='有齿的一半，先装两侧固定连接架。',view=(65,20))
    for offset, sign in [(0,-1),(11,1)]:
        ps=steps[16]; context=[ps[0]]
        old=seq(16,[('上下两根轴销',[offset+2,offset+7],(0,0,70*sign),'圆销段进转盘，十字轴段朝外。'),
                    ('3孔薄梁套两端十字孔',[offset+1],(0,0,80*sign),''),
                    ('两片2孔薄梁朝前',[offset+3,offset+8],(0,0,85*sign),'两片都用十字孔，锁住相对角度。'),
                    ('从内侧穿两根止挡轴',[offset+4,offset+9],(0,0,-80*sign),'止挡头留在内侧，贴薄梁。'),
                    ('先套内侧整轴套',[offset+5,offset+10],(0,0,90*sign),'薄梁与7孔侧梁之间各一整套。')],context=context,view=(138 if sign>0 else 42,22))
        side=[p for p in steps[13]+steps[14]+steps[15] if p.pos[2]*sign>0]
        add(16,'侧架套到两根后连接轴',old=old,moving=side,delta=(0,0,90*sign),tip='7孔侧梁后端对轴；扶稳，继续加外轴套。',view=(138 if sign>0 else 42,22))
        add(16,'最后装外侧整轴套',[ps[offset+6],ps[offset+11]],old+side,(0,0,85*sign),'上下两处各一个整套；轴端略露。',view=(138 if sign>0 else 42,22))
    for offset, title in [(0,'下夹指'),(15,'上夹指')]:
        context=[p for p in steps[15] if p.name=='32525.dat']
        seq(17,[(title+'放回正常朝向',[offset],None,'第4孔为根轴；夹指朝魔方。'),
                ('内侧两个整轴套',[offset+2,offset+3],None,'夹指两侧各一只，扶住后穿根轴。'),
                ('穿8号根轴',[offset+1],(0,0,120),'穿根架、整套、夹指，再穿另一侧。'),
                ('限位支架先插黑销',[offset+8,offset+11],{offset+8:(0,0,-65),offset+11:(0,0,65)},'两销在11孔根架的端孔。'),
                ('背面两片L形薄梁',[offset+6,offset+7],(0,0,-85),'末端十字孔套根轴，中孔套黑销。'),
                ('正面两片L形薄梁',[offset+9,offset+10],(0,0,85),'每侧叠两片，总厚8mm。'),
                ('根轴两端半套',[offset+4,offset+5],'out','贴近支架，夹指保持自由转动。'),
                ('穿8号开限位挡轴',[offset+12],(0,0,120),''),
                ('挡轴两端半套',[offset+13,offset+14],'out','上下挡轴均在正常开度之外。')],context=context,view=(40,22))
    for offset, jawidx, title in [(0,0,'下压头'),(9,15,'上压头')]:
        ps=steps[18]
        old=seq(18,[(title+'：轮胎套轮毂',[offset+7,offset+8],None,'42610轮毂 + 50945轮胎。'),
                    ('穿2号轮轴',[offset+6],(0,0,65),''),('两片4孔薄梁夹住轮毂',[offset,offset+1],'out','第4十字孔套轮轴，两端齐平。')],view=(40,22))
        jaw=[steps[17][jawidx]]
        add(18,'压头对准主臂前两孔',old=jaw,moving=old,delta=(65,0,0),tip='主臂第6、7孔，对薄梁第1、2孔。',view=(40,22))
        seq(18,[('第1孔穿3号固定轴',[offset+2],(0,0,75),''),('第2孔插挡套长销',[offset+5],(0,0,-70),''),
                ('固定轴两端半套',[offset+3,offset+4],'out','轮毂能转动；轮轴两端不加轴套。')],context=old+jaw,view=(40,22))
    ps=steps[19]
    center=seq(19,[('5号公共轴 · 中间整套',[0,1],{1:(0,0,85)},'整套放在轴正中。'),
          ('两片4孔驱动薄梁',[6,13],'out','32449：端十字孔套轴，两片都朝后。'),
          ('上下输入薄连杆',[2,9],'out','32017：端圆孔套轴，分别朝上下夹指。'),
          ('两片导向横梁',[7,14],'out','11478：中间圆孔套轴，两端十字孔留空。'),
          ('公共轴两端半套',[8,15],'out','半套贴近横梁；圆孔件仍能自由转动。')],view=(50,22))
    for link, stop, spacer, inner, jawidx, sign, label in [(9,10,12,11,0,1,'下'),(2,3,5,4,15,-1,'上')]:
        context=[ps[link]]
        old=seq(19,[(label+'输入杆插止挡轴',[stop],(0,0,70*sign),'止挡头贴薄梁外面。'),
                    ('从内端套间隔半套',[spacer],(0,0,-65*sign),'半套位于输入薄梁与夹指之间。')],context=context,view=(50 if sign>0 else -130,22))
        jaw=[steps[17][jawidx]]
        add(19,label+'关节套进主臂第2孔',old=jaw,moving=old,delta=(0,0,70*sign),tip='局部放大：公共轴组件尚未固定，可以侧移对孔。',view=(50 if sign>0 else -130,22))
        add(19,'夹指内侧装半套',[ps[inner]],old+jaw,(0,0,-65*sign),'止挡头在外，内半套贴主臂；关节可自由转动。',view=(50 if sign>0 else -130,22))
    add(19,'公共轴与两根输入杆完成',old=ps+[steps[17][0],steps[17][15]],tip='检查三种薄梁型号、孔型与轴向顺序。',view=(50,22))
    for offset, sign in [(0,-1),(6,-1),(12,1),(18,1)]:
        ps=steps[20]; root=ps[offset+1].pos
        bracket=min([p for p in steps[14] if p.name=='32140.dat' and p.pos[2]*sign>0], key=lambda p: np.linalg.norm(p.pos-root))
        transverse=[p for p in steps[19] if p.name=='11478.dat' and p.pos[2]*sign>0]
        seq(20,[('导向根轴穿支架十字孔',[offset+1],(0,0,-80*sign),''),
                ('五孔圆孔摆杆套根轴',[offset],(0,0,-80*sign),'32017两端都是圆孔。'),
                ('根轴内侧半套',[offset+2],(0,0,-70*sign),''),
                ('根轴外侧半套',[offset+3],(0,0,70*sign),''),
                ('活动端穿2号轴',[offset+4],(0,0,70*sign),'贯穿11478端十字孔与摆杆端圆孔。'),
                ('活动端只加外半套',[offset+5],(0,0,70*sign),'活动轴两端略露；检查轴向保持和自由转动。')],context=[bracket]+transverse,view=(138 if sign<0 else 42,22))
    ps=steps[21]
    old=seq(21,[('2号短轴插接头到底',[0,4],{4:(-75,0,0)},'32013后端十字孔接短轴。')],view=(42,22))
    drive=[p for p in steps[19] if p.name=='32449.dat']
    add(21,'接头放进两片驱动薄梁之间',old=drive,moving=old,delta=(-75,0,0),tip='接头圆孔对齐两片32449后端十字孔。',view=(42,22))
    seq(21,[('穿3号铰轴',[1],(0,0,75),''),('铰轴两端半套',[2,3],'out','允许接头绕铰轴转动。'),
            ('光面轴连接器推到贴合',[5],(-75,0,0),'59443前端贴32013后端。'),('11号后轴插到底',[6],(-100,0,0),'两轴端在连接器中间相接。')],context=old+drive,view=(42,22))
    path=[steps[9][11],*steps[12][:3]]
    rod=[p for p in steps[21] if p.note in ('推杆短轴','推杆长轴','推杆连接器','推杆铰接头')]
    add(22,'先看推杆穿孔路径',old=path,moving=rod,delta=(180,0,0),tip='前轴承 → 半套 → 十字块圆孔 → 半套 → 后轴承。',view=(25,25))
    head=sum((steps[k] for k in range(13,22)),[])
    add(22,'推杆随机械头向后滑入',old=steps[7]+path,moving=head,delta=(230,0,0),tip='断电装配；曲柄与黄色连杆暂时脱开。',view=(45,22))
    add(22,'扣合转盘上下两半',old=steps[7],moving=steps[16][:1],delta=(55,0,0),tip='图中隐藏周围支架：两半转盘直接卡合。',view=(65,20))
    add(22,'装好后手动检查',old=head+path,tip='推杆与夹指活动平顺后，再按单臂标定步骤连接舵机。',view=(40,25))
    for arm, title in [('R','对面机械手'),('F','前侧机械手'),('B','后侧机械手')]:
        module=[p for p in steps[23] if p.arm==arm]
        basearm=steps[1][17*model.ARMS.index(arm):17*(model.ARMS.index(arm)+1)]
        add(23,title+'重复第2—22步',module,basearm,None,'位置总览：按第8、11步接底座，第22步装机械头。',view=(35,35),tray=False)
    expected=Counter((p.step,p.name,p.color) for p in parts if p.step<24)
    assert counts==expected, ('分步零件覆盖不一致',expected-counts,counts-expected)
    assert all(used[id(p)] == 1 for p in parts if 2 <= p.step <= 23), '新增零件漏装或重复计数'
    for card in cards:
        k,n=card['step'],card['number']
        if k in (14,15) or (k==16 and n>1):
            width={14:4,15:3,16:7}[k]
            index=(n-(2 if k==16 else 1))//width
            card['title']=('第一侧 · ' if index==0 else '另一侧 · ')+card['title']
        if k==20:
            label=['第一侧后上','第一侧前下','另一侧后上','另一侧前下'][(n-1)//6]
            card['title']=label+' · '+card['title']
    # 索引型配方按型号与坐标指纹验收，防止模型调整后静默沿用旧图。
    return cards, parts


def offsets(card):
    delta=card['delta']; result={}
    ps=card['new']+card['moving']
    for p in ps:
        if delta is None: d=(0,0,0)
        elif isinstance(delta,str) and delta=='out':
            d=(0,0,75 if p.pos[2]>=0 else -75)
        elif isinstance(delta,dict):
            original=[a for a in model_parts if a.step==card['step']]
            index=next(i for i,a in enumerate(original) if a.ldraw()==p.ldraw())
            d=delta.get(index,(0,0,0))
        else:d=delta
        result[id(p)]=np.array(d,float)
    return result


def render_scene(old,new,view,key,w,h):
    CACHE.mkdir(parents=True,exist_ok=True)
    source='0 assembly\n'+'\n'.join(p.ldraw() for p in old)+'\n0 STEP\n'+'\n'.join(p.ldraw() for p in new)+'\n'
    opts=dict(w=w,h=h,yaw=view[0],pitch=view[1],margin=.10,highlight=1,fadeOld=True)
    digest=hashlib.sha256((source+json.dumps(opts)).encode()).hexdigest()[:20]
    path=CACHE/f'{digest}.png'
    if not path.exists():
        ldr=CACHE/f'{digest}.ldr';ldr.write_text(source)
        software.render(dict(model=str(ldr),out=str(path),opts=opts))
    yaw,pitch=np.radians(view)
    direction=np.array([math.sin(yaw)*math.cos(pitch),math.sin(pitch),math.cos(yaw)*math.cos(pitch)])
    right=np.array([math.cos(yaw),0,-math.sin(yaw)])
    camera=np.diag([1,-1,-1])@np.stack([right,np.cross(direction,right),direction],axis=1)
    fit=[]
    for p in old+new:
        mesh=ldraw.geometry(p.name)[0]
        fit.append(((mesh@p.rot.T+p.pos)@camera)[:,:,:2].reshape(-1,2))
    fit=np.concatenate(fit);low,high=fit.min(axis=0),fit.max(axis=0)
    scale=min(w/max(high[0]-low[0],1),h/max(high[1]-low[1],1))*.8
    def project(pt):return ((np.asarray(pt)@camera)[:2]-(low+high)/2)*[scale,-scale]+[w/2,h/2]
    # 内嵌无损WebP，自包含SVG可直接保存、缩放或打印。
    buf=io.BytesIO();Image.open(path).save(buf,format='WEBP',lossless=True)
    return base64.b64encode(buf.getvalue()).decode(), project


def picture(data,x,y,w,h):
    return f'<image x="{x}" y="{y}" width="{w}" height="{h}" href="data:image/webp;base64,{data}"/>'


def render_card(card):
    k,n=card['step'],card['number'];tag=f'{k:02d}-{n:02d}'
    ds=offsets(card); new=card['new']+card['moving']
    exploded=[p.moved(model.I,ds[id(p)]) for p in new]
    large,project=render_scene(card['old'],exploded,card['view'],tag,880,545)
    small,_=render_scene(card['old'],new,card['view'],tag+'-done',310,290)
    esc=html.escape
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="860" viewBox="0 0 1280 860">',
         '<defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="7" refY="4" orient="auto"><path d="M0 0L8 4L0 8Z" fill="#0077b6"/></marker></defs>',
         '<rect width="1280" height="860" fill="white"/><g font-family="Noto Sans CJK SC, Microsoft YaHei, sans-serif" fill="#172535">',
         f'<rect x="24" y="24" width="128" height="57" rx="12" fill="#172535"/><text x="88" y="63" text-anchor="middle" fill="white" font-size="29" font-weight="700">{k}.{n}</text>',
         f'<text x="177" y="63" font-size="31" font-weight="700">{esc(card["title"])}</text>',
         '<rect x="25" y="103" width="1230" height="143" rx="12" fill="#f1f5f9"/>']
    tally=Counter((p.name,p.color) for p in card['new'])
    if not tally or not card['tray']:
        label='使用已装好的组件' if not tally else '按第2—22步制作这一整臂'
        svg.append(f'<text x="52" y="168" font-size="25">{label}</text>')
    else:
        cell=min(205,1180/max(len(tally),1))
        for j,((name,color),qty) in enumerate(tally.items()):
            thumb=OUT/'img'/f'part_{name[:-4]}_{color}.png'
            data=base64.b64encode(thumb.read_bytes()).decode()
            x=40+j*cell
            svg += [f'<image x="{x}" y="106" width="125" height="90" href="data:image/png;base64,{data}"/>',
                    f'<text x="{x+125}" y="154" font-size="26" font-weight="700">×{qty}</text>',
                    f'<text x="{x+10}" y="223" font-size="21">{esc(name[:-4].replace("_nominal",""))}</text>']
    svg += [picture(large,12,257,880,545),'<path d="M910 274V747" stroke="#e2e8f0" stroke-width="2"/>',
            '<text x="953" y="325" font-size="24" fill="#397354">✓ 本小步完成</text>',picture(small,930,359,310,290)]
    # 每组平移画一根代表箭头，避免同轴多件箭头覆盖零件。
    groups={}
    for p in new:
        d=ds[id(p)]
        if np.linalg.norm(d)>0:groups.setdefault(tuple(d),[]).append(p)
    for d,ps in groups.items():
        mid=np.mean([p.pos for p in ps],axis=0);d=np.array(d)
        a=project(mid+d*.76)+[12,257];b=project(mid+d*.18)+[12,257]
        if np.linalg.norm(b-a)>10:
            svg += [f'<path d="M{a[0]:.1f} {a[1]:.1f}L{b[0]:.1f} {b[1]:.1f}" stroke="white" stroke-width="10"/>',
                    f'<path d="M{a[0]:.1f} {a[1]:.1f}L{b[0]:.1f} {b[1]:.1f}" stroke="#0077b6" stroke-width="5" marker-end="url(#arrow)"/>']
    svg += ['<rect x="25" y="790" width="1230" height="50" rx="10" fill="#f1f5f9"/>',
            f'<text x="45" y="824" font-size="23">{esc(card["tip"] or ("按蓝色箭头装入，对照右图确认位置。" if groups else "按图摆放，对照右图确认朝向。"))}</text>',
            '</g></svg>']
    CARDS.mkdir(parents=True,exist_ok=True)
    (CARDS/f'{tag}.svg').write_text('\n'.join(svg))
    return dict(step=k,number=n,title=card['title'],tip=card['tip'],file=f'img/assembly/{tag}.svg',
                repeat=card['repeat'],new_count=len(card['new'])*card['repeat'])


def write_layers():
    """轴向截面是尺寸示意；孔型图例与真实模型编号一一对应。"""
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="620" viewBox="0 0 1280 620">',
         '<rect width="1280" height="620" fill="white"/><g font-family="Noto Sans CJK SC, sans-serif" fill="#172535">',
         '<text x="40" y="55" font-size="32" font-weight="700">公共轴：从中央向两侧，顺序完全相同</text>',
         '<text x="40" y="100" font-size="23">截面示意 · 5号轴共40mm · 半套贴近，不挤紧圆孔转动件</text>']
    layers=[('32123a','半套',4,'#b6c1cc'),('11478','中圆孔',4,'#eeb900'),
            ('32017','端圆孔',4,'#f7d257'),('32449','端十字孔',4,'#dba900'),
            ('3713','中央整套',8,'#b6c1cc'),('32449','端十字孔',4,'#dba900'),
            ('32017','端圆孔',4,'#f7d257'),('11478','中圆孔',4,'#eeb900'),('32123a','半套',4,'#b6c1cc')]
    x=100
    for number,label,mm,color in layers:
        w=mm*27;cx=x+w/2
        svg += [f'<rect x="{x}" y="176" width="{w}" height="105" fill="{color}" stroke="white" stroke-width="3"/>',
                f'<text x="{cx}" y="153" text-anchor="middle" font-size="21">{number}</text>',
                f'<text x="{cx}" y="318" text-anchor="middle" font-size="20">{label}</text>',
                f'<text x="{cx}" y="354" text-anchor="middle" font-size="22">{mm}mm</text>']
        x+=w
    svg += ['<path d="M100 228H1180" stroke="#405364" stroke-width="13"/>',
            '<text x="40" y="421" font-size="28" font-weight="700">输入杆与主臂：止挡头必须在输入薄梁外侧</text>']
    joint=[('内半套',85,'#b6c1cc'),('主臂第2孔',160,'#d94a3a'),('间隔半套',130,'#b6c1cc'),('输入薄梁',130,'#f7d257'),('止挡头',90,'#405364')]
    x=160
    for label,w,color in joint:
        svg += [f'<rect x="{x}" y="462" width="{w}" height="66" fill="{color}" stroke="white" stroke-width="3"/>',
                f'<text x="{x+w/2}" y="563" text-anchor="middle" font-size="22">{label}</text>']
        x+=w
    svg += ['<path d="M160 495H747" stroke="#405364" stroke-width="10"/>',
            '<text x="885" y="486" font-size="23">24316 三号止挡轴</text>',
            '<text x="885" y="531" font-size="23">上、下关节镜像安装</text>','</g></svg>']
    CARDS.mkdir(parents=True,exist_ok=True)
    (CARDS/'19-layers.svg').write_text('\n'.join(svg))


def main():
    global model_parts
    parser=argparse.ArgumentParser();parser.add_argument('--step',type=int);parser.add_argument('--check',action='store_true')
    parser.add_argument('--workers',type=int,default=3)
    args=parser.parse_args();cards,model_parts=recipes()
    print(f'{len(cards)}分步图；第1—23步新增件与模型BOM一致。',flush=True)
    if args.check:return
    dest=OUT/'assembly.json'
    model_hash=hashlib.sha256(model.to_ldr(model_parts).encode()).hexdigest()
    if args.step and dest.exists() and json.loads(dest.read_text())['model_sha256'] != model_hash:
        raise ValueError('模型已改变，必须先全量生成，不能合并旧模型的分步图')
    write_layers()
    manifest=[]
    selected=[c for c in cards if not args.step or c['step']==args.step]
    with ProcessPoolExecutor(max_workers=args.workers, mp_context=multiprocessing.get_context('fork')) as pool:
        for card in pool.map(render_card,selected):
            manifest.append(card)
            print(f'{card["step"]}.{card["number"]} {card["title"]}',flush=True)
    if args.step and dest.exists():
        manifest=[c for c in json.loads(dest.read_text())['cards'] if c['step']!=args.step]+manifest
    payload=dict(model_sha256=model_hash,
                 cards=sorted(manifest,key=lambda c:(c['step'],c['number'])))
    dest.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':main()
