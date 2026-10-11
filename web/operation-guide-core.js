var OperationGuideCore=(()=>{
 const labels={manual:'手动操作（设计说明）',motor_design:'电机动作（设计目标）',check:'停下核对'};
 function actionLabel(type){if(!Object.hasOwn(labels,type))throw Error('Invalid action type');return labels[type]}
 function create(guide){
  const invalid=()=>{throw Error('Invalid operation guide')};
  if(!guide||guide.review_only!==true||!Array.isArray(guide.stages)||!guide.stages.length||!guide.states)invalid();
  const ids=new Set();
  for(const stage of guide.stages){
   const model=guide.states[stage.state_id];
   if(!stage.id||ids.has(stage.id)||!stage.title_zh||!Object.hasOwn(labels,stage.action_type)||!model||!Number.isInteger(model.count)||model.count<1||!model.model_text)invalid();
   ids.add(stage.id);
  }
  let index=0;
  const current=()=>({index,stage:guide.stages[index],state:guide.states[guide.stages[index].state_id]});
  const select=value=>{const next=typeof value==='string'?guide.stages.findIndex(s=>s.id===value):value;if(!Number.isInteger(next)||next<0||next>=guide.stages.length)throw Error('Invalid stage');index=next;return current()};
  return {current,select};
 }
 return {create,actionLabel};
})();
