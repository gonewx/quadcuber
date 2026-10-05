"""生成32449双侧薄梁的孔位、轮端叠放和后固定点示意。"""
from pathlib import Path


def main():
    out=Path(__file__).resolve().parents[3]/'docs/lego/v5/img'
    out.mkdir(parents=True,exist_ok=True)
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="1000" viewBox="0 0 1500 1000">',
         '<rect width="1500" height="1000" fill="white"/><g font-family="Noto Sans CJK SC, sans-serif" fill="#172535">',
         '<text x="55" y="58" font-size="34" font-weight="700">每个轮毂两侧各一根 32449 四孔薄梁</text>',
         '<text x="55" y="104" font-size="22">孔号从后端数；上下两只压头完全相同。孔距 8mm，图中沿长度方向展开。</text>']
    # 粗梁的第6、7孔与薄梁第1、2孔对齐；轮轴对应薄梁第4孔。
    for y,label,first,count,height,color in [(180,'7 孔主臂',200,7,60,'#c94338'),
                                           (290,'第一片 32449',750,4,34,'#e78360'),
                                           (370,'第二片 32449',750,4,34,'#e78360')]:
        svg += [f'<text x="55" y="{y+30}" font-size="23">{label}</text>',
                f'<rect x="{first-28}" y="{y}" width="{110*(count-1)+56}" height="{height}" rx="17" fill="{color}"/>']
        for i in range(count):
            x=first+i*110;cy=y+height/2
            if count==4 and i in (0,3):
                svg.append(f'<path d="M{x-10} {cy} H{x+10} M{x} {cy-10} V{cy+10}" stroke="white" stroke-width="7"/>')
            else:
                svg.append(f'<circle cx="{x}" cy="{cy}" r="11" fill="white"/>')
            svg.append(f'<text x="{x+22 if count==4 else x}" y="{y-12}" text-anchor="middle" font-size="21">{i+1}</text>')
    svg += ['<path d="M750 220V412 M860 220V412" stroke="#34465b" stroke-width="5" stroke-dasharray="8 5"/>',
            '<circle cx="1080" cy="230" r="38" fill="#222"/><circle cx="1080" cy="230" r="26" fill="#aaa"/>',
            '<path d="M1080 230V412" stroke="#77818b" stroke-width="5" stroke-dasharray="8 5"/>',
            '<text x="55" y="458" font-size="23">主臂第 2 孔接输入杆；第 4 孔作支点；第 6、7 孔固定两片薄梁。</text>',
            '<text x="55" y="502" font-size="23">薄梁第 1 十字孔装 4519；第 2 圆孔装 32054；第 3 孔空；第 4 十字孔装轮轴。</text>',
            '<text x="55" y="566" font-size="28" font-weight="700">轮端沿轴向：4mm 薄梁 ＋ 8mm 轮毂 ＋ 4mm 薄梁</text>']
    for x,w,c,label in [(300,80,'#e78360','32449'),(380,160,'#aaa','42610'),(540,80,'#e78360','32449')]:
        svg += [f'<rect x="{x}" y="610" width="{w}" height="92" fill="{c}"/>',
                f'<text x="{x+w/2}" y="735" text-anchor="middle" font-size="20">{label}</text>']
    svg += ['<path d="M300 656H620" stroke="#42566c" stroke-width="12"/>',
            '<text x="700" y="640" font-size="23">32062 二号轴：两端齐平，不加外轴套。</text>',
            '<text x="700" y="682" font-size="23">轮毂圆孔绕固定十字轴转动；试装确认不夹死。</text>',
            '<text x="55" y="800" font-size="24">后固定点：4519 三号轴贯穿薄—粗—薄，外侧各装一个 32123a 半轴套。</text>',
            '<text x="55" y="846" font-size="24">前固定点：32054 挡套长销贯穿薄—粗—薄，挡套在第一片外侧。</text>',
            '<text x="55" y="910" font-size="24">四臂合计：16 根 32449；8 组轮毂＋轮胎（已有 4 组，另补 4 组）。</text>',
            '<text x="55" y="955" font-size="21">轮胎按 14×6mm 建模；保持力、孔隙、薄梁变形及带载间隙须实测。</text>','</g></svg>']
    (out/'jaw_layers.svg').write_text('\n'.join(svg))


if __name__=='__main__':
    main()
