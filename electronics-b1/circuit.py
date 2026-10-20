"""Quadcuber B1 底板：只插 Pico H，其余元件焊在 2 层板上，尽量用贴片件（自己用热风枪/烙铁手焊）。

引脚只从 wiring/spec.py 的 ARMS 导入，不在这里重复定义。坐标单位 mm，原点为板框左上角。
"""
from pathlib import Path
import runpy

ARMS = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'wiring/spec.py'))['ARMS']

# 树莓派 Pico 物理引脚 -> 功能（官方 pinout，从顶面看 USB 朝上，左列 1..20 自上而下，右列 21..40 自下而上）。
PICO_PINS = {
    1: 'GP0', 2: 'GP1', 3: 'GND', 4: 'GP2', 5: 'GP3', 6: 'GP4', 7: 'GP5', 8: 'GND',
    9: 'GP6', 10: 'GP7', 11: 'GP8', 12: 'GP9', 13: 'GND', 14: 'GP10', 15: 'GP11',
    16: 'GP12', 17: 'GP13', 18: 'GND', 19: 'GP14', 20: 'GP15', 21: 'GP16', 22: 'GP17',
    23: 'GND', 24: 'GP18', 25: 'GP19', 26: 'GP20', 27: 'GP21', 28: 'GND', 29: 'GP22',
    30: 'RUN', 31: 'GP26', 32: 'GP27', 33: 'AGND', 34: 'GP28', 35: 'ADC_VREF',
    36: '3V3', 37: '3V3_EN', 38: 'GND', 39: 'VSYS', 40: 'VBUS',
}

FP = {
    'pico': 'RaspberryPi_Pico_Common_THT',
    'jack': 'BarrelJack_Horizontal',
    'hdr3': 'PinHeader_1x03_P2.54mm_Vertical',
    'hole': 'MountingHole_3.2mm_M3',
    'ev3': 'EV3_Socket_UserDrawing',
    'drv': 'Texas_HTSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.95x4.9mm_Mask2.4x3.1mm_ThermalVias',
    # 贴片件均选手焊加长焊盘或 0805 以上尺寸，便于烙铁/热风枪手焊
    'r': 'R_0805_2012Metric_Pad1.20x1.40mm_HandSolder',
    'c': 'C_0805_2012Metric_Pad1.18x1.45mm_HandSolder',
    'r2512': 'R_2512_6332Metric_Pad1.40x3.35mm_HandSolder',
    'fuse': 'Fuse_1206_3216Metric_Pad1.42x1.75mm_HandSolder',
    'soic8': 'SOIC-8_3.9x4.9mm_P1.27mm',
    'sot223': 'SOT-223-3_TabPin2',
    'to263_5': 'TO-263-5_TabPin3',
    'sma': 'D_SMA_Handsoldering',
    'smb': 'D_SMB_Handsoldering',
    'sod123': 'D_SOD-123',
    'cp10': 'CP_Elec_10x10.5',
    'cp8': 'CP_Elec_8x10.5',
    'cp6': 'CP_Elec_6.3x7.7',
    'l12': 'L_12x12mm_H8mm',
}

C = []


def add(ref, value, fp, pins, xy, rot=0, part='', note='', smd=False):
    C.append(dict(ref=ref, value=value, fp=FP[fp], pins={str(k): v for k, v in pins.items()},
                  xy=xy, rot=rot, part=part, note=note, smd=smd))


# ---- 输入与保护 -------------------------------------------------------------------
add('J1', '9V DC 中心正', 'jack', {1: 'VIN', 2: 'GND', 3: 'GND'}, (15, 15), 0,
    'DC-005 5.5/2.1mm', '脚1=中心(+)、脚2=外壳(-)、脚3=开关脚并地；焊前用实物核对孔位')
add('F1', '8A 慢断', 'fuse', {1: 'VIN', 2: 'VIN_F'}, (21, 6), 0, '1206 贴片保险丝 8A 慢断', '只防短路起火，不限流')
add('Q1', 'AO4407A', 'soic8', {1: 'VM', 2: 'VM', 3: 'VM', 4: 'GATE', 5: 'VIN_F', 6: 'VIN_F', 7: 'VIN_F', 8: 'VIN_F'},
    (30, 8), 180, 'AO4407A P-MOS（-30V/12A，SOIC-8）', '反接保护：漏极(5-8)接电源、源极(1-3)接 VM；导通后双向导电')
