"""真实LDraw零件的多视图和离线交互评审页。"""
import json,base64,sys
from collections import Counter
from pathlib import Path
import numpy as np
import boxed_slider as w
P=Path(__file__).parent;ROOT=w.ROOT
sys.path.insert(0,str(ROOT/'tools/lego/render'))
import software
w.m.module=w.module
states={}
for state,stroke in [('closed',0.),('open',w.OPEN_S)]:
 states[state]=w.m.build({arm:(stroke,0) for arm in w.m.ARMS})
# 静态图片同时展示完整单臂、前后两面和内部构件。
head=w.head();module=w.module()
fixed={'转盘上半','后整体框','侧整体框','侧承重直梁','后框侧垫梁','夹指根立梁','根轴内侧支承梁','转盘T形接口梁','中间承重直梁','前固定导轨块','前导轨T支板','根架间隔梁','中梁延长梁','导轨固定孔座'}
for name,parts in [('head',head),('module',module),('inside',[p for p in head if p.note not in fixed]),('assembly',states['closed'])]:
 (P/f'{name}.ldr').write_text(w.m.to_ldr(parts,'矩形骨架与双导轨候选；实物承载待测'))
for name,model,yaw,pitch in [('head-front','head',35,25),('head-reverse','head',-145,25),('head-inside','inside',35,25),('single-arm','module',35,25),('assembly','assembly',35,60)]:
 software.render({'model':str(P/f'{model}.ldr'),'out':str(P/f'{name}.png'),'opts':{'yaw':yaw,'pitch':pitch,'w':1500,'h':1050,'margin':.08}})
 print(name,flush=True)
old=w.BASE_MODULE(0.,steps=False);oldc=Counter(p.name for p in old);newc=Counter(p.name for p in module)
bom=[{'零件':n,'名称':w.m.CATALOG.get(n,(n,''))[0],'现方案单臂':oldc[n],'候选单臂':newc[n],'单臂变化':newc[n]-oldc[n],'四臂变化':4*(newc[n]-oldc[n])} for n in sorted(oldc.keys()|newc.keys())]
(P/'bom-delta.json').write_text(json.dumps({'旧单臂件数':len(old),'新单臂件数':len(module),'新机械头件数':len(head),'明细':bom},ensure_ascii=False,indent=2))
meshes={}
for parts in states.values():
 for p in parts:
  if p.name in meshes:continue
  tri,ids,_=w.mesh.ldraw.geometry(p.name)
  meshes[p.name]={'v':np.round(tri.reshape(-1),4).tolist(),'ids':ids.tolist()}
def record(p):return {'n':p.name,'c':p.col if hasattr(p,'col') else p.color,'p':np.round(p.pos,7).tolist(),'r':np.round(p.rot,9).reshape(-1).tolist(),'a':getattr(p,'arm',''),'h':p.head,'t':p.note,'f':p.note in fixed}
data={'meshes':meshes,'states':{k:[record(p) for p in v] for k,v in states.items()},'colors':software.COLORS}
def uri(path):return 'data:text/javascript;base64,'+base64.b64encode(path.read_bytes()).decode()
imports={'three':uri(ROOT/'tools/lego/render/node_modules/three/build/three.module.js'),'orbit':uri(ROOT/'tools/lego/render/node_modules/three/examples/jsm/controls/OrbitControls.js')}
html=(P/'review-template.html').read_text().replace('__IMPORTS__',json.dumps({'imports':imports})).replace('__DATA__',json.dumps(data,separators=(',',':')))
(P/'review.html').write_text(html)
print('review.html',flush=True)
