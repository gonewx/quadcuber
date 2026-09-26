"""Pico 位置控制算法 (firmware/pico/control.py) 的仿真测试。

用一阶直流马达模型 (含静摩擦、编码器量化、循环周期抖动) 代替实物。
模型参数只是大致量级, 目的是检查算法逻辑 (到位判定、堵转/失控保护), 不代表实物性能。
"""

import importlib.util
import os
import random
import unittest

_PATH = os.path.join(os.path.dirname(__file__), "..", "firmware", "pico", "control.py")
_spec = importlib.util.spec_from_file_location("pico_control", _PATH)
control = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(control)


class SimMotor:
    """ω' = (v_full * u_eff - ω) / tau; |u| 小于静摩擦时不动。角度单位: 机械手度。"""

    def __init__(self, v_full=1000.0, tau=0.05, friction=0.08, deg_per_count=0.5, sign=1, locked=False):
        self.v_full = v_full
        self.tau = tau
        self.friction = friction
        self.q = deg_per_count
        self.sign = sign  # -1 表示马达接反
        self.locked = locked
        self.pos = 0.0
        self.w = 0.0

    def advance(self, u, dt):
        u *= self.sign
        if self.locked:
            self.w = 0.0
            return
        if abs(u) <= self.friction and abs(self.w) < 1.0:
            self.w = 0.0
        else:
            u_eff = u - self.friction * (1 if u > 0 else -1) if abs(u) > self.friction else 0.0
            n = 10
            for _ in range(n):
                self.w += (self.v_full * u_eff - self.w) / self.tau * (dt / n)
                self.pos += self.w * (dt / n)

    def read(self):
        return round(self.pos / self.q) * self.q


def run_move(motor, target, gains=None, hold=0.1, jitter=True, seed=0):
    rng = random.Random(seed)
    gains = gains or control.Gains()
    t = 0
    mc = control.MoveController(motor.read(), target, gains, t)
    done_at = None
    while t < 3_000_000:
        u = mc.step(t, motor.read())
        dt = 1000
        if jitter and rng.random() < 0.02:
            dt = 3000  # 偶尔的 GC 停顿
        motor.advance(u, dt / 1e6)
        t += dt
        if mc.state in control.FAILED:
            break
        if mc.state == control.DONE:
            done_at = done_at or t
            if t - done_at >= hold * 1e6:
                break
    return mc


class TrapezoidTest(unittest.TestCase):
    def test_reaches_target_with_limits(self):
        for dist, vmax, amax in ((90, 600, 6000), (-180, 600, 6000), (10, 600, 6000)):
            prof = control.Trapezoid(0.0, dist, vmax, amax)
            p, v, a = prof.at(prof.duration)
            self.assertAlmostEqual(p, dist)
            prev = 0.0
            steps = 200
            for i in range(steps + 1):
                p, v, a = prof.at(prof.duration * i / steps)
                self.assertLessEqual(abs(v), vmax + 1e-6)
                self.assertLessEqual(abs(a), amax + 1e-6)
                self.assertGreaterEqual((p - prev) * (1 if dist > 0 else -1), -1e-9)  # 单调
                prev = p

    def test_triangle_profile_duration(self):
        prof = control.Trapezoid(0.0, 10.0, 600, 6000)
        self.assertEqual(prof.tc, 0.0)
        self.assertAlmostEqual(prof.duration, 2 * (10 / 6000) ** 0.5)


class MoveTest(unittest.TestCase):
    def test_quarter_turn_both_directions(self):
        for target in (90.0, -90.0, 180.0):
            motor = SimMotor()
            mc = run_move(motor, target)
            self.assertEqual(mc.state, control.DONE, target)
            self.assertLessEqual(abs(motor.pos - target), control.Gains().tol + 0.5)
            self.assertLess(mc.overshoot, 5.0)
            self.assertLess(mc.t_settle, mc.prof.duration + 0.1)

    def test_model_mismatch(self):
        # 前馈参数与实物差 25%, 仍应到位
        for v_full, tau in ((750.0, 0.07), (1250.0, 0.035)):
            motor = SimMotor(v_full=v_full, tau=tau, friction=0.12)
            mc = run_move(motor, 90.0)
            self.assertEqual(mc.state, control.DONE, (v_full, tau))

    def test_stall_detected(self):
        motor = SimMotor(locked=True)
        mc = run_move(motor, 90.0)
        self.assertIn(mc.state, (control.STALL, control.RUNAWAY))
        self.assertEqual(mc.step(10**7, motor.read()), 0.0)

    def test_reversed_motor_stops(self):
        motor = SimMotor(sign=-1)
        mc = run_move(motor, 90.0)
        self.assertIn(mc.state, control.FAILED)
        self.assertLess(abs(motor.pos), 90.0)  # 没有一直转下去

    def test_gains_set(self):
        g = control.Gains(kp=0.05)
        self.assertEqual(g.kp, 0.05)
        with self.assertRaises(KeyError):
            g.set("nope", 1)


class VelocityTest(unittest.TestCase):
    def test_constant_speed(self):
        est = control.VelocityEstimator()
        v = 0.0
        for i in range(20):
            v = est.update(i * 1000, i * 0.5)
        self.assertAlmostEqual(v, 500.0)


if __name__ == "__main__":
    unittest.main()
