"""洞洞板装配图：孔位、元件和导线共享同一份坐标数据。

坐标 (列, 行)，行 1=A；背面以竖直轴镜像，孔名不变。
DRV8833 引脚由用户实物丝印确认；模块机械排距暂按10.16mm。
"""
from html import escape
from pathlib import Path

COLS, ROWS, PITCH = 32, 24, 28
OX, OY = 96, 104
WIDTH, HEIGHT = 1060, 850
COLORS = {'9V': '#d94a12', 'GND': '#263445', '5V': '#d32564',
          'M1': '#783cb3', 'M2': '#a454d1', 'IN1': '#14844a',
          'IN2': '#2464bd', 'PWM': '#07888b', '3V3': '#b47800'}
TERMINALS = [
    ('J1', '开关后 9V 输入', [(3, 3), (5, 3)], ['+9V', 'GND'], 'top'),
    ('J4', 'EV3 马达 1 / 2 脚', [(3, 22), (5, 22)], ['M1', 'M2'], 'bottom'),
]
LEFT = ['VM', 'NC', 'GND', 'AO1', 'AO2', 'BO2', 'BO1', 'GND']
RIGHT = ['NC', 'AIN2', 'AIN1', 'STBY', 'BIN1', 'BIN2', 'NC', 'GND']
HEADERS = [
    ('J5', 'male', [(23,22),(24,22),(25,22)], ['GND','+5V','SIG'], '接舵机三孔母头'),
    ('J6', 'female', [(15,22),(16,22)], ['+5V','GND'], '接面包板公头线'),
    ('J7', 'female', [(9,22),(10,22),(11,22),(12,22)], ['IN1','IN2','PWM','3V3'], '接 Pico 公头线'),
]
PINS = {}
for ref, _, pins, names, _ in TERMINALS:
    for i, (pos, name) in enumerate(zip(pins, names), 1):
        PINS[f'{ref}.{i}'] = (pos, name)
# U2 四角针座；孔距是这版装配假设，XL4005 模块没有统一机械标准。
PINS.update({'J2.1': ((16, 9), 'IN+'), 'J2.2': ((16, 15), 'IN−'),
             'J3.1': ((31, 9), 'OUT+'), 'J3.2': ((31, 15), 'OUT−')})
for col, names in ((9, LEFT), (13, RIGHT)):
    for row, name in enumerate(names, 9):
        key = f'{name}_{col}_{row}' if name in ('GND', 'NC') else name
        PINS['U1.' + key] = ((col, row), name)
for ref,kind,pins,names,label in HEADERS:
    for i,(pos,name) in enumerate(zip(pins,names),1):
        PINS[f'{ref}.{i}']=(pos,name)

# 每根线只在首尾焊接；中间点仅规定绝缘导线的走向。
WIRES = [
    ('W01', '9V', 'J1.1', 'U1.VM', [(3, 6), (7, 6), (7, 7), (9, 7)], '9V → 驱动 VM'),
    ('W02', '9V', 'J1.1', 'J2.1', [(3, 5), (16, 5)], '9V → 降压输入'),
    ('W03', 'GND', 'J1.2', 'U1.GND_9_16', [(5, 4), (8, 4), (8, 16)], '驱动地单独回电源入口'),
    ('W04', 'GND', 'J1.2', 'J2.2', [(5, 6), (18, 6), (18, 15)], '电源地 → 降压 IN−'),
    ('W05', '5V', 'J3.1', 'J5.2', [(32, 9), (32, 18), (24, 18)], '5V → 舵机电源'),
    ('W06', '5V', 'J3.1', 'J6.1', [(31, 8), (29, 8), (29, 20), (15, 20)], '5V → 面包板小电流支路'),
    ('W07', 'GND', 'J3.2', 'J5.1', [(30, 15), (30, 21), (23, 21)], '舵机地单独回降压 OUT−'),
    ('W08', 'GND', 'J3.2', 'J6.2', [(31, 16), (28, 16), (28, 19), (16, 19)], '面包板公共地'),
    ('W09', 'M1', 'U1.AO1', 'J4.1', [(3, 12)], '驱动 AOUT1 → 马达 M1'),
    ('W10', 'M2', 'U1.AO2', 'J4.2', [(5, 13)], '驱动 AOUT2 → 马达 M2'),
    ('W11', 'IN1', 'J7.1', 'U1.AIN1', [(9, 18), (14, 18), (14, 11)], 'GP2 → AIN1'),
    ('W12', 'IN2', 'J7.2', 'U1.AIN2', [(10, 17), (15, 17), (15, 10)], 'GP3 → AIN2'),
    ('W13', 'PWM', 'J7.3', 'J5.3', [(11, 23), (25, 23)], 'GP8 → 舵机信号'),
    ('W14', '3V3', 'J7.4', 'U1.STBY', [(12, 19), (11, 19), (11, 12)], 'Pico 3V3 → STBY 使能'),
]


def hole(pos):
    return f'{chr(64 + pos[1])}{pos[0]}'


def xy(pos, back=False):
    c, r = pos
    return OX + ((COLS - c) if back else (c - 1)) * PITCH, OY + (r - 1) * PITCH


def txt(x, y, value, size=15, color='#172c38', anchor='middle', weight='normal'):
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}" '
            f'font-weight="{weight}" fill="{color}">{escape(str(value))}</text>')


def rect(x, y, w, h, fill, stroke='none', radius=3, extra=''):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" {extra}/>'


def points(w):
    return [PINS[w[2]][0], *w[4], PINS[w[3]][0]]


