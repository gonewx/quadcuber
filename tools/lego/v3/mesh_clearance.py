"""不侵蚀三角网格的局部间隙复查：新前端与后部连接，81个开合位置。

FCL测三角面距离。轴孔配合、轮胎配合及名义贴合面单列；不把该离散
扫描表述成整机任意状态的连续证明。依赖python-fcl。
"""
import hashlib
import json
from pathlib import Path

import fcl
import numpy as np
import model
import run_check  # noqa: F401
import check
import ldraw

MESHES = {}


def obj(p):
    if p.name not in MESHES:
        t=ldraw.geometry(p.name)[0]
        b=fcl.BVHModel()
        b.beginModel(len(t)*3,len(t))
        b.addSubModel(t.reshape(-1,3),np.arange(len(t)*3).reshape(-1,3))
        b.endModel()
        MESHES[p.name]=b
    return fcl.CollisionObject(MESHES[p.name],fcl.Transform(p.rot,p.pos))


def fitting(a,b):
    if check._allowed(a,b):
        return '轮胎轮毂等明确配合'
    for p,s in ((a,b),(b,a)):
        if p.kind in ('pin','axle') and s.kind in ('solid','bush') and check._pin_layers(p,[s]):
            return '轴销进入实际孔段，插深和孔型另查'
    return None


def mounting_contact(a,b):
    """转盘安装耳端面与相邻支承梁的名义贴合；不是体积穿入豁免。"""
    turntable,pad=(a,b) if a.name=='18938.dat' else (b,a)
    if turntable.name!='18938.dat' or pad.note not in ('转盘垫梁','转盘后横梁'):
        return False
    moved=pad.moved(np.eye(3))
    # 用转盘局部耳方向，因而也适用于机械头已回转的姿态。
    normal=turntable.rot[:,0]
    sign=np.sign((pad.pos-turntable.pos)@normal)
    moved.pos+=sign*normal*1e-4
    distance=fcl.distance(obj(turntable),obj(moved),fcl.DistanceRequest(),fcl.DistanceResult())
    return distance>=.999e-4


def front_rotation_check():
    """新前端对本臂固定件和竖直邻臂，用网格距离补查旧体素姿态扫描。"""
    worst=None; hits=[]; tested=0; states=0
    for stroke in (0.,model.OPEN_S):
        for angle in range(0,360,5):
            for neighbor in (0.,model.OPEN_S):
                parts=model.build({'L':(stroke,angle),'F':(neighbor,0.),'B':(neighbor,0.)},with_cube=False)
                moving=[p for p in parts if p.arm=='L' and p.head and p.note]
                fixed=[p for p in parts if p.arm in ('F','B') or (p.arm=='L' and not p.head)]
                bounds={id(p):check._obb(p) for p in moving+fixed}
                flo=np.array([bounds[id(p)][0] for p in fixed])
                fhi=np.array([bounds[id(p)][1] for p in fixed])
                states+=1
                for a in moving:
                    lo,hi=bounds[id(a)]
                    candidates=np.flatnonzero(np.linalg.norm(np.maximum(np.maximum(flo-hi,lo-fhi),0),axis=1)<5)
                    for index in candidates:
                        b=fixed[index]
                        if fitting(a,b):continue
                        dist=fcl.distance(obj(a),obj(b),fcl.DistanceRequest(),fcl.DistanceResult())*.4
                        tested+=1
                        row={'零件对':[a.name,a.note,b.name,b.note],'邻臂':b.arm,
                             '本臂开度':stroke/model.OPEN_S,'回转角_deg':angle,
                             '邻臂开度':neighbor/model.OPEN_S,'间隙_mm':dist}
                        if worst is None or dist<worst['间隙_mm']:worst=row
                        if dist<=1e-8:hits.append(row)
    return {'状态数':states,'AABB候选阈值_mm':2.0,'全部零件对间隙下界_mm':min(2.,worst['间隙_mm']) if worst else 2.,'距离查询数':tested,'最小候选距离':worst,'相交数':len(hits),'相交记录':hits}


def main():
    worst={}; contacts=set(); excluded=set(); hits=[]; tested=0
    for frac in np.linspace(0,1,81):
        parts=model.module(float(frac*model.OPEN_S),steps=False)
        changed={id(p) for p in parts if p.note}
        bounds={id(p):check._obb(p) for p in parts}
        objects={id(p):obj(p) for p in parts}
        for i,a in enumerate(parts):
            for b in parts[i+1:]:
                if id(a) not in changed and id(b) not in changed:
                    continue
                lo,hi=bounds[id(a)];blo,bhi=bounds[id(b)]
                if np.linalg.norm(np.maximum(np.maximum(blo-hi,lo-bhi),0))>5:
                    continue
                key=(a.name,a.note,b.name,b.note)
                reason=fitting(a,b)
                if reason:
                    excluded.add((*key,reason));continue
                overlap=np.minimum(hi,bhi)-np.maximum(lo,blo)
                if np.any(abs(overlap)<1e-8):
                    contacts.add(key);continue
                dist=fcl.distance(objects[id(a)],objects[id(b)],fcl.DistanceRequest(),fcl.DistanceResult())*.4
                tested+=1
                if dist<=1e-8 and mounting_contact(a,b):
                    contacts.add(key);continue
                row={'零件对':key,'间隙_mm':dist,'行程比例':float(frac)}
                if key not in worst or dist<worst[key]['间隙_mm']:
                    worst[key]=row
                if dist<=1e-8:
                    hits.append(row)
    front=front_rotation_check()
    data={'前端回转对竖直邻臂和本臂固定件':front,'方法':'FCL三角网格；81个行程，头部回转角0°；只覆盖带用途标记的改动件与其附近零件。旋转推杆/轴套和魔方另查连续包络。',
          'model.py_SHA256':hashlib.sha256(Path(model.__file__).read_bytes()).hexdigest(),
          '距离查询数':tested,'相交数':len(hits),'相交记录':hits,
          '最小间隙':sorted(worst.values(),key=lambda r:r['间隙_mm']),
          '名义平面接触':sorted(contacts),'有意配合':sorted(excluded)}
    out=Path(__file__).resolve().parents[3]/'docs/lego/v3/mesh_clearance.json'
    out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print('距离查询数:',tested,'相交数:',len(hits))
    for row in data['最小间隙'][:8]:
        print(row)
    print('前端回转补查:',front)
    return bool(hits or front['相交数'])


if __name__=='__main__':
    raise SystemExit(main())
