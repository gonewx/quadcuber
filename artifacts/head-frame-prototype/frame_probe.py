from pathlib import Path
import sys,json
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/lego/v3'))
import model as m
import mesh_clearance as mesh
import run_check, check, fcl
m.CATALOG.update({'39794.dat':('11x7框架','solid'),'39793.dat':('3x3交叉孔块','solid'),'32184.dat':('三孔垂直接头','solid')})
def frame():
 out=[]
 def a(n,p,r,note,col=1):
  q=m.Part(n,col,np.array(p,float),r,1,note);q.head=True;out.append(q)
 r=m.orient('+z','-x','-y') # local x宽度Z，local z长度-Y
 for x in (-250,-130):a('39794.dat',[x,0,0],r,'前后整框')
 for z in (-80,80):
  a('64179.dat',[-190,0,z],m.FRAME_XY_LONG_X,'左右整框')
  for x in (-250,-130):
   for y in (-40,40):a('2780.dat',[x,y,z*.875],m.ALONG_Z,'整框连接销',0)
 for side in (-1,1):
  a('39793.dat',[-290,0,60*side],m.orient('+x','+z','-y'),'转盘交叉孔接口块',72)
  for y in (-20,20):
   a('2780.dat',[-290,y,50*side],m.ALONG_Z,'转盘接口销',0)
   a('2780.dat',[-260,y,60*side],m.ALONG_X,'后框接口销',0)
 return out
if __name__=='__main__':
 original=m.module(0,steps=False);origin=np.array([m.MODULE_DX,0,0]);fixed=[p for p in original if not p.head];tt=next(p for p in original if p.name=='18938.dat')
 ps=[p.moved(m.I,origin) for p in frame()]
 (Path(__file__).parent/'frame.ldr').write_text(m.to_ldr(fixed+[tt]+ps,'矩形框架接口试验，未通过'))
 print('gear',[(p.name,p.note,p.pos.tolist()) for p in fixed if '齿轮' in p.note],flush=True)
 hits={}
 for angle in range(0,360,5):
  for a in ps:
   a=a.moved(m.rot_x(angle));lo,hi=check._obb(a)
   for b in fixed:
    low,high=check._obb(b)
    if np.any(np.minimum(hi,high)-np.maximum(lo,low)<=1e-7):continue
    if mesh.fitting(a,b):continue
    d=fcl.distance(mesh.obj(a),mesh.obj(b),fcl.DistanceRequest(),fcl.DistanceResult())
    if d<=1e-8:hits.setdefault((a.note,b.note,b.name),[]).append(angle)
 print(json.dumps([{'pair':k,'angles':sorted(set(v))} for k,v in hits.items()],ensure_ascii=False,indent=2))
