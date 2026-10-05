"""竖L向前一孔候选：回转、实际关节和理想刚体约束检查。"""
from vertical_forward import *
import vertical_forward as v
orig_module=m.module
m.module=lambda *a,**k:v.convert(orig_module(*a,**k))
report_path=Path(__file__).resolve().parent/'vertical-forward-check.json'
data=json.loads(report_path.read_text())
worst=None;hits=[];states=0;queries=0
for stroke in (0.,m.OPEN_S):
    for angle in range(0,360,5):
        for other in (0.,m.OPEN_S):
            ps=m.build({'L':(stroke,angle),'F':(other,0.),'B':(other,0.)},with_cube=False)
            moving=[p for p in ps if p.arm=='L' and p.note in v.NEW]
            fixed=[p for p in ps if p.arm in ('F','B') or (p.arm=='L' and not p.head)]
            bb=[check._obb(p) for p in fixed];flo=np.array([a for a,b in bb]);fhi=np.array([b for a,b in bb]);states+=1
            for a in moving:
                lo,hi=check._obb(a)
                for index in np.flatnonzero(np.linalg.norm(np.maximum(np.maximum(flo-hi,lo-fhi),0),axis=1)<5):
                    b=fixed[index]
                    if mesh.fitting(a,b):continue
                    gap=fcl.distance(mesh.obj(a),mesh.obj(b),fcl.DistanceRequest(),fcl.DistanceResult())*.4;queries+=1
                    row={'角度_度':angle,'开度比例':stroke/m.OPEN_S,'邻臂开度比例':other/m.OPEN_S,'间隙_mm':gap,'零件对':[a.name,a.note,b.name,b.note]}
                    if worst is None or gap<worst['间隙_mm']:worst=row
                    if gap<=1e-8:hits.append(row)
# 四个刚体：下3L、上2L、竖L、前侧架。转盘固定；尺寸除20避免单位条件数。
joints=[(-1,0,(-290,20)),(-1,1,(-290,-20)),(0,2,(-270,20)),(0,2,(-250,20)),(1,2,(-270,-20)),(2,3,(-270,-20)),(2,3,(-250,20))]
rows=[]
for a,b,(x,y) in joints:
    point=np.array([(x+270)/20,y/20]);jac=np.array([[1,0,-point[1]],[0,1,point[0]]]);r=np.zeros((2,12))
    if a>=0:r[:,3*a:3*a+3]-=jac
    r[:,3*b:3*b+3]+=jac;rows.extend(r)
sv=np.linalg.svd(rows,compute_uv=False)
data['新增后架对本臂固定件及两邻臂回转']={'状态数':states,'角度步长_度':5,'距离查询数':queries,'相交数':len(hits),'相交记录':hits,'最小候选距离':worst,'AABB阈值_mm':2.0}
data['平面刚体约束']={'自由度列数':12,'约束矩阵秩':int(np.linalg.matrix_rank(rows)),'最小奇异值':float(sv.min()),'假设':'前侧架沿用原两点连接形成刚体；销孔理想无间隙。结果排除自由铰链，不预测塑料弹性、孔隙或手感。'}
report_path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:data[k] for k in ('新增后架对本臂固定件及两邻臂回转','平面刚体约束')},ensure_ascii=False,indent=2))
