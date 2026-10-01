"""防翻折几何：双解、后拉汇合点、挡轴转动敏感性、工作行程与异常挡止。

独立旋转主臂查实体接触，不用jaw_beta预先选择分支掩盖翻折；不模拟弹性越过挡轴。
"""
import hashlib
import json
import math
from pathlib import Path

import fcl
import numpy as np
import model as m
from mesh_clearance import obj


def gap(a,b):
    return fcl.distance(obj(a),obj(b),fcl.DistanceRequest(),fcl.DistanceResult())*.4


def main():
    ps=m.module(0,steps=False)
    stops=[p for p in ps if p.note=='开限位挡轴']
    assert len(stops)==2
    tangencies={}
    for side in (-1,1):
        lo,hi=m.OPEN_S,m.OPEN_S+10.
        for _ in range(60):
            mid=(lo+hi)/2;c,_=m.crosshead_pose(mid)
            radius=math.hypot(m.PIVOT_X-c[0],side*m.JAW_Y-c[1])
            if radius>m.JAW_A+m.LINK_L:hi=mid
            else:lo=mid
        stroke=(lo+hi)/2;c,_=m.crosshead_pose(stroke)
        angle=math.degrees(math.atan2(m.JAW_Y-side*c[1],m.PIVOT_X-c[0]))
        tangencies[side]={'推杆行程_LDU':stroke,'汇合角_deg':angle}
    tangent_stroke=min(row['推杆行程_LDU'] for row in tangencies.values())*.4
    branches=[]
    for s in (0.,m.OPEN_S):
        c,_=m.crosshead_pose(s)
        for side in (-1,1):
            dx,dy=m.PIVOT_X-c[0],m.JAW_Y-side*c[1]
            r=math.hypot(dx,dy);alpha=math.atan2(dy,dx)
            delta=math.acos((r*r+m.JAW_A**2-m.LINK_L**2)/(2*r*m.JAW_A))
            branches.append({'夹指':'下' if side>0 else '上','推杆后退_mm':s*.4,
                             '正常角_deg':math.degrees(alpha-delta),'另一解_deg':math.degrees(alpha+delta)})
    rows=[]
    for stop in stops:
        sy=np.sign(stop.pos[1]);pivot=np.array([m.PIVOT_X+m.MODULE_DX,sy*m.JAW_Y,0.])
        beam=m.Part('32524.dat',4,pivot,m.I,0)
        tangent_angle=tangencies[sy]["汇合角_deg"]
        for roll in range(0,91,5):
            stop.rot=m.ALONG_Z@m.rot_x(roll)
            def at(deg):
                beam.rot=m.rot_z(sy*math.radians(deg))@m.BEAM_X_HOLES_Z
                return gap(beam,stop)
            work_gap=at(math.degrees(m.OPEN_BETA))
            assert work_gap>=1,work_gap
            lo,hi=25.,35.
            assert at(hi)<=1e-8
            for _ in range(32):
                mid=(lo+hi)/2
                if at(mid)<=1e-7:hi=mid
                else:lo=mid
            # 异常挡止后的角度继续取样，不能只证明一个零宽度接触点。
            assert all(at(deg)<=1e-8 for deg in np.linspace(hi+.01,tangent_angle,50))
            first_contact=hi
            slo,shi=0.,tangencies[sy]['推杆行程_LDU']-1e-9
            for _ in range(60):
                smid=(slo+shi)/2
                if math.degrees(m.jaw_beta(smid,sy))>first_contact:shi=smid
                else:slo=smid
            stroke=(slo+shi)*.2
            rows.append({'夹指':'下' if sy>0 else '上','挡轴自转_deg':roll,'25度工作间隙_mm':work_gap,
                         '首次接触角_deg':first_contact,'接触对应推杆后退_mm':stroke,'距汇合点行程_mm':tangencies[sy]['推杆行程_LDU']*.4-stroke})
    out={'model.py_SHA256':hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest(),
         '两组角度':branches,'各夹指汇合点':{str(side):{'汇合角_deg':r['汇合角_deg'],'汇合行程_mm':r['推杆行程_LDU']*.4} for side,r in tangencies.items()},
         '最早汇合行程_mm':tangent_stroke,
         '正常开行程_mm':m.OPEN_S*.4,'两组解汇合前剩余后拉_mm':tangent_stroke-m.OPEN_S*.4,
         '名义挡轴方向接触':[r for r in rows if r['挡轴自转_deg']==0],
         '挡轴自转采样接触角范围_deg':[min(r['首次接触角_deg'] for r in rows),max(r['首次接触角_deg'] for r in rows)],
         '工作间隙最小_mm':min(r['25度工作间隙_mm'] for r in rows),
         '汇合点行程裕量最小_mm':min(r['距汇合点行程_mm'] for r in rows),'接触记录':rows,
         '结论':'刚性名义网格在正常开度留隙，异常开合在汇合前被挡；实物防翻折与挡轴强度待手动验收。',
         '限制':['挡轴自转每5度采样；接触后到汇合角取50点，未进行连续弹性接触仿真。',
                  '只允许正常姿态装配，不能把处于另一分支的夹指当成正常起点。',
                  '模型行程检查不限制实物手拉或固件原始servo命令；必须校准实物开端，不能持续顶住限位。']}
    path=Path(__file__).resolve().parents[3]/'docs/lego/v3/open_stop_checks.json'
    path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='接触记录'},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
