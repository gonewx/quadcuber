from pathlib import Path
import json,hashlib,re,unittest
R=Path(__file__).resolve().parent;C=R.parent/'generated/mechanical';D=R.parent/'dist/site'
class Integration(unittest.TestCase):
 def test_all_primary_views_share_manifest(self):
  m=json.loads((D/'integrated/manifest.json').read_text()); g=json.loads((D/'integrated/operation-guide.json').read_text())
  for k,v in m.items():self.assertEqual(hashlib.sha256((D/'integrated'/v['file']).read_bytes()).hexdigest(),v['sha256'])
  for s in g['states'].values():self.assertEqual(hashlib.sha256(s['model_text'].encode()).hexdigest(),s['sha256']);self.assertEqual(s['sha256'],m[s['mechanical_key']]['sha256'])
 def test_manual_model_identity(self):
  g=json.loads((D/'integrated/guide.json').read_text()); self.assertGreater(len(g['steps']),80)
  for s in g['steps']:self.assertTrue((D/'integrated'/s['image']).is_file())
 def test_default_is_integrated(self):
  p=(D/'index.html').read_text();self.assertTrue('最终结构' in p);self.assertTrue('integrated-assembly.html' in p);self.assertFalse('本页原模型／历史记录保持独立' in p)
  self.assertTrue((D/'integrated/integrated-BOM.csv').is_file()); self.assertTrue((D/'integrated/full-revision.zip').is_file());self.assertTrue((D/'integrated/manual.pdf').is_file())
 def test_no_broken_local_references(self):
  for fn in ['index.html','integrated-assembly.html','integrated-support.html']:
   p=(D/fn).read_text()
   for url in re.findall(r'(?:href|src)="([^"]+)"',p):
    if ':' in url or url.startswith('#'):continue
    self.assertTrue((D/url.split('#')[0]).is_file(),(fn,url))
if __name__=='__main__':unittest.main()