def board_svg(back=False):
    face = '焊接面 · 已左右镜像' if back else '元件面 · 从上往下看'
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="{face}，32列24行洞洞板装配图" style="background:#f6f4ee;font-family:Arial,Microsoft YaHei,sans-serif">',
         '<defs><linearGradient id="pb-metal"><stop stop-color="#e5e9ed"/><stop offset=".5" stop-color="#a2adb6"/><stop offset="1" stop-color="#e6e8ea"/></linearGradient></defs>',
         txt(42, 32, face, 22, anchor='start', weight='bold'),
         txt(42, 50, '先焊底座所有针脚；彩色导线仅焊首尾，跨线绝缘。' if back else '两块模块插排母 · 图示端子为插头 + 底座 · 金色圆点为穿孔投影', 12, anchor='start'),
         rect(OX-35, OY-28, (COLS-1)*PITCH+70, (ROWS-1)*PITCH+56, '#b58b4b' if back else '#d7ba7d', '#886c3f', 10)]
    for c in range(1, COLS+1):
        x, _ = xy((c, 1), back)
        s.append(txt(x, OY-36, c, 12))
        s.append(txt(x, OY+(ROWS-1)*PITCH+47, c, 12))
    for r in range(1, ROWS+1):
        _, y = xy((1, r), back)
        for x in (OX-49, OX+(COLS-1)*PITCH+49):
            s.append(txt(x, y+4, chr(64+r), 13, weight='bold'))
        for c in range(1, COLS+1):
            x, y = xy((c, r), back)
            s.append(f'<circle cx="{x}" cy="{y}" r="{5.9 if back else 4.6}" fill="{chr(35)}d9ac65" stroke="#927044" stroke-width="1"/>')
            s.append(f'<circle cx="{x}" cy="{y}" r="2.3" fill="#58482f"/>')
    x, y = xy((1, 1), back)
    s.append(f'<path d="M{x-10} {y-18}h20l-10 14z" fill="#c52e21"/>')
    for ref, label, pins, names, edge in TERMINALS:
        xvals = [xy(p, back)[0] for p in pins]
        y = xy(pins[0], back)[1]
        x0, w = min(xvals)-PITCH, max(xvals)-min(xvals)+2*PITCH
        if back:
            s.append(rect(x0, y-39, w, 78, 'none', '#846538', 4, 'stroke-dasharray="5 4"'))
            s.append(txt((min(xvals)+max(xvals))/2, y-44, ref, 14, weight='bold'))
        else:
            # 深绿是焊在板上的底座，浅绿是可整块拔下的插头。
            s.append(rect(x0+3, y-53, w, 114, '#826d48', radius=5))
            s.append(rect(x0, y-57, w, 114, '#164e40', '#10382e', 4))
            s.append(rect(x0+3, y-47, w-6, 88, '#419e74', '#1c654d', 3))
            s.append(f'<path d="M{x0+2} {y+44}h{w-4}" stroke="#a4d5b6" stroke-width="2" stroke-dasharray="5 3"/>')
            for i, (x, name) in enumerate(zip(xvals, names), 1):
                s.append(rect(x-PITCH+5, y+(18 if edge=='bottom' else -42), 2*PITCH-10, 18, '#123a30', radius=2))
                s.append(f'<circle cx="{x}" cy="{y-5}" r="14" fill="url(#pb-metal)" stroke="#6b7a84"/>')
                s.append(f'<path d="M{x-9} {y+3}l18 -16" stroke="#515c63" stroke-width="3"/>')
                s.append(txt(x, y+(76 if edge=='top' else -66), f'{i} {name}', 12, weight='bold'))
            s.append(txt((min(xvals)+max(xvals))/2, y+(-67 if edge=='top' else 76), ref, 16, weight='bold'))
            s.append(txt((min(xvals)+max(xvals))/2, 837 if edge=='bottom' else y+99, label, 12))
    # DRV8833：按用户提供的左右脚序绘制。
    xl, yt = xy((9, 9), back)
    xr, yb = xy((13, 16), back)
    x0 = min(xl, xr)-14
    s.append(rect(x0, yt-14, 140, 224, 'none' if back else '#21734b', '#28563b', 3,
                  'stroke-dasharray="5 4"' if back else ''))
    if not back:
        for side, names in ((9, LEFT), (13, RIGHT)):
            for row, name in enumerate(names, 9):
                x, y = xy((side, row))
                label = name.replace(' OUT', 'O').replace(' IN', 'I')
                s.append(txt(x+(10 if side==9 else -10), y+3, label, 9, '#f4fff4', 'start' if side==9 else 'end'))
        s.append(txt((xl+xr)/2, yt-27, 'U1 · DRV8833', 15, weight='bold'))
        s.append(txt((xl+xr)/2, yb+38, '按用户丝印朝向放置', 12))
    else:
        s.append(txt((xl+xr)/2, yt-21, 'U1', 15, weight='bold'))
    # U2 降压模块：假定四角电源孔 38.1 × 15.24mm，板约44 × 22mm。
    xa,ya=xy((16,9),back); xb,yb=xy((31,15),back)
    bx=min(xa,xb)-32; bw=abs(xb-xa)+64
    s.append(rect(bx,ya-36,bw,yb-ya+72,'none' if back else '#245c9d','#204c76',5,
                  'stroke-dasharray="5 4"' if back else ''))
    if not back:
        s.append(txt((xa+xb)/2,ya-50,'U2 · DSN5000 / XL4005',17,weight='bold'))
        # 顶视外形：电感、芯片、调压电位器、模块自带电容。
        s.append(rect(xa+155,ya+34,118,112,'#182637','#111b25',7))
        s.append(f'<circle cx="{xa+214}" cy="{ya+90}" r="43" fill="#695029" stroke="#302b22" stroke-width="9"/>')
        for i in range(9):
            s.append(f'<path d="M{xa+181+i*8} {ya+63}v54" stroke="#be8d36" stroke-width="4"/>')
        s.append(rect(xa+296,ya+30,67,46,'#2b8bd0','#183e75',4))
        s.append(f'<circle cx="{xa+328}" cy="{ya+53}" r="13" fill="#c1a764"/><path d="M{xa+320} {ya+53}h16" stroke="#6d562f" stroke-width="3"/>')
        s.append(txt(xa+327,ya+95,'调压',13,'#fff'))
        s.append(rect(xa+62,ya+75,61,56,'#20272c','#112333',3))
        s.append(txt(xa+93,ya+109,'XL4005',10,'#c9d3d7'))
        for cx,cy in [(xa+78,ya+29),(xb-52,yb-14)]:
            s.append(f'<circle cx="{cx}" cy="{cy}" r="24" fill="#abbfc8" stroke="#253c4c" stroke-width="7"/>')
        for key in ('J2.1','J2.2','J3.1','J3.2'):
            pos,label=PINS[key]; px,py=xy(pos)
            s.append(rect(px-10,py-10,20,20,'#161f27',radius=2))
            s.append(txt(px+(18 if pos[0]==16 else -18),py+5,label,13,'white','start' if pos[0]==16 else 'end'))
        s.append(txt((xa+xb)/2,yb+57,'四角焊排针 ↓ 插入板上四个排母座',14,weight='bold'))
        s.append(txt((xa+xb)/2,yb+77,'本图孔距：横 38.1mm / 竖 15.24mm',13))
    else:
        s.append(txt((xa+xb)/2,ya-44,'U2（正面可拔下）',15,weight='bold'))
        for key in ('J2.1','J2.2','J3.1','J3.2'):
            pos,label=PINS[key]; px,py=xy(pos,True)
            s.append(txt(px,py+(-15 if pos[1]==9 else 25),label,12,weight='bold'))
    # 根据线端公母匹配排针或排母，均为2.54mm。
    for ref,kind,pins,names,label in HEADERS:
        xp=[xy(p,back)[0] for p in pins]; y=xy(pins[0],back)[1]
        s.append(rect(min(xp)-13,y-13,max(xp)-min(xp)+26,26,'none' if back else '#24282a','#4c4e4c',2,
                      'stroke-dasharray="4 3"' if back else ''))
        s.append(txt(sum(xp)/len(xp),y-29,ref+(' 公排针' if kind=='male' else ' 母座'),14,weight='bold'))
        if not back:
            for i,x in enumerate(xp,1):
                s.append(rect(x-5,y-5,10,10,'#e7c663' if kind=='male' else '#080d10','#8f7135',0))
                s.append(txt(x,y+29,i,12))
            s.append(txt(sum(xp)/len(xp),y+61,label,12))
    if back:
        for pos,label in PINS.values():
            px,py=xy(pos,True)
            s.append(f'<circle cx="{px}" cy="{py}" r="5" fill="url(#pb-metal)" stroke="#50616c"/><circle cx="{px}" cy="{py}" r="1.8" fill="#50524c"/>')
    if back:
        for w in WIRES:
            ident, net, a, b, _, description = w
            pts = [xy(p, True) for p in points(w)]
            path = 'M' + ' L'.join(f'{x} {y}' for x,y in pts)
            s.append(f'<g class="pb-wire" data-wire="{ident}"><title>{ident} {escape(description)}：{hole(PINS[a][0])} → {hole(PINS[b][0])}</title>')
            s.append(f'<path d="{path}" fill="none" stroke="#fcf6e5" stroke-width="9" stroke-linejoin="round" stroke-linecap="round"/>')
            s.append(f'<path d="{path}" fill="none" stroke="{COLORS[net]}" stroke-width="5" stroke-linejoin="round" stroke-linecap="round"/>')
            # 最长线段中部放线号。
            p,q = max(zip(pts, pts[1:]), key=lambda v: abs(v[0][0]-v[1][0])+abs(v[0][1]-v[1][1]))
            tx,ty=(p[0]+q[0])/2,(p[1]+q[1])/2
            s.append(rect(tx-21,ty-11,42,20,'#fffdf5',COLORS[net],4))
            s.append(txt(tx,ty+3,ident,11,COLORS[net],weight='bold'))
            for ex,ey in (pts[0],pts[-1]):
                s.append(f'<circle cx="{ex}" cy="{ey}" r="6.5" fill="url(#pb-metal)" stroke="#354751" stroke-width="1.5"/>')
                s.append(f'<circle cx="{ex}" cy="{ey}" r="2" fill="{COLORS[net]}"/>')
            s.append('</g>')
    else:
        for name,(pos,label) in PINS.items():
            if name.startswith(('J5.','J6.','J7.')):
                continue
            x,y=xy(pos)
            s.append(f'<circle cx="{x}" cy="{y}" r="4" fill="#f4d56e" stroke="#4a4e3d"><title>{escape(name)} · {hole(pos)} · {escape(label)}</title></circle>')
    s.append(txt(42,812,'A 行一直在上方；像翻书一样左右翻板。背面右上红三角仍是 A1。' if back else '深绿底座焊板，浅绿插头可拔。U1 用排母；U2 用四角针座；无螺钉、无支柱。',14,anchor='start'))
    s.append('</svg>')
    return ''.join(s)


