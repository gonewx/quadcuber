"""单臂原型测试程序 (MicroPython, 树莓派 Pico)。

用法 (详见 docs/single_arm.md):
    mpremote cp config.py control.py encoder.py motor.py arm_test.py :
    mpremote repl --capture arm.log
    >>> import arm_test; arm_test.main()

然后输入命令, 输入 help 查看列表。测量结果以 "RESULT {json}" 的形式输出,
把串口日志保存下来, 在 PC 上用 `python -m quadcuber armlog arm.log` 汇总成 timing.json。

这个程序为了方便测量, 控制循环直接跑在主核上 (动作期间阻塞)。整机固件会把 PID 放到第二个核心。
注意: 本程序尚未在实物上运行过, 首次上电请按文档里的步骤, 从 check 命令开始。
"""

import gc
import json
import time
from array import array

import config
from control import DONE, FAILED, Gains, MoveController
from encoder import Encoder
from motor import Motor, Servo

DEG_PER_COUNT = 360.0 / (config.COUNTS_PER_MOTOR_REV * config.GEAR_RATIO)
TRACE_LEN = 800  # 轨迹缓存的采样点数 (每个控制周期一个点)

ticks_us = time.ticks_us
ticks_diff = time.ticks_diff
ticks_add = time.ticks_add  # ticks_us 会回绕 (rp2 上约 18 分钟), 时间加减必须用 ticks_add/ticks_diff


def _r(x, n=4):
    return None if x is None else round(x, n)


def result(kind, data):
    data["type"] = kind
    print("RESULT " + json.dumps(data))
    return data


class Arm:
    def __init__(self):
        self.motor = Motor(config.MOTOR_IN1, config.MOTOR_IN2, config.MOTOR_INVERT, config.PWM_FREQ)
        self.enc = Encoder(config.ENC_A, config.ENC_B, config.ENC_SM, config.ENC_INVERT, pull_up=config.ENC_PULLUP)
        self.servo = Servo(config.SERVO)
        self.gains = Gains(**config.GAINS)
        self.nominal = 0.0  # 名义角度 (90 的整数倍), 相对移动以它为基准, 误差不会累积
        self.hold_ms = 50  # 到位后继续保持控制的时间, 之后刹车
        self.trace_t = array("i", [0] * TRACE_LEN)
        self.trace_ref = array("f", [0] * TRACE_LEN)
        self.trace_pos = array("f", [0] * TRACE_LEN)
        self.trace_u = array("f", [0] * TRACE_LEN)
        self.trace_n = 0

    def angle(self):
        return self.enc.count() * DEG_PER_COUNT

    def stop(self):
        if config.BRAKE_AFTER_MOVE:
            self.motor.brake()
        else:
            self.motor.coast()

    # ---- 闭环旋转 ----------------------------------------------------------

    def move_to(self, target, tag="free", q=None, rest_ms=150):
        g = self.gains
        gc.collect()
        start = self.angle()
        t0 = ticks_us()
        mc = MoveController(start, target, g, 0)
        loop = config.LOOP_US
        deadline = t0
        last = t0
        max_dt = 0
        n = 0
        done_at = None
        tn = 0
        try:
            while True:
                now = ticks_us()
                rel = ticks_diff(now, t0)
                dt = ticks_diff(now, last)
                if dt > max_dt:
                    max_dt = dt
                last = now
                pos = self.angle()
                u = mc.step(rel, pos)
                self.motor.drive(u)
                n += 1
                if tn < TRACE_LEN:
                    self.trace_t[tn] = rel
                    self.trace_ref[tn] = mc.prof.at(rel / 1e6)[0]
                    self.trace_pos[tn] = pos
                    self.trace_u[tn] = u
                    tn += 1
                if mc.state in FAILED:
                    self.motor.coast()
                    break
                if mc.state == DONE:
                    if done_at is None:
                        done_at = rel
                    elif rel - done_at >= self.hold_ms * 1000:
                        self.stop()
                        break
                deadline = ticks_add(deadline, loop)
                if ticks_diff(deadline, ticks_us()) < 0:
                    deadline = ticks_us()  # 跟不上了, 不补
                while ticks_diff(deadline, ticks_us()) > 0:
                    pass
        finally:
            if mc.state != DONE and mc.state not in FAILED:  # 被 Ctrl+C 打断
                self.motor.coast()
        self.trace_n = tn
        err = target - self.angle()
        time.sleep_ms(rest_ms)
        err_rest = target - self.angle()
        ok = mc.state == DONE
        r = dict(
            tag=tag,
            q=q,
            start=_r(start, 2),
            target=_r(target, 2),
            state=mc.state,
            ok=ok,
            t_profile=_r(mc.prof.duration),
            t_reach=_r(mc.t_reach),
            t_settle=_r(mc.t_settle) if ok else None,
            err=_r(err, 2),
            err_rest=_r(err_rest, 2),
            overshoot=_r(mc.overshoot, 2),
            max_track_err=_r(mc.max_track_err, 2),
            max_dt_us=max_dt,
            loops=n,
        )
        result("move", r)
        if not ok:
            print("!! 动作失败:", mc.state, "(马达已断电)。检查接线/方向 (check), 或放宽参数。")
        return r

    def rot(self, q, tag="free"):
        target = self.nominal + 90 * q
        r = self.move_to(target, tag, q)
        if r["ok"]:
            self.nominal = target
        return r

    # ---- 舵机 --------------------------------------------------------------

    def grip(self, close):
        self.servo.pulse(config.SERVO_CLOSE_US if close else config.SERVO_OPEN_US)
        time.sleep_ms(config.SERVO_MOVE_MS)


