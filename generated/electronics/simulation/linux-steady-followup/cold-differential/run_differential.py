from pathlib import Path
import subprocess,time,json,hashlib,csv,difflib
root=Path(__file__).parent;ref=root.parent/'xyce-reference'
model=ref/'TPS54302_TRANS.xyce-init.LIB';alias=ref/'ti-name-alias.lib'
cases=[('startup_state1','Startup','X_U1 BOOT EN 0 SW VIN VFB TPS54302DDC_TRANS PARAMS: STEADY_STATE=0','X_U1 BOOT EN 0 SW VIN VFB TPS54302DDC_TRANS PARAMS: STEADY_STATE=1'),('startup_dc12','Startup','V_Vin VIN 0 PULSE(0 12 100u 10u 10u 1 2)','V_Vin VIN 0 DC 12'),('steady_state0','Steady_State','X_U1 BOOT EN 0 SW VIN VFB TPS54302DDC_TRANS PARAMS: STEADY_STATE=1','X_U1 BOOT EN 0 SW VIN VFB TPS54302DDC_TRANS PARAMS: STEADY_STATE=0')]
results=[]
for name,view,old,new in cases:
 d=root/name;d.mkdir(exist_ok=True)
 original=(ref/view/'init-compatible-driver.cir').read_text();assert original.count(old)==1
 s=original.replace(old,new).replace('.INCLUDE "../ti-name-alias.lib"',f'.INCLUDE "{alias}"')
 lines=s.splitlines();newlines=[]
 for l in lines:
  if l.startswith('.TRAN '):l='.TRAN 20n 800u 0 20n'
  if l.startswith('.PRINT '):l+=' V(X_U1:XCORE:SS_TR) V(X_U1:XCORE:VREF_GM) V(X_U1:XCORE:U5_LOW_CLMP) V(X_U1:XCORE:N16888001) V(X_U1:XCORE:U10_N16864604) V(X_U1:XCORE:HICCUP) V(X_U1:XCORE:U11_ENAB)'
  newlines.append(l)
 s='\n'.join(newlines)+'\n';(d/'driver.cir').write_text(s)
 (d/'driver.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile=view+'/init-compatible-driver.cir',tofile=name+'/driver.cir')))
 start=time.monotonic()
 with (d/'stdout.log').open('w') as f:
  try:r=subprocess.run(['/workspace/tools/xyce-7.10/bin/Xyce','driver.cir'],cwd=d,stdout=f,stderr=subprocess.STDOUT,timeout=110);code=r.returncode
  except subprocess.TimeoutExpired:code='timeout'
 rec={'case':name,'base_reference':view,'scientific_change':{'from':old,'to':new},'returncode':code,'elapsed_s':time.monotonic()-start,'requested_stop_s':.0008,'model_sha256':hashlib.sha256(model.read_bytes()).hexdigest(),'alias_sha256':hashlib.sha256(alias.read_bytes()).hexdigest()}
 cp=d/'driver.cir.csv'
 if cp.exists():
  with cp.open() as f:rows=[{k:float(v) for k,v in r.items()} for r in csv.DictReader(f)]
  rec['rows']=len(rows)
  if rows:
   rec['first']=rows[0];rec['last']=rows[-1];rec['completed']=code==0 and abs(rows[-1]['TIME']-.0008)<1e-12
   rec['ranges']={k:[min(r[k] for r in rows),max(r[k] for r in rows)] for k in rows[0] if k!='TIME'}
   (d/'tail.json').write_text(json.dumps(rows[-10:],indent=2)+'\n')
 results.append(rec);(root/'results.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(rec),flush=True)
