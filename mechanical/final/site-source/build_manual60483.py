from pathlib import Path
import json,re,shutil,html,hashlib
R=Path(__file__).resolve().parent;C=R.parent/'lift-feasibility/compact-arm-60483-candidate';D=R/'dist/compact60483';D.mkdir(exist_ok=True)
G=json.loads((C/'manual/guide.json').read_text());manifest=json.loads((C/'candidate-manifest.json').read_text())
shutil.copytree(C/'manual/diagrams',D/'diagrams',dirs_exist_ok=True);shutil.copytree(C/'models',D/'models',dirs_exist_ok=True)
for f in ['guide.json','manual60483.pdf']:
 if (C/'manual'/f).exists():shutil.copyfile(C/'manual'/f,D/f)
(D/'manifest.json').write_text(json.dumps(manifest,indent=2))
for key,row in manifest.items():assert hashlib.sha256((D/row['file']).read_bytes()).hexdigest()==row['sha256']
css='''*{box-sizing:border-box}body{margin:0;font:17px/1.75 system-ui,sans-serif;color:#183046;background:#eef3f7}header,main,footer{max-width:1140px;margin:auto;padding:24px}nav{display:flex;gap:20px;flex-wrap:wrap}a{color:#075ba3}h1{font-size:30px;line-height:1.3}h2{font-size:24px}small{font-size:14px}.warning{padding:18px;background:#fff1d2;border-left:5px solid #cc8400;border-radius:8px}.step{background:white;padding:26px;margin:24px 0;border-radius:14px;scroll-margin-top:16px;box-shadow:0 4px 22px #1b3f5810}.step img{display:block;width:100%;height:auto;border-radius:8px}.num{display:inline-block;background:#123d62;color:white;border-radius:8px;padding:3px 12px;margin-right:12px}.parts{font-weight:700;color:#006d70}.check{padding:14px;background:#eaf5f4;border-radius:8px}ol{padding-left:1.5em}li{padding:4px 0}details{padding:16px;background:white}summary{cursor:pointer;font-weight:700}.toc{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px 24px}.downloads{display:flex;gap:18px;flex-wrap:wrap;padding:14px 0}.caption{font-size:14px;color:#526777}@media(max-width:650px){header,main,footer{padding:16px}.step{padding:16px}.toc{grid-template-columns:1fr}h1{font-size:26px}}'''
nav='<nav><a href="compact60483-guide.html">60483候选改装说明</a><a href="compact60483-operation.html">60483候选整机／操作关系</a><a href="index.html">132支承80步（原四臂）</a><a href="operation-guide.html">旧899件整机关系</a><a href="history-219.html">219失败记录</a></nav>'
head='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>60483候选 · 22步改装说明</title><style>'+css+'</style><body>'
body='<header>'+nav+'<h1>60483根部支架候选<br>22步改装补充说明书</h1><p>每头8片32056换为4件60483；四头899 → 859件。132件支承、59件底盘保持。</p><div class="warning"><b>设计候选，未通过实体装配或带电试机验收。</b><br>仅验证名义最终配合；拆装插拔路径未做连续碰撞验证，也未经实体验证。根轴64mm名义叠层零余量。正常夹指仍限25°，原8墙脚销HOLD保留。</div><div class="downloads"><a download href="compact60483/manual60483.pdf">下载PDF说明书</a><a download href="compact60483/candidate-with-manual.zip">下载模型＋说明＋源文件</a><a href="compact60483-operation.html">查看一致的859／857件整机3D</a></div><details><summary>步骤目录</summary><div class="toc">'+''.join('<a href="#step-'+str(s['id'])+'">'+str(s['id']).zfill(2)+' '+html.escape(s['title'])+'</a>'for s in G['steps'])+'</div></details></header><main>'
for s in G['steps']:
 body+='<section class="step" id="step-'+str(s['id'])+'"><h2><span class="num">'+str(s['id']).zfill(2)+'</span>'+html.escape(s['title'])+'</h2><p class="parts">'+html.escape(s['parts'])+'</p><a href="compact60483/'+s['image']+'" target="_blank" rel="noopener"><img loading="lazy" src="compact60483/'+s['image']+'" alt="'+html.escape(s['title'])+'，真实LDraw零件网格图"></a><p class="caption">青绿＝60483新件；粉红＝本步拆下件；金色＝强调保留件。箭头表示名义轴向方向；爆炸间距不是装配间隙。点击放大。</p><ol>'+''.join('<li>'+html.escape(t)+'</li>'for t in s['instructions'])+'</ol><p class="check"><b>核对：</b>'+html.escape(s['check'])+'</p></section>'
