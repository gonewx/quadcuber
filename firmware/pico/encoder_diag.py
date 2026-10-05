"""手转编码器诊断：同时比较 GPIO 正交序列和项目 PIO 计数。

仅适用于 RP2040、GP4/GP5。保持已验证的分压接线，VM 不供电。
软重启后执行 import encoder_diag; encoder_diag.main()。
不初始化马达或舵机；GPIO 轮询只用于低速诊断，不代替最终 PIO 控制。
"""
from machine import mem32
import time
from encoder import Encoder

# RP2040 SIO GPIO_IN；一次读取两脚，避免分开读取时碰到边沿。
GPIO_IN = 0xD0000004
# 状态最低位为 GP4，次低位为 GP5。符号仅供比较反转前后。
STEP = (0, 1, -1, 0, -1, 0, 0, 1, 1, 0, 0, -1, 0, -1, 1, 0)


def capture(enc, seconds=5):
    plus = minus = bad = a = b = 0
    c0 = enc.count()
    old = (mem32[GPIO_IN] >> 4) & 3
    end = time.ticks_add(time.ticks_ms(), seconds * 1000)
    while time.ticks_diff(end, time.ticks_ms()) > 0:
        new = (mem32[GPIO_IN] >> 4) & 3
        changed = old ^ new
        if changed:
            if changed & 1:
                a += 1
            if changed & 2:
                b += 1
            if changed == 3:
                bad += 1
            else:
                step = STEP[(old << 2) | new]
                if step > 0:
                    plus += 1
                elif step < 0:
                    minus += 1
            old = new
    c1 = enc.count()
    print("A=%d B=%d plus=%d minus=%d bad=%d PIO_delta=%d" %
          (a, b, plus, minus, bad, c1 - c0))


def main():
    enc = Encoder(4, 5, (0, 1), pull_up=False)
    try:
        print("只手动转轴，VM 保持不供电；每段采样5秒。")
        for label in ("保持轴不动", "朝一个方向缓慢连续转", "朝相反方向缓慢连续转"):
            input(label + "：准备好按回车，看到开始后操作 > ")
            print("开始：" + label)
            capture(enc)
            print("本段结束，停下转轴。")
    finally:
        # 本模块是一次性诊断，退出时释放两个状态机；重试前仍建议软重启。
        for sm in enc._sms:
            sm.active(0)
