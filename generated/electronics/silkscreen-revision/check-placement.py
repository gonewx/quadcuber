import json,sys
from pathlib import Path
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from shapely.affinity import translate
p=Path(sys.argv[2]);d=json.loads(Path(sys.argv[1]).read_text())
def shape(polys):return unary_union([Polygon(q['outer'],q['holes']).buffer(0) for q in polys])
mask=unary_union([shape(x) for x in d['mask']]);silk=unary_union([shape(x) for x in d['silk']]);texts=[shape(t['after']) for t in d['texts']];outline=box(50.3,50.3,193.7,161.7)
results=[]
for i,t in enumerate(d['texts']):
 other=unary_union([silk]+[s for j,s in enumerate(texts) if j!=i]);old=texts[i]
 candidates=sorted([(round(x*.1,4),round(y*.1,4)) for x in range(-20,21) for y in range(-20,21)],key=lambda a:(a[0]**2+a[1]**2,abs(a[0]),abs(a[1])))
 found=None
 for dx,dy in candidates:
  sh=translate(old,dx,dy)
  if outline.contains(sh) and sh.distance(mask)>=.1501 and sh.distance(other)>=.1501:
   found=(dx,dy,sh);break
 if found:
  dx,dy,sh=found;texts[i]=sh;r={'id':t['id'],'text':t['text'],'before_xy':t['xy'],'after_xy':[round(t['xy'][0]+dx,6),round(t['xy'][1]+dy,6)],'mask_clearance':round(sh.distance(mask),6),'silk_clearance':round(sh.distance(other),6)}
 else:r={'id':t['id'],'text':t['text'],'FAIL':True,'before_xy':t['xy'],'original_clearance':[old.distance(mask),old.distance(other)]}
 results.append(r)
print(json.dumps([r for r in results if r.get('FAIL') or r['before_xy']!=r['after_xy']],indent=2))
p.write_text(json.dumps(results,indent=2))
assert all(not r.get('FAIL') and r['before_xy']==r['after_xy'] for r in results), 'Placement requires explicit review'
print('52 labels fit at original positions')