body+='</main><footer><p>依据冻结候选模型、接合审核与有限运动证据编写。原始LDraw作者和许可证保留在源包。此页不发送任何设备指令。</p><p>版本 '+G['revision']+' · 冻结源文件 '+G['source_file']+' SHA256 '+G['source_sha256']+'</p>'+nav+'</footer></body></html>'
(R/'dist/compact60483-guide.html').write_text(head+body)
# Preserve existing operation stages; replace every geometry source with exact candidate models.
OP=R.parent/'lift-feasibility/pose-coupled-support-review/complete-seat-review/operation-guide132/operation-guide132.json'
g=json.loads(OP.read_text());mapping={'load_empty':'loading-all50','cube_above':'loading-all50','seated':'loading-all50','fb_ready':'FB0-open','fb_holds':'FB0-held','unlocked_up':'support-unlocked','parked_fb':'support-down40','lr_ready':'LR90-open','both_hold':'both-held'}
for key,s in g['states'].items():
 row=manifest[mapping[key]];s.update(model_text=(C/row['file']).read_text(),count=row['parts'],sha256=row['sha256'],file='compact60483/'+row['file'],mechanical_key=mapping[key]);s.pop('diagram_file',None)
for s in g['stages']:
 for k in ['diagram_file','diagram_alt_zh','diagram_caption_zh']:s.pop(k,None)
 s['cautions_zh']=['60483候选：正常夹指不超过25°；原异常挡轴已取消。装配路径、实体保持和控制联锁未放行。']+s.get('cautions_zh',[])
g['review_only']=True;g['candidate']='60483';g['candidate_manifest']=manifest
(D/'operation-guide.json').write_text(json.dumps(g,ensure_ascii=False,indent=2))
original=(R/'dist/index.html').read_text();large=next(x for x in re.findall(r'<script>([\s\S]*?)</script>',original)if 'const THREE = 'in x);library=large[:large.index('try{\nconst box=')]
body=(R/'operation-guide.html').read_text().replace('<h1>整机关系与放入／退出</h1>','<h1>60483候选整机 · 放入／退出设计关系</h1>').replace('132件小样怎样接在原四臂之间，以及魔方放入、夹持交接、托座下移与退出的设计关系','全机859／857件，四头合计16件60483；下方各阶段均使用同一候选几何。').replace('RELATIONSHIP_CONTENT','<p>这里只替换四头根部支架与移除原异常挡轴。132件支承和59件底盘保留。与旧899件整机区分；下面真实网格整机图与本页候选模型一致。</p><img style="width:100%;height:auto" src="compact60483/diagrams/machine-loading-all50.png" alt="60483候选四头50度整机实际网格"><p><a href="compact60483-guide.html">打开22步改装说明与PDF</a></p>').replace('WARNING_CONTENT','<ul><li>夹指正常范围约3.8417°至25°。自然端点30.872°不能用作限位。</li><li>原8墙脚销HOLD保持。64mm根轴叠层零余量，实体防脱与自由运动待验证。</li><li>25°以上仅LIMITED筛查；未经整机／实体／带电放行。</li></ul>')
styles=(R/'operation-guide.css').read_text();scripts='window.OPERATION_GUIDE='+json.dumps(g,ensure_ascii=False).replace('<','\\u003c')+';window.CANDIDATE_COLOR_META='+json.dumps((R/'candidate-colors.ldr').read_text())+';'
for f in ['candidate-source-adapter.js','operation-guide-core.js','operation-viewer-app.js','operation-guide-ui.js']:scripts+=(R/f).read_text()+'\n'
(R/'dist/compact60483-operation.html').write_text('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>60483候选整机与操作关系</title><style>'+styles+'nav{display:flex;gap:16px;flex-wrap:wrap;padding:14px}nav a{color:#075ba3}</style></head><body>'+nav+body+'<script>'+library+scripts+'</script></body></html>')
# Add a clearly separated entry without relabeling historical geometry.
for page in ['index.html','operation-guide.html','history-219.html']:
 path=R/'dist'/page;txt=path.read_text()
 banner='<div id="compact60483-entry" style="padding:16px;background:#e3f3f2;color:#123d62;font:16px/1.6 system-ui"><b>另有60483根部短支架候选：</b> <a href="compact60483-guide.html">22步改装说明／PDF</a> · <a href="compact60483-operation.html">对应859／857件整机</a>。本页原模型／历史记录保持独立。</div>'
 if 'id="compact60483-entry"'not in txt:txt=re.sub(r'(<body[^>]*>)',r'\1'+banner,txt,count=1);path.write_text(txt)
print('Built 22-step manual and candidate operation views; nine states map to seven exact candidate geometries.')
