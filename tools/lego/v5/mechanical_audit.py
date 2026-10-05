"""连续回转包络与刚度估算；发现干涉时退出 1，实物项目始终保留待测。

不使用 check.Solid 的体素侵蚀。三角形对有限圆柱的距离下界用于
证明分离；推杆直段的完整回转包络为圆柱，可给出实际相碰姿态。
运行：python tools/lego/v5/mechanical_audit.py
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

import model
import ldraw

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'docs/lego/v5/mechanical_audit.json'


def world(p):
    return ldraw.geometry(p.name)[0] @ p.rot.T + p.pos


def projected_minimum(tris):
    """各三角形在 YZ 平面投影到原点的最近点，包含退化线段。"""
    p = tris[:, :, 1:]
    q = np.roll(p, -1, axis=1)
    d = q - p
    den = np.sum(d*d, axis=2)
    t = np.clip(-np.sum(p*d, axis=2) / np.maximum(den, 1e-30), 0, 1)
    points = p + t[:, :, None] * d
    radius = np.linalg.norm(points, axis=2)
    edge = radius.argmin(axis=1)
    idx = np.arange(len(tris))
    closest = points[idx, edge].copy()
    # 投影面积为零时不把共线三角形误判成包含原点。
    cross = p[:, :, 0]*q[:, :, 1] - p[:, :, 1]*q[:, :, 0]
    area = np.abs(cross.sum(axis=1))
    inside = (area > 1e-12) & ((cross.min(axis=1) >= 0) | (cross.max(axis=1) <= 0))
    closest[inside] = 0
    return np.linalg.norm(closest, axis=1), closest


def cylinder_bounds(tris, xlo, xhi, radius):
    """表面到实心有限圆柱的距离下界，单位 LDU；0 只代表不能证明分离。"""
    rmin, _ = projected_minimum(tris)
    xmin, xmax = tris[:, :, 0].min(axis=1), tris[:, :, 0].max(axis=1)
    dx = np.maximum(np.maximum(xlo-xmax, xmin-xhi), 0)
    dr = np.maximum(rmin-radius, 0)
    lower = np.hypot(dx, dr)
    vertex_dx = np.maximum(np.maximum(xlo-tris[:,:,0], tris[:,:,0]-xhi), 0)
    vertex_dr = np.maximum(np.linalg.norm(tris[:,:,1:],axis=2)-radius, 0)
    upper = np.hypot(vertex_dx, vertex_dr).min(axis=1)
    return lower, upper


def cylinder_lower_bound(tris, xlo, xhi, radius):
    return float(cylinder_bounds(tris, xlo, xhi, radius)[0].min())


def refined_cylinder_distance(tris, labels, xlo, xhi, radius, tolerance=.025):
    """细分候选三角形直至上下界相差≤0.01mm，不丢弃潜在更近的表面。"""
    upper = float('inf')
    upper_label = ''
    for _ in range(24):
        lower, vertex_upper = cylinder_bounds(tris, xlo, xhi, radius)
        u = int(vertex_upper.argmin())
        if vertex_upper[u] < upper:
            upper, upper_label = float(vertex_upper[u]), str(labels[u])
        k = int(lower.argmin())
        if upper-lower[k] <= tolerance:
            # 上一轮下界==上界的三角形可能已被裁掉；保留它的已知最优值。
            if lower[k] >= upper:
                return upper, upper, upper_label
            return float(lower[k]), upper, str(labels[k])
        keep = lower < upper
        tris, labels = tris[keep], labels[keep]
        a,b,c = tris[:,0], tris[:,1], tris[:,2]
        ab,bc,ca = (a+b)/2, (b+c)/2, (c+a)/2
        tris = np.concatenate([np.stack(v,axis=1) for v in ((a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca))])
        labels = np.tile(labels,4)
        if len(tris)>1000000:
            raise RuntimeError('连续包络细分超过预算，不能宣称距离已收敛')
    raise RuntimeError('连续包络距离未收敛')


def clip_x(tris, lo, hi):
    """将网格三角形裁到轴向范围，再三角化，避免远处凸出部误报。"""
    result = []
    for tri in tris:
        if tri[:, 0].max() < lo or tri[:, 0].min() > hi:
            continue
        poly = list(tri)
        for bound, sign in ((lo, 1), (hi, -1)):
            new = []
            for a, b in zip(poly, poly[1:] + poly[:1]):
                ain, bin_ = sign*(a[0]-bound) >= 0, sign*(b[0]-bound) >= 0
                if ain:
                    new.append(a)
                if ain != bin_:
                    new.append(a + (b-a)*(bound-a[0])/(b[0]-a[0]))
            poly = new
            if not poly:
                break
        result.extend([poly[0], poly[i], poly[i+1]] for i in range(1, len(poly)-1))
    return np.array(result).reshape(-1, 3, 3)


def self_test():
    t = np.array([[[0, 3, -1], [0, 3, 1], [0, 5, 0]]], float)
    assert np.allclose(projected_minimum(t)[0], [3])  # 最近点在边内，顶点采样会漏。
    assert abs(cylinder_lower_bound(t, -1, 1, 2)-1) < 1e-10
    t[:, :, 0] = 5
    assert abs(cylinder_lower_bound(t, -1, 1, 2)-math.sqrt(17)) < 1e-10
    t = np.array([[[0, -1, -1], [0, 1, -1], [0, 0, 1]]], float)
    assert projected_minimum(t)[0][0] == 0
    t = np.array([[[0, 3, 0], [0, 4, 0], [0, 5, 0]]], float)
    assert projected_minimum(t)[0][0] == 3  # 退化投影不包含原点。
    clipped = clip_x(np.array([[[-2, 2, 0], [2, 2, 0], [0, 4, 0]]], float), -1, 1)
    assert clipped[:, :, 0].min() == -1 and clipped[:, :, 0].max() == 1
    # 斜三角形的 X 和半径极值位于不同位置，粗下界为0，细分后必须为正。
    t = np.array([[[0, 4, 0], [4, 0, 0], [4, 0, 1]]],float)
    lo,hi,_ = refined_cylinder_distance(t,np.array(['test']),-1,1,1)
    assert math.sqrt(2)-.025 <= lo <= math.sqrt(2) <= hi+1e-10
    # 精确最优面可在细分前被裁掉，剩余候选收敛后不能反而抬高全局下界。
    t = np.array([[[0,3,0],[0,3,0],[0,3,0]],[[0,10,0],[10,0,0],[10,0,1]]],float)
    lo,hi,label = refined_cylinder_distance(t,np.array(['exact','loose']),-1,1,1)
    assert lo == hi == 2 and label == 'exact'


def ROD_HALF(rod):
    return 157.5 if rod.name == '50451.dat' else 117.5


def rod_check():
    """检查曲柄轴与内限位的整个圆周回转包络；行程取样并加入曲柄极值。"""
    from scipy.optimize import brentq
    th0 = model.servo_theta_for(0)[0]
    th1 = model.servo_theta_for(model.OPEN_S)[0]
    strokes = np.linspace(0, model.OPEN_S, 81).tolist()
    for theta in (-math.pi/2, 0, math.pi/2):
        if min(th0, th1) < theta < max(th0, th1):
            strokes.append(brentq(lambda s:model.servo_theta_for(s)[0]-theta,0,model.OPEN_S))
    rows, worst = [], None
    for stroke in sorted(set(strokes)):
        parts = model.module(stroke, steps=False)
        rod = next(p for p in parts if p.name in ('3708.dat','50451.dat'))
        targets = [p for p in parts if p.note in ('曲柄端轴','曲柄端内限位')]
        if not targets:  # 也能复现旧单侧版的失败。
            targets = [next(p for p in parts if p.name=='32062.dat' and not p.head)]
        for part in targets:
            tris = world(part)
            # v4 夹紧时曲柄朝后折叠, 可能超出 12 号轴后端; 按无限长推杆保守计算径向余量。
            radii,_ = projected_minimum(tris)
            gap = (float(radii.min())-6)*.4
            vertices = tris.reshape(-1,3)
            witness = vertices[np.linalg.norm(vertices[:,1:],axis=1).argmin()]
            angle = math.degrees(math.atan2(witness[2],witness[1]))
            local = (witness-rod.pos) @ model.rot_x(angle)
            collision = abs(local[0])<ROD_HALF(rod) and 0<local[1]<6 and abs(local[2])<1e-8
            row = {'行程比例':stroke/model.OPEN_S, '零件':part.name, '用途':part.note,
                   '回转包络径向余量_mm':gap, '表面见证顶点_LDU':witness.tolist(),
                   '见证角_deg':angle, '顶点在推杆实体内':bool(collision)}
            rows.append(row)
            if worst is None or gap<worst['回转包络径向余量_mm']:
                worst = row
    return {'状态':'失败' if worst['回转包络径向余量_mm']<0 else '通过',
            '推杆回转半径_mm':2.4, '最差':worst, '行程记录':rows,
            '曲柄角范围_deg':[math.degrees(th0),math.degrees(th1)],
            '连续行程径向保守余量_mm':(min(model.CRANK_C[1]+model.CRANK_R*math.sin(th0),
                                         model.CRANK_C[1]+model.CRANK_R*math.sin(th1))-9.001-6)*.4}


def cube_checks():
    rows = []
    specs = [
        ('松开头回位对完整魔方', model.module(model.OPEN_S, steps=False), lambda p:p.head, -70, 70),
        ('夹紧头拧层对另外两层', model.module(0, steps=False), lambda p:p.head, -70+140/3, 70),
        ('邻臂夹紧竖直对转动单层', model.build({'F':(0,0), 'B':(0,0)}, with_cube=False), lambda p:p.arm in ('F','B'), -70, -70+140/3),
        ('邻臂松开竖直对整块翻转', model.build({'F':(model.OPEN_S,0), 'B':(model.OPEN_S,0)}, with_cube=False), lambda p:p.arm in ('F','B'), -70, 70),
    ]
    for label, parts, select, xlo, xhi in specs:
        triangles, labels = [], []
        for p in parts:
            if not select(p):
                continue
            tri = world(p)
            triangles.append(tri)
            labels.extend([p.name]*len(tri))
        lo,hi,part = refined_cylinder_distance(np.concatenate(triangles),np.array(labels),xlo,xhi,math.hypot(70,70))
        rows.append({'工况': label, '连续360度间隙保守下界_mm': lo*.4,
                     '距离上界_mm':hi*.4, '限制零件':part,
                     '状态':'证明分离' if lo>0 else '需细查'})
    return rows


def fixed_rod_checks():
    """推杆直段对所有本臂固定件；孔内导向接触单独列明，不删除结果。"""
    results = {}
    for s in np.linspace(0, model.OPEN_S, 41):
        parts = model.module(s, steps=False)
        rod = next(p for p in parts if p.name in ('3708.dat','50451.dat'))
        for i,p in enumerate(parts):
            if p.head:
                continue
            tris = world(p)
            if np.any(tris.min((0,1))[1:] > 12) or np.any(tris.max((0,1))[1:] < -12):
                continue
            tris = clip_x(tris, rod.pos[0]-ROD_HALF(rod), rod.pos[0]+ROD_HALF(rod))
            if not len(tris):
                continue
            r,_ = projected_minimum(tris)
            gap = float((r.min()-6)*.4)
            key = f'{i}:{p.name}'
            if key not in results or gap < results[key]['径向余量_mm']:
                results[key] = {'零件':p.name, '实例':i, '径向余量_mm':gap, '行程比例':float(s/model.OPEN_S),
                                '有意配合':p.name in ('64179.dat','6536.dat')}
    return list(results.values())


def rotating_bush_checks():
    """推杆两侧半轴套的完整360°外包圆柱，对固定舵机连杆；81个行程。"""
    rows=[]
    for stroke in np.linspace(0,model.OPEN_S,81):
        parts=model.module(float(stroke),steps=False)
        link=next(p for p in parts if p.note=='舵机连杆')
        tri=world(link)
        for bush in (p for p in parts if p.head and p.name=='32123a.dat' and abs(p.pos[1])+abs(p.pos[2])<1e-8):
            vertices=world(bush).reshape(-1,3)
            radius=float(np.linalg.norm(vertices[:,1:],axis=1).max())
            lo,hi,_=refined_cylinder_distance(tri,np.array([link.name]*len(tri)),
                                            vertices[:,0].min(),vertices[:,0].max(),radius)
            rows.append({'行程比例':float(stroke/model.OPEN_S),'轴套X_LDU':float(bush.pos[0]),
                         '连续回转间隙下界_mm':lo*.4,'上界_mm':hi*.4})
    return {'范围':'81个行程；每个位置覆盖半轴套连续360度回转外包络',
            '最差':min(rows,key=lambda r:r['连续回转间隙下界_mm']), '行程记录':rows}


def stiffness():
    integral = 4*8**3/3 + 16**3/3
    inertia = 7.2*4**3/12
    in_plane = 4*7.2**3/12
    return {'假设':'无孔实心矩形薄梁、理想两点支承；不含销孔间隙、扭转、轮轴和主臂变形。E仅作参数示例。',
            '支点间距_mm':8, '载荷距首支点_mm':24, '面外惯性矩_mm4':inertia,
            '面内惯性矩_mm4':in_plane, '单片支点反力与分配给该片的轮端力之比':[-2,3],
            '法向分载':'夹紧法向N作用在两薄梁中间，理想对称时每片N/2；合成偏心距为0。',
            '轴向分载':'轮轴方向的Ft由轮毂端面推向一侧薄梁，保守按单片承受全Ft；不宣称面外柔度减半。',
            'E敏感性':[{'E_MPa':E,'轴向Ft单片保守柔度_mm每N':integral/(E*inertia),
                       '轴向5N理想挠度_mm':5*integral/(E*inertia),
                       '法向N两片均分理想柔度_mm每N':integral/(2*E*in_plane)} for E in (1000,2000,3000)],
            '两轮均匀分载示例':[{'单臂输出扭矩_Nm':T,'每轮切向力_N':T/(2*.028)} for T in (.05,.1,.2,.5)],
            '实物验证':'未执行，不给出合格结论'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    self_test()
    if args.self_test:
        print('连续包络算法自检通过')
        return 0
    rod = rod_check()
    fixed, cubes = fixed_rod_checks(), cube_checks()
    bushes = rotating_bush_checks()
    failed = rod['状态']=='失败' or any(r['径向余量_mm'] < -1e-8 and not r['有意配合'] for r in fixed)
    unresolved = any(r['状态']=='需细查' for r in cubes) or bushes['最差']['连续回转间隙下界_mm']<=0
    data = {'几何源':'双侧32449支承＋后移舵机＋7孔粗连杆；以文件SHA256为准',
            'model.py_SHA256':hashlib.sha256(Path(model.__file__).read_bytes()).hexdigest(),
            '零件三角网格_SHA256':{name:hashlib.sha256(np.ascontiguousarray(ldraw.geometry(name)[0],dtype='<f8').tobytes()).hexdigest()
                                      for name in sorted({p.name for p in model.build()})},
            '结论':('发现后部回转干涉' if failed else '本脚本未检出后部包络干涉')+'；实物刚度与保持力待测',
            '曲柄轴与推杆':rod, '推杆直段对固定件_41行程位置':fixed,
            '旋转半轴套对舵机连杆':bushes, '魔方连续回转包络':cubes, '薄梁受力估算':stiffness(),
            '范围限制':['魔方工况使用完整表面三角形和连续角度包络；正距离可证明名义网格分离。',
                      '三角网格是名义外形；不包含公差、材料变形、轴窜动及未建模线缆。',
                      '整机所有零件对并未获得连续开合与回转的联合证明；原离散扫描保留为补充。',
                      '圆柱到表面下界不检测一个实体完整包住另一个实体的特殊情况；本报告魔方位于各机械零件外部。']}
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k:v for k,v in data.items() if k not in ('曲柄轴与推杆','旋转半轴套对舵机连杆')},ensure_ascii=False,indent=2))
    print('曲柄轴检查：',json.dumps(rod['最差'],ensure_ascii=False))
    print('结果：',OUT)
    return int(failed or unresolved)


if __name__ == '__main__':
    raise SystemExit(main())
