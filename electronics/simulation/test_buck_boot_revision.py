"""Regression contracts for the authorized direct-bootstrap revision."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import run_buck_vendor as m

class DirectBootstrapTests(unittest.TestCase):
 def test_actual_source_has_direct_bootstrap_and_precision_feedback(self):
  self.assertTrue(callable(getattr(m, 'buck_source_contract', None)), 'Missing enforced buck source contract')
  m.buck_source_contract(m.C)
 def test_deck_bootstrap_connects_model_boot_directly_to_sw(self):
  self.assertTrue(callable(getattr(m, 'case_lines', None)), 'Missing shared deck generator')
  lines=m.case_lines('TPS54302_TRANS', ['BOOT','EN','GND','PH','VIN','VSENSE'],9,.8)
  for ch in (1,2):
   self.assertIn(f'C{ch}boot b{ch}boot b{ch}sw 100n',lines)
   self.assertFalse(any(line.startswith(f'R{ch}boot ') for line in lines))
   self.assertFalse(any(f'b{ch}bc' in line for line in lines))
 def test_contract_rejects_wrong_feedback_mpn(self):
  self.assertTrue(callable(getattr(m, 'buck_source_contract', None)))
  parts=copy.deepcopy(m.C);parts['R21']['mpn']='RC0603FR-07100KL'
  with self.assertRaises(AssertionError):m.buck_source_contract(parts)
 def test_contract_rejects_capacitor_connected_to_old_node(self):
  self.assertTrue(callable(getattr(m, 'buck_source_contract', None)))
  parts=copy.deepcopy(m.C);parts['C22']['pins']['1']='B1_BOOT_CAP'
  with self.assertRaises(AssertionError):m.buck_source_contract(parts)

if __name__=='__main__':unittest.main()
