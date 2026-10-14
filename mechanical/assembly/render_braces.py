from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import MECHANICAL, ASSEMBLY, MANUAL_OUTPUT
"""Native-mesh detail of final arm side-brace assembly; geometry unchanged."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
H=MANUAL_OUTPUT;sys.path.insert(0,str(MECHANICAL));import candidate as C
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager,colors
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from mpl_toolkits.mplot3d import proj3d
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';font_manager.fontManager.addfont(font);plt.rcParams['font.family']=font_manager.FontProperties(fname=font).get_name()
BG='#f1f4f7';BLUE='#168bc5';OLD='#b6bfc4';INK='#18354a';base=C.retained_base();sel=set(sys.argv[1:])
# Draw in each arm's native local frame so all four instructions share an unambiguous view.
local=C.module();local_mesh=[C.world(p)for p in local];focus_lo=np.array([-232,26,20]);focus_hi=np.array([-200,116,54])
def xyz(t):return np.asarray(t)[...,[0,2,1]]*np.array([1,1,-1])
def clipped(w,lo,hi):
 result=[]
 keep=np.all(w.max(1)>=lo,1)&np.all(w.min(1)<=hi,1)
 for tri in w[keep]:
  poly=list(tri)
  for dim in range(3):
   for lim,sign in ((lo[dim],1),(hi[dim],-1)):
    if not poly:break
    output=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
     ia=sign*(a[dim]-lim)>=-1e-9;ib=sign*(b[dim]-lim)>=-1e-9
     if ia:output.append(a)
     if ia!=ib:output.append(a+(b-a)*((lim-a[dim])/(b[dim]-a[dim])))
    poly=output
  for k in range(1,len(poly)-1):result.append([poly[0],poly[k],poly[k+1]])
 return np.asarray(result)
def addmesh(ax,w,color):
 t=xyz(w);n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-9);shade=.53+.42*np.abs(n@np.array([-.4,-.55,.73]));ax.add_collection3d(Poly3DCollection(t,facecolors=np.array(colors.to_rgb(color))[None,:]*shade[:,None],edgecolors='none',rasterized=True))
def arrow(ax,p,q):
 a=proj3d.proj_transform(*xyz(p),ax.get_proj());b=proj3d.proj_transform(*xyz(q),ax.get_proj());ax.annotate('',xy=b[:2],xytext=a[:2],arrowprops={'arrowstyle':'-|>','mutation_scale':18,'lw':2.2,'color':'#147f71'},zorder=10000)
for arm,idx,ds in [('R',0,'从世界-Z外侧沿+Z装入'),('L',11,'从世界+Z外侧沿-Z装入'),('F',27,'从世界+X外侧沿-X装入'),('B',43,'从世界-X外侧沿+X装入')]:
 if sel and arm not in sel:continue
 R=C.m.ARM_ROT[arm];frame=base[idx];frame_local=C.world(frame)@R
 fig=plt.figure(figsize=(11,7),facecolor=BG);fig.text(.04,.93,f'{arm}臂 先装84号销，再装81号9L侧梁',fontsize=16,color=INK,weight='bold');fig.text(.04,.875,ds+'；82/83号销已装在各自宿主中。',fontsize=11,color=INK)
 for panel in [0,1]:
  ax=fig.add_axes([.02+panel*.49,.16,.47,.63],projection='3d');pts=[];flo=np.array([-228,92,24])if panel==0 else focus_lo;fhi=np.array([-204,116,52])if panel==0 else focus_hi
  for i,w in enumerate(local_mesh):
   if i==80 or (i==83 and panel==0):continue
   ww=clipped(w,flo,fhi)
   if len(ww):
    addmesh(ax,ww,OLD);pts.append(xyz(ww).reshape(-1,3))
  w=clipped(frame_local,flo,fhi);addmesh(ax,w,OLD);pts.append(xyz(w).reshape(-1,3))
  i=83 if panel==0 else 80;addmesh(ax,local_mesh[i],BLUE);pts.append(xyz(local_mesh[i]).reshape(-1,3))
  q=np.concatenate(pts);lo=q.min(0)-4;hi=q.max(0)+4;ax.set(xlim=(lo[0],hi[0]),ylim=(lo[1],hi[1]+14),zlim=(lo[2],hi[2]));ax.set_box_aspect([hi[0]-lo[0],hi[1]-lo[1]+14,hi[2]-lo[2]]);ax.set_proj_type('ortho');ax.view_init(elev=23,azim=135);ax.axis('off');arrow(ax,[-216,104 if panel==0 else 78,66],[-216,104 if panel==0 else 78,36 if panel==0 else 40])
  fig.text(.05+panel*.49,.805,'1  84号销先装入底框半根（放大）' if panel==0 else '2  81号9L梁套住三根露出销',fontsize=12,color=INK)
 fig.text(.04,.105,'销84挡圈留在底框外表面；侧梁81随后贴合该挡圈，三枚销的挡圈都不穿过宿主孔。',fontsize=10,color=INK)
 fig.text(.04,.065,'灰色为已装件的局部网格；蓝色为本小步装入的预留散件。单臂完成状态共169件。',fontsize=10,color=INK)
 fig.text(.04,.026,'真实LDraw网格；方向示意不等于手部接近、插入力、保持或承载验证。',fontsize=9,color='#65777f')
 p=H/'diagrams'/f'brace-{arm}.png';fig.savefig(p,dpi=120);plt.close(fig)
 ids=[81,84];data=dict(revision=C.REVISION,arm=arm,original_arm_indices1=ids,remaining_pin_indices1=[82,83],base_frame_id=f'B{idx+1:02d}',direction_zh=ds,part_records=[{'index1':i,'ldraw':local[i-1].moved(R).ldraw()}for i in ids],native_mesh=True,image_sha256=hashlib.sha256(p.read_bytes()).hexdigest());p.with_suffix('.json').write_text(json.dumps(data,ensure_ascii=False,indent=2));print(arm,flush=True)
