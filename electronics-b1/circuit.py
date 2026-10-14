"""Quadcuber B1 底板：只插 Pico H，其余元件焊在 2 层板上（DRV8871 是唯一贴片芯片）。

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
    'to220': 'TO-220-3_Vertical',
    'to220_5': 'TO-220-5_P3.4x3.7mm_StaggerOdd_Lead3.8mm_Vertical',
    'jack': 'BarrelJack_Horizontal',
    'ptc': 'Fuse_PTC_Radial_P5.10mm',
    'do15': 'D_DO-15_P10.16mm_Horizontal',
    'do201': 'D_DO-201AD_P15.24mm_Horizontal',
    'do41': 'D_DO-41_SOD81_P10.16mm_Horizontal',
    'r': 'R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal',
    'r1w': 'R_Axial_DIN0414_L11.9mm_D4.5mm_P5.08mm_Vertical',
    'rv': 'R_Axial_DIN0207_L6.3mm_D2.5mm_P2.54mm_Vertical',
    'cdisc': 'C_Disc_D3.0mm_W1.6mm_P2.50mm',
    'cp10': 'CP_Radial_D10.0mm_P5.00mm',
    'cp8': 'CP_Radial_D8.0mm_P3.50mm',
    'cp6': 'CP_Radial_D6.3mm_P2.50mm',
    'cp5': 'CP_Radial_D5.0mm_P2.00mm',
    'l': 'L_Radial_D10.0mm_P5.00mm_Fastron_07M',
    'hdr3': 'PinHeader_1x03_P2.54mm_Vertical',
    'hole': 'MountingHole_3.2mm_M3',
    'ev3': 'EV3_Socket_UserDrawing',
    'drv': 'Texas_HTSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.95x4.9mm_Mask2.4x3.1mm_ThermalVias',
}

C = []


def add(ref, value, fp, pins, xy, rot=0, part='', note='', smd=False):
    C.append(dict(ref=ref, value=value, fp=FP[fp], pins={str(k): v for k, v in pins.items()},
                  xy=xy, rot=rot, part=part, note=note, smd=smd))


# ---- 输入与保护 -------------------------------------------------------------------
add('J1', '9V DC 中心正', 'jack', {1: 'VIN', 2: 'GND', 3: 'GND'}, (15, 15), 0,
    'DC-005 5.5/2.1mm', '脚1=中心(+)、脚2=外壳(-)、脚3=开关脚并地；焊前用实物核对孔位')
add('F1', 'PTC 5A', 'ptc', {1: 'VIN', 2: 'VIN_F'}, (17, 4.5), 0, 'RXEF500 自恢复保险丝（72V/5A）')
add('Q1', 'IRF4905', 'to220', {1: 'GATE', 2: 'VIN_F', 3: 'VM'}, (27, 6), 0,
    'IRF4905 P-MOS', '反接保护：漏极(2)接电源、源极(3)接 VM；导通后双向导电')
add('R1', '10k', 'r', {1: 'GATE', 2: 'GND'}, (24, 15), 0, '1/4W')
add('DZ1', '12V', 'do41', {1: 'VM', 2: 'GATE'}, (24, 19), 0, '1N4742A', '阴极(1)接源极 VM，限制 |Vgs|<=12V')
add('D1', 'P6KE15A', 'do15', {1: 'VM', 2: 'GND'}, (28, 24), 0, 'P6KE15A 单向 TVS', '阴极(1)接 VM')
add('C1', '470u/25V', 'cp10', {1: 'VM', 2: 'GND'}, (42, 8), 0, '470µF/25V 电解')
add('C2', '470u/25V', 'cp10', {1: 'VM', 2: 'GND'}, (54, 7), 0, '470µF/25V 电解')
add('R2', '300R 1W', 'r1w', {1: 'VM', 2: 'GND'}, (40, 17), 0, '300Ω 1W 金属膜')
add('R3', '300R 1W', 'r1w', {1: 'VM', 2: 'GND'}, (51.5, 17), 0, '300Ω 1W 金属膜')

# ---- 舵机 5V：LM2596T-5.0（1 VIN, 2 OUT, 3 GND, 4 FB, 5 ON/OFF） -------------------
add('U1', 'LM2596T-5.0', 'to220_5', {1: 'VM', 2: 'BUCK_SW', 3: 'GND', 4: 'SERVO_5V', 5: 'GND'},
    (5, 40), 0, 'LM2596T-5.0', 'ON/OFF(5) 接地=常开；FB(4) 接输出；需要散热片时留空间')
add('C3', '220u/25V', 'cp8', {1: 'VM', 2: 'GND'}, (6, 48.5), 0, '220µF/25V 电解（输入）')
add('D2', '1N5822', 'do201', {1: 'BUCK_SW', 2: 'GND'}, (16, 30), 0, '1N5822 3A 肖特基', '阴极(1)接开关节点')
add('L1', '33uH 3A', 'l', {1: 'BUCK_SW', 2: 'SERVO_5V'}, (17, 45), 0, '33µH/3A 工字电感')
add('C4', '470u/16V', 'cp8', {1: 'SERVO_5V', 2: 'GND'}, (32, 46), 0, '470µF/16V 低阻电解（输出）')

# ---- 逻辑 5V：7805（1 IN, 2 GND, 3 OUT）-> 编码器 5V，经 1N5819 -> Pico VSYS ------
add('U2', '7805', 'to220', {1: 'VM', 2: 'GND', 3: '5V_LOGIC'}, (42, 30), 0, 'L7805CV')
add('C5', '0.33u', 'cdisc', {1: 'VM', 2: 'GND'}, (42, 36), 0, '0.33µF 瓷片')
add('C6', '10u/16V', 'cp5', {1: '5V_LOGIC', 2: 'GND'}, (50, 36), 0, '10µF/16V 电解')
add('C7', '0.1u', 'cdisc', {1: '5V_LOGIC', 2: 'GND'}, (51.5, 30), 0, '0.1µF 瓷片')
add('D3', '1N5819', 'do41', {1: 'VSYS', 2: '5V_LOGIC'}, (55, 42), 180, '1N5819 肖特基', '阴极(1)接 Pico VSYS')

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
        (x + 1.5, 62), 270, 'DRV8871DDAR', smd=True, note='唯一贴片件；热风枪焊散热焊盘')
    add(f'R{n}', '43.2k', 'r', {1: f'{arm}_ILIM', 2: 'GND'}, (x - 9.5, 55.5), 0, '43.2kΩ 1%', '限流约 1.48A（64/R）')
    add(f'C{n}', '0.1u', 'cdisc', {1: 'VM', 2: 'GND'}, (x + 1.0, 55.5), 0, '0.1µF 瓷片')
    add(f'C{n+1}', '100u/25V', 'cp6', {1: 'VM', 2: 'GND'}, (x + 6.4, 61), 0, '100µF/25V 电解')
    # 编码器 10k 串联 + 20k 下拉（已在面包板验证）；立式电阻，给电机线让出中间通道
    add(f'R{n+1}', '10k', 'rv', {1: f'{arm}_ENC_A_RAW', 2: ea}, (x - 10.4, 72), 90, '1/4W 立式')
    add(f'R{n+2}', '20k', 'rv', {1: ea, 2: 'GND'}, (x - 7.3, 72), 90, '1/4W 立式')
    add(f'R{n+3}', '10k', 'rv', {1: f'{arm}_ENC_B_RAW', 2: eb}, (x - 4.2, 72), 90, '1/4W 立式')
    add(f'R{n+4}', '20k', 'rv', {1: eb, 2: 'GND'}, (x - 1.1, 72), 90, '1/4W 立式')
    add(f'R{n+5}', '220', 'rv', {1: sv, 2: f'{arm}_SERVO'}, (x + 5.0, 72), 90, '1/4W 立式')
    add(f'J{n}', f'舵机 {arm} S+G', 'hdr3', {1: 'GND', 2: 'SERVO_5V', 3: f'{arm}_SERVO'}, (x + 8.3, 72), 180, '1×3 排针', '自下而上 G/+/S')
    add(f'J{n+1}', f'EV3 {arm}', 'ev3', {1: f'{arm}_M1', 2: f'{arm}_M2', 3: 'GND', 4: '5V_LOGIC',
                                          5: f'{arm}_ENC_A_RAW', 6: f'{arm}_ENC_B_RAW'},
        (x, 93), 180, '同批 EV3 插座（用户已有）', '针序未用实物核实：接电机前断电六路通断')

for k, xy in enumerate([(3.5, 3.5), (95.5, 3.5), (3.5, 95.5), (95.5, 95.5)], 1):
    add(f'H{k}', 'M3', 'hole', {}, xy, 0)

BOARD = (99.0, 99.0)
