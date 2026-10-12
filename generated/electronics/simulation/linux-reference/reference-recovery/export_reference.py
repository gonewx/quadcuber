"""Export auditable DSN-derived reference circuits; no solver or model changes."""
import csv
import hashlib
import json
from pathlib import Path
import re
import shlex

ROOT = Path(__file__).resolve().parent
OFFICIAL = Path('/workspace/tool-verification/ti-model/TPS54302_PSPICE_TRANS')
symbols, packages, pages = {}, {}, {}
current = None
variant = False
for line in (ROOT / 'parsed-reference.txt').read_text().splitlines():
    a = shlex.split(line)
    if not a:
        continue
    tag = a.pop(0)
    if tag == 'PACKAGE':
        current = packages[a[0]] = {'props': {}, 'devices': [], 'variants': []}
    elif tag == 'PACKAGE_VARIANT':
        current = {'props': {}, 'devices': []}
        packages[a[0]]['variants'].append(current)
    elif tag in ('DEVICE', 'VARDEVICE'):
        current['devices'].append(a[2:] if tag == 'DEVICE' else a)
    elif tag == 'SYMBOL':
        current = symbols[a[0]] = {'props': {}, 'pins': {}, 'variants': []}
    elif tag == 'SYMBOL_VARIANT':
        current = {'props': {}, 'pins': {}}
        symbols[a[0]]['variants'].append(current)
    elif tag in ('SYMPROP', 'PKGPROP', 'VARPROP', 'PROP'):
        current['props'][a[0]] = a[1]
    elif tag in ('SYMPIN', 'VARPIN'):
        current['pins'][int(a[0])] = a[1]
    elif tag == 'PAGE':
        page = pages[a[0]] = {'nets': {}, 'wires': [], 'instances': [], 'globals': []}
    elif tag == 'NET':
        page['nets'][int(a[0])] = a[1]
    elif tag == 'WIRE':
        page['wires'].append(list(map(int, a)))
    elif tag == 'INSTANCE':
        current = {'dbid': int(a[0]), 'ref': a[1], 'value': a[2], 'symbol': a[3],
                   'unit': int(a[4]), 'props': {}, 'pins': []}
        page['instances'].append(current)
    elif tag == 'PIN':
        current['pins'].append(dict(zip(('index', 'x', 'y', 'wordA', 'wordB'), map(int, a))))
    elif tag == 'GLOBAL':
        page['globals'].append(a)

# All cached variants must be electrically equivalent before this exporter uses
# the default cache entry. Geometry alone is not used to invent pin identities.
for name, s in symbols.items():
    for v in s['variants']:
        assert s['props'] == v['props'] and s['pins'] == v['pins'], ('symbol variant', name)
for name, p in packages.items():
    for v in p['variants']:
        assert p['props'] == v['props'] and p['devices'] == v['devices'], ('package variant', name)

