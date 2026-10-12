from pathlib import Path
import json,hashlib
r=Path(__file__).parent;p=r/'results.json';j=json.loads(p.read_text());assert len(j['cases'])==18 and j['state']!='RUNNING','Wait for full matrix'
for c in j['cases']:
 folder=r/c['case'];log=(folder/'xyce.log').read_text();c['termination']='TIMEOUT_180S' if c['returncode']==124 else 'NUMERICAL_FAILURE' if 'Time step too small' in log else 'SOLVER_ERROR' if c['returncode'] else 'COMPLETED'
 assert (c['termination']!='TIMEOUT_180S' or 'HARNESS TIMEOUT 180s' in log)
 c['input_events']=[{'start_s':.003,'end_s':.00301,'from_V':c['vin'],'to_V':9.18,'delta_V':round(9.18-c['vin'],8)},{'start_s':.004,'end_s':.00401,'from_V':9.18,'to_V':8.82,'delta_V':-.36}]
 for e in c['input_events']:e['actual_change_reached']=e['delta_V']!=0 and c.get('last_time_s',0)>e['start_s']
 c['input_step_reached']=any(e['actual_change_reached'] for e in c['input_events']);c['load_step_full_after_window']=c.get('last_time_s',0)>=.002;c['periodic_steady_state_verified']=False;c['model_compatibility_verified']=False
 c['blocker']='Solver run exceeded 180s budget; not proof of nonconvergence' if c['termination']=='TIMEOUT_180S' else 'Solver timestep too small' if c['termination']=='NUMERICAL_FAILURE' else 'See log'
 c['waveform']='test.cir.csv';c['log']='xyce.log';c['passed']=False
 assert c['testbench_sha256']==hashlib.sha256((folder/'test.cir').read_bytes()).hexdigest()
 (folder/'result.json').write_text(json.dumps(c,indent=2)+'\n')
j['state']='BLOCKED_MIXED_NUMERICAL_FAILURE_AND_TIMEOUT';j['termination_counts']={k:sum(c['termination']==k for c in j['cases']) for k in sorted({c['termination'] for c in j['cases']})};j['assessment_scope']='Preinitialized dynamics only; not cold start. Successful integration alone cannot pass while oscillator compatibility remains unverified.'
p.write_text(json.dumps(j,indent=2)+'\n');print(json.dumps(j['termination_counts']))