add('R1', '10k', 'r', {1: 'GATE', 2: 'GND'}, (30, 13.5), 0, '0805')
add('DZ1', '12V', 'sod123', {1: 'VM', 2: 'GATE'}, (30, 16.5), 0, 'BZT52C12 稳压管', '阴极(1)接源极 VM，限制 |Vgs|<=12V')
add('D1', 'SMBJ12A', 'smb', {1: 'VM', 2: 'GND'}, (30, 21), 0, 'SMBJ12A 单向 TVS', '阴极(1)接 VM')
add('C1', '470u/25V', 'cp10', {1: 'VM', 2: 'GND'}, (43, 7.5), 0, '470µF/25V 贴片电解 10×10.5')
add('C2', '470u/25V', 'cp10', {1: 'VM', 2: 'GND'}, (43, 20), 0, '470µF/25V 贴片电解 10×10.5')
add('R2', '300R 1W', 'r2512', {1: 'VM', 2: 'GND'}, (55, 5), 180, '300Ω 1W 2512')
add('R3', '300R 1W', 'r2512', {1: 'VM', 2: 'GND'}, (55, 10), 180, '300Ω 1W 2512')

# ---- 舵机 5V：LM2596S-5.0（1 VIN, 2 OUT, 3 GND/散热片, 4 FB, 5 ON/OFF） --------------
add('U1', 'LM2596S-5.0', 'to263_5', {1: 'VM', 2: 'BUCK_SW', 3: 'GND', 4: 'SERVO_5V', 5: 'GND'},
    (14, 32), 180, 'LM2596S-5.0（TO-263-5）', 'ON/OFF(5) 接地=常开；FB(4) 接输出；散热片焊盘接地铜')
add('C3', '220u/25V', 'cp8', {1: 'VM', 2: 'GND'}, (30, 33), 90, '220µF/25V 贴片电解 8×10.5（输入）')
add('D2', 'SS34', 'sma', {1: 'BUCK_SW', 2: 'GND'}, (22, 42.8), 90, 'SS34 3A 肖特基', '阴极(1)接开关节点')
add('L1', '33uH 3A', 'l12', {1: 'BUCK_SW', 2: 'SERVO_5V'}, (9, 45), 180, '33µH/3A 贴片功率电感 12×12')
add('C4', '470u/16V', 'cp8', {1: 'SERVO_5V', 2: 'GND'}, (31, 46), 0, '470µF/16V 贴片电解 8×10.5（输出）')

# ---- 逻辑 5V：AMS1117-5.0（1 GND, 2 OUT/散热片, 3 IN）-> 编码器 5V，经 SS14 -> Pico VSYS --
add('U2', 'AMS1117-5.0', 'sot223', {1: 'GND', 2: '5V_LOGIC', 3: 'VM'}, (51, 30), 0, 'AMS1117-5.0（SOT-223）',
    '输入最高 15V；约 0.1A 时功耗约 0.4W')
add('C5', '10u/25V', 'c', {1: 'VM', 2: 'GND'}, (44, 33.5), 90, '10µF/25V 0805')
add('C6', '22u/16V', 'c', {1: '5V_LOGIC', 2: 'GND'}, (58, 30), 90, '22µF/16V 0805')
add('C7', '0.1u', 'c', {1: '5V_LOGIC', 2: 'GND'}, (58, 35), 90, '0.1µF 0805')
add('D3', 'SS14', 'sma', {1: 'VSYS', 2: '5V_LOGIC'}, (53, 40), 180, 'SS14 肖特基', '阴极(1)接 Pico VSYS')

# ---- Pico H（排母插座） -----------------------------------------------------------
pico = {}
for pin, fn in PICO_PINS.items():
    pico[pin] = {'AGND': 'GND', 'VSYS': 'VSYS'}.get(fn, fn if fn == 'GND' or fn.startswith('GP') else None)
# 未用的 Pico 引脚不接网络；GP22/26/27/28 未引出。
for gp in (22, 26, 27, 28):
    pico[[k for k, v in PICO_PINS.items() if v == f'GP{gp}'][0]] = None
add('U3', 'Pico H', 'pico', pico, (66, 3), 0, '树莓派 Pico H + 2×1×20 排母', 'USB 朝上；排母两排相距 17.78mm')

add('J2', 'UART G TX RX', 'hdr3', {1: 'GND', 2: 'GP0', 3: 'GP1'}, (93, 16), 0, '1×3 排针', '接 Zero W：GP0=TX、GP1=RX')

