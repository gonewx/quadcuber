#!/usr/bin/env python3
"""Actual ngspice boundary runs. Not vendor-device or electrothermal simulation."""
import argparse, csv, gzip, hashlib, json, os, runpy, subprocess
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'generated/electronics/simulation'
C={x['ref']:x for x in runpy.run_path(str(ROOT/'electronics/circuit.py'))['C']}

def source_contract():
    required={'U2':'TPS54302DDCR','U3':'TPS54302DDCR','Q1':'CSD18540Q5B','U4':'LM74700QDBVRQ1','D3':'SMBJ12A','D2':'SS14-E3/61T','D5':'SS14-E3/61T'}
    for r,m in required.items(): assert C[r]['mpn']==m,(r,C[r]['mpn'])
    bulk=[x for x in C.values() if x['value']=='470u/25V' and set(x['pins'].values())=={'VM','GND'}]
    assert len(bulk)==6
    return {'circuit_sha256':hashlib.sha256((ROOT/'electronics/circuit.py').read_bytes()).hexdigest(), 'pcb_sha256':hashlib.sha256((ROOT/'electronics/quadcuber.kicad_pcb').read_bytes()).hexdigest(), 'vm_bulk_refs':[x['ref'] for x in bulk], 'vm_bulk_nominal_F':len(bulk)*470e-6,'parts':required}

def simulate(name,body,signals,stop,step,ng):
    signals=[('@'+x[2:-1].lower()+'[i]') if x.startswith('i(B') or x.startswith('i(I') else x for x in signals]
    folder=OUT/name;folder.mkdir(parents=True,exist_ok=True)
    net=f'''Quadcuber A1 boundary analysis: {name}
* Original simplified model; NOT a manufacturer macro-model.
{body}
.options reltol=1e-5 abstol=1e-9 vntol=1e-7 method=gear
.control
set wr_vecnames
set wr_singlescale
save all {' '.join(x for x in signals if x.startswith('@'))}
tran {step:g} {stop:g} 0 {step:g}
wrdata waveform.txt {' '.join(signals)}
quit
.endc
.end
'''
    (folder/'test.cir').write_text(net)
    (folder/'waveform.txt').unlink(missing_ok=True)
    r=subprocess.run([ng,'-b','test.cir'],cwd=folder,text=True,capture_output=True,timeout=120)
    (folder/'ngspice.log').write_text(r.stdout+r.stderr)
    if r.returncode or 'Error:' in r.stderr or not (folder/'waveform.txt').exists():raise RuntimeError(name+' failed; inspect log')
    d=np.loadtxt(folder/'waveform.txt',skiprows=1)
    if d.ndim!=2 or d.shape[1]!=len(signals)+1:raise RuntimeError(name+' malformed waveform')
    if not np.all(np.isfinite(d)) or d[-1,0]<stop*.999:raise RuntimeError(name+' incomplete')
    (folder/'waveform.txt.gz').write_bytes(gzip.compress((folder/'waveform.txt').read_bytes(),mtime=0))
    (folder/'waveform.txt').unlink()
    return d

