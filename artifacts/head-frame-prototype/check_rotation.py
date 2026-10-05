"""本臂整圈回转与相邻竖直臂的几何筛查。"""
import json
from pathlib import Path
import boxed_slider as w
def rotation_module(*args,**kwargs):
 parts=w.module(*args,**kwargs)
 # 原转盘未改，既有转盘配合不作为新增前端距离查询；单臂检查仍保留。
 for p in parts:
  if p.name=='18938.dat':p.note=''
 return parts
w.m.module=rotation_module
w.m.OPEN_S=w.OPEN_S
result=w.mesh.front_rotation_check()
Path(__file__).with_name('boxed-rotation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:(len(v) if isinstance(v,list) else v) for k,v in result.items()},ensure_ascii=False,indent=2))
