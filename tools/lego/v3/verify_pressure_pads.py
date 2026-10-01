"""补充检查：上下轮胎压头及各自的真实运动轨迹、固定轴销与双侧轮轴、推杆导向覆盖和魔方本体/相邻两层避让。

表面离散采样只能给出 CAD 筛查结果，不能证明实物公差、轮胎保持力或夹紧力。
"""
import json
import math
from pathlib import Path

import numpy as np
import model
import run_check  # noqa: F401
import check
import four_arm


def cube_clearance(parts, lower, upper):
    best = (float('inf'), '')
    for p in parts:
        if not p.head:
            continue
        lo, hi = check._obb(p)
        if np.linalg.norm(np.maximum(np.maximum(lower - hi, lo - upper), 0)) >= best[0]:
            continue
        points = check.Solid(p.name).samples @ p.rot.T + p.pos
        distance = np.maximum(np.maximum(lower - points, points - upper), 0)
        value = float(np.linalg.norm(distance, axis=1).min())
        if value < best[0]:
            best = (value, p.name)
    return best


def main():
    for stroke in np.linspace(0, model.OPEN_S, 25):
        parts = model.module(stroke, steps=False)
        for sy in (1, -1):
            beta=model.jaw_beta(stroke,sy)
            pivot = np.array([model.PIVOT_X + model.MODULE_DX, sy * model.JAW_Y, 0])
            rotation = model.rot_z(sy * beta)
            front = pivot + rotation @ [model.JAW_REACH, 0, 0]
            beam = min((p for p in parts if p.head and p.color == model.C_JAW and p.name == '32524.dat'), key=lambda p: np.linalg.norm(p.pos - pivot))
            assert np.linalg.norm(beam.pos - pivot) < 1e-6
            assert np.linalg.norm(beam.world([0, 0, -40]) - (pivot + rotation @ [-40, 0, 0])) < 1e-6
            thins = [p for p in parts if p.note == '压头支承薄梁' and np.linalg.norm(p.pos-front)<40]
            assert len(thins) == 2
            assert all(p.name == '32449.dat' for p in thins)
            for reach, note in ((40, '薄梁固定轴'), (60, '薄梁固定挡套销')):
                z = -10 if reach == 60 else 0
                expected = pivot + rotation @ [reach, 0, z]
                assert min(np.linalg.norm(p.pos-expected) for p in parts if p.note == note)<1e-6
            shaft = min((p for p in parts if p.note == '轮毂贯穿轴'), key=lambda p:np.linalg.norm(p.pos-front))
            wheel = min((p for p in parts if p.name == '42610.dat'), key=lambda p:np.linalg.norm(p.pos-front))
            tyre = min((p for p in parts if p.name == '50945_nominal.dat'), key=lambda p:np.linalg.norm(p.pos-front))
            assert np.linalg.norm(wheel.pos-front)<1e-6 and np.linalg.norm(tyre.pos-front)<1e-6
            assert np.allclose(sorted([shaft.world([-20,0,0])[2],shaft.world([20,0,0])[2]]),[-20,20])
            spans = sorted((round(lo),round(hi)) for _,lo,hi in check._pin_layers(shaft,thins+[wheel]))
            assert spans == [(-20,-10),(-10,10),(10,20)]
            # 固定轴、挡套长销均真正贯穿薄—粗—薄叠层。
            for note,expected in (('薄梁固定轴',[(-20,-10),(-10,10),(10,20)]),
                                  ('薄梁固定挡套销',[(-10,0),(0,20),(20,30)])):
                connector=min((p for p in parts if p.note==note),key=lambda p:np.linalg.norm(p.pos-front))
                spans=sorted((round(lo),round(hi)) for _,lo,hi in check._pin_layers(connector,thins+[beam]))
                assert spans==expected,(note,spans)
        servo_link = next(p for p in parts if p.note == '舵机连杆')
        assert servo_link.name == '32524.dat' and servo_link.pos[2] == 20
        crank_axle = next(p for p in parts if p.note == '曲柄端轴')
        assert np.allclose(sorted([crank_axle.world([-20,0,0])[2],crank_axle.world([20,0,0])[2]]),[0,40])
        assert any(p.note == '曲柄端内限位' and np.linalg.norm(p.pos-(crank_axle.pos+[0,0,-15]))<1e-6 for p in parts)
        # 两个导向轴承都必须完整落在后段 12L 推杆之内，不能只看无限长轴线。
        rod = next(p for p in parts if p.name == '3708.dat')
        for bearing_x in model.ROD_BEARING_X:
            hole_x=bearing_x+model.MODULE_DX
            assert rod.pos[0] - 120 <= hole_x - 10
            assert rod.pos[0] + 120 >= hole_x + 10

    # 前后推杆会随头回转；中间行程也要检查它与固定舵机连杆的相对姿态。
    for fraction in range(1, 8):
        for angle in range(0, 360, 15):
            parts = model.module(model.OPEN_S * fraction / 8, angle, steps=False)
            for p in parts:
                p.arm = 'L'
            assert not four_arm.cross_hits(parts), ('中间行程回转干涉', fraction, angle)
    results = {'中间行程对本臂固定件': {'检查姿态数': 168, '干涉数': 0}}
    for name, stroke, low in (
        ('松开回位_完整魔方', model.OPEN_S, [-70, -70, -70]),
        ('夹紧拧层_静止的另外两层', 0.0, [-70 + 140 / 3, -70, -70]),
    ):
        best = (float('inf'), None, None)
        for angle in range(360):
            distance, part = cube_clearance(model.module(stroke, angle, steps=False), np.array(low), np.array([70, 70, 70]))
            if distance < best[0]:
                best = (distance, angle, part)
        assert best[0] >= 2.0, (name, best)  # 采样间隙至少 0.8mm。
        results[name] = {'最小表面采样间隙_mm': best[0] * .4, '角度': best[1], '零件': best[2]}
    from collections import Counter
    counts = Counter(p.name for p in model.build())
    for name in ('42610.dat','50945_nominal.dat'):
        assert counts[name] == 8, (name, counts[name])
    beta = model.CLAMP_BETA
    assert counts["42003.dat"] == counts["6587.dat"] == 0
    assert counts["32017.dat"] == 24  # 8片输入杆＋16片Watt摆杆
    assert counts["32449.dat"] == 24  # 16片轮端支承＋8片推杆铰接薄梁
    assert counts["11478.dat"] == 8  # Watt横梁端孔固定活动轴
    assert counts["32002.dat"] == 0
    inner_edge = model.JAW_Y + model.JAW_REACH * math.sin(beta) - model.TYRE_RADIUS
    assert abs(inner_edge - (model.CUBE_HALF - model.TYRE_PRELOAD)) < 1e-6
    assert 0 < model.TYRE_PRELOAD < 1.5
    results['名义尺寸'] = {
        '夹紧主臂角_deg': math.degrees(beta), '松开主臂角_deg': {str(side):math.degrees(model.jaw_beta(model.OPEN_S,side)) for side in (-1,1)},
        '推杆行程_mm': model.OPEN_S * .4,
        '自由夹口_mm': 2 * (model.CUBE_HALF - model.TYRE_PRELOAD) * .4,
        '每侧橡胶名义压缩_mm': model.TYRE_PRELOAD * .4,
        '压头轴中心X_mm': (model.PIVOT_X + model.MODULE_DX + model.JAW_REACH * math.cos(beta)) * .4,
        '舵机曲柄转角_deg': math.degrees(model.servo_theta_for(model.OPEN_S)[0] - model.servo_theta_for(0)[0]),
    }
    results['整机压头用量'] = {'42610':8,'50945':8,'32062_轮轴':8,'32449':16,'4519_固定轴':8,'32123a_固定轴限位':16,'32054_固定销':8}
    output = Path(__file__).resolve().parents[3] / 'docs/lego/v3/pressure_pad_checks.json'
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
    print(output.read_text())


if __name__ == '__main__':
    main()
