"""承重传力计算：刚体闭环、公共接头灵敏度、静力平衡和接触约束。

不从名义几何推断塑料刚度、孔隙、轴套保持力或实物下沉量。
"""
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import model as m

ROOT=Path(__file__).resolve().parents[3]


def cross2(a,b):
    return float(a[0]*b[1]-a[1]*b[0])


def wheel_from_crosshead(c,side):
    """独立求解单个夹指；用于检查不再被固定高度假设隐藏的运动。"""
    p=np.array([m.PIVOT_X,side*m.JAW_Y],float)
    d=p-c
    radius=np.linalg.norm(d)
    q=(radius**2+m.JAW_A**2-m.LINK_L**2)/(2*m.JAW_A*radius)
    angle=math.atan2(d[1],d[0])-side*math.acos(q)
    direction=np.array([math.cos(angle),math.sin(angle)])
    joint=p-m.JAW_A*direction
    wheel=p+m.JAW_REACH*direction
    return p,joint,wheel,angle


def wheel_jacobian(c,side):
    p,joint,wheel,angle=wheel_from_crosshead(c,side)
    derivative_joint=m.JAW_A*np.array([math.sin(angle),-math.cos(angle)])
    derivative_wheel=m.JAW_REACH*np.array([-math.sin(angle),math.cos(angle)])
    e=joint-c
    return np.outer(derivative_wheel,e)/(e@derivative_joint)


def crosshead_spatial_balance(c, ends, guide_directions, drive_direction, input_loads, stroke):
    """横梁、公共轴、活动轴组合体的空间平衡算例。

    摆杆和驱动薄梁仅传轴向力，横梁各自满足Mz平衡；轴孔弯矩、
    轴向接触力及弹性分载均省略，故结果不是实物反力的唯一预测。
    力的轴向作用面从正式模型读取，输入薄梁±25、摆杆±45、驱动±15 LDU。
    """
    parts=m.module(stroke,steps=False)
    def wrench(point, force):
        return np.r_[force,np.cross((point-np.r_[c,0.])*.4,force)]
    input_wrench=np.zeros(6)
    for side,force in input_loads:
        z=next(p.pos[2] for p in parts if p.note=='输入薄连杆' and p.pos[2]*side>0)
        input_wrench+=wrench(np.r_[c,z],np.r_[force,0.])
    columns=[];labels=[];local_moments=[]
    for side in (-1,1):
        z=next(p.pos[2] for p in parts if p.note=='Watt连杆' and p.pos[2]*side>0)
        for k,(end,direction) in enumerate(zip(ends,guide_directions)):
            columns.append(wrench(np.r_[end,z],np.r_[direction,0.]))
            labels.append((side,k))
            local_moments.append((side,cross2(end-c,direction)*.4))
    for side in (-1,1):
        z=next(p.pos[2] for p in parts if p.note=='推杆铰接薄梁' and p.pos[2]*side>0)
        columns.append(wrench(np.r_[c,z],np.r_[drive_direction,0.]))
        labels.append((side,2));local_moments.append((side,0.))
    w=np.array(columns).T
    # FX,FY,MX,MY，加两根横梁各自的MZ平衡；FZ恒为零，总MZ随之平衡。
    matrix=np.vstack([w[[0,1,3,4]],
                      [[moment if side==target else 0. for side,moment in local_moments]
                       for target in (-1,1)]])
    forces=np.linalg.solve(matrix,np.r_[-input_wrench[[0,1,3,4]],0.,0.])
    residual=w@forces+input_wrench
    assert np.linalg.norm(residual)<1e-8
    guide_forces={};drive_forces={}
    for side,name in ((-1,'负Z'),(1,'正Z')):
        guide_forces[name]=[float(force) for force,label in zip(forces,labels) if label[0]==side and label[1]<2]
        drive_forces[name]=float(next(force for force,label in zip(forces,labels) if label==(side,2)))
    return {'假设':'摆杆和驱动薄梁为二力杆；分别平衡两根横梁Mz。省略孔轴弯矩与轴向接触力，实物弹性分载可能不同。',
            '输入杆偏心力矩_Nmm':input_wrench[3:].tolist(),
            '各侧前后摆杆轴力_N':guide_forces,'各侧驱动薄梁轴力_N':drive_forces,
            '六分量平衡残差_Fxyz_N_Mxyz_Nmm':residual.tolist(),
            '力平衡残差_N':float(np.linalg.norm(residual[:3])),
            '力矩平衡残差_Nmm':float(np.linalg.norm(residual[3:]))}


