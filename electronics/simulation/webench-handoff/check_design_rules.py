#!/usr/bin/env python3
"""Finite algebraic checks from TPS54302 Rev C; no converter simulation or PCB edits."""
import itertools,json,math,runpy,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[3];D=Path(__file__).parent
c={p['ref']:p for p in runpy.run_path(str(R/'electronics/circuit.py'))['C']}
for r,v in {'R20':'49.9','R30':'49.9','R23':'511k','R33':'511k','R24':'105k','R34':'105k','R21':'100k','R31':'100k','R22':'13.3k','R32':'13.3k'}.items():assert c[r]['value']==v
assert c['R20']['pins']=={'1':'B1_BOOT','2':'B1_BOOT_CAP'}
a,b=511e3,105e3;ip,ih=.7e-6,1.55e-6
start=lambda x,y,v=1.23,i=ip:v*(1+x/y)-i*x
stop=lambda x,y,v=1.16,i=ip+ih:v*(1+x/y)-i*x
corners=[(a*x,b*y) for x,y in itertools.product([.99,1.01],repeat=2)]
enpoints=[]
for vin in [8.82,9,9.18,12,28]:
 vals=[(vin/x+ip+ih)/(1/x+1/y) for x,y in corners]
 enpoints.append({'vin_V':vin,'en_typ_current_resistor_corner_V':[min(vals),max(vals)]})
vouts=[v*(1+100e3*x/(13.3e3*y)) for v,x,y in itertools.product([.581,.611],[.99,1.01],[.99,1.01])]
fc=[{'factor':f,'total_C_uF':44*f,'f0_est_Hz':5.1/(.596*(1+100/13.3)*44e-6*f),'Cff_rule_pF':1/(2*math.pi*(5.1/(.596*(1+100/13.3)*44e-6*f))*100e3)*1e12} for f in [.4,.8,1,1.2]]
out={'source':'https://www.ti.com/lit/ds/symlink/tps54302.pdf Rev C sections 5.5,6.3.5,7.2.3; Yageo F resistors ±1%', 'pcb_sha256':hashlib.sha256((R/'electronics/quadcuber.kicad_pcb').read_bytes()).hexdigest(),'EN':{'start_typ_V':start(a,b),'stop_typ_V':stop(a,b),'hysteresis_typ_V':start(a,b)-stop(a,b),'start_resistor_only_corners_V':[min(start(x,y) for x,y in corners),max(start(x,y) for x,y in corners)],'stop_resistor_only_corners_V':[min(stop(x,y) for x,y in corners),max(stop(x,y) for x,y in corners)],'startup_upper_conditional_ignore_positive_pullup_V':max(start(x,y,1.28,0) for x,y in corners),'ramp_1ms_9V_start_typ_ms':start(a,b)/9,'points':enpoints,'limits':'Ip/Ih have typical values only; resistor corners are not guaranteed total PVT bounds. Upper conditional assumes no negative net EN current.'},'feedback':{'typ_V':.596*(1+100/13.3),'independent_vref_resistor_corners_V':[min(vouts),max(vouts)],'above_5V25_by_V':max(vouts)-5.25,'limits':'Conservative static independent corners, excludes FB input current, line/load regulation, dynamics; no measured failure claim.'},'BOOT':{'series_R_ohm':49.9,'C_F':1e-7,'RC_s':49.9e-7,'switch_period_typ_s':1/400e3,'limits':'RC only, not effective gate-drive model; gate charge and driver current unavailable. Reference 49.9 ohm is feedback loop injection, not BOOT.'},'output_cap_rule':{'minimum_C_at_typ_V_for_f0_below40k_uF':5.1/(.596*(1+100/13.3)*40e3)*1e6,'cases':fc,'limits':'TI rough crossover estimate before Cff, not phase-margin proof; factors are assumptions, not manufacturer DC-bias evidence.'}}
(D/'design-rule-results.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
