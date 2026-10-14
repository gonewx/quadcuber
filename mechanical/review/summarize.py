"""把 run_review.py 的 review.json 汇总成 Markdown 表（写入报告附录）。"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import candidate as C  # noqa: E402

LEVER = {p.note for p in C.lever_parts()}


def group(other):
    if other.startswith('support'):
        return 'lever' if other.split()[-1] in LEVER else 'support'
    return 'arm'


def mins(entries):
    out = {}
    for e in entries:
        g = group(e['other'])
        if g not in out or e['mm'] < out[g]['mm']:
            out[g] = e
    return out


def cell(e):
    if not e:
        return '≥4'
    return ('**穿模**' if e['penetrating'] else f"{e['mm']:.2f}") + f"（{e['part'].split(' ', 1)[0]}↔{e['other'].split(' ', 2)[-1]}）"


def table(res, kind, keys, title):
    rows = [f'#### {title}', '', '| 姿态 | 现方案：托座(不含杠杆) | 现方案：杠杆 | 现方案：其他臂/本臂 | 新方案：托座(不含杠杆) | 新方案：杠杆 | 新方案：其他臂/本臂 |',
            '|---|---|---|---|---|---|---|']
    for k in keys:
        cells = []
        for f in ('previous', 'rot90'):
            r = res.get(f, {}).get(kind, {}).get(str(k))
            if r is None:
                cells += ['—'] * 3
                continue
            m = mins(r)
            cells += [cell(m.get('support')), cell(m.get('lever')), cell(m.get('arm'))]
        rows.append(f'| {k} | ' + ' | '.join(cells) + ' |')
    return '\n'.join(rows) + '\n'


def main(path, out):
    d = json.loads(Path(path).read_text())
    res = d['results']
    md = ['# 整机运动干涉核算结果（自动生成）', '', d['method'], '',
          '单位 mm；“≥4”表示 4mm 搜索半径内无零件；括号内为最近的一对零件。同一臂内按设计插接/贴面的零件对不计入。', '']
    md.append(table(res, 'state', ['loading-all50', 'FB0-open', 'FB0-held', 'support-down40_8', 'LR90-open', 'both-held'], '静态姿态（现有装料流程）'))
    md.append(table(res, 'fbroll', [str(a) for a in range(0, 51, 2)], 'FB 张开回转 50°→0°（托座上位，LR 50° 张开）'))
    md.append(table(res, 'fbclose', ['0.0', '0.25', '0.5', '0.75'], 'FB 在 0° 由张开到夹紧（行程比例，托座上位）'))
    md.append(table(res, 'drop', ['0.0', '10.0', '20.0', '30.0', '40.8'], '托座下降（FB 0° 夹紧，LR 50° 张开）'))
    md.append(table(res, 'lrroll', [str(a) for a in range(50, 91, 2)], 'LR 张开回转 50°→90°（托座下位，FB 0° 夹紧）'))
    md.append(table(res, 'lrclose', ['0.0', '0.25', '0.5', '0.75'], 'LR 在 90° 由张开到夹紧'))
    lev = res.get('rot90', {}).get('fblever')
    if lev:
        md += ['#### FB 0°~30° 段：杠杆与其余零件分开统计', '', '| FB 角 | 现方案 杠杆 | 现方案 其余 | 新方案 杠杆 | 新方案 其余 |', '|---|---|---|---|---|']
        for a in range(0, 32, 2):
            row = []
            for f in ('previous', 'rot90'):
                r = res.get(f, {}).get('fblever', {}).get(str(a), {})
                row += [cell(r.get('lever')), cell(r.get('other'))]
            md.append(f'| {a} | ' + ' | '.join(row) + ' |')
        md.append('')
    ft = res.get('rot90', {}).get('fullturn', {})
    if ft:
        md += ['#### 整圈回转（新方案，子午面精确回转体）', '', '| 转动臂 | 本臂夹指 | 相邻臂夹指 | 托座 | 新压头扫掠最近 | 其余机械头扫掠对相邻臂新压头 |', '|---|---|---|---|---|---|']
        for key, v in sorted(ft.items()):
            arm, own, adj, drop = eval(key)
            a = v['front_sweep'][0] if v['front_sweep'] else None
            b = v['head_sweep_vs_neighbour_fronts'][0] if v['head_sweep_vs_neighbour_fronts'] else None
            f = lambda x: f'{x[0]:.2f}（{x[1].split(" ", 1)[0]}↔{x[2].split(" ", 2)[-1]}）' if x else '≥6'
            md.append(f"| {arm} | {'张开' if own else '夹紧'} | {'张开' if adj else '夹紧'} | {'下位' if drop else '上位'} | {f(a)} | {f(b)} |")
        md.append('')
    Path(out).write_text('\n'.join(md))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
