"""在 CPython 里模拟 Pico 固件的运行环境, 用于测试 firmware/pico/ 下的代码。

提供假的 machine / rp2 / time 模块:
- rp2: 一个只支持本项目用到的指令的 PIO 解释器 (wait / jmp / mov / push / set),
  会真正执行 encoder.py 里的 PIO 程序, 以及通过 SMx_INSTR 插入的指令编码;
- machine: Pin / PWM / mem32, PWM 占空比被翻译成马达输入;
- time: 虚拟时钟, ticks_us 每次调用前进一点, sleep_ms 直接跳过。
马达用 tests/test_control.py 里的一阶模型, 位置变化被拆成逐个正交状态喂给 PIO。

这只能验证逻辑和指令编码 (按数据手册理解实现的解释器), 不能代替实物测试。
"""

import importlib
import os
import sys
import types

FIRMWARE = os.path.join(os.path.dirname(__file__), "..", "firmware", "pico")
FULL = 65535

# ---- PIO 解释器 ----------------------------------------------------------------


class _Program:
    def __init__(self, instrs, labels, wrap_target, wrap):
        self.instrs = instrs
        self.labels = labels
        self.wrap_target = wrap_target
        self.wrap = wrap


def asm_pio(**_kw):
    def deco(fn):
        instrs, labels = [], {}
        marks = {"wrap_target": 0, "wrap": None}
        g = dict(fn.__globals__)
        g.update(
            pin="pin",
            x_dec="x_dec",
            y_dec="y_dec",
            x="x",
            y="y",
            isr="isr",
            wrap_target=lambda: marks.__setitem__("wrap_target", len(instrs)),
            wrap=lambda: marks.__setitem__("wrap", len(instrs) - 1),
            label=lambda name: labels.__setitem__(name, len(instrs)),
            wait=lambda pol, src, idx: instrs.append(("wait", pol, src, idx)),
            jmp=lambda *a: instrs.append(("jmp",) + (a if len(a) == 2 else (None, a[0]))),
        )
        types.FunctionType(fn.__code__, g)()
        wrap = marks["wrap"] if marks["wrap"] is not None else len(instrs) - 1
        assert len(instrs) <= 32, "PIO 程序超过 32 条指令"
        return _Program(instrs, labels, marks["wrap_target"], wrap)

    return deco


class StateMachine:
    def __init__(self, sm_id, prog, freq=None, in_base=None, jmp_pin=None):
        self.id = sm_id
        self.prog = prog
        self.in_base = in_base
        self.jmp_pin = jmp_pin
        self.pc = 0
        self.x = 0
        self.y = 0
        self.isr = 0
        self.fifo = []
        self.enabled = False
        world.sms[_instr_addr(sm_id)] = self

    def active(self, v=None):
        if v is not None:
            self.enabled = bool(v)
        return self.enabled

    def rx_fifo(self):
        return len(self.fifo)

    def get(self):
        return self.fifo.pop(0)

    # 执行程序直到在 wait 上停住 (最多若干步, 防止死循环)
    def run(self):
        if not self.enabled:
            return
        for _ in range(100):
            op = self.prog.instrs[self.pc]
            nxt = self.pc + 1 if self.pc != self.prog.wrap else self.prog.wrap_target
            if op[0] == "wait":
                _, pol, _src, idx = op
                assert idx == 0
                if self.in_base.value() != pol:
                    return
                self.pc = nxt
            elif op[0] == "jmp":
                _, cond, target = op
                take = True
                if cond == "pin":
                    take = self.jmp_pin.value() == 1
                elif cond == "x_dec":
                    take = self.x != 0
                    self.x = (self.x - 1) & 0xFFFFFFFF
                elif cond == "y_dec":
                    take = self.y != 0
                    self.y = (self.y - 1) & 0xFFFFFFFF
                self.pc = self.prog.labels[target] if take else nxt
        raise AssertionError("PIO 程序没有停在 wait 上")

    # 通过 SMx_INSTR 插入的指令, 按 RP2040 数据手册的编码解析
    def exec_word(self, w):
        op = w >> 13
        if op == 0b101:  # MOV
            dest, src = (w >> 5) & 7, w & 7
            assert (w >> 3) & 3 == 0, "只支持无运算的 mov"
            val = {1: self.x, 2: self.y, 3: 0}[src]
            assert dest == 6, "只支持 mov isr, ..."
            self.isr = val
        elif op == 0b100:  # PUSH (bit7 = 0)
            assert (w >> 7) & 1 == 0 and (w >> 5) & 1 == 0, "只支持 push noblock"
            if len(self.fifo) < 4:
                self.fifo.append(self.isr)
            self.isr = 0
        elif op == 0b111:  # SET
            dest, data = (w >> 5) & 7, w & 31
            if dest == 1:
                self.x = data
            elif dest == 2:
                self.y = data
            else:
                raise AssertionError("不支持的 set 目标")
        else:
            raise AssertionError("不支持的插入指令 %04x" % w)


