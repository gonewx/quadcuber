"""候选闭环及空间静力平衡；不以刚体计算代替实物刚度。"""
from watt_candidate import *
import load_path_analysis as old
m.module=module

def analyze(stroke,weight=.4903325,preload=1.):
    c,t=m.crosshead_pose(stroke);u=40*np.array([math.cos(t),math.sin(t),0.]);ends=(c-u,c+u);d=np.array([m.DRIVE_CLOSED_X-stroke,0,0])
    dirs=[(a-g)/80 for a,g in zip(ends,m.WATT_ROOTS)];dd=(ends[0]-d)/20
    def cross(a,b):return float(np.cross(np.r_[a[:2],0.],np.r_[b[:2],0.])[2])
    jac=np.array([[*e[:2],cross(a-c,e)/40] for a,e in zip(ends,dirs)]+[[*dd[:2],cross(ends[0]-c,dd)/40]])
    singular=np.linalg.svd(jac,compute_uv=False)
    wrench=np.zeros(6);jaw_frame=[];loads=[]
    ps=module(stroke,steps=False)
    def w(point,force):return np.r_[force,np.cross((point-c)*.4,force)]
    for side in (-1,1):
        p,j,wh,angle=old.wheel_from_crosshead(c[:2],side);f=np.array([0.,-preload if side<0 else preload+weight])
        towards=(c[:2]-j)/80;T=-cross(wh-p,f)/cross(j-p,towards);fi=T*towards
        z=next(p.pos[2] for p in ps if p.note=='输入薄连杆' and p.pos[2]*side>0)
        wrench+=w(c+[0,0,z],np.r_[-fi,0.]);jaw_frame.append((p,f+fi));loads.append((side,wh,f))
    columns=[];moments=[];labels=[]
    for side in (-1,1):
        for k,(a,di) in enumerate(zip(ends,dirs)):
            columns.append(w(a+[0,0,40*side],di));moments.append((side,cross(a-c,di)*.4));labels.append((side,k))
        columns.append(w(ends[0]+[0,0,15*side],dd));moments.append((side,cross(ends[0]-c,dd)*.4));labels.append((side,2))
    W=np.array(columns).T
    matrix=np.vstack([W[[0,1,3,4]],[[value if side==target else 0 for side,value in moments] for target in (-1,1)]])
    forces=np.linalg.solve(matrix,np.r_[-wrench[[0,1,3,4]],0,0]);residual=W@forces+wrench
    frame=jaw_frame.copy();rod=np.zeros(3);rod_moment=np.zeros(3)
    for force,(side,k) in zip(forces,labels):
        if k<2:frame.append((m.WATT_ROOTS[k,:2],-force*dirs[k][:2]))
        else:
            frame.append((d[:2],-force*dd[:2]));rod-=force*dd;rod_moment+=np.cross([0.,0.,15*side*.4],-force*dd)
    total=sum((f for _,f in frame),np.zeros(2));moment=sum(cross(p-m.TT_C[:2],f)*.4 for p,f in frame)
    expected=sum(cross(wh-m.TT_C[:2],f)*.4 for side,wh,f in loads)
    assert np.linalg.norm(total-[0.,weight])<1e-8 and abs(moment-expected)<1e-8
    assert np.linalg.norm(residual)<1e-8
    closure=max([abs(np.linalg.norm(a-g)-80) for a,g in zip(ends,m.WATT_ROOTS)]+[abs(np.linalg.norm(ends[0]-d)-20)])*.4
    return {'开度':float(stroke/m.OPEN_S),'预载_N':preload,'闭环残差_mm':closure,'约束最小奇异值':float(singular.min()),'条件数':float(singular.max()/singular.min()),'空间平衡残差':float(np.linalg.norm(residual)), '最大杆轴力_N':float(max(abs(forces))),'各杆轴力_N':forces.tolist(),'推杆合力_N':rod.tolist(),'推杆合矩_Nmm':rod_moment.tolist(),'推杆扭矩_Nmm':float(rod_moment[0]),'公共轴偏心矩_Nmm':wrench[3:].tolist()}
rows=[analyze(float(s),preload=pre) for s in np.linspace(0,m.OPEN_S,81) for pre in (0.,1.,2.)]
result={'假设':'单臂分担100g魔方的一半重量；刚体、无孔隙，导杆及驱动杆作为二力杆。不能据此保证塑料挠度、摩擦或轴套保持力。','样本数':len(rows),'最小约束奇异值':min(r['约束最小奇异值'] for r in rows),'最大闭环残差_mm':max(r['闭环残差_mm'] for r in rows),'最大空间平衡残差':max(r['空间平衡残差'] for r in rows),'最大杆轴力_N':max(r['最大杆轴力_N'] for r in rows),'闭合_每接触1N预载':rows[1],'全开_每接触1N预载':rows[-2]}
Path(__file__).with_name('watt-mechanics.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
