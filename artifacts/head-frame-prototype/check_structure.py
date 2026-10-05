"""固定骨架的空间铰接约束秩；把圆孔连接保守地视为理想转动副。"""
import json
from pathlib import Path
import numpy as np
import boxed_slider as w
NAMES={'转盘上半','后整体框','前整体框','侧整体框','侧承重直梁','后框侧垫梁','夹指根立梁','根轴内侧支承梁','转盘T形接口梁','中间承重直梁','前框中梁连接梁','导轨座横梁','导轨固定孔座','前固定导轨块','前导轨T支板','根架间隔梁','中梁延长梁'}
def skew(v):
 x,y,z=v;return np.array([[0,-z,y],[z,0,-x],[-y,x,0.]])
ps=w.head();bodies=[p for p in ps if p.note in NAMES];anchor=next(p for p in bodies if p.note=='转盘上半');bodies.remove(anchor);bodies=[anchor]+bodies
index={id(p):i for i,p in enumerate(bodies)};boxes={id(p):w.check._obb(p) for p in bodies};n=len(bodies)-1
rows=[];joints=[]
for pin in ps:
 if pin.kind not in ('axle','pin'):continue
 layers=w.check._pin_layers(pin,bodies,None,boxes)
 if len(layers)<2:continue
 axis=pin.rot[:,0];pt=pin.pos
 for aa,bb in zip(layers,layers[1:]):
  a,b=aa[0],bb[0];block=np.zeros((6,6*n))
  for body,sign in ((a,1),(b,-1)):
   i=index[id(body)]
   if not i:continue
   k=6*(i-1);block[:3,k:k+3]+=sign*np.eye(3)
   block[:3,k+3:k+6]+=-sign*skew((pt-body.pos)/100.)
   block[3:,k+3:k+6]+=sign*(np.eye(3)-np.outer(axis,axis))
  rows.append(block);joints.append({'连接':pin.note,'零件':[a.note,b.note],'位置':pt.tolist(),'轴线':axis.tolist()})
A=np.vstack(rows);_,sv,vh=np.linalg.svd(A,full_matrices=True);rank=int(sum(sv>1e-8));null=vh[rank:]
free=[]
for p in bodies[1:]:
 i=index[id(p)]-1;norm=float(np.linalg.norm(null[:,6*i:6*i+6])) if len(null) else 0
 if norm>1e-6:free.append({'零件':p.note,'位置':p.pos.tolist(),'未约束运动分量范数':norm})
r={'固定件数量':len(bodies),'自由坐标数':6*n,'约束秩':rank,'未约束自由度':6*n-rank,'最小非零奇异值':float(sv[rank-1]),'未约束零件':free,'连接数':len(joints),'连接':joints,'假设':'接头理想无间隙，轴向保持按已排布销挡肩和轴套成立；秩不代表实物刚度、承载强度或轴套摩擦可靠性。'}
Path(__file__).with_name('structure-rank.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='连接'},ensure_ascii=False,indent=2))
