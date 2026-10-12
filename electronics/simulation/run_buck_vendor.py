#!/usr/bin/env python3
"""TPS54302 official-model harness. Requires locally obtained TI unencrypted LIB.
Never treats model acquisition or parse success as a passing transient simulation.
"""
import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path
import numpy as np
from run_boundaries import ROOT, C, source_contract

def main():
 p=argparse.ArgumentParser();p.add_argument('--model',type=Path,required=True);p.add_argument('--ngspice',default='ngspice');a=p.parse_args()
 model=a.model.resolve();text=model.read_text(errors='strict')
 headers=re.findall(r'^\.subckt\s+(TPS54302\S*)\s+([^\r\n]+)',text,re.I|re.M)
 candidates=[(name,pins.split()) for name,pins in headers if len(pins.split())==6]
 if len(candidates)!=1:sys.exit('Need one TPS54302 six-pin .SUBCKT; inspect original file, do not guess pin order.')
 name,pins=candidates[0]
 if {x.upper() for x in pins}!={'VIN','EN','SW','BOOT','FB','GND'}:sys.exit(f'Unsupported original pin labels: {pins}; explicit source review required.')
 for ref,value in {'C20':'10u/25V','C30':'10u/25V','C23':'22u/25V','C24':'22u/25V','C33':'22u/25V','C34':'22u/25V','R20':'49.9','R30':'49.9','R21':'100k','R31':'100k','R22':'13.3k','R32':'13.3k','R23':'511k','R33':'511k','R24':'105k','R34':'105k','C25':'75p','C35':'75p','L1':'10uH 9A Isat16A','L2':'10uH 9A Isat16A'}.items():assert C[ref]['value']==value,ref
 out=ROOT/'generated/electronics/simulation/buck-vendor';out.mkdir(parents=True,exist_ok=True)
 meta=source_contract();meta.update(model_sha256=hashlib.sha256(model.read_bytes()).hexdigest(),model_source='https://www.ti.com/lit/zip/slvmbl9',subckt=name,pins=pins,simulator=subprocess.check_output([a.ngspice,'--version'],text=True),cases=[])
 meta['state']='RUNNING'
 (out/'run-status.json').write_text(json.dumps(meta,indent=2)+'\n')
 # 0.4 includes deliberately severe unknown DC-bias derating; it is not Murata characterization.
 for vin in [8.82,9,9.18]:
  for cf in [.4,.8,1.2]:
   case=f'VIN{vin:g}_C{cf:g}';folder=out/case;folder.mkdir(exist_ok=True)
   lines=['Quadcuber actual dual TPS54302 BOM, official model required',f'.include "{model}"',f'VIN vm 0 PWL(0 0 1m {vin:g})']
   for ch,light in [(1,.25),(2,.05)]:
    pre=f'b{ch}';nodes={'VIN':'vm','GND':'0','EN':pre+'en','SW':pre+'sw','BOOT':pre+'boot','FB':pre+'fb'}
    lines += [f'X{ch} '+ ' '.join(nodes[x.upper()] for x in pins)+f' {name}',f'C{ch}in vm 0 {10e-6*cf:g}',f'C{ch}hf vm 0 100n',f'R{ch}boot {pre}boot {pre}bc 49.9',f'C{ch}boot {pre}bc {pre}sw 100n',f'L{ch} {pre}sw {pre}ld 10u',f'R{ch}dcr {pre}ld {pre}out 0.0214',f'R{ch}esr {pre}out {pre}cap 0.003',f'C{ch}out {pre}cap 0 {44e-6*cf:g}',f'R{ch}hi {pre}out {pre}fb 100k',f'R{ch}lo {pre}fb 0 13.3k',f'C{ch}ff {pre}out {pre}fb 75p',f'R{ch}enhi vm {pre}en 511k',f'R{ch}enlo {pre}en 0 105k',f'V{ch}load {pre}out {pre}load 0',f'B{ch}load {pre}load 0 I=min(max(v({pre}out)/4,0),1)*({light:g}+(1.5-{light:g})*(time>0.012 && time<0.018))']
   lines += ['.options reltol=1e-4 method=gear','.control','set wr_vecnames','set wr_singlescale','tran 100n 25m 0 100n','wrdata waveform.txt v(vm) v(b1out) v(b2out) i(L1) i(L2) v(b1en) v(b2en)','quit','.endc','.end']
   (folder/'test.cir').write_text('\n'.join(lines)+'\n');(folder/'.spiceinit').write_text('set ngbehavior=ps\n')
   # No model transformation. Any ngspice incompatibility remains an explicit failure.
   (folder/'waveform.txt').unlink(missing_ok=True)
   r=subprocess.run([a.ngspice,'-b','test.cir'],cwd=folder,text=True,capture_output=True,timeout=300)
   (folder/'ngspice.log').write_text(r.stdout+r.stderr)
   status={'case':case,'completed':False,'passed':False}
   if r.returncode==0 and 'Error:' not in r.stderr and (folder/'waveform.txt').exists():
    d=np.loadtxt(folder/'waveform.txt',skiprows=1)
    if d.ndim==2 and d.shape[1]==8 and d[-1,0]>=.02499 and np.all(np.isfinite(d)):
     settled=d[d[:,0]>=.010];status.update(completed=True,min_V=float(settled[:,2:4].min()),max_V=float(d[:,2:4].max()),max_inductor_A=float(abs(d[:,4:6]).max()),start_reached_4V75=bool((d[d[:,0]<=.010,2:4].max(axis=0)>=4.75).all()))
     status['passed']=status['start_reached_4V75'] and status['min_V']>=4.75 and status['max_V']<=5.25 and status['max_inductor_A']<6
   meta['cases'].append(status)
   (out/'run-status.json').write_text(json.dumps(meta,indent=2)+'\n')
   print(json.dumps(status),flush=True)
   if not status['completed']:sys.exit('Vendor model did not run to completion. See ngspice.log; no compatibility claim.')
 meta['state']='COMPLETED'
 (out/'run-status.json').write_text(json.dumps(meta,indent=2)+'\n')
 if not all(x['passed'] for x in meta['cases']):sys.exit('One or more acceptance criteria failed.')
if __name__=='__main__':
 try:main()
 except (Exception,SystemExit) as exc:
  if isinstance(exc,SystemExit) and exc.code in (None,0):raise
  path=ROOT/'generated/electronics/simulation/buck-vendor/run-status.json'
  path.parent.mkdir(parents=True,exist_ok=True)
  state=json.loads(path.read_text()) if path.exists() else {}
  state.update(state='FAILED_OR_BLOCKED',error=str(exc),manufacturing_released=False)
  path.write_text(json.dumps(state,indent=2)+'\n')
  raise
