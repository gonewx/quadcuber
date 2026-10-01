"""生成夹指轴向分层图；与 model.py 的实际零件位置核对后用于搭建说明书。"""
from pathlib import Path
from html import escape

OUT = Path(__file__).resolve().parents[3] / 'docs/lego/v3/img/jaw_layers.svg'
COLORS = {'连杆': '#efcb47', '接头': '#7b8797', '红梁': '#e65a57', '蓝梁': '#4d83d1', '夹块': '#edab47',
          '半套': '#b6c2cf', '整套': '#93a3b5', '座梁': '#d5dce4', '横梁': '#d5dce4', '薄梁': '#d5dce4', '支架': '#d5dce4'}


def main():
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="1524" viewBox="0 0 1500 1524">',
           '<rect width="1500" height="1524" fill="#f8fafc"/>',
           '<style>text{font-family:"Noto Sans CJK SC","Noto Sans SC",sans-serif;fill:#203046}.title{font-size:30px;font-weight:700}.sub{font-size:20px}.small{font-size:16px}</style>',
           '<text x="50" y="52" class="title">平行夹块 · 六根轴的装配截面</text>',
           '<text x="50" y="88" class="sub">前端轴齐平；主轴固定在横梁十字孔中。轴套贴合但不要挤紧活动梁。</text>']
    rows = [
        ('A　主摆臂根轴 · 7 号轴 44294', 70,
         [(-70,-60,'薄梁'),(-60,-50,'薄梁'),(-50,-30,'座梁'),(-30,-10,'整套'),(-10,10,'红梁'),
          (10,30,'整套'),(30,50,'座梁'),(50,60,'薄梁'),(60,70,'薄梁')],
         '红梁圆孔转动；外侧双薄横梁的十字孔固定轴。座梁为 3 孔梁，双薄横梁为 32449。'),
        ('B　从动臂根轴 · 10 号轴 3737', 100,
         [(-100,-90,'半套'),(-90,-70,'支架'),(-70,-50,'整套'),(-50,-30,'整套'),(-30,-20,'蓝梁'),(-20,-10,'半套'),(-10,10,'整套'),
          (10,20,'半套'),(20,30,'蓝梁'),(30,50,'整套'),(50,70,'整套'),(70,90,'支架'),(90,100,'半套')],
         '蓝梁十字孔固定轴；轴在 11 孔支架的圆孔中转动。'),
        ('C　主臂—夹块前轴 · 2 号轴 32062', 20,
         [(-20,-10,'夹块'),(-10,10,'红梁'),(10,20,'夹块')],
         '两片 L 梁靠魔方一端的十字孔固定轴；中央粗红梁前端圆孔绕轴转。无外侧轴套。'),
        ('D　从动臂—夹块轴 · 3 号轴 4519', 30,
         [(-30,-20,'蓝梁'),(-20,-10,'夹块'),(-10,10,'整套'),(10,20,'夹块'),(20,30,'蓝梁')],
         '蓝梁前端十字孔固定轴；两片 L 梁朝外一边的中间圆孔绕轴转。无外侧轴套。'),
        ('E　十字接头横轴 · 4 号轴 3705', 40,
         [(-40,-30,'半套'),(-30,-10,'连杆'),(-10,10,'接头'),(10,30,'连杆'),(30,40,'半套')],
         '接头为 32013，两侧直接贴 32526 短边中孔；只在最外侧各放一个半轴套。'),
        ('F　输入连杆—主臂轴 · 3 号轴 4519（上夹指）', (-20,40),
         [(-20,-10,'半套'),(-10,10,'红梁'),(10,30,'连杆'),(30,40,'半套')],
         '32526 长边末孔直接贴红梁后端第 2 孔；两端各半轴套。下夹指按此截面左右镜像。'),
    ]
    cx, scale = 750, 5
    for i, (title, extent, layers, note) in enumerate(rows):
        y = 148 + 222 * i
        svg.append(f'<text x="50" y="{y}" class="sub" font-weight="700">{escape(title)}</text>')
        mid = y + 60
        axis_lo, axis_hi = extent if isinstance(extent, tuple) else (-extent, extent)
        svg.append(f'<line x1="{cx+axis_lo*scale}" y1="{mid}" x2="{cx+axis_hi*scale}" y2="{mid}" stroke="#202c3b" stroke-width="12"/>')
        for a,b,label in layers:
            x = cx + a*scale
            svg.append(f'<rect x="{x}" y="{mid-25}" width="{(b-a)*scale}" height="50" rx="3" fill="{COLORS[label]}" stroke="#fff" stroke-width="2"/>')
            svg.append(f'<text x="{cx+(a+b)/2*scale}" y="{mid+6}" text-anchor="middle" class="small">{label}</text>')
        svg.append(f'<line x1="{cx}" y1="{mid-34}" x2="{cx}" y2="{mid+38}" stroke="#263549" stroke-dasharray="4 4"/>')
        boundaries = sorted({v for a,b,_ in layers for v in (a,b)})
        for t in boundaries:
            x = cx+t*scale
            svg.append(f'<line x1="{x}" y1="{mid+28}" x2="{x}" y2="{mid+35}" stroke="#6d7c8d"/>')
            svg.append(f'<text x="{x}" y="{mid+56}" text-anchor="middle" class="small">{t*.4:g}</text>')
        svg.append(f'<text x="50" y="{mid+96}" class="small">{escape(note)}</text>')
    svg.append('<text x="50" y="1484" class="small">标尺单位 mm，0 为夹指中面；半套 = 半轴套 32123a，整套 = 轴套 3713。未画孔形和倒角。</text></svg>')
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text('\n'.join(svg), encoding='utf-8')


if __name__ == '__main__':
    main()
