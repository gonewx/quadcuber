"""验证电路构建能发现断线、短接、配置漂移及未更新的图纸。"""
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
import runpy
import json
import hashlib
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

    def test_r_geometry_and_netlist_unchanged(self):
        baseline = json.loads((Path(__file__).parent / 'fixtures/direct-breadboard-r.json').read_text())
        self.assertEqual(json.loads(json.dumps(direct_wiring.WIRES)), baseline['wires'])
        self.assertEqual([list(r) for r in direct_wiring.RESISTORS], baseline['resistors'])
        self.assertEqual(hashlib.sha256(json.dumps(direct_wiring.P, sort_keys=True).encode()).hexdigest(),
                         '6dff300acf2a852d182373d6009a2349d5d151bcf5ed3c69e93db242ce7a917e')

    def test_rl_downloads_preserve_r_and_add_isolated_l(self):
        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(StringIO()):
            direct_wiring.main(tmp)
            directory = Path(tmp)
            target = directory / 'direct-breadboard-rl-netlist.json'
            self.assertTrue(target.exists(), '缺少 R+L 网络表下载')
            r_file = directory / 'direct-breadboard-netlist.json'
            self.assertEqual(r_file.read_bytes(),
                             (Path(__file__).parent / 'fixtures/direct-breadboard-r.json').read_bytes())
            r = json.loads(r_file.read_text())
            rl = json.loads(target.read_text())
            self.assertEqual(rl['wires'][:25], r['wires'])
            self.assertEqual(rl['resistors'][:4], r['resistors'])
            self.assertEqual((len(rl['wires']), len(rl['resistors'])), (38, 8))
            self.assertIn('尚未确认', rl['precondition'])
            self.assertIn('ARM_ID', rl['precondition'])
            svg = (directory / 'direct-breadboard-rl.svg').read_text()
            self.assertEqual(svg.count('data-wire='), 38)
            self.assertIn('健康', svg)
            self.assertIn('单臂', svg)

    def prepare_l(self):
        self.setUp()
        direct_wiring.make_l_parts()
        direct_wiring.make_l_wires()

    def test_l_pins_and_physical_occupancy(self):
        self.prepare_l()
        direct_wiring.validate('RL')
        expected = {
            'LC01': ('BB.j11', 'DRV.BIN1'), 'LC02': ('BB.j12', 'DRV.BIN2'),
            'LM01': ('DRV.BO1', 'L.EV3.1'), 'LM02': ('DRV.BO2', 'L.EV3.2'),
            'LE01': ('L.EV3.3', 'BB.-39'), 'LE02': ('L.EV3.4', 'BB.+39'),
            'LE03': ('L.EV3.5', 'BB.h37'), 'LE04': ('L.EV3.6', 'BB.h40'),
            'LE05': ('BB.i34', 'BB.i18'), 'LE06': ('BB.i36', 'BB.i19'),
            'LS01': ('BUCK.OUT+', 'L.SERVO.V+'), 'LS02': ('BUCK.OUT−', 'L.SERVO.GND'),
            'LS03': ('BB.j14', 'L.SERVO.SIG'),
        }
        actual = {w['code']: (w['start'], w['end']) for w in direct_wiring.WIRES if w['code'].startswith('L')}
        self.assertEqual(actual, expected)
        used = [f'BB.{row}{col}' for row in ('c', 'h') for col in range(3, 23)]
        used += [w[k] for w in direct_wiring.WIRES for k in ('start', 'end') if w[k].startswith('BB.')]
        used += [pin for _, a, b, _ in direct_wiring.resistors_for('RL') for pin in (a, b)]
        self.assertEqual(len(used), 91)
        self.assertEqual(len(used), len(set(used)))

    def test_reject_each_missing_l_wire(self):
        self.prepare_l()
        codes = [w['code'] for w in direct_wiring.WIRES if w['code'].startswith('L')]
        for code in codes:
            with self.subTest(code=code):
                self.prepare_l()
                direct_wiring.WIRES[:] = [w for w in direct_wiring.WIRES if w['code'] != code]
                with self.assertRaises(AssertionError):
                    direct_wiring.validate('RL')

    def test_reject_encoder_crosslinks_and_rail_shorts(self):
        # 四个输入和四个分压点都不能直连电源、地或另一输入/分压点。
        nodes = ['BB.f33', 'BB.g31', 'BB.f26', 'BB.g28',
                 'BB.f37', 'BB.g40', 'BB.f34', 'BB.g36']
        from itertools import combinations
        pairs = list(combinations(nodes, 2)) + [(n, rail) for n in nodes for rail in ('BB.+1', 'BB.G1')]
        for a, b in pairs:
            with self.subTest(a=a, b=b):
                self.prepare_l()
                direct_wiring.wire('BAD', 'encoder', a, b)
                with self.assertRaisesRegex(AssertionError, '短接'):
                    direct_wiring.validate('RL')

    def test_reject_l_servo_power_via_r_or_breadboard(self):
        for code, source in [('LS01', 'SERVO.V+'), ('LS01', 'BB.+1'),
                             ('LS02', 'SERVO.GND'), ('LS02', 'BB.G1')]:
            with self.subTest(code=code, source=source):
                self.prepare_l()
                next(w for w in direct_wiring.WIRES if w['code'] == code)['start'] = source
                with self.assertRaisesRegex(AssertionError, '独立直连'):
                    direct_wiring.validate('RL')

    def test_reject_l_wrong_gpio_resistor_and_occupied_hole(self):
        for code, field, wrong in [('LC01', 'start', 'BB.j10'), ('LC02', 'start', 'BB.j14'),
                                   ('LE05', 'end', 'BB.i19'), ('LE06', 'end', 'BB.i18'),
                                   ('LS03', 'start', 'BB.j15'), ('LE05', 'end', 'BB.h18')]:
            with self.subTest(code=code, wrong=wrong):
                self.prepare_l()
                next(w for w in direct_wiring.WIRES if w['code'] == code)[field] = wrong
                with self.assertRaises(AssertionError):
                    direct_wiring.validate('RL')
        self.prepare_l()
        for index in range(4):
            changed = list(direct_wiring.L_RESISTORS)
            name, a, b, value = changed[index]
            changed[index] = (name, a, b, 20000 if value == 10000 else 10000)
            with self.subTest(resistor=name), patch.object(direct_wiring, 'L_RESISTORS', changed):
                with self.assertRaisesRegex(AssertionError, '分压电阻'):
                    direct_wiring.validate('RL')
        with patch.dict(spec.ARMS, L=((6, 7), (14, 15), (9,), (2, 3))):
            with self.assertRaisesRegex(AssertionError, 'L 臂分配'):
                direct_wiring.validate('RL')

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