def harness_svg():
    # 板外器件按外形绘制；线端直接标注洞洞板孔位，避免依赖颜色。
    s=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 720" role="img" aria-label="板外接线：电源插座、串联保险丝开关、降压模块与洞洞板端子" style="background:#f6f4ee;font-family:Arial,Microsoft YaHei,sans-serif">',
       txt(32,36,'板外接线 · 先把降压输出调到 5.0V',24,anchor='start',weight='bold'),
       rect(45,92,100,70,'#263744','#172a36',12),
       '<circle cx="65" cy="127" r="22" fill="#101b24" stroke="#a8afb1" stroke-width="5"/><circle cx="65" cy="127" r="5" fill="#c1b189"/>',
       txt(95,190,'DC-005 · 5.5 × 2.1mm',14),txt(95,210,'中心正极 / 外套负极',13),
       rect(233,99,142,48,'#222e3a','#101b24',8),rect(286,100,12,46,'#626b71',radius=1),txt(304,129,'F1',16,'white'),
       txt(303,183,'线式保险丝座',14),txt(303,205,'额定值按实际电流选',12),
       rect(462,91,82,68,'#263644','#13232b',5),rect(480,101,46,47,'#a82e23','#222',4),txt(503,127,'I / O',14,'white'),
       txt(503,183,'SW1 · 直流开关',14),
       rect(766,91,276,95,'#126aaa','#18415c',6),txt(904,116,'洞洞板 J1',18,'white',weight='bold'),
       txt(904,142,'1 / C3 = +9V',15,'white'),txt(904,167,'2 / C5 = GND',15,'white')]
    for d,color in [('M145 114H233','#d94a12'),('M375 114H462','#d94a12'),('M544 114H696V138H766','#d94a12'),('M145 145H186V238H696V163H766','#263445')]:
        s.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="6" stroke-linejoin="round"/>')
    s += [txt(32,259,'DC-005：两根短线接可拔 J1 插头；第三个切换脚留空。脚位用未供电插头 + 万用表确认。',14,anchor='start'),
          txt(550,316,'两块模块的安装方式 · 侧视（上下拔插）',23,weight='bold'),
          rect(270,561,560,16,'#d7ba7d','#8a6c40',2),txt(895,575,'洞洞板',15),
          rect(270,385,560,14,'#245c9d','#204c76',2),txt(550,374,'U2 降压模块（电感、电容朝上）',18,weight='bold')]
    for x in (306,788):
        s.append(rect(x-5,399,10,77,'#d6b050','#8f7029',0))
        s.append(rect(x-14,413,28,24,'#1b2630',radius=2))
        s.append(rect(x-17,509,34,52,'#1b2630','#0e1c25',3))
        s.append(rect(x-7,508,14,7,'#786542',radius=1))
        s.append(rect(x-4,575,8,24,'#d6b050','#8f7029',0))
        s.append(f'<path d="M{x} 483v18m-6 -7l6 7 6 -7" fill="none" stroke="#d56c21" stroke-width="3"/>')
    s += [txt(550,438,'排针焊在模块上，模块可整块拔下',16),
          txt(550,486,'↓ 对准针脚，垂直插入 ↓',17,'#b45119',weight='bold'),
          txt(550,543,'排母焊在洞洞板上',16),
          txt(550,617,'U1 同理：两排 1×8 排母。U2：四个分立 1 针排母，按四角电源焊孔定位。',15),
          txt(550,649,'U2 本图假设孔距 38.1 × 15.24mm；孔距不符时改排母位置，不掰模块硬插。',15),
          txt(550,681,'J1/J4 用可拔端子；J5 公排针对舵机母头；J6/J7 母座接公头线。',15),'</svg>']
    return ''.join(s)


# 两端均为公头：洞洞板插排母，另一端插面包板弹片孔。
BRIDGE = [
    ('B01','5V','J6.1','T+',8,'上排 + 第8孔','降压5V → 编码器及电平转换'),
    ('B02','GND','J6.2','T-',9,'上排 − 第9孔','公共地'),
    ('B03','IN1','J7.1','j',6,'j6','Pico GP2 → AIN1'),
    ('B04','IN2','J7.2','j',7,'j7','Pico GP3 → AIN2'),
    ('B05','PWM','J7.3','j',13,'j13','Pico GP8 → 舵机信号'),
    ('B06','3V3','J7.4','a',7,'a7','Pico 3V3 → STBY'),
]
BRIDGE_ROWS={'T+':200,'T-':222,'a':268,'b':290,'c':312,'d':334,'e':356,
             'f':400,'g':422,'h':444,'i':466,'j':488,'B+':520,'B-':542}


def bridge_hole(col,row):
    return 100+(col-1)*22,BRIDGE_ROWS[row]