def static_case(weight_N,preload_N=0.,stroke=0.):
    c,theta=m.crosshead_pose(stroke);c=c[:2]
    d=np.array([m.DRIVE_CLOSED_X-stroke,0.])
    u=m.WATT_HALF_SPAN*np.array([math.cos(theta),math.sin(theta)])
    ends=(c-u,c+u)
    guide_directions=[(a-g[:2])/m.WATT_GUIDE_L for a,g in zip(ends,m.WATT_ROOTS)]
    drive_direction=(c-d)/m.DRIVE_LINK_L
    q=np.zeros(2);root_forces=[];jaws=[];input_loads=[]
    for side in (-1,1):
        wheel_force=np.array([0.,-preload_N if side<0 else preload_N+weight_N])
        p,joint,wheel,angle=wheel_from_crosshead(c,side)
        toward_c=(c-joint)/m.LINK_L
        tension=-cross2(wheel-p,wheel_force)/cross2(joint-p,toward_c)
        input_force=tension*toward_c
        frame_force=wheel_force+input_force
        root_forces.append((p,frame_force))
        q-=input_force
        input_loads.append((side,-input_force))
        jaws.append({'夹指':'上' if side<0 else '下','轮端力_N':wheel_force.tolist(),
                     '输入杆拉力_N':tension,'输入杆轴力幅值_N':abs(tension),
                     '根轴传给侧架的力_N':frame_force.tolist()})
    matrix=np.array([[guide_directions[0][0],guide_directions[1][0],drive_direction[0]],
                     [guide_directions[0][1],guide_directions[1][1],drive_direction[1]],
                     [cross2(ends[0]-c,guide_directions[0])/m.WATT_HALF_SPAN,
                      cross2(ends[1]-c,guide_directions[1])/m.WATT_HALF_SPAN,0.]])
    forces=np.linalg.solve(matrix,np.array([-q[0],-q[1],0.]))
    frame_forces=root_forces+[(g[:2],-force*direction) for g,force,direction in zip(m.WATT_ROOTS,forces[:2],guide_directions)]
    frame_forces.append((d,-forces[2]*drive_direction))
    total_force=sum((f for _,f in frame_forces),np.zeros(2))
    total_moment=sum(cross2(p-m.TT_C[:2],f)*.4 for p,f in frame_forces)
    expected_moment=sum(cross2(wheel_from_crosshead(c,side)[2]-m.TT_C[:2],
                               np.array(row['轮端力_N']))*.4 for side,row in zip((-1,1),jaws))
    virtual_work=sum((wheel_jacobian(c,side).T@np.array(row['轮端力_N']) for side,row in zip((-1,1),jaws)),np.zeros(2))
    assert np.linalg.norm(virtual_work-q)<1e-9
    assert np.linalg.norm(total_force-[0.,weight_N])<1e-9
    assert abs(total_moment-expected_moment)<1e-8
    spatial=crosshead_spatial_balance(c,ends,guide_directions,drive_direction,input_loads,stroke)
    # 不能用驱动薄梁的合力替代完整载荷：正负Z两片轴力不同，会传入绕Y的弯矩。
    # 两片梁是二力杆，D端受力分别与C端相反；孔轴弯矩等仍沿用算例的省略假设。
    rod_force=np.zeros(3);rod_moment=np.zeros(3)
    parts=m.module(stroke,steps=False)
    for side,label in ((-1,'负Z'),(1,'正Z')):
        z=next(p.pos[2] for p in parts if p.note=='推杆铰接薄梁' and p.pos[2]*side>0)*.4
        force=-spatial['各侧驱动薄梁轴力_N'][label]*np.r_[drive_direction,0.]
        rod_force+=force
        rod_moment+=np.cross([0.,0.,z],force)
    return {'单臂分担重量_N':weight_N,'每个上接触预载_N':preload_N,
            '夹指':jaws,'输入杆传给公共接头的力_N':q.tolist(),
            '两侧合计的前后导向杆轴力_N':forces[:2].tolist(),
            '公共接头组合体空间平衡':spatial,
            '推杆前接头载荷':{'合力_xyz_N':rod_force.tolist(),'合矩_xyz_Nmm':rod_moment.tolist(),
                '绕推杆轴线的扭矩_Nmm':float(rod_moment[0]),
                '横向弯矩幅值_Nmm':float(np.linalg.norm(rod_moment[1:])),
                '假设':'由同一空间二力杆算例的两侧D端反力合成；合力很小不代表合矩为零。'},
            '符号':'导向杆正值为压缩，负值为拉伸；两侧分配须计输入杆轴向偏心。',
            '铰接驱动轴力_N':float(forces[2]),
            '推杆铰接头竖向反力幅值_N':float(abs(forces[2]*drive_direction[1])),
            '转盘附加俯仰矩_Nm':float(total_moment/1000),
            '力平衡残差_N':float(np.linalg.norm(total_force-[0.,weight_N])),
            '力矩平衡残差_Nmm':float(abs(total_moment-expected_moment))}


