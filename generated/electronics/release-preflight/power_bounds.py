#!/usr/bin/env python3
"""Read-only source/native/BOM audit and algebraic bounds, not a regulator simulation."""
from pathlib import Path
import csv,hashlib,json,math,re,runpy,subprocess,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).parent
C={x['ref']:x for x in runpy.run_path(str(ROOT/'electronics/circuit.py'))['C']}
bom={x['Reference']:x for x in csv.DictReader((ROOT/'generated/electronics/bom.csv').open())}
xml=ET.parse(ROOT/'generated/electronics/netlist.xml')
xpins={(n.get('ref'),n.get('pin')):net.get('name') for net in xml.findall('./nets/net') for n in net.findall('node')}
# KiCad native S-expression parser avoids importing a mismatched system pcbnew 9 for this KiCad10 file.
tokens=iter(re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',(ROOT/'electronics/quadcuber.kicad_pcb').read_text()))
def sexpr():
 a=[]
 for t in tokens:
  if t=='(': a.append(sexpr())
  elif t==')': return a
  else:a.append(json.loads(t) if t.startswith('"') else t)
 return a
root=sexpr()[0]
fp={next(x[2] for x in f if isinstance(x,list) and x[:2]==['property','Reference']):f for f in root if isinstance(f,list) and f[:1]==['footprint']}
ppins={(r,p[1]):next((v[1] for v in p if isinstance(v,list) and v[:1]==['net']),None) for r,f in fp.items() for p in f if isinstance(p,list) and p[:1]==['pad']}
refs=['F1','U4','Q1','D3','D4','R500','R501','C2','C3','C102','C122','C142','C162']
refs+=['U2','U3','L1','L2']+[f'C{n}' for n in [20,21,22,23,24,25,30,31,32,33,34,35]]+[f'R{n}' for n in [21,22,23,24,31,32,33,34]]
for r in refs:
 assert bom[r]['MPN']==C[r]['mpn'],r
 assert next(x[2] for x in fp[r] if isinstance(x,list) and x[:2]==['property','MPN'])==C[r]['mpn'],r
 for p,n in C[r]['pins'].items():
  assert xpins[(r,str(p))]==n,(r,p,'XML')
  assert ppins[(r,str(p))]==n,(r,p,'PCB')
for r in ['R20','R30']:assert r not in C and r not in fp and r not in bom
for r in ['C26','C36']:assert C[r]['dnp'] and bom[r]['Quantity']=='0'
assert all('BOOT_CAP' not in n for n in ppins.values() if n)
feedback=[]
for dt in [0,15,40,65,100]:
 qhi=100e3*(1.001)*(1+25e-6*dt)/(13.3e3*.999*(1-25e-6*dt))
 qlo=100e3*(.999)*(1-25e-6*dt)/(13.3e3*1.001*(1+25e-6*dt))
 lo=.581*(1+qlo);hi=.611*(1+qhi)
 feedback.append(dict(delta_from_25_C=dt,low_V=lo,high_V=hi,low_budget_mV=(lo-4.75)*1e3,high_budget_mV=(5.25-hi)*1e3))
vnom=.596*(1+100/13.3)
fmin=290e3; lmin=8e-6; vinmax=9.18
ripple=5.25*(vinmax-5.25)/(vinmax*lmin*fmin)
cap=[]
for cf in [.4,.8,1.0,1.2]:
 co=44e-6*cf
 cap.append(dict(assumed_factor=cf,Cout_uF=co*1e6,fo_no_Cff_kHz=5.1/(vnom*co)/1e3,step_B_two_cycle_drop_V=2*1.45/(fmin*co),ripple_cap_V=ripple/(8*fmin*co),Cin_uF=10*cf,Cin_ripple_no_ESR_V=1.5*.25/(10e-6*cf*fmin)))
cmin=6*470e-6*.8;cmax=6*470e-6*1.2;rmax=151.5;v0=9.18;E=.05
vp=math.sqrt(v0*v0+2*E/cmin)
regen=dict(C_min_F=cmin,C_max_F=cmax,VM_initial_V=v0,E_per_whole_board_event_J=E,Vpeak_ideal_C_V=vp,energy_to_12V_J=.5*cmin*(12**2-v0**2),return_to_9p18_ms=rmax*cmin*math.log(vp/v0)*1e3,minimum_quiet_gap_ms=100,bleed_power_each_12V_W=12**2/(300*.99),bleed_power_each_peak_W=vp**2/(300*.99),E_times_5Hz_W=.25,cold_start_charge_C=cmax*v0,ramp_100ms_cap_current_A=cmax*v0/.1)
thermal=[]
for ta in [25,40]:
 for i in [.25,.75,1.5]:
  for eta in [.85,.9,.95]:
   loss=5.25*i*(1/eta-1)
   thermal.append(dict(Ta_C=ta,Iout_A=i,assumed_efficiency=eta,all_converter_loss_W=loss,Tj_using_118p9_C=ta+118.9*loss,Tj_using_EVM_57p2_C=ta+57.2*loss))
result=dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),scope='algebraic bounds; source/native/BOM contract; no macro-model run',contract_refs=refs,contract='PASS',hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['electronics/circuit.py','electronics/quadcuber.kicad_pcb','generated/electronics/netlist.xml','generated/electronics/bom.csv']},feedback=dict(nominal_V=vnom,corners=feedback,warning='VFB limits specified at VIN12V; resistor temperatures independent; no line/load, aging, FB bias or dynamic guarantee'),caps=dict(curves='UNAVAILABLE official403; all capacitance factors/3mOhm remain assumptions',corners=cap,inductor_ripple_pp_A=ripple,peak_at_1p5_A=1.5+ripple/2,output_C_for_40kHz_uF=5.1/(feedback[-1]['low_V']*40000)*1e6,output_C_for_B_1p45A_step_250mV_290kHz_uF=2*1.45/(fmin*.25)*1e6,output_C_for_B_step_low_PVT_budget_uF=2*1.45/(fmin*(feedback[-1]['low_V']-4.75))*1e6,input_C_for_400mV_1p5A_290kHz_no_ESR_uF=1.5*.25/(fmin*.4)*1e6),regen=regen,thermal=thermal,joint_input_current_A={str(v):3+5.25*3/(.85*v)+v/148.5 for v in [8,8.82,9.18]},motor_ILIM_range_A=[59/(43.2*1.01),69/(43.2*.99)],thermal_IC_loss_budget_Ta40_Tj125_W=(125-40)/118.9)
(OUT/'power-bounds.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['contract','feedback','caps','regen','joint_input_current_A']},indent=2))
