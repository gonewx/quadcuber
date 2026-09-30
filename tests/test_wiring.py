"""验证电路构建能发现断线、短接、配置漂移及未更新的图纸。"""
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch

WIRING = Path(__file__).resolve().parents[1] / 'docs/wiring'
sys.path.insert(0, str(WIRING))
try:
    import build as wiring_build
    import direct_wiring
    import perfboard_layout
    import spec
finally:
    sys.path.pop(0)


class WiringTest(unittest.TestCase):
    def setUp(self):
        direct_wiring.P.clear()
        direct_wiring.PARTS.clear()
        direct_wiring.WIRES.clear()
        direct_wiring.make_parts()
        direct_wiring.make_wires()

    def test_existing_networks(self):
        spec.validate()
        direct_wiring.validate()
        perfboard_layout.validate()

    def test_reject_firmware_drift(self):
        config = runpy.run_path(str(spec.ROOT / 'firmware/pico/config.py'))
        for key, value in [('ENC_A', 12), ('ENC_PULLUP', True), ('ENC_SM', (2, 3))]:
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, key):
                spec.validate(dict(config, **{key: value}))

    def test_reject_pwm_alias(self):
        # GP25 与 L 臂 GP9 是同一 PWM 通道，但不重复占用 GPIO。
        with patch.dict(spec.ARMS, B=((14, 15), (18, 19), (25,), (6, 7))):
            with self.assertRaisesRegex(ValueError, 'PWM'):
                spec.validate()

    def test_reject_missing_ground(self):
        direct_wiring.WIRES[:] = [w for w in direct_wiring.WIRES if w['code'] != 'P10']
        with self.assertRaises(AssertionError):
            direct_wiring.validate()

    def test_reject_bypassed_divider(self):
        direct_wiring.wire('BAD', 'encoder', 'BB.i33', 'BB.j8')
        with self.assertRaisesRegex(AssertionError, '短接'):
            direct_wiring.validate()

    def test_reject_occupied_pico_hole(self):
        # c5 与 a5 电气等价，但 c5 已被 Pico 占用。
        wire = next(w for w in direct_wiring.WIRES if w['code'] == 'G01')
        wire['start'] = 'BB.c5'
        with self.assertRaisesRegex(AssertionError, '占用'):
            direct_wiring.validate()

    def test_reject_servo_power_via_breadboard(self):
        wire = next(w for w in direct_wiring.WIRES if w['code'] == 'S01')
        wire['start'] = 'BB.+39'
        with self.assertRaisesRegex(AssertionError, '独立直连'):
            direct_wiring.validate()

    def test_reject_buck_ground_via_driver(self):
        wire = next(w for w in direct_wiring.WIRES if w['code'] == 'P04')
        wire['start'] = 'DRV.GND-L2'
        with self.assertRaisesRegex(AssertionError, '独立直连'):
            direct_wiring.validate()

    def test_reject_missing_servo_signal(self):
        direct_wiring.WIRES[:] = [w for w in direct_wiring.WIRES if w['code'] != 'S03']
        with self.assertRaises(AssertionError):
            direct_wiring.validate()

    def test_reject_perfboard_short(self):
        bad = ('BAD', '9V', 'J1.1', 'J1.2', [], '意外短路')
        with patch.object(perfboard_layout, 'WIRES', perfboard_layout.WIRES + [bad]):
            with self.assertRaisesRegex(AssertionError, '网络错误'):
                perfboard_layout.validate()

    def test_build_is_repeatable_and_check_is_read_only(self):
        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(StringIO()):
            directory = Path(tmp) / 'docs/wiring'
            wiring_build.build(directory)
            snapshot = {p: p.read_bytes() for p in directory.parent.rglob('*') if p.is_file()}
            wiring_build.build(directory)
            self.assertEqual(snapshot, {p: p.read_bytes() for p in snapshot})
            with patch.object(wiring_build, 'HERE', directory):
                self.assertEqual(wiring_build.check(), 0)
                page = directory / 'index.html'
                page.write_text('过期页面', encoding='utf-8')
                self.assertEqual(wiring_build.check(), 1)
                self.assertEqual(page.read_text(encoding='utf-8'), '过期页面')
                page.unlink()
                self.assertEqual(wiring_build.check(), 1)
                self.assertFalse(page.exists())
