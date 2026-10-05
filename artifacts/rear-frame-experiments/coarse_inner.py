"""库存替换几何实验；不作为装配说明。"""
from coarse_rear import *
import coarse_rear as rear
m.CATALOG["3705.dat"]=("4号轴","axle")
m.CONNECTOR_LEN['3705.dat']=80
check.CONNECTOR_LEN.update(m.CONNECTOR_LEN)

def convert(parts):
    out=[]
    ps=rear.convert(parts)
    tt=next(p for p in ps if p.name=='18938.dat');R=tt.rot@m.TT_ROT.T;origin=tt.pos-R@m.TT_C
    c=R.T@(next(p for p in ps if p.note=='Watt公共轴').pos-origin)
    bar=next(p for p in ps if p.note=='Watt横梁');u=(R.T@bar.rot)[:,2]*40
    a=c-u;d=a-np.array([np.sqrt(20**2-a[1]**2),a[1],0])
    oldd=R.T@(next(p for p in ps if p.note=='推杆铰接头').pos-origin);delta=d-oldd
    dr=m.rot_z(np.arctan2(a[1],a[0]-d[0]))
    def add(n,v,r,note,color=m.C_BUSH,step=tt.step):
        q=m.Part(n,color,R@v+origin,R@r,step,note);q.head=True;out.append(q)
    jawnotes={'压头支承薄梁','薄梁固定轴','薄梁固定轴限位','薄梁固定挡套销','轮毂贯穿轴','轮毂','橡胶胎'}
    for p in ps:
        v=R.T@(p.pos-origin);sg=1 if v[2]>=0 else -1;sy=1 if v[1]>0 else -1;n=p.name;r=R.T@p.rot
        if p.note in {'公共轴中隔套','推杆铰接薄梁'}:continue
        if p.note=='输入薄连杆':n='32316.dat';v[2]=10*sg
        elif p.note=='输入关节轴':
            n='4519.dat';v[2]=0;add('32123a.dat',v+[0,0,25*sg],m.BUSH_Z,'输入外半套')
        elif p.note=='输入关节轴套':
            if sg==sy:continue
            v[2]=-25*sy
        elif p.note=='Watt公共轴':n='3705.dat'
        elif p.note=='Watt横梁':v[2]=25*sg
        elif p.note=='公共轴半套':v[2]=35*sg
        elif p.note=='Watt连杆':n='32316.dat';v[2]=40*sg
        elif p.note=='Watt根轴':n='4519.dat';v[2]=50*sg
        elif p.note=='导向根轴限位':v[2]=(25 if abs(v[2])<50 else 75)*sg
        elif p.note=='Watt活动轴':
            if np.linalg.norm(v[:2]-a[:2])<.01:continue
            v[2]=40*sg
        elif p.note=='活动轴半套':v[2]=55*sg
        elif p.note in {'推杆铰接头','推杆铰轴','推杆铰轴半套','推杆短轴','推杆连接器','推杆长轴'}:
            v+=delta
            if p.note in {'推杆铰轴','推杆铰轴半套'}:r=dr@(m.ALONG_Z if p.note=='推杆铰轴' else m.BUSH_Z)
        elif p.note=='压头支承薄梁':v[2]=25*sg
        elif p.note=='薄梁固定轴':
            n='3705.dat'
            add('43857.dat',v+(r@m.ALONG_Z.T)@np.array([10,0,10*sy]),(r@m.ALONG_Z.T)@m.BEAM_X_HOLES_Z,'压头补厚梁',m.C_FRAME)
        elif p.note=='薄梁固定轴限位':v[2]=35*sg
        elif p.note=='薄梁固定挡套销':
            n='3705.dat';v[2]=0
            for z in (-35,35):add('32123a.dat',v+[0,0,z],m.BUSH_Z,'压头第二轴限位')
        elif p.note=='轮毂贯穿轴':
            n='4519.dat'
            for z in (-15,15):add('32123a.dat',v+[0,0,z],m.BUSH_Z,'轮毂内隔套')
        elif n=='32524.dat' and p.color==m.C_JAW:v[2]-=10*sy
        elif n=='3713.dat' and not p.note and abs(v[0]-m.PIVOT_X)<.01 and abs(v[1])==80:
            if sg==-sy:n='32123a.dat';v[2]=-25*sy
            else:
                v[2]=10*sy;add('32123a.dat',v+[0,0,15*sy],m.BUSH_Z,'夹指偏置轴套')
        add(n,v,r,p.note,p.color,p.step)
        out[-1].head=p.head;out[-1].arm=p.arm
    add('3706.dat',a,(R.T@bar.rot)@m.BEAM_X_HOLES_Z.T@m.ALONG_Z,'导向驱动共用轴',m.C_AXLE)
    add('3713.dat',a,(R.T@bar.rot)@m.BEAM_X_HOLES_Z.T@m.BUSH_Z,'导向驱动中套')
    for sg in (-1,1):add('32449.dat',(a+d)/2+[0,0,15*sg],dr@m.BEAM_X_HOLES_Z,'导向驱动薄梁',m.C_LINK)
    return out

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
