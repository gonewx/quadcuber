"""DRV8833 单路马达驱动 + Geekservo 舵机。

DRV8833 采用 "慢衰减" 方式: 正转时 IN1 常高、IN2 输出 (1-占空比) 的 PWM;
PWM 关断期间两端短路刹车, 转速与占空比的关系比 "快衰减" 更接近线性, 低速也更好控制。

    IN1 IN2
     1   0   正转 (全速)
     0   1   反转 (全速)
     1   1   刹车 (两端短路)
     0   0   滑行 (高阻)

注意: DRV8833 模块的 nSLEEP (有的标 EEP/STBY) 必须接高电平才会工作, 很多模块板上已经上拉,
请对照模块说明确认。
"""

from machine import PWM, Pin

_FULL = 65535


class Motor:
    def __init__(self, in1, in2, invert=False, freq=20000):
        if invert:
            in1, in2 = in2, in1
        self._a = PWM(Pin(in1))
        self._b = PWM(Pin(in2))
        self._a.freq(freq)  # 同一个 slice, 设一次即可; 两个都设也无妨
        self._b.freq(freq)
        self.coast()

    def drive(self, u):
        """u 取 -1.0 ~ 1.0。"""
        if u > 1.0:
            u = 1.0
        elif u < -1.0:
            u = -1.0
        off = int((1.0 - abs(u)) * _FULL)
        if u >= 0:
            self._a.duty_u16(_FULL)
            self._b.duty_u16(off)
        else:
            self._a.duty_u16(off)
            self._b.duty_u16(_FULL)

    def brake(self):
        self._a.duty_u16(_FULL)
        self._b.duty_u16(_FULL)

    def coast(self):
        self._a.duty_u16(0)
        self._b.duty_u16(0)


class Servo:
    """Geekservo: 50Hz, 脉宽约 500~2500 微秒。"""

    def __init__(self, pin):
        # 启动只把信号脚拉低；首个显式 pulse 才创建 PWM，避免重用旧 PWM 占空比。
        self._pin = Pin(pin, Pin.OUT)
        self._pwm = None
        self.us = None
        self.off()

    def pulse(self, us):
        if type(us) is not int or not 500 <= us <= 2500:
            raise ValueError("舵机脉宽必须是 500..2500 内的整数，不能用截断代替校验")
        if self._pwm is None:
            self._pwm = PWM(self._pin)
            self._pwm.duty_u16(0)
            self._pwm.freq(50)
        self._pwm.duty_ns(us * 1000)
        self.us = us

    def off(self):
        """停止 PWM，不等于切断 5V，也不保证舵机释放保持力。"""
        if self._pwm is not None:
            self._pwm.duty_u16(0)
        self._pin.value(0)
        self.us = None