def guide_constraints():
    rows=[]
    for s in np.linspace(0,m.OPEN_S,81):
        c,theta=m.crosshead_pose(float(s))
        u=m.WATT_HALF_SPAN*np.array([math.cos(theta),math.sin(theta),0.])
        ends=(c-u,c+u)
        d=np.array([m.DRIVE_CLOSED_X-s,0.,0.])
        closure=[abs(np.linalg.norm(a-g)-m.WATT_GUIDE_L) for a,g in zip(ends,m.WATT_ROOTS)]
        closure.append(abs(np.linalg.norm(c-d)-m.DRIVE_LINK_L))
        jac=[]
        for a,g in zip(ends,m.WATT_ROOTS):
            direction=(a-g)[:2]/m.WATT_GUIDE_L
            arm=(a-c)[:2]
            jac.append([*direction,cross2(arm,direction)/m.WATT_HALF_SPAN])
        jac.append([*((c-d)[:2]/m.DRIVE_LINK_L),0.])
        sv=np.linalg.svd(jac,compute_uv=False)
        rows.append({'推杆后退_mm':float(s*.4),'公共轴高度_mm':float(c[1]*.4),
                     '杆长闭环最大残差_mm':float(max(closure)*.4),
                     '约束雅可比最小奇异值':float(sv.min()),'约束条件数':float(sv.max()/sv.min())})
    return {'状态数':len(rows),'最大闭环残差_mm':max(r['杆长闭环最大残差_mm'] for r in rows),
            '最小奇异值':min(r['约束雅可比最小奇异值'] for r in rows),
            '最坏条件数':max(r['约束条件数'] for r in rows),
            '最大公共轴横移_mm':max(abs(r['公共轴高度_mm']) for r in rows),
            '含义':'转角按横梁半长缩放。推杆位置固定时，三条独立约束限制公共轴平面内位姿；不等同于无弹性变形。',
            '记录':rows}


def contact_rank(arms):
    """每个自由滚轮仅计法向及轮轴方向摩擦，不虚构沿滚动方向的锁止力。"""
    columns=[]
    parts=m.build(with_cube=False)
    for wheel in (p for p in parts if p.name=='42610.dat' and p.arm in arms):
        normal=np.array([0.,1. if wheel.pos[1]<0 else -1.,0.])
        contact=wheel.pos+normal*m.TYRE_RADIUS
        lateral=wheel.rot[:,2]
        for force in (normal,lateral):
            columns.append(np.r_[force,np.cross(contact,force)/m.CUBE_HALF])
    sv=np.linalg.svd(np.array(columns).T,compute_uv=False)
    return {'臂':list(arms),'秩':int(np.count_nonzero(sv>1e-8)),'奇异值':sv.tolist()}


