"""用模型中的真实零件生成 v4 分步装配图；不修改机构、BOM 或主步骤。

python assembly_instructions.py [--step 14] [--check]
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
import model
import ldraw
_search_path = list(sys.path)
try:
    sys.path.insert(0, str(HERE.parent / 'render'))
    import software
finally:
    # 软件渲染器会加入上一级目录，不能让它覆盖后续的 v4 同名模块。
    sys.path[:] = _search_path

OUT = HERE.parents[2] / 'docs/lego/v4'
CACHE = HERE.parent / '.cache/assembly-v4'
CARDS = OUT / 'img/assembly'


LAST = 20  # 有分步图的主步骤: 1~20 (第 21 步放魔方只看总览)


def recipes():
    parts = model.build()
    steps = {k: [p for p in parts if p.step == k] for k in range(1, LAST + 2)}
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

    S = steps
    blade = S[1][16:32]  # L 模块那一组底座 (四组相同)
    # 1 底座: 一组 16 件, 做 4 组
    seq(1, [
        ('两根15孔底梁摆成直角 · 做4组', [1, 6], None, '两根梁贴桌面，一横一竖。'),
        ('底梁插黑销', [2, 3, 4, 5, 7, 8], (0, -65, 0), '本侧长梁4个，另一根梁2个。'),
        ('插两根蓝色长销', [9, 10], (0, -65, 0), '1孔段朝下插梁，上面露出1孔，以后接马达底块。'),
        ('压上15x11大框', [0], (0, -85, 0), '大框长边压在本侧长梁的4个销上。'),
        ('角上插4个黑销', [12, 13, 14, 15], (0, -65, 0), '两根梁各2个。'),
        ('压上7x5角框', [11], (0, -85, 0), '与大框同层，跨过两根底梁。')], view=(25, 60), repeat=4, source=blade)
    add(1, '四组旋转合拢', old=S[1], tip='每块大框压到相邻一组底梁的销上，四角闭合。', view=(25, 75))
    # 2 竖墙
    seq(2, [('最下面一块7x5框', [2], None, ''), ('插三个黑销', [6, 7, 8], (0, -60, 0), ''),
            ('接中间框', [1], (0, -90, 0), ''), ('再插三个黑销', [3, 4, 5], (0, -60, 0), ''),
            ('接最上面的框', [0], (0, -90, 0), '三块框上下对齐，拼成7x15的墙。')], view=(62, 20))
    # 3 马达底块 (看底面)
    seq(3, [('马达底面朝上', [0], None, '底面有一排3个销孔。'), ('底面插三个黑销', [1, 2, 3], (0, 65, 0), ''),
            ('第一层5孔垫梁', [4], (0, 85, 0), '扣在梁的第2、3、4孔。'), ('两端各插一个黑销', [5, 6], (0, 65, 0), ''),
            ('第二层5孔垫梁', [7], (0, 85, 0), '两层对齐。')], view=(55, -35))
    # 4 马达前梁
    seq(4, [('颈部插蓝色长销和黑销', [0, 1], (65, 0, 0), '蓝色长销在上孔，1孔段插进马达。'), ('压上3孔竖梁', [2], (65, 0, 0), ''),
            ('中孔补一个黑销', [3], (65, 0, 0), ''), ('接两根横梁', [4, 5], (85, 0, 0), '11孔在上、7孔在下，都朝竖墙伸出。')],
        context=S[3][:1], view=(65, 20))
    # 5 齿轮
    seq(5, [('7号轴插到底', [0], (100, 0, 0), '另一头和马达背面输出盘基本齐平。'), ('第一个半轴套', [1], (85, 0, 0), ''),
            ('第二个半轴套', [2], (85, 0, 0), ''), ('一个整轴套', [3], (85, 0, 0), ''), ('24齿齿轮', [4], (85, 0, 0), ''),
            ('最外面半轴套', [5], (65, 0, 0), '套到轴头。')], context=S[3][:1], view=(50, 20))
    # 6 装马达
    motor = S[3] + S[4] + S[5]
    seq(6, [('横梁插四个黑销', [0, 1, 2, 3], (55, 0, 0), '11孔梁3个，7孔梁1个。')], context=S[4], view=(65, 20))
    add(6, '马达整体平推到竖墙背面', old=S[2], moving=motor + S[6], delta=(-100, 0, 0), tip='四个销同时对孔；底块下表面与墙底平齐。', view=(65, 20))
    # 7 转盘下半 + 竖墙侧梁
    seq(7, [('下半转盘凸台塞进最上面的框', [0], (75, 0, 0), '没有齿的一半；圆盘边沿贴住框架正面。'),
            ('一侧从外面插3根蓝色长销', [1, 2, 3], (0, 0, 60), '2孔段朝里，穿框架短边进凸耳；挡肩贴框外。'),
            ('另一侧也插3根', [4, 5, 6], (0, 0, -60), '上中下三个孔全部插满。'),
            ], context=S[2], view=(70, 18))
    wall_tt = S[2] + S[7][:7]
    seq(7, [('中框侧面插2个黑销和1根蓝色长销', [8, 9, 10], (0, 0, 60), '最下面用蓝色长销，露出的1孔段以后接斜撑。'),
            ('压上9孔侧梁', [7], (0, 0, 85), '上3孔套蓝色长销露出的一段，下3孔套黑销。')], context=wall_tt, view=(20, 15))
    seq(7, [('另一侧：中框插3个黑销', [12, 13, 14], (0, 0, -60), ''),
            ('另一侧压上9孔侧梁', [11], (0, 0, -85), '上下两块框在两侧锁成一体。')], context=wall_tt + S[7][7:11], view=(160, 15))
    # 8 装竖墙
    seq(8, [('大框短边插两个黑销', [0, 1], (0, -60, 0), '长边上的蓝色长销第1步已插好。')], context=blade, view=(40, 40))
    wall = sum((S[k] for k in range(2, 8)), [])
    add(8, '竖墙和马达一起往下压', old=blade + S[8], moving=wall, delta=(0, -140, 0), tip='墙底两个销、马达底块两个长销同时对孔。', view=(40, 30))
    # 9 舵机平台
    platform = seq(9, [('两根15孔梁平行摆好', [1, 2], None, '两梁相距4个孔。'),
                       ('插六个黑销', [3, 4, 5, 6, 7, 15], (0, -60, 0), '另一根梁中间两个孔留给蓝色长销。'),
                       ('扣上7x5平台框', [0], (0, -90, 0), '框前端与梁前端对齐。'),
                       ('垫梁位置插三个黑销', [9, 10, 11], (0, -60, 0), ''),
                       ('压上7孔垫梁', [8], (0, -70, 0), '第3、7孔空着，留给舵机耳朵。'),
                       ('后端插两个黑销', [17, 18], (0, -60, 0), ''),
                       ('压上5孔后横梁', [16], (0, -70, 0), '后段围成封闭长方形。'),
                       ('插两根蓝色长销', [13, 14], (0, -65, 0), '2孔段朝下，穿平台框和梁。'),
                       ('立起导向框', [12], (0, -100, 0), '短边正中的孔是推杆轴承。')], view=(30, 40))
    add(9, '翻过来：梁下挂两个55615', S[9][19:21], platform, (0, 75, 0), '两个前后错开一孔，按图对位。', view=(30, -35))
    # 10 舵机
    seq(10, [('舵机放到垫梁上', [0], (0, -75, 0), '输出轴朝推杆一侧。'),
             ('耳朵插两根蓝色长销', [1, 2], (0, -60, 0), '1孔段朝下插进垫梁。')], context=S[9], view=(30, 40))
    # 11 装平台
    seq(11, [('底座后短边插55615', [2], (0, -70, 0), '两个朝下的销插进短边。')], context=blade[:1], view=(40, 30))
    seq(11, [('平台前端插两个黑销', [0, 1], (-60, 0, 0), '沿推杆方向。')], context=S[9][:1], view=(130, 25))
    add(11, '平台整体向前推进竖墙', old=S[2], moving=S[9] + S[10] + S[11][:2], delta=(-100, 0, 0), tip='导向框轴承孔与转盘中心同轴。', view=(130, 25))
    seq(11, [('马达侧：55615上插两个黑销', [4, 5], (0, 0, -60), ''), ('压上9孔竖梁', [3], (0, 0, -90), '下端接底座上的55615。')],
        context=[S[9][19], S[11][2]], view=(-140, 22))
    seq(11, [('舵机侧：插三个黑销', [7, 8, 9], (0, 0, 60), '上面两个进55615，下面一个进大框长边。'), ('压上9孔竖梁', [6], (0, 0, 90), '')],
        context=[S[9][20], blade[0]], view=(40, 22))
    seq(11, [('舵机侧斜撑：平台框侧孔插黑销', [10], (0, 0, 60), '平台框侧边从前数第3个侧孔。'),
             ('压上7孔斜撑', [11], (0, 0, 90), '第1孔套竖墙侧梁下部露出的蓝色长销，第6孔套黑销。')],
        context=S[2] + S[7] + S[9] + S[11][:2], view=(170, 15))
    # 12 十字块和舵机连杆
    seq(12, [('十字块：圆孔在上', [0], None, '圆孔以后穿推杆；下面的十字孔接连杆轴。'),
             ('穿3号轴', [3], (0, 0, 70), ''), ('背面半轴套', [4], (0, 0, -65), ''),
             ('7孔粗连杆第1孔', [9], (0, 0, 75), '粗梁直接贴十字块。'), ('外端半轴套', [5], (0, 0, 65), '')], view=(42, 22))
    seq(12, [('曲柄套2号轴', [6, 7], (0, 0, 65), '2号轴穿曲柄和连杆第7孔；首次装配先不连。'),
             ('2号轴内端半轴套', [8], (0, 0, -65), '贴住连杆。')], context=[S[12][9], S[10][0]], view=(42, 22))
    add(12, '准备两个半轴套', S[12][1:3], old=[S[12][0], S[9][12]], tip='第19步穿推杆时套在十字块两侧，先不固定。', view=(30, 25))
    # 13 侧板: 每侧 9 件 (+z 侧 0~8, -z 侧 9~17)
    for off, sign in ((0, 1), (9, -1)):
        side = '第一侧' if sign > 0 else '另一侧'
        seq(13, [(side + '：内侧一长一短两段梁', [off + 2, off + 3], None, '中间空出连杆通道；两侧长短段上下相反。'),
                 ('插三根蓝色长销', [off + 5, off + 6, off + 7], (0, 0, 60 * sign), '1孔段插进内侧梁，挡肩贴梁面。'),
                 ('压上两根L形梁', [off, off + 1], (0, 0, 85 * sign), '短臂在靠魔方一头，一根朝上、一根朝下。'),
                 ('补一个黑销', [off + 8], (0, 0, 60 * sign), '内侧没有梁的那个孔。'),
                 ('压上外侧7孔梁', [off + 4], (0, 0, 85 * sign), '把上下两根L形梁连成一体。')],
            view=(40, 20) if sign > 0 else (140, 20))
    # 14 转盘上半与推杆导向
    sides = S[13]
    top = seq(14, [('取转盘上半', [0], None, '有齿的一面朝后；正面两侧各一个3孔凸耳。'),
                   ('39793连接块放进两个凸耳之间', [1], (90, 0, 0), '正面中心孔对准转盘中心，侧面孔对准凸耳上下孔。'),
                   ('从外面插4根蓝色长销', [2, 3, 4, 5], 'out', '2孔段朝里，穿过凸耳插进方块；挡肩贴凸耳外面。')], view=(60, 20))
    add(14, '两套侧板压到露出的销上', old=top, moving=sides, delta='out', tip='L形梁长臂后端的孔套住露出的1孔段。', view=(60, 20))
    # 15 夹指与防翻折限位
    inner = [p for p in S[13] if p.note in ('内侧长段', '内侧短段')]
    for off, title in ((0, '下夹指'), (15, '上夹指')):
        seq(15, [(title + '：放到两侧梁之间', [off], None, '第4孔是根轴孔；夹指朝魔方。'),
                 ('两侧各一个整轴套', [off + 2, off + 3], None, '扶住，准备穿根轴。'),
                 ('穿8号根轴', [off + 1], (0, 0, 120), '穿内侧梁、整轴套、夹指，再穿另一侧。'),
                 ('限位支架黑销', [off + 8, off + 11], {off + 8: (0, 0, -65), off + 11: (0, 0, 65)}, '插在内侧梁的端孔。'),
                 ('一侧两片L形薄梁', [off + 6, off + 7], (0, 0, -85), '末端十字孔套根轴，中孔套黑销。'),
                 ('另一侧两片L形薄梁', [off + 9, off + 10], (0, 0, 85), '每侧叠两片。'),
                 ('根轴两端半轴套', [off + 4, off + 5], 'out', '夹指仍能自由转动。'),
                 ('穿8号开限位挡轴', [off + 12], (0, 0, 120), ''),
                 ('挡轴两端半轴套', [off + 13, off + 14], 'out', '正常张开时碰不到挡轴。')], context=inner, view=(40, 22))
    # 16 压头
    for off, jaw, title in ((0, 0, '下压头'), (9, 15, '上压头')):
        old = seq(16, [(title + '：轮胎套上轮毂', [off + 7, off + 8], None, '42610轮毂＋50945轮胎。'),
                       ('穿2号轮轴', [off + 6], (0, 0, 65), ''),
                       ('两片4孔薄梁夹住轮毂', [off, off + 1], 'out', '第4孔（十字孔）套轮轴，两端齐平。')], view=(40, 22))
        add(16, '压头对准主臂前端', old=[S[15][jaw]], moving=old, delta=(65, 0, 0), tip='薄梁第1、2孔对主臂第6、7孔。', view=(40, 22))
        seq(16, [('第6孔穿3号轴', [off + 2], (0, 0, 75), ''), ('第7孔插红色挡套长销', [off + 5], (0, 0, -70), ''),
                 ('3号轴两端半轴套', [off + 3, off + 4], 'out', '轮毂能转动。')], context=old + [S[15][jaw]], view=(40, 22))
    # 17 连杆与十字接头
    jaws = [S[15][0], S[15][15]]
    seq(17, [('主臂第2孔插灰色销', [5, 7], {5: (0, 0, 65), 7: (0, 0, -65)}, '上下两个夹指各一个，从外侧插。'),
             ('套上两根5孔连杆', [4, 6], {4: (0, 0, 75), 6: (0, 0, -75)}, '连杆另一端朝中间汇合。'),
             ('十字接头放进两根连杆之间', [0], (70, 0, 0), '圆孔对准连杆端孔，十字孔朝后。'),
             ('穿4号轴', [1], (0, 0, 90), ''),
             ('两端半轴套', [2, 3], 'out', '连杆要能自由转动。')], context=jaws + inner, view=(42, 22))
    # 18 推杆
    add(18, '准备推杆：一根12号轴', S[18], tip='下一步装好机械头后，从平台后面穿入。', view=(30, 25))
    # 19 装机械头
    head = sum((S[k] for k in range(13, 18)), [])
    add(19, '机械头扣到转盘下半上', old=S[2] + S[7], moving=head, delta=(90, 0, 0), tip='转盘两半直接卡合，不用销。', view=(60, 20))
    path = [S[9][12], S[12][0]] + S[12][1:3]
    add(19, '推杆从平台后面穿入', old=path + head, moving=S[18], delta=(-180, 0, 0),
        tip='穿导向框后孔、半轴套、十字块、半轴套、前孔、转盘、导向，插进十字接头到底。', view=(25, 25))
    add(19, '断电手推推杆检查', old=path + head + S[18], tip='曲柄暂不连接；活动平顺后按单臂标定步骤连接舵机。', view=(40, 25))
    # 20 另外三个机械手
    for arm, title in (('R', '对面机械手'), ('F', '前侧机械手'), ('B', '后侧机械手')):
        module = [p for p in S[20] if p.arm == arm]
        base = S[1][16 * model.ARMS.index(arm):16 * (model.ARMS.index(arm) + 1)]
        add(20, title + '：重复第2~19步', module, base, None, '按第8、11步接底座，第19步装机械头。', view=(35, 35), tray=False)
    expected = Counter((p.step, p.name, p.color) for p in parts if p.step <= LAST)
    assert counts == expected, ('分步零件覆盖不一致', expected - counts, counts - expected)
    assert all(used[id(p)] == 1 for p in parts if 2 <= p.step <= LAST), '新增零件漏装或重复计数'
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
        label='使用已装好的组件' if not tally else '按第2~19步制作这一整臂'
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


def main():
    global model_parts
    parser=argparse.ArgumentParser();parser.add_argument('--step',type=int);parser.add_argument('--check',action='store_true')
    parser.add_argument('--workers',type=int,default=3)
    args=parser.parse_args();cards,model_parts=recipes()
    print(f'{len(cards)}分步图；第1~{LAST}步新增件与模型BOM一致。',flush=True)
    if args.check:return
    dest=OUT/'assembly.json'
    model_hash=hashlib.sha256(model.to_ldr(model_parts).encode()).hexdigest()
    if args.step and dest.exists() and json.loads(dest.read_text())['model_sha256'] != model_hash:
        raise ValueError('模型已改变，必须先全量生成，不能合并旧模型的分步图')
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
