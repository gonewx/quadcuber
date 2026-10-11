from pathlib import Path
import json,hashlib,re,unittest
R=Path(__file__).resolve().parent
C=R.parent/'lift-feasibility/compact-arm-60483-candidate'
class ManualTest(unittest.TestCase):
 def test_guide_has_small_steps_and_safe_retention(self):
  p=R/'dist/compact60483/guide.json'
  self.assertTrue(p.exists(),'60483 step data missing')
  g=json.loads(p.read_text());self.assertGreaterEqual(len(g['steps']),18)
  text=json.dumps(g,ensure_ascii=False)
  for s in ['25°','64mm','HOLD','2780','3713','32123a','不同时','断电','装配路径','LIMITED']:self.assertIn(s,text)
  for s in g['steps']:self.assertTrue((R/'dist/compact60483'/s['image']).is_file());self.assertGreater(len(s['instructions']),0)
 def test_all_models_are_exact_candidate(self):
  p=R/'dist/compact60483/manifest.json';self.assertTrue(p.exists(),'60483 model mapping missing')
  a=json.loads(p.read_text());b=json.loads((C/'candidate-manifest.json').read_text());self.assertEqual(set(a),set(b))
  for k,v in a.items():
   f=R/'dist/compact60483'/v['file'];self.assertEqual(hashlib.sha256(f.read_bytes()).hexdigest(),b[k]['sha256'])
 def test_pages_are_distinct_and_linked(self):
  for n in ['compact60483-guide.html','compact60483-operation.html']:
   p=R/'dist'/n;self.assertTrue(p.exists(),n+' missing');self.assertIn('60483',p.read_text());self.assertIn('候选',p.read_text())
  self.assertIn('compact60483-guide.html',(R/'dist/index.html').read_text())
if __name__=='__main__':unittest.main()
