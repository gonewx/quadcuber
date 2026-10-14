#!/usr/bin/env python3
# SPDX-License-Identifier: CC0-1.0
"""Build independently authored display envelopes; never rewrite PCB geometry.

Run with Python + CadQuery. No manufacturer CAD is imported or redistributed.
Model colors are presentation choices, not material specifications.
"""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parent
MODELS = ROOT / 'lib/3dmodels'
CUSTOM = MODELS / 'project'
SPECIAL = {
    'Fuse_1812_4532Metric': 'MF_MSMF050_SIMPLIFIED_MAX_ENVELOPE.step',
    'Fuse_Bourns_MF_MSMF_Style2_1812': 'MF_MSMF110_16X_SIMPLIFIED_MAX_ENVELOPE.step',
    'L_Bourns_SRP1245A': 'SRP1245A_SIMPLIFIED_MAX_ENVELOPE.step',
    'Jack_DC_Switchcraft_RASPC722X': 'RASPC722X_SIMPLIFIED_BODY.step',
    'EV3_UserDrawing_PINMAP_HOLD': 'EV3_USER_DRAWING_SIMPLIFIED_BODY.step',
}


def nodes(text, kind):
    """Return balanced S-expression spans, respecting quoted/escaped strings."""
    for m in re.finditer(r'\(' + re.escape(kind) + r'(?=\s)', text):
        start = m.start()
        depth = 0
        quoted = escaped = False
        for i in range(start, len(text)):
            c = text[i]
            if quoted:
                if escaped:
                    escaped = False
                elif c == '\\':
                    escaped = True
                elif c == '"':
                    quoted = False
            elif c == '"':
                quoted = True
            elif c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    yield start, i + 1
                    break
        else:
            raise ValueError('Unbalanced expression')


def without_models(text):
    for a, b in reversed(list(nodes(text, 'model'))):
        text = text[:a] + text[b:]
    return re.findall(r'"(?:\\.|[^"\\])*"|[^\s()]+|[()]', text)


def model_block(filename, hide=False):
    return (f'(model "{filename}"' + (' (hide yes)' if hide else '') +
            '\n\t\t(offset (xyz 0 0 0))\n\t\t(scale (xyz 1 1 1))'
            '\n\t\t(rotate (xyz 0 0 0))\n\t)')


def attach(footprint, hide=False):
    name = re.match(r'\(footprint "([^"]+)"', footprint).group(1).split(':')[-1]
    if name in SPECIAL:
        for a, b in reversed(list(nodes(footprint, 'model'))):
            footprint = footprint[:a] + footprint[b:]
        end = footprint.rfind(')')
        footprint = (footprint[:end] + '\n\t' +
                     model_block('${KIPRJMOD}/lib/3dmodels/project/' + SPECIAL[name], hide) +
                     '\n' + footprint[end:])
    else:
        footprint = footprint.replace('${KICAD9_3DMODEL_DIR}/', '${KIPRJMOD}/lib/3dmodels/kicad/')
        if hide:
            for a, b in reversed(list(nodes(footprint, 'model'))):
                model = footprint[a:b]
                if '(hide yes)' not in model:
                    model = model[:-1] + '\n\t\t(hide yes)\n\t)'
                footprint = footprint[:a] + model + footprint[b:]
    return '\n'.join(line.rstrip() for line in footprint.splitlines() if line.strip()) + ('\n' if footprint.endswith('\n') else '')


