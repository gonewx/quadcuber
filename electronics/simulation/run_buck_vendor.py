#!/usr/bin/env python3
"""TPS54302 official-model harness. Requires locally obtained TI unencrypted LIB.
Never treats model acquisition or parse success as a passing transient simulation.
"""
import argparse, difflib, gzip, hashlib, json, re, subprocess, sys, time
from pathlib import Path
import numpy as np
from run_boundaries import ROOT, C, source_contract

REVISION="direct-boot-precision-v1"
OUT=ROOT/"generated/electronics/simulation"/("buck-vendor-"+REVISION)

def parse_model(text):
 headers=re.findall(r'^\.subckt\s+(TPS54302\S*)\s+([^\r\n]+)',text,re.I|re.M)
 candidates=[(name,re.split(r'\s+PARAMS:',body,flags=re.I)[0].split()) for name,body in headers]
 if len(candidates)!=1:raise ValueError('Need exactly one TPS54302 subcircuit')
 name,pins=candidates[0]
 # Reviewed against slvmbl9a LIB header; PH is switching node, VSENSE feedback.
 if [x.upper() for x in pins]!=['BOOT','EN','GND','PH','VIN','VSENSE']:
  raise ValueError(f'Unreviewed original pin order: {pins}')
 return name,pins

def adapt_model(text):
 old='V(YTD) > 0.5 ^ V(IN) > .5'
 if text.count(old)!=1:raise ValueError('Expected exactly one reviewed PSpice XOR expression')
 return text.replace(old,'((V(YTD) > 0.5) != (V(IN) > .5))')

def assess(d,log,returncode,stop=.025):
 status={'completed':False,'passed':False,'returncode':returncode}
 failure=re.search(r'error|aborted|timestep too small|fatal',log,re.I)
 if failure:status['log_error']=failure.group(0)
 if d is None:return status
 if d.ndim!=2 or d.shape[1]!=8 or not np.all(np.isfinite(d)):return status
 status['last_time_s']=float(d[-1,0]);status['points']=len(d)
 if returncode or failure or d[-1,0]<stop-1e-9 or d[0,0]>1e-9 or np.any(np.diff(d[:,0])<=0):return status
 settled=d[d[:,0]>=.010]
 if not len(settled):return status
 status.update(completed=True,min_V=float(settled[:,2:4].min()),max_V=float(d[:,2:4].max()),max_inductor_A=float(abs(d[:,4:6]).max()),start_reached_4V75=bool((d[d[:,0]<=.010,2:4].max(axis=0)>=4.75).all()))
 status['rails']={}
 for ch in (1,2):
  v=d[:,ch+1];status['rails'][f'5V_{"A" if ch==1 else "B"}']={'minimum_after_10ms_V':float(v[d[:,0]>=.010].min()),'maximum_V':float(v.max()),'final_V':float(v[-1])}
 status['passed']=status['start_reached_4V75'] and status['min_V']>=4.75 and status['max_V']<=5.25 and status['max_inductor_A']<6
 return status

def initialize_run(out):
 out.mkdir(parents=True,exist_ok=True)
 (out/'run-status.json').write_text(json.dumps({'state':'INITIALIZING','cases':[], 'manufacturing_released':False},indent=2)+'\n')

def reset_case_outputs(folder):
 for name in ['waveform.txt','waveform.txt.gz']:(folder/name).unlink(missing_ok=True)

def buck_source_contract(parts):
 for ch in (1,2):
  base=10+10*ch;pre=f'B{ch}_'
  assert f'R{base}' not in parts, 'BOOT series resistor must be absent'
  assert parts[f'C{base+2}']['value']=='100n'
  assert parts[f'C{base+2}']['pins']=={'1':pre+'BOOT','2':pre+'SW'}
  assert parts[f'U{ch+1}']['pins']['6']==pre+'BOOT'
  assert parts[f'U{ch+1}']['pins']['2']==pre+'SW'
  for offset,value,mpn,nets in [(1,'100k','RT0603BRD07100KL',{'5V_'+('A' if ch==1 else 'B'),pre+'FB'}),(2,'13.3k','RT0603BRD0713K3L',{pre+'FB','GND'})]:
   part=parts[f'R{base+offset}']
   assert part['value']==value and part['mpn']==mpn,part['ref']
   assert set(part['pins'].values())==nets,part['ref']
 assert not any(net and net.endswith('BOOT_CAP') for part in parts.values() for net in part['pins'].values())
 return {'revision':REVISION,'bootstrap':'100n directly BOOT-SW; no series resistor','feedback_tolerance':0.001,'dynamic_validation':'PENDING'}

