const fs=require('fs'),vm=require('vm'),assert=require('assert/strict'),path=require('path');
const current=fs.readFileSync('dist/index.html','utf8'),history=fs.readFileSync('dist/history-219.html','utf8'),base=fs.readFileSync('history219-source.html','utf8');
function scripts(html){return [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(m=>m[1])}
function dataset(html,key){const mark='window.'+key+'=',start=html.indexOf(mark);assert(start>=0,key+' missing');const text=html.slice(start+mark.length);let quoted=false,escaped=false,depth=0;for(let i=0;i<text.length;i++){const c=text[i];if(quoted){if(escaped)escaped=false;else if(c==='\\')escaped=true;else if(c==='"')quoted=false}else if(c==='"')quoted=true;else if(c==='{'||c==='[')depth++;else if(c==='}'||c===']')depth--;else if(c===';'&&depth===0)return JSON.stringify(JSON.parse(text.slice(0,i)));}throw Error('Unclosed dataset '+key)}
assert.equal(dataset(history,'ASSEMBLY_BOOK'),dataset(base,'ASSEMBLY_BOOK'));
assert.equal(dataset(history,'V3D_MODEL_TEXT'),dataset(base,'V3D_MODEL_TEXT'));
assert.equal(JSON.parse(dataset(history,'ASSEMBLY_BOOK')).steps.length,145);
assert(current.includes('var CandidateStepsCore='),'Detailed step core must be bundled');assert(current.indexOf('var CandidateStepsCore=')<current.indexOf('window.showCandidateStep='),'Detailed step core must load before viewer');assert(!current.includes('132件小样步骤尚未接入'));assert(current.includes('window.CANDIDATE_STEP_BOOK='));assert(!current.includes('window.ASSEMBLY_BOOK='));assert(!current.includes('window.V3D_MODEL_TEXT='));
for(const t of ['132件小样＋59件复用共同底盘＝191件','原四臂708件＝899件整机','承重／销尖滑动／半轴套保持未实测','不可照搭运行','安装环境扫掠尚未验证','8枚墙脚销','HOLD','132件 · 逐步审阅'])assert(current.includes(t),t);
for(const h of [current,history])assert(h.includes('已收到放入魔方即下垂的实物失败，承重待修，暂停带魔方运行'));
assert(current.includes('href="history-219.html"'));assert(history.includes('href="index.html"'));
for(const [name,html]of [['index.html',current],['history-219.html',history]]){
 for(const script of scripts(html))new vm.Script(script,{filename:name});
 const ids=[...html.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);assert.equal(new Set(ids).size,ids.length,name+' duplicate IDs');
 for(const [,link]of html.matchAll(/\bhref="([^"]+)"/g)){
  if(/^(data:|https?:|mailto:)/.test(link))continue;
  const [file,anchor]=link.split('#');if(file)assert(fs.existsSync(path.join('dist',file)),link);else if(anchor)assert(ids.includes(anchor),link);
 }
}
const result={candidateDefault:132,historical219ModelUnchanged:true,historical145InstructionsUnchanged:true,riskWarningsPresent:true,historyPhysicalFailureExplicit:true,linksAndIDs:'pass',inlineJavaScriptSyntax:'pass',browserVisualVerification:'not performed'};
fs.writeFileSync('dual-page-validation.json',JSON.stringify(result,null,2)+'\n');console.log(result);
