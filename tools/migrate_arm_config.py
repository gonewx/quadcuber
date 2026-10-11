"""PC-only conversion of a backed-up flat R config; never communicates with Pico."""
import argparse
import ast
import hashlib
import os
from pathlib import Path
import pprint
import tempfile

TEMPLATE = Path(__file__).resolve().parents[1] / 'firmware/pico/config.py'


def read_settings(path):
    """Accept literal assignments only, with no ambiguous duplicate keys/names."""
    try:
        tree = ast.parse(Path(path).read_text(encoding='utf-8'))
        result = {}
        for index, statement in enumerate(tree.body):
            if (index == 0 and isinstance(statement, ast.Expr)
                    and isinstance(statement.value, ast.Constant)
                    and isinstance(statement.value.value, str)):
                continue
            if (not isinstance(statement, ast.Assign) or len(statement.targets) != 1
                    or not isinstance(statement.targets[0], ast.Name)):
                raise ValueError('仅支持字面值赋值；不执行导入、计算或函数')
            name = statement.targets[0].id
            if name in result:
                raise ValueError('重复配置名，拒绝猜测覆盖顺序')
            for node in ast.walk(statement.value):
                if isinstance(node, ast.Dict):
                    keys = [ast.literal_eval(key) for key in node.keys]
                    if len(set(keys)) != len(keys):
                        raise ValueError('字典存在重复键')
            result[name] = ast.literal_eval(statement.value)
        return result
    except (SyntaxError, TypeError, ValueError) as exc:
        # Do not print user values or source lines in diagnostics.
        raise ValueError('配置无法可靠解析：需要无重复键的字面值赋值；未执行备份代码') from exc


def expected_groups(source):
    r = read_settings(source)
    if 'ARMS' in r:
        raise ValueError('已经是分组配置，无需迁移；请备份后直接维护原 R/L 分组')
    template = read_settings(TEMPLATE)['ARMS']
    missing = set(template['R']) - set(r)
    if missing:
        raise ValueError('旧配置缺少字段：' + ', '.join(sorted(missing)) + '；保留原文件，不用默认值补齐')
    for key in ('MOTOR_IN1', 'MOTOR_IN2', 'ENC_A', 'ENC_B', 'SERVO', 'ENC_SM',
                'ENC_PULLUP', 'ARM_ID'):
        if type(r[key]) is not type(template['R'][key]) or r[key] != template['R'][key]:
            raise ValueError('旧 R 的固定接线或身份不符：' + key)
    l = template['L']
    for key in ('SERVO_OPEN_US', 'SERVO_CLOSE_US', 'SERVO_MIN_US', 'SERVO_MAX_US',
                'SERVO_MOVE_MS', 'SERVO_CALIBRATION_ARM', 'SERVO_CALIBRATION_PROFILE'):
        l[key] = None
    l['SERVO_CALIBRATED'] = False
    l['SERVO_TIMING_CONFIRMED'] = False
    return {'R': r, 'L': l}


def verify(source, converted):
    expected = expected_groups(source)
    actual = read_settings(converted)
    # repr distinguishes bool/int and list/tuple as well as literal values.
    if (set(actual) != {'ARMS'} or
            pprint.pformat(actual['ARMS'], sort_dicts=True) !=
            pprint.pformat(expected, sort_dicts=True)):
        raise ValueError('校验失败：R 未完整保留或 L 与未标定模板不符；勿上传')


def migrate(source, destination):
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise FileExistsError('输出已存在，拒绝覆盖；请使用新文件名')
    groups = expected_groups(source)
    rendered = ('"""由设备 R 备份迁移。仅修改本臂分组；L 尚未标定。"""\n\nARMS = '
                + pprint.pformat(groups, sort_dicts=False, width=100) + '\n')
    # Validate before atomic, exclusive installation. Never replace a backup.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                         dir=destination.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(rendered)
            stream.flush()
            os.fsync(stream.fileno())
        verify(source, temporary)
        os.link(temporary, destination)  # fails if destination already exists
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('migrate', 'verify'))
    parser.add_argument('backup', type=Path)
    parser.add_argument('converted', type=Path)
    args = parser.parse_args()
    try:
        if args.action == 'migrate':
            migrate(args.backup, args.converted)
        else:
            verify(args.backup, args.converted)
    except (OSError, ValueError) as exc:
        parser.exit(1, '未完成：' + str(exc) + '\n')
    print('校验通过：R 原值完整保留，L 未标定；未连接设备。')
    print('输出 SHA256:', hashlib.sha256(args.converted.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
