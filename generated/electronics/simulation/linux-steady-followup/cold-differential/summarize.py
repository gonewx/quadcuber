import csv,json,hashlib
from pathlib import Path
root=Path(__file__).parent
results=json.loads((root/'results.json').read_text())
summary=[]
for rec in results:
 d=root/rec['case']
 with (d/'driver.cir.csv').open() as f:rows=[{k:float(v) for k,v in r.items()} for r in csv.DictReader(f)]
 edges=[]
 for a,b in zip(rows,rows[1:]):
  if a['V(SW)']<=1<b['V(SW)']:edges.append({'before_s':a['TIME'],'after_s':b['TIME'],'after_SW_V':b['V(SW)']})
 summary.append({'case':rec['case'],'switch_rises_above_1V':len(edges),'first_rise':edges[0] if edges else None,'last_time_s':rows[-1]['TIME'],'last_minus_first_rise_s':rows[-1]['TIME']-edges[0]['after_s'] if edges else None,'model_sha256':rec['model_sha256'],'files_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in d.iterdir() if f.is_file()},'last_50us_VOUT_range':[min(r['V(VOUT)'] for r in rows if r['TIME']>=max(0,rows[-1]['TIME']-50e-6)),max(r['V(VOUT)'] for r in rows if r['TIME']>=max(0,rows[-1]['TIME']-50e-6))]})
(root/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
try:
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 fig,axes=plt.subplots(3,1,figsize=(9,9),layout='constrained')
 for rec in results:
  with (root/rec['case']/'driver.cir.csv').open() as f:rs=[{k:float(v) for k,v in r.items()} for r in csv.DictReader(f)]
  t=[r['TIME']*1e6 for r in rs]
  axes[0].plot(t,[r['V(VOUT)'] for r in rs],label=rec['case'])
  axes[1].plot(t,[r['V(X_U1:XCORE:VREF_GM)'] for r in rs],label=rec['case'])
  if rec['case']!='steady_state0':
   end=rs[-1]['TIME'];tail=[r for r in rs if end-r['TIME']<5e-9]
   axes[2].plot([(r['TIME']-end)*1e9 for r in tail],[r['V(SW)'] for r in tail],'.-',label=rec['case'])
 axes[0].set(ylabel='VOUT (V)',xlabel='Time (us)',title='Diagnostic variants: completion is not cold-start validation')
 axes[1].set(ylabel='VREF_GM (V)',xlabel='Time (us)')
 axes[2].set(ylabel='SW (V)',xlabel='Time relative to last accepted point (ns)',title='Both cold variants stop immediately after first switch rise')
 for ax in axes:ax.grid(alpha=.3);ax.legend()
 fig.savefig(root/'differential.png',dpi=150)
except ImportError:pass
print(json.dumps(summary,indent=2))
