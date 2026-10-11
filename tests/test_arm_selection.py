"""R/L isolation and hardware lifecycle using the real firmware in the Pico simulator."""
import builtins
import contextlib
import io
import unittest
from unittest.mock import patch
from tests import pico_sim
from tests.pico_sim import world


class ArmSelectionTest(unittest.TestCase):
    def setUp(self):
        world.reset()
        self.at, = pico_sim.load_firmware('arm_test')

    def test_boot_holds_both_arms_low_without_servo_pulse(self):
        world.pins.update({p: 1 for p in (2, 3, 6, 7, 8, 9)})
        arm = self.at.Arm()
        self.assertEqual(arm.config.ARM_ID, 'R')
        self.assertEqual([world.pins[p] for p in (2, 3, 6, 7, 8, 9)], [0]*6)
        self.assertFalse(world.servo_ns)
        self.assertEqual(sum(sm.enabled for sm in world.sms.values()), 2)

    def test_l_configuration_and_calibration_start_blank(self):
        arm = self.at.Arm()
        arm.select('L')
        c = arm.config
        self.assertEqual((c.MOTOR_IN1, c.MOTOR_IN2, c.ENC_A, c.ENC_B, c.SERVO, c.ENC_SM),
                         (6, 7, 12, 13, 9, (2, 3)))
        for field in ('SERVO_OPEN_US', 'SERVO_CLOSE_US', 'SERVO_MIN_US', 'SERVO_MAX_US',
                      'SERVO_CALIBRATION_ARM', 'SERVO_CALIBRATION_PROFILE', 'SERVO_MOVE_MS'):
            self.assertIsNone(getattr(c, field), field)
        self.assertIs(c.SERVO_CALIBRATED, False)
        for command in ('open', 'close', 'rot', 'grip', 'cycle'):
            with self.subTest(command=command), self.assertRaises(ValueError):
                self.at.COMMANDS[command](arm, ['1'] if command in ('rot','grip','cycle') else [])
        self.assertFalse(world.servo_ns)

    def test_selection_releases_old_resources_and_revokes_authorization(self):
        arm = self.at.Arm()
        arm.begin_servo_calibration(1400, 1600, 1500, 'detached')
        arm.manual_servo(1500)
        old_motor, old_servo, old_sms = arm.motor, arm.servo, list(arm.enc._sms)
        arm.select('L')
        self.assertFalse(any(sm.enabled for sm in old_sms))
        self.assertIsNone(old_servo.us)
        self.assertEqual(world.pwm[8], 0)
        self.assertTrue(old_motor._a.closed and old_motor._b.closed)
        self.assertTrue(old_servo._pwm is None or old_servo._pwm.closed)
        self.assertIsNone(arm._servo_cal)
        self.assertFalse(arm._motor_test)
        self.assertNotIn(9, world.servo_ns)
        with self.assertRaises(ValueError): arm.manual_servo(1500)

    def test_repeated_switch_resets_transient_state_and_leaves_two_pio_active(self):
        arm = self.at.Arm()
        for name in ('L', 'R', 'R', 'L') * 5:
            arm._motor_test = True
            arm.nominal = 90
            arm.gains.set('vmax', 7)
            arm.select(name)
            self.assertEqual(sum(sm.enabled for sm in world.sms.values()), 2)
            self.assertEqual(arm.nominal, 0)
            self.assertEqual(arm.gains.vmax, arm.config.GAINS['vmax'])
            self.assertFalse(arm._motor_test)
            self.assertIsNone(arm._servo_cal)
        self.assertFalse(world.servo_ns)

    def test_invalid_selection_stops_old_arm_and_leaves_no_selected_hardware(self):
        arm = self.at.Arm()
        arm.motor.drive(.2)
        arm._motor_test = True
        for invalid in ('F', 'l', '', None):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError): arm.select(invalid)
            self.assertFalse(any(sm.enabled for sm in world.sms.values()))
            self.assertFalse(arm._motor_test)
            self.assertTrue(all(v == 0 for v in world.pwm.values()))
            with self.assertRaises(ValueError): arm.move_to(90)
        arm.select('L')
        self.assertEqual(arm.config.ARM_ID, 'L')

    def test_r_values_and_gains_are_not_replaced_by_l(self):
        self.at.config.SERVO_OPEN_US = 1711
        self.at.config.GAINS['vmax'] = 123
        arm = self.at.Arm()
        arm.select('L')
        self.assertIsNone(arm.config.SERVO_OPEN_US)
        arm.config.SERVO_OPEN_US = 1411
        arm.config.GAINS['vmax'] = 321
        arm.select('R')
        self.assertEqual(arm.config.SERVO_OPEN_US, 1711)
        self.assertEqual(arm.gains.vmax, 123)
        arm.select('L')
        self.assertEqual(arm.config.SERVO_OPEN_US, 1411)
        self.assertEqual(arm.gains.vmax, 321)

    def test_l_cannot_use_r_calibration_identity(self):
        arm = self.at.Arm(); arm.select('L')
        pico_sim.set_synthetic_servo_calibration(arm.config)
        with self.assertRaises(ValueError): arm.grip(True)
        arm.config.SERVO_CALIBRATION_ARM = 'L'
        arm.grip(True)
        self.assertEqual(world.servo_ns[9], 1600000)
        self.assertNotIn(8, world.servo_ns)

    def test_l_first_pulse_and_existing_in_bounds_jump_policy(self):
        arm = self.at.Arm(); arm.select('L')
        arm.begin_servo_calibration(1400, 1600, 1500, 'detached')
        self.assertFalse(world.servo_ns)
        with self.assertRaises(ValueError): arm.manual_servo(1490)
        arm.manual_servo(1500)
        arm.manual_servo(1600)
        arm.manual_servo(1400)
        with self.assertRaises(ValueError): arm.manual_servo(1399)
        self.assertEqual(world.servo_ns[9], 1400000)
        self.assertNotIn(8, world.servo_ns)

    def test_partial_encoder_init_failure_releases_new_resources(self):
        arm = self.at.Arm()
        real = pico_sim.StateMachine
        def fail(sm_id, *args, **kwargs):
            if sm_id == 3: raise OSError('synthetic PIO failure')
            return real(sm_id, *args, **kwargs)
        with patch.object(self.at.Encoder.__init__.__globals__['rp2'], 'StateMachine', fail):
            with self.assertRaises(OSError): arm.select('L')
        self.assertFalse(any(sm.enabled for sm in world.sms.values()))
        self.assertTrue(all(v == 0 for v in world.pwm.values()))
        with self.assertRaises(ValueError): arm.manual_servo(1500)
        arm.select('R')

    def test_cli_selection_status_invalid_and_fault_stop(self):
        arm = self.at.Arm()
        lines = iter(['arm L', 'arm', 'show', 'servo_cal 1400 1600 1500 detached',
                      'servo 1500', 'servo 1700', 'arm R', 'arm F', 'arm L', 'quit'])
        out = io.StringIO()
        with patch.object(self.at, 'Arm', lambda: arm), patch.object(builtins, 'input', lambda _: next(lines)), contextlib.redirect_stdout(out):
            self.at.main()
        self.assertIn('L', out.getvalue())
        self.assertNotIn('未知命令', out.getvalue())
        self.assertTrue(all(v == 0 for v in world.pwm.values()))
        self.assertFalse(any(sm.enabled for sm in world.sms.values()))
        self.assertIsNone(arm._servo_cal)

    def test_l_encoder_and_rotation_use_l_pins_and_scale(self):
        from tests.test_control import SimMotor
        world.reset(motor=SimMotor(), in1=6, in2=7, enc_a=12, enc_b=13)
        arm = self.at.Arm(); arm.select('L')
        arm.config.GEAR_RATIO = 1.0
        arm.select('L')
        with contextlib.redirect_stdout(io.StringIO()):
            self.at.cmd_motor_test(arm, ['unloaded'])
            result = arm.rot(1)
        self.assertTrue(result['ok'])
        self.assertAlmostEqual(arm.angle(), 90, delta=3)
        self.assertEqual((world.pwm.get(2, 0), world.pwm.get(3, 0)), (0, 0))
        arm.select('R')
        self.assertEqual(arm.deg_per_count, 360 / (720 * 2.5))

    def test_partial_pwm_failure_and_cleanup_failure_hold_all_outputs_low(self):
        arm = self.at.Arm()
        real = pico_sim.PWM
        def fail(pin, **kwargs):
            if pin.id == 7: raise OSError('synthetic PWM failure')
            return real(pin, **kwargs)
        with patch.dict(self.at.Motor.__init__.__globals__, PWM=fail):
            with self.assertRaises(OSError): arm.select('L')
        self.assertTrue(all(v == 0 for v in world.pwm.values()))
        self.assertFalse(any(sm.enabled for sm in world.sms.values()))
        arm.select('R')
        with patch.object(arm.servo, 'deinit', side_effect=OSError('synthetic cleanup failure')):
            with self.assertRaises(OSError): arm.select('L')
        self.assertFalse(arm._ready)
        self.assertFalse(any(sm.enabled for sm in world.sms.values()))
        self.assertEqual([world.pins[p] for p in (2, 3, 6, 7, 8, 9)], [0]*6)

    def test_arm_status_is_read_only_and_reports_selected_configuration(self):
        arm = self.at.Arm(); arm.select('L')
        arm.begin_servo_calibration(1400, 1600, 1500, 'detached')
        arm.manual_servo(1500)
        before = dict(world.servo_ns)
        out = io.StringIO()
        with contextlib.redirect_stdout(out): self.at.cmd_arm(arm, [])
        self.assertIn('config_l.py', out.getvalue())
        self.assertIn('GP6/7', out.getvalue())
        self.assertEqual(world.servo_ns, before)
        self.assertIsNotNone(arm._servo_cal)

    def test_selected_identity_cannot_be_changed_to_accept_other_arm_calibration(self):
        arm = self.at.Arm(); arm.select('L')
        pico_sim.set_synthetic_servo_calibration(arm.config)
        arm.config.ARM_ID = 'R'
        with self.assertRaises(ValueError): arm.grip(True)
        self.assertFalse(world.servo_ns)

    def test_released_handles_cannot_reenable_previous_arm(self):
        arm = self.at.Arm()
        motor, servo = arm.motor, arm.servo
        arm.select('L')
        for action in (lambda: motor.drive(.1), motor.brake, lambda: servo.pulse(1500)):
            with self.subTest(action=action), self.assertRaises(ValueError): action()
        self.assertNotIn(8, world.servo_ns)

    def test_l_command_error_stops_pulse_before_next_prompt(self):
        arm = self.at.Arm()
        lines = ['arm L', 'servo_cal 1400 1600 1500 detached', 'servo 1500', 'servo 1700', 'quit']
        count = [0]
        def read(_):
            if count[0] == 4:
                self.assertIsNone(arm._servo_cal)
                self.assertIsNone(arm.servo.us)
                self.assertEqual(world.pwm[9], 0)
                self.assertEqual(world.pwm.get(8, 0), 0)
            value = lines[count[0]]
            count[0] += 1
            return value
        with patch.object(self.at, 'Arm', lambda: arm), patch.object(builtins, 'input', read), contextlib.redirect_stdout(io.StringIO()):
            self.at.main()

    def test_shared_pwm_slice_does_not_reattach_stale_duty(self):
        # RP2 remembers the peer's duty across deinit; CC updates buffer while
        # a slice runs. Model the worst case: no wrap between two constructors.
        saved, compare, running, pending, glitches = {}, {}, {}, {}, []
        class RetainedPWM(pico_sim.PWM):
            def __init__(self, pin, *, freq=None, duty_u16=0):
                channel, slice_id = pin.id, pin.id // 2
                peer = channel ^ 1
                def write(ch, value):
                    if running.get(slice_id, False): pending[ch] = value
                    else: compare[ch] = value
                write(peer, saved.get(peer, 0))
                saved[channel] = duty_u16
                write(channel, duty_u16)
                running[slice_id] = True
                if compare.get(channel, 0): glitches.append(channel)
                super().__init__(pin, freq=freq, duty_u16=duty_u16)
            def duty_u16(self, value):
                saved[self.pin] = value
                if running.get(self.pin // 2, False): pending[self.pin] = value
                else: compare[self.pin] = value
                running[self.pin // 2] = True
                super().duty_u16(value)
            def deinit(self):
                running[self.pin // 2] = False
                super().deinit()
        with patch.dict(self.at.Motor.__init__.__globals__, PWM=RetainedPWM):
            arm = self.at.Arm()
            for name in ('R', 'L', 'R', 'L'):
                arm.select(name)
                arm.motor.brake()
                compare.update(pending); pending.clear()  # elapsed PWM wrap
                arm.select(name)
                self.assertFalse(glitches, 'stale duty reattached to GP%s' % glitches)
            arm.close()

    def test_serial_input_failure_releases_all_outputs(self):
        arm = self.at.Arm()
        lines = iter(['arm L', 'servo_cal 1400 1600 1500 detached', 'servo 1500'])
        def read(_):
            try: return next(lines)
            except StopIteration: raise OSError('synthetic serial disconnect')
        with patch.object(self.at, 'Arm', lambda: arm), patch.object(builtins, 'input', read), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(OSError): self.at.main()
        self.assertTrue(all(v == 0 for v in world.pwm.values()))
        self.assertFalse(any(sm.enabled for sm in world.sms.values()))

    def test_pin_cleanup_error_does_not_skip_pwm_disable(self):
        arm = self.at.Arm()
        arm.begin_servo_calibration(1400, 1600, 1500, 'detached'); arm.manual_servo(1500)
        real_pin = pico_sim.Pin
        calls = [0]
        def fail_once(pid, *args, **kwargs):
            if pid == 8 and calls[0] == 0:
                calls[0] += 1
                raise OSError('synthetic pin mux failure')
            return real_pin(pid, *args, **kwargs)
        fail_once.OUT = real_pin.OUT
        with patch.dict(self.at.Servo.deinit.__globals__, Pin=fail_once):
            with self.assertRaises(OSError): arm.close()
        self.assertEqual(world.pwm[8], 0)
        self.assertFalse(any(sm.enabled for sm in world.sms.values()))
