"""可摆压块的二维可行性计算；不是搭建模型或实物受力验证。

基准尺寸来自 claude/pro-redesign-jp5l33:tools/lego/v3/model.py。
运行：python tools/lego/research/swivel_pad_probe.py
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'docs/lego/research/swivel_pad_probe.json'
H, R, A = 32.0, 32.0, 16.0  # mm: 根轴半距、前端臂长、原版输入力臂
L_OLD, L_CANDIDATE = 32.0, math.hypot(32.0, 8.0)
HALF_CUBE, MAIN_RADIUS = 28.0, 3.6


def slider(beta, a, length):
    q = H - a * math.sin(beta)
    disc = length**2 - q**2
    if disc < -1e-10:
        return None
    return -a * math.cos(beta) - math.sqrt(max(0, disc))


def force_ratio(beta, a, length, r=R):
    """每侧法向力 / 推杆总轴向力；理想刚体，无摩擦，避开奇异位置。"""
    q = H - a * math.sin(beta)
    disc = length**2 - q**2
    if disc <= 1e-12:
        return None
    dx = a * math.sin(beta) - a * q * math.cos(beta) / math.sqrt(disc)
    return abs(dx) / (2 * r * math.cos(beta))


def main():
    rows = []
    for deg in (2, 1, 0, -.25, -.5, -1, -2, -3):
        b = math.radians(deg)
        rows.append({
            '主臂角度_deg_负值表示内收': deg,
            '原版输入点到中轴的最小距离_mm': H - A * math.sin(b),
            '32mm原连杆可达': slider(b, A, L_OLD) is not None,
            '32.985mm候选连杆可达': slider(b, A, L_CANDIDATE) is not None,
            '原粗梁前端裸夹口_mm': 2 * (H + R * math.sin(b) - MAIN_RADIUS),
            '候选每侧法向力_推杆总轴力比_仅在接触后适用': force_ratio(b, A, L_CANDIDATE),
        })
    assert slider(math.radians(-.25), A, L_OLD) is None
    assert slider(math.radians(-2), A, L_CANDIDATE) is not None
    assert slider(math.radians(-4), A, L_CANDIDATE) is None
    # 力矩平衡、虚功导数、数值差分三者相互校验。
    for deg in (-2, -.25, 1, 5, 15):
        b = math.radians(deg)
        step = 1e-6
        numerical = abs((slider(b + step, A, L_CANDIDATE)
                         - slider(b - step, A, L_CANDIDATE)) / (2 * step)) / (2 * R * math.cos(b))
        ratio = force_ratio(b, A, L_CANDIDATE)
        q = H - A * math.sin(b)
        horizontal = math.sqrt(L_CANDIDATE**2 - q**2)
        statics = abs(A * (q / horizontal - math.tan(b)) / (2 * R))
        assert abs(numerical - ratio) < 1e-7
        assert abs(statics - ratio) < 1e-10
    # 对称接触块：接触低边受到向外法向力时，应产生恢复到贴平的力矩。
    # 只验证法向接触、零铰链摩擦；实际摩擦/限位/回位结构另验。
    half_patch, pivot_to_face = 6.0, 4.0
    for deg in (-8, -4, -1, 1, 4, 8):
        angle = math.radians(deg)
        low_edge = -math.copysign(half_patch, angle)
        torque_per_normal = low_edge * math.cos(angle) + pivot_to_face * math.sin(angle)
        assert angle * torque_per_normal < 0
    # 现有平行夹块的垫片都在前端转轴后方；直接去掉从动臂无法平衡法向力矩。
    old_patch = (-14.4, -1.6)
    assert old_patch[1] < 0
    report = {
        '范围': '二维刚体几何和理想静力；没有证明装配可行、整机无干涉或实际夹紧力。',
        '尺寸单位': 'mm',
        '基准': 'claude/pro-redesign-jp5l33',
        '原版裸夹口_mm': 2 * (H - MAIN_RADIUS),
        '单侧前端内收1度位移_mm': R * math.sin(math.radians(1)),
        '原粗梁首次接触56mm魔方_内收角度_deg': math.degrees(math.asin((H - MAIN_RADIUS - HALF_CUBE) / R)),
        '候选连杆孔距_mm': L_CANDIDATE,
        '候选几何极限内收_deg_不含实体碰撞': math.degrees(math.asin((L_CANDIDATE - H) / A)),
        '研究分支当前单侧法向力比_负0_25度': force_ratio(math.radians(-.25), 8, L_CANDIDATE),
        '恢复原版16mm输入力臂的单侧法向力比_负0_25度': force_ratio(math.radians(-.25), A, L_CANDIDATE),
        '原压块垫片相对前端转轴的X范围_mm': old_patch,
        '判定': {
            '原版32mm输入连杆阻止负角内收': True,
            '32_985mm连杆允许小角度内收_仅孔位几何': True,
            '原粗梁内收1度会进入魔方实体': rows[5]['原粗梁前端裸夹口_mm'] < 56,
            '居中压块在正负8度内具有法向接触恢复力矩_理想条件': True,
            '旧压块直接移除从动臂可保持静力平衡': False,
        },
        '角度扫描': rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != '角度扫描'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