def _instr_addr(sm_id):
    return (0x50200000, 0x50300000)[sm_id // 4] + 0xD8 + 0x18 * (sm_id % 4)


# ---- machine ------------------------------------------------------------------


class Pin:
    IN = 0
    OUT = 1
    PULL_UP = 1

    def __init__(self, pid, mode=None, pull=None):
        self.id = pid
        world.pins.setdefault(pid, 1 if pull == Pin.PULL_UP else 0)

    def value(self, v=None):
        if v is not None:
            world.pins[self.id] = v
        return world.pins[self.id]


class PWM:
    def __init__(self, pin):
        self.pin = pin.id
        self.f = None
        world.pwm[self.pin] = 0

    def freq(self, f=None):
        if f is not None:
            self.f = f
        return self.f

    def duty_u16(self, v):
        world.sync()
        world.pwm[self.pin] = v

    def duty_ns(self, ns):
        world.servo_ns[self.pin] = ns
        world.pwm[self.pin] = int(ns / 20_000_000 * FULL)


class _Mem32:
    def __setitem__(self, addr, value):
        world.sync()
        world.sms[addr].exec_word(value)


# ---- 虚拟世界 -----------------------------------------------------------------

# 正转时 (A, B) 依次为 00 -> 10 -> 11 -> 01 (A 超前 B)
_QUAD = ((0, 0), (1, 0), (1, 1), (0, 1))


class World:
    def __init__(self):
        self.reset()

    def reset(self, motor=None, in1=2, in2=3, enc_a=4, enc_b=5, deg_per_count=0.5):
        self.now = 0
        self.last_sync = 0
        self.pins = {}
        self.pwm = {}
        self.servo_ns = {}
        self.sms = {}
        self.motor = motor
        self.in1, self.in2 = in1, in2
        self.enc_a, self.enc_b = enc_a, enc_b
        self.deg_per_count = deg_per_count
        self.count = 0  # 物理上的真实计数
        self.pins[enc_a], self.pins[enc_b] = _QUAD[0]

    def duty(self):
        a = self.pwm.get(self.in1, 0)
        b = self.pwm.get(self.in2, 0)
        if a == FULL and b == FULL:
            return 0.0  # 刹车
        if a == FULL:
            return 1.0 - b / FULL
        if b == FULL:
            return -(1.0 - a / FULL)
        return 0.0  # 滑行 (本模型不区分)

    def set_count(self, c):
        """逐个正交状态走到计数 c, 每一步都让 PIO 运行到停住。"""
        while self.count != c:
            self.count += 1 if c > self.count else -1
            a, b = _QUAD[self.count % 4]
            self.pins[self.enc_a] = a
            self.pins[self.enc_b] = b
            for sm in self.sms.values():
                sm.run()

    def sync(self):
        if self.motor is None:
            return
        dt = self.now - self.last_sync
        if dt <= 0:
            return
        self.last_sync = self.now
        u = self.duty()
        while dt > 0:
            step = min(dt, 1000)
            self.motor.advance(u, step / 1e6)
            dt -= step
            self.set_count(round(self.motor.pos / self.deg_per_count))

    # time 模块
    def ticks_us(self):
        self.now += 20
        return self.now

    def sleep_ms(self, ms):
        self.now += int(ms * 1000)


world = World()


def _module(name, **attrs):
    m = types.ModuleType(name)
    m.__dict__.update(attrs)
    return m


def load_firmware(*names):
    """在假环境里导入固件模块, 返回模块元组。每次调用都会重新导入。"""
    fake = {
        "machine": _module("machine", Pin=Pin, PWM=PWM, mem32=_Mem32()),
        "rp2": _module("rp2", asm_pio=asm_pio, StateMachine=StateMachine),
        "time": _module(
            "time",
            ticks_us=world.ticks_us,
            ticks_diff=lambda a, b: a - b,
            ticks_add=lambda a, b: a + b,
            sleep_ms=world.sleep_ms,
        ),
    }
    fw_names = ("config", "control", "encoder", "motor", "arm_test")
    saved = {k: sys.modules.get(k) for k in list(fake) + list(fw_names)}
    sys.path.insert(0, FIRMWARE)
    try:
        sys.modules.update(fake)
        for k in fw_names:
            sys.modules.pop(k, None)
        mods = tuple(importlib.import_module(n) for n in names)
    finally:
        sys.path.remove(FIRMWARE)
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v
    return mods
