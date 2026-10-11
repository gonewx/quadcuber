const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const target=process.argv[2]||'preview219/index.html';const h=fs.existsSync(target)?fs.readFileSync(target,'utf8'):fs.readFileSync('dist/index.html','utf8');
const source='../lift-feasibility/detailed-instructions-192/inventory-compatible-candidate/';
const model=JSON.parse(h.match(/<script>window.V3D_MODEL_TEXT=([\s\S]*?);<\/script>/)[1]);
assert(model===fs.readFileSync(source+'machine-working-927.mpd','utf8'),'Viewer must contain exact 927-part source, not the old192 model');
console.log('Exact219 source embedded');
for(const s of h.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g))new vm.Script(s[1]);
const hand=JSON.parse(fs.readFileSync(source+'viewer-handoff219.json','utf8')),r=JSON.parse(h.match(/window.LIFT_ROLES=(.*?);<\/script>/)[1]);
assert.deepEqual(r.moving_index1,hand.roles_core_index1.moving);assert.deepEqual(r.fixed_index1,hand.roles_core_index1.fixed);assert.deepEqual(r.key_index1,hand.roles_core_index1.key);
const top=t=>t.split('\n0 FILE ')[0].split('\n').filter(x=>x.startsWith('1 ')).map(x=>x.trim().split(/\s+/));
const working=top(model),parked=top(fs.readFileSync(source+'machine-park-921.mpd','utf8')),old=top(fs.readFileSync('../lift-feasibility/unified-base-validation/corrected-snapshot/shared-chassis-machine-900.mpd','utf8'));
assert.equal(working.length,927);assert.equal(parked.length,921);assert.equal(working.filter(x=>x[14]==='39790.dat').length,4);assert.equal(working.filter(x=>x[14]==='71709.dat').length,0);
assert.deepEqual(working.slice(219),old.slice(192),'Original708 instances must remain unchanged, including8 pending wallpin corrections');
const moving=new Set(r.moving_index1),keys=new Set(r.key_index1),expectedPark=working.filter((_,i)=>!keys.has(i+1));
let k=0;working.forEach((line,i)=>{if(keys.has(i+1))return;const q=parked[k++];assert.equal(q[14],line[14]);assert.equal(q[1],line[1]);for(let j=2;j<14;j++)assert(Math.abs(Number(q[j])-Number(line[j])-(j===3&&moving.has(i+1)?100:0))<1e-6)});
const {THREE,LDrawLoader,LDrawConditionalLineMaterial}=require('../viewer-fix/dependencies-classic.cjs');let fetches=0;global.fetch=()=>{fetches++;throw Error('Unexpected geometry fetch')};
const loader=new LDrawLoader();loader.setConditionalLineMaterial(LDrawConditionalLineMaterial);
loader.parse(model,group=>{
 assert.equal(group.children.length,927);const fn=h.slice(h.indexOf('function applyLiftView(){'),h.indexOf("document.getElementById('lift-pose').addEventListener"));const els={};const ctx={group,window:{LIFT_ROLES:r},document:{getElementById:id=>els[id]??={setAttribute(){}},dispatchEvent(){}},Event:class{},assemblyStep:null,cubeRef:{visible:true},restoreAssemblyMaterials:()=>{},label:{},liftDown:false,liftOnly:false};vm.createContext(ctx);vm.runInContext(fn,ctx);const initial=group.children.map(c=>c.position.clone());const counts=[];
 for(const [down,only,n]of[[false,false,927],[true,false,921],[true,true,213],[false,true,219],[false,false,927]]){ctx.liftDown=down;ctx.liftOnly=only;vm.runInContext('applyLiftView()',ctx);assert.equal(group.children.filter(c=>c.visible).length,n);counts.push(n);group.children.forEach((c,i)=>{assert.equal(c.position.y,initial[i].y+(down&&moving.has(i+1)?100:0));assert.equal(c.position.x,initial[i].x);assert.equal(c.position.z,initial[i].z)})}
 assert.equal(fetches,0);const materialColors={};let meshes=0,triangles=0;group.traverse(o=>{if(o.isMesh){meshes++;triangles+=(o.geometry.index?.count||o.geometry.attributes.position.count)/3;for(const m of(Array.isArray(o.material)?o.material:[o.material]))materialColors[m.name]=m.color?.getHexString()}});
 let stepGroupsChecked=0;
 if(h.includes('window.ASSEMBLY_BOOK=')){
  const book=JSON.parse(h.match(/window.ASSEMBLY_BOOK=([\s\S]*?);<\/script>/)[1]),sc={};assert.equal(book.core_count,219);vm.createContext(sc);vm.runInContext(fs.readFileSync('step-reader-core.js','utf8'),sc);
  group.traverse(o=>{if(o.isMesh){o.userData.baseMaterial=o.material;const mats=Array.isArray(o.material)?o.material:[o.material];const hi=mats.map(m=>{const q=m.clone();q.color=new THREE.Color(0xffb600);return q});o.userData.stepHighlightMaterial=Array.isArray(o.material)?hi:hi[0]}});
  for(const step of book.steps){const rr=sc.StepReaderCore.applyGroup(group,step),visible=new Set(step.visible_part_ids),highlight=new Set(step.highlight_part_ids||step.added_part_ids);assert.equal(rr.visibleParts,visible.size);assert.equal(rr.newParts,step.added_part_ids.length);group.children.forEach((c,i)=>{assert.equal(c.visible,visible.has(i+1));assert.equal(c.position.y,initial[i].y);c.traverse(o=>{if(o.isMesh)assert.equal(o.material,highlight.has(i+1)?o.userData.stepHighlightMaterial:o.userData.baseMaterial)})});stepGroupsChecked++;}
 }
 const result={stepGroupsChecked,syntax:'pass',embeddedModel:'exact219source',parts:927,core:219,moving:69,fixed:144,keys:6,visibleCounts:counts,strokeMM:40,parkedSourceMatches:true,original708Exact:true,original8WallpinFixIncluded:false,inventory39790:4,inventory71709:0,fetches,meshes,triangles,materialColors,browserRendering:'unverified'};fs.writeFileSync('preview219/validation.json',JSON.stringify(result,null,2));console.log(result);
},e=>{throw e});