def bridge_svg():
    s=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 1140" role="img" aria-label="面包板与洞洞板六根公对公跳线连接：J6到电源轨，J7到j6、j7、j13、a7" style="background:#f6f4ee;font-family:Arial,Microsoft YaHei,sans-serif">',
       txt(32,34,'面包板 ↔ 洞洞板 · 六根公对公跳线',24,anchor='start',weight='bold'),
       txt(32,62,'两块板均从元件面看；Pico USB 朝左。下面洞洞板只显示 S～X 行与接线插座。',15,anchor='start'),
       txt(32,86,'旧版诊断图：BSS138 编码器支路已撤回；新接口见 ev3-interface-verification.md。',16,'#a82020',anchor='start',weight='bold'),
       rect(70,170,918,389,'#ebe9e0','#b6b3a7',9),rect(74,367,910,20,'#d0cbbd',radius=1)]
    for row in BRIDGE_ROWS:
        yy=BRIDGE_ROWS[row]
        label={'T+':'上 +','T-':'上 −','B+':'下 +','B-':'下 −'}.get(row,row)
        s.append(txt(60,yy+5,label,12,anchor='end'))
        if row in ('T+','T-','B+','B-'):
            color='#d73d3d' if row.endswith('+') else '#3679b5'
            s.append(f'<path d="M83 {yy-9}H976" fill="none" stroke="{color}" stroke-width="2"/>')
        for c in range(1,41):
            x,y=bridge_hole(c,row)
            s.append(rect(x-3,y-3,6,6,'#777365',radius=1))
    for c in range(1,41):
        x,_=bridge_hole(c,'a')
        s.append(txt(x,250,c,10))
        s.append(txt(x,574,c,10))
    # Pico 与原面包板图使用相同孔位：c3~c22 / h3~h22。
    s.append(rect(134,302,440,152,'#21734b','#224f3b',6))
    s.append(rect(109,351,28,55,'#a6b2b9','#5e6970',3))
    s.append(rect(304,348,60,60,'#1e2830','#172128',3))
    s.append(txt(445,373,'Pico · USB 供电',20,'#fff',weight='bold'))
    s.append(txt(445,397,'不要把 5V 轨接到 3V3',13,'#e2f0e5'))
    for c in range(3,23):
        for row in ('c','h'):
            x,y=bridge_hole(c,row)
            s.append(f'<circle cx="{x}" cy="{y}" r="4.5" fill="#e1c96c"/>')
    for c,row,label in [(5,'c','GND'),(7,'c','3V3'),(6,'h','GP2'),(7,'h','GP3'),(8,'h','GP4'),(9,'h','GP5'),(13,'h','GP8')]:
        x,y=bridge_hole(c,row)
        s.append(txt(x,y+(20 if row=='c' else -12),label,10,'white'))
    lx,ly=bridge_hole(30,'d')
    s.append(rect(lx-11,ly-10,132,108,'#25578e','#163d63',4))
    s.append(txt(lx+55,377,'电平转换',17,'white',weight='bold'))
    s.append(txt(lx+55,399,'上 HV / 下 LV',12,'white'))
    for c,name in zip(range(30,36),('4','3','G','V','2','1')):
        for row in ('d','g'):
            x,y=bridge_hole(c,row)
            s.append(f'<circle cx="{x}" cy="{y}" r="4" fill="#e1c96c"/>')
            s.append(txt(x,y+(17 if row=='d' else -8),name,9,'white'))
    # 保留的板内跳线，使用较细浅色线，与六根板间线区分。
    internal=[((5,'a'),(5,'T-')),((5,'j'),(5,'B-')),((40,'T-'),(40,'B-')),
              ((33,'a'),(33,'T+')),((32,'a'),(32,'T-'))]
    for a,b in internal:
        ax,ay=bridge_hole(*a); bx,by=bridge_hole(*b)
        s.append(f'<path d="M{ax} {ay}L{bx} {by}" fill="none" stroke="#849597" stroke-width="2.5"/>')
    for a,b,bend in [((7,'b'),(33,'j'),170),((8,'i'),(35,'i'),560),((9,'j'),(34,'j'),585)]:
        ax,ay=bridge_hole(*a); bx,by=bridge_hole(*b)
        s.append(f'<path d="M{ax} {ay}Q{(ax+bx)/2} {bend} {bx} {by}" fill="none" stroke="#8c9ba4" stroke-width="2.5"/>')
    s.append(txt(748,600,'细灰线：原有板内跳线继续保留',13))
    # 洞洞板下沿原图裁切，方向、接头位置和孔号直接复用真实装配数据。
    crop=board_svg().split('>',1)[1].rsplit('</svg>',1)[0]
    s.append('<defs><clipPath id="pb-bridge-crop"><rect x="20" y="790" width="1060" height="250"/></clipPath></defs>')
    s.append('<g clip-path="url(#pb-bridge-crop)"><g transform="translate(20 190)">'+crop+'</g></g>')
    s.append(txt(70,750,'洞洞板元件面下沿（S～X 行）',16,anchor='start',weight='bold'))
    routes={
        'B01':lambda a,b:[a,(a[0],140),(1000,140),(1000,690),(b[0],690),b],
        'B02':lambda a,b:[a,(a[0],116),(1040,116),(1040,720),(b[0],720),b],
        'B03':lambda a,b:[a,(a[0],604),(b[0],604),b],
        'B04':lambda a,b:[a,(a[0],636),(b[0],636),b],
        'B05':lambda a,b:[a,(a[0],668),(b[0],668),b],
        'B06':lambda a,b:[a,(a[0],246),(36,246),(36,704),(b[0],704),b],
    }
    labels={'B01':(630,140),'B02':(630,116),'B03':(278,604),
            'B04':(280,636),'B05':(385,668),'B06':(194,704)}
    for ident,net,pin,row,col,label,desc in BRIDGE:
        a=bridge_hole(col,row); px,py=xy(PINS[pin][0]); b=(20+px,760+py-570)
        pts=routes[ident](a,b)
        path='M'+' L'.join(f'{x} {y}' for x,y in pts)
        color=COLORS[net]
        s.append(f'<g data-bridge="{ident}"><title>{ident} {pin} ↔ {label}：{escape(desc)}</title>')
        s.append(f'<path d="{path}" fill="none" stroke="#f6f4ee" stroke-width="8" stroke-linejoin="round"/>')
        s.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="4" stroke-linejoin="round"/>')
        tx,ty=labels[ident]
        s.append(rect(tx-62,ty-12,124,24,'#fffdf6',color,4))
        s.append(txt(tx,ty+5,ident+' '+net,13,color,weight='bold'))
        for ex,ey in (a,b):
            s.append(rect(ex-5,ey-7,10,14,'#202c34','#5b6469',2))
            s.append(f'<circle cx="{ex}" cy="{ey}" r="2.5" fill="{color}"/>')
        s.append('</g>')
    s.append(txt(32,1070,'线材：公—公杜邦跳线。洞洞板端插 J6 / J7 排母，面包板端直接插孔；均可拔下。',16,anchor='start'))
    s.append(txt(32,1100,'9V、马达线与舵机供电留在洞洞板。先接公共地；断开 9V 和 USB 后再插拔。',15,anchor='start'))
    s.append('</svg>')
    return ''.join(s)


def bridge_rows():
    return [(ident,pin+' / '+hole(PINS[pin][0]),label,desc) for ident,net,pin,row,col,label,desc in BRIDGE]


# EV3 线色按常见配色画，实际接线先以脚号与通断确认。
LOADS = [
    ('E1','EV3 1脚','白 / M1','J4.1','AO1 → 马达端1'),
    ('E2','EV3 2脚','黑 / M2','J4.2','AO2 → 马达端2'),
    ('E3','EV3 3脚','红 / GND','T-37','面包板上排 − 第37孔'),
    ('E4','EV3 4脚','绿 / 5V','T+36','面包板上排 + 第36孔'),
    ('E5','EV3 5脚','黄 / A相','b35','电平转换 HV1 → LV1 → GP4'),
    ('E6','EV3 6脚','蓝 / B相','b34','电平转换 HV2 → LV2 → GP5'),
    ('S1','舵机 GND','棕 / GND','J5.1','地；洞洞板 V23'),
    ('S2','舵机 V+','红 / 5V','J5.2','5V；洞洞板 V24'),
    ('S3','舵机 SIG','黄 / SIG','J5.3','GP8 信号；洞洞板 V25'),
]