audit = []
summary = {}
for name, page in pages.items():
    for wire in page['wires']:
        n, x1, y1, x2, y2 = wire
        assert x1 == x2 or y1 == y2, ('non-orthogonal wire', wire)
        page['nets'].setdefault(n, 'N' + str(n))
    covered = set()
    for instance in page['instances']:
        sym = symbols[instance['symbol']]
        pkg = packages[instance['symbol'].split('.')[0]]
        effective = {**sym['props'], **pkg['props'], **instance['props']}
        instance['effective_props'] = effective
        for pin in instance['pins']:
            assert pin['index'] > 0, ('NC or absent pin index', instance['ref'], pin)
            slot = pin['index'] - 1
            assert slot in sym['pins'], ('unknown symbol slot', instance['ref'], pin)
            pin['symbol_name'] = sym['pins'][slot]
            pin['package_number'] = pkg['devices'][instance['unit']][slot]
            x, y = pin['x'], pin['y']
            touching = [(wi, w[0]) for wi, w in enumerate(page['wires'])
                        if min(w[1], w[3]) <= x <= max(w[1], w[3])
                        and min(w[2], w[4]) <= y <= max(w[2], w[4])]
            netids = {n for wi, n in touching}
            assert len(netids) == 1, ('ambiguous/unconnected pin', name, instance['ref'], pin, netids)
            pin['net_id'] = netids.pop()
            pin['net'] = page['nets'][pin['net_id']]
            covered.add(pin['net_id'])
            audit.append([name, instance['ref'], instance['value'], pin['index'],
                          pin['symbol_name'], pin['package_number'], x, y,
                          pin['net_id'], pin['net'], ','.join(str(wi) for wi, _ in touching)])
        assert len(instance['pins']) == len(sym['pins']), ('missing instance pins', instance['ref'])
    assert covered == {w[0] for w in page['wires']}, ('wire net without component', name)
    # Each wire ID must form a connected geometrical network (joins at endpoints
    # or points on axis-aligned segments). This checks all 53/54 wire records.
    for netid in covered:
        wires = [w for w in page['wires'] if w[0] == netid]
        seen = {0}
        while True:
            previous = set(seen)
            for j, a in enumerate(wires):
                for i in list(seen):
                    b = wires[i]
                    if (max(min(a[1], a[3]), min(b[1], b[3])) <= min(max(a[1], a[3]), max(b[1], b[3]))
                            and max(min(a[2], a[4]), min(b[2], b[4])) <= min(max(a[2], a[4]), max(b[2], b[4]))):
                        seen.add(j)
            if seen == previous:
                break
        # Ground can have separate geometry joined by global ground symbols.
        if page['nets'][netid] != '0':
            assert len(seen) == len(wires), ('disconnected geometry same net', name, netid)

    result = [f'* DSN-derived TI TPS54302 {name} reference testbench',
              '* Locally reconstructed from original DSN by official KiCad parser;',
              '* not an export made by Cadence. See pin-connectivity.csv and recovery-audit.json.',
              '* Original model file is included read-only without modifications.',
              f'.LIB "{OFFICIAL / "TPS54302_TRANS.LIB"}"']
    for i in page['instances']:
        p = i['effective_props']
        pins = {pin['symbol_name']: pin['net'] for pin in i['pins']}
        ref, value, symbol = i['ref'], i['value'], i['symbol']
        result.append(f'* DSN instance {i["dbid"]}: {ref}; template: {p["PSpiceTemplate"]}')
        if symbol == 'R.Normal':
            assert not p.get('TOLERANCE')
            line = f'R_{ref} {pins["1"]} {pins["2"]} {value}'
        elif symbol == 'C.Normal':
            assert not p.get('TOLERANCE')
            line = f'C_{ref} {pins["1"]} {pins["2"]} {value}'
            if p.get('IC'):
                line += f' IC={p["IC"]}'
        elif symbol == 'LDCR.Normal':
            assert value == 'LDCR'
            line = f'X_{ref} {pins["1"]} {pins["2"]} LDCR PARAMS: L={p["L"]} DCR={p["DCR"]} IC={p["IC"]}'
        elif symbol == 'CESR_1.Normal':
            assert value == 'CESR'
            line = f'X_{ref} {pins["1"]} {pins["2"]} CESR PARAMS: C={p["C"]} ESR={p["ESR"]} IC={p.get("IC") or "0"} X={p["X"]}'
        elif symbol == 'TPS54302DDC_TRANS.Normal':
            order = ('BOOT', 'EN', 'GND', 'SW', 'VIN', 'FB')
            line = f'X_{ref} ' + ' '.join(pins[n] for n in order) + f' {value} PARAMS: STEADY_STATE={p["STEADY_STATE"]}'
        elif symbol == 'VPULSE.Normal':
            assert not p.get('AC') and not p.get('DC')
            line = f'V_{ref} {pins["+"]} {pins["-"]} PULSE(' + ' '.join(p[k] for k in ('V1', 'V2', 'TD', 'TR', 'TF', 'PW', 'PER')) + ')'
        elif symbol in ('VDC.Normal', 'IDC.Normal'):
            line = symbol[0] + f'_{ref} {pins["+"]} {pins["-"]} DC {p["DC"]}'
        elif symbol == 'IC1.Normal':
            line = f'.IC V({pins["+"]})={value}'
        else:
            raise AssertionError(('unsupported symbol', symbol))
        result.append(line)
    profile = (OFFICIAL / 'TPS54302_TRANS-PSpiceFiles' / name / 'trans.sim').read_text()
    block = re.search(r'@Analysis: 0 1\n(.*?)@End Analysis', profile, re.S).group(1)
    fields = dict(re.findall(r'^\+(\d) "([^"]*)"', block, re.M))
    assert '+0 0 0 0' in block
    options_block = re.search(r'@Analysis: 11 1\n(.*?)@End Analysis', profile, re.S).group(1)
    profile_options = dict(re.findall(r'^\+ (ABSTOL|VNTOL|ITL1|ITL2|ITL4) \"([^\"]+)\"', options_block, re.M))
    assert profile_options == {'ABSTOL': '10n', 'VNTOL': '10u', 'ITL1': '1500', 'ITL2': '400', 'ITL4': '100'}, profile_options
    result += ['* Analysis restored from original trans.sim; no UIC requested.',
               '.OPTIONS ABSTOL=10n VNTOL=10u ITL1=1500 ITL2=400 ITL4=100',
               f'.TRAN 0 {fields["0"]} {fields["2"]} {fields["3"]}', '.PROBE', '.END']
    (ROOT / (name + '-recovered.cir')).write_text('\n'.join(result) + '\n')
    summary[name] = {'instances': len(page['instances']), 'pins': sum(len(i['pins']) for i in page['instances']),
                     'wires': len(page['wires']), 'nets_including_unnamed': len(page['nets']),
                     'profile_analysis': fields}

with (ROOT / 'pin-connectivity.csv').open('w') as f:
    w = csv.writer(f)
    w.writerow(['view', 'reference', 'value', 'placed_pin_index', 'symbol_pin_name', 'package_pin_number',
                'x_dbu', 'y_dbu', 'net_database_id', 'net_name', 'touching_wire_record_indices'])
    w.writerows(audit)
(ROOT / 'recovery-audit.json').write_text(json.dumps({'summary': summary, 'symbols': symbols,
    'packages': packages, 'pages': pages, 'official_library_sha256': hashlib.sha256((OFFICIAL/'TPS54302_TRANS.LIB').read_bytes()).hexdigest(),
    'direct_execution_blocker': {'dsn_model_name': 'TPS54302DDC_TRANS',
        'available_library_subcircuit': 'TPS54302_TRANS',
        'dsn_template_order': ['BOOT', 'EN', 'GND', 'SW', 'VIN', 'FB'],
        'library_declaration_order': ['BOOT', 'EN', 'GND', 'PH', 'VIN', 'VSENSE'],
        'resolution': 'Separate transparent alias wrapper required; original DSN-derived circuit and original LIB are intentionally unchanged.'}}, indent=2))
print(json.dumps(summary, indent=2))
