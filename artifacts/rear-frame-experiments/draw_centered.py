from draw_vertical import software, OUT, m, convert
import numpy as np
import base64
ps=convert(m.module(0,steps=False));parts=[]
for p in ps:
    if p.name=='18938.dat' or (p.note=='侧架长梁' and p.pos[2]<0):parts.append(p.moved(m.I))
    elif p.note in {'竖L后架','竖架三孔梁'} and p.pos[2]<0:parts.append(p.moved(m.I,[0,20,0]))
path=OUT/'vertical-centered.ldr';path.write_text(m.to_ldr(parts,'长边居中，仅示意高度差'))
software.render({'model':str(path),'out':str(OUT/'vertical-centered.png'),'opts':{'w':1000,'h':660,'yaw':138,'pitch':22,'margin':.06}})
data=base64.b64encode((OUT/'vertical-centered.png').read_bytes()).decode()
(OUT/'vertical-centered.svg').write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="1060" height="900" viewBox="0 0 1060 900"><rect width="1060" height="900" fill="white"/><g font-family="sans-serif" fill="#172536"><text x="30" y="44" font-size="28" font-weight="bold">长边居中竖放：转盘接第2、第4孔</text><text x="30" y="83" font-size="22">绿色：竖L梁　橙色：随短边下移的3孔梁　灰色：原侧梁与转盘</text><image x="30" y="105" width="1000" height="660" href="data:image/png;base64,{data}"/><text x="30" y="802" font-size="23">L梁对齿轮外半轴套：每1°扫整圈无相交，最小间隙约2.22mm。</text><text x="30" y="842" font-size="23" fill="#aa2525">短边与原下侧梁错开一孔（8mm）；橙色梁尚未连接灰色侧梁。</text><text x="30" y="880" font-size="19" fill="#526171">孔位核对图，省略销轴；不能作为完成的装配方案。</text></g></svg>''')