def loads_svg():
    s=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1300 1640" role="img" aria-label="单臂完整实物连线图，包含面包板、洞洞板、EV3马达六芯线和舵机三芯线" style="background:#f6f4ee;font-family:Arial,Microsoft YaHei,sans-serif">']
    base=bridge_svg().split('>',1)[1].rsplit('</svg>',1)[0]
    base=base.replace('面包板 ↔ 洞洞板 · 六根公对公跳线','单臂完整接线 · 面包板、洞洞板、马达、舵机')
    base=base.replace(txt(32,1070,'线材：公—公杜邦跳线。洞洞板端插 J6 / J7 排母，面包板端直接插孔；均可拔下。',16,anchor='start'),'')
    base=base.replace(txt(32,1100,'9V、马达线与舵机供电留在洞洞板。先接公共地；断开 9V 和 USB 后再插拔。',15,anchor='start'),'')
    s.append(base)
    # EV3 实物外形示意，六芯线先剪开／经转接板引出；不是6个互相连通的接点。
    s += [rect(62,1360,327,151,'#c6cbd0','#666e78',18),
          rect(70,1370,98,130,'#f1f2ef','#b2b7b8',14),
          rect(105,1400,26,70,'#9aa2a7','#788288',4),
          rect(297,1377,93,112,'#e1e2de','#8c9297',9),
          '<circle cx="379" cy="1435" r="49" fill="#bb3028" stroke="#842720" stroke-width="4"/>',
          '<circle cx="379" cy="1435" r="25" fill="#6f7477" stroke="#deddd7" stroke-width="6"/>',
          '<path d="M367 1435h24 M379 1423v24" stroke="#242c31" stroke-width="8"/>',
          txt(212,1440,'EV3 马达',23,weight='bold'),
          txt(212,1466,'大 / 中马达接法相同',13),
          rect(108,1283,212,21,'#444a51',radius=7),
          '<path d="M315 1293Q363 1293 354 1360" fill="none" stroke="#444a51" stroke-width="18"/>',
          txt(214,1325,'EV3 六芯线拆线 / 转接板',16),
          txt(214,1345,'灰色条表示线缆外皮，不是导电连接',12)]
    # Geekservo 与自带线，母插头位于 J5，上方插座保持可拔。
    s += [rect(813,1360,190,136,'#9aa2aa','#626a75',7),
          rect(796,1375,224,23,'#aeb4ba','#717985',3),
          rect(796,1450,224,23,'#aeb4ba','#717985',3),
          '<circle cx="809" cy="1387" r="5" fill="#414c56"/><circle cx="1007" cy="1387" r="5" fill="#414c56"/>',
          '<circle cx="809" cy="1462" r="5" fill="#414c56"/><circle cx="1007" cy="1462" r="5" fill="#414c56"/>',
          '<circle cx="963" cy="1408" r="23" fill="#e3e6e6" stroke="#505964" stroke-width="3"/>',
          '<path d="M951 1408h24 M963 1396v24" stroke="#555e67" stroke-width="7"/>',
          txt(892,1435,'Geekservo',18,weight='bold'),txt(906,1530,'灰色 270° 舵机',16),
          txt(32,1571,'EV3 的红线是地线；线色仅作常见配色参考，先核对脚号。编码器信号必须经过电平转换。',16,anchor='start'),
          txt(32,1604,'舵机三孔母头插 J5：1=棕 GND，2=红 5V，3=黄 SIG。马达与舵机的大电流供电不经过面包板。',16,anchor='start')]
    def port(name):
        x,y=xy(PINS[name][0]);return x+20,y+190
    dest={
        'E1':port('J4.1'),'E2':port('J4.2'),
        'E3':bridge_hole(37,'T-'),'E4':bridge_hole(36,'T+'),
        'E5':bridge_hole(35,'b'),'E6':bridge_hole(34,'b'),
        'S1':port('J5.1'),'S2':port('J5.2'),'S3':port('J5.3'),
    }
    paths={
        'E1':[(140,1293),(140,1080),(dest['E1'][0],1080),dest['E1']],
        'E2':[(170,1293),(170,1110),(dest['E2'][0],1110),dest['E2']],
        'E3':[(200,1293),(200,1140),(1140,1140),(1140,174),(dest['E3'][0],174),dest['E3']],
        'E4':[(230,1293),(230,1170),(1170,1170),(1170,154),(dest['E4'][0],154),dest['E4']],
        'E5':[(260,1293),(260,1200),(1200,1200),(1200,254),(dest['E5'][0],254),dest['E5']],
        'E6':[(290,1293),(290,1230),(1230,1230),(1230,276),(dest['E6'][0],276),dest['E6']],
        'S1':[dest['S1'],(dest['S1'][0],1090),(700,1090),(700,1400),(813,1400)],
        'S2':[dest['S2'],(dest['S2'][0],1110),(725,1110),(725,1420),(813,1420)],
        'S3':[dest['S3'],(dest['S3'][0],1130),(750,1130),(750,1440),(813,1440)],
    }
    colors={'E1':'#f5f5f2','E2':'#252c33','E3':'#cf3836','E4':'#228e51','E5':'#c79708','E6':'#287dc3',
            'S1':'#80502d','S2':'#cf3836','S3':'#c79708'}
    labels={'E1':(140,1050),'E2':(238,1110),'E3':(458,1140),'E4':(458,1170),
            'E5':(458,1200),'E6':(458,1230),'S1':(700,1270),'S2':(725,1302),'S3':(750,1334)}
    names={'E1':'E1 M1','E2':'E2 M2','E3':'E3 GND 红','E4':'E4 5V 绿','E5':'E5 A 黄','E6':'E6 B 蓝',
           'S1':'S1 GND 棕','S2':'S2 5V 红','S3':'S3 SIG 黄'}
    # 画出插到 J5 公排针上的三孔母头。
    px,py=port('J5.1')
    s.append(rect(px-12,py-12,80,26,'#202b32','#59646c',3))
    s.append(txt(px+28,py-22,'舵机三孔母头 ↓ J5',14,weight='bold'))
    for ident,pts in paths.items():
        path='M'+' L'.join(f'{x} {y}' for x,y in pts)
        s.append(f'<g data-load="{ident}"><title>{names[ident]}</title>')
        s.append(f'<path d="{path}" fill="none" stroke="{chr(35)}747e86" stroke-width="8" stroke-linejoin="round"/>' if ident=='E1' else f'<path d="{path}" fill="none" stroke="#f6f4ee" stroke-width="8" stroke-linejoin="round"/>')
        s.append(f'<path d="{path}" fill="none" stroke="{colors[ident]}" stroke-width="4.5" stroke-linejoin="round"/>')
        tx,ty=labels[ident]; lc='#3e4750' if ident=='E1' else colors[ident]
        s.append(rect(tx-51,ty-12,102,24,'#fffdf6',lc,4))
        s.append(txt(tx,ty+5,names[ident],13,lc,weight='bold'))
        ex,ey=dest[ident]
        s.append(f'<circle cx="{ex}" cy="{ey}" r="5" fill="{colors[ident]}" stroke="#354a59"/>')
        s.append('</g>')
    return ''.join(s)+'</svg>'


def load_rows():
    return [(ident,source,color,target+' / '+hole(PINS[target][0]) if target in PINS else target,desc)
            for ident,source,color,target,desc in LOADS]


STYLE = '''
.pb-controls{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}
.pb-controls button,.pb-wire-button{font:inherit;cursor:pointer;border:1px solid #b7c3c8;border-radius:6px;padding:7px 12px;background:var(--sheet,#fff);color:var(--ink,#172c38)}
.pb-controls button[aria-pressed="true"]{background:#245e79;color:#fff;border-color:#245e79}
.pb-controls button:focus-visible,.pb-wire-button:focus-visible{outline:3px solid #cc8d18;outline-offset:2px}
.pb-view[hidden]{display:none}.pb-view .scroll{padding:0;background:#f6f4ee}
.pb-view svg{display:block;width:100%;min-width:760px;height:auto}.pb-view.pb-zoom svg{width:150%;min-width:1100px}
.pb-wire{transition:opacity .15s}.pb-focus .pb-wire{opacity:.1}.pb-focus .pb-wire.pb-active{opacity:1}
.pb-current{padding:12px 16px;border-left:4px solid #d58c26;background:var(--panel,#faf8f1);font-weight:600}
.pb-legend{display:flex;gap:16px;flex-wrap:wrap}.pb-legend span{white-space:nowrap}
.pb-legend i{display:inline-block;width:22px;height:5px;margin-right:6px;vertical-align:middle}
.pb-wire-button{font-family:monospace;font-weight:bold;padding:4px 8px}
@media print{.pb-controls,.pb-current,.pb-downloads{display:none!important}.pb-view[hidden]{display:block!important}.pb-view{break-before:page}.pb-view svg{width:100%!important;min-width:0!important}.pb-wire{opacity:1!important}}
'''

JS = '''
(function(){
const root=document.getElementById('perfboard');
if(!root)return;
const views=root.querySelectorAll('.pb-view');
function show(name){views.forEach(v=>v.hidden=v.dataset.view!==name);root.querySelectorAll('[data-face]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.face===name)));}
function select(id){
const back=root.querySelector('[data-view="back"]');
back.classList.toggle('pb-focus',!!id);
back.querySelectorAll('.pb-wire').forEach(w=>w.classList.toggle('pb-active',w.dataset.wire===id));
const row=id?root.querySelector('[data-row="'+id+'"]'):null;
root.querySelector('.pb-current').textContent=row?row.dataset.description:'背面全部 14 根线；底座先焊好；导线只焊首尾，中途跨线不相连。';
if(id){show('back');back.scrollIntoView({block:'start',behavior:'instant'});}
}
root.querySelectorAll('[data-face]').forEach(b=>b.addEventListener('click',()=>show(b.dataset.face)));
root.querySelectorAll('[data-select-wire]').forEach(b=>b.addEventListener('click',()=>select(b.dataset.selectWire)));
root.querySelector('[data-zoom]').addEventListener('click',function(){const on=this.getAttribute('aria-pressed')!=='true';this.setAttribute('aria-pressed',String(on));views.forEach(v=>v.classList.toggle('pb-zoom',on));});
root.querySelector('[data-all-wires]').addEventListener('click',()=>{show('back');select(null);});
if(location.hash==='#bridge')show('bridge');
if(location.hash==='#loads')show('loads');
})();
'''


