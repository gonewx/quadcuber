from pathlib import Path
import numpy as np,json
r=Path(__file__).parent;j=json.loads((r/'results.json').read_text());assess=[]
for case in j['cases']:
 p=r/case['case']/case.get('waveform','test.cir.csv');d=np.genfromtxt(p,delimiter=',',names=True)
 if d.size<2:continue
 t=d['TIME'];out={'case':case['case'],'termination':'TIMEOUT_180S' if case['returncode']==124 else 'NUMERICAL_FAILURE' if case['returncode'] else 'COMPLETED','completed':case['completed'],'periodic_steady_state_verified':False,'load_step_verified':False,'input_change_verified':False,'windows':[]}
 for a,b in j['planned_observation_windows_s']:
  w={'start_s':a,'end_s':b,'complete':bool(t[0]<=a and t[-1]>=b)}
  if w['complete']:
   ts=np.unique(np.r_[a,(a+b)/2,t[(t>a)&(t<b)],b]);w['rails']={}
   for ch in [1,2]:
    v=np.interp(ts,t,d[f'VB{ch}OUT']);il=np.interp(ts,t,d[f'IL{ch}']);clock=np.interp(ts,t,d[f'VX{ch}XCORESYSCLK']);rises=np.where((clock[:-1]<.5)&(clock[1:]>=.5))[0]
    half=(a+b)/2;left=ts<=half;right=ts>=half;means=[np.trapezoid(v[q],ts[q])/(ts[q][-1]-ts[q][0]) for q in [left,right]]
    w['rails'][f'5V_{ch}']={'min_V':float(v.min()),'max_V':float(v.max()),'mean_V':float(np.trapezoid(v,ts)/(b-a)),'half_window_mean_shift_V':float(means[1]-means[0]),'max_abs_IL_A':float(abs(il).max()),'observed_clock_rises':len(rises),'voltage_current_band_met':bool(v.min()>=4.75 and v.max()<=5.25 and abs(il).max()<6),'stationarity_mean_criterion_met':bool(abs(means[1]-means[0])<=.005),'physical_clock_validated':False}
  out['windows'].append(w)
 assess.append(out)
(r/'window-assessment.json').write_text(json.dumps({'note':'Observed clock rises are not accepted physical cycles until oscillator compatibility is validated. Partial voltage extrema are not a hardware failure diagnosis.','cases':assess},indent=2)+'\n')
print('Window assessments',len(assess))
