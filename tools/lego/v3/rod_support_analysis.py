"""记录真实推杆支承尺寸及理想梁的相对柔度；不预测乐高装配的实物位移。"""
import hashlib
import json
from pathlib import Path
import numpy as np
import model as m
import run_check  # noqa: F401
import check
from load_path_analysis import static_case


def analyze():
    rows=[]
    for s in np.linspace(0,m.OPEN_S,81):
        parts=m.module(float(s),steps=False)
        rods=[p for p in parts if p.note in ('推杆短轴','推杆长轴')]
        ends=[p.pos[0]+e for p in rods for e in check.connector_bounds(p.name)]
        rear=next(p for p in rods if p.note=='推杆长轴')
        lo,hi=check.connector_bounds(rear.name)
        bearing_edges=[(x+m.MODULE_DX-10,x+m.MODULE_DX+10) for x in m.ROD_BEARING_X]
        margins=[min(a-rear.pos[0]-lo,rear.pos[0]+hi-b) for a,b in bearing_edges]
        D=next(p for p in parts if p.note=='推杆铰接头').pos[0]
        connector=next(p for p in parts if p.note=='推杆连接器')
        # 推杆沿X平移并绕X回转，连接器最靠后的X面在回转中保持不变。
        connector_back=check._obb(connector)[0][0]
        rows.append({'行程比例':float(s/m.OPEN_S),'总名义长度_mm':float((max(ends)-min(ends))*.4),
                     '前轴承中心至铰点_mm':float((D-max(m.ROD_BEARING_X)-m.MODULE_DX)*.4),
                     '后轴完整覆盖全部导向孔的最小端部余量_mm':float(min(margins)*.4),
                     '连接器后面至前轴承前面的轴向间隙_mm':float((connector_back-max(b for a,b in bearing_edges))*.4)})
    closed=rows[0]
    b=closed['前轴承中心至铰点_mm'];a=float(np.ptp(m.ROD_BEARING_X)*.4)
    old_b=63.822620791223564;old_a=48.
    force_ratio=b*b*(a+b)/(old_b*old_b*(old_a+old_b))
    moment_ratio=(b*b/2+a*b/3)/(old_b*old_b/2+old_a*old_b/3)
    return {'model.py_SHA256':hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest(),
            '参考版本':{'提交':'35db5e5','总名义长度_mm':120.,'夹紧悬伸_mm':old_b,'轴承中心距_mm':old_a},
            '当前':{'总名义长度_mm':closed['总名义长度_mm'],'夹紧悬伸_mm':b,'轴承中心距_mm':a,
                    '全行程最小孔外余量_mm':min(r['后轴完整覆盖全部导向孔的最小端部余量_mm'] for r in rows),
                    '连接器到前轴承连续轴向间隙下界_mm':min(r['连接器后面至前轴承前面的轴向间隙_mm'] for r in rows)},
            '100g两臂均分_夹紧_仅重量增量':static_case(.1*9.80665/2)['推杆前接头载荷'],
            '理想梁相对柔度':{
                '假设':'均匀Euler–Bernoulli梁、两个理想简支、相同EI和载荷；a为支点间距，b为前悬伸。忽略连接器、塑料蠕变、孔隙和支座变形。',
                '端部横向力柔度公式':'b²(a+b)/(3EI)',
                '端部弯矩导致的位移柔度公式':'(b²/2+ab/3)/EI',
                '端部横向力_新旧柔度比':force_ratio,'端部弯矩_新旧柔度比':moment_ratio,
                '限制':'这些比值只说明缩短的方向性收益，不能作为整机刚度提升或实际下沉量的预测。'},
            '全行程记录':rows}


if __name__=='__main__':
    data=analyze()
    target=Path(__file__).resolve().parents[3]/'docs/lego/v3/rod_support_checks.json'
    target.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in data.items() if k!='全行程记录'},ensure_ascii=False,indent=2))
