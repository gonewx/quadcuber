"""系统候选图：同一朝向的装配及机构视图，不作为逐件说明书。"""
from watt_candidate import *
import importlib.util
import base64
spec=importlib.util.spec_from_file_location('redesign_software',ROOT/'tools/lego/render/software.py');software=importlib.util.module_from_spec(spec);spec.loader.exec_module(software)
OUT=Path(__file__).resolve().parent

def render(name,parts,w,h):
    colored=[]
    for p in parts:
        q=p.moved(m.I)
        if p.note=='输入薄连杆':q.color=25
        elif p.note=='Watt连杆':q.color=1
        elif p.note=='Watt横梁':q.color=14
        elif p.note=='导向驱动薄梁':q.color=22
        colored.append(q)
    path=OUT/(name+'.ldr');path.write_text(m.to_ldr(colored,'机械头系统候选（设计核对）'))
    software.render({'model':str(path),'out':str(OUT/(name+'.png')),'opts':{'w':w,'h':h,'yaw':25,'pitch':0,'margin':.065}})
ps=module(0,steps=False)
# 保留整个机械头；后方马达/齿轮仅作方位参照。
main=[p for p in ps if p.head or p.name in {'95658.dat','18939.dat','3648b.dat'} or (abs(p.pos[2]+100)<1e-6 and p.name in {'44294.dat','3713.dat','32123a.dat'})]
render('head-overview',main,1200,780)
notes={'输入薄连杆','输入无摩擦关节销','输入关节轴','输入关节轴套','输入外半套','Watt公共轴','Watt横梁','公共轴半套','Watt连杆','Watt根轴','导向根轴限位','Watt活动轴','活动轴半套','导向驱动共用轴','导向驱动中套','导向驱动薄梁','Watt支架','推杆铰接头','推杆铰轴','推杆铰轴半套','推杆短轴','推杆连接器','压头支承薄梁','薄梁固定轴','薄梁固定轴限位','薄梁固定挡套销','轮毂贯穿轴','轮毂','橡胶胎','压头补厚梁','压头第二轴限位','轮毂内隔套'}
for name,s in [('mechanism-closed',0.),('mechanism-open',m.OPEN_S)]:
    ps=module(s,steps=False)
    selected=[p for p in ps if p.note in notes or (p.name=='32524.dat' and p.color==m.C_JAW)]
    render(name,selected,760,520)
def data(n):return base64.b64encode((OUT/(n+'.png')).read_bytes()).decode()
svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1580" height="900" viewBox="0 0 1580 900"><rect width="1580" height="900" fill="white"/><g font-family="sans-serif" fill="#172536">
<text x="30" y="45" font-size="30" font-weight="bold">机械头系统候选：粗梁连杆＋双侧承重导向</text><text x="30" y="88" font-size="23">↑ 实际上方　　左：推杆／马达（后）　　右：轮胎压头／魔方（前）　　↓ 实际下方</text>
<text x="30" y="136" font-size="23">橙：5孔粗输入杆　蓝：5孔粗摆杆　黄：带十字端孔的导向横梁　紫：短驱动连接</text>
<text x="30" y="183" font-size="26" font-weight="bold">夹紧端</text><text x="815" y="183" font-size="26" font-weight="bold">松开端 · 最大夹指角25°</text>
<image x="15" y="200" width="760" height="520" href="data:image/png;base64,{data('mechanism-closed')}"/>
<image x="800" y="200" width="760" height="520" href="data:image/png;base64,{data('mechanism-open')}"/>
<text x="30" y="757" font-size="23">两根紫色4孔薄梁使用中间两个圆孔铰接；端部十字孔留空。</text>
<text x="30" y="800" font-size="23">推杆连接导向横梁后端；两根橙色输入杆绕中间公共轴分别转动。</text>
<text x="30" y="843" font-size="23">轮胎仍在原中心面；夹指主梁的横向错位由压头支架补回。</text>
<text x="30" y="884" font-size="19" fill="#576575">为看清运动关系，图中省略固定侧架、后架和推杆后段。此图用于设计核对，尚未发布装配步骤。</text>
</g></svg>'''
(OUT/'mechanism-review.svg').write_text(svg)
svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1260" height="970" viewBox="0 0 1260 970"><rect width="1260" height="970" fill="white"/><g font-family="sans-serif" fill="#172536"><text x="30" y="43" font-size="29" font-weight="bold">系统候选整体：上、下按实际安装方向</text><text x="30" y="86" font-size="23">↑ 上　　左：马达／后　　右：魔方／前　　↓ 下</text><image x="30" y="110" width="1200" height="780" href="data:image/png;base64,{data('head-overview')}"/><text x="30" y="926" font-size="23">马达、24齿齿轮和转盘均保留；图中粗梁后架已向前让出一孔。</text><text x="30" y="960" font-size="18" fill="#576575">设计核对图；后部底座省略，不能直接代替搭建说明书。</text></g></svg>'''
(OUT/'head-overview.svg').write_text(svg)
