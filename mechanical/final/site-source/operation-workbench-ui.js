/* Workbench controls only. The authored operation state machine owns every stage. */
(()=>{
 const el=id=>document.getElementById(id),shell=el('viewport-shell'),button=el('view-fullscreen');
 const views=[...document.querySelectorAll('[data-view]')],zooms=[...document.querySelectorAll('[data-zoom]')];
 let describedIndex=null;
 function list(id,items){const node=el(id);node.replaceChildren();for(const text of items||[]){const item=document.createElement('li');item.textContent=text;node.appendChild(item)}}
 window.operationWorkbenchSync=({index,stage},busy,displayed)=>{
  if(index!==describedIndex){el('operation-panel').scrollTop=0;el('operation-fullscreen-note').scrollTop=0;describedIndex=index}
  el('operation-view-title').textContent=(index+1)+' / '+window.OPERATION_GUIDE.stages.length+' · '+stage.title_zh;
  list('operation-expanded-instructions',stage.instructions_zh);list('operation-expanded-cautions',stage.cautions_zh);
  el('operation-expanded-hands').hidden=stage.action_type!=='motor_design';
  for(const b of [...views,...zooms])b.disabled=busy||!displayed;
  el('operation-fit').disabled=busy||!displayed;
 };
 for(const b of views)b.addEventListener('click',()=>window.operationCamera?.view(b.dataset.view));
 for(const b of zooms)b.addEventListener('click',()=>window.operationCamera?.zoom(Number(b.dataset.zoom)));
 function sync(){const expanded=document.fullscreenElement===shell||shell.classList.contains('expanded');button.textContent=expanded?'退出大屏':'全屏查看';button.setAttribute('aria-pressed',String(expanded));document.body.classList.toggle('expanded-body',shell.classList.contains('expanded'));window.operationCamera?.resize()}
 async function expand(){if(document.fullscreenElement===shell){await document.exitFullscreen();sync();button.focus();return}if(shell.classList.contains('expanded')){shell.classList.remove('expanded');sync();button.focus();return}if(shell.requestFullscreen){try{await shell.requestFullscreen();sync();return}catch(_){}}shell.classList.add('expanded');sync()}
 button.addEventListener('click',expand);document.addEventListener('fullscreenchange',sync);
 document.addEventListener('keydown',event=>{if(event.key==='Escape'&&shell.classList.contains('expanded')){event.preventDefault();shell.classList.remove('expanded');sync();button.focus()}});
 const current=window.operationStageState();window.operationWorkbenchSync({index:current.index,stage:window.OPERATION_GUIDE.stages[current.index]},current.busy,current.displayed);
})();
