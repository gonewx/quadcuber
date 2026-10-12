from pathlib import Path
import numpy as np,json,hashlib
root=Path(__file__).parent
full=Path('/workspace/tool-verification/reference-steady-extended/test.cir.csv');d=np.loadtxt(full,delimiter=',',skiprows=1)
results={'full_waveform_sha256':hashlib.sha256(full.read_bytes()).hexdigest(),'full_SYSCLK_column':'V(X_U1:XCORE:SYSCLK), index 8 including TIME','windows':[],'isolated':[]}
for lo,hi in [(0,.0001),(.00075,.0008),(.001,.0015)]:
 a=(d[:,0]>=lo)&(d[:,0]<=hi);t=d[a,0];v=d[a,8];up=t[1:][(v[:-1]<=.5)&(v[1:]>.5)]
 sch=[];armed=v[0]<=.1
 for x,y in zip(t,v):
  if y<=.1:armed=True
  elif y>=.9 and armed:sch.append(x);armed=False
 def stats(ts):
  delta=np.diff(ts);return {'count':len(ts),'period_quantiles_s':np.quantile(delta,[0,.1,.5,.9,1]).tolist(),'median_frequency_Hz':float(1/np.median(delta))}
 results['windows'].append({'from_s':lo,'to_s':hi,'SYSCLK_range':[float(min(v)),float(max(v))],'threshold05':stats(up),'schmitt01_09':stats(sch)})
for p in sorted(root.glob('*/test.cir.csv')):
 try:x=np.loadtxt(p,delimiter=',',skiprows=1)
 except ValueError:continue
 if x.ndim!=2 or not len(x):continue
 results['isolated'].append({'case':p.parent.name,'rows':len(x),'last_time_s':float(x[-1,0]),'last_SYSCLK':float(x[-1,1]),'last_RAMP':float(x[-1,2]),'last_raw_comparator':float(x[-1,3]),'SYSCLK_rising_count':int(np.sum((x[:-1,1]<=.5)&(x[1:,1]>.5))),'completed_100us':bool(x[-1,0]>=.0001),'csv_sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
results['nominal_estimate']={'C_F':7.14286e-12,'threshold_V':1.75,'base_current_A':5e-6,'base_charge_time_s':7.14286e-12*1.75/5e-6,'initial_current_A':5.3e-6,'initial_charge_time_s':7.14286e-12*1.75/5.3e-6,'approx_charge_period_range_s':[7.14286e-12*1.75/5.3e-6,7.14286e-12*1.75/4.7e-6]}
(root/'analysis.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