def assembly_rows():
    rows=[]
    for ref, label, pins, names, edge in TERMINALS:
        rows.append((ref, '5.08mm 插拔端子，'+str(len(pins))+' 位（底座+插头）', '；'.join(f'{i}={hole(p)} ({n})' for i,(p,n) in enumerate(zip(pins,names),1)), '进线口朝'+('上' if edge=='top' else '下')+'板边'))
    rows += [('J2 / J3','U2 四角电源排母（4 个分立 1 针座）','J2.1=I16 IN+；J2.2=O16 IN−；J3.1=I31 OUT+；J3.2=O31 OUT−','横向 15 孔距，纵向 6 孔距；排母单触点额定电流需满足负载'),
             ('U2','DSN5000 / XL4005 模块 + 四根向下排针','四角插入 I16、O16、I31、O31','电感、电位器朝上；图中模块机械尺寸是明确假设'),
             ('U1','用户 DRV8833 + 两排 1×8 排母','左 I9～P9；右 I13～P13','左上 VM、右上 NC；排距暂按10.16mm，单触点额定电流满足负载'),
             ('J5','2.54mm 1×3 公排针','1=V23 GND；2=V24 +5V；3=V25 SIG','配舵机三孔母头，先核对线序'),
             ('J6','2.54mm 1×2 排母','1=V15 +5V；2=V16 GND','配面包板公头引线，仅小电流支路'),
             ('J7','2.54mm 1×4 排母','1=V9；2=V10；3=V11；4=V12','配Pico公头线，1/2/3/4接GP2/GP3/GP8/3V3')]
    return rows


def table(headers,rows):
    return '<div class="tbl"><table><thead><tr>'+''.join('<th>'+escape(h)+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+escape(str(cell))+'</td>' for cell in row)+'</tr>' for row in rows)+'</tbody></table></div>'


def section():
    views=[]
    for name,title,svg in [('front','01 · 照孔位插元件',board_svg()),('back','02 · 翻面逐根焊线',board_svg(True)),('external','03 · 板外电源与模块拔插方式',harness_svg()),('bridge','04 · 面包板与洞洞板实际连线',bridge_svg()),('loads','05 · 舵机与马达完整连线',loads_svg())]:
        # 内联 SVG 的 ID 属于整页；隐藏视图不能与当前视图共用裁剪标识。
        for resource in ('pb-metal', 'pb-bridge-crop'):
            svg = svg.replace(resource, name + '-' + resource)
        views.append(f'<div class="pb-view" data-view="{name}"'+(' hidden' if name!='front' else '')+f'><h3>{title}</h3><div class="scroll">{svg}</div></div>')
    rows=[]
    for w in WIRES:
        ident,net,a,b,_,desc=w
        start,end=hole(PINS[a][0]),hole(PINS[b][0])
        via=' → '.join(hole(p) for p in w[4]) or '直达'
        detail=f'{ident}：{a} / {start} → {b} / {end}。{desc}；中途只走线，不焊接。'
        rows.append(f'<tr data-row="{ident}" data-description="{escape(detail,quote=True)}"><td><button type="button" class="pb-wire-button" data-select-wire="{ident}" aria-label="在焊接图中突出显示 {ident}">{ident}</button></td><td>{escape(a)}<br><b>{start}</b></td><td>{escape(b)}<br><b>{end}</b></td><td>{via}</td><td>{escape(desc)}</td></tr>')
    legend=''.join(f'<span><i style="background:{COLORS[k]}"></i>{label}</span>' for k,label in [('9V','9V'),('5V','5V'),('GND','GND'),('M1','马达'),('IN1','IN1'),('IN2','IN2'),('PWM','舵机 PWM'),('3V3','STBY / 3.3V')])
    pinrows=[(chr(64+r),f'{hole((9,r))} = {LEFT[r-9]}',f'{hole((13,r))} = {RIGHT[r-9]}') for r in range(9,17)]
    return f'''<section id="perfboard">
<style>{STYLE}</style>
<h2>洞洞板实物装配与焊接图</h2>
<div class="warn"><b>2026-09-27：编码器接口复核未通过。</b>④⑤ 中的 BSS138/HV/LV 接线只留作旧版诊断参考，不是可继续安装的编码器方案。供电和马达端子分工保留；新接口使用 SN74LVC2G17，实际模块孔位待确认。见<a href="../ev3-interface-verification.md">接口复核报告</a>。</div>
<p>按这版孔位插元件，再左右翻板照背面焊 14 根线。列 1～32、行 A～X，孔距 2.54mm；选至少有这块完整孔阵的独立焊盘洞洞板，约 90 × 70mm。先给 A1 旁边做红色标记。</p>
<div class="warn"><b>全部可拆换：</b>洞洞板只焊底座和配线，模块均可拔。选用5.08mm 插拔式端子（配套直针底座＋可拔螺钉插头）、2.54mm 排针、DRV8833 按你提供的实物丝印（左上 VM、右上 NC）安装，两排 8 针，机械排距暂按 10.16mm。你的模块若外形或脚序不同，先指出差异再改图，不能把同名芯片的其他模块直接插进这些孔。U2 按 XL4005 四角电源孔 <b>38.1 × 15.24mm</b> 这一机械假设画；这不是所有 XL4005 的统一尺寸。两块模块均插排母，无螺钉或支柱；不另装电容。</div>
<div class="pb-controls" role="group" aria-label="选择装配视图">
<button type="button" data-face="front" aria-pressed="true">① 元件面</button><button type="button" data-face="back" aria-pressed="false">② 镜像焊接面</button><button type="button" data-face="external" aria-pressed="false">③ 电源与拔插结构</button><button type="button" data-face="bridge" aria-pressed="false">④ 面包板连接</button><button type="button" data-face="loads" aria-pressed="false">⑤ 舵机与马达</button><button type="button" data-zoom aria-pressed="false">放大 150%</button><button type="button" data-all-wires>显示全部焊线</button></div>
<div class="pb-legend">{legend}</div>
{''.join(views)}
<p class="pb-current" aria-live="polite">背面全部 14 根线；底座先焊好；导线只焊首尾，中途跨线不相连。</p>
<p class="pb-downloads">下载可放大的矢量图：<a href="perfboard-front.svg" download>元件面 SVG</a> · <a href="perfboard-back.svg" download>焊接面 SVG</a> · <a href="perfboard-external.svg" download>板外接线 SVG</a> · <a href="perfboard-bridge.svg" download>两板连接 SVG</a> · <a href="perfboard-loads.svg" download>舵机与马达全图 SVG</a>。图已放大供阅读，打印不能当 1:1 钻孔模板。</p>
<h3>两板之间的 6 根公对公线</h3>
{table(["线号","洞洞板接口 / 孔位","面包板孔位","用途"],bridge_rows())}
<p>3.3V 线使用 a7；原有 b7 → 电平转换 LV 跳线继续保留。a7、b7、c7 同组相通。电源轨按原指南检查中间断口并补跨线。</p>
<h3>舵机与 EV3 马达的 9 根线</h3>
{table(["线号","设备线端","常见颜色 / 功能","接入点 / 孔位","去向"],load_rows())}
<p>EV3 线 1/2 脚接 J4 可拔端子；3/4/5/6 脚用公头转接线插面包板。舵机自带三孔母头插 J5，按棕 GND / 红 5V / 黄 SIG 核对顺序。EV3 红线是地线，不能当成电源正极。</p>
<h3>安装表：先焊连接器底座，再插入模块</h3>
{table(['编号','器件','插入孔位','朝向'],assembly_rows())}
<h3>焊线表：点击线号，在背面图中单独看这一根</h3>
<p>所有线都用绝缘导线，只剥首尾约 2～3mm 焊在指定孔。表中“途经”是走线转弯位置，不是焊点；交叉处保留绝缘，一根从另一根上方跨过。配电端子同一焊脚接两根线时先合并固定，不能只依赖薄焊盘受力。</p>
<div class="tbl"><table><thead><tr><th>线号</th><th>起点 / 孔位</th><th>终点 / 孔位</th><th>途经（不焊）</th><th>用途</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<h3>DRV8833 方向核对：按你提供的左右脚序</h3>
{table(['行','左排（第 9 列）','右排（第 13 列）'],pinrows)}
<p>脚序按你提供的实物丝印：VM 接 9V，AO1/AO2 接马达；AIN1/AIN2 接 GP2/GP3；STBY 经 J7.4 接 Pico 3V3。NC 留空，未用 B 路输出留空；不另装电容，模块自带电容保留。机械排距仍是绘图假设，焊排母前用实物对齐。</p>
<h3>焊接顺序与检查</h3>
<ol><li>先只焊 J1/J4 端子底座、J5 排针、J6/J7 排母、U1 两排排母和 U2 四角排母；DRV8833 先不插。核对 A1、各接口正负和两排间距。</li><li>按 W01～W14 焊接绝缘导线。断电测各线首尾导通；DRV8833 和降压都拔下时，9V、5V、地和各信号网络之间不能短路。</li><li>先只插 U2 降压模块，按“电源与拔插结构”接 9V，空载调到 5.0V。确认 J5.2、J6.1 对各自 GND 约 5V，再断电放电。</li><li>插入 DRV8833，接 J6、J7 和编码器，Pico 仍用 USB。先按<a href="../single_arm.md#5-测试步骤">单臂步骤</a>测马达，再断电接舵机测试。</li><li>大电流导线和接点按实际启动电流选型；带载检查压降、温升与 VM 瞬态，DRV8833 工作电压不超过 10.8V。用绝缘底板保护焊接面，线束留松弛并固定，插拔时扶住底座。</li></ol>
<p>接面包板：J6.1 → 上排 +，J6.2 → 上排 −；J7.1 → j6（GP2），J7.2 → j7（GP3），J7.3 → j13（GP8），J7.4 → a7（3V3）。编码器与电平转换跳线保持原接法。完整说明见<a href="../perfboard.md">洞洞板设计文档</a>。</p>
<script>{JS}</script>
</section>'''


