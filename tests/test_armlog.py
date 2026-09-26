import contextlib
import io
import json
import os
import tempfile
import unittest

from quadcuber import armlog
from quadcuber.__main__ import main
from quadcuber.machine import Timing
from tests import pico_sim
from tests.pico_sim import world
from tests.test_control import SimMotor


def simulated_log():
    """用模拟环境跑一遍测试程序, 返回串口输出。"""
    world.reset(motor=SimMotor())
    (at,) = pico_sim.load_firmware("arm_test")
    arm = at.Arm()
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        for line in ("bench 1 6 free", "bench 2 4 free", "bench 1 6 load", "grip 1", "cycle 2"):
            name, *args = line.split()
            print("arm> " + line)
            at.COMMANDS[name](arm, args)
        world.motor.locked = True
        at.COMMANDS["rot"](arm, ["1", "load"])  # 一次失败的动作
    return out.getvalue()


class ArmLogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.log = simulated_log()
        cls.results = armlog.parse_results(cls.log.splitlines() + ["RESULT {broken", "garbage"])

    def test_groups(self):
        groups = armlog.group_moves(self.results)
        self.assertEqual(set(groups), {("free", 1), ("free", 2), ("load", 1)})
        self.assertEqual(groups[("free", 1)].ok, 8)  # bench 6 次 + cycle 2 次
        load = groups[("load", 1)]
        self.assertEqual((load.ok, load.total), (8, 9))
        self.assertEqual(sum(load.failures.values()), 1)

    def test_suggest_timing(self):
        base = Timing()
        t, notes = armlog.suggest_timing(self.results, base)
        groups = armlog.group_moves(self.results)
        self.assertAlmostEqual(t.rotate90, groups[("free", 1)].mean, places=3)
        self.assertAlmostEqual(t.turn90, groups[("load", 1)].mean, places=3)
        self.assertGreater(t.rotate180, t.rotate90)
        self.assertEqual(t.turn180, base.turn180)  # 没测
        self.assertEqual(t.cube90, base.cube90)
        self.assertTrue(any("turn180" in n for n in notes))

    def test_report(self):
        text = armlog.report(self.results)
        self.assertIn("load 90°", text)
        self.assertIn("循环: 2 次", text)

    def test_cli_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            log = os.path.join(d, "arm.log")
            out = os.path.join(d, "timing.json")
            with open(log, "w", encoding="utf-8") as f:
                f.write(self.log)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["armlog", log, "-o", out]), 0)
                with open(out, encoding="utf-8") as f:
                    Timing.from_dict(json.load(f))
                # 生成的文件能直接给规划器用
                self.assertEqual(main(["bench", "--count", "2", "--length", "8", "--timing", out]), 0)


if __name__ == "__main__":
    unittest.main()
