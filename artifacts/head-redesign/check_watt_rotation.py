from watt_candidate import *
m.module=module
result=mesh.front_rotation_check()
Path(__file__).with_name('watt-rotation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
