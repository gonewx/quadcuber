from pathlib import Path
import json,hashlib,csv,re,unittest
R=Path(__file__).resolve().parent;C=R.parent/'generated/mechanical';D=R.parent/'dist/site'
class FinalPresentation(unittest.TestCase):
 def test_operation_route_identifies_final_version(self):
  page=(D/'integrated-operation.html').read_text()
  self.assertIn('<title>Quadcuber · 装卸动作演示</title>',page)
  self.assertIn('最终结构 / 882件',page)
  nav=re.search(r'<nav class="primary-nav"[^>]*>(.*?)</nav>',page,re.S).group(1)
  self.assertEqual(len(re.findall('<a ',nav)),2)
  self.assertNotIn('integrated-operation',nav)
  self.assertIn('class="workspace assembly operation"',page)
  self.assertIn('装卸动作演示',page)
  self.assertIn((R/'viewer-workbench.css').read_text(),page)
  self.assertNotIn('class="integrated-shell"',page)
  self.assertNotIn('class="operation-selector"',page)
  self.assertIn('id="view-fullscreen"',page)
  self.assertIn('data-view="top"',page)
  self.assertIn('data-zoom="0.85"',page)
  self.assertIn('href="index.html">整机3D</a>',page)
  self.assertIn('href="integrated-assembly.html">逐步组装</a>',page)
  visible=re.sub(r'<script>[\s\S]*?</script>','',page)
  self.assertNotIn('整合版',visible)
 def test_operation_states_are_frozen_final_models(self):
  page=(D/'integrated-operation.html').read_text()
  payload=page.split('window.OPERATION_GUIDE=',1)[1]
  guide=json.JSONDecoder().raw_decode(payload)[0]
  self.assertEqual(guide,json.loads((D/'integrated/operation-guide.json').read_text()))
  self.assertEqual(len(guide['states']),9);self.assertEqual(len(guide['stages']),17)
  for state in guide['states'].values():
   model=(D/state['file']).read_text()
   self.assertEqual(model,state['model_text'])
   self.assertEqual(hashlib.sha256(model.encode()).hexdigest(),state['sha256'])
   self.assertEqual(state['count'],882);self.assertFalse(state['keys_present'])
   root=re.split(r'(?m)^0 FILE ',model)[1].splitlines()[1:]
   self.assertEqual(sum(line.startswith('1 ')for line in root),882)
   self.assertIn(state['seat_drop_mm'],[0,40.8])
 def test_final_only_visible_manual(self):
  g=json.loads((C/'manual/guide.json').read_text())
  words='\n'.join('\n'.join([s['title'],s['phase'],s['parts'],*s['instructions'],s['check']])for s in g['steps'])
  for bad in ['改装','旧机','旧版','32056','32002','替代两件','拆下两','移除两','177→','177改','R1支承','R3标记']:
   self.assertNotIn(bad,words)
  self.assertTrue(g['coverage']['original_arm_from_scratch']);self.assertEqual(g['coverage']['prebuilt_core_total_parts'],0);self.assertEqual(len(g['instance_introduction_ledger']),882);self.assertEqual(len({r['instance_key']for r in g['instance_introduction_ledger']}),882)
  self.assertEqual(g['coverage']['model_count_working'],882)
 def test_download_pdf_fits_host_single_file_limit(self):
  self.assertLessEqual((C/'manual/manual.pdf').stat().st_size,25*1024*1024)
 def test_frozen_final_models(self):
  old=json.loads((R.parent/'mechanical/inputs/PROVENANCE.json').read_text())
  for row in old['frozen_models'].values():self.assertEqual(hashlib.sha256((C/row['file']).read_bytes()).hexdigest(),row['sha256'])
 def test_current_pages_no_history(self):
  for file in ['index.html','integrated-assembly.html','integrated-operation.html','integrated-support.html']:
   html=(D/file).read_text(); visible=re.sub(r'<script>[\s\S]*?</script>','',html)
   for bad in ['改装','旧版','历史资料','history-132.html','history-219.html','原两枚工作锁销','209步','209页','128步']:
    self.assertNotIn(bad,visible,(file,bad))
 def test_current_bom(self):
  rows=list(csv.DictReader((D/'integrated/final-BOM.csv').open()))
  self.assertEqual(list(rows[0]),['part','quantity']);self.assertTrue(all(int(r['quantity'])>0 for r in rows));self.assertEqual(sum(int(r['quantity'])for r in rows),882)
 def test_every_current_step_exact_geometry(self):
  g=json.loads((C/'manual/guide.json').read_text())
  for s in g['steps']:
   self.assertTrue((C/'manual'/s['image']).is_file())
   rows=s.get('geometry_records')or[]
   if not rows:continue
   ids=[r['index1']for r in rows];self.assertEqual(len(ids),len(set(ids)));self.assertEqual(set(ids),set(s['visible_part_ids']));self.assertTrue(set(s['added_part_ids'])<=set(ids))
   self.assertTrue(all(r['name'] not in ['32056.dat','32002.dat']for r in rows))
if __name__=='__main__':unittest.main()
