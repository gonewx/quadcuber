let assemblyStep=null;
function restoreAssemblyMaterials(){
 if(!group)return;
 group.traverse(o=>{if(o.userData.baseMaterial)o.material=o.userData.baseMaterial});
}
function showAssemblyStep3D(step){
 if(!group)throw Error('3D模型仍在加载，请稍后再试');
 const result=StepReaderCore.applyGroup(group,step);
 assemblyStep=step;liftDown=false;liftOnly=false;cubeRef.visible=false;
 label.textContent=(step.construction_status==='paused'?'暂停施工，仅供审阅 · ':'')+step.id+' · '+step.title+' · 已装'+result.visibleParts+'件 / 本步高亮'+result.highlightedParts+'件';
 document.getElementById('lift-pose').setAttribute('aria-pressed','false');
 document.getElementById('lift-scope').setAttribute('aria-pressed','false');
 document.getElementById('lift-pose').textContent='切换到下位40mm';
 document.getElementById('lift-scope').textContent='只看底盘与升降';
 fit();return result;
}
window.setAssemblyStep3D=showAssemblyStep3D;
window.clearAssemblyStep3D=()=>{liftDown=false;liftOnly=false;applyLiftView();fit()};
