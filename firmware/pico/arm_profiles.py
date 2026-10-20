"""Independent single-arm profiles; no GPIO access or config mutation at import."""
import config

# Fixed wiring, mirrored by wiring/spec.py and checked by repository tests.
PINS = {'R': (2, 3, 4, 5, 8, (0, 1)), 'L': (6, 7, 12, 13, 9, (2, 3)),
        'F': (10, 11, 16, 17, 20, (4, 5)), 'B': (14, 15, 18, 19, 21, (6, 7))}
# 选臂前全部拉低，四路驱动都停在滑行/休眠
OUTPUTS = (2, 3, 6, 7, 8, 9, 10, 11, 14, 15, 20, 21)


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
    if name not in PINS:
        raise ValueError('只支持 arm R/L/F/B；无效选择已停止输出')
    if hasattr(config, 'ARMS'):
        groups = config.ARMS
        if (not isinstance(groups, dict) or not {'R', 'L'} <= set(groups)
                or not set(groups) <= set(PINS)):
            raise ValueError('config.py 的 ARMS 必须包含独立 R/L 分组，可选 F/B')
        if name not in groups:
            raise ValueError('config.py 的 ARMS 没有 %s 分组；先补配置' % name)
        vals = list(groups.values())
        for i, a in enumerate(vals):
            if not isinstance(a, dict):
                raise ValueError('ARMS 每个分组必须是独立字典')
            for b in vals[i + 1:]:
                if a is b or ('GAINS' in a and a.get('GAINS') is b.get('GAINS')):
                    raise ValueError('各臂配置和 GAINS 不得共用同一字典')
        cfg = Profile(groups[name])
    else:
        if name != 'R':
            raise ValueError('旧平铺 config.py 仅支持 R；先备份并迁移为 ARMS 分组')
        cfg = config
    fields = ('MOTOR_IN1', 'MOTOR_IN2', 'ENC_A', 'ENC_B', 'SERVO', 'ENC_SM')
    if tuple(getattr(cfg, key) for key in fields) != PINS[name]:
        raise ValueError('%s 引脚与固定四臂接线不符，拒绝初始化' % name)
    if getattr(cfg, 'ARM_ID', None) != name or cfg.ENC_PULLUP is not False:
        raise ValueError('%s 的 ARM_ID 或编码器分压配置不符' % name)
    return cfg
