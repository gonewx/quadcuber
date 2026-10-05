"""直线滑座概念的夹紧端平面静力；不包含材料刚度、孔隙或滑动摩擦。"""
import math,json
from pathlib import Path
beta=math.asin(6.7/100)
a,reach,L=16.,40.,32.
jy=32-a*math.sin(beta)
dx=math.sqrt(L*L-jy*jy)
W=.100*9.80665/2
rows=[]
for preload in (0.,1.,2.):
    slider=[0.,0.];root=[0.,0.];jaws=[]
    for s in (-1,1):
        rj=(-a*math.cos(beta),-s*a*math.sin(beta));rt=(reach*math.cos(beta),s*reach*math.sin(beta))
        d=(-dx/L,-s*jy/L)
        fy=s*preload-W/2
        det=rj[0]*d[1]-rj[1]*d[0]
        t=-rt[0]*fy/det
        fj=(t*d[0],t*d[1]);fj_root=(-fj[0],-fy-fj[1]);fj_slider=(-fj[0],-fj[1])
        assert abs(rt[0]*fy+rj[0]*fj[1]-rj[1]*fj[0])<1e-12
        for k in (0,1):slider[k]+=fj_slider[k];root[k]+=fj_root[k]
        jaws.append({'侧':s,'接触Fy_N':fy,'杆轴力_N':t,'根轴对夹指反力_N':fj_root})
    # slider 为连杆对滑座的作用力，root 为框架对夹指的作用力。
    assert abs(root[1]-slider[1]-W)<1e-12
    rows.append({'每侧夹紧预载_N':preload,'连杆对滑座力_N':slider,'根轴对夹指总反力_N':root,'夹指':jaws})
lever=(124-52+reach*math.cos(beta))/1000
result={'状态':'概念计算，仅夹紧端平面静力；并非新实体模型通过验收',
'假设':['100g魔方由两臂均分，每臂上下接触均分该臂重量；不验证接触摩擦是否足够','理想铰链、刚体、无间隙、导轨无摩擦，活动件自重暂不计','0N预载仅用于分离重力增量，不表示无夹紧力即可抓住魔方','仅头部竖直时的二维分析；90度时的横向/轴向约束需另做空间模型'],
'参考尺寸_mm':{'夹指前力臂':reach,'后力臂':a,'输入杆孔距':L,'两根轴高度间距':64},
'每臂魔方重量_N':W,'夹紧端滑座横向载荷_N':abs(rows[0]['连杆对滑座力_N'][1]),'夹紧端魔方引起的转盘弯矩_Nm':W*lever,
'头部自重敏感性':{'每100g头部质量_质心距转盘60mm_附加弯矩_Nm':.1*9.80665*.060,'说明':'敏感性示例，不是假定或实测头部质量'},
'算例':rows}
p=Path(__file__).with_name('concept-load.json');p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
