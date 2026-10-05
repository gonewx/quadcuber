"""竖向后架的静态连接与回转相交位置。"""
from vertical_rear import *
import importlib.util
import base64
OUT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('vertical_software',ROOT/'tools/lego/render/software.py')
software=importlib.util.module_from_spec(spec);spec.loader.exec_module(software)
ps=convert(m.module(0,steps=False))
keeper=next(p for p in ps if p.note=='齿轮外限位');keeper.color=4
local=[p for p in ps if (p.note in NEW and p.pos[2]<0) or (p.note=='侧架长梁' and p.pos[2]<0) or p.name=='18938.dat']
for p in local:
    if p.name=='18938.dat':p.color=71
for name,angle,yaw,pitch,include_tt in [('vertical-static',0,138,22,True),('vertical-hit',45,270,0,False)]:
    parts=[p.moved(m.rot_x(angle)) for p in local if include_tt or p.name!='18938.dat']+[keeper]
    if name=='vertical-hit':
        parts=[p for p in parts if p.note in {'竖L后架','齿轮外限位'}]
    path=OUT/(name+'.ldr');path.write_text(m.to_ldr(parts,'竖放后架局部核对'))
    software.render({'model':str(path),'out':str(OUT/(name+'.png')),'opts':{'w':760,'h':540,'yaw':yaw,'pitch':pitch,'margin':.07}})
# 输出具体相交接触点，供核对。
a=next(p for p in local if p.note=='竖L后架').moved(m.rot_x(45))
r=fcl.CollisionResult();fcl.collide(mesh.obj(a),mesh.obj(keeper),fcl.CollisionRequest(num_max_contacts=8,enable_contact=True),r)
print('45度碰撞',r.is_collision,'接触点',[c.pos.tolist() for c in r.contacts])
def data(n):return base64.b64encode((OUT/(n+'.png')).read_bytes()).decode()
svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1580" height="830" viewBox="0 0 1580 830">
<rect width="1580" height="830" fill="white"/><g font-family="sans-serif" fill="#172536">
<text x="35" y="48" font-size="30" font-weight="bold">竖放核对：5孔长边靠转盘，短边朝前接3孔粗梁</text>
<text x="35" y="91" font-size="23">绿：3×5 L梁　橙：3孔粗梁　红：静止齿轮外半轴套　灰：原侧梁与转盘</text>
<text x="35" y="142" font-size="25" font-weight="bold">① 保持现有侧梁孔位的竖放候选</text>
<text x="815" y="142" font-size="25" font-weight="bold">② 回转45°，正视碰撞部位</text>
<image x="15" y="160" width="760" height="540" href="data:image/png;base64,{data('vertical-static')}"/>
<image x="805" y="160" width="760" height="540" href="data:image/png;base64,{data('vertical-hit')}"/>
<text x="35" y="725" font-size="21">转盘接长边第3、第5孔；朝前短边与3孔粗梁两点连接。</text>
<text x="815" y="725" font-size="21">省略转盘与侧架，只显示竖L梁和半轴套。</text>
<text x="35" y="763" font-size="21">连接检查通过；L梁上端多出两孔，需检查回转空间。</text>
<text x="815" y="763" font-size="21" fill="#aa2525">1°步长扫描：这一侧在38°～51°与半轴套相交。</text>
<text x="35" y="807" font-size="19" fill="#526171">本图是按现有侧梁高度建立的候选，尚未作为正式装配方案；不能据静态连接通过推断整圈能转。</text>
</g></svg>'''
(OUT/'vertical-rear-review.svg').write_text(svg)
