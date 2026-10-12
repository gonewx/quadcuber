#!/usr/bin/env python3
"""RLC / current-limited source and finite regenerative-energy sensitivity runs.
Original behavioral boundary models; no TI model, no manufacturer thermal model.
"""
import argparse,csv,json,math,hashlib
from pathlib import Path
import numpy as np
import run_boundaries as base

def save(name,rows):
 with (base.OUT/(name+'.csv')).open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)

def main():
 p=argparse.ArgumentParser();p.add_argument('--ngspice',default='ngspice');a=p.parse_args()
 base.OUT=base.ROOT/'generated/electronics/protection-analysis';base.OUT.mkdir(exist_ok=True)
 assert base.C['F1']['mpn']=='0407008.WR'
 for ref in ['R500','R501']:assert base.C[ref]['mpn']=='CRCW2512300RFKEG'
 meta=base.source_contract();meta.update(state='RUNNING',vendor_model_cases=0)
 (base.OUT/'run-status.json').write_text(json.dumps(meta,indent=2)+'\n')
 inputs=[]
 # Rwire includes connector and fuse resistance; Csrc is an assumed PSU reservoir.
 for vset in [8.82,9.18]:
  for rw in [.02,.06,.12]:
   for lw in [.2e-6,2e-6]:
    for cs in [470e-6,2200e-6]:
     for cm in [.002256,.003384]:
      name=f'input_V{vset:g}_R{rw:g}_L{lw:g}_Cs{cs:g}_Cm{cm:g}'
      body=f'''* PSU ideal current limit 6.5A; physical output reservoir can still cause surge.
Bpsu 0 psu I=min(max(({vset:g}-v(psu))/0.03,0),6.5)
Cpsu psu 0 {cs:g} ic={vset:g}
Venable ctl 0 PWL(0 0 100u 0 101u 1)
Bplug psu wire I=v(psu,wire)*(v(ctl)/0.005+1e-9)
Rwire wire wl {rw:g}
Lwire wl anode {lw:g}
Cpar anode 0 100p
Bideal anode vm I=max((v(anode,vm)-0.02)/0.0033,0)
Resr vm bulk 0.010
Cbulk bulk 0 {cm:g} ic=0
Bload vm 0 I=4*min(max(v(vm)/6.5,0),1)*(time>0.004)
R500 vm 0 300
R501 vm 0 300
.ic v(psu)={vset:g} v(bulk)=0 v(vm)=0'''
      d=base.simulate(name,body,['v(vm)','i(Lwire)','v(psu)','i(Bpsu)'],.010,1e-6,a.ngspice)
      t,v,i,ps,ip=d.T;win=t<.004
      inputs.append(dict(case=name,source_V=vset,Rwire_ohm=rw,Lwire_H=lw,Csource_F=cs,Cbus_F=cm,peak_fuse_A=float(i.max()),startup_I2t_A2s=float(np.trapezoid(i[win]**2,t[win])),I2t_fraction_407_nominal=float(np.trapezoid(i[win]**2,t[win])/24.12),VM_peak_V=float(v.max()),VM_end_V=float(v[-1]),supply_peak_A=float(ip.max())))
 regen=[]
 for energy in [.02,.05,.1,.3,1]:
  for dur in [.005,.02,.1]:
   for repeat in [1,5]:
    for rb in [1e9,151.5]:
     period=1/repeat;stop=4*period+dur+.01;cap=.002256;bv=14.7;rd=(19.9-bv)/30.2
     name=f'energy_E{energy:g}_T{dur:g}_Hz{repeat:g}_R{rb:g}'
     points=['0 0']
     for n in range(5):
      start=.001+n*period;points += [f'{start:g} 0',f'{start+dur/2:g} {2*energy/dur:g}',f'{start+dur:g} 0']
     body=f'''Vpower power 0 PWL({' '.join(points)})
Bregen 0 vm I=v(power)/max(v(vm),1)
Cbulk vm 0 {cap:g} ic=9.18
BTVS vm 0 I=max((v(vm)-{bv:g})/{rd:g},0)
Rbleed vm 0 {rb:g}
Bhold 0 vm I=min(max((9.18-v(vm))/0.1,0),6.5)
.ic v(vm)=9.18'''
     d=base.simulate(name,body,['v(vm)','i(BTVS)','v(power)','i(Bhold)'],stop,min(dur/100,.001),a.ngspice)
     t,v,it,power,ih=d.T;pt=v*it
     tvse=float(np.trapezoid(pt,t));ein=float(np.trapezoid(power,t));stored=.5*cap*(v[-1]**2-9.18**2)
     eb=float(np.trapezoid(v*v/rb,t));eh=float(np.trapezoid(v*ih,t));res=ein+eh-tvse-eb-stored
     assert abs(res)<.002,(name,res)
     peak=float(v.max())
     if rb<200 and energy<=.05:assert peak<12,(name,peak)
     regen.append(dict(case=name,bleed_ohm=rb,energy_per_event_J=energy,pulse_s=dur,repetition_Hz=repeat,VM_peak_V=peak,TVS_total_5events_J=tvse,TVS_peak_W=float(pt.max()),TVS_last_event_average_W=float(np.trapezoid(pt[t>=.001+4*period],t[t>=.001+4*period])*repeat),input_5events_J=ein,bleed_energy_J=eb,source_energy_J=eh,energy_balance_J=res))
 # Output-referred inertia includes rotor inertia times gear ratio squared.
 mech=[]
 for j in [3e-5,1e-4,3e-4,1e-3]:
  for rpm in [60,120,175]:
   for lm in [.0005,.002,.010]:
    ek=4*.5*j*(rpm*2*math.pi/60)**2;el=4*.5*lm*1.613**2
    mech.append(dict(J_equiv_each_kg_m2=j,output_rpm=rpm,motor_L_H=lm,four_rotational_J=ek,four_magnetic_J=el,total_max_regen_J=ek+el))
 save('input_rlc',inputs);save('regenerative_energy',regen);save('mechanical_envelope',mech)
 meta.update(state='COMPLETED_BOUNDARY_ONLY',ngspice_cases=len(inputs)+len(regen),input_cases=len(inputs),regen_cases=len(regen),mechanical_energy_rows=len(mech),hardware_tested=False,manufacturing_release=False)
 (base.OUT/'run-status.json').write_text(json.dumps(meta,indent=2)+'\n')
 print(json.dumps(meta,indent=2))
if __name__=='__main__':
 try:main()
 except Exception as e:
  path=base.OUT/'run-status.json';s=json.loads(path.read_text()) if path.exists() else {};s.update(state='FAILED',error=repr(e));path.write_text(json.dumps(s,indent=2)+'\n');raise
