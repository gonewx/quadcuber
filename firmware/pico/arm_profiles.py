"""Independent single-arm profiles; no GPIO access or config mutation at import."""
import config
import config_l

# Fixed wiring, mirrored by wiring/spec.py and checked by repository tests.
PINS = {'R': (2, 3, 4, 5, 8, (0, 1)), 'L': (6, 7, 12, 13, 9, (2, 3))}
OUTPUTS = (2, 3, 6, 7, 8, 9)


def get_profile(name):
    if name not in ('R', 'L'):
        raise ValueError('只支持 arm R 或 arm L；无效选择已停止输出')
    cfg = config if name == 'R' else config_l
    fields = ('MOTOR_IN1', 'MOTOR_IN2', 'ENC_A', 'ENC_B', 'SERVO', 'ENC_SM')
    if tuple(getattr(cfg, key) for key in fields) != PINS[name]:
        raise ValueError('%s 引脚与固定 R/L 接线不符，拒绝初始化' % name)
    if getattr(cfg, 'ARM_ID', None) != name or cfg.ENC_PULLUP is not False:
        raise ValueError('%s 的 ARM_ID 或编码器分压配置不符' % name)
    return cfg
