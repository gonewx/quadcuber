"""第16步后架两种三孔梁摆法：真实网格对照，不改变正式模型。"""
from coarse_rear import *
import importlib.util
import base64

OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('rear_software',ROOT/'tools/lego/render/software.py')
software=importlib.util.module_from_spec(spec);spec.loader.exec_module(software)


def main():
    original=m.module(0,steps=False)
    keeper=next(p for p in original if p.note=='齿轮外限位')
    # 用户只说明“原2孔梁的位置”；此处明确画出本次对该位置的理解。
    t=next(p for p in original if p.name=='18938.dat');origin=t.pos-m.TT_C
    upper=m.Part('32523.dat',25,np.array([-270.,-20.,-80.])+origin,m.BEAM_X_HOLES_Z,t.step,'上侧三孔粗梁假设')
    collisions=[];distances=[]
    for angle in range(361):
        p=upper.moved(m.rot_x(angle))
        gap=fcl.distance(mesh.obj(p),mesh.obj(keeper),fcl.DistanceRequest(),fcl.DistanceResult())*.4
        distances.append([angle,gap])
        if gap<=1e-8:collisions.append(angle)
    report={'摆法说明':'32526放在Z=-60下侧长边；32523放在Z=-80，沿X，三个孔X=-290/-270/-250、Y=-20。仅代表对用户位置描述的这一种理解。',
            '角度步长_度':1,'相交角度_度':collisions,'零度间隙_mm':distances[0][1],'注意':'只检查此三孔梁与静止齿轮外半轴套；不等于完整连接方案或用户实物摆法。'}
    (OUT/'upper-three-hole-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))
    common=[]
    for p in convert(original):
        if p.name=='18938.dat' or p.note in {'齿轮外限位'} or (p.pos[2]<0 and p.note in {'侧架长梁','粗梁后接架'}):
            q=p.moved(m.I)
            q.color=2 if p.note=='粗梁后接架' else 71
            if p.note=='齿轮外限位':q.color=4
            common.append(q)
    lower=next(p for p in convert(original) if p.note=='后接架三孔垫梁' and p.pos[2]<0).moved(m.I);lower.color=25
    variants=[('lower',common+[lower],138,22),('upper',common+[upper],138,22)]
    for name,parts,yaw,pitch in variants:
        path=OUT/(name+'.ldr');path.write_text(m.to_ldr(parts,'后架位置对照'))
        software.render({'model':str(path),'out':str(OUT/(name+'.png')),'opts':{'w':740,'h':540,'yaw':yaw,'pitch':pitch,'margin':.06}})
    def data(name):return base64.b64encode((OUT/(name+'.png')).read_bytes()).decode()
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1560" height="820" viewBox="0 0 1560 820">
<rect width="1560" height="820" fill="white"/><g font-family="sans-serif" fill="#172536">
<text x="35" y="48" font-size="30" font-weight="bold">第16步：区别在3孔粗梁的位置，3×5 L梁可以保留</text>
<text x="35" y="88" font-size="22">绿色：3×5 L粗梁　橙色：3孔粗梁　红色：齿轮外侧半轴套　灰色：原有零件</text>
<text x="35" y="137" font-size="25" font-weight="bold">A　已试的后架候选</text><text x="805" y="137" font-size="25" font-weight="bold">B　我对“原2孔梁位置”的理解</text>
<image x="15" y="155" width="740" height="540" href="data:image/png;base64,{data('lower')}"/>
<image x="785" y="155" width="740" height="540" href="data:image/png;base64,{data('upper')}"/>
<text x="35" y="715" font-size="22">3孔梁在下侧，垫在L梁长边与侧长梁之间。</text>
<text x="35" y="750" font-size="21">新增件初筛无相交；尚未验证实物刚度。</text>
<text x="805" y="715" font-size="22">3孔梁在上侧，其后孔与转盘安装孔同轴。</text>
<text x="805" y="750" font-size="21">这一叠法转动时会碰红色轴套；未断定你的摆法相同。</text>
<text x="35" y="797" font-size="19" fill="#526171">局部位置示意，省略销轴及其他结构；不是完整装配图。第19、20步连杆换件是另一项问题。</text>
</g></svg>'''
    (OUT/'rear-comparison.svg').write_text(svg)

if __name__=='__main__':main()