def document():
    def mdtable(heads, rows):
        return '\n'.join(['| ' + ' | '.join(heads) + ' |', '| ' + ' | '.join('---' for _ in heads) + ' |'] + ['| ' + ' | '.join(str(c) for c in row) + ' |' for row in rows])
    wire_rows = [(w[0], f'{w[2]} / {hole(PINS[w[2]][0])}', f'{w[3]} / {hole(PINS[w[3]][0])}', ' → '.join(hole(p) for p in w[4]) or '直达', w[5]) for w in WIRES]
    return '''# 单臂洞洞板：可拔插的逐孔安装与焊接图

> **2026-09-27：原 BSS138 编码器支路撤回。** 以下 HV/LV 图及孔位表保留作旧版诊断参考，不再用于安装编码器接口；电源、马达和舵机分工保留。修订采用 SN74LVC2G17，实际模块孔位待确认，见 [接口复核报告](ev3-interface-verification.md)。

打开 [实物装配页面](wiring/perfboard.html)：可以切换**元件面、镜像焊接面、电源与拔插结构、面包板连接、舵机与马达**，点击 W01～W14 单独查看一根线，还可下载五张 SVG 矢量图。

本文件和图纸由 `docs/wiring/perfboard_layout.py` 的同一份孔位数据生成，运行 `python3 docs/wiring/build.py` 更新。

## 1. 本版确定的结构

- **模块全部可拔插。** 洞洞板上只焊插拔端子底座、排母、J5 排针和配线。DRV8833 和降压模块焊上排针后插入排母，不焊死在洞洞板上。
- **不用螺钉和支柱安装降压模块。** 四角针脚插入四个排母座，外部线束留松弛并固定，插拔时扶住底座。
- **不另装电容。** 模块原有的去耦／滤波电容保留。是否需要增加储能电容，留待实物供电与运行情况决定，本版没有外接电容或电容插座。
- J1、J4 使用 **5.08mm 插拔式接线端子**，由板上直针底座和可整块拔出的螺钉插头组成；不是必须逐根拧螺钉才能拆下的固定式端子。
- Pico 与电平转换仍放在面包板，Pico 由 USB 供电；J6 只给编码器、电平转换及公共地连接供电，不接 Pico 的 VBUS、VSYS、3V3。

## 2. 图纸基准与朝向

**孔阵：32 列 × 24 行，2.54mm 孔距。** 选至少有这块完整孔阵的独立焊盘洞洞板（约 90 × 70mm），从选定的左上第一孔开始标 A1。列号向右增加，行号 A～X 向下增加。端子孔距 5.08mm，即隔一个孔装一脚。

**U1：用户手上的 DRV8833，脚序已由用户确认。** 左侧自上而下为 `VM、NC、GND、AO1、AO2、BO2、BO1、GND`；右侧为 `NC、AIN2、AIN1、STBY、BIN1、BIN2、NC、GND`。按这个朝向放置，左上 VM、右上 NC；不再套用其他厂商的脚序。两排各 8 针，针距按 2.54mm，机械排距暂按 **10.16mm（4 个孔距）** 绘制；焊接前用实物模块对齐排母，如排距不同再调整。模块下面的针座要留出元件空间，不能让焊点或器件碰到洞洞板。

**U2：DSN5000 / XL4005。** 外形按约 44 × 22mm 的模块绘制，电感、电位器朝上；四角电源焊孔假定横向相距 **38.1mm（15 个孔距）**、纵向相距 **15.24mm（6 个孔距）**，各焊一根向下的排针。此孔距是本版明确选定的机械假设，并非 XL4005 统一标准。若实物焊孔不匹配，只调整四个排母位置及相应焊线；不要硬掰模块插入。电路外形图中的芯片、电感等仅用于辨认，焊孔和电源标注才是接线依据。

把红三角标在 A1 附近。看背面时像翻书一样**左右翻板，A 行仍在上方**：红三角到了右上角，列号从左往右为 32～1。孔名不变，例如正面的 C3，在背面仍叫 C3，不能重新从左边数第 3 孔。

## 3. 元件插入孔位

''' + mdtable(['编号', '器件', '孔位', '朝向／连接'], assembly_rows()) + '''

J2/J3 是降压模块的四个针座编号，不再是接往板外降压模块的接线端子。J2 为输入侧，J3 为输出侧。

## 4. 背面逐根焊线

每根线只在起点、终点焊接；中间途经孔仅指示绝缘导线的走向，不剥皮、不焊接。交叉位置保留绝缘，其中一根从另一根上方跨过。底座的所有针脚先焊在各自独立焊盘上，图中彩线端头带彩色中心的银色圆是导线焊点；未接线的针脚只作底座固定，不与其他孔连锡。

''' + mdtable(['线号', '起点／孔', '终点／孔', '途经（不焊）', '用途'], wire_rows) + '''

W01～W04 是电源入口分支；W05～W08 是降压输出分支；W09～W10 是电机输出；W11～W13 是控制信号，W14 是 STBY 的 3.3V 使能线。两条马达输出都不能接 GND 或 9V。

## 5. 面包板与洞洞板连接

见 [两板实际连线图](wiring/perfboard-bridge.svg)，或在装配页面选择“④ 面包板连接”。六根线均为公对公跳线，板上接口 J6/J7 是排母。

''' + mdtable(['线号', '洞洞板接口／孔位', '面包板孔位', '用途'], bridge_rows()) + '''

a7、b7、c7 是同一列上半侧的连通组，c7 是 Pico 3V3。b7 已有到电平转换 LV 的跳线，所以 STBY 的 3.3V 线使用 a7，不往 b7 再塞一根。面包板原有板内跳线和编码器连线保留；上下地轨与电源轨中间断口按原图连接。

### 舵机与马达完整接线

见 [完整实物连线图](wiring/perfboard-loads.svg)，或选择“⑤ 舵机与马达”。图中保留两块板之间的六根线，同时补上 EV3 六芯线与舵机三芯线。

''' + mdtable(['线号', '设备线端', '常见颜色／功能', '接入点／孔位', '去向'], load_rows()) + '''

EV3 线色只作常见配色参考，必须先确认脚号；红色对应编码器地，不是正极。编码器 A/B 经 HV1/HV2 转换到 LV1/LV2，再去 GP4/GP5，不能直接把 5V 信号接 Pico。面包板上排 +36、−37 和 b35、b34 均为预留接线孔。

马达两根驱动线接 J4 的可拔端子；四根编码器线经公头转接线插面包板。舵机自带三孔母头直接插 J5 公排针，1=棕 GND、2=红 5V、3=黄 SIG，先核对线序后再插。裸线需使用合适的压接／转接连接，不能将多股散线直接塞进面包板。

### 其他板外插线

- DC-005 插座中心针对应的焊脚（确认供电为中心正极）→ 线式保险丝 F1 → 直流开关 SW1 → J1.1；插座负极 → J1.2。插座型号为用户已有的 DC-005、5.5 × 2.1mm；中心针接电源正极，外套接负极，第三个切换脚留空并绝缘。断电插入一个未供电的 DC 插头，用万用表找出与中心、外套相通的焊脚，不能凭通用编号猜针脚。不同 DC-005 版本有差异，孔距不按 2.54mm 强插。插座引出短线到可拔 J1 插头，本体固定在绝缘底板或机架上，整套可拆换，不焊死在主洞洞板上。保险丝及开关在板外线束上，不占洞洞板孔位。
- J4.1 / J4.2 → EV3 线 1 / 2 脚（马达两端）。
- J5.1 / J5.2 / J5.3 → 舵机 GND / +5V / 信号；按舵机实际线序制作可拔转接线。
- J6.1 / J6.2 → 面包板上排 + / − 电源轨。
- J7.1 → j6（GP2）；J7.2 → j7（GP3）；J7.3 → j13（GP8）；J7.4 → a7（Pico 3V3，物理36脚）。公头排针线插入板上 J7 排母。
- EV3 线 3、4 脚仍接面包板 GND、5V；5、6 脚经电平转换接 GP4、GP5，详见 [单臂接线](single_arm.md)。

STBY 经 W14 接 Pico 3V3，不接 9V。NC 保持悬空，B 路输出留空。驱动电源、信号和电机均按本页用户确认的脚序连接。

## 6. 排针、配线与验收

1. 接口匹配：线端公针配板上排母（J6/J7），线端母孔配板上公排针（J5）；模块公排针配 U1/U2 排母。先焊连接器底座，模块都先拔下。两排 U1 排母可借助尚未通电的模块对齐后点焊定位，再拔下模块完成焊接。U2 四角排母同样先按实物孔距定位。
2. 电源排针／排母的**单触点额定电流**必须覆盖该支路实际负载。不要用无规格、松动的杜邦插头承载舵机总电流；额定不足就换合适的连接器，模块仍保持可拆换。DSN5000 标称“5A”不代表当前散热条件下能持续输出 5A。
3. 单臂短线的主电源可从 0.5～0.75mm² 铜线评估，马达／舵机分支可从 0.3～0.5mm² 评估，最终按电流、压降、温升及端子允许线径确认。电源不通过普通细排线；配电不靠长串锡桥。螺钉插头按其规格压接线端，跨线全程绝缘。
4. 按 W01～W14 逐根焊线，断开 9V、USB，拔下模块，用万用表核对每根线首尾导通，以及不同网络之间无短路。图中铜焊盘彼此独立，不等同于面包板内部连通。
5. 确认 U2 的 IN− 与 OUT− 为公共地，再只插 U2，空载调到 5.0V，检查 J5.2、J6.1 对各自地约为 5V。调压后断电，等待模块自带电容放电。
6. 插 U1、接控制线及编码器，Pico 用 USB。先测马达，再断电接舵机，按 [单臂测试](single_arm.md#5-测试步骤) 操作。每次插拔或改线都断开 9V 和 USB。
7. 运行时检查驱动、降压、针座和导线的温升、压降及接触稳定性。DRV8833 工作电压不超过 10.8V；电机刹车回灌可能造成瞬态上升，普通万用表不一定能捕捉。本版不增加电容，不等于已验证所有负载下供电都稳定。
8. 板底加绝缘底板，避免裸焊点接触导电物；线束固定在底板或机架上，插拔时扶住连接器，不能用模块针脚承受拉线的力。

DRV8833 与降压模块的地各自回电源入口；舵机和面包板分别回降压输出地。GND 通过非隔离降压模块的 IN− / OUT− 相通，无需再让电机／舵机电流经过面包板。

## 7. 四臂扩展

本图只供单臂装配。四臂阶段增加一块 DRV8833、马达及舵机接口，重新核算同时启动电流、供电针座额定值、总线线径与散热，并按 [四臂 GPIO 表](single_arm.md#2-引脚分配) 接线；不能把当前单臂针座直接当成足够的整机供电接口。
'''


