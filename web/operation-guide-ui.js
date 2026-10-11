(()=>{
 const guide=window.OPERATION_GUIDE,controller=OperationGuideCore.create(guide),el=id=>document.getElementById(id);
 const select=el('operation-select'),prev=el('operation-prev'),next=el('operation-next'),retry=el('operation-retry');
 let busy=false,displayed=null;
 function list(id,items){const node=el(id);node.replaceChildren();for(const text of items||[]){const li=document.createElement('li');li.textContent=text;node.appendChild(li)}}
 for(const [i,stage]of guide.stages.entries()){const option=document.createElement('option');option.value=String(i);option.textContent=String(i+1).padStart(2,'0')+' · '+stage.title_zh;select.appendChild(option)}
 function lock(){const i=controller.current().index;select.disabled=busy;prev.disabled=busy||i===0;next.disabled=busy||i===guide.stages.length-1;retry.disabled=busy;window.operationWorkbenchSync?.(controller.current(),busy,displayed)}
 function describe(){
  const {index,stage,state}=controller.current();select.value=String(index);el('operation-progress').textContent=(index+1)+' / '+guide.stages.length;
  el('operation-title').textContent=stage.id+' · '+stage.title_zh;el('operation-action-type').textContent=OperationGuideCore.actionLabel(stage.action_type);el('operation-action-type').setAttribute('data-action',stage.action_type);el('operation-hands-out').hidden=stage.action_type!=='motor_design';
  list('operation-instructions',stage.instructions_zh);list('operation-cautions',stage.cautions_zh);el('operation-cautions-box').hidden=!stage.cautions_zh?.length;
  el('operation-cube-support').textContent=state.cube_support_zh||'请按阶段说明核对';
  el('operation-cube-position').textContent=state.cube_position_mm?'参考魔方中心 X '+state.cube_position_mm[0]+' / Y '+state.cube_position_mm[1]+' / Z '+state.cube_position_mm[2]+' mm':'此阶段没有魔方参考盒';
  el('operation-arms').textContent=state.arms_zh||'';el('operation-keys').textContent=state.keys_zh||'';el('operation-tray').textContent=state.tray_zh||'';
  el('operation-diagram').hidden=!stage.diagram_file;el('operation-diagram-note').textContent='';
  if(stage.diagram_file){el('operation-image').src=stage.diagram_file;el('operation-image-open').href=stage.diagram_file;el('operation-image').alt=stage.diagram_alt_zh||stage.title_zh+'的设计关系图';el('operation-image-caption').textContent=stage.diagram_caption_zh||'阶段关系图；以本页警示和阶段说明为准'}
  lock();
 }
 async function choose(value){
  if(busy)throw Error('模型正在加载，请稍后');
  controller.select(value);busy=true;displayed=null;describe();retry.hidden=true;el('operation-result').textContent='正在载入此阶段整机…';
  try{const {stage}=controller.current();const result=await window.operationView(stage.state_id);displayed=stage.id;el('operation-result').textContent='已显示此阶段整机 · '+result.parts+'件；参考魔方另计，不属于LEGO件数';return result}
  catch(error){el('operation-result').textContent='此阶段模型未能载入：'+error.message;retry.hidden=false;throw error}
  finally{busy=false;lock()}
 }
 const fromControl=value=>choose(value).catch(()=>{});
 select.addEventListener('change',()=>fromControl(Number(select.value)));prev.addEventListener('click',()=>fromControl(controller.current().index-1));next.addEventListener('click',()=>fromControl(controller.current().index+1));retry.addEventListener('click',()=>fromControl(controller.current().index));
 el('operation-image').addEventListener('error',()=>{el('operation-diagram').hidden=true;el('operation-diagram-note').textContent='图示未能载入；可继续旋转3D并阅读阶段说明'});
 window.selectOperationStage=choose;window.operationStageState=()=>({id:controller.current().stage.id,index:controller.current().index,displayed,busy});
 window.operationGuideReady=choose(0);window.operationGuideReady.catch(()=>{});
})();
