import csv,json,math,hashlib,datetime
from pathlib import Path
root=Path(__file__).resolve().parent
res=json.loads((root/'runs/results.json').read_text())
def read(name,mode='default'):
 p=root/'runs'/mode/name/(name+'.cir.csv')
 with p.open() as f:return [{k:float(v) for k,v in r.items()} for r in csv.DictReader(f)]
def equal(a,b):
 return {'same_rows':len(a)==len(b),'max_abs_difference':max(abs(x[k]-y[k]) for x,y in zip(a,b) for k in x),'exact_numeric_equality':a==b}
out={'validated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'solver':'Xyce Release 7.10.0-opensource','run_count':len(res),'exit_codes':{r['mode']+'/'+r['netlist']:r['returncode'] for r in res},'numeric_checks':{},'source_integrity':{}}
checks=out['numeric_checks']
for r in res:
 src=root/r['netlist'];run=Path(r['log']).parent/r['netlist']
 out['source_integrity'][r['mode']+'/'+r['netlist']]={'matches_prepared_netlist':src.read_bytes()==run.read_bytes(),'sha256':hashlib.sha256(run.read_bytes()).hexdigest()}
for mode in ['default','hspice_math']:
 for name in ['xor_exact','xor_parenthesized','xor_adapted']:
  rows=read(name,mode);bad=[]
  for row in rows:
   expected=float((row['V(YTD)']>.5)!=(row['V(IN)']>.5))
   if abs(row['V(P)']-expected)>1e-8:bad.append({'input_ytd':row['V(YTD)'],'input_in':row['V(IN)'],'actual':row['V(P)'],'expected':expected})
  negative=mode=='hspice_math' and name!='xor_adapted'
  checks[mode+'/'+name]={'rows':len(rows),'xor_mismatches':bad,'xor_correct':not bad,'negative_control':negative,'pass':len(rows)==9 and (len(bad)>0 if negative else not bad)}
for name in ['xor_parenthesized','xor_adapted']:
 checks['equality_default_xor_exact_vs_'+name]=equal(read('xor_exact'),read(name))
checks['equality_hspice_original_vs_parenthesized']=equal(read('xor_exact','hspice_math'),read('xor_parenthesized','hspice_math'))
rows=read('logic_value');err=0
for r in rows:
 a=r['V(A)']>.5;b=r['V(B)']>.5
 for k,v in {'V(AS)':a and b,'V(AD)':a and b,'V(OS)':a or b,'V(OD)':a or b,'V(GS)':2 if a else -1,'V(GE)':2 if a else -1}.items():err=max(err,abs(r[k]-v))
checks['logic_value']={'rows':len(rows),'max_abs_error':err,'pass':len(rows)==9 and err<=1e-8}
rows=read('switch_transfer');errors=[];points=[]
for r in rows:
 v=r['V(CTRL)'];u=(v-.4)/(.7)
 if u<=0:resistance=1e7
 elif u>=1:resistance=.04
 else:
  s=2*u-1;resistance=math.exp(math.log(math.sqrt(.04*1e7))+.75*math.log(.04/1e7)*s-.25*math.log(.04/1e7)*s**3)
 expected=-1/resistance;err=abs((r['I(VTEST)']-expected)/expected);errors.append(err)
 points.append({'control_V':v,'actual_I_A':r['I(VTEST)'],'expected_I_A':expected,'relative_error':err})
checks['switch_transfer']={'rows':len(rows),'max_relative_error':max(errors),'pass':len(rows)==19 and max(errors)<=1e-5,'points':points}
def curve(name,col,fn):
 rows=read(name);errs=[abs(r[col]-fn(r['TIME'])) for r in rows]
 return {'rows':len(rows),'first':rows[0],'last':rows[-1],'max_abs_error_V':max(errs),'max_error_time_s':rows[errs.index(max(errs))]['TIME'],'pass':max(errs)<=.002}
for mode in ['op','uic','noop']:
 for ic in ['ic','noic']:
  name=f'rc_{mode}_{ic}'
  initial=.25 if ic=='ic' else (1 if mode=='op' else 0)
  checks[name]=curve(name,'V(OUT)',lambda t,v=initial:1-(1-v)*math.exp(-t/.001))
for ic in ['ic','noic']:checks['equality_uic_vs_noop_'+ic]=equal(read('rc_uic_'+ic),read('rc_noop_'+ic))
for name in ['ic_alias_space','ic_alias_compact']:
 checks[name+'_EN']=curve(name,'V(ACTUAL_EN)',lambda t:1-math.exp(-t/.001))
 checks[name+'_COMP']=curve(name,'V(ACTUAL_COMP)',lambda t:1.3695*math.exp(-t/.001))
checks['equality_alias_whitespace']=equal(read('ic_alias_space'),read('ic_alias_compact'))
checks['ic_with_equals']=curve('ic_with_equals','V(OUT)',lambda t:.25*math.exp(-t/.001))
log=(root/'runs/default/ic_no_equals/stdout.log').read_text()
checks['ic_no_equals_expected_failure']={'returncode':next(r['returncode'] for r in res if r['netlist']=='ic_no_equals.cir'),'errors':[l for l in log.splitlines() if 'Netlist error:' in l],'pass':"Cannot convert '(' to double for expression VALUE" in log}
out['all_expected_checks_pass']=all(c.get('pass',c.get('exact_numeric_equality',False)) for c in checks.values()) and all(c['matches_prepared_netlist'] for c in out['source_integrity'].values())
out['caveats']=['Xyce runs are not independent PSpice solver validation.','No full TI model convergence or device physical validation is established by these probes.','One-terminal voltage-node warnings occur in ideal-source test fixtures; only ic_no_equals reports ignored initial-condition nodes or fatal parsing errors.','CSV outputs include t=0 despite older source comments suggesting otherwise; numerical checks use actual timestamps.']
# Follow-up changes only PRINT observation, leaving original test and all circuit equations intact.
obs=read('ic_with_equals_observe')
checks['ic_with_equals_observed_storage_node']=curve('ic_with_equals_observe','V(X1:QINT)',lambda t:.25*math.exp(-t/.001))
checks['ic_with_equals_observed_output']={'t0_OUT_V':obs[0]['V(OUT)'],'t0_Qint_V':obs[0]['V(X1:QINT)'],'t0_algebraic_mismatch_V':obs[0]['V(OUT)']-obs[0]['V(X1:QINT)'],'positive_time_rows':len(obs)-1,'positive_time_max_OUT_minus_Qint_V':max(abs(r['V(OUT)']-r['V(X1:QINT)']) for r in obs if r['TIME']>0),'positive_time_max_error_vs_analytic_V':max(abs(r['V(OUT)']-.25*math.exp(-r['TIME']/.001)) for r in obs if r['TIME']>0)}
original=(root/'ic_with_equals.cir').read_text()
observed=(root/'runs/default/ic_with_equals_observe/ic_with_equals_observe.cir').read_text()
out['followup_observation']={'netlist':'runs/default/ic_with_equals_observe/ic_with_equals_observe.cir','log':'runs/default/ic_with_equals_observe/stdout.log','command':['/workspace/tools/xyce-7.10/bin/Xyce','ic_with_equals_observe.cir'],'returncode':0,'only_change_add_PRINT_Qint':observed==original.replace('.PRINT TRAN FORMAT=CSV V(OUT)','.PRINT TRAN FORMAT=CSV V(OUT) V(X1:Qint)'),'purpose':'Disambiguate derived E-source OUT t=0 versus explicitly initialized storage node Qint.'}
out['conclusion']='Original no-equals IC syntax fails. Adding only equals preserves specified capacitor-node IC exactly. Original output-only expectation fails at t=0 because OUT is not initialized there; this discrepancy remains explicitly recorded. Qint matches the analytic curve at all samples, and OUT equals Qint at every positive-time sample. Native XOR, logic, continuous switch, RC and aliases pass.'
out['caveats'].append('Original ic_with_equals output-only all-sample check fails at t=0; direct storage-node follow-up resolves intended IC semantics without erasing that failure.')
(root/'actual-validation.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in checks.items() if 'points' not in v},indent=2));print('SWITCH',checks['switch_transfer']['max_relative_error']);print('ALL_EXPECTED_CHECKS_PASS',out['all_expected_checks_pass'])