def validate():
    """检查物理孔位和裸板网络，避免镜像/引脚/线路表不一致。"""
    coords=[pos for pos,_ in PINS.values()]
    assert len(coords)==len(set(coords)), '元件针脚占用同一孔'
    for pos in coords:
        assert 1 <= pos[0] <= COLS and 1 <= pos[1] <= ROWS
        assert xy(pos)[0]+xy(pos,True)[0] == 2*OX+(COLS-1)*PITCH
        assert xy(pos)[1]==xy(pos,True)[1]
    graph={p:set() for p in PINS}
    for w in WIRES:
        assert w[2] in graph and w[3] in graph
        graph[w[2]].add(w[3]);graph[w[3]].add(w[2])
        for p in points(w):
            assert 1 <= p[0] <= COLS and 1 <= p[1] <= ROWS
        for p,q in zip(points(w),points(w)[1:]):
            assert p[0]==q[0] or p[1]==q[1], w[0]
    expected=[{'J1.1','J2.1','U1.VM'}, {'J1.2','J2.2','U1.GND_9_16'},
              {'J3.1','J5.2','J6.1'}, {'J3.2','J5.1','J6.2'},
              {'U1.AO1','J4.1'}, {'U1.AO2','J4.2'},
              {'J7.1','U1.AIN1'}, {'J7.2','U1.AIN2'}, {'J7.3','J5.3'}, {'J7.4','U1.STBY'}]
    actual=[];seen=set()
    for p in graph:
        if p in seen or not graph[p]:continue
        todo=[p];group=set()
        while todo:
            q=todo.pop()
            if q in group:continue
            group.add(q);todo.extend(graph[q]-group)
        seen|=group;actual.append(group)
    assert {frozenset(g) for g in actual}=={frozenset(g) for g in expected}, '裸板网络错误'
    assert graph['J7.4'] == {'U1.STBY'}
    assert all(not graph[key] for key, (_, label) in PINS.items() if label == 'NC')
    return f'{len(PINS)} 个独立针脚、{len(WIRES)} 根导线：孔位、镜像、裸板网络检查通过'


def write_assets(directory):
    validate()
    for name,svg in [('front',board_svg()),('back',board_svg(True)),('external',harness_svg()),('bridge',bridge_svg()),('loads',loads_svg())]:
        (Path(directory)/f'perfboard-{name}.svg').write_text(svg,encoding='utf-8')
    (Path(directory)/'perfboard-section.html').write_text(section(),encoding='utf-8')
    (Path(directory).parent/'perfboard.md').write_text(document(),encoding='utf-8')


if __name__=='__main__':
    print(validate())
    write_assets(Path(__file__).parent)
