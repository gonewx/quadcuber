"""验证长边居中摆法的回转和孔位差，避免把一种竖放当作全部竖放。"""
from vertical_rear import *
parts=m.module(0,steps=False)
tt=next(p for p in parts if p.name=='18938.dat');origin=tt.pos-m.TT_C
keeper=next(p for p in parts if p.note=='齿轮外限位')
rows=[]
for y0 in (-60,-40,-20):
    p=m.Part('32526.dat',2,np.array([-290.,y0,-60.])+origin,m.orient('+x','-z','+y'),tt.step,'竖放位置枚举')
    hits=[];minimum=float('inf')
    for angle in range(360):
        d=fcl.distance(mesh.obj(p.moved(m.rot_x(angle))),mesh.obj(keeper),fcl.DistanceRequest(),fcl.DistanceResult())*.4
        minimum=min(minimum,d)
        if d<=1e-8:hits.append(angle)
    rows.append({'转盘两销对应长边孔序':[int((-20-y0)/20+1),int((20-y0)/20+1)],'短边高度_LDU':y0+80,'相对现有下侧梁高度差_mm':(y0+80-20)*.4,'最小网格间隙_mm':minimum,'相交角度_度':hits})
print(json.dumps(rows,ensure_ascii=False,indent=2))
Path(__file__).with_suffix('.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
