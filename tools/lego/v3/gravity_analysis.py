"""从当前几何重算100g载荷和小位移敏感度；实测状态保持未执行。"""
import hashlib
import json
import math
from pathlib import Path
import model as m
from load_path_analysis import static_case,wheel_from_crosshead,wheel_jacobian


def main():
    c,_=m.crosshead_pose(0.);c=c[:2]
    pivot,joint,wheel,beta=wheel_from_crosshead(c,-1)
    phi=math.atan2(abs(joint[1]-c[1]),joint[0]-c[0])
    root_lever=(wheel[0]-pivot[0])*.4
    turntable_lever=(wheel[0]-m.TT_C[0])*.4
    weight=.1*9.80665
    cases={str(n):static_case(weight/n) for n in (1,2,4)}
    jac=wheel_jacobian(c,-1)
    rows=[]
    for n in (1,2,4):
        rows.append({'理想均分下轮数':n,'每轮附加载荷_N':weight/n,
                     '单根输入杆轴向力增量幅值_N':cases[str(n)]['夹指'][1]['输入杆轴力幅值_N'],
                     '根轴力矩_Nm':weight/n*root_lever/1000,
                     '转盘平面力矩_Nm':weight/n*turntable_lever/1000})
    result={'性质':'静力与小位移敏感度；不是实物下沉预测','设计质量_g':100,'重力_N':weight,
            'model.py_SHA256':hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest(),
            '主臂角_deg':abs(math.degrees(beta)),'输入杆方向角_deg':math.degrees(phi),
            '根轴竖直载荷力臂_mm':root_lever,'转盘到轮轴纵向距离_mm':turntable_lever,
            '输入杆轴向力倍率':cases['1']['夹指'][1]['输入杆轴力幅值_N']/weight,
            '轮端外移对推杆退让倍率':abs(float(jac[1,0])),
            '载荷分配':rows,
            '转角敏感度':[{'角度_deg':deg,'主臂摆动竖直轮端位移_mm':root_lever*math.radians(deg),
                            '转盘俯仰悬伸竖直位移_mm':turntable_lever*math.radians(deg)} for deg in (.1,.2,1)],
            '验证':'平面主臂力矩、虚功及公共接头组合体六分量空间平衡通过；空间反力基于二力杆假设。另保留推杆前接头合矩。',
            '实测状态':'未执行',
            '结构说明':'2L＋11L推杆共104mm，舵机和导向框前移16mm。前接头仍受两片驱动薄梁的不平衡弯矩；实际刚度与保持未实测。',
            '公共接头竖移对轮端同向位移倍率':float(jac[1,1]),'承重路径计算':cases}
    target=Path(__file__).resolve().parents[3]/'docs/lego/v3/gravity_calculations.json'
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(target)


if __name__=='__main__':main()
