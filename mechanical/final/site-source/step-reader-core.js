var StepReaderCore = (() => {
  function mask(step, count) {
    if (!step || !Array.isArray(step.visible_part_ids) || !Array.isArray(step.added_part_ids)) throw Error('本步缺少经过核对的3D零件编号');
    const visible=Array(count).fill(false), added=Array(count).fill(false), highlight=Array(count).fill(false);
    for (const [ids,out] of [[step.visible_part_ids,visible],[step.added_part_ids,added],[step.highlight_part_ids||step.added_part_ids,highlight]]) {
      for (const id of ids) {
        if (!Number.isInteger(id)||id<1||id>count||out[id-1]) throw Error('步骤零件编号无效或重复');
        out[id-1]=true;
      }
    }
    if (added.some((v,i)=>v&&!visible[i])||highlight.some((v,i)=>v&&!visible[i])) throw Error('本步新增件不在已装件视图内');
    return {visible,added,highlight};
  }
  function create(book) {
    if (!book || !Array.isArray(book.steps) || !book.steps.length) throw Error('细分步骤尚未提供');
    const steps=book.steps, ids=new Set();
    steps.forEach(s=>{if(!s.id||ids.has(s.id)||!s.module_id)throw Error('步骤身份无效');ids.add(s.id)});
    let index=0;
    const current=()=>({index,total:steps.length,step:steps[index],canPrevious:index>0,canNext:index<steps.length-1});
    const go=n=>{if(!Number.isInteger(n))throw Error('步骤号必须是整数');index=Math.max(0,Math.min(steps.length-1,n));return current()};
    return {current,go,move:n=>go(index+n),module:id=>{const n=steps.findIndex(s=>s.module_id===id);if(n<0)throw Error('没有这个模块');return go(n)}};
  }
  function applyGroup(group,step){
    const view=mask(step,group.children.length);
    group.children.forEach((c,i)=>{
      if(c.userData.liftOriginalY===undefined)c.userData.liftOriginalY=c.position.y;
      c.position.y=c.userData.liftOriginalY;c.visible=view.visible[i];
      c.traverse(o=>{if(o.userData.baseMaterial)o.material=view.highlight[i]?(o.userData.stepHighlightMaterial||o.userData.hiMaterial||o.userData.baseMaterial):o.userData.baseMaterial});
    });
    return {visibleParts:view.visible.filter(Boolean).length,newParts:view.added.filter(Boolean).length,highlightedParts:view.highlight.filter(Boolean).length};
  }
  return {create,mask,applyGroup};
})();
