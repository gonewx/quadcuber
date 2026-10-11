from pathlib import Path
import json,re,hashlib,urllib.parse,sys,ast
root=Path(__file__).resolve().parent
src=root.parent/'lift-feasibility/detailed-instructions-192/inventory-compatible-candidate'
hand=json.loads((src/'viewer-handoff219.json').read_text());assembly=json.loads((src/'assembly-candidate219.json').read_text());model=(src/'machine-working-927.mpd').read_text()
assert hashlib.sha256((src/'assembly-candidate219.json').read_bytes()).hexdigest()==hand['source_assembly_sha256']
assert hashlib.sha256((src/'machine-working-927.mpd').read_bytes()).hexdigest()==hand['source_mpd_sha256']
ids=hand['roles_core_index1'];assert sorted(ids['fixed']+ids['moving']+ids['key'])==list(range(1,220))
roles={'fixed_index1':ids['fixed'],'moving_index1':ids['moving'],'key_index1':ids['key'],'core_count':hand['core_count'],'whole_count':hand['whole_count_working'],'drop_ldu':hand['drop_mm']/0.4}
assert len(roles['fixed_index1'])==144 and len(roles['moving_index1'])==69 and len(roles['key_index1'])==6
assert sum(r['name']=='39790.dat'for r in assembly)==4 and not any(r['name']=='71709.dat'for r in assembly)
h=(root.parent/'lift-feasibility/technic-seat-lift-160/technic-seat-lift-offline.html').read_text()
tree=ast.parse((root/'build_viewer.py').read_text());css=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='css'for t in n.targets))
css+='\n.guide-warning{background:#fff6e8;border-left:4px solid #b46b12;padding:12px 16px}.bar a{color:#1264a1;font-size:14px;padding:10px 4px;text-underline-offset:3px}\n'
css+='\n.revision-note{border:1px solid #c88b26;background:#fff8e8;padding:16px 18px;border-radius:8px;margin:18px 0;max-width:1400px}.revision-note h2{margin:0 0 8px}.revision-note p{margin:8px 0}\n'
h=re.sub(r'<style>.*?</style>','<style>'+css+'</style>',h,count=1,flags=re.S)
h=re.sub(r'<title>.*?</title>','<title>共用底盘 219 · quadcuber 3D 查看</title>',h,count=1)
heading='<h1>共用底盘 219</h1><p class="intro"><b>库存适配审阅版 · 实物待验收</b>　219件底盘与升降，927件整机，40毫米行程</p><p class="notes">39790框使用4个；不使用71709面板。已换入新门架、承托和底部角连接，满足这两项已确认的库存限制。</p>'
h=re.sub(r'<h1>.*?</h1><p>.*?</p>',heading,h,count=1,flags=re.S)
notes='<p class="notes">固定144件、移动69件、可取出锁件6件。下位隐藏6件锁件，整机921件，底盘与升降213件。蓝框标示56毫米魔方的上位位置；按钮只展示上下位，不模拟完整机械头操作。</p><section id="step-builder" class="revision-note"><h2>219件装配说明正在修订</h2><p>门架、承托和底部角连接已换成新实件，零件编号与移动分组也已更新。旧137步属于192件版本，不能用于当前219件模型。</p><p>当前页面提供新模型的旋转、缩放、整机／底盘和40毫米上下位审阅；新分步图会在逐件核对后补入。</p></section><p class="guide-warning"><b>原四臂接口仍待确认。</b>原708件模块保持不变，8枚墙脚销的未批准纠错没有混入本版；相关装回施工继续暂缓。</p><p class="notes">导轨与座体部分配合为名义相切，不能当作实物公差余量。所有尺寸为名义CAD尺寸。停车状态最小名义间隙约0.371毫米，仍须核对实物余量。实物装配、制造公差、刚度、插拔力、保持力及手部空间仍需验证。内嵌全部CAD几何与渲染脚本，可离线查看。</p>'
h=re.sub(r'<p>1,622.*?</p>',notes,h,count=1,flags=re.S)
h=re.sub(r'<script>window.V3D_MODEL_TEXT=.*?;</script>',lambda _: '<script>window.V3D_MODEL_TEXT='+json.dumps(model,ensure_ascii=False).replace('<','\\u003c')+';</script>',h,count=1,flags=re.S)
h=re.sub(r'<script>window.LIFT_ROLES=.*?;</script>',lambda _: '<script>window.LIFT_ROLES='+json.dumps(roles)+';</script>',h,count=1,flags=re.S)
h=h.replace('160件升降机构 + 708件原机械头与支架','219件底盘与升降 + 708件原机械头与支架')
start=h.index('function applyLiftView(){');end=h.index("document.getElementById('lift-pose').addEventListener",start)
h=h[:start]+'''function applyLiftView(){
 if(!group)return;
 const r=window.LIFT_ROLES,moving=new Set(r.moving_index1),keys=new Set(r.key_index1);
 group.children.forEach((c,i)=>{
  if(c.userData.liftOriginalY===undefined)c.userData.liftOriginalY=c.position.y;
  c.position.y=c.userData.liftOriginalY+(liftDown&&moving.has(i+1)?r.drop_ldu:0);
  c.visible=!(liftDown&&keys.has(i+1))&&!(liftOnly&&i>=r.core_count);
 });
 document.getElementById('lift-pose').textContent=liftDown?'切换到上位定位':'切换到下位40mm';
 document.getElementById('lift-scope').textContent=liftOnly?'显示整机':'只看底盘与升降';
 document.getElementById('lift-pose').setAttribute('aria-pressed',String(liftDown));
 document.getElementById('lift-scope').setAttribute('aria-pressed',String(liftOnly));
 label.textContent=(liftDown?'下位40mm':'上位定位')+' · '+(liftOnly?'底盘与升降':'整机')+' '+group.children.filter(c=>c.visible).length+'件';
}
'''+h[end:]
h=h.replace('liftDown=!liftDown;applyLiftView()','liftDown=!liftDown;applyLiftView();fit()')
h=h.replace('只看底座与升降','只看底盘与升降')
h=h.replace('<span id="v3d-label">','<a href="#step-builder">说明修订状态</a><span id="v3d-label" aria-live="polite">',1)
h=h.replace('<div id="v3d">','<div id="v3d" role="img" aria-label="219件底盘与927件整机3D模型" tabindex="0">',1)
h=h.replace('</div>\n<p class="notes">','</div><p class="hint">拖动旋转 · 滚轮／双指缩放 · A/D、W/S旋转 · +/-缩放 · R复位</p>\n<p class="notes">',1)
h=h.replace("slider.addEventListener('input', () => showStep(Number(slider.value)));", "slider.addEventListener('input', () => {showStep(Number(slider.value));applyLiftView()});")
svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect x="3" y="3" width="26" height="26" rx="5" fill="#17212f"/><path d="M9 9h14v14H9zM9 16h14M16 9v14" fill="none" stroke="#64b5ff" stroke-width="2"/></svg>'
h=h.replace('<title>','<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,'+urllib.parse.quote(svg,safe='')+'"><meta name="description" content="219件库存适配底盘与927件整机3D审阅；40毫米上下位，新装配说明修订中，原8墙脚销纠错未采用。"><title>',1)
webmcp='''
if(document.modelContext?.registerTool){
 const lifetime=new AbortController();window.addEventListener('pagehide',()=>lifetime.abort(),{once:true});
 const tool={name:'set_quadcuber_view',title:'切换底盘视图',description:'切换219件底盘或927件整机的上下位查看状态，不执行机械操作。',inputSchema:{type:'object',properties:{pose:{type:'string',enum:['upper','lower']},scope:{type:'string',enum:['machine','chassis']}},required:['pose','scope'],additionalProperties:false},annotations:{readOnlyHint:false,untrustedContentHint:false},execute(input){
 if(!input||!['upper','lower'].includes(input.pose)||!['machine','chassis'].includes(input.scope)||Object.keys(input).some(k=>!['pose','scope'].includes(k)))throw Error('Invalid pose or scope');
 if(!group)throw Error('Model is still loading');liftDown=input.pose==='lower';liftOnly=input.scope==='chassis';applyLiftView();fit();return {pose:input.pose,scope:input.scope,visibleParts:group.children.filter(c=>c.visible).length};
 }};try{Promise.resolve(document.modelContext.registerTool(tool,{signal:lifetime.signal})).catch(()=>{});}catch(_){}
}
'''
h=h.replace('window.v3dReady = () => group !== null;',webmcp+'\nwindow.v3dReady = () => group !== null;',1)
bom=(src/'candidate219-bom.csv').read_text()
h=h.replace('<a href="#step-builder">说明修订状态</a>','<a href="#step-builder">说明修订状态</a> <a download="quadcuber-219-bom.csv" href="data:text/csv;charset=utf-8,'+urllib.parse.quote(bom,safe='')+'">219件零件表</a>',1)
if (root/'load-hold.json').exists():
 hold=json.loads((root/'load-hold.json').read_text())
 if hold['status']=='failed_sag':
  banner='<div id="load-test-alert" class="load-warning" role="alert"><strong>承载实测未通过：暂停带魔方运行</strong><p>实际反馈：放入魔方后出现整体下垂。当前承载问题仍在诊断，请暂停带魔方运行。</p><p>此前的几何与运动检查不能代表承重合格。当前模型和装配说明保留供浏览、排查；没有修改机械模型或确认修复。</p><p>原8枚墙脚销的待批准项仍独立保留，不能视为已处理。</p></div>'
  h=h.replace('<h1>共用底盘 219</h1>',banner+'<h1>共用底盘 219 · 承载诊断中</h1>',1)
  h=h.replace('库存适配审阅版 · 实物待验收','承载实测未通过 · 暂停带魔方运行')
  h=h.replace('<title>共用底盘 219 · quadcuber 3D 查看</title>','<title>共用底盘 219 · 承载诊断中</title>')
  h=h.replace('</style>','.load-warning{border:2px solid #ae2424;background:#fff0ec;color:#7b1414;border-radius:8px;padding:16px 18px;margin:0 0 18px;font-size:16px;line-height:1.6;max-width:1400px}.load-warning strong{display:block;font-size:21px}.load-warning p{margin:8px 0}.load-warning[hidden]{display:none}</style>',1)
out=Path(sys.argv[1]) if len(sys.argv)>1 else root/'preview219/index.html';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(h)
(root/'viewer219-source.json').write_text(json.dumps({'source_path':str(src),'assembly_sha256':hand['source_assembly_sha256'],'model_sha256':hand['source_mpd_sha256'],'roles':roles,'old_instructions_reused':False,'original8wallpin_fix_included':False},ensure_ascii=False,indent=2))
print(json.dumps({'output':str(out),'bytes':len(h.encode()),'core':219,'whole':927,'moving':69}))
