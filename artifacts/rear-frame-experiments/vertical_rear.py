"""长边靠转盘竖放的后接架：按现有上下侧梁孔位建立候选。"""
from coarse_rear import *
import coarse_rear as rear

NEW={'竖L后架','竖架三孔梁','竖架下垫梁','竖架转盘销','竖架连接长销'}

def convert(parts):
    out=[p for p in parts if p.note not in rear.REMOVED]
    tt=next(p for p in out if p.name=='18938.dat');R=tt.rot@m.TT_ROT.T;origin=tt.pos-R@m.TT_C
    for side in (-1,1):
        def add(n,v,r,note,color=m.C_FRAME):
            p=m.Part(n,color,R@np.array(v)+origin,R@r,tt.step,note);p.head=True;p.arm=tt.arm;out.append(p)
        # 长边竖向；转盘两销用长边第3、第5孔；短边朝前接下侧梁。
        add('32526.dat',[-290,-60,60*side],m.orient('+x','-z','+y'),'竖L后架',2)
        # 3孔梁直接接在L梁朝前的短边外侧，再接原下侧长梁。
        add('32523.dat',[-250,20,80*side],m.BEAM_X_HOLES_Z,'竖架三孔梁',25)
        for y in (-20,20):
            add('2780.dat',[-290,y,50*side],m.ALONG_Z,'竖架转盘销',m.C_PIN)
        for x in (-270,-250):
            add('6558.dat',[x,20,80*side],m.ALONG_Z if side>0 else m.LPIN_SHORT_Z,'竖架连接长销',m.C_LPIN)
        add('2780.dat',[-230,20,90*side],m.ALONG_Z,'竖架连接长销',m.C_PIN)
    return out

def main():
    ps=convert(m.module(0,steps=False));out=Path(__file__).resolve().parent
    (out/'vertical-rear.ldr').write_text(m.to_ldr(ps,'竖向L梁后架候选，未通过'))
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
    report={'基准模型_SHA256':hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest(),'候选说明':'长边在转盘处竖放，3/5孔接转盘；短边向前，与下侧7L梁两点连接；3孔粗梁垫在朝前短边与下侧7L之间，两点固定。','连接检查':checks,'回转检查':rows}
    (out/'vertical-rear-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
