"""生成库存四组轮胎方案的孔位和叠放示意。"""
from pathlib import Path


def main():
    out = Path(__file__).resolve().parents[3] / 'docs/lego/v3/img'
    out.mkdir(parents=True, exist_ok=True)
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="1000" viewBox="0 0 1500 1000">',
           '<rect width="1500" height="1000" fill="white"/><g font-family="Noto Sans CJK SC, sans-serif" fill="#172535">',
           '<text x="60" y="65" font-size="36" font-weight="700">每臂一组轮胎＋一个硬压头</text>',
           '<text x="60" y="110" font-size="23">孔号从后端数；图示展开孔位，1 孔距 = 8mm，夹紧角约 3.64°。</text>']
    for n,y,title in [(7,200,'上侧：7 孔粗梁'),(5,430,'下侧：5 孔粗梁')]:
        start=220 if n==7 else 330
        svg += [f'<text x="60" y="{y-35}" font-size="26">{title}</text>',f'<rect x="{start-35}" y="{y}" width="{(n-1)*110+70}" height="70" rx="35" fill="#c94338"/>']
        for i in range(n):
            x=start+i*110
            svg += [f'<circle cx="{x}" cy="{y+35}" r="20" fill="white"/><text x="{x}" y="{y-10}" text-anchor="middle" font-size="22">{i+1}</text>']
        svg += [f'<rect x="635" y="{y+80}" width="510" height="32" rx="16" fill="#e78360"/>']
        for i in range(5):
            x=660+i*110
            svg += [f'<circle cx="{x}" cy="{y+96}" r="9" fill="white"/>']
        svg += [f'<path d="M660 {y+40} V{y+120} M{880 if n==7 else 770} {y+40} V{y+120}" stroke="#172535" stroke-width="8"/>']
    svg += ['<text x="1000" y="225" font-size="23">薄梁前孔装轮毂</text>',
            '<text x="1000" y="263" font-size="23">32002 短段穿薄梁</text>',
            '<text x="1000" y="301" font-size="23">长段进入 42610</text>',
            '<text x="850" y="608" font-size="23">薄梁第 3、4 孔 → 42003 两个圆孔</text>',
            '<text x="60" y="690" font-size="29" font-weight="700">装配剖面（尺寸为 mm）</text>',
            '<text x="60" y="742" font-size="24">上侧：4mm 薄梁 │ 8mm 轮毂，轮胎 14×6mm；轮毂与主臂中面对齐。</text>',
            '<text x="60" y="791" font-size="24">下侧：魔方 ← 凸点端面 ┃ 6587 轴肩 │ 42003 │ 半轴套 │ 原长轴尾。</text>',
            '<text x="60" y="854" font-size="24">推力由轴肩抵住块体承受；两个固定销防止块体转动。不要截短轴尾。</text>',
            '<text x="60" y="923" font-size="24">轮毂可以滚动；硬凸点随主臂倾斜。夹紧保持与魔方表面接触需实测。</text>', '</g></svg>']
    (out / 'jaw_layers.svg').write_text('\n'.join(svg))


if __name__ == '__main__':
    main()
