#!/usr/bin/env python3
"""导出 B1 的检查报告、制板文件和手焊清单。用系统 Python 运行，KiCad 通过 toolchain 的 KICAD_APP_RUN/KICAD_CLI 调用。

输出：generated/electronics-b1/（ERC/DRC 报告、网表、Gerber+钻孔 ZIP、BOM、预览图）。不改动 PCB。
"""
import csv
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / 'electronics'))
sys.path.insert(0, str(HERE))
from toolchain import cli_command  # noqa: E402
from circuit import C  # noqa: E402

OUT = ROOT / 'generated/electronics-b1'
PCB = HERE / 'quadcuber-b1.kicad_pcb'
SCH = HERE / 'quadcuber-b1.kicad_sch'
LAYERS = 'F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts'


def run(*args):
    env = dict(os.environ)
    cache = Path(tempfile.gettempdir()) / 'quadcuber-kicad'
    for key, leaf in [('XDG_CONFIG_HOME', 'config'), ('XDG_CACHE_HOME', 'cache'), ('XDG_DATA_HOME', 'data')]:
        env.setdefault(key, str(cache / leaf))
        Path(env[key]).mkdir(parents=True, exist_ok=True)
    r = subprocess.run([*cli_command(), *map(str, args)], cwd=ROOT, env=env, capture_output=True, text=True)
    if r.returncode:
        print(r.stdout, r.stderr)
        raise RuntimeError(args)
    return r.stdout


def finish_assembly_preview():
    """固定深色背景，让浅色装配线条在浏览器和图片查看器中均清晰可见。"""
    svg = OUT / 'assembly.svg'
    source = svg.read_text()
    # 使用实际矩形而非 CSS 背景，确保 SVG 转 PNG 后仍不透明。
    if 'id="assembly-background"' not in source:
        source = re.sub(
            r'(<svg\b[^>]*>)',
            r'\1\n<rect id="assembly-background" x="0" y="0" width="100%" '
            r'height="100%" fill="#161b22" />', source, count=1,
        )
        svg.write_text(source)
    import cairosvg
    cairosvg.svg2png(
        url=str(svg), write_to=str(OUT / 'assembly.png'),
        output_width=2400, output_height=2400, background_color='#161b22',
    )


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    run('sch', 'erc', '-o', OUT / 'erc.rpt', SCH)
    run('sch', 'export', 'netlist', '--format', 'kicadxml', '-o', OUT / 'netlist.xml', SCH)
    run('sch', 'export', 'pdf', '-o', OUT / 'schematic.pdf', SCH)
    run('pcb', 'drc', '--schematic-parity', '-o', OUT / 'drc.rpt', PCB)
    erc, drc = (OUT / 'erc.rpt').read_text(), (OUT / 'drc.rpt').read_text()
    assert 'Errors 0' in erc, 'ERC 有错误'
    errors = [blk for blk in re.split(r'\n(?=\[)', drc) if '; error' in blk]
    assert not errors and 'Found 0 unconnected pads' in drc, 'DRC 有错误或未连通焊盘'

    with tempfile.TemporaryDirectory(prefix='b1-fab-') as td:
        run('pcb', 'export', 'gerbers', '--layers', LAYERS, '--subtract-soldermask', '-o', td + '/', PCB)
        run('pcb', 'export', 'drill', '--excellon-separate-th', '-o', td + '/', PCB)
        files = sorted(p for p in Path(td).iterdir() if p.is_file())
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w', zipfile.ZIP_DEFLATED) as z:
            for f in files:
                info = zipfile.ZipInfo(f.name, date_time=(2026, 10, 14, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, f.read_bytes())
        (OUT / 'quadcuber-b1-gerber.zip').write_bytes(stream.getvalue())
        names = [f.name for f in files]

    for name, layers, mirror in [('pcb-top', 'F.Cu,F.Silkscreen,Edge.Cuts', False),
                                 ('pcb-bottom', 'B.Cu,B.Silkscreen,Edge.Cuts', True),
                                 ('assembly', 'F.Silkscreen,F.Fab,Edge.Cuts', False)]:
        run('pcb', 'export', 'svg', '--mode-single', '--fit-page-to-board', '--exclude-drawing-sheet',
            '--layers', layers, *(['--mirror'] if mirror else []), '-o', OUT / f'{name}.svg', PCB)
    finish_assembly_preview()

    # 手焊清单：先贴片后通孔，贴片里先 IC（热风枪）再小件，最后焊高的通孔插座。同型号合并。
    order = ['贴片 IC', '贴片电阻电容', '贴片二极管', '贴片保险丝', '贴片电解电容', '贴片电感', '排针/排母', '插座']

    def kind(c):
        fp = c['fp']
        if c['ref'][0] in 'UQ' and 'Pico' not in fp:
            return '贴片 IC'
        if fp.startswith(('R_0805', 'C_0805', 'R_2512')):
            return '贴片电阻电容'
        if fp.startswith('D_'):
            return '贴片二极管'
        if fp.startswith('Fuse'):
            return '贴片保险丝'
        if fp.startswith('CP_'):
            return '贴片电解电容'
        if fp.startswith('L_'):
            return '贴片电感'
        if fp.startswith('PinHeader') or 'Pico' in fp:
            return '排针/排母'
        return '插座'

    groups = defaultdict(list)
    for c in C:
        if not c['ref'].startswith('H'):
            part = c['part'] or c['value']
            if c['value'] not in part and not c['ref'].startswith('U'):
                part = f"{c['value']} {part}"
            groups[(kind(c), part, c['fp'], c['note'])].append(c)
    rows = []
    for (k, part, fp, _note), cs in sorted(groups.items(), key=lambda kv: (order.index(kv[0][0]), kv[0][1])):
        notes = sorted({c['note'] for c in cs if c['note']})
        rows.append({'焊接顺序': order.index(k) + 1, '类别': k, '型号/规格': part, '位号': ','.join(c['ref'] for c in cs),
                     '数量': len(cs), '封装': fp, '说明': '；'.join(notes)})
    with (OUT / 'bom-hand-solder.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, list(rows[0]), lineterminator='\n')
        w.writeheader()
        w.writerows(rows)

    manifest = {
        'board': 'quadcuber-b1', 'size_mm': [99.0, 99.0], 'layers': 2,
        'erc': 'Errors 0', 'drc': re.findall(r'Found \d+ [^*]+', drc),
        'gerber_files': names,
        'sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in [PCB, SCH, OUT / 'quadcuber-b1-gerber.zip', OUT / 'bom-hand-solder.csv']},
    }
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
