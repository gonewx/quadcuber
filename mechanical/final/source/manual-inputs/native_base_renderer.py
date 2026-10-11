"""Render genuine small-part assembly pages from reviewed, explicit step data."""
from pathlib import Path
import sys,json,math,textwrap,argparse,collections,hashlib,functools
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
import candidate as C
world=C.world;mesh=C.mesh;files=C.files
def norm(name):return name.replace('\\','/').lower()
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager,colors
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
from matplotlib.lines import Line2D
from PIL import Image, ImageDraw
import contourpy
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection
from mpl_toolkits.mplot3d import proj3d
FONT='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';font_manager.fontManager.addfont(FONT);plt.rcParams['font.family']='Noto Sans CJK JP';plt.rcParams['axes.unicode_minus']=False
OUT=Path(__file__).parent;BG='#f1f4f7';INK='#18354a';NEW='#168bc5';OLD='#c3cbd3';MERGE='#e2ad42';ARROW='#147f71'
DESCS={'39790.dat':'15×11 框','64179.dat':'7×5 框','32278.dat':'15L 厚梁','32525.dat':'11L 厚梁','32524.dat':'7L 厚梁','40490.dat':'9L 厚梁','32316.dat':'5L 厚梁','32523.dat':'3L 厚梁','32526.dat':'3×5 厚L梁','14720.dat':'3×5 H框','71709.dat':'3×7 面板','60484.dat':'3×3 T梁','42003.dat':'垂直轴/双销孔接头','55615.dat':'四销直角接头','15100.dat':'销孔＋摩擦销接头','18654.dat':'1L 销孔套','62462.dat':'2L 销连接套','32192.dat':'斜向双轴孔接头','2780.dat':'2L 摩擦销','6558.dat':'3L 摩擦销','4519.dat':'3L 轴','3705.dat':'4L 轴','32073.dat':'5L 轴','3708.dat':'12L 轴','3713.dat':'1L 轴套','32123a.dat':'半轴套'}
P={i+1:p for i,p in enumerate(C.retained_base())};W={};M={}
def world_cached(i):
 if i not in W:W[i]=world(P[i])
 return W[i]
def xyz(t):return t[..., [0,2,1]]*np.array([1,1,-1])
def shade(t,c,a=1):
 n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-10);light=np.array([-.35,-.55,.76]);light/=np.linalg.norm(light);s=.51+.43*np.abs(n@light);rgba=np.empty((len(t),4));rgba[:,:3]=np.array(colors.to_rgb(c))*s[:,None];rgba[:,3]=a;return rgba

def clipped_triangles(w,center,half):
 lo=center-half;hi=center+half;result=[]
 for tri in w:
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
 return np.array(result)

@functools.lru_cache(None)
def outline(name):
 name=norm(name)
 if name not in files:
  name=next((cand for cand in ('p/'+name,'parts/'+name,'s/'+name) if cand in files),name)
 lines=[]
 for line in files[name]:
  ss=line.split()
  if not ss:continue
  if ss[0]=='1':
   v=np.array(list(map(float,ss[2:14])));child=outline(norm(' '.join(ss[14:])))
   if len(child):lines.extend(child@v[3:].reshape(3,3).T+v[:3])
  elif ss[0]=='2':lines.append(np.array(list(map(float,ss[2:8]))).reshape(2,3))
 return np.array(lines)

def draw(ax,items,focus=None):
 ts=[];cs=[]
 for i,c,alpha,offset in items:
  w=world_cached(i)+offset
  if focus:
   center,half=focus;mask=np.all(w.max(1)>=center-half,1)&np.all(w.min(1)<=center+half,1);w=clipped_triangles(w[mask],center,half)
  if not len(w):continue
  t=xyz(w);ts.append(t);cs.append(shade(t,c,alpha))
 if ts:ax.add_collection3d(Poly3DCollection(np.concatenate(ts),facecolors=np.concatenate(cs),edgecolors='none',linewidth=0,rasterized=True,zsort='average'))

def draw_ghosts(ax,ghosts):
 for i,c,alpha,offset in ghosts:
  p=P[i];lines=outline(p.name)
  if len(lines):
   lines=xyz((lines@p.rot.T+p.pos)*.4+offset)
   ax.add_collection3d(Line3DCollection(lines,colors=c,linewidths=.65,linestyles=(0,(3,3)),alpha=.66))

def project_fig(fig,ax,point):
 x,y,z=xyz(np.asarray(point));xx,yy,_=proj3d.proj_transform(x,y,z,ax.get_proj())
 return fig.transFigure.inverted().transform(ax.transData.transform([xx,yy]))

