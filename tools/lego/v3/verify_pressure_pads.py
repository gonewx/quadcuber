"""补充检查：压头固定销、轮毂短销与硬压头轴肩、推杆导向覆盖和魔方本体/相邻两层避让。

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
        beta = model.jaw_beta(stroke)
        parts = model.module(stroke, steps=False)
        for sy in (1, -1):
            pivot = np.array([model.PIVOT_X + model.MODULE_DX, sy * model.JAW_Y, 0])
            rotation = model.rot_z(sy * beta)
            front = pivot + rotation @ [model.JAW_REACH, 0, 0]
            beam = next(p for p in parts if p.head and p.color == model.C_JAW and p.name == ('32524.dat' if sy == -1 else '32316.dat'))
            assert np.linalg.norm(beam.pos - pivot) < 1e-6
            assert np.linalg.norm(beam.world([0, 0, -40]) - (pivot + rotation @ [-40, 0, 0])) < 1e-6
            thin = min((p for p in parts if p.note == '压头延伸薄梁'), key=lambda p: np.linalg.norm(p.pos - front))
            assert np.linalg.norm(thin.world([0, 0, 40]) - (front + [0, 0, -15])) < 1e-6
            expected_reaches = (20, 60) if sy == -1 else (20, 40)
            for reach in expected_reaches:
                expected = pivot + rotation @ [reach, 0, -10]
                assert min(np.linalg.norm(p.pos - expected) for p in parts if p.note == '薄梁固定销') < 1e-6
            if sy == -1:
                pin = next(p for p in parts if p.note == '轮毂短销')
                wheel = next(p for p in parts if p.name == '42610.dat')
                tyre = next(p for p in parts if p.name == '50945_nominal.dat')
                assert np.linalg.norm(wheel.pos - front) < 1e-6
                assert np.linalg.norm(tyre.pos - front) < 1e-6
                assert np.allclose(sorted([pin.world([-20,0,0])[2], pin.world([10,0,0])[2]]), [-20,10])
                layers = check._pin_layers(pin, [thin, wheel])
                assert len(layers) == 2 and sorted(round(hi-lo) for _,lo,hi in layers) == [10,20]
            else:
                block = next(p for p in parts if p.name == '42003.dat')
                axle = next(p for p in parts if p.note == '硬压头止挡轴')
                bush = next(p for p in parts if p.note == '硬压头防脱轴套')
                # 6587 轴肩的平面抵住块体内面；凸点端面再朝魔方突出 6 LDU。
                assert np.linalg.norm(axle.world([28,0,0]) - (front + rotation @ [0,-10,0])) < 1e-6
                assert np.linalg.norm(axle.world([34,0,0]) - (front + rotation @ [0,-16,0])) < 1e-6
                assert np.linalg.norm(bush.pos - (front + rotation @ [0,15,0])) < 1e-6
                for reach in (60,80):
                    expected = pivot + rotation @ [reach,0,-10]
                    pin = min((p for p in parts if p.note == '硬压头座固定销'), key=lambda p: np.linalg.norm(p.pos - expected))
                    assert np.linalg.norm(pin.pos - expected) < 1e-6
                    assert len(check._pin_layers(pin,[thin,block])) == 2
        # 两个导向轴承都必须完整落在后段 12L 推杆之内，不能只看无限长轴线。
        rod = next(p for p in parts if p.name == '3708.dat')
        for hole_x in (-450 + model.MODULE_DX, -330 + model.MODULE_DX):
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
    for name in ('42610.dat','50945_nominal.dat','42003.dat','6587.dat','32002.dat'):
        assert counts[name] == 4, (name, counts[name])
    beta = model.CLAMP_BETA
    hard_edge = model.JAW_Y + 94 * math.sin(beta) - 16 * math.cos(beta)
    assert abs(hard_edge - model.CUBE_HALF) < 1e-6
    assert 0 < model.TYRE_PRELOAD < 1.5
    results['名义尺寸'] = {
        '夹紧主臂角_deg': math.degrees(beta), '松开主臂角_deg': math.degrees(model.OPEN_BETA),
        '推杆行程_mm': model.OPEN_S * .4,
        '自由夹口_mm': (2 * model.CUBE_HALF - model.TYRE_PRELOAD) * .4,
        '橡胶侧名义压缩_mm': model.TYRE_PRELOAD * .4,
        '压头轴中心X_mm': (model.PIVOT_X + model.MODULE_DX + model.JAW_REACH * math.cos(beta)) * .4,
        '舵机曲柄转角_deg': math.degrees(model.servo_theta_for(0)[0] - model.servo_theta_for(model.OPEN_S)[0]),
    }
    results['库存检查'] = {'42610':4,'50945':4,'42003':4,'6587':4}
    output = Path(__file__).resolve().parents[3] / 'docs/lego/v3/pressure_pad_checks.json'
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
    print(output.read_text())


if __name__ == '__main__':
    main()
