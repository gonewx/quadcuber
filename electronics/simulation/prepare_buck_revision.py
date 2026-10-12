#!/usr/bin/env python3
"""Build versioned, NOT_RUN PSpice handoff from the current reviewed topology."""
import csv
import hashlib
import json
from pathlib import Path
from run_buck_vendor import C, ROOT, REVISION, buck_source_contract, case_lines
from run_boundaries import source_contract

PINS=['BOOT','EN','GND','PH','VIN','VSENSE']
DEST=Path(__file__).parent/('pspice-handoff-'+REVISION)

def main():
 contract=buck_source_contract(C)
 DEST.mkdir(exist_ok=True)
 cases=[]
 for vin in (8.82,9,9.18):
  for cf in (.4,.8,1.2):
   name=f'VIN{vin:g}_C{cf:g}'
   lines=case_lines('TPS54302_TRANS',PINS,vin,cf)
   # PSpice behavioral current source syntax, with identical load schedule.
   for ch,light in ((1,.25),(2,.05)):
    i=next(i for i,line in enumerate(lines) if line.startswith(f'B{ch}load '))
    lines[i]=f'G{ch}load b{ch}load 0 VALUE = {{LIMIT(V(b{ch}out)/4,0,1)*({light:g}+(1.5-{light:g})*IF(TIME>12m,IF(TIME<18m,1,0),0))}}'
   body='\n'.join([f'A1 {REVISION} {name}: PSPICE HANDOFF ONLY - NOT RUN', '* Use the unchanged, independently obtained TI model; not bundled.', '.LIB "TPS54302_TRANS.LIB"',*lines,'.OPTIONS RELTOL=1e-4 ABSTOL=10n VNTOL=10u ITL1=1500 ITL2=400 ITL4=100','.TEMP 27','.TRAN 100n 25m 0 20n','.PROBE V(vm) V(b1out) V(b2out) I(L1) I(L2) V(b1en) V(b2en)','.PRINT TRAN V(vm) V(b1out) V(b2out) I(L1) I(L2) V(b1en) V(b2en)','.END',''])
   for ch in (1,2):
    assert f'C{ch}boot b{ch}boot b{ch}sw 100n' in body
    assert f'b{ch}bc' not in body and f'R{ch}boot ' not in body
   (DEST/(name+'.cir')).write_text(body)
   cases.append({'case':name,'vin_V':vin,'cap_factor':cf,'state':'NOT_RUN','deck_sha256':hashlib.sha256(body.encode()).hexdigest()})
 meta=source_contract();meta.update(contract)
 meta.update(state='STATIC_CONTRACT_PASS_DYNAMIC_NOT_RUN', cases=cases, manufacturing_released=False, hardware_validated=False,
  original_model_sha256='52a568f08f1eed44961238a1ff10b68c2ce1faa1cdf2c24659b17b1f820f0026',
  source='https://www.ti.com/lit/zip/slvmbl9',feedback_parts={r:{k:C[r][k] for k in ('value','mpn','pins')} for r in ('R21','R22','R31','R32')},
  static_feedback_range_V=[.581*(1+100*.999/(13.3*1.001)),.611*(1+100*1.001/(13.3*.999))],
  limitations=['Static feedback range includes Vref and initial resistor tolerance only; excludes TCR, aging, line/load, FB bias and transients.', 'Nominal SPICE resistors do not implement a tolerance sweep.', 'Output ESR 3mOhm and capacity factors are assumptions, not measured Murata DC-bias data.', 'Ideal input source excludes input impedance/ripple validation.', 'Historical 49.9-ohm BOOT simulations are not results for this revision.'])
 (DEST/'static-validation.json').write_text(json.dumps(meta,indent=2)+'\n')
 with (DEST/'cases-and-results.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=['case','vin_V','cap_factor','state','deck_sha256'],lineterminator='\n');w.writeheader();w.writerows(cases)
 print(json.dumps({'directory':str(DEST),'cases':len(cases),'state':meta['state']}))

if __name__=='__main__':main()
