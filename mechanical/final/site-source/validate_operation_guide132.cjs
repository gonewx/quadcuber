const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),vm=require('node:vm'),crypto=require('node:crypto');
const {LDrawLoader,LDrawConditionalLineMaterial}=require('../viewer-fix/dependencies-classic.cjs');
const source='../lift-feasibility/pose-coupled-support-review/complete-seat-review/operation-guide132',raw=fs.readFileSync(path.join(source,'operation-guide132.json')),data=JSON.parse(raw),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const html=fs.readFileSync('dist/operation-guide.html','utf8'),ctx={window:{}};vm.createContext(ctx);vm.runInContext([...html.matchAll(/<script>([\s\S]*?)<\/script>/g)][0][1],ctx);vm.runInContext(fs.readFileSync('candidate-source-adapter.js','utf8'),ctx);
const bundled=ctx.window.OPERATION_GUIDE,manifest=JSON.parse(fs.readFileSync('operation-guide132-source.json','utf8'));
assert.equal(manifest.source_sha256,sha(raw));assert.equal(bundled.review_only,true);assert.equal(bundled.stages.length,17);assert.equal(Object.keys(bundled.states).length,9);
assert(Object.values(bundled.physical_validation).every(value=>value===false));assert.equal(bundled.exact_reverse_zh,data.exact_reverse_zh);
const top=text=>text.split('\n0 FILE ')[0].split('\n').filter(line=>line.startsWith('1 '));
const unique=new Map();
for(const [key,state]of Object.entries(data.states)){
 const bytes=fs.readFileSync(path.join(source,state.file));assert.equal(sha(bytes),state.sha256);assert.equal(bundled.states[key].model_text,bytes.toString());assert.equal(bundled.states[key].count,state.count);assert.equal(top(bytes.toString()).length,state.count);assert.equal(state.cube_size_mm,56);assert.equal(state.cube_orientation,'axis_aligned');assert.equal(state.count,state.keys_present?899:897);assert.equal(state.seat_drop_mm,state.tray_zh.includes('下位')?40:0);unique.set(state.sha256,{key,...state});
 assert.deepEqual(JSON.parse(JSON.stringify(bundled.states[key].cube_position_mm)),state.cube_position_mm);
 assert(fs.existsSync(path.join('dist',bundled.states[key].diagram_file)));assert.equal(sha(fs.readFileSync(path.join('dist',bundled.states[key].diagram_file))),sha(fs.readFileSync(path.join(source,state.diagram_file))));
}
for(const [i,stage]of data.stages.entries()){
 const actual=bundled.stages[i];for(const key of ['id','title_zh','state_id','action_type','flow'])assert.equal(actual[key],stage[key]);for(const key of ['instructions_zh','cautions_zh'])assert.deepEqual(JSON.parse(JSON.stringify(actual[key])),stage[key]);assert(fs.existsSync(path.join('dist',actual.diagram_file)));assert.equal(sha(fs.readFileSync(path.join('dist',actual.diagram_file))),sha(fs.readFileSync(path.join(source,stage.diagram_file))));
}
assert.equal(unique.size,7);let fetches=0;global.fetch=()=>{fetches++;throw Error('Unexpected external geometry request')};
(async()=>{
 const models=[];
 for(const state of unique.values()){
  const loader=new LDrawLoader();loader.setConditionalLineMaterial(LDrawConditionalLineMaterial);
  const renderText=ctx.CandidateSourceAdapter.prepare(loader,bundled.states[state.key].model_text,ctx.window.CANDIDATE_COLOR_META);
  const model=await new Promise((resolve,reject)=>{const timeout=setTimeout(()=>reject(Error('Unresolved state '+state.key)),120000);loader.parse(renderText,g=>{clearTimeout(timeout);resolve(g)},e=>{clearTimeout(timeout);reject(e)})});
  assert.equal(model.children.length,state.count);let meshes=0,triangles=0,unknownColors=0;
  model.traverse(o=>{if(o.isMesh){meshes++;triangles+=(o.geometry.index?.count||o.geometry.attributes.position.count)/3;for(const m of(Array.isArray(o.material)?o.material:[o.material]))if(m.color?.getHexString()==='ff00ff')unknownColors++}});assert.equal(unknownColors,0);models.push({file:state.file,parts:model.children.length,meshes,triangles,unknownColors});console.log(models.at(-1));
  const geometries=new Set(),materials=new Set();model.traverse(o=>{if(o.geometry)geometries.add(o.geometry);for(const m of(Array.isArray(o.material)?o.material:o.material?[o.material]:[]))materials.add(m)});geometries.forEach(g=>g.dispose());materials.forEach(m=>m.dispose());
 }
 assert.equal(fetches,0);
 const result={source_sha256:sha(raw),stages:17,visualStates:9,uniqueAuthoredModels:7,models,referenceCubeMm:56,cubeExcludedFromLegoCount:true,worldAxes:'R=+X; L=-X; F=+Z; B=-Z; up=-Y',stageInstructionsExact:true,diagramsMatchSource:true,externalGeometryRequests:fetches,physicalAcceptance:false,browserVisualQA:'Not performed; separate from real model parser and simulated DOM tests'};
 fs.writeFileSync('operation-guide132-validation.json',JSON.stringify(result,null,2)+'\n');console.log('PASS operation guide source and loader validation');
})().catch(error=>{console.error(error);process.exitCode=1});
