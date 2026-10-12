from pathlib import Path
import json,subprocess,time,hashlib,csv,math
ROOT=Path(__file__).resolve().parent
XYCE='/workspace/tools/xyce-7.10/bin/Xyce'
MODEL=Path('/workspace/tool-verification/xyce-reference/TPS54302_TRANS.xyce-init.LIB')
assert hashlib.sha256(MODEL.read_bytes()).hexdigest()=='47f1df44d7467c19c63eedf896bb61e2061eb455c65938f05a43e12819f812e7'
results=[]
for initial in ['light','heavy']:
 template=(ROOT/('nominal' if initial=='light' else 'nominal-heavy')/'test.cir').read_text()
 for vin in [8.82,9,9.18]:
  for cf in [.4,.8,1.2]:
   name=f'{initial}_VIN{vin:g}_C{cf:g}';folder=ROOT/name;folder.mkdir(exist_ok=True)
   s=template.replace('VIN vm 0 DC 9',f'VIN vm 0 PWL(0 {vin:g} 3m {vin:g} 3.01m 9.18 4m 9.18 4.01m 8.82)')
   for i in [1,2]:s=s.replace(f'C{i}in vm 0 8e-06',f'C{i}in vm 0 {10e-6*cf:g}').replace(f'C{i}out b{i}cap 0 3.52e-05',f'C{i}out b{i}cap 0 {44e-6*cf:g}').replace(f'C{i}boot b{i}bc b{i}sw 100n IC=9',f'C{i}boot b{i}bc b{i}sw 100n IC={vin:g}')
   s=s.replace('.TRAN 20n 3m 0 20n','.TRAN 20n 5m 0 20n');(folder/'test.cir').write_text(s)
   start=time.monotonic()
   with (folder/'xyce.log').open('w') as f:
    try:rc=subprocess.run([XYCE,'test.cir'],cwd=folder,stdout=f,stderr=subprocess.STDOUT,timeout=180).returncode
    except subprocess.TimeoutExpired:rc=124;f.write('\nHARNESS TIMEOUT 180s: INCOMPLETE\n')
   r={'case':name,'vin':vin,'cap_factor':cf,'initial_load_A':[.25,.05] if initial=='light' else [1.5,1.5],'returncode':rc,'elapsed_s':time.monotonic()-start,'requested_stop_s':.005,'completed':False,'passed':False,'cold_start_test':False,'load_step_reached':False,'input_step_reached':False,'testbench_sha256':hashlib.sha256(s.encode()).hexdigest()}
   p=folder/'test.cir.csv'
   if p.exists():
    rows=[{k:float(v) for k,v in row.items()} for row in csv.DictReader(p.open())]
    if rows:
     last=rows[-1]['TIME'];r.update(rows=len(rows),last_time_s=last,finite=all(math.isfinite(v) for row in rows for v in row.values()),strictly_increasing=all(b['TIME']>a['TIME'] for a,b in zip(rows,rows[1:])),load_step_reached=last>=.001,input_step_reached=last>=.003,observed_rails={f'5V_{ch}':{'min_V':min(row[f'V(B{i}OUT)'] for row in rows),'max_V':max(row[f'V(B{i}OUT)'] for row in rows),'final_V':rows[-1][f'V(B{i}OUT)'],'max_abs_inductor_A':max(abs(row[f'I(L{i})']) for row in rows)} for i,ch in [(1,'A'),(2,'B')]})
     r['completed']=rc==0 and r['finite'] and r['strictly_increasing'] and abs(last-.005)<1e-12
   (folder/'result.json').write_text(json.dumps(r,indent=2)+'\n');results.append(r);(ROOT/'results.json').write_text(json.dumps({'baseline_git':'0c2517720d7764b3bae5c0347b3b211606647013','state':'RUNNING','initialization':'normal OP, STEADY_STATE=1, output IC=5V, inductor IC=initial load, boot capacitor IC=VIN; no continuous clamps','cold_start_validated':False,'manufacturing_released':False,'planned_observation_windows_s':[[.0007,.001],[.0017,.002],[.0027,.003],[.0037,.004],[.0047,.005]],'diagnostic_thresholds':{'Vout_min':4.75,'Vout_max':5.25,'inductor_abs_max_A':6,'window_mean_shift_max_V':.005,'window_min_cycles':50},'cases':results},indent=2)+'\n');print(json.dumps(r),flush=True)
j=json.loads((ROOT/'results.json').read_text());j['state']='INCOMPLETE_NUMERICAL_FAILURE' if not all(r['completed'] for r in results) else 'COMPLETED_REQUIRES_WINDOW_ASSESSMENT';j.update(attempted=len(results),completed=sum(r['completed'] for r in results),passed=sum(r['passed'] for r in results));(ROOT/'results.json').write_text(json.dumps(j,indent=2)+'\n')
