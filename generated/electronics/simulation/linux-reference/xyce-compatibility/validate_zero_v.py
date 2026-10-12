from pathlib import Path
import csv,json,math
root=Path(__file__).parent
out={'runs':[],'matrix':{},'scope':'Normal-OP reference only; UIC remapping is numerically nonequivalent.'}
for d in sorted((root/'runs/zero_v_ic').iterdir()):
 log=(d/'stdout.log').read_text(); cp=d/(d.name+'.cir.csv')
 obj={'name':d.name,'log':str(d/'stdout.log'),'singular_warning':'Numerically singular matrix' in log,'dcop_failed':'DC Operating Point Failed' in log}
 if cp.exists():
  with cp.open() as f:rows=[{k:float(v) for k,v in r.items()} for r in csv.DictReader(f)]
  obj['rows']=len(rows)
  if rows:
   obj.update(first=rows[0],last=rows[-1],max_A_B_difference=max(abs(r['V(A)']-r['V(B)']) for r in rows))
   obj['max_A_B_positive_time_difference']=max(abs(r['V(A)']-r['V(B)']) for r in rows if r['TIME']>0)
   for n in ['A','B']:
    obj['max_analytic_error_'+n]=max(abs(r['V('+n+')']-(1-.75*math.exp(-r['TIME']/.001))) for r in rows)
 out['runs'].append(obj)
p=Path('/workspace/tool-verification/xyce-reference/Startup/Failed_Matrix1.mm')
ls=[l for l in p.read_text().splitlines() if l and not l.startswith('%')];n,m,nnz=map(int,ls[0].split());rows=[[] for _ in range(n)]
for l in ls[1:]:
 i,j,v=l.split();rows[int(i)-1].append((int(j)-1,float(v)))
out['matrix']={'path':str(p),'shape':[n,m],'stored_entries':nnz,'zero_rows_0based':[i for i,r in enumerate(rows) if not any(v for _,v in r)],'row9_entries_0based':rows[9],'row9_has_structural_diagonal':any(j==9 for j,v in rows[9]),'node9':'x_u1:xcore:comp'}
out['recommendation']='Accept only normal-OP intended-constraint compatibility remap COMP to zero-source-connected N16888001 with same value and documented reason; no claim of UIC equivalence or byte-identical original model. Prefer this small audited model adaptation to an unvalidated custom solver graph patch for the immediate reference run.'
(root/'zero-v-ic-detailed-validation.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps([r for r in out['runs'] if 'double_nested' in r['name']],indent=2))
