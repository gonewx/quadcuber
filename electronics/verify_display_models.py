#!/usr/bin/env python3
"""Read-only verification with official KiCad 10; writes only the audit report."""
import hashlib
import json
from pathlib import Path
import subprocess
import pcbnew
from display_models import without_models, nodes
from toolchain import require_version

require_version(pcbnew.GetBuildVersion())
ROOT = Path(__file__).resolve().parents[1]
BASE = 'b0c1822d67cf4002c179fc86d4f697d17ba24381'
OUT = ROOT / 'generated/electronics/3d-display-repair'
OUT.mkdir(parents=True, exist_ok=True)
board_path = ROOT / 'electronics/quadcuber.kicad_pcb'
old = subprocess.check_output(['git', 'show', BASE + ':electronics/quadcuber.kicad_pcb'], cwd=ROOT).decode()
new = board_path.read_text()
assert without_models(old) == without_models(new), 'PCB contains a non-model change'
board = pcbnew.LoadBoard(str(board_path))
rows = []
used = set()
for f in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
    name = str(f.GetFPID().GetLibItemName())
    lib = ROOT / 'electronics/lib/Quadcuber.pretty' / (name + '.kicad_mod')
    used.add(lib)
    ref = f.GetReference()
    models = []
    for m in f.Models():
        assert m.m_Filename.startswith('${KIPRJMOD}/'), (ref, m.m_Filename)
        path = ROOT / 'electronics' / m.m_Filename.removeprefix('${KIPRJMOD}/')
        data = path.read_bytes()
        assert data.startswith(b'ISO-10303-21;') and b'END-ISO-10303-21;' in data
        assert m.m_Filename in lib.read_text(), (ref, 'library/model mismatch')
        models.append({'path': str(path.relative_to(ROOT)), 'visible': m.m_Show,
                       'sha256': hashlib.sha256(data).hexdigest()})
    if ref.startswith(('TP', 'H')):
        category = 'bare test pad or mounting hole; no component-body model required'
    elif f.IsDNP():
        category = 'DNP; model explicitly hidden in board'
        assert ref in ('C26', 'C36') and models and not any(x['visible'] for x in models)
    else:
        category = 'populated component with visible, locally resolved model'
        assert models and any(x['visible'] for x in models), (ref, 'missing visible model')
    rows.append({'ref': ref, 'footprint': name, 'dnp': f.IsDNP(), 'category': category, 'models': models})
for lib in used:
    rel = str(lib.relative_to(ROOT))
    oldlib = subprocess.check_output(['git', 'show', BASE + ':' + rel], cwd=ROOT).decode()
    assert without_models(oldlib) == without_models(lib.read_text()), rel
for rel in ['electronics/quadcuber.kicad_pro', 'electronics/quadcuber.kicad_dru']:
    assert (ROOT / rel).read_bytes() == subprocess.check_output(['git', 'show', BASE + ':' + rel], cwd=ROOT)
report = {
    'pass': True, 'baseline_commit': BASE, 'kicad': pcbnew.GetBuildVersion(),
    'pcb_sha256': hashlib.sha256(board_path.read_bytes()).hexdigest(),
    'proof': 'All PCB S-expression tokens outside model nodes exactly equal baseline; same for every used footprint library. Includes pads, holes, tracks, vias, zones and filled polygons, all text, placements, rotations, UUIDs, nets and DNP attributes.',
    'project_and_rules_byte_identical': True,
    'footprints': len(rows),
    'visible_populated_component_bodies': sum(r['category'].startswith('populated') for r in rows),
    'dnp_hidden': [r['ref'] for r in rows if r['dnp']],
    'no_body_required': [r['ref'] for r in rows if r['category'].startswith('bare')],
    'missing_model_files': [], 'missing_populated_body_models': [],
    'exact_full_board_manufacturer_CAD_verified': False, 'manufacturing_release': False,
    'inventory': rows,
}
(OUT / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k != 'inventory'}, indent=2))
