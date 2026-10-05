from watt_candidate import *
worst={}
for frac in np.linspace(0,1,81):
    ps=module(float(frac*m.OPEN_S),steps=False)
    groups=[('输入销对摆杆',[p for p in ps if p.note=='输入无摩擦关节销'],[p for p in ps if p.note=='Watt连杆']),('根轴止挡对夹指',[p for p in ps if p.note=='Watt根轴'],[p for p in ps if p.name=='32524.dat' and p.color==m.C_JAW]),('输入杆对短驱动',[p for p in ps if p.note=='输入薄连杆'],[p for p in ps if p.note=='导向驱动薄梁'])]
    for name,aa,bb in groups:
        for a in aa:
            for b in bb:
                gap=fcl.distance(mesh.obj(a),mesh.obj(b),fcl.DistanceRequest(),fcl.DistanceResult())*.4
                if name not in worst or gap<worst[name]['间隙_mm']:worst[name]={'间隙_mm':gap,'开度比例':float(frac),'零件对':[a.name,b.name]}
result={'开度数':81,'最小间隙':worst}
Path(__file__).with_name('local-gaps.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
