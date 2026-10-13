"""Attended, externally supported two-servo positioning. No motor/PIO control.

GP8/9 share PWM slice4. Own both at50Hz; never deinit one while retaining
another. Deadlines are cooperative software limits, not a hardware safety stop.
"""
import sys
import time
from machine import Pin, PWM
from arm_profiles import get_profile, OUTPUTS

HELP = """static> 仅托盘或独立支承全程承重；禁止降盘、悬空保持、转动。
  status
  cal R|L <min_us> <max_us> <start_us> detached|aligned <ttl_s>
  start R|L <start_us>           首脉冲可能跳转；首次脱杆，aligned须核实轴位
  move R|L <target_us> <rate_us/s> verified   已核实区间内限速分段，速率10..200
  renew R|L supported           明确重申支承，续该臂原时限；查询不会续期
  off / quit                   两路停信号并退出；不发松开脉冲，不保证机械保持
任一授权到期、错误、Ctrl+C或检测到输入断开都会停两路；5V不会被切断。
TTL为5..120秒。没有open/close、马达、翻转或降盘命令。
"""


class StaticPair:
    def __init__(self, support):
        self.active = False
        self.pwm = {}
        self.sessions = {'R': None, 'L': None}
        if support != 'supported':
            raise ValueError('static supported：先由托盘或独立支承全程承重')
        try:
            # Entry via arm_test first releases motor PWM and encoder PIO.
            self.profiles = {name: get_profile(name) for name in ('R', 'L')}
            for pin in OUTPUTS:
                Pin(pin, Pin.OUT, value=0)
            for name in ('R', 'L'):
                self.pwm[name] = PWM(Pin(self.profiles[name].SERVO, Pin.OUT, value=0),
                                     freq=50, duty_u16=0)
                if name == 'R':
                    # Clear A while slice is disabled before initializing B.
                    self.pwm[name].deinit()
            self.active = True
        except BaseException:
            self.close()
            raise

    def close(self):
        self.active = False
        self.sessions = {'R': None, 'L': None}
        error = None
        # Disconnect every output before a duty setter can restart shared PWM.
        for pin in OUTPUTS:
            try:
                Pin(pin, Pin.OUT, value=0)
            except BaseException as exc:
                error = exc
        for pwm in self.pwm.values():
            try:
                try:
                    pwm.duty_u16(0)
                finally:
                    pwm.deinit()
            except BaseException as exc:
                error = exc
        for pin in OUTPUTS:
            try:
                Pin(pin, Pin.OUT, value=0)
            except BaseException as exc:
                error = exc
        if error is not None:
            raise error

    def _check(self):
        if not self.active:
            raise ValueError('静态会话已结束；重新显式进入，不自动恢复')
        now = time.ticks_us()
        for name, session in self.sessions.items():
            if session and time.ticks_diff(now, session['expires']) >= 0:
                raise TimeoutError('%s授权到期，两路停止；继续由外部支承承重' % name)
        return now

    def command(self, line):
        try:
            return self._command(line)
        except BaseException:
            self.close()
            raise

    def _command(self, line):
        now = self._check()
        args = line.split()
        if args in (['off'], ['quit']):
            self.close()
            return {'stopped': True, 'mechanical_release_or_hold_confirmed': False}
        if args == ['help']:
            return HELP
        if args == ['status']:
            result = {'active': True, 'support_required': True, 'motors_enabled': False}
            for name, session in self.sessions.items():
                cfg = self.profiles[name]
                result[name] = {
                    'pin': cfg.SERVO,
                    'configured_calibrated': getattr(cfg, 'SERVO_CALIBRATED', False),
                    'configured_open_us': getattr(cfg, 'SERVO_OPEN_US', None),
                    'configured_close_us': getattr(cfg, 'SERVO_CLOSE_US', None),
                    'authorized': session is not None,
                    'commanded_us': session['us'] if session else None,
                    'target_us': session['target'] if session else None,
                    'bounds_us': [session['lo'], session['hi']] if session else None,
                    'remaining_ms': max(0, time.ticks_diff(session['expires'], now)//1000)
                    if session else 0,
                    'actual_position_known': False,
                }
            return result
        if len(args) < 2 or args[1] not in ('R', 'L'):
            raise ValueError('只支持显式R/L静态命令；错误会停止两路')
        cmd, name = args[:2]
        session = self.sessions[name]
        if cmd == 'cal' and len(args) == 7:
            if session is not None:
                raise ValueError('本臂已有授权；续期用renew，改范围须off后重新进入')
            lo, hi, start = (int(v) for v in args[2:5])
            condition, ttl = args[5], int(args[6])
            if (condition not in ('detached', 'aligned') or not 500 <= lo < hi <= 2500
                    or not lo <= start <= hi or not 5 <= ttl <= 120):
                raise ValueError('核实独立安全范围、首脉冲条件及时限5..120秒')
            cfg = self.profiles[name]
            if cfg.MACHINE_PROFILE != 'v4':
                raise ValueError('机械身份不匹配')
            limits = (getattr(cfg, 'SERVO_MIN_US', None), getattr(cfg, 'SERVO_MAX_US', None))
            if any(v is not None for v in limits) or getattr(cfg, 'SERVO_CALIBRATED', False) is True:
                if (any(type(v) is not int for v in limits)
                        or not 500 <= limits[0] <= lo < hi <= limits[1] <= 2500):
                    raise ValueError('声明不得扩大本臂已有范围；部分范围配置必须先核实')
            if getattr(cfg, 'SERVO_CALIBRATED', False) is True:
                if (getattr(cfg, 'SERVO_CALIBRATION_ARM', None) != name
                        or getattr(cfg, 'SERVO_CALIBRATION_PROFILE', None) != cfg.MACHINE_PROFILE):
                    raise ValueError('声明不得扩大本臂已有标定范围或借用另一臂身份')
            self.sessions[name] = dict(lo=lo, hi=hi, start=start, condition=condition,
                ttl=ttl, expires=time.ticks_add(now, ttl*1000000), us=None,
                target=None, position=None, rate=None, last=now)
            return {'authorized': name, 'pulse_sent': False, 'first_jump_risk': True}
        if session is None:
            raise ValueError('先为本臂独立cal声明，不继承另一臂参数')
        if cmd == 'renew' and args[2:] == ['supported']:
            session['expires'] = time.ticks_add(now, session['ttl']*1000000)
            return {'renewed': name, 'support_required': True}
        if cmd == 'start' and len(args) == 3:
            target = int(args[2])
            if session['us'] is not None or target != session['start']:
                raise ValueError('仅允许一次与声明start相同的首脉冲；之后必须move限速')
            self.pwm[name].duty_ns(target*1000)
            session.update(us=target, target=target, position=float(target), last=now)
            return {'started': name, 'commanded_us': target, 'actual_position_known': False}
        if cmd == 'move' and len(args) == 5 and args[4] == 'verified':
            target, rate = int(args[2]), int(args[3])
            if (session['us'] is None or not session['lo'] <= target <= session['hi']
                    or not 10 <= rate <= 200):
                raise ValueError('先start；目标限于已核实区间；显式速率10..200微秒/秒')
            duration = abs(target-session['us'])*1000000//rate
            if duration+1000000 >= time.ticks_diff(session['expires'], now):
                raise ValueError('授权余时不足；重新确认支承并renew，不能在途中预期超时')
            session.update(target=target, rate=rate, position=float(session['us']), last=now)
            return {'moving': name, 'target_us': target, 'rate_us_per_s': rate}
        raise ValueError('静态模式无此命令；不支持马达、自动开合或翻转')

    def tick(self):
        try:
            now = self._check()
            for name, s in self.sessions.items():
                if not s or s['us'] is None or s['us'] == s['target']:
                    continue
                if time.ticks_diff(now, s['last']) < 20000:
                    continue
                # Never catch up after a blocked/late console by a large jump.
                step = s['rate']*.02
                direction = 1 if s['target'] > s['position'] else -1
                pos = s['position']+direction*step
                pos = min(pos, s['target']) if direction > 0 else max(pos, s['target'])
                pulse = int(round(pos))
                if pulse != s['us']:
                    self.pwm[name].duty_ns(pulse*1000)
                    s['us'] = pulse
                s['position'], s['last'] = pos, now
        except BaseException:
            self.close()
            raise


def run_console(support, stream=None, poller=None):
    """Poll then read one raw byte; text read can wait for UTF-8 continuation."""
    pair = StaticPair(support)
    try:
        if stream is None:
            stream = sys.stdin
        if poller is None:
            import select
            poller = select.poll()
        poller.register(stream, 1)
        print(HELP)
        print('static> ', end='')
        line = ''
        byte = bytearray(1)
        while pair.active:
            pair.tick()
            events = poller.poll(10)
            if not events:
                continue
            if any(event[1] & (8 | 16 | 32) for event in events):
                raise EOFError('静态输入连接中断')
            count = stream.readinto(byte)
            if count is None:
                continue
            if count == 0:
                break
            char = chr(byte[0])
            if char == '\x04':
                break
            if char == '\x03':
                raise KeyboardInterrupt
            if char in ('\r', '\n'):
                if not line:
                    continue
                print()
                response = pair.command(line)
                print(response)
                line = ''
                if pair.active:
                    print('static> ', end='')
            elif char in ('\x08', '\x7f'):
                line = line[:-1]
                print('\b \b', end='')
            elif ' ' <= char <= '~':
                line += char
                if len(line) > 160:
                    raise ValueError('命令过长')
                print(char, end='')
            else:
                raise ValueError('静态命令仅接受ASCII；非法字节已停止两路')
    finally:
        pair.close()
        print('\n静态模式结束：两路停信号；5V未切断，仍需外部支承。重新arm R/L才恢复单臂查询。')
