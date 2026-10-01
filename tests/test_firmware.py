"""在模拟环境 (tests/pico_sim.py) 里运行 Pico 固件: PIO 编码器计数, 以及 arm_test 的各条命令。"""

import builtins
import contextlib
import io
import json
import random
import unittest

from tests import pico_sim
from tests.pico_sim import world
from tests.test_control import SimMotor


class EncoderTest(unittest.TestCase):
    def make(self, start_count=0, invert=False):
        world.reset()
        world.set_count(start_count)  # 此时还没有状态机, 只是设置引脚电平
        world.count = 0
        (encoder,) = pico_sim.load_firmware("encoder")
        return encoder.Encoder(4, 5, (0, 1), invert)

    def test_program_fits(self):
        (encoder,) = pico_sim.load_firmware("encoder")
        self.assertLessEqual(len(encoder._edge_counter.instrs), 32)

    def test_forward_backward(self):
        enc = self.make()
        world.set_count(1000)
        self.assertEqual(enc.count(), 1000)
        world.set_count(-37)
        self.assertEqual(enc.count(), -37)

    def test_start_with_phase_high(self):
        # 上电时 A 相为高, 状态机会多数一个边沿, 构造函数里的清零应把它吸收
        for start in (1, 2, 3):
            enc = self.make(start_count=start)
            self.assertEqual(enc.count(), 0, start)
            world.set_count(10)
            self.assertEqual(enc.count(), 10, start)

    def test_jitter_and_wraparound(self):
        enc = self.make()
        rng = random.Random(3)
        c = 0
        for _ in range(3000):
            c += rng.choice((-1, 1, 1))
            world.set_count(c)
        self.assertEqual(enc.count(), c)
        # 32 位寄存器回绕 (x/y 从 0 开始递减, 本身就在回绕)
        for sm in world.sms.values():
            self.assertGreater(sm.x, 1 << 31)

    def test_invert_and_zero(self):
        enc = self.make(invert=True)
        world.set_count(50)
        self.assertEqual(enc.count(), -50)
        enc.zero(90)
        world.set_count(40)
        self.assertEqual(enc.count(), 100)


class ArmTestCommands(unittest.TestCase):
    def setUp(self):
        world.reset(motor=SimMotor())
        (self.at,) = pico_sim.load_firmware("arm_test")
        self.arm = self.at.Arm()

    def run_cmd(self, line):
        name, *args = line.split()
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.at.COMMANDS[name](self.arm, args)
        return out.getvalue()

    def results(self, text, kind=None):
        rows = [json.loads(l[7:]) for l in text.splitlines() if l.startswith("RESULT ")]
        return [r for r in rows if kind is None or r["type"] == kind]

    def test_check_direction(self):
        self.assertIn("方向正确", self.run_cmd("check"))

    def test_check_reversed_encoder(self):
        world.motor.sign = -1
        self.assertIn("方向相反", self.run_cmd("check"))

    def test_rot_and_bench(self):
        out = self.run_cmd("rot 1")
        r = self.results(out, "move")[0]
        self.assertTrue(r["ok"], out)
        self.assertLessEqual(abs(r["err"]), 2.5)
        self.assertEqual(self.arm.nominal, 90)
        out = self.run_cmd("bench 1 6 load")
        rows = self.results(out, "move")
        self.assertEqual(len(rows), 6)
        self.assertTrue(all(r["ok"] and r["tag"] == "load" for r in rows))
        self.assertIn("成功 6/6", out)
        self.assertEqual(self.arm.nominal, 90)  # 来回偶数次, 回到起点

    def test_cycle(self):
        out = self.run_cmd("cycle 3")
        self.assertEqual(len(self.results(out, "cycle")), 3)
        tags = [r["tag"] for r in self.results(out, "move")]
        self.assertEqual(tags, ["load", "free"] * 3)
        close_ns = self.at.config.SERVO_CLOSE_US * 1000
        open_ns = self.at.config.SERVO_OPEN_US * 1000
        self.assertEqual(world.servo_ns[self.at.config.SERVO], open_ns)
        self.assertNotEqual(close_ns, open_ns)

    def test_speed_and_friction(self):
        out = self.run_cmd("speed")
        r = self.results(out, "speed")[0]
        # 模型马达: 1000 * (1 - 0.08) 度/秒; 结果按机械手换算, 要除以齿轮比
        self.assertAlmostEqual(r["v_ss"], 920 / self.at.config.GEAR_RATIO, delta=30 / self.at.config.GEAR_RATIO)
        self.assertAlmostEqual(r["tau"], 0.05, delta=0.015)
        out = self.run_cmd("friction")
        r = self.results(out, "friction")[0]
        self.assertAlmostEqual(r["pos"], 0.085, delta=0.02)
        self.assertAlmostEqual(r["neg"], 0.085, delta=0.02)

    def test_stall_reported(self):
        world.motor.locked = True
        out = self.run_cmd("rot 1")
        r = self.results(out, "move")[0]
        self.assertFalse(r["ok"])
        self.assertIn("动作失败", out)
        self.assertEqual(world.duty(), 0.0)
        self.assertEqual(self.arm.nominal, 0)

    def test_misc_commands(self):
        self.run_cmd("set kp 0.05")
        self.assertEqual(self.arm.gains.kp, 0.05)
        self.assertIn("kp", self.run_cmd("show"))
        self.run_cmd("goto 45")
        self.assertIn("TRACE", self.run_cmd("trace"))
        self.assertIn("机械手", self.run_cmd("enc"))
        self.run_cmd("zero")
        self.assertIn("转了", self.run_cmd("duty 0.3 100"))
        self.run_cmd("grip 1")
        self.run_cmd("servo 1500")
        self.assertEqual(world.servo_ns[self.at.config.SERVO], 1_500_000)
        self.run_cmd("off")
        self.assertEqual(world.pwm[self.at.config.SERVO], 0)

    def test_cal(self):
        # 手转方向可正可负；显示保留编码器符号，标定圈数使用绝对值。
        orig = builtins.input
        encoder_sign = -1 if self.at.config.ENC_INVERT else 1
        try:
            for delta in (720, -720):
                with self.subTest(delta=delta):
                    builtins.input = lambda prompt="": world.set_count(world.count + delta)
                    out = self.run_cmd("cal")
                    self.assertIn("机械手一圈 = %d 计数" % (delta * encoder_sign), out)
                    self.assertIn("COUNTS_PER_MOTOR_REV 应为 %.1f" %
                                  (abs(delta) / self.at.config.GEAR_RATIO), out)
        finally:
            builtins.input = orig

    def test_main_loop(self):
        lines = iter(["help", "bogus", "rot 1", "set nope 1", "quit"])
        orig = builtins.input
        builtins.input = lambda prompt="": next(lines)
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                self.at.main()
        finally:
            builtins.input = orig
        text = out.getvalue()
        self.assertIn("未知命令", text)
        self.assertIn("错误", text)
        self.assertIn("退出", text)


if __name__ == "__main__":
    unittest.main()
