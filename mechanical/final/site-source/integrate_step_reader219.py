from pathlib import Path
import json,re,sys,shutil,hashlib
root=Path(__file__).resolve().parent
if len(sys.argv)<2:raise SystemExit('Provide the audited219 instruction JSON; never infer from the old192 book')
input_path=Path(sys.argv[1]).resolve();raw=json.loads(input_path.read_text())
hand=json.loads((root.parent/'lift-feasibility/detailed-instructions-192/inventory-compatible-candidate/viewer-handoff219.json').read_text())
assert raw.get('core_count',raw.get('core_part_count'))==219,'Instruction book must explicitly target219 parts'
assert raw.get('source_assembly_sha256')==hand['source_assembly_sha256'],'New instructions must match frozen219 assembly'
assert raw.get('steps'),'No actual steps supplied'
book={k:raw[k]for k in ['title','data_status','subassembly_titles']if k in raw};book.update(core_count=219,source_sha256=hand['source_assembly_sha256'],source_mpd_sha256=hand['source_mpd_sha256'],steps=[])
assets=root/'dist/steps219';assets.mkdir(exist_ok=True)
for i,original in enumerate(raw['steps']):
 s=dict(original);assert s.get('id')and s.get('module_id')and s.get('title')
 assert isinstance(s.get('added_part_ids'),list)and isinstance(s.get('visible_part_ids'),list)
 if s.get('original_module_part_ids'):raise AssertionError('Original module installation is still on hold; require a new authorized handoff')
 if s.get('image_path'):
  image_path=Path(s['image_path']);image_path=image_path if image_path.is_absolute()else input_path.parent/image_path
  assert image_path.is_file();filename=s['id'].lower()+image_path.suffix.lower();assert '/'not in filename and '\\'not in filename
  shutil.copy2(image_path,assets/filename);s['image_url']='steps219/'+filename
 else:s['image_url']=None
 for p in s.get('parts',[]):
  stem=p['name'].removesuffix('.dat');matches=[d for d in s.get('parts_source_descriptions',[])if d.get('name','').startswith(stem)and d.get('count')==p.get('count')]
  p['display_name']=matches[0]['name']if len(matches)==1 else p.get('display_name',stem)
 s.pop('image_path',None);s['step_number']=i+1;book['steps'].append(s)
book['covered_core_count']=len({n for s in book['steps']for n in s['added_part_ids']})
if (root/'load-hold.json').exists():book['load_test_status']=json.loads((root/'load-hold.json').read_text())['status']
(root/'instruction-book219.json').write_text(json.dumps(book,ensure_ascii=False,indent=2)+'\n')
h=(root/'preview219/index.html').read_text();assert 'window.ASSEMBLY_BOOK='not in h
h=h.replace("img-src data:;","img-src 'self' data:;")
h=h.replace('>说明修订状态</a>','>219件一步一步搭建</a>')
h,n=re.subn(r'<section id="step-builder".*?</section>',(root/'step-reader.html').read_text(),h,count=1,flags=re.S);assert n==1
h=h.replace('</style>',(root/'step-reader.css').read_text()+'</style>',1)
h=h.replace('<p class="hint">','<div class="bar" id="v3d-step-nav" hidden><button id="step-previous-top" type="button">上一步</button><span id="step-top-counter"></span><button id="step-next-top" type="button">下一步</button><a href="#step-builder">查看图文</a></div><p class="hint">',1)
bootstrap='<script>'+ (root/'step-reader-core.js').read_text()+'\nwindow.ASSEMBLY_BOOK='+json.dumps(book,ensure_ascii=False).replace('<','\\u003c')+';</script>'
h=h.replace('<script>window.V3D_STEPS=',bootstrap+'\n<script>window.V3D_STEPS=',1)
h=h.replace('let liftDown=false, liftOnly=false;',(root/'step-reader-bridge.js').read_text()+'\nlet liftDown=false, liftOnly=false;',1)
h=h.replace('function applyLiftView(){\n if(!group)return;','function applyLiftView(){\n if(!group)return;\n assemblyStep=null;restoreAssemblyMaterials();cubeRef.visible=true;document.dispatchEvent(new Event("v3d-normal-mode"));',1)
h=h.replace('o.userData.hiMaterial = Array.isArray(o.material) ? hi : hi[0];','''o.userData.hiMaterial = Array.isArray(o.material) ? hi : hi[0];
 const stepHi=mats.map(m=>{const k=m.clone();k.color=new THREE.Color(0xffb600);k.emissive=new THREE.Color(0x553000);return k});
 o.userData.stepHighlightMaterial=Array.isArray(o.material)?stepHi:stepHi[0];''',1)
h=h.replace("if (!group || e.ctrlKey || e.metaKey || e.altKey) return;","if (!group || e.ctrlKey || e.metaKey || e.altKey || e.target.closest?.('#step-builder, #v3d-step-nav')) return;",1)
h=h.replace('</script></html>','</script><script>'+ (root/'step-reader-ui.js').read_text()+'</script></html>',1)
(root/'dist/index.html').write_text(h)
print(json.dumps({'core':219,'steps':len(book['steps']),'covered':book['covered_core_count'],'data_status':book.get('data_status'),'htmlBytes':len(h.encode())}))
