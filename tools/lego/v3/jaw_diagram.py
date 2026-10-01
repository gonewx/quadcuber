"""生成前端孔位和轴向叠放示意。"""
from pathlib import Path


def main():
    out = Path(__file__).resolve().parents[3] / 'docs/lego/v3/img'
    out.mkdir(parents=True, exist_ok=True)
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="1000" viewBox="0 0 1500 1000">
<rect width="1500" height="1000" fill="#fff"/><g font-family="Noto Sans CJK SC, sans-serif" fill="#172535">
<text x="70" y="75" font-size="38" font-weight="700">压头装配：两个孔固定轴芯</text>
<text x="70" y="120" font-size="23">孔号从主臂后端数起；上下轮胎都在主臂同一侧。1 孔距 = 8mm。</text>
<rect x="130" y="200" width="1060" height="88" rx="44" fill="#c94338"/>
'''
    for i in range(9):
        x = 180 + 120*i
        svg += f'<circle cx="{x}" cy="244" r="24" fill="white"/><text x="{x}" y="178" text-anchor="middle" font-size="25">{i+1}</text>'
    svg += '''<rect x="879" y="295" width="282" height="38" rx="19" fill="#e78360"/>
<path d="M 900 286 V 350 M 1140 286 V 350" stroke="#172535" stroke-width="10"/>
<text x="180" y="390" font-size="23">第 2 孔：接输入连杆</text><text x="495" y="390" font-size="23">第 4 孔：主转轴</text>
<text x="800" y="390" font-size="23">第 7、9 孔：2 号轴 + 6632</text>
<text x="70" y="485" font-size="30" font-weight="700">沿前轴看：总宽约 16.4mm（胎体外缘）</text>
<rect x="510" y="570" width="90" height="170" fill="#e78360"/>
<rect x="600" y="570" width="180" height="170" fill="#c94338"/>
<rect x="780" y="605" width="90" height="100" fill="#77818b"/>
<rect x="775" y="548" width="100" height="214" rx="16" fill="none" stroke="#222" stroke-width="20"/>
<path d="M510 655 H870" stroke="#111" stroke-width="13"/>
<text x="555" y="815" text-anchor="middle" font-size="23">薄梁 4mm</text>
<text x="690" y="850" text-anchor="middle" font-size="23">主臂 8mm</text>
<text x="950" y="790" font-size="23">半轴套 4mm</text><text x="950" y="830" font-size="23">外套 3139b 小胎</text>
<text x="70" y="925" font-size="24">后轴叠放相同，只有半轴套，不套轮胎。前后轴相距 16mm；轴端与薄梁、轴套外侧齐平。</text>
</g></svg>'''
    (out / 'jaw_layers.svg').write_text(svg)


if __name__ == '__main__':
    main()
