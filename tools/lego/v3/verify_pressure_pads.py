"""补充检查：压头两端十字孔、推杆导向覆盖和魔方本体/相邻两层避让。

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
            back = front + rotation @ [-40, 0, 0]
            lock = min((p for p in parts if p.name == '6632.dat'), key=lambda p: np.linalg.norm(p.pos - back))
            main_beam = min((p for p in parts if p.name == '40490.dat' and p.color == model.C_JAW), key=lambda p: np.linalg.norm(p.pos - pivot))
            assert np.linalg.norm(main_beam.world([0, 0, 80]) - front) < 1e-6
            assert np.linalg.norm(main_beam.world([0, 0, 40]) - back) < 1e-6
            assert np.linalg.norm(main_beam.world([0, 0, -20]) - pivot) < 1e-6
            assert np.linalg.norm(main_beam.world([0, 0, -60]) - (pivot + rotation @ [-40, 0, 0])) < 1e-6
            # 6632 的端孔坐标是 0 和 40，中间孔是圆孔，不能误当作十字孔。
            for local, expected in (([0, 0, 0], back), ([0, 0, 40], front)):
                actual = lock.world(local) + [0, 0, 15]
                assert np.linalg.norm(actual - expected) < 1e-6, '固定薄梁端孔未与主臂对齐'
                axes = [p for p in parts if p.note == '压头固定轴']
                assert min(np.linalg.norm(p.pos - expected) for p in axes) < 1e-6
            tyre = min((p for p in parts if p.name == 'grip_tyre.dat'), key=lambda p: np.linalg.norm(p.pos - front))
            assert abs(tyre.pos[2] - 15) < 1e-6, '上下压头必须在同一侧'
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
    beta = model.CLAMP_BETA
    eps = 1e-6
    derivative = (model.cross_x_for_beta(beta + eps) - model.cross_x_for_beta(beta - eps)) / (2 * eps)
    results['名义尺寸'] = {
        '夹紧主臂角_deg': math.degrees(beta), '松开主臂角_deg': math.degrees(model.OPEN_BETA),
        '推杆行程_mm': model.OPEN_S * .4,
        '自由夹口_mm': 2 * (model.JAW_Y + model.JAW_REACH * math.sin(beta) - model.TYRE_RADIUS) * .4,
        '接触中心X_mm': (model.PIVOT_X + model.MODULE_DX + model.JAW_REACH * math.cos(beta)) * .4,
        '每侧法向力_推杆总轴力比_理想': abs(derivative) / (2 * model.JAW_REACH * math.cos(beta)),
        '舵机曲柄转角_deg': math.degrees(model.servo_theta_for(0)[0] - model.servo_theta_for(model.OPEN_S)[0]),
    }
    output = Path(__file__).resolve().parents[3] / 'docs/lego/v3/pressure_pad_checks.json'
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
    print(output.read_text())


if __name__ == '__main__':
    main()
