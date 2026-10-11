"""Device settings survive conversion without executing backup Python."""
import copy
import importlib
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch
from tests import pico_sim
from tests.pico_sim import world

ROOT = Path(__file__).resolve().parents[1]


class ConfigMigrationTest(unittest.TestCase):
    def setUp(self):
        self.tool = importlib.import_module('tools.migrate_arm_config')
        self.arms = runpy.run_path(str(ROOT / 'firmware/pico/config.py'))['ARMS']
        self.r = copy.deepcopy(self.arms['R'])
        self.r.update(SERVO_OPEN_US=1777, SERVO_CALIBRATED=True,
                      SERVO_CALIBRATION_ARM='R', MOTOR_INVERT=True,
                      USER_NOTE={'custom': [None, False, (3, 4)]})
        self.r['GAINS']['vmax'] = 193.25
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / 'backup.py'
        self.output = Path(self.temp.name) / 'converted.py'
        self.source.write_text(''.join('%s = %r\n' % item for item in self.r.items()))

    def test_preserves_all_device_r_values_and_creates_uncalibrated_l(self):
        before = self.source.read_bytes()
        self.tool.migrate(self.source, self.output)
        arms = self.tool.read_settings(self.output)['ARMS']
        self.assertEqual(arms['R'], self.r)
        self.assertEqual(arms['L'], self.arms['L'])
        self.assertIsNone(arms['L']['SERVO_OPEN_US'])
        self.assertFalse(arms['L']['SERVO_CALIBRATED'])
        self.assertEqual(before, self.source.read_bytes())
        self.tool.verify(self.source, self.output)

    def test_migrated_calibrated_r_boots_without_pulses_and_l_stays_locked(self):
        from types import SimpleNamespace
        self.r.update(SERVO_MIN_US=1400, SERVO_MAX_US=1900,
                      SERVO_CALIBRATION_PROFILE='v4', SERVO_MOVE_MS=250,
                      SERVO_TIMING_CONFIRMED=True)
        self.source.write_text(''.join('%s = %r\n' % item for item in self.r.items()))
        self.tool.migrate(self.source, self.output)
        world.reset()
        at, profiles = pico_sim.load_firmware('arm_test', 'arm_profiles')
        with patch.object(profiles, 'config', SimpleNamespace(**self.tool.read_settings(self.output))):
            arm = at.Arm()
            self.assertEqual(arm.config.SERVO_OPEN_US, 1777)
            self.assertTrue(arm.config.SERVO_CALIBRATED)
            self.assertFalse(world.servo_ns)
            arm.select('L')
            with self.assertRaises(ValueError): arm.grip(True)
            arm.select('R')
            self.assertFalse(world.servo_ns)
            self.assertEqual(arm.config.SERVO_MOVE_MS, 250)
            arm.close()

    def test_never_overwrites_existing_output_or_source(self):
        self.output.write_text('keep me')
        with self.assertRaises(FileExistsError): self.tool.migrate(self.source, self.output)
        self.assertEqual(self.output.read_text(), 'keep me')
        with self.assertRaises(FileExistsError): self.tool.migrate(self.source, self.source)

    def test_rejects_executable_ambiguous_or_incomplete_input_without_output(self):
        for bad in ['import os\n', 'VALUE = 1 + 2\n', 'VALUE = 1\nVALUE = 2\n',
                    'VALUE = {"x": 1, "x": 2}\n', 'MOTOR_IN1 = 2\n']:
            with self.subTest(bad=bad):
                self.source.write_text(bad)
                with self.assertRaises(ValueError): self.tool.migrate(self.source, self.output)
                self.assertFalse(self.output.exists())

    def test_verify_detects_changed_r_and_changed_l(self):
        self.tool.migrate(self.source, self.output)
        original = self.output.read_text()
        for old, new in [("1777", "1778"), ("'SERVO_OPEN_US': None", "'SERVO_OPEN_US': 1500")]:
            self.output.write_text(original.replace(old, new))
            with self.assertRaises(ValueError): self.tool.verify(self.source, self.output)

    def test_atomic_write_failure_preserves_backup_and_leaves_no_output(self):
        before = self.source.read_bytes()
        with patch.object(self.tool.os, 'link', side_effect=OSError('simulated failure')):
            with self.assertRaises(OSError): self.tool.migrate(self.source, self.output)
        self.assertEqual(self.source.read_bytes(), before)
        self.assertEqual(list(self.source.parent.iterdir()), [self.source])

    def test_grouped_input_is_not_migrated_again(self):
        self.source.write_text('ARMS = %r\n' % self.arms)
        with self.assertRaises(ValueError): self.tool.migrate(self.source, self.output)
        self.assertFalse(self.output.exists())


class GroupedConfigTest(unittest.TestCase):
    def setUp(self):
        world.reset()
        self.at, self.profiles = pico_sim.load_firmware('arm_test', 'arm_profiles')

    def test_single_file_and_separate_group_values(self):
        self.assertFalse((ROOT / 'firmware/pico/config_l.py').exists())
        groups = self.profiles.config.ARMS
        self.assertIsNot(groups['R']['GAINS'], groups['L']['GAINS'])
        groups['L']['GAINS']['vmax'] = 99
        groups['L']['SERVO_OPEN_US'] = 1601
        arm = self.at.Arm()
        self.assertEqual(arm.config.SERVO_OPEN_US, 1700)
        self.assertEqual(arm.gains.vmax, 240)
        arm.select('L')
        self.assertEqual(arm.config.SERVO_OPEN_US, 1601)
        self.assertEqual(arm.gains.vmax, 99)
        self.assertFalse(world.servo_ns)
        arm.close()

    def test_legacy_r_is_unchanged_and_l_selection_stops(self):
        from types import SimpleNamespace
        legacy = SimpleNamespace(**copy.deepcopy(self.profiles.config.ARMS['R']))
        legacy.SERVO_OPEN_US = 1789
        with patch.object(self.profiles, 'config', legacy):
            arm = self.at.Arm()
            self.assertIs(arm.config, legacy)
            arm.motor.drive(.2)
            arm._motor_test = True
            with self.assertRaisesRegex(ValueError, '迁移'): arm.select('L')
            self.assertFalse(arm._ready)
            self.assertFalse(arm._motor_test)
            self.assertTrue(all(v == 0 for v in world.pwm.values()))
            arm.select('R')
            self.assertEqual(arm.config.SERVO_OPEN_US, 1789)
            self.assertFalse(world.servo_ns)
            arm.close()

    def test_shared_gains_or_groups_are_rejected_after_stopping(self):
        groups = self.profiles.config.ARMS
        arm = self.at.Arm()
        arm.motor.drive(.2)
        original = groups['L']['GAINS']
        groups['L']['GAINS'] = groups['R']['GAINS']
        with self.assertRaises(ValueError): arm.select('L')
        self.assertFalse(arm._ready)
        self.assertTrue(all(v == 0 for v in world.pwm.values()))
        groups['L']['GAINS'] = original
        groups['L'] = groups['R']
        with self.assertRaises(ValueError): arm.select('R')
        self.assertFalse(arm._ready)

    def test_docs_reselect_target_after_each_calibration_restart(self):
        text = (ROOT / 'docs/single_arm.md').read_text()
        for start, end in [('#### C.', '#### D.'),
                           ('5. **先进入单次开合测时阶段**', '6. 测时阶段'),
                           ('7. **实测时序后再解锁连续动作**', '### 4.')]:
            section = text[text.index(start):]
            if end in section:
                section = section[:section.index(end)]
            self.assertIn('重新选臂', section, start)
            self.assertIn('arm L', section, start)
