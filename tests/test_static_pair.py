"""Static supported servo mode: real firmware under the Pico test environment."""
import contextlib
import copy
import importlib
import io
import unittest
from unittest.mock import patch
from tests import pico_sim
from tests.pico_sim import world


class StaticPairTest(unittest.TestCase):
    def setUp(self):
        world.reset()
        self.at, = pico_sim.load_firmware('arm_test')
        self.assertIn('static', self.at.COMMANDS, 'explicit supported static mode is missing')
        self.sp = self.at.static_pair
        self.arm = self.at.Arm()
        self.arm.close()
        self.pair = self.sp.StaticPair('supported')
        self.addCleanup(self.pair.close)

    def command(self, text):
        return self.pair.command(text)

    def start(self, name='R', ttl=30):
        self.command('cal %s 1400 1600 1500 detached %d' % (name, ttl))
        self.command('start %s 1500' % name)

    def advance(self, ms, steps=1):
        for _ in range(steps):
            world.sleep_ms(ms)
            self.pair.tick()

    def assert_stopped(self):
        self.assertFalse(self.pair.active)
        self.assertTrue(all(world.pins.get(p, 0) == 0 for p in (2,3,6,7,8,9)))
        self.assertTrue(all(world.pwm.get(p, 0) == 0 for p in (2,3,6,7,8,9)))

    def test_entry_no_pulse_or_pio_and_requires_support(self):
        self.assertFalse(world.servo_ns)
        self.assertFalse(any(sm.enabled for sm in world.sms.values()))
        with self.assertRaises(ValueError): self.sp.StaticPair('unsupported')

    def test_independent_first_pulses_and_no_r_to_l_authorization(self):
        self.start('R')
        self.assertNotIn(9, world.servo_ns)
        self.command('cal L 1450 1550 1490 detached 30')
        self.assertEqual(world.servo_ns[8],1500000)
        self.command('start L 1490')
        self.assertEqual(world.servo_ns[9],1490000)
        self.assertEqual(world.servo_ns[8],1500000)
        with self.assertRaises(ValueError): self.command('move L 1600 100 verified')
        self.assert_stopped()

    def test_first_pulse_must_match_declared_start(self):
        self.command('cal L 1400 1600 1500 detached 30')
        with self.assertRaises(ValueError): self.command('start L 1450')
        self.assertFalse(world.servo_ns)
        self.assert_stopped()

    def test_large_target_is_ramped_without_changing_other_channel(self):
        self.start('R');self.start('L')
        self.command('move R 1600 100 verified')
        self.assertEqual(world.servo_ns[8],1500000)
        self.advance(20)
        self.assertEqual(world.servo_ns[8],1502000)
        self.assertEqual(world.servo_ns[9],1500000)
        self.advance(20,49)
        self.assertEqual(world.servo_ns[8],1600000)
        self.assertEqual(self.command('status')['R']['target_us'],1600)
        self.assertEqual(world.servo_ns[9],1500000)

    def test_scheduling_delay_does_not_create_catchup_jump(self):
        self.start();self.command('move R 1600 200 verified')
        self.advance(1000)
        self.assertLessEqual(world.servo_ns[8],1504000)

    def test_status_does_not_extend_timeout_and_either_expiry_stops_both(self):
        self.start('R',5);self.start('L',30)
        self.advance(4000);self.command('status')
        with self.assertRaises(TimeoutError):self.advance(1100)
        self.assert_stopped()

    def test_explicit_supported_renewal_is_per_arm(self):
        self.start('R',5);self.start('L',30)
        self.advance(4000);self.command('renew R supported')
        self.advance(2000)
        self.assertTrue(self.pair.active)
        self.assertGreater(self.command('status')['R']['remaining_ms'],0)

    def test_known_calibration_bounds_and_identity_are_not_bypassed(self):
        cfg=self.sp.get_profile('R')
        cfg.SERVO_CALIBRATED=True;cfg.SERVO_MIN_US=1450;cfg.SERVO_MAX_US=1550
        cfg.SERVO_CALIBRATION_ARM='R';cfg.SERVO_CALIBRATION_PROFILE='v4'
        with self.assertRaises(ValueError):self.command('cal R 1400 1600 1500 aligned 30')
        self.assert_stopped()

    def test_manual_authorization_never_mutates_configuration(self):
        before=copy.deepcopy(self.at.config.ARMS)
        self.start('L');self.command('move L 1550 100 verified');self.advance(20,25)
        self.assertEqual(self.at.config.ARMS,before)
        self.assertIsNone(self.sp.get_profile('L').SERVO_CLOSE_US)

    def test_forbidden_commands_and_bad_rate_close_both(self):
        self.start('R');self.start('L')
        with self.assertRaises(ValueError): self.command('goto 90')
        self.assert_stopped()

    def test_pwm_exception_stops_both_outputs(self):
        self.start('R');self.start('L');self.command('move L 1550 100 verified')
        with patch.object(self.pair.pwm['L'],'duty_ns',side_effect=OSError('simulated write failure')):
            with self.assertRaises(OSError):self.advance(20)
        self.assert_stopped()

    def test_entry_releases_single_arm_and_return_does_not_select_or_pulse(self):
        self.pair.close();self.arm.select('R')
        with patch.object(self.sp,'run_console') as run:
            self.at.cmd_static(self.arm,['supported'])
        run.assert_called_once_with('supported')
        self.assertFalse(self.arm._ready)
        self.assertFalse(any(sm.enabled for sm in world.sms.values()))
        self.assertFalse(world.servo_ns)

    def test_off_revokes_both_and_never_sends_open_endpoint(self):
        self.start('R');self.start('L');before=dict(world.servo_ns)
        self.command('off')
        self.assert_stopped()
        self.assertEqual(world.servo_ns,before)

    def test_existing_partial_calibration_bounds_remain_limits(self):
        cfg=self.sp.get_profile('R')
        cfg.SERVO_MIN_US=1450;cfg.SERVO_MAX_US=1550
        cfg.SERVO_CALIBRATED=False
        with self.assertRaises(ValueError):self.command('cal R 1400 1600 1500 aligned 30')
        self.assert_stopped()

    def test_valid_bounds_cannot_bypass_wrong_calibration_identity(self):
        cfg = self.sp.get_profile('L')
        cfg.SERVO_CALIBRATED = True
        cfg.SERVO_MIN_US, cfg.SERVO_MAX_US = 1400, 1600
        cfg.SERVO_CALIBRATION_ARM = 'R'
        cfg.SERVO_CALIBRATION_PROFILE = 'v4'
        with self.assertRaises(ValueError):
            self.command('cal L 1450 1550 1500 aligned 30')
        self.assert_stopped()

    def test_incomplete_known_bounds_are_rejected(self):
        self.sp.get_profile('L').SERVO_MIN_US = 1400
        with self.assertRaises(ValueError):
            self.command('cal L 1450 1550 1500 detached 30')
        self.assert_stopped()

    def test_r_authorization_cannot_start_l(self):
        self.start('R')
        with self.assertRaises(ValueError):
            self.command('start L 1500')
        self.assertNotIn(9, world.servo_ns)
        self.assert_stopped()

    def test_malformed_commands_stop_both(self):
        for command in ('cal X 1400 1600 1500 detached 30', 'start R nope',
                        'status extra', 'off extra', 'renew R',
                        'move R 1500 100 verified extra'):
            with self.subTest(command=command):
                self.pair.close()
                self.pair = self.sp.StaticPair('supported')
                self.start('R'); self.start('L')
                with self.assertRaises(ValueError):
                    self.command(command)
                self.assert_stopped()

    def test_poller_error_stops_both(self):
        self.pair.close()
        class Poll:
            def register(self, *args): pass
            def poll(self, ms): raise OSError('poll failure')
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(OSError):
                self.sp.run_console('supported', io.BytesIO(), Poll())
        self.assertTrue(all(world.pwm.get(p, 0) == 0 for p in (8, 9)))

    def test_first_start_cannot_be_used_again_to_skip_ramp(self):
        self.start()
        with self.assertRaises(ValueError):self.command('start R 1600')
        self.assert_stopped()

    def test_rate_and_verified_declaration_required(self):
        for command in ('move R 1550 0 verified', 'move R 1550 201 verified',
                        'move R 1550 100', 'move R 1550 100 unchecked'):
            with self.subTest(command=command):
                self.pair.close();self.pair=self.sp.StaticPair('supported');self.start()
                with self.assertRaises(ValueError):self.command(command)
                self.assert_stopped()

    def test_shared_slice_not_deinitialized_on_second_start_or_motion(self):
        class SharedPWM(pico_sim.PWM):
            deinitializations=0
            def deinit(self):
                type(self).deinitializations+=1
                super().deinit()
                if self.pin in (8,9):
                    world.pwm[8]=world.pwm[9]=0
        self.pair.close()
        with patch.object(self.sp,'PWM',SharedPWM):
            self.pair=self.sp.StaticPair('supported')
        self.start('R');n=SharedPWM.deinitializations
        self.start('L');self.command('move L 1550 100 verified');self.advance(20,25)
        self.assertEqual(SharedPWM.deinitializations,n)
        self.assertGreater(world.pwm[8],0);self.assertGreater(world.pwm[9],0)
        self.assertEqual(world.servo_ns[8],1500000)
        self.assertEqual(world.servo_ns[9],1550000)
        self.assertEqual(self.pair.pwm['R'].freq(),50)
        self.assertEqual(self.pair.pwm['L'].freq(),50)

    def test_initialization_failure_cleans_partial_resources(self):
        self.pair.close()
        def fail_second(pin,**kw):
            if pin.id==9:raise OSError('second-channel init failure')
            return pico_sim.PWM(pin,**kw)
        with patch.object(self.sp,'PWM',side_effect=fail_second):
            with self.assertRaises(OSError):self.sp.StaticPair('supported')
        self.assertTrue(all(world.pwm.get(p,0)==0 for p in (8,9)))
        self.assertFalse(world.servo_ns)

    def test_idle_partial_line_timeout_does_not_wait_for_newline(self):
        self.pair.close()
        data='cal R 1400 1600 1500 detached 5\nstart R 1500\nstat'
        stream=io.BytesIO(data.encode('ascii'))
        class Poll:
            def register(self,*a):pass
            def poll(self,ms):
                world.sleep_ms(ms)
                return [(0,1)] if stream.tell()<len(data) else []
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(TimeoutError):self.sp.run_console('supported',stream,Poll())
        self.assertEqual(world.servo_ns[8],1500000)
        self.assertEqual(world.pwm[8],0);self.assertEqual(world.pwm[9],0)

    def test_console_ctrl_c_and_eof_stop_both(self):
        for ending in ('\x03','\x04'):
            self.pair.close()
            data='cal R 1400 1600 1500 detached 30\nstart R 1500\n'+ending
            stream=io.BytesIO(data.encode('ascii'))
            class Poll:
                def register(self,*a):pass
                def poll(self,ms):world.sleep_ms(ms);return [(0,1)]
            with contextlib.redirect_stdout(io.StringIO()):
                if ending=='\x03':
                    with self.assertRaises(KeyboardInterrupt):self.sp.run_console('supported',stream,Poll())
                else:self.sp.run_console('supported',stream,Poll())
            self.assertEqual(world.pwm[8],0);self.assertEqual(world.pwm[9],0)

    def test_console_raw_byte_read_rejects_incomplete_utf8_and_controls(self):
        # Text read(1) can wait for UTF-8 continuation bytes on MicroPython.
        class ByteStream(io.BytesIO):
            def read(self, size=-1):
                raise AssertionError('text read could block waiting for UTF-8')
        class Poll:
            def register(self, *args): pass
            def poll(self, ms): world.sleep_ms(ms); return [(0, 1)]
        for byte in (b'\xe4', b'\x01'):
            self.pair.close()
            data = b'cal R 1400 1600 1500 detached 30\nstart R 1500\n' + byte
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(ValueError):
                    self.sp.run_console('supported', ByteStream(data), Poll())
            self.assertEqual(world.servo_ns[8], 1500000)
            self.assertEqual(world.pwm[8], 0)
            self.assertEqual(world.pwm[9], 0)


if __name__=='__main__':unittest.main()
