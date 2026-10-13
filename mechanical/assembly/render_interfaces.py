from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import MECHANICAL, ASSEMBLY, MANUAL_OUTPUT
from pathlib import Path
import sys,json,numpy as np
H=MANUAL_OUTPUT;sys.path.insert(0,str(MECHANICAL));import candidate as C
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
D=H/'diagrams';D.mkdir(exist_ok=True)
SELECT=set(sys.argv[1:])
def draw(name,pp,group,title,view=(25,-55)):
 if SELECT and name not in SELECT:return
 fig=plt.figure(figsize=(11,7),facecolor='white');ax=fig.add_subplot(111,projection='3d');bounds=[]
 for p,g in zip(pp,group):
  t=C.world(p)[:,:,[0,2,1]].copy();t[:,:,2]*=-1;bounds.append(t.reshape(-1,3));n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-9);c=np.array(to_rgb(['#aebbc4','#308ba4','#e6aa3c','#c15577','#7877aa'][g]));sh=.5+.5*np.abs(n@np.array([.38,-.53,.76]));ax.add_collection3d(Poly3DCollection(t,facecolors=c[None,:]*sh[:,None],edgecolors='none',rasterized=True))
 q=np.concatenate(bounds);lo=q.min(0);hi=q.max(0);pad=(hi-lo)*.07+3;lo-=pad;hi+=pad;ax.set(xlim=(lo[0],hi[0]),ylim=(lo[1],hi[1]),zlim=(lo[2],hi[2]));ax.set_box_aspect(hi-lo,zoom=.95 if name.startswith('lever-') else 1.5);ax.set_proj_type('ortho');ax.view_init(*view);ax.set_axis_off();fig.suptitle(title,fontsize=15);fig.subplots_adjust(left=0,right=1,bottom=.03,top=.93);fig.savefig(D/(name+'.png'),dpi=110);plt.close(fig);print(name,flush=True)
base=C.retained_base();support=C.core_parts();manifest=json.loads((H.parent/'candidate-manifest.json').read_text());arms=C.state_parts(manifest['loading-all50']['heads'])
draw('integrated-whole',support+base+arms,[1]*len(support)+[2]*len(base)+[0]*len(arms),'ASSEMBLY | loading-all50 | 938 parts | head roll50 / jaw25 deg')
arms=C.state_parts({a:(0.,0.)for a in C.m.ARMS})
installed=[]
for arm in ['R','L','F','B']:
 a=[p for p in arms if p.arm==arm];prior_installed=installed.copy();installed+=a;staged=prior_installed+[p for i,p in enumerate(a,1)if i not in (81,84)]
 lev=C.lever_parts(42.4);lev=[p for p in lev if not p.note.startswith('stop_')]
 draw('interface-'+arm,lev+base+staged,[1]*len(lev)+[2]*len(base)+[3]*len(staged),'ASSEMBLY | '+arm+' staged arm165 | closed / roll0 | beam81 / pin84 installed next | '+str(len(lev)+len(base)+len(staged))+' parts')
draw('support-complete',support+base,[1]*len(support)+[2]*len(base),'ASSEMBLY | 150 support + 120 reinforced base | hold or support upper tray')

down=C.core_parts(40.8);draw('support-lowered',down+base,[1]*len(down)+[2]*len(base),'ASSEMBLY | lower guide stop | tray drop40.8 mm | 270 parts')
draw('lever-upper',[C.module()[2].moved(C.m.ARM_ROT['R']),base[0]]+C.lever_parts(),[0,2]+[3 if p.note=='outer_handle' else 4 if p.note.startswith('stop_')else 1 for p in C.lever_parts()],'ASSEMBLY | 20-part lever at upper stop | hold from above',view=(28,-123))
draw('lever-lowered',[C.module()[2].moved(C.m.ARM_ROT['R']),base[0]]+C.lever_parts(42.4),[0,2]+[3 if p.note=='outer_handle' else 4 if p.note.startswith('stop_')else 1 for p in C.lever_parts(42.4)],'ASSEMBLY | gravity-return lower pose | control descent',view=(28,-123))
