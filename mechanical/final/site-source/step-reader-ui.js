(function(){
 const book=window.ASSEMBLY_BOOK;if(!book?.steps?.length)return;
 const el=id=>document.getElementById(id),reader=StepReaderCore.create(book),root=el('step-builder');
 root.hidden=false;
 const moduleNames=new Map();book.steps.forEach(s=>moduleNames.set(s.module_id,s.module_title||s.module_id));
 for(const [id,name]of moduleNames){const o=document.createElement('option');o.value=id;o.textContent=(book.inventory_hold?.blocked_module_ids.includes(id)?'暂停 · ':'')+name;el('step-module').appendChild(o)}
 const coreCount=book.core_count||192;const readyImages=book.steps.filter(s=>s.image_url).length;
 el('step-book-status').textContent=(book.data_status==='inventory_hold'?'待修订版本：39790与71709库存不足，立柱及承托座相关步骤暂停':book.data_status==='core_complete_original_interface_hold'?'核心'+coreCount+'件步骤齐全；原四臂接口暂缓':book.data_status==='final'?'已覆盖'+coreCount+'件底盘与升降的新增／复用步骤':'首批模块细步骤；其他模块尚未补齐')+' · 本批覆盖'+(book.covered_core_count??new Set(book.steps.flatMap(s=>s.added_part_ids)).size)+'/'+coreCount+'件 · '+book.steps.length+'步，已配图'+readyImages+'步。'+(readyImages<book.steps.length?'其余细图制作中时可用3D逐步查看。':'')+'名义装配说明，实物待验收';
 if(book.load_test_status==='failed_sag'){
  el('step-book-status').textContent='承载实测未通过：放入魔方后整体下垂。暂停带魔方运行；'+book.steps.length+'步说明保留供诊断，不能当作承重合格。原四臂接口仍暂缓';
  el('step-load-hold').hidden=false;el('step-load-hold').textContent='暂停带魔方运行。用户已实测整体下垂，原因与修正方案诊断中。几何通过不代表承重合格。';
 }else el('step-load-hold').hidden=true;
 function evidence(id,values){
  const out=el(id);out.replaceChildren();
  for(const value of (Array.isArray(values)?values:(values?[values]:[]))){const li=document.createElement('li');
   li.textContent=typeof value==='string'?value:(value.label||'')+(Array.isArray(value.center_mm)?' · 坐标（'+value.center_mm.map(v=>Number(v.toFixed(3))).join('，')+'）毫米':'');
   out.appendChild(li);
  }
 }
 let step3D=false;
 function show(){
  const state=reader.current(),s=state.step;
  el('step-number').value=String(state.index+1);el('step-number').max=String(state.total);el('step-module').value=s.module_id;
  el('step-counter').textContent='/ '+state.total;el('step-bottom-counter').textContent=(state.index+1)+' / '+state.total;el('step-top-counter').textContent=(state.index+1)+' / '+state.total;
  for(const suffix of['','-bottom','-top']){el('step-previous'+suffix).disabled=!state.canPrevious;el('step-next'+suffix).disabled=!state.canNext}
  el('step-id').textContent=s.id+(s.module_step_number?' · 模块第'+s.module_step_number+'步':'');
  const actions={merge_subassemblies:'合并预装组件',mount_existing_original_modules:'恢复原有708件模块'};
  el('step-action').textContent=actions[s.assembly_action]||('本步加入'+s.added_part_ids.length+'件');
  el('step-title').textContent=(s.construction_status==='paused'?'暂停施工 · ':'')+s.title;
  el('step-hold').hidden=s.construction_status!=='paused';el('step-hold').textContent=s.hold_reason||'';
  el('step-prerequisites').textContent=s.requires_subassemblies?.length?'先备好：'+s.requires_subassemblies.map(x=>moduleNames.get(x)||book.subassembly_titles?.[x]||x).join('、'):'';
  el('step-part-ids').textContent=s.added_part_ids.length?'本步实例编号：'+s.added_part_ids.map(n=>'#'+n).join('、'):'';
  el('step-parts').replaceChildren();
  for(const p of s.parts||[]){const span=document.createElement('span');span.className='step-part';span.textContent=(p.display_name||p.name||p.part||'零件')+' × '+p.count+(p.color_name||typeof p.color==='string'?' · '+(p.color_name||p.color):'');el('step-parts').appendChild(span)}
  el('step-image').alt=s.image_alt||s.title+'装配步骤图';el('step-image-error').hidden=true;
  el('step-image-frame').hidden=!s.image_url;el('step-image-zoom').disabled=!s.image_url;
  if(s.image_url){el('step-image').src=s.image_url;el('step-image-error').textContent='这张步骤图暂未载入，请先看文字或切换3D'}else{el('step-image-error').hidden=false;el('step-image-error').textContent='本步细图制作中；点击“3D看这一步”查看已装件和本步高亮件，文字步骤已可用'}
  el('step-image-frame').classList.remove('enlarged');el('step-image-zoom').setAttribute('aria-pressed','false');el('step-image-zoom').textContent='放大细看';
  el('step-instructions').replaceChildren();for(const t of s.instructions||[]){const li=document.createElement('li');li.textContent=t;el('step-instructions').appendChild(li)}
  evidence('step-insertion',s.insertion);evidence('step-ports',s.ports);evidence('step-technical-instructions',s.technical_instructions);
  el('step-3d-status').textContent='';
  if(step3D)apply3D(false);
 }
 function apply3D(scroll){
  try{if(typeof window.setAssemblyStep3D!=='function')throw Error('3D模型仍在加载，请稍后再试');
   const r=window.setAssemblyStep3D(reader.current().step);step3D=true;el('step-exit-3d').hidden=false;el('v3d-step-nav').hidden=false;
   el('step-3d-status').textContent='3D显示'+r.visibleParts+'件，本步高亮'+(r.highlightedParts??r.newParts)+'件'+(scroll?'，已跳到上方3D':'');
   if(scroll)el('v3d').scrollIntoView({behavior:'smooth',block:'start'});
  }catch(e){el('step-3d-status').textContent=e.message}
 }
 function move(n){reader.move(n);show()}
 for(const suffix of['','-bottom','-top']){el('step-previous'+suffix).addEventListener('click',()=>move(-1));el('step-next'+suffix).addEventListener('click',()=>move(1))}
 el('step-module').addEventListener('change',()=>{reader.module(el('step-module').value);show()});
 el('step-number').addEventListener('change',()=>{const n=Number(el('step-number').value);if(Number.isInteger(n))reader.go(n-1);show()});
 el('step-image-zoom').addEventListener('click',()=>{const on=el('step-image-frame').classList.toggle('enlarged');el('step-image-zoom').setAttribute('aria-pressed',String(on));el('step-image-zoom').textContent=on?'适合屏幕':'放大细看'});
 el('step-image').addEventListener('error',()=>{el('step-image-error').hidden=false});
 el('step-3d').addEventListener('click',()=>apply3D(true));
 el('step-exit-3d').addEventListener('click',()=>{window.clearAssemblyStep3D?.();step3D=false;el('step-exit-3d').hidden=true;el('v3d-step-nav').hidden=true;el('step-3d-status').textContent='已恢复整机视图'});
 document.addEventListener('v3d-normal-mode',()=>{step3D=false;el('step-exit-3d').hidden=true});
 const stepKeys=e=>{if(/INPUT|SELECT/.test(e.target.tagName)||e.ctrlKey||e.metaKey||e.altKey)return;if(e.key==='ArrowLeft'||e.key==='ArrowRight'){e.preventDefault();move(e.key==='ArrowLeft'?-1:1)}};
 root.addEventListener('keydown',stepKeys);el('v3d-step-nav').addEventListener('keydown',stepKeys);
 show();
 if(document.modelContext?.registerTool){
  const lifecycle=new AbortController();window.addEventListener('pagehide',()=>lifecycle.abort(),{once:true});
  const tool={name:'show_assembly_step',title:'查看装配步骤',description:'按稳定步骤编号打开真实装配说明，并同步当前启用的3D步骤视图。',inputSchema:{type:'object',properties:{step_id:{type:'string'}},required:['step_id'],additionalProperties:false},annotations:{readOnlyHint:false,untrustedContentHint:false},execute(input){
   if(!input||typeof input.step_id!=='string'||Object.keys(input).some(k=>k!=='step_id'))throw Error('需要一个有效的step_id');
   const index=book.steps.findIndex(s=>s.id===input.step_id);if(index<0)throw Error('这一步尚未提供');
   reader.go(index);show();return {id:reader.current().step.id,number:index+1,total:book.steps.length,data_status:book.data_status||'partial'};
  }};
  try{Promise.resolve(document.modelContext.registerTool(tool,{signal:lifecycle.signal})).catch(()=>{});}catch(_){}
 }
})();
