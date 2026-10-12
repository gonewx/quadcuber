#!/usr/bin/env python3
"""Prepare an explicitly limited assembly candidate; never edit design files."""
import csv
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
VARIANT = 'ENG-POWER-CONTROLLER-NO-EV3-v2-JLC'
OUT = HERE / VARIANT
OMIT = {'J10', 'J11', 'J12', 'J13', 'C26', 'C36'}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
pcb = ROOT / 'electronics/quadcuber.kicad_pcb'
assert sha(pcb) == 'b04859e7a282eb648943abfbf70d00e488a887627a74470aab24ffc20d637d44'
OUT.mkdir(exist_ok=True)
inputs, outputs, refs = {}, {}, []
for kind, key in [('bom', 'Reference'), ('positions', 'Ref')]:
    src = HERE / f'fabrication-populated-{kind}.csv'
    with src.open(newline='') as f:
        reader = csv.DictReader(f)
        fields, original = reader.fieldnames, list(reader)
    assert len(original) == 171
    rows = [r for r in original if r[key] not in OMIT]
    assert len(rows) == 167
    these_refs = {r[key] for r in rows}
    assert len(these_refs) == 167 and not these_refs & OMIT
    refs.append(these_refs)
    dst = OUT / f'{VARIANT}-{kind}.csv'
    with dst.open('w', newline='') as f:
        w = csv.DictWriter(f, fields)
        w.writeheader()
        w.writerows(rows)
    inputs[str(src.relative_to(ROOT))] = sha(src)
    outputs[dst.name] = sha(dst)
assert refs[0] == refs[1]
manifest = {
    'variant': VARIANT, 'status': 'CANDIDATE_NOT_RELEASED_NOT_ORDERED',
    'design_baseline_commit': 'da5fc42b5e0c6352c827f9ae905eb891fe0dd12b',
    'pcb_sha256': sha(pcb), 'populated_ref_count': 167,
    'do_not_populate': sorted(OMIT),
    'assembly_variant_only': True, 'hardware_changed': False,
    'scope': 'Power/controller bench evaluation; no EV3 connectors or external motors/servos/encoders connected.',
    'conditions': ['Resolve JLC fabrication findings before ordering.',
                   'No generic/full-board BOM or CPL may be substituted.',
                   'Begin with no external loads, controlled 9V source, 0.5A current limit and known source capacitance.',
                   'USB host must supply VBUS while connected; disconnect before host power-off.',
                   'C26/C36 remain DNP; do not add bulk output capacitance without loop verification.',
                   'No robot integration/EV3 operation approval; later verified pin mapping may require a PCB revision.'],
    'source_sha256': inputs, 'output_sha256': outputs,
}
(OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps({'variant': VARIANT, 'bom_cpl_refs_match': True, 'populated_refs': 167,
                  'do_not_populate': sorted(OMIT), 'pcb_sha256': sha(pcb)}, indent=2))
