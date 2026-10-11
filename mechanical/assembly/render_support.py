from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import MECHANICAL, ASSEMBLY, MANUAL_OUTPUT
"""Render actual frozen LDraw triangle meshes, never schematic substitute parts."""
from pathlib import Path
import json,sys,math,textwrap,os,hashlib
os.environ.setdefault("MPLCONFIGDIR","/tmp/mpl132")
os.environ.setdefault("XDG_CACHE_HOME","/tmp/cache132")
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import colors,font_manager
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from mpl_toolkits.mplot3d import proj3d
HERE=MANUAL_OUTPUT
sys.path.insert(0,str(MECHANICAL));import candidate as C
book=json.loads((ASSEMBLY/'support-steps.json').read_text());rows=C.rows
context_parts=[C.module()[2].moved(C.m.ARM_ROT['R']),C.retained_base()[0]]
context_mesh=[]
for p in context_parts:
 t=C.world(p)[:,:,[0,2,1]].copy();t[:,:,2]=116-t[:,:,2];context_mesh.append(t)
world_mesh={r['index1']:C.world(p)for r,p in zip(rows,C.core_parts())};mesh={}
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';font_manager.fontManager.addfont(font);plt.rcParams['font.family']=font_manager.FontProperties(fname=font).get_name();plt.rcParams['axes.unicode_minus']=False
BG='#f5f4ef';INK='#183b4d';MUTED='#65777f';BLUE='#2188b8';OLD='#b6bfc3';GREEN='#21846e'
light=np.array([-.4,-.6,.8]);light/=np.linalg.norm(light)
for r in rows:
 t=world_mesh[r['index1']][:,:,[0,2,1]].copy();t[:,:,2]=116-t[:,:,2];mesh[r['index1']]=t

def transform(v):
 q=np.array(v)[[0,2,1]].copy();q[2]=116-q[2];return q

def wrapped(t,width):
 # East Asian text: width measured in roughly character columns.
 import unicodedata
 lines=[];line='';n=0
 for ch in t:
  w=2 if unicodedata.east_asian_width(ch)in 'WF' else 1
  if n+w>width:lines.append(line);line='';n=0
  line+=ch;n+=w
 if line:lines.append(line)
 return '\n'.join(lines)

def draw(ax,ids,hi,arrows,zoom=False,mod='',context=False):
 ax.set_facecolor(BG)
 camera_arrows=arrows
 if not ids:ax.axis('off');return
 if zoom:ids=list(hi or ids);arrows=[]
 allpts=np.concatenate([mesh[i].reshape(-1,3)for i in ids]+([t.reshape(-1,3)for t in (context_mesh[:1]if context=='isolated_root'else context_mesh)]if context and not zoom else []));focus=np.concatenate([mesh[i].reshape(-1,3)for i in (hi or ids)])
 bounds=focus if zoom else allpts
 if arrows and not zoom:bounds=np.concatenate([bounds,np.array([transform(a[k])for a in arrows for k in ['from','to']])])
 lo=bounds.min(0);high=bounds.max(0);span=high-lo
 margin=np.maximum(span*.15,6 if zoom else 4)
 lo-=margin;high+=margin
 for i in ids:
  t=mesh[i]
  if zoom:
   keep=np.all(t.max(1)>=lo,axis=1)&np.all(t.min(1)<=high,axis=1);t=t[keep]
  if not len(t):continue
  n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12)
  shade=.56+.40*np.abs(n@light);rgba=np.ones((len(t),4));rgba[:,:3]=np.array(colors.to_rgb(BLUE if i in hi else OLD))*shade[:,None]
  ax.add_collection3d(Poly3DCollection(t,facecolors=rgba,edgecolors='none',linewidths=0,zsort='average',rasterized=True))
 if context and not zoom:
  for t in (context_mesh[:1]if context=='isolated_root'else context_mesh):
   n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12);shade=.56+.40*np.abs(n@light);rgb=np.array(colors.to_rgb('#91a6b5'))*shade[:,None];ax.add_collection3d(Poly3DCollection(t,facecolors=rgb,edgecolors='none',linewidths=0,zsort='average',alpha=.30))
 # Give thin dimensions visual breathing room without stretching the part.
 mid=(lo+high)/2;sp=np.maximum(high-lo,10);lo=mid-sp/2;high=mid+sp/2
 ax.set_xlim(lo[0],high[0]);ax.set_ylim(lo[1],high[1]);ax.set_zlim(lo[2],high[2]);ax.set_box_aspect(sp)
 az=-52 if not mod.startswith('L_')else 128
 if mod.startswith('x_'):az=-46
 if mod=='lever':az=-123
 # View from the incoming side so late-stage blue parts do not sit behind their hosts.
 if camera_arrows and camera_arrows[0]['direction'][2]:
  from_positive_z=camera_arrows[0]['direction'][2]<0
  from_negative_x=focus[:,0].mean()<0
  az=(128 if from_negative_x else 52) if from_positive_z else (-128 if from_negative_x else -52)
 ax.view_init(elev=26,azim=az);ax.set_proj_type('ortho');ax.set_axis_off();ax.set_facecolor(BG)
 for vector in arrows:
  p,q=transform(vector['from']),transform(vector['to']);a=proj3d.proj_transform(*p,ax.get_proj());b=proj3d.proj_transform(*q,ax.get_proj())
  ax.annotate('',xy=(b[0],b[1]),xytext=(a[0],a[1]),arrowprops={'arrowstyle':'-|>','mutation_scale':18,'lw':2.2,'color':GREEN},zorder=10000)