def build_assets():
    import cadquery as cq
    CUSTOM.mkdir(parents=True, exist_ok=True)
    records = []

    def save(name, parts, evidence):
        assembly = cq.Assembly(name=name.removesuffix('.step'))
        for i, (shape, color) in enumerate(parts):
            assert shape.isValid()
            assembly.add(shape, name=f'part_{i}', color=cq.Color(*color))
        target = CUSTOM / name
        assembly.save(str(target))
        combined = cq.Compound.makeCompound([p[0] for p in parts])
        box = combined.BoundingBox()
        evidence.update(file=name, sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                        bbox_mm={k: round(getattr(box, k), 6) for k in
                                 ['xmin', 'xmax', 'ymin', 'ymax', 'zmin', 'zmax']},
                        solids=len(combined.Solids()), valid=combined.isValid())
        records.append(evidence)

    box = lambda x, y, z, center: cq.Workplane('XY').box(x, y, z, centered=(True, True, False)).translate(center).val()
    save(SPECIAL['Fuse_1812_4532Metric'],
         [(box(4.73, 3.41, 0.85, (0, 0, 0)), (0.65, 0.69, 0.30))], {
             'classification': 'independently authored SIMPLIFIED maximum rectangular envelope; CC0-1.0',
             'source': 'sources/bourns-3d-review/mf-msmf.pdf pages4,7; published dimension facts only',
             'references': ['F2', 'F3'],
             'evidence': 'MF-MSMF050 Style1 maxima A4.73 B3.41 C0.85mm; centered on pads; seatingz0; -2 is packaging',
             'limitations': 'No original CAD imported, notches or metallization. Manufacturer CAD redistribution permission unconfirmed, so the aligned official model is not distributed.'})
    save(SPECIAL['L_Bourns_SRP1245A'],
         [(box(14.0, 12.8, 5.0, (0, 0, 0)), (0.31, 0.32, 0.34))], {
             'classification': 'independently authored SIMPLIFIED maximum rectangular envelope; CC0-1.0',
             'source': 'sources/bourns-3d-review/SRP1245A.pdf page1 Lead Frame dimensions; published facts only',
             'references': ['L1', 'L2'],
             'evidence': 'Outer terminal span13.5+/-0.5, body width12.5+/-0.3, height4.8+/-0.2 -> envelope14.0x12.8x5.0mm',
             'limitations': 'No internal coil, terminal geometry, top marking or original CAD imported. Manufacturer model had12.9mm span (0.1 below datasheet minimum); redistribution permission also unconfirmed. This dimension-derived block is not exact part CAD or a qualified collision model.'})

    save(SPECIAL['Fuse_Bourns_MF_MSMF_Style2_1812'],
         [(box(4.83, 3.41, 0.8, (0, 0, 0)), (0.78, 0.41, 0.17))], {
             'classification': 'project-authored SIMPLIFIED maximum rectangular envelope',
             'source': 'sources/bourns-3d-review/mf-msmf.pdf pages5,7', 'references': ['F10', 'F11', 'F12', 'F13'],
             'evidence': 'MF-MSMF110/16X Style2 maxima A4.83 B3.41 C0.80mm; centered on pads; seatingz0',
             'limitations': 'No notches, metallization or internal structure; NOT manufacturer CAD. Wrong050 download is not used.'})
    save(SPECIAL['Jack_DC_Switchcraft_RASPC722X'],
         [(box(9, 14.5, 11, (0, -7.25, 0)), (0.18, 0.37, 0.63))], {
             'classification': 'project-authored SIMPLIFIED nominal body', 'references': ['J1'],
             'source': 'sources/raspc722x-review.md; parent visually verified official PDF, original unavailable here',
             'evidence': 'Body9x14.5x11mm; mating face at localPCB y0, body extends toPCB y+14.5 (modely-14.5)',
             'limitations': 'Solid block, no guessed bore, internal contacts, shunt tab, solder tails or cable clearance. Not full envelope or manufacturer CAD.'})
    save(SPECIAL['EV3_UserDrawing_PINMAP_HOLD'],
         [(box(12.2, 15, 14.95, (0, -1.5, 0)), (0.18, 0.37, 0.63))], {
             'classification': 'project-authored SIMPLIFIED nominal body', 'references': ['J10', 'J11', 'J12', 'J13'],
             'source': 'sources/ev3-connector-user-drawing.png and sources/ev3-user-drawing-review.md',
             'evidence': 'Body12.2x15x14.95; localPCB x+/-6.1,y-6..+9; modely-9..+6; origin locating-hole midpoint',
             'limitations': 'No guessed ears, latch cavity, internal contacts, pins or insertion space. Body is not complete mechanical envelope; existing drawing-view uncertainty persists.'})
    (MODELS / 'project-models.json').write_text(json.dumps(records, indent=2) + '\n')


def attach_assets():
    board = ROOT / 'quadcuber.kicad_pcb'
    old = board.read_text()
    new = old
    used = set()
    for a, b in reversed(list(nodes(old, 'footprint'))):
        fp = old[a:b]
        used.add(re.match(r'\(footprint "([^"]+)"', fp).group(1).split(':')[-1])
        ref = re.search(r'\(property "Reference" "([^"]+)"', fp).group(1)
        new = new[:a] + attach(fp, ref in ('C26', 'C36')) + new[b:]
    assert without_models(old) == without_models(new), 'Non-model PCB data changed'
    board.write_text(new)
    for name in sorted(used):
        path = ROOT / 'lib/Quadcuber.pretty' / (name + '.kicad_mod')
        old = path.read_text()
        new = attach(old)
        assert without_models(old) == without_models(new)
        if new != old:
            path.write_text(new)


if __name__ == '__main__':
    build_assets()
    attach_assets()
    print('Display models generated and attached; non-model PCB/library tokens unchanged.')
