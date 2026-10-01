"""生成两端十字孔薄梁安装轮胎的孔位与叠放示意。"""
from pathlib import Path


def main():
    out = Path(__file__).resolve().parents[3] / 'docs/lego/v3/img'
    out.mkdir(parents=True, exist_ok=True)
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="1000" viewBox="0 0 1500 1000">',
           '<rect width="1500" height="1000" fill="white"/><g font-family="Noto Sans CJK SC, sans-serif" fill="#172535">',
           '<text x="60" y="65" font-size="36" font-weight="700">上下相同：42610 轮毂＋50945 轮胎</text>',
           '<text x="60" y="110" font-size="23">孔号从后端数；图示展开孔位，1 孔距 = 8mm，夹紧角约 3.84°。</text>']
    for y,title in [(200,'上侧：7 孔粗梁'),(430,'下侧：7 孔粗梁')]:
        svg += [f'<text x="60" y="{y-35}" font-size="26">{title}</text>',f'<rect x="185" y="{y}" width="730" height="70" rx="35" fill="#c94338"/>']
        for i in range(7):
            x=220+i*110
            svg += [f'<circle cx="{x}" cy="{y+35}" r="20" fill="white"/><text x="{x}" y="{y-10}" text-anchor="middle" font-size="22">{i+1}</text>']
        svg += [f'<rect x="745" y="{y+80}" width="510" height="32" rx="16" fill="#e78360"/>']
        for i in range(5):
            x=770+i*110
            if i in (0,4):
                svg += [f'<path d="M{x-10} {y+96} H{x+10} M{x} {y+86} V{y+106}" stroke="white" stroke-width="7"/>']
            else:
                svg += [f'<circle cx="{x}" cy="{y+96}" r="9" fill="white"/>']
        svg += [f'<path d="M770 {y+40} V{y+120} M880 {y+40} V{y+120}" stroke="#172535" stroke-width="8"/>',
                f'<circle cx="1100" cy="{y+35}" r="42" fill="#222"/><circle cx="1100" cy="{y+35}" r="29" fill="#aaa"/>',
                f'<path d="M1100 {y+35} V{y+115}" stroke="#77818b" stroke-width="9"/>']
    svg += ['<text x="60" y="610" font-size="25">主臂第 2 孔：输入连杆；第 4 孔：支点；第 6、7 孔：接薄梁。</text>',
            '<text x="60" y="660" font-size="25">薄梁第 1 十字孔：3749 轴销；第 2 圆孔：黑销；第 4 圆孔：轮毂。</text>',
            '<text x="60" y="735" font-size="29" font-weight="700">轴向叠放（上下完全相同）</text>',
            '<text x="60" y="786" font-size="24">4mm 薄梁 │ 8mm 轮毂；32002 短段穿薄梁、长段插轮毂。</text>',
            '<text x="60" y="837" font-size="24">第 5 十字孔留空。轮胎 14×6mm，轮胎与主臂中面对齐。</text>',
            '<text x="60" y="904" font-size="24">轮毂可以滚动，沿轮轴方向的夹持能力需实测。整机需 8 组：已有 4 组，补 4 组。</text>', '</g></svg>']
    (out / 'jaw_layers.svg').write_text('\n'.join(svg))


if __name__ == '__main__':
    main()
