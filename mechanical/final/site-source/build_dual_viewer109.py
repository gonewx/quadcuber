from pathlib import Path
import re,json,hashlib,ast,urllib.parse
root=Path(__file__).resolve().parent;src=root.parent/'lift-feasibility/pose-coupled-support-review/candidate109'
hand=json.loads((src/'viewer-handoff109.json').read_text());assembly=(src/'assembly109.json').read_bytes();assert hashlib.sha256(assembly).hexdigest()==hand['source_assembly_sha256']
files={'core_up':'candidate109-working.mpd','core_down':'candidate107-parked.mpd','whole_up':'candidate876-machine-working.mpd','whole_down':'candidate874-machine-parked.mpd'}
states={}
for key,name in files.items():
 b=(src/name).read_bytes();assert hashlib.sha256(b).hexdigest()==hand['files'][name];states[key]={'count':hand['states'][key],'source_file':name,'source_sha256':hand['files'][name],'model_text':b.decode()}
oldtemplate=(root.parent/'lift-feasibility/technic-seat-lift-160/technic-seat-lift-offline.html').read_text();large=next(s for s in re.findall(r'<script(?:\s[^>]*)?>([\s\S]*?)</script>',oldtemplate)if 'const THREE = 'in s);library=large[:large.index('try {\n// 说明书')]
tree=ast.parse((root/'build_viewer.py').read_text());css=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='css'for t in n.targets))
navcss='''.review-tabs{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 16px}.review-tabs a{display:block;min-height:44px;box-sizing:border-box;padding:10px 14px;border:1px solid #aac0d5;border-radius:6px;background:#fff;color:#17486f;font-size:15px;text-decoration:none}.review-tabs a[aria-current=page]{background:#153e5c;color:#fff;border-color:#153e5c}.review-alert{border:2px solid #b82424;background:#fff0ec;color:#7b1414;border-radius:8px;padding:14px 16px;margin:12px 0;font-size:16px;line-height:1.55}.review-alert strong{font-size:19px;display:block}.review-alert p{margin:6px 0}.review-alert .compact{font-size:14px}.review-risk{max-width:1200px;margin:16px 0;border:1px solid #cad5df;border-radius:6px;padding:12px 16px;background:white}.review-risk summary{cursor:pointer;font-weight:650;font-size:16px}.review-risk li{margin:8px 0;font-size:15px}.history-note{font-size:14px;color:#6b3333;padding:12px;border-left:4px solid #b82424;background:#fff8f5}.bar button{min-height:44px}.bar span{font-size:14px}#v3d{height:62vh;min-height:320px}#candidate-state-label{font-size:14px}button:disabled{opacity:.5;cursor:wait}.review-tabs a:focus-visible{outline:3px solid #1681dd;outline-offset:3px}@media(max-width:600px){.review-tabs a{flex:1;text-align:center;font-size:14px}.review-alert{padding:12px}.review-alert strong{font-size:18px}#v3d{height:52vh;min-height:300px}}'''
css+=navcss
favicon='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect x="2" y="2" width="28" height="28" rx="5" fill="#153e5c"/><path d="M8 24V8h5v10h6V8h5v16M8 18h16" fill="none" stroke="#f6c45e" stroke-width="2"/></svg>'
nav=lambda active:'<nav class="review-tabs" aria-label="模型与实测记录"><a href="index.html"'+(' aria-current="page"'if active=='new'else'')+'>新支承候选审阅</a><a href="history-219.html"'+(' aria-current="page"'if active=='history'else'')+'>219版失败记录／旧说明</a></nav>'
head='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'; base-uri 'none'; form-action 'none'"><title>新支承候选109 · 未完成，不可照搭</title><meta name="description" content="83件双侧支承与26件四点承托的可旋转候选审阅；定位边未完成、承重未实测，不可照搭。219实物下垂历史记录单独保留。">'''
head+='<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,'+urllib.parse.quote(favicon,safe='')+'"><style>'+css+'</style></head><body>'
body=nav('new')+'''<h1>新支承候选审阅 · 109件</h1><p class="intro">83件双侧短桥支承＋26件四点承托，仅供查看实际零件布局</p>
<div class="review-alert" role="alert"><strong>定位边未完成 · 承重未实测 · 不可照搭</strong><p>内部接合已做名义复核，实物表现仍待验证；滑槽销尖跨孔缘在约8／32毫米行程附近有卡滞风险。</p><p class="compact">这是未完成的新候选，不是已经通过施工或承载验收的版本。</p></div>
<div id="v3d" role="img" aria-label="未完成的新支承候选3D审阅" tabindex="0"><span id="v3d-status">正在解析候选模型…</span></div>
<div class="bar"><button id="v3d-fit" type="button">复位视角</button><button id="candidate-pose" type="button">查看下位端姿（40mm）</button><button id="candidate-scope" type="button">查看整机背景</button><span id="candidate-state-label" aria-live="polite"></span></div>
<p class="hint">拖动旋转 · 滚轮／双指缩放 · A/D、W/S旋转 · +/-缩放 · R复位</p><p id="candidate-pose-note" class="notes" aria-live="polite"></p>
<details class="review-risk"><summary>审阅范围、姿态与未解决风险</summary><ul>
<li>候选本体：固定30件、移动77件、可抽锁件2件。上位109件，下位移除2件锁后107件。</li>
<li>整机背景另加保留基础59件及原四臂708件：上位876件，下位874件。上位四头均张开50°；下位前后夹紧0°、左右仍开50°，不是正常还原姿态。</li>
<li>X／Z定位边尚未完成，当前只有承托面与接口候选，不能用作完整定位夹具。</li>
<li>109件合并源已做名义接合与40毫米平移复查；数字几何结果不能替代实物配合、摩擦与载荷验证。</li>
<li>滑槽销尖与滑面名义共面，跨孔缘可能卡滞；0.4毫米墙侧名义间隙没有实物余量保证。滑顺、刚度、载荷与保持力均未验收。</li>
<li>原8枚墙脚销仍是独立HOLD项，未在这次候选中修正。端姿切换只作几何展示。</li></ul></details>
<section id="step-builder" class="history-note"><b>本候选没有可施工说明书。</b>定位边和接合检查完成前，不把旧145步接到这个候选上。</section>
<p class="history-note"><b>219版历史实物失败：</b>已收到放入魔方即下垂的实物失败，承重待修，暂停带魔方运行。<a href="history-219.html">查看219版模型与145步诊断资料</a></p>'''
js='<script>window.CANDIDATE_STATES='+json.dumps(states,ensure_ascii=False).replace('<','\\u003c')+';window.CANDIDATE_COLOR_META='+json.dumps((root/'candidate-colors.ldr').read_text())+';</script><script>'+(root/'candidate-source-adapter.js').read_text()+(root/'candidate-view-core.js').read_text()+'</script><script>'+library+(root/'candidate-viewer-app.js').read_text()+'</script>'
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
(root/'candidate109-source.json').write_text(json.dumps({'source_directory':str(src),'assembly_sha256':hand['source_assembly_sha256'],'files':hand['files'],'state_counts':hand['states'],'role_counts':{'fixed':30,'moving':77,'keys':2},'review_only':True,'historical219_route':'history-219.html'},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'candidateHTML':(root/'dist/index.html').stat().st_size,'historyHTML':(root/'dist/history-219.html').stat().st_size,'states':hand['states'],'constructionQualified':False}))
