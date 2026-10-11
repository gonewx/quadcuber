var CandidateViewCore=(()=>{
 function create(states){
  for(const scope of ['core','whole'])for(const pose of ['up','down']){const s=states[scope+'_'+pose];if(!s||!Number.isInteger(s.count)||s.count<1)throw Error('Missing authored candidate state')}
  let scope='core',pose='up';
  const current=()=>({key:scope+'_'+pose,scope,pose,...states[scope+'_'+pose]});
  const set=(s,p)=>{if(!['core','whole'].includes(s)||!['up','down'].includes(p))throw Error('Invalid candidate view');scope=s;pose=p;return current()};
  return {current,set,toggleScope:()=>set(scope==='core'?'whole':'core',pose),togglePose:()=>set(scope,pose==='up'?'down':'up')};
 }
 return {create};
})();
