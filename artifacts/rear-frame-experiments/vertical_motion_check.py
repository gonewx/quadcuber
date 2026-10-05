"""竖放候选的81点开合筛查；回转失败另单列。"""
from vertical_rear import *
import vertical_rear as vertical
old_mount=rear.intended_mount

def mounting(a,b):
    a=a.moved(m.I);b=b.moved(m.I)
    for p in (a,b):
        if p.note=='竖L后架':p.note='粗梁后接架'
    return old_mount(a,b)
rear.convert=vertical.convert
rear.NEW=vertical.NEW
rear.intended_mount=mounting
result=rear.scan()
path=Path(__file__).resolve().parent/'vertical-rear-check.json'
data=json.loads(path.read_text());data['开合检查']=result
path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print('开合相交数',result['相交数']);print('最小间隙',result['最小间隙'][:3])
