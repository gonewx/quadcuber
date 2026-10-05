from vertical_forward import *
import vertical_forward as vertical

def mounting(a,b):
    tt,p=(a,b) if a.name=='18938.dat' else (b,a)
    if tt.name!='18938.dat' or p.note not in {'竖架三孔梁','竖架上短梁'}:return False
    normal=tt.rot[:,0];sign=np.sign((p.pos-tt.pos)@normal)
    q=p.moved(m.I,sign*normal*1e-4)
    return fcl.distance(mesh.obj(tt),mesh.obj(q),fcl.DistanceRequest(),fcl.DistanceResult())>=.999e-4
rear.convert=vertical.convert;rear.NEW=vertical.NEW;rear.intended_mount=mounting
result=rear.scan()
path=Path(__file__).resolve().parent/'vertical-forward-check.json';data=json.loads(path.read_text());data['开合检查']=result
path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print('开合相交数',result['相交数']);print('最小间隙',result['最小间隙'][:6]);print('相交',result['相交记录'][:4])
