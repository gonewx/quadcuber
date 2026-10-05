"""保持实际上下方向，补全马达、齿轮和半轴套的后架核对图。"""
from vertical_rear import *
import importlib.util
import base64
OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('oriented_software',ROOT/'tools/lego/render/software.py')
software=importlib.util.module_from_spec(spec);spec.loader.exec_module(software)
ps=convert(m.module(0,steps=False));chosen=[]
for p in ps:
    motor=p.name=='95658.dat'
    gear=(p.name=='3648b.dat' or (abs(p.pos[2]+100)<1e-7 and p.name in {'44294.dat','3713.dat','32123a.dat'}))
    tt=p.name in {'18938.dat','18939.dat'}
    frame=p.pos[2]<0 and (p.note in NEW|{'侧架长梁','前角梁','前角连接销'} or (p.name=='32525.dat' and p.head))
    if motor or gear or tt or frame:
        q=p.moved(m.I)
        if p.note=='齿轮外限位':q.color=4
        elif gear:q.color=72
        chosen.append(q)

def panel(name,parts,w,h):
    opts={'w':w,'h':h,'yaw':25,'pitch':0,'margin':.09}
    path=OUT/(name+'.ldr');path.write_text(m.to_ldr(parts,'上下方向核对'))
    software.render({'model':str(path),'out':str(OUT/(name+'.png')),'opts':opts})
    yaw=np.radians(25);direction=np.array([np.sin(yaw),0,np.cos(yaw)]);right=np.array([np.cos(yaw),0,-np.sin(yaw)]);up=np.cross(direction,right)
    camera=np.diag([1,-1,-1])@np.stack([right,up,direction],axis=1)
    vertices=np.concatenate([(ldraw.geometry(p.name)[0]@p.rot.T+p.pos).reshape(-1,3)@camera for p in parts])
    lo,hi=vertices[:,:2].min(axis=0),vertices[:,:2].max(axis=0);scale=min(w/(hi[0]-lo[0]),h/(hi[1]-lo[1]))*.82
    def project(point):return ((np.array(point)@camera)[:2]-(lo+hi)/2)*[scale,-scale]+[w/2,h/2]
    return project
p1=panel('oriented-overview',chosen,660,670)
detail=[p for p in chosen if p.name!='95658.dat' and p.name!='44294.dat']
p2=panel('oriented-detail',detail,850,520)
def data(n):return base64.b64encode((OUT/(n+'.png')).read_bytes()).decode()
# 右侧视图标出真实投影位置。
keeper=next(p for p in detail if p.note=='齿轮外限位');gear=next(p for p in detail if p.name=='3648b.dat');beam=next(p for p in detail if p.note=='竖L后架');short=next(p for p in detail if p.note=='竖架三孔梁')
def line(p,x,y,text,color='#24364b'):
    a,b=p2(p);a+=700;b+=180
    return f'<path d="M{x},{y+7} L{a:.1f},{b:.1f}" stroke="{color}" stroke-width="2" fill="none"/><circle cx="{a:.1f}" cy="{b:.1f}" r="4" fill="{color}"/><text x="{x}" y="{y}" font-size="21" fill="{color}" paint-order="stroke" stroke="white" stroke-width="6">{text}</text>'
svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1580" height="950" viewBox="0 0 1580 950"><defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto"><path d="M0,0 L9,4.5 L0,9" fill="#233c55"/></marker></defs><rect width="1580" height="950" fill="white"/><g font-family="sans-serif" fill="#172536">
<text x="32" y="45" font-size="30" font-weight="bold">后接架方向核对 · 头部未回转</text>
<text x="32" y="88" font-size="24">页面上方＝实际上方　｜　左边朝马达（后）　｜　右边朝魔方（前）</text>
<text x="32" y="141" font-size="24" font-weight="bold">整体位置：马达、齿轮、转盘与侧架</text><text x="725" y="141" font-size="24" font-weight="bold">同方向放大：竖L与3孔粗梁</text>
<image x="15" y="180" width="660" height="670" href="data:image/png;base64,{data('oriented-overview')}"/>
<image x="700" y="180" width="850" height="520" href="data:image/png;base64,{data('oriented-detail')}"/>
<path d="M75,355 L75,215" stroke="#233c55" stroke-width="4" marker-end="url(#arrow)"/><text x="35" y="197" font-size="25" font-weight="bold">上 ↑</text>
<path d="M75,660 L75,790" stroke="#233c55" stroke-width="4" marker-end="url(#arrow)"/><text x="35" y="826" font-size="25" font-weight="bold">下 ↓</text>
{line(keeper.pos,720,725,'红色：原齿轮外侧半轴套','#b32626')}
{line(gear.pos,720,765,'24齿齿轮（与转盘啮合）')}
{line(beam.world([0,0,20]),1110,208,'绿色：5孔长边竖放','#176f37')}
{line(short.pos,1130,805,'橙色：3孔粗梁','#9b5700')}
<path d="M1020,861 L1480,861" stroke="#233c55" stroke-width="3" marker-end="url(#arrow)"/><text x="1020" y="897" font-size="23">朝魔方／前 →</text>
<text x="35" y="911" font-size="20">仅核对摆法；远侧零件及活动连杆省略。绿色、橙色、红色为说明用配色。</text>
</g></svg>'''
(OUT/'rear-orientation.svg').write_text(svg)