# ---- 命令 ------------------------------------------------------------------


def cmd_help(arm, args):
    print(HELP)


def cmd_enc(arm, args):
    c = arm.enc.count()
    print("计数 %d, 马达 %.1f 度, 机械手 %.2f 度 (名义 %.0f)" % (c, c * 360.0 / config.COUNTS_PER_MOTOR_REV, c * DEG_PER_COUNT, arm.nominal))


def cmd_zero(arm, args):
    arm.enc.zero()
    arm.nominal = 0.0
    print("已清零")


def cmd_check(arm, args):
    """正占空比短暂驱动, 检查马达和编码器的方向是否一致。"""
    duty = float(args[0]) if args else 0.3
    c0 = arm.enc.count()
    arm.motor.drive(duty)
    time.sleep_ms(150)
    arm.motor.brake()
    time.sleep_ms(100)
    d = arm.enc.count() - c0
    print("占空比 %+.2f 驱动 150ms, 编码器变化 %d 计数 (机械手 %.1f 度)" % (duty, d, d * DEG_PER_COUNT))
    if abs(d) < 4:
        print("!! 几乎没有读数: 马达没转 (查供电/DRV8833 的 nSLEEP/接线), 或编码器没接好 (查分压电阻和黄/蓝线通断)")
    elif d < 0:
        print("!! 方向相反: 把 config.py 里的 ENC_INVERT 改成相反的值 (或 MOTOR_INVERT)")
    else:
        print("方向正确 (马达和编码器一致)。机械头转向还要用 duty 0.3 500 目测: 从舵机那头朝魔方看应为顺时针, 见 docs/single_arm.md 第 5 节")
    arm.nominal = round(arm.angle() / 90) * 90


def cmd_duty(arm, args):
    duty = float(args[0])
    ms = int(args[1]) if len(args) > 1 else 300
    a0 = arm.angle()
    arm.motor.drive(duty)
    time.sleep_ms(ms)
    arm.motor.brake()
    time.sleep_ms(100)
    print("转了 %.1f 度" % (arm.angle() - a0))


def cmd_cal(arm, args):
    arm.motor.coast()
    c0 = arm.enc.count()
    input("用手把机械手 (没装机械手时就是马达输出轴) 转正好 1 整圈, 做个记号对齐, 转完按回车 > ")
    d = arm.enc.count() - c0
    print("机械手一圈 = %d 计数" % d)
    print("当前 GEAR_RATIO = %s, 所以 COUNTS_PER_MOTOR_REV 应为 %.1f" % (config.GEAR_RATIO, abs(d) / config.GEAR_RATIO))
    print("(EV3 马达 4 倍频预期 720; 若 GEAR_RATIO 未知, 可以用 %d / 720 估计齿轮比)" % abs(d))


