"""Independent regression contract for authorized direct-bootstrap revision."""
import unittest, runpy
from pathlib import Path
C={c['ref']:c for c in runpy.run_path(str(Path(__file__).with_name('circuit.py')))['C']}
class BuckSourceContract(unittest.TestCase):
 def test_no_series_boot_resistor_or_intermediate_net(self):
  self.assertTrue({'R20','R30'}.isdisjoint(C))
  self.assertFalse(any(n and n.endswith('_BOOT_CAP') for c in C.values() for n in c['pins'].values()))
 def test_cap_bridges_boot_sw_not_short(self):
  for i,ref in [(1,'C22'),(2,'C32')]:
   self.assertEqual(C[ref]['value'],'100n')
   self.assertEqual(C[ref]['pins'],{'1':f'B{i}_BOOT','2':f'B{i}_SW'})
   self.assertEqual(C[f'U{i+1}']['pins']['6'],f'B{i}_BOOT')
   self.assertEqual(C[f'U{i+1}']['pins']['2'],f'B{i}_SW')
 def test_cap_placement_matches_reviewed_local_board(self):
  for ref,xy in [('C22',(48,41.9)),('C32',(97,41.9))]:
   self.assertEqual(tuple(C[ref]['xy']),xy)
   self.assertEqual(C[ref]['rot'],0)
 def test_precision_feedback_exact_mpn_same_values(self):
  for refs,value,mpn in [(('R21','R31'),'100k','RT0603BRD07100KL'),(('R22','R32'),'13.3k','RT0603BRD0713K3L')]:
   for ref in refs:
    self.assertEqual((C[ref]['value'],C[ref]['mpn']),(value,mpn))
if __name__=='__main__':unittest.main()
