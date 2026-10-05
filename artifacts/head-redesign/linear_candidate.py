"""双导轨承重候选；设计试验，未发布装配图。"""
from pathlib import Path
import sys
import json
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'artifacts/rear-frame-experiments'))
from vertical_forward import m, check, ldraw, mesh, fcl, run_check
import vertical_forward as rear
m.CATALOG.update({'32184.dat':('三孔垂直接头','solid'),'41239.dat':('13孔粗梁','solid'),'3705.dat':('4号轴','axle')})
m.CONNECTOR_LEN['3705.dat']=80;check.CONNECTOR_LEN.update(m.CONNECTOR_LEN)
m._crosshead_state=lambda s:(m.CROSS_CLOSED_X-s,0.,0.)
m.OPEN_S=m.CROSS_CLOSED_X-m.cross_x_for_beta(m.OPEN_BETA)
BASE_MODULE=m.module
# 旧构造器仍临时生成随后删除的Watt杆；直线轨迹不满足其杆长。
# 仅将构造朝向归一化，丢弃这些旧件后再检查新候选。
BASE_ORIENT=m.orient
def unit(v):return v if isinstance(v,str) else np.asarray(v)/np.linalg.norm(v)
m.orient=lambda a,b,c=None:BASE_ORIENT(unit(a),unit(b),None if c is None else unit(c))
REMOVE={'Watt支架','上导向垫梁','上导向垫梁销','导向支架长销','上前垫梁','下前垫梁','公共轴中隔套','推杆铰接薄梁','Watt横梁','Watt连杆','Watt根轴','导向根轴限位','Watt活动轴','活动轴半套','推杆铰轴','推杆铰轴半套','推杆短轴','推杆连接器','推杆长轴'}

def convert(parts):
    ps=rear.convert(parts);out=[]
    tt=next(p for p in ps if p.name=='18938.dat');R=tt.rot@m.TT_ROT.T;origin=tt.pos-R@m.TT_C
    c=R.T@(next(p for p in ps if p.note=='Watt公共轴').pos-origin)
    def add(n,v,r,note,color=m.C_FRAME):
        p=m.Part(n,color,R@np.array(v)+origin,R@r,tt.step,note);p.head=True;p.arm=tt.arm;out.append(p);return p
    for p in ps:
        if p.note in REMOVE:continue
        v=R.T@(p.pos-origin);s=1 if v[2]>=0 else -1
        if p.note=='前根长销' and v[1]<0:continue
        if p.note=='输入薄连杆':p.name='32316.dat';v[2]=20*s;p.note='输入粗连杆'
        elif p.note=='输入关节轴':p.name='4519.dat';v[2]=10*s;p.rot=R@m.ALONG_Z
        elif p.note=='输入关节轴套':
            side=1 if v[1]>0 else -1
            if v[2]*side>0:v[2]=35*side
        elif p.note=='Watt公共轴':p.name='3706.dat';p.note='滑块公共轴'
        elif p.note=='公共轴半套':v[2]=55*s
        elif p.note=='推杆铰接头':v=c.copy()
        p.pos=R@v+origin;out.append(p)
    add('50451.dat',c-[170,0,0],m.ALONG_X,'一体推杆',m.C_AXLE)
    for s in (-1,1):
        add('32523.dat',[-130,40,60*s],m.BEAM_Y_HOLES_Z,'下前垫梁')
        add('2780.dat',[-150,20,90*s],m.ALONG_Z,'下前角补销',m.C_PIN)
        add('6536.dat',c+[0,-20,40*s],m.BLOCK_ROT,'导轨滑块')
        add('44294.dat',[-200,-20,40*s],m.ALONG_X,'承重导轨',m.C_AXLE)
        for x in (-265,-135):add('32123a.dat',[x,-20,40*s],m.BUSH_X,'导轨端限位',m.C_BUSH)
        r=m.orient('+z','+y','-x')
        add('32184.dat',[-270,-20,120*s],r,'后导轨座')
        add('2780.dat',[-260,-20,120*s],m.ALONG_X,'后导轨横梁销',m.C_PIN)
        for y in (-40,0):
            add('3705.dat',[-270,y,100*s],m.ALONG_Z,'后座固定轴',m.C_AXLE)
            add('3713.dat',[-270,y,100*s],m.BUSH_Z,'后座整隔套',m.C_BUSH)
            for z in (65,135):add('32123a.dat',[-270,y,z*s],m.BUSH_Z,'后座轴限位',m.C_BUSH)
        add('32184.dat',[-130,-20,60*s],r,'前导轨座')
        add('2780.dat',[-140,-20,60*s],m.ALONG_X,'前导轨横梁销',m.C_PIN)
        for y in (-60,-40):
            add('3705.dat',[-130,y,60*s],m.ALONG_Z,'上前根固定轴',m.C_AXLE)
            if y==-60:add('3713.dat',[-130,y,60*s],m.BUSH_Z,'上前根整隔套',m.C_BUSH)
            for z in (25,95):add('32123a.dat',[-130,y,z*s],m.BUSH_Z,'上前根轴限位',m.C_BUSH)
        add('4519.dat',[-130,0,50*s],m.ALONG_Z,'前座第二固定轴',m.C_AXLE)
        for z in (25,75):add('32123a.dat',[-130,0,z*s],m.BUSH_Z,'前座第二轴限位',m.C_BUSH)
    add('41239.dat',[-250,-20,0],m.BEAM_Z_HOLES_X,'后导轨横梁')
    add('32524.dat',[-150,-20,0],m.BEAM_Z_HOLES_X,'前导轨横梁')
    return out

def module(*a,**k):return convert(BASE_MODULE(*a,**k))

def scan():
    hits={};checks={};count=0
    for frac in np.linspace(0,1,21):
        ps=module(float(frac*m.OPEN_S),steps=False)
        if frac in (0.,1.):checks[str(frac)]={k:f(ps) for k,f in [('孔型',run_check.pins_in_axle_holes),('插深',run_check.pin_depth),('长销',check.long_pins)]}
        bb=[check._obb(p) for p in ps]
        for i,a in enumerate(ps):
            if not a.head:continue
            for j,b in enumerate(ps):
                if a is b or (b.head and j<i):continue
                if not a.note and not b.note:continue
                lo,hi=bb[i];low,high=bb[j]
                if np.any(np.minimum(hi,high)-np.maximum(lo,low)<=1e-7):continue
                if mesh.fitting(a,b):continue
                count+=1;d=fcl.distance(mesh.obj(a),mesh.obj(b),fcl.DistanceRequest(),fcl.DistanceResult())
                if d<=1e-8:
                    key=(a.name,a.note,b.name,b.note)
                    if key not in hits:hits[key]={'行程比例':float(frac),'位置':[a.pos.tolist(),b.pos.tolist()]}
    result={'连接检查':checks,'查询数':count,'相交对':[{'零件对':k,**v} for k,v in hits.items()]}
    return result

if __name__=='__main__':
    out=Path(__file__).resolve().parent
    (out/'linear-candidate.ldr').write_text(m.to_ldr(module(0,steps=False),'双导轨承重候选（未通过）'))
    result=scan();(out/'linear-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