def case_lines(name,pins,vin,cf):
 lines=[f'VIN vm 0 PWL(0 0 1m {vin:g})']
 for ch,light in [(1,.25),(2,.05)]:
  pre=f'b{ch}';nodes={'VIN':'vm','GND':'0','EN':pre+'en','PH':pre+'sw','BOOT':pre+'boot','VSENSE':pre+'fb'}
  lines += [f'X{ch} '+ ' '.join(nodes[x.upper()] for x in pins)+f' {name}',f'C{ch}in vm 0 {10e-6*cf:g}',f'C{ch}hf vm 0 100n',f'C{ch}boot {pre}boot {pre}sw 100n',f'L{ch} {pre}sw {pre}ld 10u',f'R{ch}dcr {pre}ld {pre}out 0.0214',f'R{ch}esr {pre}out {pre}cap 0.003',f'C{ch}out {pre}cap 0 {44e-6*cf:g}',f'R{ch}hi {pre}out {pre}fb 100k',f'R{ch}lo {pre}fb 0 13.3k',f'C{ch}ff {pre}out {pre}fb 75p',f'R{ch}enhi vm {pre}en 511k',f'R{ch}enlo {pre}en 0 105k',f'V{ch}load {pre}out {pre}load 0',f'B{ch}load {pre}load 0 I=min(max(v({pre}out)/4,0),1)*({light:g}+(1.5-{light:g})*(time>0.012 && time<0.018))']
 return lines