def side_frame_gear_clearance():
    """固定侧架几何对齿轮外轴套的连续360°下界，不以离散角度代替整圈。"""
    import check
    import ldraw
    from mechanical_audit import clip_x
    parts=m.module(0,steps=False)
    keeper=next(p for p in parts if p.note=='齿轮外限位')
    blo,bhi=check._obb(keeper)
    keeper_radius=max(np.linalg.norm(v[1:]-keeper.pos[1:]) for v in (ldraw.geometry(keeper.name)[0]@keeper.rot.T+keeper.pos).reshape(-1,3))
    radial_center=np.linalg.norm(keeper.pos[1:])
    names={'侧架长梁','前角梁','转盘后横梁','后短连接梁','转盘轴销','侧架后连接轴','侧架后连接隔套'}
    rows=[]
    for p in parts:
        if p.note not in names:continue
        lo,hi=check._obb(p)
        axial=max(float(blo[0]-hi[0]),float(lo[0]-bhi[0]),0.)
        if axial>0:
            gap=axial;method='沿转轴方向分离'
        else:
            triangles=ldraw.geometry(p.name)[0]@p.rot.T+p.pos
            clipped=clip_x(triangles,blo[0],bhi[0])
            assert len(clipped)
            radius=np.linalg.norm(clipped[:,:,1:],axis=2).max()
            gap=float(radial_center-keeper_radius-radius);method='完整回转径向包络分离'
        assert gap>0,(p.note,gap)
        rows.append({'零件':p.name,'用途':p.note,'连续整圈下界_mm':gap*.4,'依据':method})
    return {'连续整圈下界_mm':min(r['连续整圈下界_mm'] for r in rows),'记录':rows,
            '范围':'侧架相关固定形状随机械头整圈回转，轴套也取完整自转包络；不含塑料变形。'}


def main():
    c,_=m.crosshead_pose(0.);c=c[:2]
    jac={str(side):wheel_jacobian(c,side).tolist() for side in (-1,1)}
    for side in (-1,1):
        numeric=np.column_stack([(wheel_from_crosshead(c+np.eye(2)[i]*1e-4,side)[2]-
                                  wheel_from_crosshead(c-np.eye(2)[i]*1e-4,side)[2])/2e-4 for i in (0,1)])
        assert np.allclose(numeric,jac[str(side)],atol=1e-7)
    cases={str(n):static_case(.1*9.80665/n) for n in (1,2,4)}
    constraints=guide_constraints()
    rank_two=contact_rank(('L','R'));rank_four=contact_rank(m.ARMS)
    assert rank_two['秩']==5 and rank_four['秩']==6
    assert constraints['最大闭环残差_mm']<1e-8 and constraints['最小奇异值']>.2
    report={'model.py_SHA256':hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest(),
            '状态':'刚体约束和静力平衡通过；实物承重尚未验收','设计质量_g':100.,
            '公共轴到轮端的位移雅可比':jac,'约束检查':constraints,
            '侧架对齿轮外轴套的连续回转':side_frame_gear_clearance(),
            '重量附加载荷_有效分担臂数':cases,'示例_每轮1N预载_两臂分担':static_case(.1*9.80665/2,1.),
            '接触约束':{'两臂':rank_two,'四臂':rank_four,
                         '限制':'两臂模式沿共同夹持轴方向依赖未测滚阻与交接定位；矩阵秩不证明单向接触和摩擦锥内的力封闭。'},
            '未测项目':['转盘与侧架俯仰刚度','各铰链间隙及换向回差','轴套和轮轴轴向保持','轮胎预压、摩擦和滚阻','动态交接与翻转漂移']}
    out=ROOT/'docs/lego/v3/load_path_checks.json'
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('闭环最大残差_mm',constraints['最大闭环残差_mm'])
    print('约束最小奇异值',constraints['最小奇异值'])
    print('两臂100g静力',cases['2'])
    print('两臂/四臂接触秩',rank_two['秩'],rank_four['秩'])
    print(out)


if __name__=='__main__':main()
