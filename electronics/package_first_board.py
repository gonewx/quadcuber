#!/usr/bin/env python3
"""Package the frozen db20b98 engineering board; never save or regenerate its design.
Run with KiCad 10 Python: package_first_board.py --audit-dir <verified audit directory>.
Subsequent rebuilds use the archived validation directory by default.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'generated/electronics/engineering-first-board'
BASE = 'db20b983d23d1dedc107f435f8ece6b734b3bd6b'
NAME = 'quadcuber-A1-first-board-db20b98'
HAND = set('J1 J2 J3 J4 J10 J11 J12 J13 J20 J21 J22 J23 C2 C3 C102 C122 C142 C162'.split())
MATCHES = {
    'TPS54302DDCR': ('C311983', 'https://www.lcsc.com/product-detail/C311983.html'),
    'USB4105-GF-A': ('C3020560', 'https://www.lcsc.com/product-detail/C3020560.html'),
}
FAB_EXT = {'.gbl','.gbs','.gbp','.gbo','.gm1','.gtl','.gts','.gtp','.gto','.g1','.g2','.drl','.gbrjob'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def csv_bytes(rows, fields=None):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fields or list(rows[0]), lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode('utf-8')


def archive(files):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 10, 14, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, data)
    return stream.getvalue()


def main():
    import pcbnew as pcb
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit-dir', type=Path, default=OUT/'validation')
    args = parser.parse_args()
    if not pcb.Version().startswith('10.'):
        raise RuntimeError('KiCad 10 pcbnew is required')
    # Byte-for-byte preservation includes routing, holes, risk silkscreen and native libraries.
    tracked = subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,'electronics'], cwd=ROOT, text=True).splitlines()
    immutable = sorted(r for r in tracked if Path(r).suffix in {'.kicad_pcb','.kicad_sch','.kicad_pro','.kicad_dru','.kicad_mod','.kicad_sym'} or r=='electronics/circuit.py')
    baseline = {}
    for rel in immutable:
        original = subprocess.check_output(['git','show',BASE+':'+rel],cwd=ROOT)
        if (ROOT/rel).read_bytes()!=original:
            raise RuntimeError('Frozen design differs from db20b98: '+rel)
        baseline[rel] = sha(original)
    sources = dict(baseline)
    payload = {}

    def source(rel):
        data = (ROOT/rel).read_bytes()
        sources[rel] = sha(data)
        return data

    def copy(rel, dest):
        payload[dest] = source(rel)

    audit_files = ['fabrication-preflight.json','jlc-preflight.json','checks.json','power-bounds.json',
                   'current-drc.rpt','current-erc.rpt','current-netlist.xml']
    evidence = {name:(args.audit_dir/name).read_bytes() for name in audit_files}
    fabcheck = json.loads(evidence['fabrication-preflight.json'])
    jlccheck = json.loads(evidence['jlc-preflight.json'])
    controller = json.loads(evidence['checks.json'])
    power = json.loads(evidence['power-bounds.json'])
    board_sha = baseline['electronics/quadcuber.kicad_pcb']
    assert fabcheck['source_sha256']==jlccheck['source_sha256']==board_sha
    assert fabcheck['all_automatic_checks_pass'] and len(fabcheck['checks'])==30
    assert all(c['pass'] for c in fabcheck['checks'])
    assert controller['pass'] and power['contract']=='PASS'
    for mapping in [fabcheck['original_files_sha256'],controller['sha256'],power['hashes']]:
        for rel, digest in mapping.items():
            assert sha(source(rel))==digest, 'Audit input drift: '+rel
    assert 'Found 0 DRC violations' in evidence['current-drc.rpt'].decode()
    assert 'Found 0 unconnected pads' in evidence['current-drc.rpt'].decode()
    assert 'Found 0 Footprint errors' in evidence['current-drc.rpt'].decode()
    assert 'ERC messages: 0  Errors 0  Warnings 0' in evidence['current-erc.rpt'].decode()
    payload.update({'validation/'+name:data for name,data in evidence.items()})

    bom = list(csv.DictReader(io.StringIO(source('generated/electronics/bom.csv').decode())))
    positions = list(csv.DictReader(io.StringIO(source('generated/electronics/positions.csv').decode())))
    positive = {r['Reference']:r for r in bom if int(r['Quantity'])>0}
    board = pcb.LoadBoard(str(ROOT/'electronics/quadcuber.kicad_pcb'))
    fps = {f.GetReference():f for f in board.GetFootprints()}
    thermal_ids = {h['id'] for h in jlccheck['thermal_holes']}
    assert len(thermal_ids)==28
    process = []
    padmap = []
    for ref, row in sorted(positive.items()):
        fp = fps[ref]
        counts = Counter()
        for pad in fp.Pads():
            attr = pad.GetAttribute()
            kind = ('thermal via' if pad.m_Uuid.AsString() in thermal_ids else
                    'SMD' if attr==pcb.PAD_ATTRIB_SMD else
                    'PTH' if attr==pcb.PAD_ATTRIB_PTH else
                    'NPTH' if attr==pcb.PAD_ATTRIB_NPTH else 'other')
            counts[kind] += 1
            xy = pad.GetPosition()
            padmap.append(dict(Reference=ref,Pad=pad.GetNumber(),Net=pad.GetNetname(),
                Native_X_mm=round(pcb.ToMM(xy.x),6),Native_Y_mm=round(pcb.ToMM(xy.y),6),
                Side='Bottom' if fp.IsFlipped() else 'Top',Type=kind))
        if ref in HAND:
            assert counts['SMD']==0 and counts['PTH']>0, ref
            assignment = 'USER_THT'
        elif ref=='J5':
            assert counts['SMD']>0 and counts['PTH']==4
            assignment = 'FACTORY_MIXED_SMT_PLUS_4_PTH_SHIELDS'
        else:
            assert counts['SMD']>0 and counts['PTH']==0, (ref,counts)
            assignment = 'FACTORY_SMT'
        process.append(dict(Reference=ref,Assignment=assignment,SMD_pads=counts['SMD'],
            Component_PTH_pads=counts['PTH'],Thermal_holes=counts['thermal via'],NPTH=counts['NPTH'],
            Side='Bottom' if fp.IsFlipped() else 'Top',MPN=row['MPN']))
    factory = set(positive)-HAND
    assert len(factory)==153 and len(HAND)==18 and len(positive)==171
    groups = defaultdict(list)
    for ref in sorted(factory):
        r = positive[ref]
        groups[tuple(r[k] for k in ['Manufacturer','MPN','Footprint','Value'])].append(ref)
    factory_bom, matching = [], []
    for (maker,mpn,footprint,value), refs in sorted(groups.items()):
        part_id,url = MATCHES.get(mpn,('',''))
        factory_bom.append(dict(Comment=value,Designator=','.join(refs),Footprint=footprint,
            Quantity=len(refs),Manufacturer=maker,MPN=mpn,**{'LCSC Part #':part_id}))
        matching.append(dict(Designator=','.join(refs),Manufacturer=maker,MPN=mpn,
            **{'LCSC Part #':part_id},Catalog_status='EXACT_CATALOG_ID_CHECKED' if part_id else 'UNVERIFIED',
            Catalog_date='2026-10-14' if part_id else '',Source_URL=url,
            Order_status='PENDING: stock, selected JLC service, footprint and rotation confirmation; no substitutions'))
    payload['assembly/jlc-smt-bom.csv'] = csv_bytes(factory_bom)
    payload['assembly/part-matching.csv'] = csv_bytes(matching)
    cpl = [dict(Designator=r['Ref'],**{'Mid X':r['PosX'],'Mid Y':r['PosY']},
                Rotation=f"{float(r['Rot'])%360:.6f}",Layer=r['Side'].title())
           for r in positions if r['Ref'] in factory]
    assert len(cpl)==153 and sum(r['Layer']=='Bottom' for r in cpl)==15
    payload['assembly/jlc-smt-cpl.csv'] = csv_bytes(cpl)
    hand = [dict(positive[ref],Process='USER_THT',Procurement_status=(
        'User drawing / same-batch EV3 connector; no verified procurement MPN; unpowered continuity and fit before motor use'
        if ref in {'J10','J11','J12','J13'} else 'Exact MPN required; quantity per board; stock unverified')) for ref in sorted(HAND)]
    payload['assembly/hand-solder-purchase.csv'] = csv_bytes(hand)
    payload['assembly/process-by-reference.csv'] = csv_bytes(process)
    payload['assembly/polarity-padmap.csv'] = csv_bytes(padmap)
    payload['assembly/do-not-populate.csv'] = csv_bytes([r for r in bom if r['Reference'] in {'C26','C36'}])
    payload['assembly/thermal-holes.csv'] = csv_bytes([dict(Reference=h['footprint_ref'],Pad=h['pad'],
        Native_X_mm=h['xy'][0],Native_Y_mm=h['xy'][1],Drill_mm=h['drill_mm'][0],Ring_mm=h['ring_mm'],
        Process='CAM: open via + stencil/acceptance OR targeted epoxy fill and cap; not ordinary ink plugging')
        for h in jlccheck['thermal_holes']])
    fabrication = {}
    for f in sorted((ROOT/'generated/electronics/fabrication-preview-NOT-RELEASED').iterdir()):
        if f.suffix in FAB_EXT:
            data = source(str(f.relative_to(ROOT)))
            fabrication[f.name] = data
            payload['fabrication/'+f.name] = data
    assert len(fabrication)==14
    payload['fabrication/gerber-drill-only.zip'] = archive(fabrication)
    for name in ['order-and-cam.md','assembly-and-polarity.md','bring-up.md']:
        copy('electronics/first-board/'+name,'docs/'+name)
    for name in ['assembly.png','assembly-bottom.png','pcb-top.png','pcb-bottom.png','schematic.pdf']:
        copy('generated/electronics/'+name,'drawings/'+name)
    firmware = 'quadcuber-a1-micropython-v1.27.0.uf2'
    copy('generated/electronics/firmware/'+firmware,'firmware/'+firmware)
    copy('electronics/first-board/package-readme.md','README.md')
    source('electronics/package_first_board.py')
    manifest = dict(package=NAME,status='ENGINEERING_FIRST_BOARD_CAM_CANDIDATE_NOT_PRODUCTION_RELEASE',
        design_source_commit=BASE,design_source_pcb_sha256=board_sha,
        delivery_commit_note='The containing Git commit identifies delivery; this manifest pins the immutable design commit to avoid a self-referential commit hash.',
        factory_placements=153,factory_top=138,factory_bottom=15,user_tht=18,
        mixed_process={'J5':'Factory SMT contacts plus four PTH shield legs; service confirmation required'},
        dnp=['C26','C36'],firmware_path='firmware/'+firmware,
        fabrication_note='Unchanged 11 Gerbers + 2 drills + job; risk silkscreen retained. No factory upload or order performed.',
        audit_note='Read-only audit of the same db20b98 native design; archived reports retain their original timestamps. 30/30 fabrication checks, ERC/DRC zero; physical and CAM checks remain pending.',
        immutable_design_files=immutable,design_baseline_sha256=baseline,source_sha256=dict(sorted(sources.items())),
        payload_sha256={k:sha(v) for k,v in sorted(payload.items())})
    payload['manifest.json'] = (json.dumps(manifest,indent=2,ensure_ascii=False)+'\n').encode()
    # Only write owned paths; no recursive deletion or discovery of arbitrary sibling files.
    for name,data in payload.items():
        dest=OUT/name
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(data)
    zipped=archive(payload)
    (OUT/(NAME+'.zip')).write_bytes(zipped)
    sums={**{k:sha(v) for k,v in payload.items()},NAME+'.zip':sha(zipped)}
    (OUT/'SHA256SUMS').write_text(''.join(f'{v}  {k}\n' for k,v in sorted(sums.items())))
    print(json.dumps({'package':str(OUT/(NAME+'.zip')),'sha256':sha(zipped),'factory':len(factory),'hand':len(HAND),'payload_files':len(payload)},indent=2))


if __name__=='__main__':
    main()