def cmd_speed(arm, args):
    """开环全速驱动, 测空载速度和时间常数。"""
    duty = float(args[0]) if args else 1.0
    ms = int(args[1]) if len(args) > 1 else 400
    print("机械手会连续转约 %d 度, 确认线缆不会缠住。3 秒后开始..." % int(ms * arm.gains.v_full / 1000 * duty))
    time.sleep_ms(3000)
    n = min(ms, TRACE_LEN)
    ts, ps = arm.trace_t, arm.trace_pos
    gc.collect()
    t0 = ticks_us()
    arm.motor.drive(duty)
    for i in range(n):
        target = ticks_add(t0, i * 1000)
        while ticks_diff(target, ticks_us()) > 0:
            pass
        ts[i] = ticks_diff(ticks_us(), t0)
        ps[i] = arm.angle()
    arm.motor.brake()
    arm.trace_n = 0
    # 稳态速度: 最后 40% 时间的平均斜率
    i0 = int(n * 0.6)
    v_ss = (ps[n - 1] - ps[i0]) * 1e6 / (ts[n - 1] - ts[i0])
    # 时间常数: 速度 (5ms 窗口) 达到稳态 63% 的时刻
    tau = None
    for i in range(5, n):
        v = (ps[i] - ps[i - 5]) * 1e6 / (ts[i] - ts[i - 5])
        if abs(v) >= 0.63 * abs(v_ss):
            tau = (ts[i] + ts[i - 5]) / 2e6  # 窗口中点
            break
    kfs = arm.gains.kfs
    print("占空比 %.2f: 稳态 %.0f 度/秒, 时间常数约 %s 秒" % (duty, v_ss, _r(tau, 3)))
    if abs(duty) > kfs:
        print("建议 v_full = %.0f (已扣除静摩擦 kfs=%.2f), tau = %s" % (abs(v_ss) / (abs(duty) - kfs), kfs, _r(tau, 3)))
    result("speed", dict(duty=duty, v_ss=_r(v_ss, 1), tau=_r(tau)))
    time.sleep_ms(300)
    arm.nominal = round(arm.angle() / 90) * 90


def cmd_friction(arm, args):
    """占空比从 0 慢慢加大, 找到开始转动的值。"""
    found = []
    for sign in (1, -1):
        c0 = arm.enc.count()
        duty = 0.0
        while duty < 0.5:
            duty += 0.005
            arm.motor.drive(sign * duty)
            time.sleep_ms(30)
            if abs(arm.enc.count() - c0) >= 3:
                break
        arm.motor.brake()
        found.append(duty)
        print("方向 %+d: 起转占空比 %.3f" % (sign, duty))
        time.sleep_ms(300)
    print("建议 kfs = %.3f (取两个方向的较小值, 略偏小比偏大好)" % min(found))
    result("friction", dict(pos=_r(found[0]), neg=_r(found[1])))
    arm.nominal = round(arm.angle() / 90) * 90


def cmd_rot(arm, args):
    arm.rot(int(args[0]), args[1] if len(args) > 1 else "free")


def cmd_goto(arm, args):
    target = float(args[0])
    if arm.move_to(target, "goto")["ok"]:
        arm.nominal = target


def _summary(tag, q, total, ts, errs, rests):
    if ts:
        ts_sorted = sorted(ts)
        p90 = ts_sorted[min(len(ts) - 1, int(len(ts) * 0.9))]
        print(
            "[%s q=%d] 成功 %d/%d, 到位耗时 平均 %.3fs 最长 %.3fs (p90 %.3fs), |误差| 平均 %.2f 最大 %.2f 度, 静止后最大 %.2f 度"
            % (tag, q, len(ts), total, sum(ts) / len(ts), ts_sorted[-1], p90, sum(errs) / len(errs), max(errs), max(rests))
        )


def cmd_bench(arm, args):
    """来回转 n 次, 统计耗时和误差。tag: free = 空转 (不夹魔方), load = 夹着魔方拧一层。"""
    q = int(args[0]) if args else 1
    n = int(args[1]) if len(args) > 1 else 20
    tag = args[2] if len(args) > 2 else "free"
    ts, errs, rests = [], [], []
    for i in range(n):
        d = q if i % 2 == 0 else -q
        r = arm.rot(d, tag)
        if not r["ok"]:
            break
        ts.append(r["t_settle"])
        errs.append(abs(r["err"]))
        rests.append(abs(r["err_rest"]))
    _summary(tag, q, n, ts, errs, rests)


def cmd_cycle(arm, args):
    """模拟实际工作: 夹紧 -> 转 q (拧面, load) -> 松开 -> 转回 (空转, free), 重复 n 次。"""
    n = int(args[0]) if args else 10
    q = int(args[1]) if len(args) > 1 else 1
    for i in range(n):
        t0 = ticks_us()
        arm.grip(True)
        if not arm.rot(q, "load")["ok"]:
            break
        arm.grip(False)
        if not arm.rot(-q, "free")["ok"]:
            break
        result("cycle", dict(q=q, i=i, t_total=_r(ticks_diff(ticks_us(), t0) / 1e6)))
    arm.grip(False)


