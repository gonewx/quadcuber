"""Build every current route from the single frozen integrated candidate."""
from pathlib import Path
import json,re,shutil,hashlib,html,csv,tempfile
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'mechanical'))
from paths import OUTPUT, ASSEMBLY
from resource_paths import canonicalize
_stage=tempfile.TemporaryDirectory(prefix='quadcuber-web-')
R=Path(__file__).resolve().parent;C=OUTPUT;D=Path(_stage.name);I=D/'integrated';I.mkdir(exist_ok=True)
manifest=json.loads((C/'candidate-manifest.json').read_text()); guide=json.loads((C/'manual/guide.json').read_text())
revision=guide['revision']
for step in guide['steps']:
 target=I/step['image'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(C/'manual'/step['image'],target)
# Current model folder is an exact manifest projection; no stale lock-pin states.
for stale in (I/'models').glob('*.mpd'):
 if stale.name not in {Path(r['file']).name for r in manifest.values()}:stale.unlink()
for folder in ['models','manual/diagrams']:
 shutil.copytree(C/folder,I/('diagrams' if folder.endswith('diagrams') else folder),dirs_exist_ok=True)
for src,dst in [('candidate-manifest.json','manifest.json'),('manual/guide.json','guide.json'),('manual/manual.pdf','manual.pdf'),('integrated-BOM.csv','integrated-BOM.csv'),('assembly-integrated132.json','assembly.json'),('baseline-diff.json','baseline-diff.json'),('subsystem-BOM.csv','subsystem-BOM.csv'),('instance-inventory.csv','instance-inventory.csv')]:
 shutil.copyfile(C/src,I/dst)
for row in manifest.values():assert hashlib.sha256((I/row['file']).read_bytes()).hexdigest()==row['sha256']
nav='<nav aria-label="整合版导航"><a href="index.html">整合版整机／动作关系</a><a href="integrated-assembly.html">完整装配说明</a><a href="integrated-support.html">支承逐步3D</a><a href="index.html#bom">整机零件表</a></nav>'
css='''*{box-sizing:border-box}body{margin:0;font:17px/1.75 system-ui,sans-serif;color:#183046;background:#eef3f7}header,main,footer,.integrated-shell{max-width:1300px;margin:auto;padding:20px}nav{display:flex;gap:12px;flex-wrap:wrap;padding:8px 0}nav a{padding:8px 12px;background:#fff;border:1px solid #c1d3df;border-radius:7px;text-decoration:none}a{color:#075ba3}h1{font-size:30px;line-height:1.3}h2{font-size:24px}.warning{padding:16px;background:#fff1d2;border-left:5px solid #cc8400;border-radius:7px}.step,.panel{background:white;padding:24px;margin:22px 0;border-radius:12px;scroll-margin-top:16px}.step img{display:block;width:100%;height:auto}.num{display:inline-block;background:#123d62;color:white;border-radius:7px;padding:3px 12px;margin-right:12px}.parts{font-weight:700;color:#006d70}.check{padding:14px;background:#eaf5f4;border-radius:7px}ol{padding-left:1.5em}li{padding:4px 0}details{padding:16px;background:white}summary{cursor:pointer;font-weight:700}.toc{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px 24px}.downloads{display:flex;gap:16px;flex-wrap:wrap;padding:12px 0}.caption,small{font-size:14px;color:#526777}.bom{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}.bom th,.bom td{padding:8px;border-bottom:1px solid #dde6ec;text-align:left}.bom tr.change{background:#eaf5f4}code{overflow-wrap:anywhere}@media(max-width:650px){header,main,footer,.integrated-shell{padding:14px}.step,.panel{padding:16px}.toc{grid-template-columns:1fr}h1{font-size:26px}nav{gap:6px}nav a{font-size:14px;padding:6px}}'''
def page(title,body,scripts='',extra_css=''):
 return '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+title+'</title><style>'+css+extra_css+'</style></head><body>'+body+scripts+'</body></html>'
warning='<div class="warning"><b>整合设计候选，尚未通过实体装配、承载或带电验收。</b>支承总成含20件重力回落杠杆。只有持续按住外柄才保持上位；夹头可靠接管后缓松回落40.8毫米。无阻尼，不保证实物自落、刚度或回落冲击安全。外柄对新桌面约33毫米、对新增梁约9毫米名义间隙，手只从末端三孔区域上方按压。'+html.escape(guide.get('hold_summary',''))+'</div>'

downloads='<div class="downloads"><a download href="integrated/manual.pdf">完整PDF</a><a download href="integrated/full-revision.zip">模型／构建源文件（完整图解PDF另下）</a><a download href="integrated/models/loading-all50.mpd">整机MPD</a><a download href="integrated/final-BOM.csv">整机BOM</a><a download href="integrated/subsystem-BOM.csv">分组件／颜色BOM</a></div>'
# Whole-machine operation UI is the primary view, using only integrated geometries.
g=json.loads((R/'operation-template.json').read_text())
mapping={'load_empty':'loading-all50','cube_above':'loading-all50','seated':'loading-all50','fb_ready':'FB0-open','fb_holds':'FB0-held','unlocked_up':'support-held','parked_fb':'support-down40_8','lr_ready':'LR90-open','both_hold':'both-held'}
for key,s in g['states'].items():
 row=manifest[mapping[key]];s.update(model_text=(C/row['file']).read_text(),count=row['parts'],sha256=row['sha256'],file='integrated/'+row['file'],mechanical_key=mapping[key]);s.pop('diagram_file',None)
 s['arms_zh']='；'.join(k+'：朝向'+str(v['angle_deg'])+'°，'+('夹指开25°／空头' if v['jaw']=='open' else '夹持') for k,v in s['heads'].items())
for stage in g['stages']:
 for key in ['diagram_file','diagram_alt_zh','diagram_caption_zh']:stage.pop(key,None)
 stage['cautions_zh']=['本页全部阶段为同一整合候选。正常夹指仅25°；实体承载与控制联锁未放行。']+stage.get('cautions_zh',[])
g.update(revision=revision,candidate='integrated',candidate_manifest=manifest,review_only=True,source_model_sha256=manifest['loading-all50']['sha256'],source_assembly_sha256=hashlib.sha256((C/'assembly-integrated132.json').read_bytes()).hexdigest())
g['title_zh']='整合版整机与魔方放入／撤座／取出'
from gravity_operation import update as update_gravity_operation
g=update_gravity_operation(g)
(I/'operation-guide.json').write_text(json.dumps(g,ensure_ascii=False,indent=2))
native=json.loads((R/'native-presentation.json').read_text());library=native['library']
body=(R/'operation-guide.html').read_text();body=body.replace('<h1>整机关系与放入／退出</h1>','<h1>整合版 · 整机与动作关系</h1>');body=body.replace('132件小样怎样接在原四臂之间，以及魔方放入、夹持交接、托座下移与退出的设计关系','120件闭环底盘、四个60483机械头、150件支承总成。整机与装配说明采用同一946件最终结构。')
body=body.replace('RELATIONSHIP_CONTENT','<ul>'+''.join('<li>'+x+'</li>'for x in g['relationship_zh'])+'</ul>').replace('WARNING_CONTENT',warning)
body=body.replace('href="index.html">回到132件／80步逐步审阅','href="integrated-assembly.html">打开完整装配说明').replace(' · <a href="history-219.html">219版实物失败记录</a>','')
body=body.replace('132件小样怎样接在原四臂之间，以及魔方放入、夹持交接、托座下移与退出的设计关系','946件整机与20件重力回落杠杆：按住抬起，夹头可靠接管后缓松回落').replace('<dt>两枚锁件</dt>','<dt>上位保持</dt>').replace('先让手、工具完全离开四臂与托座的运动区域，再讨论电机动作。不得一边伸手托扶，一边驱动电机。','按压手只在外柄末端三孔上方；放取魔方的手和工具须完全离开四臂及托座运动区域。外柄手部隔离和控制联锁尚待实体验证，验证前不带电执行。')
rows=list(csv.DictReader((C/'integrated-BOM.csv').open()))
bom='<section class="panel" id="bom"><h2>最终整机零件表</h2><p>与946件整机模型逐实例一致。仅列最终结构所用零件；颜色见分组件BOM。</p><table class="bom"><thead><tr><th>设计号</th><th>数量</th></tr></thead><tbody>'+''.join('<tr><td>'+r['part']+'</td><td>'+r['quantity']+'</td></tr>'for r in rows if int(r['quantity'])>0)+'</tbody></table></section>'
# Public download is the final inventory; comparison provenance stays in the source archive.
with (I/'final-BOM.csv').open('w') as f:
 w=csv.DictWriter(f,lineterminator='\n',fieldnames=['part','quantity']);w.writeheader();w.writerows({k:r[k] for k in ['part','quantity']}for r in rows if int(r['quantity'])>0)

js='window.OPERATION_GUIDE='+json.dumps(g,ensure_ascii=False).replace('<','\\u003c')+';window.CANDIDATE_COLOR_META='+json.dumps((R/'candidate-colors.ldr').read_text())+';'
for f in ['candidate-source-adapter.js','operation-guide-core.js','operation-viewer-app.js','operation-guide-ui.js']:js+=(R/f).read_text()+'\n'
(D/'index.html').write_text(page('Quadcuber整合版 · 设计候选','<div class="integrated-shell">'+nav+downloads+body+bom+'<footer>版本 '+html.escape(revision)+' · 整机SHA256 <code>'+manifest['loading-all50']['sha256']+'</code></footer></div>','<script>'+library+js+'</script>',(R/'operation-guide.css').read_text()))
# The full illustrated sequence is a single continuous document.
content='<header>'+nav+'<h1>整合版 · 完整装配说明</h1>'+warning+downloads+'<p>'+'本说明连续覆盖：120件闭环底盘从零装配（' + str(guide['coverage'].get('base_steps',33)) + '步）、150件支承总成（含20件杠杆）的详细装配（'+str(guide['coverage']['support_steps'])+'步）、四个机械臂组件的最终装配、墙脚接口、总装核对及按压操作。整机模型和BOM覆盖全部946件；四臂与底盘均从清单单件开始，没有预装核心。'+'</p><details><summary>完整步骤目录</summary><div class="toc">'+''.join('<a href="#step-'+str(s['id'])+'">'+str(s['id'])+' '+html.escape(s['title'])+'</a>'for s in guide['steps'])+'</div></details></header><main>'
last=None
for s in guide['steps']:
 if s.get('phase')!=last:last=s.get('phase');content+='<h2>'+html.escape(str(last or '装配'))+'</h2>'
 content+='<section class="step" id="step-'+str(s['id'])+'"><h2><span class="num">'+str(s['id'])+'</span>'+html.escape(s['title'])+'</h2><p class="parts">'+html.escape(s.get('parts',''))+'</p><a target="_blank" rel="noopener" href="integrated/'+s['image']+'"><img loading="lazy" src="integrated/'+s['image']+'" alt="'+html.escape(s['title'])+'，实际零件网格"></a><ol>'+''.join('<li>'+html.escape(t)+'</li>'for t in s['instructions'])+'</ol><p class="check"><b>核对：</b>'+html.escape(s['check'])+'</p></section>'
content+='</main><footer>'+nav+'<p>版本 '+html.escape(revision)+'。插入方向、静态接合及运动检查的适用范围见PDF；不代表实体装配路径、强度和防脱验收。</p></footer>'
(D/'integrated-assembly.html').write_text(page('Quadcuber整合版 · 完整装配说明',content))
# Preserve the detailed interactive support reader with regenerated mappings/images.
book=json.loads((ASSEMBLY/'support-steps.json').read_text());book['parts']=json.loads((C/'assembly-integrated132.json').read_text())
states={}
for k,n in {'core_up':'support-raised','core_down':'support-only-down40_8','whole_up':'loading-all50','whole_down':'support-down40_8'}.items():
 row=manifest[n];states[k]={'count':row['parts'],'source_file':row['file'],'source_sha256':row['sha256'],'model_text':(C/row['file']).read_text()}
step_images={s['source_step_id']:'integrated/'+s['image']for s in guide['steps']if s.get('source_step_id')and s['source_step_id'] in {q['id'] for q in book['steps']}}
workbench=native['support_shell']
workbench=workbench.replace('132','150').replace('40mm','40.8mm')
js='window.CANDIDATE_STATES='+json.dumps(states,ensure_ascii=False).replace('<','\\u003c')+';window.CANDIDATE_COLOR_META='+json.dumps((R/'candidate-colors.ldr').read_text())+';window.CANDIDATE_STEP_BOOK='+json.dumps(book,ensure_ascii=False).replace('<','\\u003c')+';window.CANDIDATE_STEP_IMAGES='+json.dumps(step_images)+';'
for f in ['candidate-source-adapter.js','candidate-view-core.js','candidate-steps-core.js']:js+=(R/f).read_text()+'\n'
viewer=(R/'candidate-viewer-app.js').read_text().replace('左右、前后四头均张开50°','四头均处50°装卸朝向，夹指正常开25°').replace('前后夹紧0°，左右仍张开50°','前后朝向0°并夹持，左右朝向50°且夹指开25°')
viewer=viewer.replace('40mm','40.8mm').replace('132件小样','150件支承总成')
step_ui=(R/'candidate-steps-ui.js').read_text().replace('create(book,132)','create(book,book.parts.length)').replace("+' / 132件'","+' / '+book.parts.length+'件'").replace("'阶段 '+s.stage+' · '","'阶段 '+(s.stage??'整合装配')+' · '").replace("s.view_note_zh||'最终接合姿态的名义图示，不代表安装扫掠已验证。'","s.pose_label||s.view_note_zh||'本步骤名义装配姿态，不代表安装扫掠已验证。'")
viewer=viewer.replace('CandidateStepsCore.prepare(group);const result=', 'GravityStepPose.apply(group,step);CandidateStepsCore.prepare(group);const result=').replace('CandidateStepsCore.restore(group);currentStep=null;', 'GravityStepPose.restore(group);CandidateStepsCore.restore(group);currentStep=null;').replace('本步零件使用冻结来源的最终坐标，仅隐藏无关组件并标记重点；不表示插入过程、承重或实物试装已验证。','本步3D只含支承／杠杆零件，原机接口参照对应图解。使用本步骤真实零件坐标，区分下位U组件和最终上位；不证明手部空间或实体验收。')
js+=library+(R/'gravity-step-pose.js').read_text()+viewer+step_ui
oldcss=native['support_css']
(D/'integrated-support.html').write_text(page('整合版 · 支承逐步3D','<div class="integrated-shell">'+nav+'<h1>整合版 · 支承逐步3D</h1><p>此处支承与主整机及完整说明书同源。底盘、机械臂组件装配及总装顺序请按<a href="integrated-assembly.html">完整说明</a>。</p>'+warning+workbench+'</div>','<script>'+js+'</script>',oldcss))
# Existing archival pages remain unlinked and are not regenerated.
(R/'CURRENT_VIEWER.json').write_text(json.dumps({'mode':'integrated review candidate','revision':revision,'default_route':'index.html','manual_route':'integrated-assembly.html','support_route':'integrated-support.html','manifest':manifest,'review_only':True},ensure_ascii=False,indent=2))
print(json.dumps({'revision':revision,'models':len(manifest),'steps':len(guide['steps']),'support_steps':len(book['steps'])}))
# UI-only workbench, using exact frozen guide and geometry assets.
from build_viewer_workbench import build as build_workbench
build_workbench(R,C,D,library)
# Standard pages reference the one canonical mechanical output tree.
canonical=R.parent/'generated/site';canonical.mkdir(parents=True,exist_ok=True)
for name in ['index.html','integrated-assembly.html','integrated-operation.html','integrated-support.html']:
 (canonical/name).write_text(canonicalize((D/name).read_text()))
(canonical/'operation-guide.json').write_text(canonicalize((I/'operation-guide.json').read_text()))
shutil.move(R/'CURRENT_VIEWER.json',canonical/'CURRENT_VIEWER.json')
_stage.cleanup()