# ---- 四臂 ---------------------------------------------------------------------------
X0 = {'R': 16, 'L': 38, 'F': 60, 'B': 82}   # 每臂 EV3 插座的中心 X
for i, (arm, (motor, enc, servo, _sm)) in enumerate(ARMS.items()):
    x = X0[arm]
    in1, in2 = (f'GP{n}' for n in motor)
    ea, eb = (f'GP{n}' for n in enc)
    sv = f'GP{servo[0]}'
    n = 10 * (i + 1)
    add(f'U{n}', 'DRV8871', 'drv', {1: 'GND', 2: in2, 3: in1, 4: f'{arm}_ILIM', 5: 'VM', 6: f'{arm}_M1',
                                     7: 'GND', 8: f'{arm}_M2', 9: 'GND'},
        (x + 1.5, 62), 270, 'DRV8871DDAR', note='热风枪焊散热焊盘')
    add(f'R{n}', '43.2k', 'r', {1: f'{arm}_ILIM', 2: 'GND'}, (x - 3.4, 59.4), 180, '43.2kΩ 1% 0805', '限流约 1.48A（64/R）')
    add(f'C{n}', '0.1u', 'c', {1: 'VM', 2: 'GND'}, (x - 5.0, 64.5), 0, '0.1µF 0805')
    add(f'C{n+1}', '100u/25V', 'cp6', {1: 'VM', 2: 'GND'}, (x + 9.0, 60.5), 0, '100µF/25V 贴片电解 6.3×7.7')
    # 编码器 10k 串联 + 20k 下拉（已在面包板验证）
    add(f'R{n+1}', '10k', 'r', {1: f'{arm}_ENC_A_RAW', 2: ea}, (x - 10.0, 71), 90, '0805')
    add(f'R{n+2}', '20k', 'r', {1: ea, 2: 'GND'}, (x - 7.5, 71), 90, '0805')
    add(f'R{n+3}', '10k', 'r', {1: f'{arm}_ENC_B_RAW', 2: eb}, (x - 5.0, 71), 90, '0805')
    add(f'R{n+4}', '20k', 'r', {1: eb, 2: 'GND'}, (x - 2.5, 71), 90, '0805')
    add(f'R{n+5}', '220', 'r', {1: sv, 2: f'{arm}_SERVO'}, (x + 5.5, 71), 90, '0805')
    add(f'J{n}', f'舵机 {arm} S+G', 'hdr3', {1: 'GND', 2: 'SERVO_5V', 3: f'{arm}_SERVO'}, (x + 8.3, 72), 180, '1×3 排针', '自下而上 G/+/S')
    add(f'J{n+1}', f'EV3 {arm}', 'ev3', {1: f'{arm}_M1', 2: f'{arm}_M2', 3: 'GND', 4: '5V_LOGIC',
                                          5: f'{arm}_ENC_A_RAW', 6: f'{arm}_ENC_B_RAW'},
        (x, 93), 180, '同批 EV3 插座（用户已有）', '针序未用实物核实：接电机前断电六路通断')

for k, xy in enumerate([(3.5, 3.5), (95.5, 3.5), (3.5, 95.5), (95.5, 95.5)], 1):
    add(f'H{k}', 'M3', 'hole', {}, xy, 0)

# ---- 接口丝印 -------------------------------------------------------------------
# (文字, x, y, 层 'F'/'B', 左对齐)。B1 实测把舵机插反、把舵机插进 J2，故逐针标出。
SILK = []
for arm, x in X0.items():
    for name, dy in (('G', 0.0), ('+', -2.54), ('S', -5.08)):   # 舵机排针自下而上 G/+/S，标在右侧
        SILK.append((name, x + 10.5, 72 + dy, 'F', False))
    SILK.append(('1', x + 4.15, 88.16, 'B', False))             # 背面焊 EV3 时认第 1 针（M1）
for name, dy in (('GND', 0.0), ('TX', 2.54), ('RX', 5.08)):     # J2 自上而下 GND/TX/RX
    SILK.append((name, 95.2, 16 + dy, 'F', True))
SILK.append(('UART', 93, 24.2, 'F', False))
# 下一臂编码器电阻 R21/R31/R41 的位号原在电阻左侧，会压住上面的 G/+，挪到电阻正下方并横排
REF_MOVES = {f'R{10 * i + 1}': (X0[arm] - 10.0, 74.3, 0) for i, arm in enumerate(X0, 1) if arm != 'R'}

BOARD = (99.0, 99.0)
