"""用 PIO 读 EV3 马达的正交编码器 (4 倍频)。

做法: 每个编码器用两个 PIO 状态机, 一个数 A 相的边沿 (用 B 相判断方向), 另一个数 B 相的边沿
(用 A 相判断方向), 两者相减就是 4 倍频计数。计数完全在 PIO 里完成, 不占 CPU, 也不会因为
Python 忙而丢步。

每个状态机用 X、Y 两个寄存器分别记录 "减" 和 "加" 的次数, 每次计数都是一条 jmp x--/y-- 指令,
所以读的时候不会读到加了一半的值。读数时通过 SMx_INSTR 寄存器插入 "mov isr, x; push" 指令,
把寄存器值推到 FIFO 里再取出 (比 sm.exec() 快, 后者每次都要汇编字符串)。

注意: 本文件尚未在实物上验证。
"""

import rp2
from machine import Pin, mem32

# SMx_INSTR 寄存器地址: PIO0 基址 0x50200000, PIO1 基址 0x50300000,
# SM0_INSTR 偏移 0xd8, 每个状态机间隔 0x18 (RP2040 数据手册 3.7 节)
_PIO_BASE = (0x50200000, 0x50300000)

# 预先编码好的指令 (RP2040 数据手册 3.4 节)
_MOV_ISR_X = 0xA0C1  # mov isr, x
_MOV_ISR_Y = 0xA0C2  # mov isr, y
_PUSH = 0x8000  # push noblock
_SET_X0 = 0xE020  # set x, 0
_SET_Y0 = 0xE040  # set y, 0


@rp2.asm_pio()
def _edge_counter():
    # in_base = 本相, jmp_pin = 另一相。按 "A 超前 B 为正转" 的规则:
    #   本相上升沿时另一相为低 -> +1 (y--), 为高 -> -1 (x--)
    #   本相下降沿时另一相为高 -> +1 (y--), 为低 -> -1 (x--)
    # jmp x--/y-- 无论是否跳转都会减 1, 所以两个分支都指向同一个下一步。
    wrap_target()
    label("rise")
    wait(1, pin, 0)
    jmp(pin, "rise_hi")
    jmp(y_dec, "fall")
    label("fall")
    wait(0, pin, 0)
    jmp(pin, "fall_hi")
    jmp(x_dec, "rise")
    jmp("rise")
    label("rise_hi")
    jmp(x_dec, "fall")
    jmp("fall")
    label("fall_hi")
    jmp(y_dec, "rise")
    wrap()


class Encoder:
    def __init__(self, pin_a, pin_b, sm_ids, invert=False, freq=10_000_000):
        a = Pin(pin_a, Pin.IN, Pin.PULL_UP)
        b = Pin(pin_b, Pin.IN, Pin.PULL_UP)
        self._sms = []
        self._instr = []
        for sm_id, (base, other) in zip(sm_ids, ((a, b), (b, a))):
            sm = rp2.StateMachine(sm_id, _edge_counter, freq=freq, in_base=base, jmp_pin=other)
            self._instr.append(_PIO_BASE[sm_id // 4] + 0xD8 + 0x18 * (sm_id % 4))
            self._sms.append(sm)
        for sm, addr in zip(self._sms, self._instr):
            mem32[addr] = _SET_X0
            mem32[addr] = _SET_Y0
            while sm.rx_fifo():
                sm.get()
            sm.active(1)
        self._sign = -1 if invert else 1
        self._offset = 0
        # 状态机刚启动时, 如果本相已经是高电平, 会多数一个 "上升沿"; 清零把它吸收掉
        self.zero()

    def _raw_one(self, sm, addr):
        mem32[addr] = _MOV_ISR_X
        mem32[addr] = _PUSH
        mem32[addr] = _MOV_ISR_Y
        mem32[addr] = _PUSH
        x = sm.get()
        y = sm.get()
        # x = -(减的次数), y = -(加的次数), 所以 加-减 = x - y
        v = (x - y) & 0xFFFFFFFF
        return v - 0x100000000 if v & 0x80000000 else v

    def raw(self):
        """4 倍频累计计数 (A 相边沿计数 - B 相边沿计数, 后者的方向规则正好相反)。"""
        a = self._raw_one(self._sms[0], self._instr[0])
        b = self._raw_one(self._sms[1], self._instr[1])
        return a - b

    def count(self):
        return self._sign * (self.raw() - self._offset)

    def zero(self, count=0):
        """把当前位置设为 count。"""
        self._offset = self.raw() - self._sign * count
