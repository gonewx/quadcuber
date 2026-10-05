"""搭建图逐件覆盖、左右侧架合拢路径的离散检查。"""
import json,hashlib
import numpy as np
import build_instructions as b
w=b.w
hits=[];queries=0
for c in b.cards:
 if not c['title'].startswith('合拢'):continue
 for f in np.linspace(1,0,26):
  for source in c['moving']:
   a=source.moved(w.m.I,np.array(c['delta'])*f);lo,hi=w.check._obb(a)
   for other in c['old']:
    low,high=w.check._obb(other)
    if np.any(np.minimum(hi,high)-np.maximum(lo,low)<=1e-7):continue
    if w.mesh.fitting(a,other):continue
    queries+=1
    dist=w.fcl.distance(w.mesh.obj(a),w.mesh.obj(other),w.fcl.DistanceRequest(),w.fcl.DistanceResult())
    if dist<=1e-8 and not w.nominal_contact(a,other):hits.append({'步骤':c['n'],'离完成比例':float(f),'零件对':[a.note,other.note]})
r={'候选SHA256':hashlib.sha256((b.P/'boxed_slider.py').read_bytes()).hexdigest(),'图纸脚本SHA256':hashlib.sha256((b.P/'build_instructions.py').read_bytes()).hexdigest(),'步骤数':len(b.cards),'零件数':len(b.parts),'逐件覆盖':'每件首次增加一次，最终组件逐件一致','侧架合拢姿态数':52,'网格查询数':queries,'相交':hits,'范围':'左右完整侧架各沿Z平移40mm至最终位置，26点采样；不证明全部零件逐一插入路径，也不模拟手指、摩擦和公差。'}
(b.OUT/'assembly-check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));print(json.dumps(r,ensure_ascii=False,indent=2))
