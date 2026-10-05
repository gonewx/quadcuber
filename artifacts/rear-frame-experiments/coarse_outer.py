"""库存替换几何实验；不作为装配说明。"""
from coarse_rear import *
import coarse_rear as rear
m.CATALOG["3705.dat"]=("4号轴","axle")

def convert(parts):
    out=rear.convert(parts)
    tt=next(p for p in out if p.name=='18938.dat')
    R=tt.rot@m.TT_ROT.T;origin=tt.pos-R@m.TT_C
    added=[]
    joints=[R.T@(p.pos-origin) for p in out if p.note=='输入关节轴']
    for p in out:
        v=R.T@(p.pos-origin);sg=1 if v[2]>=0 else -1
        def bush(z,note):
            q=m.Part('3713.dat',m.C_BUSH,R@(v*np.array([1,1,0])+[0,0,z])+origin,R@m.BUSH_Z,p.step,note);q.head=True;added.append(q)
        if p.note=='输入薄连杆':p.name='32316.dat';v[2]=60*sg
        elif p.note=='输入关节轴':p.name='32073.dat';v[2]=30*sg;p.rot=R@m.ALONG_Z
        elif p.note=='输入关节轴套':
            j=min(joints,key=lambda j:np.linalg.norm(j[:2]-v[:2]))
            js=1 if j[2]>0 else -1
            if v[2]*js>0:
                v[2]=75*js
                for z in (20,40):bush(z*js,'输入间隔整套')
        elif p.note=='Watt公共轴':p.name='3707.dat'
        elif p.note=='Watt横梁':v[2]=25*sg
        elif p.note=='公共轴半套':v[2]=75*sg;bush(40*sg,'公共轴输入隔套')
        elif p.note=='Watt连杆':p.name='32316.dat';v[2]=40*sg
        elif p.note=='Watt根轴':p.name='3705.dat';v[2]=50*sg
        elif p.note=='导向根轴限位':v[2]=(25 if abs(v[2])<50 else 75)*sg
        elif p.note=='Watt活动轴':p.name='4519.dat';v[2]=40*sg
        elif p.note=='活动轴半套':v[2]=55*sg
        p.pos=R@v+origin
    return out+added

if __name__=='__main__':
    ps=convert(m.module(0,steps=False))
    Path(__file__).with_suffix('.ldr').write_text(m.to_ldr(ps,'粗梁分层实验'))
    print('checks', {name:fn(ps) for name,fn in [('孔型',run_check.pins_in_axle_holes),('插深',run_check.pin_depth),('长销',check.long_pins)]})
    # Inspect all solids except known fitted pairs, broad phase then triangles.
    issues={}
    for frac in np.linspace(0,1,11):
        ps=convert(m.module(float(frac*m.OPEN_S),steps=False))
        bounds=[check._obb(p) for p in ps]
        for i,a in enumerate(ps):
            if not a.head:continue
            for j in range(i+1,len(ps)):
                b=ps[j]
                lo,hi=bounds[i];low,high=bounds[j]
                if np.any(np.minimum(hi,high)-np.maximum(lo,low)<=1e-7):continue
                if mesh.fitting(a,b):continue
                dist=fcl.distance(mesh.obj(a),mesh.obj(b),fcl.DistanceRequest(),fcl.DistanceResult())
                if dist<=1e-8 and not rear.intended_mount(a,b):
                    key=(a.name,a.note,b.name,b.note)
                    if key not in issues:issues[key]=(frac,a.pos.tolist(),b.pos.tolist())
    for k,v in issues.items():print(k,v)
    print('pair count',len(issues))
