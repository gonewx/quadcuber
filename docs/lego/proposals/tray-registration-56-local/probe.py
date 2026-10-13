"""Local feasibility probe only; canonical candidate and inputs are read-only."""
from pathlib import Path
import sys,json,math,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'mechanical'))
import candidate as c
OUT=Path(__file__).resolve().parent

def part(n,pos,R,note):return c.m.Part(n,14,np.array(pos)/.4,np.array(R),0,note)
I=np.eye(3)
TOOL=[part('32526.dat',[-31.6,24,.4],np.diag([1,-1,-1]),'low_corner_pusher'),part('32524.dat',[-31.6,32,-47.6],I,'handle_7L')]
for z in [-31.6,-23.6]:TOOL.append(part('2780.dat',[-31.6,28,z],[[0,-1,0],[1,0,0],[0,0,1]],'handle_pin_'+str(z)))
def bb(p):
 v=c.world(p);return np.array([v.min((0,1)),v.max((0,1))])
def label(p):return '/'.join([str(getattr(p,'arm','')),p.name,p.note])
def pairs(A,B,tol=1e-6):
 if not A or not B:return []
 a=np.array([b for n,b in A]);b=np.array([b for n,b in B]);idx=np.argwhere(np.all(np.minimum(a[:,None,1],b[None,:,1])-np.maximum(a[:,None,0],b[None,:,0])>tol,axis=2))
 return [[A[i][0],B[j][0]] for i,j in idx]
def boxes(pp):return [(label(p),bb(p)) for p in pp]
def moved(pp,vec):return [p.moved(I,np.array(vec)/.4) for p in pp]
def arms(angle=90,s=0):return [p for p in c.state_parts({'R':(s,angle),'L':(s,angle)}) if p.arm in ['R','L']]
def hit(at,bt):
 # Strict triangle-edge crossings; coplanar/contained solids need separate handling.
 e1=bt[:,1]-bt[:,0];e2=bt[:,2]-bt[:,0]
 for tr in at:
  for k in range(3):
   o=tr[k];d=tr[(k+1)%3]-o;h=np.cross(d,e2);a=np.sum(e1*h,axis=1);ok=np.abs(a)>1e-9
   f=np.divide(1,a,out=np.zeros_like(a),where=ok);s=o-bt[:,0];u=f*np.sum(s*h,axis=1);q=np.cross(s,e1);v=f*(q@d);t=f*np.sum(e2*q,axis=1)
   ok&=(u>1e-6)&(v>1e-6)&(u+v<1-1e-6)&(t>1e-6)&(t<1-1e-6)
   if ok.any():return (o+t[np.flatnonzero(ok)[0]]*d).tolist()
 return None

def ports(name,R=I,v=np.zeros(3)):
 out=[]
 for line in c.files[c.resolve(name)]:
  s=line.split()
  if not s or s[0]!='1':continue
  a=np.array(s[2:14],float);rr=R@a[3:].reshape(3,3);vv=R@a[:3]+v;n=' '.join(s[14:])
  if n=='peghole.dat':
   axis=rr@np.array([0.,1.,0.]);axis/=np.linalg.norm(axis);out.append((vv*.4+axis*4,axis))
  elif n in ['beamhole.dat','connhole.dat']:
   axis=rr@np.array([0.,1.,0.]);out.append((vv*.4,axis/np.linalg.norm(axis)))
  elif n in c.files or 's/' in n.replace('\\','/'):out+=ports(n,rr,vv)
 return out

