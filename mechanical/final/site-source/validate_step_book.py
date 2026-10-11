from pathlib import Path
import json,collections,hashlib,re
from html.parser import HTMLParser
from PIL import Image
root=Path(__file__).resolve().parent
book=json.loads((root/'instruction-book.json').read_text())
assert book.get('data_status') in ['partial','final','core_complete_original_interface_hold','inventory_hold']
steps=book['steps'];assert steps
source_path=root.parent/'lift-feasibility/unified-base-validation/corrected-snapshot/assembly.json'
source=json.loads(source_path.read_text());assert hashlib.sha256(source_path.read_bytes()).hexdigest()==book['source_sha256']
canonical_checked=0
ids=[s['id']for s in steps];assert len(ids)==len(set(ids))
added=[];image_stats=[];introduced=set()
for s in steps:
 assert s.get('title') and s.get('module_title'),s['id']
 assert isinstance(s['instructions'],list) and all(isinstance(x,str)for x in s['instructions'])
 assert len(s['added_part_ids'])<=4,s['id']
 assert all(isinstance(i,int)and 1<=i<=192 for i in s['added_part_ids']),s['id']
 assert len(s['added_part_ids'])==len(set(s['added_part_ids']))
 assert set(s['added_part_ids'])<=set(s['visible_part_ids']),s['id']
 assert set(s.get('highlight_part_ids',s['added_part_ids']))<=set(s['visible_part_ids']),s['id']
 assert all(1<=i<=900 for i in s['visible_part_ids'])
 assert sum(p['count']for p in s.get('parts',[]))==len(s['added_part_ids']),s['id']
 if all(p['name'].endswith('.dat') and isinstance(p.get('color'),int)for p in s.get('parts',[])):
  actual=collections.Counter((source[i-1]['name'],source[i-1]['color'])for i in s['added_part_ids'])
  supplied=collections.Counter()
  for part in s.get('parts',[]):supplied[(part['name'],part['color'])]+=part['count']
  assert actual==supplied,(s['id'],actual,supplied)
  canonical_checked+=1
 introduced.update(s['added_part_ids'])
 assert {i for i in s['visible_part_ids']if i<=192}<=introduced,(s['id'],'Visible core part was not introduced yet')
 added+=s['added_part_ids']
 if not s.get('image_url'):
  assert book['data_status']=='partial','Final book missing step image'
  continue
 p=root/'dist'/s['image_url'];assert p.is_file(),p
 with Image.open(p)as im: im.verify()
 image_stats.append({'id':s['id'],'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
assert not[k for k,v in collections.Counter(added).items()if v>1], 'Duplicate core installation'
missing=sorted(set(range(1,193))-set(added))
if book['data_status']!='partial':assert not missing,missing
h=(root/'dist/index.html').read_text()
class Parser(HTMLParser):
 def __init__(self):super().__init__();self.ids=[];self.links=[]
 def handle_starttag(self,t,a):
  d=dict(a)
  if'id'in d:self.ids.append(d['id'])
  if'href'in d:self.links.append(d['href'])
p=Parser();p.feed(h);assert len(p.ids)==len(set(p.ids))
assert all(x[1:]in p.ids for x in p.links if x.startswith('#'))
assert not re.search('__\\w+_DATA__',h)
assert '[object Object]'not in h
result={'status':book['data_status'],'steps':len(steps),'modules':len(set(s['module_id']for s in steps)),'corePartsCovered':len(set(added)),'missingCoreParts':missing,'singleInstallPerCorePart':True,'visibleCorePartsPreviouslyIntroduced':True,'maxPartsPerStep':max(len(s['added_part_ids'])for s in steps),'canonicalPartListsVerified':canonical_checked,'imagesVerified':len(image_stats),'imageBytes':sum(x['bytes']for x in image_stats),'uniqueElementIDs':True,'allAnchorTargetsPresent':True,'sourceSHA256':book.get('source_sha256'),'browserVisualValidation':'unavailable: cloud local preview previously blocked; no bypass'}
(root/'step-book-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
(root/'step-image-integrity.json').write_text(json.dumps(image_stats,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
