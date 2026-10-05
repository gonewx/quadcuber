from watt_candidate import *
from collections import Counter
old=Counter(p.name for p in BASE_MODULE(0,steps=False));new=Counter(p.name for p in module(0,steps=False))
rows=[]
for name in sorted(old.keys()|new.keys()):
    if old[name]!=new[name]:rows.append({'编号':name.removesuffix('.dat'),'名称':m.CATALOG[name][0],'旧_单臂':old[name],'新_单臂':new[name],'变化_单臂':new[name]-old[name],'变化_四臂':4*(new[name]-old[name])})
result={'旧_单臂总件数':sum(old.values()),'新_单臂总件数':sum(new.values()),'变化_四臂总件数':4*(sum(new.values())-sum(old.values())),'变化':rows}
Path(__file__).with_name('bom-delta.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False,indent=2))
