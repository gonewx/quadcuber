"""Independent single-arm profiles; no GPIO access or config mutation at import."""
import config

# Fixed wiring, mirrored by wiring/spec.py and checked by repository tests.
PINS = {'R': (2, 3, 4, 5, 8, (0, 1)), 'L': (6, 7, 12, 13, 9, (2, 3))}
OUTPUTS = (2, 3, 6, 7, 8, 9)


class Profile:
    """Attribute view of one group; no copied or shared fallback values."""
    def __init__(self, values):
        object.__setattr__(self, '_values', values)

    def __getattr__(self, name):
        try:
            return self._values[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self._values[name] = value

    def __delattr__(self, name):
        try:
            del self._values[name]
        except KeyError:
            raise AttributeError(name)


def get_profile(name):
    if name not in ('R', 'L'):
        raise ValueError('只支持 arm R 或 arm L；无效选择已停止输出')
    if hasattr(config, 'ARMS'):
        groups = config.ARMS
        if not isinstance(groups, dict) or set(groups) != {'R', 'L'}:
            raise ValueError('config.py 的 ARMS 必须包含独立 R/L 分组')
        r, l = groups['R'], groups['L']
        if (not isinstance(r, dict) or not isinstance(l, dict) or r is l
                or ('GAINS' in r and r.get('GAINS') is l.get('GAINS'))):
            raise ValueError('R/L 配置和 GAINS 不得共用同一字典')
        cfg = Profile(groups[name])
    else:
        if name != 'R':
            raise ValueError('旧平铺 config.py 仅支持 R；先备份并迁移为 ARMS 分组')
        cfg = config
    fields = ('MOTOR_IN1', 'MOTOR_IN2', 'ENC_A', 'ENC_B', 'SERVO', 'ENC_SM')
    if tuple(getattr(cfg, key) for key in fields) != PINS[name]:
        raise ValueError('%s 引脚与固定 R/L 接线不符，拒绝初始化' % name)
    if getattr(cfg, 'ARM_ID', None) != name or cfg.ENC_PULLUP is not False:
        raise ValueError('%s 的 ARM_ID 或编码器分压配置不符' % name)
    return cfg
