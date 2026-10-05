"""粗梁输入/摆杆与竖向后架的系统候选，闭环为后端短驱动。"""
from pathlib import Path
import sys
import math
import json
from functools import lru_cache
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'artifacts/rear-frame-experiments'))
import coarse_inner as inner
import vertical_forward as frame
m=inner.m;check=inner.check;mesh=inner.mesh;fcl=inner.fcl;run_check=inner.run_check
# 原夹紧端C与横梁角，确定新20LDU驱动的精确起点。
OLD_OPEN_S=m.OPEN_S
OLD_OPEN_POSE=m.crosshead_pose(m.OPEN_S)
c0,t0=m.crosshead_pose(0.);u0=40*np.array([math.cos(t0),math.sin(t0),0.]);a0=c0-u0
m.DRIVE_LINK_L=20.
m.DRIVE_CLOSED_X=float(a0[0]-math.sqrt(20**2-a0[1]**2))
@lru_cache(maxsize=4096)
def pose(stroke):
    dx=m.DRIVE_CLOSED_X-stroke
    p=np.array([c0[0]-stroke,0.,(c0[0]-stroke+190)**2/(2*80*40)])
    for _ in range(40):
        x,y,t=p;u=40*np.array([math.cos(t),math.sin(t)]);du=np.array([-u[1],u[0]]);c=np.array([x,y]);a=c-u
        e1=a-m.WATT_ROOTS[0,:2];e2=c+u-m.WATT_ROOTS[1,:2];e3=a-[dx,0.]
        residual=np.array([(e1@e1-80**2)/160,(e2@e2-80**2)/160,(e3@e3-20**2)/40])
        if max(abs(residual))<1e-11:return tuple(p)
        jac=np.array([[e1[0]/80,e1[1]/80,-e1@du/80],[e2[0]/80,e2[1]/80,e2@du/80],[e3[0]/20,e3[1]/20,-e3@du/20]])
        p-=np.linalg.solve(jac,residual)
    raise ValueError('新闭环未收敛')
m._crosshead_state=pose
lo,hi=0.,30.
for _ in range(60):
    mid=(lo+hi)/2
    if max(m.jaw_beta(mid,k) for k in (-1,1))>m.OPEN_BETA:hi=mid
    else:lo=mid
m.OPEN_S=(lo+hi)/2
BASE_MODULE=m.module
# inner.convert原本试的是横L后架；换成已经完成候选检查的竖向前移后架。
inner.rear.convert=frame.convert

def module(*args,**kwargs):
    ps=inner.convert(BASE_MODULE(*args,**kwargs));out=[]
    tt=next(p for p in ps if p.name=='18938.dat');R=tt.rot@m.TT_ROT.T;origin=tt.pos-R@m.TT_C
    for p in ps:
        v=R.T@(p.pos-origin);side=1 if v[2]>=0 else -1
        if p.note in {'输入关节轴套','输入外半套'}:continue
        if p.note=='输入关节轴':
            p.name='3673.dat';p.color=71;v[2]=0;p.rot=R@m.ALONG_Z;p.note='输入无摩擦关节销'
        elif p.note=='Watt根轴':
            p.name='24316.dat';v[2]=58*side;p.rot=R@(m.LPIN_SHORT_Z if side>0 else m.ALONG_Z)
        elif p.note=='导向根轴限位' and abs(v[2])<50:continue
        p.pos=R@v+origin;out.append(p)
    return out

def scan():
    hits={};checks={};queries=0
    for frac in np.linspace(0,1,81):
        ps=module(float(frac*m.OPEN_S),steps=False)
        if frac in (0.,1.):checks[str(frac)]={k:f(ps) for k,f in [('孔型',run_check.pins_in_axle_holes),('插深',run_check.pin_depth),('长销',check.long_pins)]}
        bb=[check._obb(p) for p in ps]
        for i,a in enumerate(ps):
            for j in range(i+1,len(ps)):
                b=ps[j]
                if not (a.head or b.head) or (not a.note and not b.note):continue
                lo,hi=bb[i];low,high=bb[j]
                if np.any(np.minimum(hi,high)-np.maximum(lo,low)<=1e-7):continue
                if mesh.fitting(a,b):continue
                queries+=1;dist=fcl.distance(mesh.obj(a),mesh.obj(b),fcl.DistanceRequest(),fcl.DistanceResult())
                if dist<=1e-8:
                    if mesh.rod_socket_contact(a,b):continue
                    tt,p=(a,b) if a.name=='18938.dat' else (b,a)
                    if tt.name=='18938.dat' and p.note in {'竖架上短梁','竖架三孔梁'}:
                        normal=tt.rot[:,0];sg=np.sign((p.pos-tt.pos)@normal);q=p.moved(m.I,sg*normal*1e-4)
                        if fcl.distance(mesh.obj(q),mesh.obj(tt),fcl.DistanceRequest(),fcl.DistanceResult())>=.999e-4:continue
                    key=(a.name,a.note,b.name,b.note)
                    if key not in hits:hits[key]={'行程比例':float(frac),'位置':[a.pos.tolist(),b.pos.tolist()]}
    return {'连接检查':checks,'开度数':81,'距离查询数':queries,'相交对':[{'零件对':k,**v} for k,v in hits.items()]}
if __name__=='__main__':
    out=Path(__file__).resolve().parent
    (out/'watt-candidate.ldr').write_text(m.to_ldr(module(0,steps=False),'粗梁承重机构候选，未发布'))
    result=scan();result['推杆行程_mm']=m.OPEN_S*.4;result['全圆孔薄梁数量']=sum(p.name=='32017.dat' for p in module(0,steps=False))
    (out/'watt-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
