var CandidateSourceAdapter=(()=>{
 function prepare(loader,text,colorMeta){
  const map={};for(const match of text.matchAll(/^0 FILE (.+)$/gm)){const name=match[1].trim().replace(/\\/g,'/');map[name]=name}
  loader.setFileMap(map);
  const firstEnd=text.indexOf('\n');if(firstEnd<0)throw Error('Missing MPD root header');
  return text.slice(0,firstEnd+1)+colorMeta+'\n'+text.slice(firstEnd+1);
 }
 return {prepare};
})();
