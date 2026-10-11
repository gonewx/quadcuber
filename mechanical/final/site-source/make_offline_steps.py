from pathlib import Path
import json,base64,mimetypes,hashlib
root=Path(__file__).resolve().parent
h=(root/'dist/index.html').read_text();book=json.loads((root/'instruction-book.json').read_text())
for s in book['steps']:
 url=s.get('image_url')
 if not url:continue
 path=root/'dist'/url
 data='data:'+ (mimetypes.guess_type(path.name)[0] or 'image/png')+';base64,'+base64.b64encode(path.read_bytes()).decode()
 old='"image_url": '+json.dumps(url);assert old in h,url
 h=h.replace(old,'"image_url": '+json.dumps(data),1)
out=root.parent/'shared-chassis-offline/quadcuber-shared-chassis-192-offline.html';out.parent.mkdir(exist_ok=True);out.write_text(h)
assert '"image_url": "steps/' not in h
print(json.dumps({'offlinePath':str(out),'bytes':out.stat().st_size,'stepImagesEmbedded':sum(bool(s.get('image_url'))for s in book['steps']),'sha256':hashlib.sha256(out.read_bytes()).hexdigest()}))
