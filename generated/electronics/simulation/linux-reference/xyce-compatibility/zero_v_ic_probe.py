from pathlib import Path
import subprocess,json,csv,math
root=Path(__file__).parent
results=[]
for target in ['A','B']:
 for mode in ['op','uic']:
  name=f'zero_v_ic_{target.lower()}_{mode}'
  d=root/'runs'/'zero_v_ic'/name;d.mkdir(parents=True,exist_ok=True)
  text=f'''Zero voltage source IC target {target}, mode {mode}
VS IN 0 1
R1 IN A 1k
C1 A 0 1u
VZERO A B 0Vdc
EOBS OUT 0 VALUE={{V(B)}}
.IC V({target})=0.25
.TRAN 1u 1m 0 1u {'UIC' if mode=='uic' else ''}
.PRINT TRAN FORMAT=CSV V(A) V(B) V(OUT) I(VZERO)
.END
'''
  (d/(name+'.cir')).write_text(text)
  with (d/'stdout.log').open('w') as f:
   r=subprocess.run(['/workspace/tools/xyce-7.10/bin/Xyce',name+'.cir'],cwd=d,stdout=f,stderr=subprocess.STDOUT,timeout=40)
  result={'name':name,'target':target,'mode':mode,'returncode':r.returncode,'log':str(d/'stdout.log')}
  csvpath=d/(name+'.cir.csv')
  if csvpath.exists():
   with csvpath.open() as f:rows=[{k:float(v) for k,v in row.items()} for row in csv.DictReader(f)]
   result['rows']=len(rows)
   if rows:
    result['first']=rows[0];result['last']=rows[-1]
    result['max_AB_error_all']=max(abs(x['V(A)']-x['V(B)']) for x in rows)
    result['max_AB_error_positive_time']=max(abs(x['V(A)']-x['V(B)']) for x in rows if x['TIME']>0)
    for n in ['A','B']:
     result['max_analytic_error_'+n]=max(abs(x[f'V({n})']-(1-.75*math.exp(-x['TIME']/.001))) for x in rows)
     result['max_analytic_error_positive_time_'+n]=max(abs(x[f'V({n})']-(1-.75*math.exp(-x['TIME']/.001))) for x in rows if x['TIME']>0)
  results.append(result)
(root/'zero-v-ic-validation.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
