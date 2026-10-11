"""Integrated reversible support plus 60483 head candidate. Frozen originals remain unchanged."""
from pathlib import Path
import importlib.util,functools,numpy as np,math
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('baseline60483',HERE/'source/baseline_model.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
files={};n=None
for line in (HERE/'source/baseline-machine-899.mpd').read_text().splitlines():
 if line.startswith('0 FILE '):n=line[7:].replace('\\','/').lower();files[n]=[]
 elif n:files[n].append(line)
for p in (HERE/'parts').glob('*.dat'):
 name=('s/'if p.name in ['60483s01.dat','6538s01.dat']else'')+p.name;files[name]=p.read_text().splitlines()
def resolve(n):
 n=n.replace('\\','/').lower()
 for k in [n,'p/'+n,'parts/'+n,'s/'+n]:
  if k in files:return k
 raise KeyError(n)
@functools.lru_cache(None)
def mesh(n):
 tris=[]
 for line in files[resolve(n)]:
  s=line.split()
  if not s:continue
  if s[0]=='1':
   v=np.array(s[2:14],float);tris.extend(mesh(' '.join(s[14:]))@v[3:].reshape(3,3).T+v[:3])
  elif s[0]=='3':tris.append(np.array(s[2:11],float).reshape(3,3))
  elif s[0]=='4':
   q=np.array(s[2:14],float).reshape(4,3);tris.extend([q[[0,1,2]],q[[0,2,3]]])
 return np.asarray(tris).reshape(-1,3,3)
def world(p):return (mesh(p.name)@p.rot.T+p.pos)*.4
def replace_module(pp):
 out=[];new=[];removed=[]
 for p in pp:
  if p.note in ['开限位挡轴','开限位挡轴轴套'] or (p.name=='32056.dat'and p.note=='限位支架'):
   removed.append(p)
   continue
  out.append(p)
 # Obtain pair centroids and exact transformed old local axes. No world pose assumptions.
 old=[p for p in removed if p.name=='32056.dat'];used=set()
 for i,p in enumerate(old):
  if i in used:continue
  j=next(j for j,q in enumerate(old)if j!=i and j not in used and np.allclose(p.rot,q.rot)and abs(np.linalg.norm(p.pos-q.pos)-10)<1e-6)
  used.update([i,j]);q=old[j]
  # 60483 cross hole at local0, round at local+Z20. Old root at old+Z40.
  R=p.rot@np.diag([-1.,1.,-1.]);pos=(p.pos+q.pos)/2+p.rot@np.array([0,0,40.])
  a=m.Part('60483.dat',p.color,pos,R,p.step,'60483根轴支架（无开挡轴）');a.arm,a.head,a.sub=p.arm,p.head,p.sub
  out.append(a);new.append(a)
 assert len(old)==8 and len(new)==4 and len(removed)==14 and len(out)==len(pp)-10
 return out
BASE_MODULE=m.module

def module(open_s=0.,angle=0.,steps=False,on_base=True):
 pp=replace_module(BASE_MODULE(open_s,angle,steps,on_base))
 # Authorized wall-foot correction. LDraw +Y is physical down.
 for i in ([48,49] if on_base else []):
  p=pp[i];assert p.name=='2780.dat'and not p.head
  pp[i]=p.moved(np.eye(3),[0,10,0])
 return pp
def state_parts(state,candidate=True):
 pp=[]
 for arm in m.ARMS:
  s,a=state.get(arm,(0.,0.));mm=module(s,a)if candidate else BASE_MODULE(s,a,False,True)
  for p in mm:q=p.moved(m.ARM_ROT[arm]);q.arm=arm;pp.append(q)
 return pp

def natural_stroke():
 h=m.CRANK_C[1]-m.BLOCK_Y;th=-math.atan2(h,math.sqrt((m.LINK2_L+m.CRANK_R)**2-h*h))
 cp=m.CRANK_C+m.CRANK_R*np.array([math.cos(th),math.sin(th)])
 return float(cp[0]+math.sqrt(m.LINK2_L**2-(cp[1]-m.BLOCK_Y)**2)-m.BLOCK_X_CLOSED)

# Full integrated review: preserve original inputs, expose one source of truth.
import json,copy
original_rows=json.loads((HERE/'source/assembly132.json').read_text())
r1_rows=json.loads((HERE/'source/assembly-integrated-R1.json').read_text())
removed_ids=[r['id'] for r in r1_rows if r['role']=='key']
rows=[copy.deepcopy(r) for r in r1_rows if r['role']!='key']
REVISION='INTEGRATED-GRAVITY-R4-2026-10-08'
TRAVEL_MM=40.8
AZ=np.array([[0,0,-1],[0,1,0],[1,0,0]])
BYZ=np.array([[1,0,0],[0,0,-1],[0,1,0]])
def lever_parts(parameter_mm=0):
 dy=47.2+parameter_mm-80
 v=np.array([-math.sqrt(112**2-dy**2),dy,0])/112
 N=np.array([0.,0.,1.]);T=np.cross(N,v);R=np.stack([T,N,v],1)
 root=np.array([112.,80.,0.]);Q=root+112*v;pp=[]
 def add(n,xyz,rot,note):pp.append(m.Part(n,14,np.array(xyz)/.4,np.array(rot),0,note))
 for z in [-32,32]:add('32278.dat',root+[0,0,z]+56*v,R,f'inner_arm_z{z}')
 add('32278.dat',root+[0,0,-40]-24*v,R,'outer_handle')
 for lam in [16,32]:add('2780.dat',root+lam*v+[0,0,-36],AZ,f'root_overlap_pin_{lam}')
 add('3708.dat',root+[0,0,-4],AZ,'root_12L_axle')
 for z in [-46,38]:add('32123a.dat',root+[0,0,z],np.eye(3),f'root_retainer_{z}')
 add('23948.dat',Q,AZ,'end_11L_axle')
 for z in [-38,38]:add('32123a.dat',Q+[0,0,z],np.eye(3),f'end_retainer_{z}')
 for z in [-20,20]:add('62462.dat',Q+[0,0,z],AZ,f'end_spacer2L_{z}')
 for z in [-8,8]:add('18654.dat',Q+[0,0,z],BYZ,f'end_spacer1L_{z}')
 add('3713.dat',Q,np.eye(3),'center_roller_bush')
 C=root-56*v
 add('3705.dat',C+[0,0,-36],AZ,'stop_4L_axle')
 add('3713.dat',C+[0,0,-32],np.eye(3),'stop_bush')
 add('32123a.dat',C+[0,0,-46],np.eye(3),'stop_outer_retainer')
 add('32123a.dat',C+[0,0,-26],np.eye(3),'stop_inner_retainer')
 return pp
for p in lever_parts():
 rows.append(dict(id=p.note,name=p.name,color=p.color,role='lever',functional_group='gravity_lever',note=p.note,position_ldu=p.pos.tolist(),rotation=p.rot.tolist(),baseline_index1=None,old109_index1=None))
changed_ids=[p.note for p in lever_parts()]
for i,r in enumerate(rows,1):r['index1']=i
assert len(rows)==150

def core_parts(drop_mm=0,locks=False,lever_parameter_mm=None):
 # locks is retained only for old callers; both working locks are physically absent in every R3 state.
 if not 0<=drop_mm<=TRAVEL_MM:raise ValueError('Tray pose outside nominal0..40.8mm range')
 if lever_parameter_mm is None:lever_parameter_mm=0 if drop_mm==0 else drop_mm+1.6
 ordinary=[m.Part(r['name'],r['color'],np.array(r['position_ldu'])+np.array([0,drop_mm/.4 if r['role']=='moving'else 0,0]),r['rotation'],0,r['id'])for r in rows if r['role']!='lever']
 return ordinary+lever_parts(lever_parameter_mm)
def original_retained_base():
 out=[]
 for line in [l for l in files['machine_working-899.ldr']if l.startswith('1 ')][132:191]:
  s=line.split();v=np.array(s[2:14],float);out.append(m.Part(s[14],int(s[1]),v[:3],v[3:].reshape(3,3),0,'retained59'))
 return out
def retained_base():
 # Approved R4: close missing R-B corner; frozen support/lever untouched.
 out=original_retained_base()
 for i,pos,rot in [(1,[260,280,-80],[[0,0,-1],[0,1,0],[1,0,0]]),(6,[120,280,-260],[[-1,0,0],[0,1,0],[0,0,-1]])]:
  assert out[i].name=='32524.dat'
  out[i]=m.Part('32278.dat',72,np.array(pos,dtype=float),np.array(rot,dtype=float),0,'closed_base_15L')
 out.append(m.Part('32526.dat',14,np.array([120.,260.,-160.]),np.eye(3),0,'closed_RB_corner'))
 pinrot=np.array([[0,1,0],[1,0,0],[0,0,-1]],dtype=float)
 for pos in [[120,270,-80],[160,270,-80],[120,270,-160],[120,270,-120]]:
  out.append(m.Part('2780.dat',0,np.array(pos,dtype=float),pinrot.copy(),0,'closed_RB_corner_pin'))
 assert len(out)==64
 return out
def full_machine(state,drop_mm=0,locks=True):return core_parts(drop_mm,locks)+retained_base()+state_parts(state)
