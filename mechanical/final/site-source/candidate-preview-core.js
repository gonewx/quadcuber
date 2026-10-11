var CandidatePreviewCore=(()=>{
 function mask(step,count){
  const visible=[...(step.visible_part_ids||[]),...(step.retained_foundation_part_ids||[]),...(step.original_module_part_ids||[])];
  return StepReaderCore.mask({...step,visible_part_ids:visible,highlight_part_ids:step.highlight_part_ids||step.highlight||step.added_part_ids},count);
 }
 function prepare(group){
  const variants=new Map();
  group.traverse(o=>{if(!o.material)return;const list=Array.isArray(o.material)?o.material:[o.material];
   o.userData.previewBase=o.material;
   const convert=kind=>{const out=list.map(m=>{const key=m.uuid+kind;if(!variants.has(key)){const copy=m.clone();if(copy.color)copy.color.set(kind==='new'?'#1285d5':(o.isMesh?'#b7bdc4':'#687584'));variants.set(key,copy)}return variants.get(key)});return Array.isArray(o.material)?out:out[0]};
   o.userData.previewNew=convert('new');o.userData.previewOld=convert('old');
  });
 }
 function apply(group,step){
  const m=mask(step,group.children.length);
  group.children.forEach((part,i)=>{part.visible=m.visible[i];part.traverse(o=>{if(o.userData.previewBase)o.material=m.highlight[i]?o.userData.previewNew:o.userData.previewOld})});
  return{visible:m.visible.filter(Boolean).length,highlight:m.highlight.filter(Boolean).length,core:m.visible.slice(0,132).filter(Boolean).length};
 }
 function restore(group){group.children.forEach(c=>c.visible=true);group.traverse(o=>{if(o.userData.previewBase)o.material=o.userData.previewBase})}
 return{mask,prepare,apply,restore};
})();
