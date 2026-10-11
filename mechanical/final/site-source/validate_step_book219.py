from pathlib import Path
import json,collections,hashlib,re
from html.parser import HTMLParser
from PIL import Image
root=Path(__file__).resolve().parent
book=json.loads((root/'instruction-book219.json').read_text());assert book['core_count']==219
source_path=root.parent/'lift-feasibility/detailed-instructions-192/inventory-compatible-candidate/assembly-candidate219.json'
source=json.loads(source_path.read_text());assert hashlib.sha256(source_path.read_bytes()).hexdigest()==book['source_sha256']
steps=book['steps'];assert steps
assert len({s['id']for s in steps})==len(steps)
added=[];images=[];introduced=set();unprovided_prerequisites={}
for s in steps:
 assert s.get('title')and s.get('module_title');assert isinstance(s['instructions'],list)
 assert all(isinstance(t,str)for t in s['instructions'])
 assert len(s['added_part_ids'])<=4
 assert all(isinstance(i,int)and 1<=i<=219 for i in s['added_part_ids'])
 assert len(s['added_part_ids'])==len(set(s['added_part_ids']))
 assert set(s['added_part_ids'])<=set(s['visible_part_ids'])
 assert set(s.get('highlight_part_ids',s['added_part_ids']))<=set(s['visible_part_ids'])
 assert all(1<=i<=219 for i in s['visible_part_ids']),'Original module installation is not approved'
 supplied=collections.Counter()
 for p in s.get('parts',[]):
  assert p['name'].endswith('.dat')and isinstance(p.get('color'),int)
  supplied[(p['name'],p['color'])]+=p['count']
 actual=collections.Counter((source[i-1]['name'],source[i-1]['color'])for i in s['added_part_ids']);assert actual==supplied,s['id']
 introduced.update(s['added_part_ids']);missing_prereq=set(s['visible_part_ids'])-introduced
 if missing_prereq:
  assert book['data_status']=='partial',s['id']
  assert missing_prereq<=set(s.get('prerequisite_part_ids',[])),(s['id'],sorted(missing_prereq))
  unprovided_prerequisites[s['id']]=sorted(missing_prereq)
 added+=s['added_part_ids']
 if not s.get('image_url'):
  assert book['data_status']=='partial';continue
 p=root/'dist'/s['image_url'];assert p.is_file()
 with Image.open(p)as im:im.verify()
 images.append({'id':s['id'],'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
assert all(n==1 for n in collections.Counter(added).values())
missing=sorted(set(range(1,220))-set(added))
if book['data_status']!='partial':assert not missing
h=(root/'dist/index.html').read_text()
class Parser(HTMLParser):
 def __init__(self):super().__init__();self.ids=[];self.links=[]
 def handle_starttag(self,t,a):
  d=dict(a)
  if'id'in d:self.ids.append(d['id'])
  if'href'in d:self.links.append(d['href'])
p=Parser();p.feed(h);assert len(p.ids)==len(set(p.ids));assert all(l[1:]in p.ids for l in p.links if l.startswith('#'))
embedded=json.loads(re.search(r'window.ASSEMBLY_BOOK=([\s\S]*?);</script>',h)[1]);assert embedded==book
assert '旧137步属于192件版本'not in h,'Old placeholder must be replaced by actual219 book'
result={'status':book['data_status'],'core':219,'steps':len(steps),'modules':len({s['module_id']for s in steps}),'partsCovered':len(set(added)),'missing':missing,'singleInstallPerPart':True,'maxNewParts':max(len(s['added_part_ids'])for s in steps),'canonicalPartListsVerified':len(steps),'explicitUnprovidedPrerequisites':unprovided_prerequisites,'imagesVerified':len(images),'imageBytes':sum(i['bytes']for i in images),'sourceSHA256':book['source_sha256'],'browserVisualValidation':'unverified'}
(root/'step-book219-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