def main():
 up=c.core_parts(0);a=arms();tb=boxes(TOOL)
 data={'status':'LOCAL_GEOMETRY_PROBE_NOT_PHYSICAL_APPROVAL','tool':[{'id':p.note,'part':p.name,'position_mm':(p.pos*.4).tolist(),'rotation':p.rot.tolist(),'bbox_mm':bb(p).tolist()} for p in TOOL]}
 data['tool_up_core_aabb_pairs']=pairs(tb,boxes(up))
 data['tool_horizontal_LR_all_parts_aabb_pairs']=pairs(tb,boxes(a))
 # Swept bounds for straight diagonal withdrawal, exact translation sweep AABB.
 swept=[]
 for n,b in tb:
  # Disengage both faces by 2mm, then withdraw straight along -Z (no diagonal swing into L).
  mid=b+np.array([-2,0,-2]);end=mid+np.array([0,0,-80])
  for start,finish in [(b,mid),(mid,end)]:
   swept.append((n,np.array([np.minimum(start[0],finish[0]),np.maximum(start[1],finish[1])])) )
 data['tool_withdraw_two_stage_continuous_aabb_pairs']=pairs(swept,boxes(up+a+c.retained_base()))
 data['tool_withdraw_y_plusminus2_aabb_pairs']=pairs([(n,b+np.array([[0,-2,0],[0,2,0]])) for n,b in swept],boxes(up+a+c.retained_base()))
 data['tool_withdraw_path_mm']=[[0,0,0],[-2,0,-2],[-2,0,-82]]
 # Refine concave-part candidates with native triangle swept bounds.
 obstacles=boxes(up+a+c.retained_base()); refined=[]; cube_candidates=[]
 for part_ in TOOL:
  tri=c.world(part_); lo=tri.min(axis=1); hi=tri.max(axis=1)
  cube_candidates.extend([part_.note,int(i)] for i in np.flatnonzero(np.all(np.minimum(hi,28)-np.maximum(lo,-28)>1e-6,axis=1)))
  for stage,(v0,v1) in enumerate([(np.zeros(3),np.array([-2,0,-2])),(np.array([-2,0,-2]),np.array([-2,0,-82]))]):
   sl=lo+np.minimum(v0,v1)+[0,-2,0]; sh=hi+np.maximum(v0,v1)+[0,2,0]
   for name,b in obstacles:
    ids=np.flatnonzero(np.all(np.minimum(sh,b[1])-np.maximum(sl,b[0])>1e-6,axis=1))
    if len(ids):refined.append({'part':part_.note,'stage':stage,'obstacle':name,'triangle_candidates':len(ids)})
 data['tool_withdraw_y_plusminus2_triangle_sweep_candidates']=refined
 data['tool_cube_triangle_bbox_candidates']=cube_candidates

 tool_cube=[]
 for p in TOOL:
  v=c.world(p).reshape(-1,3);inside=np.all((v>-28+1e-6)&(v<28-1e-6),axis=1)
  if inside.any():tool_cube.append({'id':p.note,'strict_interior_vertices':int(inside.sum()),'sample':v[inside][0].tolist()})
 data['tool_cube_strict_interior_vertices']=tool_cube
 # Native hole-center verification, no assumed hole orientation.
 holes=[]
 for p in TOOL[:2]:
  hp=[(p.rot@v+p.pos*.4,p.rot@axis) for v,axis in ports(p.name)]
  for z in [-31.6,-23.6]:
   target=np.array([-31.6,p.pos[1]*.4,z]);matches=[v for v,axis in hp if np.linalg.norm(v-target)<1e-5 and abs(axis[1])>0.999]
   holes.append({'part':p.note,'target_mm':target.tolist(),'matched':bool(matches)})
 data['attachment_hole_checks']=holes
 sopen=c.m.cross_x_for_beta(c.m.OPEN_BETA)-c.m.CROSS_CLOSED_X
 opening=[];separation=[]
 for s in np.linspace(0,sopen,65):
  aa=arms(90,float(s));ab=boxes([p for p in aa if p.head])
  opening.extend([float(s),*pair] for pair in pairs(tb,ab))
  separation.extend([float(s),*pair] for pair in pairs(ab,boxes(up)))
 data['opening65_tool_aabb_pairs']=opening;data['opening65_original_core_vs_heads_aabb_pairs']=separation
 # Nominal tray moving-part continuous translational envelope vs static horizontal arms.
 moving={r['id'] for r in c.rows if r['role']=='moving'}
 ms=[]
 for p in up:
  if p.note in moving:
   b=bb(p);b[1,1]+=c.TRAVEL_MM;ms.append((label(p),b))
 data['tray_full_drop_moving_continuous_envelope_vs_LR']=pairs(ms,boxes(a))
 lever=[]
 for drop in np.linspace(0,c.TRAVEL_MM,65):
  lp=c.lever_parts(0 if drop==0 else float(drop)+1.6)
  lever.extend([float(drop),*pair] for pair in pairs(boxes(lp),boxes([p for p in a if p.head])))
 data['lever_drop65_vs_horizontal_LR_heads_aabb_pairs']=lever
 # Confirm vertical baseline problem with native surface witnesses.
 av=[p for p in arms(0) if p.head and p.note=='橡胶胎' and p.pos[1]>0]
 confirmed=[]
 for p in av:
  for q in up:
   if pairs(boxes([p]),boxes([q])):
    point=hit(c.world(p),c.world(q)) or hit(c.world(q),c.world(p))
    if point:confirmed.append({'arm':p.arm,'core':q.note,'point_mm':point})
 data['vertical_original_confirmed_surface_crossings']=confirmed
 # Record narrow-support minimum changes indicated by full-head overlap candidates.
 data['vertical_original_full_heads_aabb_pairs']=pairs(boxes([p for p in arms(0) if p.head]),boxes(up))
 data['hand_box_assumption_mm']=[[-46.6,17,-91.6],[-16.6,47,-51.6]]
 data['hand_box_vs_horizontal_LR_core_aabb_pairs']=pairs([('hand_assumption',np.array(data['hand_box_assumption_mm']))],boxes(up+a))
 data['unchanged_core_vs_fixed_arm_aabb_candidates']=pairs(boxes([p for p in a if not p.head]),boxes(up))
 data['scope_limits']=['AABB non-overlap certifies nominal geometric separation only. Positive pairs are candidates, not proven collisions.','Opening and lever movement are samples, not continuous certification.','No holding load, friction, backlash, actual cube bevel or operator hand envelope verified.','Pusher is manually biased and removable, not a self-centering clamp or load-bearing support.']
 data['source_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'mechanical/candidate.py',ROOT/'mechanical/inputs/baseline_model.py',ROOT/'mechanical/inputs/assembly-integrated-R1.json',ROOT/'mechanical/inputs/baseline-machine-899.mpd']}
 (OUT/'geometry.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
 print(json.dumps(data,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