def configure(ax,bounds,view):
 lo,hi=bounds;span=np.maximum(hi-lo,8);pad=max(float(span.max())*.075,3);lo=lo-pad;hi=hi+pad;span=hi-lo
 ax.set_xlim(lo[0],hi[0]);ax.set_ylim(lo[1],hi[1]);ax.set_zlim(lo[2],hi[2]);ax.set_box_aspect(span);ax.view_init(elev=view.get('elev',30),azim=view.get('azim',-55));ax.set_proj_type('ortho');ax.set_axis_off();ax.set_facecolor(BG)

def short_ids(ids):
 ids=sorted(ids)
 if len(ids)>5:return '#'+str(ids[0])+'–'+str(ids[-1])
 return ' '.join('#'+str(i)for i in ids)

def render_step(step):
 sid=step['id'];visible=list(dict.fromkeys(step['visible_part_ids']+step.get('original_module_part_ids',[])));added=set(step['added_part_ids']);highlight=set(step.get('highlight_part_ids',[])) or added
 assert added<=set(visible),(sid,'missing added')
 external=set(step.get('original_module_part_ids',[]));view=step.get('view',{})
 items=[(i,NEW if i in added else MERGE if i in highlight else OLD,.12 if i in external else 1,np.zeros(3))for i in visible]
 ghosts=[];arrows=[]
 for ins in step.get('insertion',[]):
  ids=ins.get('part_ids',[]);off=np.array(ins.get('start_offset_mm',[0,0,0]),float)
  if np.linalg.norm(off)<1e-7:continue
  if len(ids)>5:
   anchor=np.mean([P[i].pos*.4 for i in ids],axis=0);arrows.append((anchor+off,anchor))
  else:
   for i in ids:
    if i not in visible:continue
    anchor=P[i].pos*.4;arrows.append((anchor+off,anchor));ghosts.append((i,NEW if i in added else MERGE,.18,off))
 allverts=[xyz(world_cached(i)+offset).reshape(-1,3)for i,_,_,offset in items+ghosts]
 bounds=(np.min([v.min(0)for v in allverts],0),np.max([v.max(0)for v in allverts],0));span=bounds[1]-bounds[0]
 fig=plt.figure(figsize=(12,9),facecolor=BG)
 fig.text(.035,.962,step.get('module_title',{'foundation':'共用底盘：四翼分别预装','carriage':'升降滑架与悬臂','seat':'魔方承座','seat_elbow':'承座与斜臂连接','guides':'导轨安装','upper_locks':'工作位锁轴','foundation_ties':'导轨与底盘拉接','mast_root':'外侧导轨根座'}.get(step['module_id'],step['module_id'])),fontsize=12,color='#667b8c',va='top')
 fig.text(.035,.915,f"{step['module_step_number']:02d}",fontsize=39,weight='bold',color=INK,va='top')
 title='\n'.join(textwrap.wrap(step['title'],29));fig.text(.135,.911,title,fontsize=19,weight='bold',color=INK,va='top')
 fig.text(.966,.955,sid,fontsize=10,color='#82909c',ha='right',va='top')
 text_lines=sum(len(textwrap.wrap(t,44)) for t in step.get('instructions',[]));long_text=text_lines>3
 ax=fig.add_axes([.005,.30 if long_text else .23,.715,.515 if long_text else .585],projection='3d');draw(ax,items);configure(ax,bounds,view)
 ports=step.get('ports',[])
 # New-part bill: exact instance identities determine part type, quantity and colour.
 groups=collections.defaultdict(list)
 for i in sorted(added):groups[(P[i].name,P[i].color)].append(i)
 fig.patches.append(FancyBboxPatch((.742,.315),.235,.50,boxstyle='round,pad=.012',facecolor='white',edgecolor='#dbe3e9',transform=fig.transFigure,zorder=-1))
 if groups:
  fig.text(.755,.790,'本步新件',fontsize=12,weight='bold',color=INK)
  h=min(.14,.42/len(groups));top=.75
  for n,((name,color),ids)in enumerate(groups.items()):
   yy=top-n*h;th=fig.add_axes([.765,yy-h*.70,.10,h*.68],projection='3d');t=mesh(name)*.4;t=xyz(t);th.add_collection3d(Poly3DCollection(t,facecolors=shade(t,NEW),edgecolors='none',linewidth=0,rasterized=True));configure(th,(t.min((0,1)),t.max((0,1))),{'azim':-50,'elev':35});th.set_facecolor('white')
   fig.text(.875,yy-.015,f'{name.removesuffix(".dat")}  ×{len(ids)}',fontsize=10.5,weight='bold',color=INK,va='top')
   desc=DESCS.get(name,name);fig.text(.875,yy-.048,'\n'.join(textwrap.wrap(desc,9)),fontsize=8.3,color='#536c7e',va='top')

 else:
  fig.text(.755,.779,'合并已完成组件',fontsize=12,weight='bold',color=INK)
  fig.text(.755,.738,'本步不增加核心零件',fontsize=10,color='#60788b')
  if highlight:fig.text(.755,.690,'金色组件沿箭头合拢',fontsize=10,color='#6b7d8d')
 # A real-mesh close-up for long assemblies and small pin/bush operations.
 if ports and max(span)>90 and (step.get('insertion') or len(visible)>18):
  center=np.array(ports[0]['center_mm'],float);half=np.array([14.,14.,14.]);da=fig.add_axes([.755,.105,.21,.19],projection='3d');draw(da,items,focus=(center,half));c=xyz(center);configure(da,(c-half,c+half),view);da.scatter(*c,s=28,color=ARROW,depthshade=False);fig.text(.758,.302,'标记孔位放大',fontsize=9.2,color=INK)
 # Readable action text, never a substitute for the exact instance/port data.
 y=.265 if long_text else .198
 leading=min(.030,(y-.072-.006*len(step.get('instructions',[])))/max(text_lines,1))
 for line in step.get('instructions',[]):
  for ss in textwrap.wrap(line,44):fig.text(.04,y,ss,fontsize=11 if leading>=.024 else 10,color=INK,va='top');y-=leading
  y-=.006
 fig.text(.04,.044,'蓝：本步新件   浅灰：已装件   金：正在合并的组件   绿箭头：装入方向',fontsize=9,color='#738695')
 fig.text(.04,.019,'虚线轮廓：移入前位置，不是额外零件。销的中环须贴住梁面；不要强推。',fontsize=8,color='#8494a0')
 fig.canvas.draw()
 # One dashed projected silhouette per starting piece: no transparent internal mesh.
 for i,c,alpha,offset in ghosts:
  tris=xyz(world_cached(i)+offset).reshape(-1,3);xx,yy,_=proj3d.proj_transform(tris[:,0],tris[:,1],tris[:,2],ax.get_proj())
  pts=fig.transFigure.inverted().transform(ax.transData.transform(np.stack([xx,yy],axis=-1).reshape(-1,2))).reshape(-1,3,2)
  low=pts.min((0,1));high=pts.max((0,1));extent=np.maximum(high-low,1e-8)
  res=np.maximum(40,np.ceil(extent/extent.max()*240).astype(int));mask=Image.new('L',tuple(res+4),0);pen=ImageDraw.Draw(mask)
  pix=(pts-low)/extent*res+2
  for tri in pix:pen.polygon([tuple(v) for v in tri],fill=1)
  lines=contourpy.contour_generator(z=np.asarray(mask,dtype=float)).lines(.5)
  for line in lines:
   area=abs(np.sum(line[:,0]*np.roll(line[:,1],1)-line[:,1]*np.roll(line[:,0],1)))*.5
   if area<20:continue
   v=(line-2)/res*extent+low
   fig.lines.append(Line2D(v[:,0],v[:,1],transform=fig.transFigure,color=c,linewidth=1.2,linestyle=(0,(4,3)),alpha=.75,zorder=40))
 for start,end in arrows:
  s=project_fig(fig,ax,start);e=project_fig(fig,ax,end)
  fig.patches.append(FancyArrowPatch(s,e,transform=fig.transFigure,arrowstyle='-|>',mutation_scale=16,linewidth=2.0,color=ARROW,zorder=60,shrinkA=3,shrinkB=2))
 for k,p in enumerate(ports[:6]):
  v=project_fig(fig,ax,p['center_mm'])
  fig.patches.append(Circle(v,.005,transform=fig.transFigure,fill=False,edgecolor=ARROW,linewidth=1.2,zorder=55))
 image=OUT/'images'/f'{sid}.png';fig.savefig(image,dpi=150,facecolor=BG);plt.close(fig)
 return {'id':sid,'image_path':str(image.resolve()),'width':1800,'height':1350,'visible_part_ids':visible,'added_part_ids':sorted(added),'sha256':hashlib.sha256(image.read_bytes()).hexdigest()}

def main():
 a=argparse.ArgumentParser();a.add_argument('module_files',nargs='+');a.add_argument('--ids');args=a.parse_args();wanted=set(args.ids.split(','))if args.ids else None;report=[]
 for f in args.module_files:
  data=json.loads(Path(f).read_text())
  for step in (data if isinstance(data,list) else data['steps']):
   if wanted is not None and step['id']not in wanted:continue
   report.append(render_step(step));print('RENDERED',step['id'],flush=True)
 name='render-'+('-'.join(Path(f).stem for f in args.module_files))+(('-'+args.ids.replace(',','_'))if args.ids else'')+'.json';(OUT/name).write_text(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