def main():
    p=argparse.ArgumentParser();p.add_argument('--ngspice',default='ngspice');a=p.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    meta=source_contract();meta['ngspice']=subprocess.check_output([a.ngspice,'--version'],text=True)
    meta['state']='RUNNING';meta['vendor_model_cases']=0
    (OUT/'run-status.json').write_text(json.dumps(meta,indent=2)+'\n')
    regen=[]; selected={}
    # TVS straight-line envelope: breakdown 13.3..14.7 V, 19.9 V at 30.2 A.
    # Not a guaranteed bound between endpoints; no capacitance, heating or degradation.
    for cf in [.8,1,1.2]:
      for amps in [1,3,6.452]:
       for duration in [.005,.020,.100]:
        for bv in [13.3,14.7]:
          name=f'regen_C{cf:g}_I{amps:g}_T{duration:g}_BV{bv:g}'
          cap=meta['vm_bulk_nominal_F']*cf; rd=(19.9-bv)/30.2
          body=f'''* VM precharged to 9V. Supply disconnected; no other loads (conservative for charge).
* Constant injected BUS current is a test parameter, not a motor current prediction.
Cbulk vm 0 {cap:g} ic=9
Rleak vm 0 1e9
Vregen regen vm 0
Iregen 0 regen PWL(0 0 1m 0 1.001m {amps:g} {0.001+duration:g} {amps:g} {0.001001+duration:g} 0)
BTVS vm 0 I=max((v(vm)-{bv:g})/{rd:g},0)
.ic v(vm)=9'''
          d=simulate(name,body,['v(vm)','i(BTVS)','i(Vregen)'],duration+.005,2e-5,a.ngspice)
          t,v,it,ii=d.T
          peak=float(v.max());et=float(np.trapezoid(v*it,t));ein=float(np.trapezoid(v*ii,t))
          regen.append(dict(case=name,cap_F=cap,injected_bus_A=amps,pulse_s=duration,tvs_knee_V=bv,VM_max_V=peak,TVS_energy_J=et,TVS_peak_W=float((v*it).max()),input_energy_J=ein,stored_delta_J=float(.5*cap*(v[-1]**2-81)),below_25V=peak<25,below_12V=peak<12))
          if cf==.8 and amps==6.452 and bv==14.7:selected[duration]=d
    switch=[]
    for mode in ['usb_only','external_only','external_removed','usb_removed']:
      for current in [.05,.15]:
       # branch VF linearization is declared assumed, not vendor SS14 diode model.
       usb='5' if mode!='external_only' else '0'
       ext='5' if mode!='usb_only' else '0'
       if mode=='external_removed':ext='PWL(0 5 2m 5 2.001m 0)'
       if mode=='usb_removed':usb='PWL(0 5 2m 5 2.001m 0)'
       body=f'''Vusb usb 0 {usb}
Vext ext 0 {ext}
BD5 usb vsys I=max((v(usb,vsys)-0.35)/0.2,0)
BD2 ext vsys I=max((v(ext,vsys)-0.35)/0.2,0)
C1 vsys 0 1.1u
Bload vsys 0 I={current:g}*min(max(v(vsys)/3.5,0),1)
Rleak vsys 0 1e9'''
       name=f'logic_{mode}_{current:g}A';d=simulate(name,body,['v(vsys)','i(BD5)','i(BD2)'],.005,1e-6,a.ngspice)
       switch.append(dict(case=name,load_A=current,min_VSYS_after_1ms=float(d[d[:,0]>.001,1].min()),max_VSYS=float(d[:,1].max()),headroom_3V3_V=float(d[d[:,0]>.001,1].min()-3.3),usb_reverse_A=float(min(d[:,2].min(),0)),external_reverse_A=float(min(d[:,3].min(),0))))
    # Input hot plug / reverse DC boundary; ideal controller, excludes turnoff delay and reverse recovery.
    inputs=[]
    for rsrc in [.05,.2,.5]:
     body=f'''Vinput src 0 PWL(0 0 100u 9 20m 9 20.001m 0)
Rsource src fused {rsrc:g}
Bideal fused vm I=max(v(fused,vm)/0.0033,0)
Cbulk vm 0 {meta['vm_bulk_nominal_F']:g}
Bload vm 0 I=4*min(max(v(vm)/6.5,0),1)
Rbleed vm 0 1e9'''
     name=f'input_switch_R{rsrc:g}';d=simulate(name,body,['v(vm)','i(Bideal)','i(Vinput)'],.03,2e-6,a.ngspice)
     t,v,i,_=d.T; start=t<.015
     inputs.append(dict(case=name,source_R_ohm=rsrc,peak_input_A=float(i.max()),startup_integral_A2s=float(np.trapezoid(i[start]**2,t[start])),pre_drop_VM_V=float(v[np.searchsorted(t,.019)]),reverse_A=float(min(i.min(),0)),min_VM_V=float(v.min())))
    thermal=[]
    for ambient in [25,40,60]:
      for current in [.5,1,1.352,1.481,1.613]:
       for theta in [41.1,60,80]:
        for rbridge in [.565,1.13]:
         power=current**2*rbridge
         thermal.append(dict(device='DRV8871',ambient_C=ambient,current_A=current,assumed_bridge_ohm=rbridge,theta_C_per_W=theta,conduction_W=power,Tj_conduction_only_C=ambient+power*theta,below125_conduction_only=ambient+power*theta<125))
    ldo=[dict(ambient_C=ta,VSYS_V=vin,current_A=i,power_W=(vin-3.3)*i,Tj_estimate_C=ta+(vin-3.3)*i*231.1) for ta in [25,40,60] for vin in [4.65,5.0,5.25] for i in [.05,.15]]
    # Efficiency includes external loss: treating ALL converter loss as IC heat is conservative,
    # but actual theta and actual efficiency still unknown; no self-consistent electrothermal model.
    buck_heat=[dict(ambient_C=ta,Iout_A=i,assumed_efficiency=eff,total_loss_W=5*i*(1/eff-1),theta_C_per_W=118.9,Tj_if_all_loss_in_IC_C=ta+5*i*(1/eff-1)*118.9) for ta in [25,40,60] for i in [.75,1.5,1.65] for eff in [.85,.90,.95]]
    for name,rows in [('regen',regen),('logic_switch',switch),('input_switch',inputs),('driver_thermal',thermal),('ldo_thermal',ldo),('buck_thermal',buck_heat)]:
      with (OUT/(name+'.csv')).open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n");w.writeheader();w.writerows(rows)
    # Charge conservation independently verifies the capacitor-only test subset.
    unclamped=[r for r in regen if r['TVS_energy_J']<1e-9]
    residual=max(abs(r['input_energy_J']-r['stored_delta_J']-r['TVS_energy_J']) for r in regen)
    assert residual<.001, residual
    assert all(abs(r['VM_max_V']-(9+r['injected_bus_A']*r['pulse_s']/r['cap_F']))<.01 for r in unclamped)
    meta.update({'state':'COMPLETED','ngspice_cases':len(regen)+len(switch)+len(inputs),'vendor_model_cases':0,'vendor_model_status':'BLOCKED_DOWNLOAD_HTTP_403','model_class':'original boundary surrogate, no vendor protection dynamics','max_energy_balance_residual_J':residual,'hardware_validated':False,'manufacturing_released':False})
    (OUT/'run-status.json').write_text(json.dumps(meta,indent=2)+'\n')
    os.environ.setdefault('XDG_CACHE_HOME','/tmp/quadcuber-cache')
    os.environ.setdefault('MPLCONFIGDIR','/tmp/quadcuber-matplotlib')
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(2,1,figsize=(9,6),layout='constrained')
    for duration,d in selected.items():
      ax[0].plot(d[:,0]*1e3,d[:,1],label=f'{duration*1000:g} ms bus-current injection')
      ax[1].plot(d[:,0]*1e3,d[:,1]*d[:,2])
    ax[0].axhline(12,c='red',ls='--',label='12 V TVS standoff (not clamp)');ax[0].set_ylabel('VM (V)');ax[0].legend()
    ax[1].set_ylabel('TVS power (W)');ax[1].set_xlabel('Time (ms)')
    fig.suptitle('BOUNDARY MODEL ONLY: 6.452 A bus injection, 2256 uF, 14.7 V TVS knee')
    fig.savefig(OUT/'regen-boundary.png',dpi=160);plt.close(fig)
    print(json.dumps(meta,indent=2))
if __name__=='__main__':
 try:main()
 except Exception as exc:
  path=OUT/'run-status.json'
  state=json.loads(path.read_text()) if path.exists() else {}
  state.update(state='FAILED',error=repr(exc),manufacturing_released=False)
  path.write_text(json.dumps(state,indent=2)+'\n')
  raise
