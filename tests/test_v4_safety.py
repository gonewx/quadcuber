"""v4 默认约束与舵机门禁回归；只在 CPython 模拟器中运行。"""

import builtins
import contextlib
import io
import unittest
from unittest.mock import patch

from quadcuber import __main__ as cli
from quadcuber.cube import invert, parse_moves
from quadcuber.machine import CubeRotate, InvalidStep, Machine, Open, Rotate, initial_state
from quadcuber.planner import plan
from quadcuber.simulate import verify_plan
from tests import pico_sim
from tests.pico_sim import world
from tests.test_control import SimMotor


class V4ProfileTest(unittest.TestCase):
    def test_default_profile_rejects_adjacent_tilt_and_reset(self):
        machine = Machine()
        self.assertTrue(machine.no_adjacent_horizontal)
        state = machine.apply(initial_state(), (Open("F"), Open("B")))
        with self.assertRaises(InvalidStep):
            machine.check(state, (CubeRotate(0, 1), Rotate("F", 1)))

    def test_default_plan_is_safe_for_v4(self):
        moves = parse_moves("R U R' U'")
        result = plan(moves)
        strict = Machine(no_adjacent_horizontal=True)
        checked = verify_plan(result, invert(moves), strict)
        self.assertTrue(checked.solved, checked.error)
        for state, step in zip(result.states, result.steps):
            strict.check(state, step)

    def test_generic_profile_preserves_explicit_legacy_behavior(self):
        machine = Machine(profile="generic")
        self.assertFalse(machine.no_adjacent_horizontal)
        state = machine.apply(initial_state(), (Open("F"), Open("B")))
        machine.check(state, (CubeRotate(0, 1), Rotate("F", 1)))
        self.assertTrue(Machine(profile="generic", no_adjacent_horizontal=True).no_adjacent_horizontal)

    def test_v4_profile_cannot_disable_safety_or_misspell_profile(self):
        for kwargs in ({"profile": "v4", "no_adjacent_horizontal": False}, {"profile": "v44"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Machine(**kwargs)

    def test_cli_plan_and_bench_use_profile_defaults(self):
        for command in (["plan", "R"], ["bench", "--count", "1", "--length", "1"]):
            for flags, expected in (([], True), (["--profile", "generic"], False),
                                    (["--profile", "generic", "--no-adjacent-horizontal"], True)):
                seen = []
                real_plan = cli.plan
                def capture(moves, machine, *args, **kwargs):
                    seen.append(machine.no_adjacent_horizontal)
                    return real_plan(moves, machine, *args, **kwargs)
                with self.subTest(command=command, flags=flags), patch.object(cli, "plan", capture):
                    with contextlib.redirect_stdout(io.StringIO()):
                        self.assertEqual(cli.main(command + flags), 0)
                    self.assertEqual(seen, [expected])

    def test_limited_generic_plan_preserves_profile(self):
        machine = Machine(profile="generic", angle_limit=2)
        moves = parse_moves("R U R' U'")
        result = plan(moves, machine)
        self.assertTrue(verify_plan(result, invert(moves), machine).solved)


class ServoSafetyTest(unittest.TestCase):
    def setUp(self):
        world.reset(motor=SimMotor())
        (self.at,) = pico_sim.load_firmware("arm_test")
        self.arm = self.at.Arm()

    def run_cmd(self, line):
        name, *args = line.split()
        with contextlib.redirect_stdout(io.StringIO()):
            self.at.COMMANDS[name](self.arm, args)

    def calibrated(self):
        pico_sim.set_synthetic_servo_calibration(self.at.config)

    def test_boot_and_default_config_do_not_position_servo(self):
        self.assertIsNone(self.at.config.SERVO_OPEN_US)
        self.assertIsNone(self.at.config.SERVO_CLOSE_US)
        self.assertIs(self.at.config.SERVO_CALIBRATED, False)
        self.assertIsNone(self.arm.servo.us)
        self.assertNotIn(self.at.config.SERVO, world.servo_ns)
        self.assertEqual(world.pwm.get(self.at.config.SERVO, 0), 0)

    def test_unvalidated_commands_and_arm_entry_fail_before_motion(self):
        for line in ("open", "close", "grip 2", "cycle 1", "servo 1500"):
            with self.subTest(line=line), self.assertRaises(ValueError):
                self.run_cmd(line)
            self.assertIsNone(self.arm.servo.us)
            self.assertEqual(world.duty(), 0)
            self.assertEqual(self.arm.nominal, 0)
        with self.assertRaises(ValueError):
            self.arm.grip(True)

    def test_missing_or_invalid_configuration_stays_locked(self):
        self.calibrated()
        invalid = (None, True, False, "1500", 499, 2501, float("nan"), float("inf"), 1500.5)
        for value in invalid:
            self.at.config.SERVO_OPEN_US = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.run_cmd("close")
            self.assertIsNone(self.arm.servo.us)
        self.at.config.SERVO_OPEN_US = self.at.config.SERVO_CLOSE_US
        with self.assertRaises(ValueError):
            self.run_cmd("open")
        self.calibrated()
        del self.at.config.SERVO_CALIBRATED
        with self.assertRaises(ValueError):
            self.run_cmd("close")

    def test_calibrated_open_close_use_only_validated_endpoints(self):
        self.calibrated()
        self.run_cmd("close")
        self.assertEqual(self.arm.servo.us, 1600)
        self.run_cmd("open")
        self.assertEqual(self.arm.servo.us, 1400)

    def test_calibration_entry_no_pulse_then_declared_start_and_small_steps(self):
        self.run_cmd("servo_cal 1450 1550 1500 detached")
        self.assertIsNone(self.arm.servo.us)
        self.assertNotIn(self.at.config.SERVO, world.servo_ns)
        with self.assertRaises(ValueError):
            self.run_cmd("servo 1490")
        self.run_cmd("servo 1500")
        self.run_cmd("servo 1520")
        self.assertEqual(self.arm.servo.us, 1520)
        for line in ("servo 1550", "servo 1449", "servo 2501"):
            with self.subTest(line=line), self.assertRaises(ValueError):
                self.run_cmd(line)
            self.assertEqual(self.arm.servo.us, 1520)

    def test_calibration_requires_bounded_explicit_physical_confirmation(self):
        for line in ("servo_cal", "servo_cal 1450 1550 1500", "servo_cal 1450 1550 1500 yes",
                     "servo_cal 499 1550 1500 detached", "servo_cal 1450 2501 1500 detached",
                     "servo_cal 1550 1450 1500 detached", "servo_cal 1450 1550 1600 detached"):
            with self.subTest(line=line), self.assertRaises(ValueError):
                self.run_cmd(line)
            self.assertIsNone(self.arm.servo.us)

    def test_off_end_and_new_arm_revoke_manual_calibration(self):
        for stop in ("off", "servo off", "servo_cal end"):
            self.run_cmd("servo_cal 1450 1550 1500 aligned")
            self.run_cmd("servo 1500")
            self.run_cmd(stop)
            self.assertIsNone(self.arm.servo.us)
            with self.assertRaises(ValueError):
                self.run_cmd("servo 1500")
        self.run_cmd("servo_cal 1450 1550 1500 detached")
        self.arm = self.at.Arm()
        with self.assertRaises(ValueError):
            self.run_cmd("servo 1500")

    def test_automatic_clamp_commands_blocked_during_manual_calibration(self):
        self.calibrated()
        self.run_cmd("servo_cal 1450 1550 1500 detached")
        for line in ("open", "close", "grip 1", "cycle 1"):
            with self.subTest(line=line), self.assertRaises(ValueError):
                self.run_cmd(line)
        self.assertIsNone(self.arm.servo.us)
        self.assertEqual(world.duty(), 0)

    def test_cycle_failure_stops_without_automatic_open(self):
        self.calibrated()
        world.motor.locked = True
        self.run_cmd("cycle 1")
        self.assertIsNone(self.arm.servo.us)
        self.assertEqual(world.servo_ns[self.at.config.SERVO], 1600000)
        self.assertEqual(world.duty(), 0)

    def test_uncalibrated_motor_commands_and_move_method_are_locked(self):
        for line in ("check", "duty 0.2 50", "speed", "friction", "rot 1", "goto 20", "bench 1 1"):
            with self.subTest(line=line), self.assertRaises(ValueError):
                self.run_cmd(line)
            self.assertEqual(world.duty(), 0)
            self.assertEqual(self.arm.nominal, 0)
        with self.assertRaises(ValueError):
            self.arm.move_to(20)

    def test_unloaded_motor_mode_is_explicit_and_separate_from_servo_mode(self):
        for line in ("motor_test", "motor_test yes"):
            with self.subTest(line=line), self.assertRaises(ValueError):
                self.run_cmd(line)
        self.run_cmd("motor_test unloaded")
        self.assertEqual(world.duty(), 0)
        self.assertIsNone(self.arm.servo.us)
        self.run_cmd("check")
        for line in ("open", "cycle 1", "servo 1500", "rot 1 load", "bench 1 1 load"):
            with self.subTest(line=line), self.assertRaises(ValueError):
                self.run_cmd(line)
        self.run_cmd("servo_cal 1450 1550 1500 detached")
        with self.assertRaises(ValueError):
            self.run_cmd("rot 1")
        self.run_cmd("motor_test unloaded")
        with self.assertRaises(ValueError):
            self.run_cmd("servo 1500")
        self.run_cmd("off")
        with self.assertRaises(ValueError):
            self.run_cmd("check")

    def test_calibration_record_requires_valid_bounds_identity_and_confirmation(self):
        for field, values in (
            ("SERVO_MIN_US", (None, True, 499, 1450, float("nan"))),
            ("SERVO_MAX_US", (None, 2501, 1550, float("inf"))),
            ("SERVO_CALIBRATED", (False, 1, "yes")),
            ("SERVO_CALIBRATION_PROFILE", (None, "v3", "generic")),
            ("SERVO_CALIBRATION_ARM", (None, "L", "")),
            ("SERVO_MOVE_MS", (0, -1, True, float("nan"), 5001)),
        ):
            for value in values:
                self.calibrated()
                self.at.config.SERVO_MOVE_MS = 120
                setattr(self.at.config, field, value)
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    self.run_cmd("close")
                self.assertIsNone(self.arm.servo.us)
                with self.assertRaises(ValueError):
                    self.arm.move_to(20)

    def test_unconfirmed_timing_only_allows_single_open_or_close(self):
        self.calibrated()
        self.at.config.SERVO_TIMING_CONFIRMED = False
        self.run_cmd("close")
        self.assertEqual(self.arm.servo.us, 1600)
        self.run_cmd("open")
        self.assertEqual(self.arm.servo.us, 1400)
        for line in ("grip 1", "cycle 1", "rot 1", "goto 20", "bench 1 1", "duty 0.2 50"):
            with self.subTest(line=line), self.assertRaises(ValueError):
                self.run_cmd(line)
        self.run_cmd("motor_test unloaded")
        self.run_cmd("check")

    def test_timing_confirmation_must_be_explicit(self):
        for value in (None, False, 1, "yes"):
            self.calibrated()
            self.at.config.SERVO_TIMING_CONFIRMED = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.run_cmd("cycle 1")
            self.assertIsNone(self.arm.servo.us)
        self.calibrated()
        del self.at.config.SERVO_TIMING_CONFIRMED
        with self.assertRaises(ValueError):
            self.run_cmd("rot 1")

    def test_shipped_timing_is_not_a_measurement(self):
        self.assertIsNone(self.at.config.SERVO_MOVE_MS)
        self.assertIs(self.at.config.SERVO_TIMING_CONFIRMED, False)

    def run_main(self, lines, after_command=None):
        lines = iter(lines)
        calls = [0]
        def read_line(prompt=""):
            if after_command is not None:
                after_command(calls[0])
            calls[0] += 1
            return next(lines)
        with patch.object(self.at, "Arm", lambda: self.arm), patch.object(builtins, "input", read_line):
            with contextlib.redirect_stdout(io.StringIO()):
                self.at.main()

    def test_main_error_revokes_manual_session_and_stops_pwm(self):
        def check(index):
            if index == 3:
                self.assertIsNone(self.arm.servo.us)
                self.assertIsNone(self.arm._servo_cal)
                self.assertFalse(self.arm._motor_test)
                self.assertEqual(world.pwm[self.at.config.SERVO], 0)
        self.run_main(["servo_cal 1450 1550 1500 detached", "servo 1500", "servo 2000", "quit"], check)

    def test_main_interrupt_revokes_motor_session_and_coasts(self):
        def interrupt(ms):
            raise KeyboardInterrupt()
        def check(index):
            if index == 2:
                self.assertFalse(self.arm._motor_test)
                self.assertIsNone(self.arm._servo_cal)
                self.assertEqual(world.duty(), 0)
        with patch.object(self.at.time, "sleep_ms", interrupt):
            self.run_main(["motor_test unloaded", "duty 0.2 50", "quit"], check)

    def test_main_input_interrupt_and_exit_disable_servo(self):
        for stop in (KeyboardInterrupt(), EOFError(), "quit"):
            lines = iter(["servo_cal 1450 1550 1500 detached", "servo 1500", stop])
            def read_line(prompt=""):
                value = next(lines)
                if isinstance(value, BaseException):
                    raise value
                return value
            with self.subTest(stop=stop), patch.object(self.at, "Arm", lambda: self.arm):
                with patch.object(builtins, "input", read_line), contextlib.redirect_stdout(io.StringIO()):
                    self.at.main()
            self.assertIsNone(self.arm._servo_cal)
            self.assertFalse(self.arm._motor_test)
            self.assertIsNone(self.arm.servo.us)
            self.assertEqual(world.pwm[self.at.config.SERVO], 0)

    def test_valid_calibration_does_not_arm_or_position_on_start(self):
        self.calibrated()
        self.arm = self.at.Arm()
        self.assertIsNone(self.arm.servo.us)
        self.assertNotIn(self.at.config.SERVO, world.servo_ns)
        self.assertFalse(self.arm._motor_test)
        self.assertIsNone(self.arm._servo_cal)
        self.run_main(["help", "show", "off", "quit"])
        self.assertNotIn(self.at.config.SERVO, world.servo_ns)

    def test_low_level_pulse_rejects_out_of_range_instead_of_clamping(self):
        for value in (499, 2501, True, "1500", float("nan")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.arm.servo.pulse(value)
        self.assertIsNone(self.arm.servo.us)
