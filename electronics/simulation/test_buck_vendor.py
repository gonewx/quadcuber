import sys,unittest,json,tempfile
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).parent))
import run_buck_vendor as m
class VendorHarnessTests(unittest.TestCase):
 def test_rerun_cannot_reuse_old_compressed_waveform(self):
  with tempfile.TemporaryDirectory() as tmp:
   folder=Path(tmp);(folder/'waveform.txt.gz').write_bytes(b'old evidence');(folder/'waveform.txt').write_text('old')
   m.reset_case_outputs(folder)
   self.assertFalse((folder/'waveform.txt.gz').exists());self.assertFalse((folder/'waveform.txt').exists())
 def test_initialization_failure_cannot_inherit_completed_state(self):
  with tempfile.TemporaryDirectory() as tmp:
   folder=Path(tmp);(folder/'run-status.json').write_text('{"state":"COMPLETED","cases":[{"passed":true}]}')
   m.initialize_run(folder)
   with self.assertRaises(ValueError):m.parse_model('invalid model')
   state=json.loads((folder/'run-status.json').read_text())
   self.assertEqual(state['state'],'INITIALIZING');self.assertEqual(state['cases'],[])
 def test_official_pin_order_and_params(self):
  self.assertEqual(m.parse_model('.SUBCKT TPS54302_TRANS BOOT EN GND PH VIN VSENSE PARAMS: STEADY_STATE=0\n'),('TPS54302_TRANS',['BOOT','EN','GND','PH','VIN','VSENSE']))
 def test_pspice_xor_is_not_left_as_power(self):
  text='EXOR P 0 VALUE={IF(V(YTD) > 0.5 ^ V(IN) > .5, 1, 0)}\n'
  converted=m.adapt_model(text)
  self.assertNotIn('^',converted)
  self.assertIn('((V(YTD) > 0.5) != (V(IN) > .5))',converted)
 def test_adapter_rejects_unexpected_expression(self):
  with self.assertRaises(ValueError):m.adapt_model('unknown model')
 def test_unknown_pin_is_rejected(self):
  with self.assertRaises(ValueError):m.parse_model('.SUBCKT TPS54302_TRANS BOOT EN GND XYZ VIN VSENSE PARAMS: STEADY_STATE=0\n')
 def test_incomplete_even_with_zero_returncode(self):
  data=np.array([[0,0,0,0,0,0,0,0],[.00065,9,.4,.4,0,0,1.5,1.5]])
  self.assertFalse(m.assess(data,'',0)['completed'])
 def test_abort_log_invalidates_complete_data(self):
  data=np.array([[0,0,0,0,0,0,0,0],[.010,9,5,5,1,1,1.5,1.5],[.025,9,5,5,1,1,1.5,1.5]])
  self.assertFalse(m.assess(data,'run simulation(s) aborted',0)['completed'])
 def test_valid_data_is_accepted(self):
  data=np.array([[0,0,0,0,0,0,0,0],[.009,9,5,5,1,1,1.5,1.5],[.010,9,5,5,1,1,1.5,1.5],[.025,9,5,5,1,1,1.5,1.5]])
  self.assertTrue(m.assess(data,'',0)['passed'])
 def test_bad_rail_fails_separately(self):
  data=np.array([[0,0,0,0,0,0,0,0],[.009,9,5,5,1,1,1.5,1.5],[.010,9,5,4.5,1,1,1.5,1.5],[.025,9,5,4.5,1,1,1.5,1.5]])
  result=m.assess(data,'',0)
  self.assertTrue(result['completed']);self.assertFalse(result['passed'])
if __name__=='__main__':unittest.main()
