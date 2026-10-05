"""长边靠转盘竖放的后接架：按现有上下侧梁孔位建立候选。"""
from coarse_rear import *
import coarse_rear as rear

NEW={'竖L后架','竖架三孔梁','竖架上短梁','竖架转盘销','竖架连接长销'}

def convert(parts):
    out=[p for p in parts if p.note not in rear.REMOVED]
    tt=next(p for p in out if p.name=='18938.dat');R=tt.rot@m.TT_ROT.T;origin=tt.pos-R@m.TT_C
    for side in (-1,1):
        def add(n,v,r,note,color=m.C_FRAME):
            p=m.Part(n,color,R@np.array(v)+origin,R@r,tt.step,note);p.head=True;p.arm=tt.arm;out.append(p)
        # 竖L向前让一孔；靠转盘的两根短粗梁留在较内层。
        add('32526.dat',[-270,-60,80*side],m.orient('+x','-z','+y'),'竖L后架',2)
        add('32523.dat',[-270,20,60*side],m.BEAM_X_HOLES_Z,'竖架三孔梁',25)
        add('43857.dat',[-280,-20,60*side],m.BEAM_X_HOLES_Z,'竖架上短梁',25)
        for y in (-20,20):
            add('2780.dat',[-290,y,50*side],m.ALONG_Z,'竖架转盘销',m.C_PIN)
        for x,y in ((-270,-20),(-270,20),(-250,20)):
            add('6558.dat',[x,y,80*side],m.ALONG_Z if side>0 else m.LPIN_SHORT_Z,'竖架连接长销',m.C_LPIN)
        add('2780.dat',[-230,20,90*side],m.ALONG_Z,'竖架连接长销',m.C_PIN)
    return out

def main():
    ps=convert(m.module(0,steps=False));out=Path(__file__).resolve().parent
    (out/'vertical-forward.ldr').write_text(m.to_ldr(ps,'竖向L梁后架候选，未通过'))
    keeper=next(p for p in ps if p.note=='齿轮外限位')
    rows=[]
    for p in ps:
        if p.note not in NEW:continue
        hits=[]
        for angle in range(360):
            q=p.moved(m.rot_x(angle))
            gap=fcl.distance(mesh.obj(q),mesh.obj(keeper),fcl.DistanceRequest(),fcl.DistanceResult())*.4
            if gap<=1e-8:hits.append(angle)
        rows.append({'零件':p.name,'用途':p.note,'位置':p.pos.tolist(),'相交角度_度':hits})
    checks={k:f(ps) for k,f in [('圆销孔型',run_check.pins_in_axle_holes),('销插深',run_check.pin_depth),('长销挡肩',check.long_pins)]}
    report={'基准模型_SHA256':hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest(),'候选说明':'竖L向前一孔，内层上2L/下3L粗梁接转盘，竖L外侧接原侧架；下3L与L短边两点固定。','连接检查':checks,'回转检查':rows}
    (out/'vertical-forward-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
