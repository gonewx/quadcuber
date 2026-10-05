"""候选验证汇总；离散采样不等于连续扫掠证明。"""
import json,hashlib,math
from pathlib import Path
import numpy as np
import boxed_slider as w
P=Path(__file__).parent
r=w.scan(81)
r['source_sha256']=hashlib.sha256((P/'boxed_slider.py').read_bytes()).hexdigest()
(P/'boxed-check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
# 魔方为56mm实心盒；允许轮胎在夹紧端接触，只报告其他硬件。
box=w.fcl.CollisionObject(w.fcl.Box(140,140,140))
hits=[];smallest=1e6;count=0
for fraction,angle in [(float(f),0) for f in np.linspace(0,1,81)]+[(1.,a) for a in range(0,360,5)]:
 for p in w.module(fraction*w.OPEN_S,angle):
  if not p.head or p.name=='50945_nominal.dat':continue
  dist=w.fcl.distance(w.mesh.obj(p),box,w.fcl.DistanceRequest(),w.fcl.DistanceResult())*.4
  smallest=min(smallest,dist);count+=1
  if dist<=1e-8:hits.append([fraction,angle,p.name,p.note])
cube={'状态数':153,'距离查询数':count,'非轮胎最小间隙_mm':smallest,'相交':hits,'轮胎':'夹紧接触面单列；松开回转另查'}
smallest=1e6
for angle in range(0,360,5):
 for p in w.module(w.OPEN_S,angle):
  if p.name=='50945_nominal.dat':smallest=min(smallest,w.fcl.distance(w.mesh.obj(p),box,w.fcl.DistanceRequest(),w.fcl.DistanceResult())*.4)
cube['松开轮胎回转最小间隙_mm']=smallest
(P/'cube-check.json').write_text(json.dumps(cube,ensure_ascii=False,indent=2))
# 100g全部由一个下轮承担，叠加每轮2N夹紧预载；两侧杆理想均分。
rows=[];c=np.array([w.C0,0.,0.]);b=w.beta(0)
for angle in (0,45,90):
 total=np.zeros(3);moment=np.zeros(3);jaws=[]
 for sy in (-1,1):
  piv=np.array([-130.,80*sy,0.]);R=w.m.rot_z(b*sy);joint=piv+R@np.array([-40.,0,0]);tip=piv+R@np.array([100.,0,0])
  F=np.array([0.,sy*2.,0.])
  if sy==1:F+=np.array([0.,.980665*math.cos(math.radians(angle)),.980665*math.sin(math.radians(angle))])
  u=(c-joint)/80;tension=-np.cross(tip-piv,F)[2]/np.cross(joint-piv,u)[2]
  link=tension*u;root=F+link;total-=link
  z=30 if sy<0 else 50
  for side in (-1,1):moment+=np.cross(np.array([0.,0.,z*side*.4]),-link/2)
  outmom=np.cross((tip-piv)*.4,F)[0:2]
  jaws.append({'侧':sy,'每根输入杆轴力_N':tension/2,'根轴合力_N':root.tolist(),'轮端面外弯矩_Nmm':outmom.tolist(),'根轴32mm支承跨距产生的反力差量_N':float(np.linalg.norm(outmom)/32)})
 rows.append({'回转角_deg':angle,'夹指':jaws,'滑块输入合力_N':total.tolist(),'理想双侧输入力矩_Nmm':moment.tolist(),'推杆轴向力幅值_N':abs(float(total[0])),'导轨承受横向合力幅值_N':abs(float(total[1]))})
load={'质量_g':100,'每轮预载_N':2,'假设':'魔方重量全部分配给一个下轮；两侧输入杆均分；忽略零件自重、加速度及摩擦。面外力由根轴及骨架承担。32mm为两侧内立梁中心距。反力差量为弯矩/跨距，不含合力分配。不是实物强度或下沉预测。','算例':rows}
(P/'boxed-load.json').write_text(json.dumps(load,ensure_ascii=False,indent=2))
print(json.dumps({'开合':{k:v for k,v in r.items() if k!='source_sha256'},'魔方':cube,'承重':load},ensure_ascii=False,indent=2))
