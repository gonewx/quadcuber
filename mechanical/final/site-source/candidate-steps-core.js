var CandidateStepsCore=(()=>{
 function mask(step,count){
  if(!step||!Array.isArray(step.visible_part_ids)||!Array.isArray(step.added_part_ids))throw Error('缺少核对后的步骤零件编号');
  const visible=Array(count).fill(false),added=Array(count).fill(false),highlight=Array(count).fill(false);
  for(const [ids,out]of [[step.visible_part_ids,visible],[step.added_part_ids,added],[step.highlight_part_ids||step.added_part_ids,highlight]])for(const id of ids){if(!Number.isInteger(id)||id<1||id>count||out[id-1])throw Error('零件编号超出范围或重复');out[id-1]=true}
  if(added.some((v,i)=>v&&!visible[i])||highlight.some((v,i)=>v&&!visible[i]))throw Error('新增或重点零件不在本步视图内');
  return{visible,added,highlight};
 }
 function create(book,count=132){
  if(!book||!Array.isArray(book.steps)||!book.steps.length)throw Error('步骤数据不可用');
  const ids=new Set(),introduced=new Set();
  for(const s of book.steps){if(!s.id||ids.has(s.id)||!s.module_id)throw Error('步骤身份缺失或重复');const m=mask(s,count);for(const p of s.prerequisite_step_ids||[])if(!ids.has(p))throw Error('前置步骤未建立');for(const p of s.added_part_ids){if(introduced.has(p))throw Error('零件重复引入');introduced.add(p)}for(const p of s.visible_part_ids)if(!introduced.has(p))throw Error('视图含尚未引入的零件');ids.add(s.id)}
  let index=0;const current=()=>({index,total:book.steps.length,step:book.steps[index],canPrevious:index>0,canNext:index<book.steps.length-1});const go=n=>{if(!Number.isInteger(n))throw Error('步骤序号无效');index=Math.max(0,Math.min(book.steps.length-1,n));return current()};return{current,go,move:n=>go(index+n)};
 }
 function prepare(group){
  if(group.userData?.stepPrepared)return;const variants=new Map();
  group.traverse(o=>{if(!o.material)return;const list=Array.isArray(o.material)?o.material:[o.material];o.userData.stepBase=o.material;
   const make=kind=>{const out=list.map(m=>{const key=m.uuid+kind;if(!variants.has(key)){const copy=m.clone();if(copy.color)copy.color.set(kind==='new'?'#0784d6':(o.isMesh?'#bcc3ca':'#647487'));variants.set(key,copy)}return variants.get(key)});return Array.isArray(o.material)?out:out[0]};o.userData.stepNew=make('new');o.userData.stepOld=make('old');
  });group.userData.stepPrepared=true;
 }
 function apply(group,step){const m=mask(step,group.children.length);group.children.forEach((p,i)=>{p.visible=m.visible[i];p.traverse(o=>{if(o.userData.stepBase)o.material=m.highlight[i]?o.userData.stepNew:o.userData.stepOld})});return{visible:m.visible.filter(Boolean).length,added:m.added.filter(Boolean).length,highlight:m.highlight.filter(Boolean).length}}
 function restore(group){group.children.forEach(p=>p.visible=true);group.traverse(o=>{if(o.userData.stepBase)o.material=o.userData.stepBase})}
 return{mask,create,prepare,apply,restore};
})();
