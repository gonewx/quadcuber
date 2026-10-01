"""未采用的短横梁候选；只在内存中构造模型，不改正式模型或验证结果。

从仓库根目录运行：
  tools/lego/.cache/venv/bin/python artifacts/clearance-experiments/compact_watt.py
输出相交是此候选的预期失败证据，不代表正式模型存在同一碰撞。
"""
import sys,types,pathlib,hashlib
root=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'tools/lego/v3'))
import model as old
src=pathlib.Path(old.__file__).read_text()
assert hashlib.sha256(src.encode()).hexdigest()=="57f59768f287afb6141984c21c39aa2534436d5ada284bf2ba142cbb4ddbd492", "基准模型已变更，请重新审查候选变换"
edits={
'WATT_HALF_SPAN = 40.0':'WATT_HALF_SPAN = 20.0',
'[[-230., -80., 0.], [-150., 80., 0.]]':'[[-210., -80., 0.], [-170., 80., 0.]]',
'DRIVE_LINK_L = 60.0':'DRIVE_LINK_L = 40.0',
'if yy==20 and xx==-150:':'if (yy==20 and xx==-150) or (yy==-20 and xx==-190):',
'        hadd("43857.dat",C_FRAME,[-240,-20,80*sz],BEAM_X_HOLES_Z,s,"上导向垫梁")\n':'',
'        hadd("2780.dat",C_PIN,[-250,-20,90*sz],ALONG_Z,s,"上导向垫梁销")\n':'',
'((-230,-20),(-210,-20),(-150,20))':'((-210,-20),(-190,-20),(-170,20),(-150,20))',
'hadd("43857.dat",C_FRAME,[PIVOT_X,50,60*sz],BEAM_Y_HOLES_Z,s,"下前垫梁")':'hadd("32523.dat",C_FRAME,[PIVOT_X,40,60*sz],BEAM_Y_HOLES_Z,s,"下前垫梁")',
'hadd("32449.dat",C_LINK,(c+drive)/2':'hadd("6632.dat",C_LINK,(c+drive)/2',
'hadd("11478.dat",C_LINK,c+':'hadd("6632.dat",C_LINK,c+',
'hadd("4519.dat",C_AXLE,g+[0,0,55*sz],ALONG_Z,s,"Watt根轴")':'hadd("24316.dat",C_AXLE,g+[0,0,68*sz],LPIN_SHORT_Z if sz==1 else ALONG_Z,s,"Watt根轴")',
'for z in (35,75):':'for z in (75,):',
'hadd("4519.dat",C_ROD,[rod_front-30,0,0]':'hadd("3705.dat",C_ROD,[rod_front-40,0,0]',
'[rod_front-60,0,0]':'[rod_front-80,0,0]',
'[rod_front-180,0,0]':'[rod_front-200,0,0]',
'CATALOG = {':'CATALOG = {\n    "3705.dat": ("4 号轴", "axle"),',
}
for a,b in edits.items():
 assert a in src,a
 src=src.replace(a,b)
m=types.ModuleType('compact_candidate');m.__file__=old.__file__;sys.modules[m.__name__]=m
src=src.replace('(c+drive)/2+[0,0,15*sy]','(c+drive)/2-20*drive_direction+[0,0,15*sy]')
src=src.replace('c+[0,0,35*sy],rot_z(guide_theta)','c-20*np.array([math.cos(guide_theta),math.sin(guide_theta),0.])+[0,0,35*sy],rot_z(guide_theta)')
exec(compile(src,m.__file__,'exec'),m.__dict__)
import run_check,mesh_clearance,check,numpy as np,fcl
check.CONNECTOR_LEN.update(m.CONNECTOR_LEN)
print('OPEN_S',old.OPEN_S,m.OPEN_S,'angles',*[np.degrees(m.jaw_beta(m.OPEN_S,sy)) for sy in [-1,1]],flush=True)
worst={};hits=[]
for frac in np.linspace(0,1,81):
 parts=m.module(float(frac*m.OPEN_S),steps=False)
 bounds=[check._obb(p) for p in parts];objects=[mesh_clearance.obj(p) for p in parts]
 for i,a in enumerate(parts):
  for k in range(i+1,len(parts)):
   b=parts[k]
   if not(a.note or b.note):continue
   lo,hi=bounds[i];blo,bhi=bounds[k]
   if np.linalg.norm(np.maximum(np.maximum(blo-hi,lo-bhi),0))>5:continue
   if mesh_clearance.fitting(a,b):continue
   if np.any(abs(np.minimum(hi,bhi)-np.maximum(lo,blo))<1e-8):continue
   d=fcl.distance(objects[i],objects[k],fcl.DistanceRequest(),fcl.DistanceResult())*.4
   if d<=1e-8 and mesh_clearance.mounting_contact(a,b):continue
   key=(a.name,a.note,b.name,b.note)
   if key not in worst or d<worst[key][0]:worst[key]=(d,float(frac))
   if d<=1e-8:hits.append((key,d,float(frac)))
print('HITS',len(hits),hits[:20])
for k,v in sorted(worst.items(),key=lambda kv:kv[1][0])[:40]:print(k,v)
