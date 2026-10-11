from pathlib import Path
import re,json,hashlib,ast,urllib.parse,shutil
root=Path(__file__).resolve().parent;src=root.parent/'lift-feasibility/pose-coupled-support-review/complete-seat-review'
hand=json.loads((src/'viewer-handoff-complete.json').read_text());assembly=(src/'assembly132.json').read_bytes();assert hashlib.sha256(assembly).hexdigest()==hand['source_assembly_sha256']
state_keys={'core_up':'core_working','core_down':'core_parked','whole_up':'machine_working','whole_down':'machine_parked'}
states={}
for key,source_key in state_keys.items():
 meta=hand['states'][source_key];name=meta['file'];b=(src/name).read_bytes();assert hashlib.sha256(b).hexdigest()==meta['sha256'];states[key]={'count':meta['count'],'source_file':name,'source_sha256':meta['sha256'],'model_text':b.decode()}
assert [states[k]['count'] for k in state_keys]==[132,130,899,897]
assert hand['role_counts']=={'fixed':30,'moving':100,'key':2}
book=json.loads((src/'detailed-steps132.json').read_text())
assert book['source_assembly_sha256']==hand['source_assembly_sha256']
book['parts']=json.loads(assembly)
assert len(book['parts'])==132
introduced=set();step_ids=set()
for step in book['steps']:
 assert step['id'] not in step_ids
 assert set(step.get('prerequisite_step_ids',[]))<=step_ids
 step_ids.add(step['id'])
 for field in ['added_part_ids','visible_part_ids','highlight_part_ids']:
  ids=step[field];assert len(ids)==len(set(ids)) and all(isinstance(i,int) and 1<=i<=132 for i in ids)
 added=set(step['added_part_ids']);visible=set(step['visible_part_ids'])
 assert not introduced&added
 introduced.update(added)
 assert added<=visible and set(step['highlight_part_ids'])<=visible and visible<=introduced
 assert len(added)<=4
assert introduced==set(range(1,133))
step_images={}
for step in book['steps']:
 image=src/step.get('image_file','missing.png')
 if image.is_file():
  target=root/'dist/candidate132-steps'/image.name
  target.parent.mkdir(parents=True,exist_ok=True)
  shutil.copyfile(image,target)
  step_images[step['id']]='candidate132-steps/'+image.name