out=HERE/'support-diagrams';out.mkdir(exist_ok=True)
sel=set(map(int,sys.argv[1:]))if len(sys.argv)>1 else None
for step in book['steps']:
 if sel and step['number']not in sel:continue
 # Each drawing uses the serialized pose snapshot, including lower-pose lever assembly.
 for r in step['geometry_records']:
  p=C.m.Part(r['name'],r['color'],r['position_ldu'],r['rotation'],0,r['id']);t=C.world(p)[:,:,[0,2,1]].copy();t[:,:,2]=116-t[:,:,2];mesh[r['index1']]=t
 fig=plt.figure(figsize=(12,8),facecolor=BG)
 fig.text(.035,.956,f'{step["number"]:02d} / {len(book["steps"])}  {step["title_zh"]}',fontsize=17.5,weight='bold',color=INK)
 inv='；'.join(f'#{p["index1"]} {p["part"].removesuffix(".dat")}'for p in step['new_parts'])or'无新增件：合并／定位／待执行检查'
 fig.text(.035,.913,'本步新增：'+inv+f'     累计 {step["cumulative_introduced_count"]} / 150 件',fontsize=10.5,color=INK)
 fig.text(.035,.878,'蓝色＝新件或合并件；灰色＝相关已装件；绿色＝装入方向（示意）'+(' | '+step['pose_label'] if step.get('pose_label') else ''),fontsize=9.5,color=MUTED)
 ids=step['visible_part_ids'];hi=step['highlight_part_ids'];arrows=step['insertion_vectors_mm']
 ax=fig.add_axes([.012,.28,.66,.59],projection='3d');draw(ax,ids,hi,arrows,mod=step['module_id'],context=step.get('external_context'))
 if ids:
  ax2=fig.add_axes([.677,.34,.307,.45],projection='3d');draw(ax2,ids,hi,arrows,zoom=True,mod=step['module_id'],context=step.get('external_context'));fig.text(.69,.80,'蓝色件单独看（保持原朝向）'if hi else'完整状态参考',fontsize=10.5,color=GREEN)
 else:
  fig.text(.06,.70,'这一步先核对外部接口与限制',fontsize=20,color=INK)
  fig.text(.06,.57,'近侧 +Z：绿色高L定位边\n右侧 +X：黄色双柱定位框\n上方 −Y：放魔方的一面',fontsize=15,color=MUTED,linespacing=1.8)
 txt='\n'.join(wrapped(f'{j+1}. {v}',137)for j,v in enumerate(step['instructions_zh']))
 caution='；'.join(step['cautions_zh'])
 if caution:txt+='\n'+wrapped('注意：'+caution,137)
 nlines=txt.count('\n')+1
 fig.text(.035,.253,txt,fontsize=9.3 if nlines<=9 else 8.3,color=INK,va='top',linespacing=1.45)
 fig.text(.035,.026,'实际网格 · 130件支承＋20件杠杆 · 上位须持续按住或独立托稳 · 安装路径／保持／强度／重力回落未实测',fontsize=8.3,color=MUTED)
 path=out/f'{step["number"]:03d}.png';fig.savefig(path,dpi=105,facecolor=BG);plt.close(fig)
 canonical=json.dumps(step,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
 (out/(path.stem+'.json')).write_text(json.dumps({'step_id':step['id'],'step_number':step['number'],'step_sha256':hashlib.sha256(canonical).hexdigest(),'image_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'revision':book['revision'],'geometry_snapshot_used':True},indent=2))
 print(step['number'],path.name,flush=True)
print('Finished actual-mesh drawings.',flush=True)
