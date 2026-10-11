from pathlib import Path
import json,re,urllib.parse,base64
root=Path(__file__).resolve().parent
src=root.parent/'lift-feasibility/unified-base-validation/corrected-snapshot'
h=(root.parent/'lift-feasibility/technic-seat-lift-160/technic-seat-lift-offline.html').read_text()
roles=dict(fixed_start=0,fixed_end=123,moving_start=123,moving_end=186,keys_start=186,core_count=192,whole_count=900)
model=(src/'shared-chassis-machine-900.mpd').read_text()
h=re.sub(r'<title>.*?</title>','<title>共用底盘 192 · quadcuber 3D 查看</title>',h,count=1)
h=re.sub(r'<h1>.*?</h1><p>.*?</p>','<h1>共用底盘 192</h1><p class="intro"><b>名义几何复核版 · 实物待验收</b>　192件底盘与升降，900件整机，40毫米行程</p>',h,count=1)
h=re.sub(r'<p>1,622.*?</p>','<p class="notes">原708件机械头与支架保持原位。移动组件仍为63件，其中第132件修正为6558销，挡肩位于单面孔入口侧。下位移除2根锁轴及4个半轴套，整机894件，底盘与升降186件。透明蓝框标示56毫米魔方的上位位置，不计入零件；升降按钮仅展示两个位置，不模拟完整机械头操作。</p><p class="notes">本版名义几何已复核：包含上下位全192／186件零件对、121根销轴占位、指定机械头操作流程及魔方装取路径。约0.37毫米的机械头名义分离下界、8毫米桌面间隙仍须实物检查；公差、刚度、轴套保持、32192防拔和手部抓取空间未获实物验证。</p>',h,count=1)
h=re.sub(r'<script>window.V3D_MODEL_TEXT=.*?;</script>',lambda _: '<script>window.V3D_MODEL_TEXT='+json.dumps(model,ensure_ascii=False).replace('<','\\u003c')+';</script>',h,count=1,flags=re.S)
h=re.sub(r'<script>window.LIFT_ROLES=.*?;</script>',lambda _: '<script>window.LIFT_ROLES='+json.dumps(roles)+';</script>',h,count=1,flags=re.S)
h=h.replace('160件升降机构 + 708件原机械头与支架','192件共用底盘与升降 + 708件原机械头与支架')
h=h.replace("label.textContent=(liftDown?'下位40mm · 已取出6件锁定件':'上位定位 · 已插入双锁轴')+' · '+(liftOnly?'底座与升降':'完整整机');", "label.textContent=(liftDown?'下位40mm':'上位定位')+' · '+(liftOnly?'底盘与升降':'整机')+' '+group.children.filter(c=>c.visible).length+'件';\n document.getElementById('lift-pose').setAttribute('aria-pressed',String(liftDown));\n document.getElementById('lift-scope').setAttribute('aria-pressed',String(liftOnly));")
h=h.replace('只看底座与升降','只看底盘与升降')
h=h.replace('<span id="v3d-label">','<a href="#assembly">搭建步骤</a><span id="v3d-label">',1)
h=h.replace('liftDown=!liftDown;applyLiftView()','liftDown=!liftDown;applyLiftView();fit()')
h=h.replace("slider.addEventListener('input', () => showStep(Number(slider.value)));", "slider.addEventListener('input', () => {showStep(Number(slider.value));applyLiftView()});")
h=h.replace('<div id="v3d">','<div id="v3d" role="img" aria-label="可旋转的共用底盘与整机3D模型" tabindex="0">')
h=h.replace('<span id="v3d-label">','<span id="v3d-label" aria-live="polite">')
h=h.replace('</div>\n<p class="notes">','</div><p class="hint">拖动旋转 · 滚轮／双指缩放 · A/D、W/S旋转 · +/-缩放 · R复位</p>\n<p class="notes">',1)
css='''body{font:16px/1.55 system-ui,sans-serif;color:#17212f;background:#eef2f6;margin:20px}h1{font-size:24px;margin:0 0 4px}p{max-width:1100px}.intro{margin:0 0 14px;font-size:14px}.intro b{color:#9b4c00}#v3d{height:65vh;min-height:300px;position:relative;background:white;--v3d-bg:#fff;border:1px solid #d8dfe8;border-radius:8px 8px 0 0;overflow:hidden}#v3d-status{position:absolute;inset:0;display:grid;place-items:center;padding:20px}#v3d-status[hidden]{display:none}canvas{display:block;width:100%;height:100%;touch-action:none}button{font:inherit;font-size:14px;min-height:44px;padding:8px 15px;border:1px solid #b4c2d3;background:#fff;border-radius:6px;color:#14253d;cursor:pointer}button:hover{background:#edf4fb}button:focus-visible,#v3d:focus-visible{outline:3px solid #1681dd;outline-offset:3px}button[aria-pressed=true]{background:#e0efff;border-color:#1681dd}.bar{padding:12px;background:white;display:flex;flex-wrap:wrap;gap:10px;align-items:center;border:1px solid #d8dfe8;border-top:0;border-radius:0 0 8px 8px}#v3d-label{font-size:14px;color:#42556e}.hint{font-size:14px;color:#536379;margin:10px 0}.notes{font-size:14px;color:#485567;margin:12px 0}@media(max-width:600px){body{margin:12px}h1{font-size:22px}#v3d{height:58vh;min-height:300px}.bar{gap:8px;padding:10px}button{flex:1 1 auto}#v3d-label{width:100%}}'''
css+=(root/'assembly-guide.css').read_text()
h=re.sub(r'<style>.*?</style>','<style>'+css+'</style>',h,count=1,flags=re.S)
svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect x="3" y="3" width="26" height="26" rx="5" fill="#17212f"/><path d="M9 9h14v14H9zM9 16h14M16 9v14" fill="none" stroke="#64b5ff" stroke-width="2"/></svg>'
h=h.replace('<title>','<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,'+urllib.parse.quote(svg,safe='')+'"><meta name="description" content="quadcuber 192件共用底盘与900件整机交互3D查看，含40毫米上下位；设计候选，尚未实物认证。"><title>',1)
webmcp='''\nif(document.modelContext?.registerTool){
 const lifecycle=new AbortController();
 window.addEventListener('pagehide',()=>lifecycle.abort(),{once:true});
 const tool={name:'set_quadcuber_view',title:'切换共用底盘视图',description:'切换当前3D模型的上下位和整机/底盘范围，仅改变查看状态。',inputSchema:{type:'object',properties:{pose:{type:'string',enum:['upper','lower']},scope:{type:'string',enum:['machine','chassis']}},required:['pose','scope'],additionalProperties:false},annotations:{readOnlyHint:false,untrustedContentHint:false},execute(input){
  if(!input||!['upper','lower'].includes(input.pose)||!['machine','chassis'].includes(input.scope)||Object.keys(input).some(k=>!['pose','scope'].includes(k)))throw Error('Invalid pose or scope');
  if(!group)throw Error('Model is still loading');
  liftDown=input.pose==='lower';liftOnly=input.scope==='chassis';applyLiftView();fit();return {pose:input.pose,scope:input.scope,visibleParts:group.children.filter(c=>c.visible).length};
 }};
 try{Promise.resolve(document.modelContext.registerTool(tool,{signal:lifecycle.signal})).catch(()=>{});}catch(_){}
}
'''
h=h.replace('window.v3dReady = () => group !== null;',webmcp+'\nwindow.v3dReady = () => group !== null;')
guide=(root/'assembly-guide.html').read_text()
assets={ '__ASSEMBLY_IMAGE_DATA__':'corner-bay-29-assembly.png','__FULL_IMAGE_DATA__':'complete-build-guide-9-stages.png','__LOCK_IMAGE_DATA__':'corrected-joint-and-upper-lock.png'}
for placeholder,name in assets.items():
 img=root.parent/'lift-feasibility/unified-base-validation/assembly-review'/name
 guide=guide.replace(placeholder,'data:image/png;base64,'+base64.b64encode(img.read_bytes()).decode())
h=h.replace('<script>window.V3D_STEPS=',guide+'\n<script>window.V3D_STEPS=',1)
(root/'dist/index.html').write_text(h)
print(json.dumps({'bytes':len(h.encode()),'roles':roles}))
