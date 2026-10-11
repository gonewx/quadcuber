var GravityStepPose=(()=>{
 function capture(group){for(const child of group.children)if(!child.userData.gravityBasePose)child.userData.gravityBasePose={position:child.position.clone(),quaternion:child.quaternion.clone(),scale:child.scale.clone()};}
 function restore(group){capture(group);for(const child of group.children){const b=child.userData.gravityBasePose;child.position.copy(b.position);child.quaternion.copy(b.quaternion);child.scale.copy(b.scale);child.updateMatrix();}}
 function apply(group,step){restore(group);for(const r of step.geometry_records||[]){if(!Number.isInteger(r.index1)||r.index1<1||r.index1>group.children.length)throw Error('步骤姿态实例编号无效');const a=r.rotation,p=r.position_ldu;if(!a||!p||p.length!==3||a.length!==3)throw Error('步骤姿态数据缺失');const m=new THREE.Matrix4().set(a[0][0],a[0][1],a[0][2],p[0],a[1][0],a[1][1],a[1][2],p[1],a[2][0],a[2][1],a[2][2],p[2],0,0,0,1),child=group.children[r.index1-1];m.decompose(child.position,child.quaternion,child.scale);child.updateMatrix();}group.updateMatrixWorld(true);}
 return{apply,restore};
})();