def cmd_grip(arm, args):
    n = int(args[0]) if args else 5
    for _ in range(n):
        arm.grip(True)
        time.sleep_ms(300)
        arm.grip(False)
        time.sleep_ms(300)
    # 舵机没有位置反馈, 这里记录的是配置的等待时间, 实际值要靠录像确认
    result("grip", dict(open=config.SERVO_MOVE_MS / 1000, close=config.SERVO_MOVE_MS / 1000))


def cmd_open(arm, args):
    arm.grip(False)


def cmd_close(arm, args):
    arm.grip(True)


def cmd_servo(arm, args):
    if args and args[0] == "off":
        arm.servo.off()
    else:
        arm.servo.pulse(int(args[0]))
        print("舵机脉宽 %d 微秒" % arm.servo.us)


def cmd_set(arm, args):
    if args[0] == "hold":
        arm.hold_ms = int(args[1])
    else:
        arm.gains.set(args[0], args[1])
    print("%s = %s" % (args[0], args[1]))


def cmd_show(arm, args):
    for k, v in arm.gains.as_dict().items():
        print("  %-10s %s" % (k, v))
    print("  %-10s %s" % ("hold", arm.hold_ms))
    print("  1 计数 = %.4f 度 (机械手)" % DEG_PER_COUNT)


def cmd_trace(arm, args):
    """输出最近一次闭环动作的轨迹 (CSV), 复制到 PC 上画图调参。"""
    print("TRACE t_us,ref_deg,pos_deg,duty")
    for i in range(arm.trace_n):
        print("TRACE %d,%.2f,%.2f,%.3f" % (arm.trace_t[i], arm.trace_ref[i], arm.trace_pos[i], arm.trace_u[i]))


def cmd_off(arm, args):
    arm.motor.coast()
    arm.servo.off()
    print("马达、舵机均已断开")


COMMANDS = {
    "help": cmd_help,
    "enc": cmd_enc,
    "zero": cmd_zero,
    "check": cmd_check,
    "duty": cmd_duty,
    "cal": cmd_cal,
    "speed": cmd_speed,
    "friction": cmd_friction,
    "rot": cmd_rot,
    "goto": cmd_goto,
    "bench": cmd_bench,
    "cycle": cmd_cycle,
    "grip": cmd_grip,
    "open": cmd_open,
    "close": cmd_close,
    "servo": cmd_servo,
    "set": cmd_set,
    "show": cmd_show,
    "trace": cmd_trace,
    "off": cmd_off,
}

HELP = """命令:
  check [占空比]        短暂正转, 检查马达/编码器方向 (首次上电先做这个)
  enc / zero            读编码器 / 当前位置清零
  cal                   手转一圈, 测每圈计数
  duty <u> [ms]         开环驱动 (u: -1~1, 默认 300ms) 后刹车
  speed [u] [ms]        测空载速度和时间常数 (v_full, tau)
  friction              测起转占空比 (kfs)
  rot <q> [tag]         机械手转 q*90 度 (q = 1, -1, 2, -2; 正 = 从舵机那头朝魔方看顺时针)
  goto <度>             转到绝对角度
  bench <q> [n] [tag]   来回转 n 次并统计; tag: free (空转) / load (夹着魔方拧一层)
  cycle [n] [q]         夹紧 -> 拧 -> 松开 -> 转回, 重复 n 次
  open / close          夹爪开 / 合
  grip [n]              开合 n 次 (观察舵机动作, 配合录像定 SERVO_MOVE_MS)
  servo <us> | off      舵机输出指定脉宽 (找开/合位置) / 停止脉冲
  set <参数> <值>       在线修改参数 (show 查看全部; hold = 到位后保持毫秒数)
  trace                 输出上一次动作的轨迹 CSV
  off                   马达、舵机全部断开
  quit                  退出"""

def main():
    arm = Arm()
    print("quadcuber 单臂测试。输入 help 查看命令。首次上电请先运行 check。")
    while True:
        try:
            line = input("arm> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not line:
            continue
        parts = line.split()
        name, args = parts[0], parts[1:]
        if name in ("quit", "exit", "q"):
            break
        fn = COMMANDS.get(name)
        if fn is None:
            print("未知命令, 输入 help 查看")
            continue
        try:
            fn(arm, args)
        except KeyboardInterrupt:
            arm.motor.coast()
            print("已中断, 马达断电")
        except Exception as e:  # noqa: BLE001 - 命令行里任何错误都不应让程序退出
            arm.motor.coast()
            print("错误:", e)
    arm.motor.coast()
    arm.servo.off()
    print("退出")


if __name__ == "__main__":
    main()
