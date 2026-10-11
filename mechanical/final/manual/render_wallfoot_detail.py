from pathlib import Path
import sys,numpy as np,json
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent));import candidate as C
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
pp=C.module();parts=[pp[2],pp[48],pp[49]]
for p in C.retained_base():
 if p.name!='39790.dat':continue
 t=C.world(p);lo=t.min((0,1));hi=t.max((0,1))
 if lo[0]<=-112<=hi[0] and lo[2]<=-16<=hi[2] and lo[1]<=108 and hi[1]>=100:parts.append(p)
assert len(parts)==4,len(parts)
fig=plt.figure(figsize=(9,6));ax=fig.add_subplot(111,projection='3d')
for p in parts:
 t=C.world(p);keep=(t.max(1)[:,0]>=-132)&(t.min(1)[:,0]<=-92)&(t.max(1)[:,1]>=80)&(t.min(1)[:,1]<=114)&(t.max(1)[:,2]>=-30)&(t.min(1)[:,2]<=30);t=t[keep][:,:,[0,2,1]];t[:,:,2]*=-1
 n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-9);sh=.5+.5*np.abs(n@np.array([.3,-.5,.8]));col='#e0a32e'if p.name=='2780.dat'else'#3786a8'if p.name=='64179.dat'else'#aeb9c0';ax.add_collection3d(Poly3DCollection(t,facecolors=np.array(to_rgb(col))[None,:]*sh[:,None],edgecolors='none',alpha=1 if p.name=='2780.dat'else .24))
ax.set(xlim=(-132,-92),ylim=(-30,30),zlim=(-115,-80));ax.set_box_aspect((40,60,35));ax.view_init(18,-40);ax.set_axis_off()
fig.suptitle('Wall-foot detail | 2 pins per arm | final pin center Y100 mm',fontsize=13)
fig.text(.5,.04,'Transparent hosts; gold 2780 center Y100 mm. Wall bore Y92..100 | base bore Y100..108.',ha='center',fontsize=10)
fig.savefig(H/'diagrams/wallfoot-detail.png',dpi=135);plt.close(fig)
(H/'wallfoot-detail-state.json').write_text(json.dumps({'parts':[p.ldraw()for p in parts],'clipped_view_only':True,'local_arm':'L','other_arms':'apply frozen ARM_ROT; Y unchanged'},indent=2))
