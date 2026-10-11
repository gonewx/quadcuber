from pathlib import Path
import json,unittest,collections
H=Path(__file__).resolve().parent
class FullArmCoverage(unittest.TestCase):
 def test_no_prebuilt_and_every_instance_introduced_once(self):
  b=json.loads((H/'final-head-steps.json').read_text());p=b['prerequisites']
  self.assertEqual(p['prebuilt_core_count'],0)
  added=[i for s in b['steps'] for i in s['added_part_ids']];defer=p['deferred_interface_part_ids']
  self.assertEqual(collections.Counter(added+defer),collections.Counter(range(1,168)))
  seen=set()
  for s in b['steps']:
   seen.update(s['added_part_ids']);self.assertLessEqual(set(s['visible_part_ids']),seen,s['id'])
 def test_pin_hosts_close_after_shoulder(self):
  b=json.loads((H/'final-head-steps.json').read_text());at={i:s['number'] for s in b['steps'] for i in s['added_part_ids']}
  for a,z in [(64,63),(65,63),(73,72),(74,72),(35,41),(38,45),(41,44),(44,86),(85,86),(45,24)]:self.assertIn(a,at);self.assertIn(z,at);self.assertLess(at[a],at[z],(a,z))
 def test_882_direct_coverage(self):
  g=json.loads((H/'guide.json').read_text());self.assertEqual(g['coverage']['prebuilt_core_total_parts'],0);self.assertEqual(g['coverage']['direct_assembly_parts'],882);self.assertTrue(g['coverage']['original_arm_from_scratch']);ledger=g['instance_introduction_ledger'];self.assertEqual(len(ledger),882);self.assertEqual(len({r['instance_key']for r in ledger}),882)
if __name__=='__main__':unittest.main()
