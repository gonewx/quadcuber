"""粗梁后接架候选：只构造对照，不修改正式模型。

每侧一根32526粗L梁＋一根32523三孔粗梁；L短边接转盘上下两孔，
长边沿下侧朝前，三孔梁垫在L梁与外侧7孔梁之间。
"""
from pathlib import Path
import sys
import hashlib
import json
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/lego/v3'))
import model as m
import run_check
import check
import ldraw
import mesh_clearance as mesh
import fcl

REMOVED={'转盘后横梁','转盘轴销','后短连接梁','侧架后连接轴','侧架后连接隔套'}
NEW={'粗梁后接架','后接架三孔垫梁','后接架转盘销','后接架长销'}


def convert(parts):
    out=[p for p in parts if p.note not in REMOVED]
    t=next(p for p in out if p.name=='18938.dat')
    # 由真实转盘姿态建立模块局部坐标，兼容闭合/张开及头部绕X回转。
    R=t.rot@m.TT_ROT.T
    origin=t.pos-R@m.TT_C
    for side in (-1,1):
        specs=[('32526.dat',m.C_FRAME,[-210,20,60*side],m.orient('-y','+z','-x'),'粗梁后接架'),
               ('32523.dat',m.C_FRAME,[-250,20,80*side],m.BEAM_X_HOLES_Z,'后接架三孔垫梁')]
        specs += [('2780.dat',m.C_PIN,[-290,y,50*side],m.ALONG_Z,'后接架转盘销') for y in (-20,20)]
        specs += [('6558.dat',m.C_LPIN,[x,20,80*side],m.ALONG_Z if side>0 else m.LPIN_SHORT_Z,'后接架长销') for x in (-270,-230,-210)]
        for name,color,pos,rot,note in specs:
            p=m.Part(name,color,R@np.array(pos)+origin,R@rot,t.step,note)
            p.head=True;p.arm=t.arm;out.append(p)
    return out


def intended_mount(a,b):
    # 粗L梁与转盘安装耳的端面贴合；只在外移0.0001LDU后完全分离时接受。
    if {a.name,b.name}!={'32526.dat','18938.dat'}:return False
    pad,tt=(a,b) if a.name=='32526.dat' else (b,a)
    if pad.note!='粗梁后接架':return False
    normal=tt.rot[:,0];side=np.sign((pad.pos-tt.pos)@normal)
    shifted=pad.moved(m.I,side*normal*1e-4)
    return fcl.distance(mesh.obj(shifted),mesh.obj(tt),fcl.DistanceRequest(),fcl.DistanceResult())>=.999e-4


def scan():
    results={};collisions=[];queries=0
    for frac in np.linspace(0,1,81):
        parts=convert(m.module(float(frac*m.OPEN_S),steps=False))
        bounds={id(p):check._obb(p) for p in parts}
        for a in parts:
            if a.note not in NEW:continue
            for b in parts:
                if a is b or (b.note in NEW and parts.index(b)<parts.index(a)):continue
                lo,hi=bounds[id(a)];low,high=bounds[id(b)]
                if np.linalg.norm(np.maximum(np.maximum(low-hi,lo-high),0))>5:continue
                if mesh.fitting(a,b):continue
                if np.any(abs(np.minimum(hi,high)-np.maximum(lo,low))<1e-8):continue
                distance=fcl.distance(mesh.obj(a),mesh.obj(b),fcl.DistanceRequest(),fcl.DistanceResult())*.4
                queries+=1
                if distance<=1e-8 and intended_mount(a,b):continue
                key=(a.name,a.note,b.name,b.note)
                row={'零件对':key,'间隙_mm':distance,'行程比例':float(frac)}
                if key not in results or distance<results[key]['间隙_mm']:results[key]=row
                if distance<=1e-8:collisions.append(row)
    return dict(开度数=81,距离查询数=queries,相交数=len(collisions),相交记录=collisions,最小间隙=sorted(results.values(),key=lambda r:r['间隙_mm']))


def rotation():
    from mechanical_audit import clip_x
    parts=convert(m.module(0,steps=False))
    keeper=next(p for p in parts if p.note=='齿轮外限位')
    lo,hi=check._obb(keeper)
    kmesh=ldraw.geometry(keeper.name)[0]@keeper.rot.T+keeper.pos
    kradius=np.linalg.norm(kmesh[:,:,1:]-keeper.pos[1:],axis=2).max()
    radius=np.linalg.norm(keeper.pos[1:]);rows=[]
    for p in parts:
        if p.note not in NEW:continue
        a,b=check._obb(p)
        axial=max(float(lo[0]-b[0]),float(a[0]-hi[0]),0.)
        if axial>0:gap=axial;method='轴向分离'
        else:
            clipped=clip_x(ldraw.geometry(p.name)[0]@p.rot.T+p.pos,lo[0],hi[0])
            gap=float(radius-kradius-np.linalg.norm(clipped[:,:,1:],axis=2).max());method='连续360度径向包络'
        rows.append(dict(零件=p.name,用途=p.note,下界_mm=gap*.4,方法=method))
    return dict(最小下界_mm=min(r['下界_mm'] for r in rows),记录=rows)


def main():
    ps=convert(m.module(0,steps=False))
    output=Path(__file__).resolve().parent
    (output/'coarse-rear.ldr').write_text(m.to_ldr(ps,'粗梁后接架候选（待实物试装）'))
    checks={name:fn(ps) for name,fn in [('圆销与十字孔',run_check.pins_in_axle_holes),('插深',run_check.pin_depth),('长销挡肩',check.long_pins),('挡环装配',run_check.collar_pins)]}
    result={'基准模型_SHA256':hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest(),'结构':'每侧32526＋32523，L梁走下侧，三孔粗梁作长边垫层；两转盘销、三长销',
            '连接检查':checks,'开合网格':scan(),'新增件对齿轮外轴套整圈':rotation(),'实物刚度':'未测，不能据名义网格确认手感和承重改善'}
    (output/'coarse-rear-checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='开合网格'},ensure_ascii=False,indent=2))
    print('开合网格',result['开合网格']['相交数'],'相交；最小距离',result['开合网格']['最小间隙'][:6])
    return bool(any(checks.values()) or result['开合网格']['相交数'] or result['新增件对齿轮外轴套整圈']['最小下界_mm']<=0)


if __name__=='__main__':raise SystemExit(main())