oldtemplate=(root.parent/'lift-feasibility/technic-seat-lift-160/technic-seat-lift-offline.html').read_text();large=next(s for s in re.findall(r'<script(?:\s[^>]*)?>([\s\S]*?)</script>',oldtemplate)if 'const THREE = 'in s);library=large[:large.index('try {\n// 说明书')]
tree=ast.parse((root/'build_viewer.py').read_text());css=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='css'for t in n.targets))
navcss='''.review-tabs{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 16px}.review-tabs a{display:block;min-height:44px;box-sizing:border-box;padding:10px 14px;border:1px solid #aac0d5;border-radius:6px;background:#fff;color:#17486f;font-size:15px;text-decoration:none}.review-tabs a[aria-current=page]{background:#153e5c;color:#fff;border-color:#153e5c}.review-alert{border:2px solid #b82424;background:#fff0ec;color:#7b1414;border-radius:8px;padding:14px 16px;margin:12px 0;font-size:16px;line-height:1.55}.review-alert strong{font-size:19px;display:block}.review-alert p{margin:6px 0}.review-alert .compact{font-size:14px}.review-risk{max-width:1200px;margin:16px 0;border:1px solid #cad5df;border-radius:6px;padding:12px 16px;background:white}.review-risk summary{cursor:pointer;font-weight:650;font-size:16px}.review-risk li{margin:8px 0;font-size:15px}.history-note{font-size:14px;color:#6b3333;padding:12px;border-left:4px solid #b82424;background:#fff8f5}.bar button{min-height:44px}.bar span{font-size:14px}#v3d{height:62vh;min-height:320px}#candidate-state-label{font-size:14px}button:disabled{opacity:.5;cursor:wait}.review-tabs a:focus-visible{outline:3px solid #1681dd;outline-offset:3px}@media(max-width:600px){.review-tabs a{flex:1;text-align:center;font-size:14px}.review-alert{padding:12px}.review-alert strong{font-size:18px}#v3d{height:52vh;min-height:300px}}'''
css+=navcss+(root/'candidate-steps.css').read_text()
favicon='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect x="2" y="2" width="28" height="28" rx="5" fill="#153e5c"/><path d="M8 24V8h5v10h6V8h5v16M8 18h16" fill="none" stroke="#f6c45e" stroke-width="2"/></svg>'
nav=lambda active:'<nav class="review-tabs" aria-label="模型与实测记录"><a href="index.html"'+(' aria-current="page"'if active=='new'else'')+'>新支承候选审阅</a><a href="operation-guide.html">整机关系与放入／退出</a><a href="history-219.html"'+(' aria-current="page"'if active=='history'else'')+'>219版失败记录／旧说明</a></nav>'
head='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: 'self'; connect-src 'none'; base-uri 'none'; form-action 'none'"><title>新支承候选132 · 实物待验证</title><meta name="description" content="132件升降、托座与定位小样候选；另加59件复用底盘为191件，加原708件为899件整机。名义几何已审，承重、销尖滑动与半轴套保持未实测。">'''
head+='<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,'+urllib.parse.quote(favicon,safe='')+'"><style>'+css+'</style></head><body>'
body=nav('new')+'''<h1>新支承候选审阅 · 132件</h1><p class="intro">升降支承＋托座＋X／Z定位边 · 仅供审阅的小样候选</p>
<p class="notes"><b>件数范围：</b>132件小样＋59件复用共同底盘＝191件；再加原四臂708件＝899件整机。旧219件包含底盘，比较时需使用同一范围。</p>
<div class="review-alert" role="alert"><strong>承重／销尖滑动／半轴套保持未实测 · 不可照搭运行</strong><p>X／Z定位边已纳入模型；名义几何与理想关节检查通过，尚未通过实物承载验收。</p><p class="compact">滑槽销尖跨孔缘在约8／32毫米行程附近仍可能卡滞，安装环境扫掠也未验证。几何检查不代表承重合格。</p></div>
<div class="candidate-workbench"><div class="candidate-canvas-column"><div class="candidate-mode"><button id="mode-steps" type="button" aria-pressed="true">逐步审阅</button><button id="mode-full" type="button" aria-pressed="false">完整模型</button></div><div id="v3d" role="img" aria-label="132件新支承小样候选3D审阅" tabindex="0"><span id="v3d-status">正在解析候选模型…</span><p id="candidate-empty" class="candidate-empty" hidden></p></div>
<div class="bar"><button id="v3d-fit" type="button">复位视角</button><button id="candidate-pose" type="button">查看下位端姿（40mm）</button><button id="candidate-scope" type="button">查看整机背景</button><span id="candidate-state-label" aria-live="polite"></span></div>
<div class="step-legend"><span>新增／合并重点</span><span>本地已有组件</span></div><p class="hint">拖动旋转 · 滚轮／双指缩放 · A/D、W/S旋转 · +/-缩放 · R复位</p><p id="candidate-pose-note" class="notes" aria-live="polite"></p>
</div>STEP_READER_MARKER</div><details class="review-risk"><summary>审阅范围、姿态与未解决风险</summary><ul>
<li>132件小样包含83件支承、25件托座、9件Z定位边及15件X定位边。固定30件、移动100件、可抽锁件2件；下位移除2件锁后130件。</li>
<li>59件复用共同底盘和原四臂708件单独计入整机背景：上位899件，下位897件。上位四头均张开50°；下位前后夹紧0°、左右仍开50°，不是正常还原姿态。</li>
<li>X／Z两面用于手动贴边定位，没有自动弹簧对中功能。模型为56毫米名义魔方设置定位基准，实物配合仍须验证。</li>
<li>来源模型接合与运动空间、定位增量的名义几何与理想关节已审；理想关节检查不等于实体的刚度、承载、摩擦或保持力验收。</li>
<li>滑槽销尖与滑面名义共面，跨孔缘可能卡滞；0.4毫米墙侧名义间隙没有实物余量保证。销尖滑动、半轴套保持、刚度和承重均未实测。</li>
<li>安装环境扫掠尚未验证。这里的两端姿仅用于几何审阅，不表示可在整机中按图装入或运行。</li>
<li>原8枚墙脚销仍是独立HOLD项，未在这次候选中修正。上、下位分别读取实际来源文件。</li></ul></details>

<p class="history-note"><b>219版历史实物失败：</b>已收到放入魔方即下垂的实物失败，承重待修，暂停带魔方运行。<a href="history-219.html">查看219版模型与145步诊断资料</a></p>'''
body=body.replace('STEP_READER_MARKER',(root/'candidate-steps.html').read_text())
js='<script>window.CANDIDATE_STATES='+json.dumps(states,ensure_ascii=False).replace('<','\\u003c')+';window.CANDIDATE_COLOR_META='+json.dumps((root/'candidate-colors.ldr').read_text())+';window.CANDIDATE_STEP_BOOK='+json.dumps(book,ensure_ascii=False).replace('<','\\u003c')+';window.CANDIDATE_STEP_IMAGES='+json.dumps(step_images)+';</script><script>'+(root/'candidate-source-adapter.js').read_text()+(root/'candidate-view-core.js').read_text()+(root/'candidate-steps-core.js').read_text()+'</script><script>'+library+(root/'candidate-viewer-app.js').read_text()+'</script><script>'+(root/'candidate-steps-ui.js').read_text()+'</script>'
(root/'dist/index.html').write_text(head+body+js+'</body></html>')
# Preserve the failed219 model and instruction dataset as a separate diagnostic route.
base=root/'history219-source.html'
assert base.exists(),'Freeze current published219 HTML before building the new default'
history=base.read_text();history=history.replace('</style>',navcss+'</style>',1)
history=history.replace('<div id="load-test-alert"',nav('history')+'<div id="load-test-alert"',1)
history=history.replace('实际反馈：放入魔方后出现整体下垂。当前承载问题仍在诊断，请暂停带魔方运行。','已收到放入魔方即下垂的实物失败，承重待修，暂停带魔方运行。本页保留失败记录及原模型供诊断，不推断实物故障位置。')
history=history.replace('<h1>共用底盘 219 · 承载诊断中</h1>','<h1>219版实物失败 · 历史诊断</h1>')
history=history.replace('<title>共用底盘 219 · 承载诊断中</title>','<title>219版实物失败记录 · 仅供诊断</title>')
history=history.replace('<h2 id="step-book-title">一步一步搭建</h2>','<h2 id="step-book-title">145步旧说明 · 仅供历史诊断</h2>')
(root/'dist/history-219.html').write_text(history)
(root/'candidate132-source.json').write_text(json.dumps({'source_directory':str(src),'assembly_sha256':hand['source_assembly_sha256'],'states':hand['states'],'role_counts':hand['role_counts'],'functional_counts':hand['functional_counts'],'review_only':True,'small_sample_count':132,'common_chassis_count':191,'whole_count':899,'detailed_step_count':len(book['steps']),'step_source_sha256':hashlib.sha256((src/'detailed-steps132.json').read_bytes()).hexdigest(),'historical219_route':'history-219.html'},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'candidateHTML':(root/'dist/index.html').stat().st_size,'historyHTML':(root/'dist/history-219.html').stat().st_size,'states':{k:v['count'] for k,v in states.items()},'detailedSteps':len(book['steps']),'introducedParts':len(introduced),'constructionQualified':False}))

# Independent whole-machine relationship and placement/withdrawal guide.
import subprocess, sys
subprocess.run([sys.executable, str(root/'build_operation_guide132.py')], check=True)
