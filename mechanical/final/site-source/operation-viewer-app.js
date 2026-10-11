try{
 const box=document.getElementById('operation-v3d'),status=document.getElementById('operation-v3d-status'),fitButton=document.getElementById('operation-fit');
 const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));box.appendChild(renderer.domElement);
 const scene=new THREE.Scene();scene.background=new THREE.Color('#ffffff');scene.add(new THREE.HemisphereLight(0xffffff,0x8a8a8a,2.3));const light=new THREE.DirectionalLight(0xffffff,1.5);light.position.set(-1,2,1.5);scene.add(light);
 const camera=new THREE.PerspectiveCamera(35,1,1,20000),controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;
 let group=null,cube=null,loadedKey=null,loading=false,lastView='iso';
 const directions={iso:[.55,.5,.67],front:[0,0,-1],side:[1,0,0],top:[0,1,.001]};
 const markerPositions=window.OPERATION_GUIDE.world_axes,markerText={R:'R +X',L:'L −X',F:'F +Z',B:'B −Z'};
 const markers=Object.entries(markerText).map(([name,text])=>{const el=document.createElement('span');el.textContent=text;el.setAttribute('data-side',name);document.getElementById('operation-world-labels').appendChild(el);const p=markerPositions[name];return {el,point:new THREE.Vector3(p[0],-p[1],-p[2])}});
 function resize(){const w=box.clientWidth,h=box.clientHeight;if(!w||!h)return;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix()}
 new ResizeObserver(resize).observe(box);resize();
 function fit(view=lastView){if(!group)return;if(!Object.hasOwn(directions,view))view='iso';lastView=view;group.updateMatrixWorld(true);const bounds=new THREE.Box3().setFromObject(group);if(cube){cube.updateMatrixWorld(true);bounds.expandByObject(cube)}for(const marker of markers)bounds.expandByPoint(marker.point);const center=bounds.getCenter(new THREE.Vector3()),radius=bounds.getSize(new THREE.Vector3()).length()/2||100;camera.position.copy(center).addScaledVector(new THREE.Vector3(...directions[view]).normalize(),radius/Math.sin(Math.atan(Math.tan(THREE.MathUtils.degToRad(camera.fov/2))*Math.min(1,camera.aspect)))*1.10);camera.near=radius/50;camera.far=radius*50;camera.updateProjectionMatrix();controls.target.copy(center);controls.update()}
 function dispose(object){if(!object)return;scene.remove(object);const geometries=new Set(),materials=new Set();object.traverse(o=>{if(o.geometry)geometries.add(o.geometry);for(const material of(Array.isArray(o.material)?o.material:o.material?[o.material]:[]))materials.add(material)});geometries.forEach(g=>g.dispose());materials.forEach(m=>m.dispose())}
 function clear(){dispose(group);dispose(cube);group=null;cube=null;loadedKey=null}
 function showCube(position){if(!position)return;cube=new THREE.Group();const shape=new THREE.BoxGeometry(140,140,140);const face=new THREE.Mesh(shape,new THREE.MeshBasicMaterial({color:0xf5b942,transparent:true,opacity:.48,depthWrite:false}));const edge=new THREE.LineSegments(new THREE.EdgesGeometry(shape),new THREE.LineBasicMaterial({color:0x9a5600}));cube.add(face,edge);cube.position.set(position[0]*2.5,-position[1]*2.5,-position[2]*2.5);scene.add(cube)}
 window.operationView=async key=>{
  const state=window.OPERATION_GUIDE.states[key];if(!state)throw Error('Unknown operation state');if(loading)throw Error('模型正在加载');
  if(loadedKey===key&&group)return {parts:group.children.length,referenceCube:!!cube};
  loading=true;fitButton.disabled=true;status.hidden=false;status.textContent='正在解析此阶段整机 '+state.count+'件…';clear();
  try{
   await new Promise(resolve=>requestAnimationFrame(()=>setTimeout(resolve,0)));
   const loader=new LDrawLoader();loader.setConditionalLineMaterial(LDrawConditionalLineMaterial);loader.smoothNormals=true;
   const text=CandidateSourceAdapter.prepare(loader,state.model_text,window.CANDIDATE_COLOR_META);
   const model=await new Promise((resolve,reject)=>{const timeout=setTimeout(()=>reject(Error('模型解析超时')),120000);loader.parse(text,g=>{clearTimeout(timeout);resolve(g)},e=>{clearTimeout(timeout);reject(e)})});
   if(model.children.length!==state.count){dispose(model);throw Error('来源件数校验不符，停止显示')}
   group=model;group.rotation.x=Math.PI;scene.add(group);showCube(state.cube_position_mm);loadedKey=key;box.setAttribute('aria-label',state.count+'件整机设计端姿'+(cube?'，另加56毫米魔方参考盒':'')+'，可拖动旋转');fit();status.hidden=true;return {parts:group.children.length,referenceCube:!!cube};
  }catch(error){clear();status.hidden=false;status.textContent='整机模型未能载入：'+error.message;throw error}
  finally{loading=false;fitButton.disabled=!group}
 };
 function orbit(az,pol){const offset=camera.position.clone().sub(controls.target),s=new THREE.Spherical().setFromVector3(offset);s.theta+=az;s.phi=Math.max(.05,Math.min(Math.PI-.05,s.phi+pol));camera.position.copy(controls.target).add(new THREE.Vector3().setFromSpherical(s));controls.update()}
 function zoom(factor){const offset=camera.position.clone().sub(controls.target).multiplyScalar(factor);camera.position.copy(controls.target).add(offset);controls.update()}
 fitButton.addEventListener('click',()=>fit('iso'));
 window.operationCamera={view:fit,zoom:factor=>{if(group&&!loading)zoom(factor)},resize};
 document.addEventListener('keydown',e=>{if(!group||e.ctrlKey||e.metaKey||e.altKey||/INPUT|TEXTAREA|SELECT/.test(e.target.tagName)||e.target.isContentEditable)return;const b=box.getBoundingClientRect();if(b.bottom<0||b.top>window.innerHeight)return;const step=Math.PI/24,act={a:()=>orbit(step,0),d:()=>orbit(-step,0),w:()=>orbit(0,-step),s:()=>orbit(0,step),'+':()=>zoom(.85),'=':()=>zoom(.85),'-':()=>zoom(1/.85),r:()=>fit('iso')}[e.key.toLowerCase()];if(act){e.preventDefault();act()}});
 (function render(){requestAnimationFrame(render);controls.update();renderer.render(scene,camera);for(const marker of markers){const p=marker.point.clone().project(camera);marker.el.hidden=!group||p.z<-1||p.z>1;marker.el.style.left=((p.x+1)*.5*box.clientWidth)+'px';marker.el.style.top=((-p.y+1)*.5*box.clientHeight)+'px'}})();
 window.operationViewState=()=>({state:loadedKey,parts:group?.children.length||0,referenceCube:!!cube,loading,view:lastView});
}catch(error){document.getElementById('operation-v3d-status').textContent='无法启动3D，请使用支持WebGL的现代浏览器：'+error.message;window.operationView=async()=>{throw error};console.error(error)}
