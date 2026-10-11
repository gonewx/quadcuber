from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import MECHANICAL, ASSEMBLY, MANUAL_OUTPUT
"""Render final-design base assembly pages from the audited native meshes."""
from pathlib import Path
import sys,json,hashlib,importlib.util
H=MANUAL_OUTPUT;sys.path.insert(0,str(MECHANICAL));import candidate as C
source=MECHANICAL/'inputs/manual-inputs/native_base_renderer.py'
spec=importlib.util.spec_from_file_location('r4_native_base_renderer',source);r=importlib.util.module_from_spec(spec);exec(compile(source.read_text().replace('fig.text(.758,.302', 'fig.text(.758,.276').replace("'合并已完成组件'", "'四角闭合核对'").replace("'本步不增加核心零件'","'本步不增加零件'").replace("'金色组件沿箭头合拢'","'金色：本步核对的转角'"),str(source),'exec'),r.__dict__)
r.OUT=H;r.P={i:p for i,p in enumerate(C.retained_base(),1)};r.W={};r.M={}
book=json.loads((ASSEMBLY/'base-steps.json').read_text());selected=set(sys.argv[1:]);report=[]
for st in book['steps']:
 if selected and st['id']not in selected:continue
 # Keep legacy file names for references while replacing only affected image content.
 generated=r.render_step(st);src=H/'images'/f"{st['id']}.png";dst=H/st['image_relative'];src.replace(dst)
 generated['image_path']=str(dst);generated['step_sha256']=hashlib.sha256(json.dumps(st,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();generated['geometry_source']='candidate.retained_base';generated['revision']=C.REVISION
 dst.with_suffix('.json').write_text(json.dumps(generated,ensure_ascii=False,indent=2));report.append(generated);print(st['id'],flush=True)
(H/'base-r4-render.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
