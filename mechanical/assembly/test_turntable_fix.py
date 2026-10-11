from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import MECHANICAL, ASSEMBLY, MANUAL_OUTPUT
from pathlib import Path
import json,collections,unittest
H=MANUAL_OUTPUT
class TurntableFix(unittest.TestCase):
 def test_separate_prerequisites_and_exact_final_partition(self):
  b=json.loads((ASSEMBLY/'final-head-steps.json').read_text());p=b['prerequisites'];added=[i for s in b['steps']for i in s['added_part_ids']]
  self.assertEqual(p['prebuilt_core_count'],0);self.assertEqual(len(added),165);self.assertEqual(len(set(added)),165);self.assertEqual(set(added)|set(p['deferred_interface_part_ids']),set(range(1,168)))
 def test_fixation_precedes_core_head_merge_without_closed_entry(self):
  b=json.loads((ASSEMBLY/'final-head-steps.json').read_text());ss=b['steps'];new=[s for s in ss if s['id'].startswith('HEAD-TT-')]
  self.assertEqual(len(new),9);self.assertEqual({i for s in new for i in s['added_part_ids']},set(range(34,49))|{86})
  at={i:s['number']for s in ss for i in s['added_part_ids']}
  self.assertLess(at[34],at[35]);self.assertLess(at[34],at[38]);self.assertLess(at[35],at[41]);self.assertLess(at[38],at[45]);self.assertLess(at[42],at[41]);self.assertLess(at[46],at[45]);self.assertLess(at[41],at[44]);self.assertLess(at[44],at[86])
  merge=next(s for s in ss if s['subassembly_id']=='merge_core');self.assertLess(new[-1]['number'],merge['number']);self.assertEqual(new[-1]['added_part_ids'],[])
  for s in new[:-1]:self.assertFalse(set(range(24,30))&set(s['visible_part_ids']))
  for s in ss:
   if s['number']<at[86]:self.assertNotIn(86,s['visible_part_ids'])
  self.assertEqual([s['id']for s in ss if s['id'].startswith('HEAD-FINAL-')],[f'HEAD-FINAL-{i:02d}'for i in range(1,31)])
 def test_four_arms_and_global_accounting(self):
  g=json.loads((H/'guide.json').read_text());self.assertEqual(len(g['steps']),501);self.assertEqual(g['coverage']['prebuilt_core_total_parts'],0);self.assertEqual(g['coverage']['direct_assembly_parts'],882)
  self.assertEqual(g['coverage']['model_count_working'],882);self.assertTrue(g['coverage']['original_arm_from_scratch'])
  for arm in ['R','L','F','B']:
   seq=[s for s in g['steps']if s.get('arm')==arm and s.get('source_step_id','').startswith('HEAD-')];self.assertEqual(len(seq),88);self.assertEqual(len([s for s in seq if '-HEAD-TT-'in s['source_step_id']]),9)
if __name__=='__main__':unittest.main()