def main():
 p=argparse.ArgumentParser();p.add_argument('--model',type=Path,required=True);p.add_argument('--ngspice',default='ngspice');p.add_argument('--vin',type=float,nargs='+',default=[8.82,9,9.18]);p.add_argument('--cap-factor',type=float,nargs='+',default=[.4,.8,1.2]);p.add_argument('--timeout',type=float,default=180);p.add_argument('--no-adapt',action='store_true');p.add_argument('--method',choices=['trap','gear'],default='trap');a=p.parse_args()
 out=OUT;initialize_run(out)
 buck_source_contract(C)
 original=a.model.resolve();text=original.read_text(errors='strict');name,pins=parse_model(text);original_hash=hashlib.sha256(original.read_bytes()).hexdigest();model=original
 if original_hash!='52a568f08f1eed44961238a1ff10b68c2ce1faa1cdf2c24659b17b1f820f0026':raise ValueError('Unreviewed model hash; do not silently use another revision')
 for ref,value in {'C20':'10u/25V','C30':'10u/25V','C23':'22u/25V','C24':'22u/25V','C33':'22u/25V','C34':'22u/25V','R21':'100k','R31':'100k','R22':'13.3k','R32':'13.3k','R23':'511k','R33':'511k','R24':'105k','R34':'105k','C25':'75p','C35':'75p','L1':'10uH 9A Isat16A','L2':'10uH 9A Isat16A'}.items():assert C[ref]['value']==value,ref
 out=OUT;out.mkdir(parents=True,exist_ok=True)
 transformations=[]
 if not a.no_adapt:
  adapted=adapt_model(text);model=ROOT/'output/electronics/ti-model/TPS54302_TRANS.ngspice.LIB';model.parent.mkdir(parents=True,exist_ok=True);model.write_text(adapted)
  transformations=['CRLF to LF during text serialization','MONONEG_PS: PSpice boolean XOR ^ -> parenthesized boolean !=; truth table independently checked']
  (out/'compatibility.patch').write_text(''.join(difflib.unified_diff(text.splitlines(True),adapted.splitlines(True),fromfile='TI-original',tofile='ngspice-adapted')))
 meta=source_contract();meta.update(buck_source_contract(C));meta.update(original_model_sha256=original_hash,model_sha256=hashlib.sha256(model.read_bytes()).hexdigest(),model_source='https://www.ti.com/lit/zip/slvmbl9',subckt=name,pins=pins,simulator=subprocess.check_output([a.ngspice,'--version'],text=True),cases=[])
 meta.update(state='RUNNING',pin_mapping={'PH':'SW','VSENSE':'FB'},model_transformations=transformations,compatibility='ngbehavior=ps; analog.cm and xtradev.cm required',method=a.method,timeout_s=a.timeout,baseline_git=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),working_tree_revision=REVISION,thresholds={'settled_min_V':4.75,'all_time_max_V':5.25,'startup_deadline_s':.010,'inductor_peak_A':6,'stop_s':.025},manufacturing_released=False)
 (out/'run-status.json').write_text(json.dumps(meta,indent=2)+'\n')
 # Ideal VM clamps the input capacitors: no input-impedance/ripple validation here.
 # 0.4 includes deliberately severe unknown DC-bias derating; it is not Murata characterization.
 for vin in a.vin:
  for cf in a.cap_factor:
   case=f'VIN{vin:g}_C{cf:g}';folder=out/case;folder.mkdir(exist_ok=True)
   lines=['Quadcuber direct-BOOT precision-feedback revision',f'.include "{model}"']+case_lines(name,pins,vin,cf)
   lines += [f'.options reltol=1e-4 method={a.method}','.control','set wr_vecnames','set wr_singlescale','tran 100n 25m 0 100n','wrdata waveform.txt v(vm) v(b1out) v(b2out) i(L1) i(L2) v(b1en) v(b2en)','quit','.endc','.end']
   (folder/'test.cir').write_text('\n'.join(lines)+'\n');(folder/'.spiceinit').write_text('set ngbehavior=ps\n')
   # Only the reviewed logical XOR adaptation; no protection or device-parameter changes.
   reset_case_outputs(folder)
   started=time.monotonic();rc=0
   with (folder/'ngspice.log').open('w') as log:
    try:r=subprocess.run([a.ngspice,'-b','test.cir'],cwd=folder,text=True,stdout=log,stderr=subprocess.STDOUT,timeout=a.timeout);rc=r.returncode
    except subprocess.TimeoutExpired:rc=124;log.write('\nHARNESS TIMEOUT: incomplete; no pass claim.\n')
   logtext=(folder/'ngspice.log').read_text(errors='replace');d=None
   if (folder/'waveform.txt').exists():
    try:d=np.loadtxt(folder/'waveform.txt',skiprows=1)
    except ValueError:pass
   status=assess(d,logtext,rc);status.update(case=case,elapsed_s=round(time.monotonic()-started,3))
   if (folder/'waveform.txt').exists():
    (folder/'waveform.txt.gz').write_bytes(gzip.compress((folder/'waveform.txt').read_bytes(),mtime=0));(folder/'waveform.txt').unlink()
   meta['cases'].append(status)
   (out/'run-status.json').write_text(json.dumps(meta,indent=2)+'\n')
   print(json.dumps(status),flush=True)

 meta['vendor_model_cases_attempted']=len(meta['cases']);meta['vendor_model_cases_completed']=sum(x['completed'] for x in meta['cases']);meta['vendor_model_cases_passed']=sum(x['passed'] for x in meta['cases'])
 meta['state']='COMPLETED' if all(x['completed'] for x in meta['cases']) else 'INCOMPLETE_NUMERICAL_FAILURE'
 (out/'run-status.json').write_text(json.dumps(meta,indent=2)+'\n')
 if not all(x['passed'] for x in meta['cases']):sys.exit('One or more acceptance criteria failed.')
if __name__=='__main__':
 try:main()
 except (Exception,SystemExit) as exc:
  if isinstance(exc,SystemExit) and exc.code in (None,0):raise
  path=OUT/'run-status.json'
  path.parent.mkdir(parents=True,exist_ok=True)
  state=json.loads(path.read_text()) if path.exists() else {}
  state.update(error=str(exc),manufacturing_released=False)
  if state.get('state') not in ['INCOMPLETE_NUMERICAL_FAILURE','COMPLETED']:state['state']='FAILED_OR_BLOCKED'
  path.write_text(json.dumps(state,indent=2)+'\n')
  raise
