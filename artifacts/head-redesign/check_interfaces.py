from watt_candidate import *
from collections import Counter
import rod_support_analysis as rods
m.module=module
rod=[]
for stroke in np.linspace(0,m.OPEN_S,81):
    ps=module(float(stroke),steps=False)
    shafts=[p for p in ps if p.note in ('推杆短轴','推杆长轴')]
    ends=[p.pos[0]+v for p in shafts for v in check.connector_bounds(p.name)]
    rear=next(p for p in shafts if p.note=='推杆长轴');lo,hi=check.connector_bounds(rear.name)
    bearings=[(x+m.MODULE_DX-10,x+m.MODULE_DX+10) for x in m.ROD_BEARING_X]
    margin=min(min(a-rear.pos[0]-lo,rear.pos[0]+hi-b) for a,b in bearings)*.4
    sleeve=next(p for p in ps if p.note=='推杆连接器')
    gap=(check._obb(sleeve)[0][0]-max(b for a,b in bearings))*.4
    rod.append({'总长_mm':(max(ends)-min(ends))*.4,'覆盖余量_mm':margin,'连接器到轴承_mm':gap})
assert min(r['覆盖余量_mm'] for r in rod)>0
assert min(r['连接器到轴承_mm'] for r in rod)>0
newc,newt=m.crosshead_pose(m.OPEN_S)
assert np.linalg.norm(newc-OLD_OPEN_POSE[0])<1e-8
assert abs(newt-OLD_OPEN_POSE[1])<1e-8
# 压头保持中心面、根轴和固定框架参考位置不变。
wheel_z=[];errors=[]
for s in np.linspace(0,m.OPEN_S,81):
    ps=module(float(s),steps=False)
    for p in ps:
        if p.note=='橡胶胎':wheel_z.append(float(p.pos[2]))
    if any(p.name=='32017.dat' for p in ps):errors.append('仍使用全圆孔薄梁')
assert max(abs(v) for v in wheel_z)<1e-8
result={'旧推杆行程_mm':OLD_OPEN_S*.4,'新推杆行程_mm':m.OPEN_S*.4,'松开端公共轴差_mm':float(np.linalg.norm(newc-OLD_OPEN_POSE[0]))*.4,'轮胎偏离原中心面最大值_mm':max(abs(v) for v in wheel_z)*.4,'推杆支承':rod,'问题':errors}
Path(__file__).with_name('interfaces.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='推杆支承'},ensure_ascii=False,indent=2));print('rod',rod[0],rod[-1])
