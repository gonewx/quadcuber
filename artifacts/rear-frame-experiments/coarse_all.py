"""库存替换几何实验；不作为装配说明。"""
from coarse_rear import *
import coarse_rear as rear
m.CATALOG["3705.dat"]=("4号轴","axle")

def convert(parts):
    out=[]
    tt=next(p for p in parts if p.name=='18938.dat')
    R=tt.rot@m.TT_ROT.T;origin=tt.pos-R@m.TT_C
    def add(n,c,v,r,note,step=tt.step):
        p=m.Part(n,c,R@np.array(v)+origin,R@r,step,note);p.head=True;p.arm=tt.arm;out.append(p)
    removed={'前角连接销','上前垫梁','下前垫梁','前根长销','导向支架长销','上导向垫梁销','后接架长销','后接架三孔垫梁'}
    for p in rear.convert(parts):
        if p.note in removed:continue
        v=R.T@(p.pos-origin);s=1 if v[2]>=0 else -1;r=R.T@p.rot;n=p.name
        if p.note=='输入薄连杆':n='32316.dat';v[2]=30*s
        elif p.note=='输入关节轴':v[2]+=10*s
        elif p.note=='Watt公共轴':n='3706.dat' #6L
        elif p.note=='Watt横梁':v[2]=45*s
        elif p.note=='公共轴半套':v[2]=55*s
        elif p.note=='Watt连杆':n='32316.dat';v[2]=60*s
        elif p.note=='Watt根轴':n='3705.dat';v[2]=70*s #4L
        elif p.note=='导向根轴限位':v[2]=(45 if abs(v[2])<50 else 95)*s
        elif p.note=='Watt活动轴':n='4519.dat';v[2]=60*s
        elif p.note=='活动轴半套':v[2]=75*s
        elif p.note=='Watt支架':v[2]=80*s
        elif p.note=='上导向垫梁':v[2]=60*s
        elif p.note=='前角梁':n='32140.dat';v[0]=-190;v[2]=60*s
        add(n,p.color,v,r,p.note,p.step)
    for s in (-1,1):
        along=m.ALONG_Z if s>0 else m.LPIN_SHORT_Z
        for y in (-20,20):
            add('32523.dat',m.C_FRAME,[-170,y,80*s],m.BEAM_X_HOLES_Z,'前角外垫梁')
            # lower foot takes -150/-130 in z80; shorten padding there
            if y==20:
                out.pop();add('43857.dat',m.C_FRAME,[-180,y,80*s],m.BEAM_X_HOLES_Z,'前角外垫梁')
            for x in (-170,-150):
                add('6558.dat',m.C_LPIN,[x,y,80*s],along,'前角三层销')
        for y in (-40,-20,20,40):
            if y==20:add('6558.dat',m.C_LPIN,[-130,y,60*s],along,'前根重排销')
            else:add('2780.dat',m.C_PIN,[-130,y,50*s],m.ALONG_Z,'前根重排销')
        # upper bracket feet: filler at -230 and -210 in z60
        add('43857.dat',m.C_FRAME,[-220,-20,60*s],m.BEAM_X_HOLES_Z,'导向内垫梁')
        for x in (-230,-210):add('6558.dat',m.C_LPIN,[x,-20,80*s],along,'导向重排销')
        add('32523.dat',m.C_FRAME,[-250,20,80*s],m.BEAM_X_HOLES_Z,'后接架三孔垫梁')
        for x in (-270,-230):add('6558.dat',m.C_LPIN,[x,20,80*s],along,'后接架长销')
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
