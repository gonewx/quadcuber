"""电路文档共享数据；固定孔位图与固件变更必须一起复核。"""
from html import escape
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[2]
# 顺序：马达 IN1/IN2、编码器 A/B、舵机、PIO 状态机。
ARMS = {
    "R": ((2, 3), (4, 5), (8,), (0, 1)),
    "L": ((6, 7), (12, 13), (9,), (2, 3)),
    "F": ((10, 11), (16, 17), (20,), (4, 5)),
    "B": ((14, 15), (18, 19), (21,), (6, 7)),
}
DRV_LEFT = ['VM', 'NC', 'GND', 'AO1', 'AO2', 'BO2', 'BO1', 'GND']
DRV_RIGHT = ['NC', 'AIN2', 'AIN1', 'STBY', 'BIN1', 'BIN2', 'NC', 'GND']
TABLE_START = '<!-- wiring:pin-table:start -->'
TABLE_END = '<!-- wiring:pin-table:end -->'


def pin_rows():
    rows = [['用途'] + [arm + ' 臂' for arm in ARMS]]
    for index, label in enumerate(('马达 IN1 / IN2', '编码器 A / B', '舵机', 'PIO 状态机')):
        rows.append([label] + [
            (' / '.join('GP' + str(pin) for pin in values[index]) if index < 3
             else ', '.join(map(str, values[index]))) for values in ARMS.values()])
    return rows


def pin_table_html():
    rows = pin_rows()
    return '<table>' + ''.join(
        '<tr>' + ''.join(f'<{tag}>{escape(cell)}</{tag}>' for cell in row) + '</tr>'
        for row, tag in [(rows[0], 'th')] + [(row, 'td') for row in rows[1:]]) + '</table>'


def pin_table_markdown():
    rows = pin_rows()
    rows.insert(1, ['---'] * len(rows[0]))
    return '\n'.join('| ' + ' | '.join(row) + ' |' for row in rows)


def single_arm_document():
    source = (ROOT / 'docs/single_arm.md').read_text(encoding='utf-8')
    before, rest = source.split(TABLE_START)
    _, after = rest.split(TABLE_END)
    return before + TABLE_START + '\n' + pin_table_markdown() + '\n' + TABLE_END + after


def validate(config=None):
    """拒绝固件和固定接线图漂移，并检查四臂 GPIO/PWM/PIO 资源。"""
    if config is None:
        config = runpy.run_path(str(ROOT / 'firmware/pico/config.py'))
    # 图中还包含固定物理脚位/导线坐标；改表不能自动迁移接线图。
    expected = dict(MOTOR_IN1=2, MOTOR_IN2=3, ENC_A=4, ENC_B=5,
                    SERVO=8, ENC_SM=(0, 1), ENC_PULLUP=False)
    for key, value in expected.items():
        if config.get(key) != value:
            raise ValueError(f'{key} 与固定接线图不符：固件={config.get(key)!r}，图纸={value!r}；请复核孔位和导线')
    if ARMS['R'] != ((2, 3), (4, 5), (8,), (0, 1)):
        raise ValueError('R 臂分配与固定孔位图不符')
    gpio = [0, 1]  # 预留 UART
    states = []
    motor_slices, servo_slices = set(), set()
    for motor, encoder, servo, sm in ARMS.values():
        gpio.extend(motor + encoder + servo)
        states.extend(sm)
        if encoder[1] != encoder[0] + 1:
            raise ValueError('编码器 A/B 必须使用相邻 GPIO')
        motor_slices.update((pin // 2) % 8 for pin in motor)
        servo_slices.update((pin // 2) % 8 for pin in servo)
    if len(gpio) != len(set(gpio)):
        raise ValueError('GPIO 重复分配')
    pwm = [pin % 16 for motor, _, servo, _ in ARMS.values() for pin in motor + servo]
    if len(pwm) != len(set(pwm)) or motor_slices & servo_slices:
        raise ValueError('马达和舵机 PWM 通道或频率冲突')
    if sorted(states) != list(range(8)):
        raise ValueError('PIO 状态机分配错误')
