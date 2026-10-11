from pathlib import Path
import json,shutil,base64,hashlib,sys
root=Path(__file__).resolve().parent
input_path=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else root.parent/'lift-feasibility/detailed-instructions-192/instructions.json'
if not input_path.exists():raise SystemExit('Actual instruction dataset not ready; do not publish placeholders')
raw=json.loads(input_path.read_text());assert raw.get('steps'), 'No real steps'
book={k:raw[k] for k in ['data_status','subassembly_titles'] if k in raw};book['source_sha256']=raw.get('source_assembly_sha256',raw.get('source_sha256'));book['steps']=[]
assets=root/'dist/steps';assets.mkdir(exist_ok=True)
# Preserve stable IDs. Read only explicit authored membership; never infer assembly order.
for i,original in enumerate(raw['steps']):
 s=dict(original);assert s.get('id') and s.get('module_id') and s.get('title')
 assert isinstance(s.get('added_part_ids'),list) and isinstance(s.get('visible_part_ids'),list)
 if s.get('original_module_part_ids'):s['visible_part_ids']=sorted(set(s['visible_part_ids']+s['original_module_part_ids']))
 image_path=s.get('image_path')
 if image_path:
  source=Path(image_path);source=source if source.is_absolute() else input_path.parent/source
  assert source.is_file(),str(source)
  filename=s['id'].lower()+source.suffix.lower();assert '/' not in filename and '\\' not in filename
  shutil.copy2(source,assets/filename);s['image_url']='steps/'+filename
 else:s['image_url']=None
 for part in s.get('parts',[]):
  stem=part['name'].removesuffix('.dat');matches=[p for p in s.get('parts_source_descriptions',[]) if p.get('name','').startswith(stem) and p.get('count')==part.get('count')]
  part['display_name']=matches[0]['name'] if len(matches)==1 else part['name'].removesuffix('.dat')
 s.pop('image_path',None);s['step_number']=i+1
 book['steps'].append(s)
book['covered_core_count']=len({n for step in book['steps']for n in step['added_part_ids']})
if (root/'inventory-hold.json').exists():
 hold=json.loads((root/'inventory-hold.json').read_text());book['inventory_hold']=hold;book['data_status']='inventory_hold'
 for step in book['steps']:
  if step['module_id'] in hold['blocked_module_ids']:
   step['construction_status']='paused';step['hold_reason']=' '.join(issue['reason']for issue in hold.get('issues',[hold])if step['module_id']in issue['blocked_module_ids'])
# Generated asset manifest is for reproducible source and checks, not an extra page.
(root/'instruction-book.json').write_text(json.dumps(book,ensure_ascii=False,indent=2))
h=(root/'dist/index.html').read_text()
h=h.replace('当前可用范围：角舱16步。','当前可用范围：'+str(len(book['steps']))+'步，覆盖'+str(book['covered_core_count'])+'/192件。')
if book.get('inventory_hold'):
 banner='<div id="inventory-alert" class="inventory-alert" role="alert"><strong>库存警示：当前模型待修订，相关步骤暂停</strong><p>39790框：库存4个，现版需要5个。第53步（MST-01）额外用了第5个框，立柱及依赖装配暂停施工。</p><p>71709面板：库存0个，现版需要1个。第84步（SEAT-03）使用该面板，承托座、悬臂接合及依赖装配暂停施工。</p><p>正在统一核对库存后重设计；本页没有采用任何替代件。基础、29件角舱及独立滑架步骤未因这两项缺件暂停。</p><p>原四臂接口的8枚墙脚销仍是独立待批准修正项，尚未修复。</p></div>'
 h=h.replace('<h1>共用底盘 192</h1>',banner+'<h1>共用底盘 192 · 待修订</h1>',1)
 h=h.replace('名义几何复核版 · 实物待验收','库存不足 · 立柱与承托座相关步骤暂停')
 h=h.replace('192件名义几何复核版，实物待验收。','旧版结构参考：39790与71709库存不足，相关步骤暂停。')
 h=h.replace('本版名义几何已复核：','旧版名义几何记录仅供审阅，库存问题尚未修复：')
 h=h.replace('当前可用范围：'+str(len(book['steps']))+'步，覆盖'+str(book['covered_core_count'])+'/192件。','旧版记录仅供审阅：库存不足，立柱与承托座相关65步暂停施工。')
assert '<section id="step-builder"' not in h
h=h.replace('其中第132件修正为6558销，挡肩位于单面孔入口侧','承托座采用修正后的6558销，挡肩位于凹口侧')
h=h.replace("img-src data:;", "img-src 'self' data:;")
h=h.replace('href="#assembly">搭建步骤','href="#step-builder">一步一步搭建')
h=h.replace('<section id="assembly"',(root/'step-reader.html').read_text()+'\n<details class="guide-reference"><summary>分组总览与结构参考</summary><section id="assembly"',1)
h=h.replace('</section>\n<script>window.V3D_STEPS=','</section></details>\n<script>window.V3D_STEPS=',1)
h=h.replace('<p class="hint">','<div class="bar" id="v3d-step-nav" hidden><button id="step-previous-top" type="button">上一步</button><span id="step-top-counter"></span><button id="step-next-top" type="button">下一步</button><a href="#step-builder">查看图文</a></div><p class="hint">',1)
h=h.replace('</style>',(root/'step-reader.css').read_text()+'</style>',1)
bootstrap='<script>'+ (root/'step-reader-core.js').read_text()+'\nwindow.ASSEMBLY_BOOK='+json.dumps(book,ensure_ascii=False).replace('<','\\u003c')+';</script>'
h=h.replace('<script>window.V3D_STEPS=',bootstrap+'\n<script>window.V3D_STEPS=',1)
bridge=(root/'step-reader-bridge.js').read_text()
h=h.replace('let liftDown=false, liftOnly=false;',bridge+'\nlet liftDown=false, liftOnly=false;',1)
h=h.replace('function applyLiftView(){\n if(!group)return;','function applyLiftView(){\n if(!group)return;\n assemblyStep=null;restoreAssemblyMaterials();cubeRef.visible=true;document.dispatchEvent(new Event("v3d-normal-mode"));',1)
h=h.replace('o.userData.hiMaterial = Array.isArray(o.material) ? hi : hi[0];','''o.userData.hiMaterial = Array.isArray(o.material) ? hi : hi[0];
    const stepHi=mats.map(m=>{const k=m.clone();k.color=new THREE.Color(0xffb600);k.emissive=new THREE.Color(0x553000);return k});
    o.userData.stepHighlightMaterial=Array.isArray(o.material)?stepHi:stepHi[0];''',1)
h=h.replace("if (!group || e.ctrlKey || e.metaKey || e.altKey) return;","if (!group || e.ctrlKey || e.metaKey || e.altKey || e.target.closest?.('#step-builder, #v3d-step-nav')) return;",1)
h=h.replace('</script></html>','</script><script>'+ (root/'step-reader-ui.js').read_text()+'</script></html>',1)
(root/'dist/index.html').write_text(h)
print(json.dumps({'steps':len(book['steps']),'data_status':book.get('data_status'),'imageBytes':sum(p.stat().st_size for p in assets.iterdir()),'htmlBytes':len(h.encode())}))
