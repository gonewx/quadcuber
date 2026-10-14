#!/usr/bin/env python3
"""Package the frozen 3cfff7c engineering board; never save or regenerate its design.
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
BASE = '3cfff7c8cb5a1b523186130fa96828cea1cd69d7'
NAME = 'quadcuber-A1-first-board-3cfff7c'
HAND = set('J1 J2 J3 J4 J10 J11 J12 J13 J20 J21 J22 J23 C2 C3 C102 C122 C142 C162'.split())
# Exact-MPN LCSC catalog pages (productModel and brand checked character by character).
# (part id, catalog date, LCSC page stock at that date). Missing MPNs are intentionally absent: no substitutes.
CATALOG = '2026-10-13'
MATCHES = {
    'TPS54302DDCR': ('C311983', '2026-10-14', None),
    'USB4105-GF-A': ('C3020560', '2026-10-14', None),
    'ABM8-272-T3': ('C20625731', CATALOG, 7245),
    'MF-MSMF050-2': ('C17313', CATALOG, 129420),
    'SRP1245A-100M': ('C2042471', CATALOG, 20),
    'TL3342F160QG': ('C2886898', CATALOG, 1083),
    'C0603C750J5GACTU': ('C2169965', CATALOG, 3600),
    'C0805C475K4PACTU': ('C2167163', CATALOG, 20),
    'LTST-C190KGKT': ('C125094', CATALOG, 99900),
    '0407008.WR': ('C1882503', CATALOG, 0),
    'SMBJ12A': ('C151251', CATALOG, 34700),
    'SMBJ12CA': ('C83849', CATALOG, 23490),
    'GRM1555C1H150JA01D': ('C76950', CATALOG, 55300),
    'GRM155R61C105KA12D': ('C77006', CATALOG, 0),
    'GRM155R71C104KA88D': ('C71629', CATALOG, 985800),
    'GRM21BR71C105KA01L': ('C77079', CATALOG, 1340),
    'GRM21BR71H104KA01L': ('C77082', CATALOG, 169680),
    'GRM32DR71E106KA12L': ('C77100', CATALOG, 350135),
    'GRM32ER71E226KE15L': ('C21397', CATALOG, 35030),
    'RP2040': ('C2040', CATALOG, 46380),
    'USBLC6-2SC6': ('C7519', CATALOG, 30105),
    'CSD18540Q5B': ('C86513', CATALOG, 0),
    'DRV8871DDAR': ('C75864', CATALOG, 8713),
    'LM74700QDBVRQ1': ('C2941042', CATALOG, 7),
    'SN74AHCT1G125DBVR': ('C7484', CATALOG, 27600),
    'SN74LVC2G17DBVR': ('C10429', CATALOG, 34555),
    'TLV75533PDBVR': ('C404027', CATALOG, 127295),
    'CRCW2512300RFKEG': ('C1854538', CATALOG, 25),
    'SS14-E3/61T': ('C47460', CATALOG, 174),
    'RC0402FR-071KL': ('C106235', CATALOG, 943400),
    'RC0402FR-0727RL': ('C138021', CATALOG, 0),
    'RC0603FR-07100KL': ('C14675', CATALOG, 8066900),
    'RC0603FR-07105KL': ('C141685', CATALOG, 33800),
    'RC0603FR-0710KL': ('C98220', CATALOG, 4354200),
    'RC0603FR-071KL': ('C22548', CATALOG, 9461100),
    'RC0603FR-07220RL': ('C107696', CATALOG, 26500),
    'RC0603FR-0743K2L': ('C137720', CATALOG, 15000),
    'RC0603FR-07511KL': ('C188257', CATALOG, 0),
    'RC0603FR-075K1L': ('C105580', CATALOG, 5967000),
    'RT0603BRD07100KL': ('C122538', CATALOG, 1055580),
    'RT0603BRD0713K3L': ('C861117', CATALOG, 460),
}
NOT_LISTED = {
    'W25Q16RVCNJQ': 'NOT LISTED on LCSC/JLC at catalog date (only RVSSJQ/RVSNJQ suffixes). Use JLC global sourcing or consigned parts; any suffix change requires flash review first.',
    'MF-MSMF110/16X-2': 'NOT LISTED on LCSC/JLC at catalog date (only /16-2 NRND, /24X-2, -2). Use JLC global sourcing or consigned parts; do not substitute /16-2.',
}
# Package-facing notes replace internal review references that are not shipped in this package.
HAND_NOTES = {
    'J1': ('Switchcraft', 'RASPC722X', 'Mating plug 5.5/2.1 mm center-positive (Switchcraft 762/762Z, 9.5 mm barrel). Pin 1 = center +9V, pin 2 = sleeve GND, pin 3 = sleeve shunt not connected. Regulated 9V only, <=5A continuous budget.'),
    'EV3': ('User-supplied', 'NO_MPN_SAME_BATCH_AS_USER_DRAWING', 'EV3 6-pin socket from the same batch as the user drawing; no procurement MPN; do not use a generic RJ12. Pins 1=M1 2=M2 3=GND 4=5V_ENC 5=TACHO A 6=TACHO B. Unpowered six-way continuity and fit check before connecting a motor.'),
    'CAP': (None, None, 'Polarity: pad 1 = + (VM), pad 2 = - (GND); match the can stripe to pad 2.'),
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
            raise RuntimeError(f'Frozen design differs from {BASE[:7]}: '+rel)
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
        part_id,date,stock = MATCHES.get(mpn,('','',None))
        url = f'https://www.lcsc.com/product-detail/{part_id}.html' if part_id else ''
        factory_bom.append(dict(Comment=value,Designator=','.join(refs),Footprint=footprint,
            Quantity=len(refs),Manufacturer=maker,MPN=mpn,**{'LCSC Part #':part_id}))
        status = ('PENDING: confirm JLC stock/service, footprint and rotation; no substitutions' if part_id else
                  'BLOCKER: '+NOT_LISTED[mpn])
        if stock is not None and stock < 100:
            status = f'LOW/ZERO LCSC STOCK ({stock}) at catalog date; confirm JLC availability, global sourcing or consignment. '+status
        matching.append(dict(Designator=','.join(refs),Manufacturer=maker,MPN=mpn,
            **{'LCSC Part #':part_id},Catalog_status='EXACT_CATALOG_ID_CHECKED' if part_id else 'NOT_LISTED',
            Catalog_date=date or CATALOG,LCSC_page_stock='' if stock is None else stock,Source_URL=url,
            Order_status=status))
    payload['assembly/jlc-smt-bom.csv'] = csv_bytes(factory_bom)
    payload['assembly/part-matching.csv'] = csv_bytes(matching)
    cpl = [dict(Designator=r['Ref'],**{'Mid X':r['PosX'],'Mid Y':r['PosY']},
                Rotation=f"{float(r['Rot'])%360:.6f}",Layer=r['Side'].title())
           for r in positions if r['Ref'] in factory]
    assert len(cpl)==153 and sum(r['Layer']=='Bottom' for r in cpl)==15
    payload['assembly/jlc-smt-cpl.csv'] = csv_bytes(cpl)
    hand = []
    for ref in sorted(HAND):
        row = dict(positive[ref],Process='USER_THT')
        key = 'EV3' if ref in {'J10','J11','J12','J13'} else 'CAP' if ref.startswith('C') else ref
        maker, mpn, note = HAND_NOTES.get(key,(None,None,''))
        if key=='EV3':
            row['Value'] = f'EV3 socket {row["Value"].split()[1]}'
        row.update(Manufacturer=maker or row['Manufacturer'],MPN=mpn or row['MPN'],Notes=note,
            Procurement_status='User sample; continuity and fit before motor use' if key=='EV3'
            else 'Exact MPN required; quantity per board; stock unverified')
        hand.append(row)
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
        fabrication_note='Unchanged 11 Gerbers + 2 drills + job from the 3cfff7c design (prototype silkscreen). No factory upload or order performed.',
        audit_note='Read-only audit of the same 3cfff7c native design; archived reports retain their original timestamps. 30/30 fabrication checks, ERC/DRC zero; physical and CAM checks remain pending.',
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
