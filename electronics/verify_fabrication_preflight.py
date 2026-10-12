#!/usr/bin/env python3
"""Read-only KiCad 10 manufacturing audit. Run with AppRun python3.11.
Exports to a temporary directory only; never saves the native board.
"""
import csv, hashlib, json, math, os, re, subprocess, tempfile
from pathlib import Path
from collections import Counter
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'electronics/quadcuber.kicad_pcb'
FAB=ROOT/'generated/electronics/fabrication-preview-NOT-RELEASED'
OUT=ROOT/'generated/electronics/release-preflight'; OUT.mkdir(parents=True,exist_ok=True)
APP=Path('/workspace/tools/kicad-10.0.7/squashfs-root/AppRun')
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
before=sha(SRC); b=p.LoadBoard(str(SRC)); mm=lambda n:round(p.ToMM(n),6)
v=lambda q:[mm(q.x),mm(q.y)]
fps={f.GetReference():f for f in b.GetFootprints()}
bom=list(csv.DictReader((ROOT/'generated/electronics/bom.csv').open()))
pos=list(csv.DictReader((ROOT/'generated/electronics/positions.csv').open()))
bm={r['Reference']:r for r in bom}; pm={r['Ref']:r for r in pos}
checks=[]
def check(name,ok,detail): checks.append({'check':name,'pass':bool(ok),'detail':detail})
check('BOM unique references',len(bm)==len(bom),len(bom));check('CPL unique references',len(pm)==len(pos),len(pos))
check('BOM/native reference set',set(bm)==set(fps),{'bom_only':sorted(set(bm)-set(fps)),'board_only':sorted(set(fps)-set(bm))})
groups=list(csv.DictReader((ROOT/'generated/electronics/bom-grouped.csv').open()))
group_errors=[]; grouped_refs=[]
for row in groups:
 refs=[r.strip() for r in row['References'].split(';')];grouped_refs.extend(refs)
 if any(r not in bm for r in refs):group_errors.append(row['References']);continue
 if sum(int(bm[r]['Quantity']) for r in refs)!=int(row['Quantity']):group_errors.append(row['References']+' quantity')
 for ref in refs:
  if any(row[k]!=bm[ref][k] for k in ['Value','Manufacturer','MPN','Footprint','Notes']):group_errors.append(ref+' metadata')
check('Grouped BOM matches individual BOM',not group_errors and Counter(grouped_refs)==Counter(bm.keys()),group_errors)
errors=[]
for ref,r in pm.items():
 f=fps.get(ref)
 if not f: errors.append([ref,'absent native']);continue
 expected=[*v(f.GetPosition()),f.GetOrientationDegrees()]
 if abs(float(r['PosX'])-expected[0])>1e-5 or abs(float(r['PosY'])+expected[1])>1e-5 or abs((float(r['Rot'])-expected[2]+180)%360-180)>1e-5 or r['Side']!=('bottom' if f.IsFlipped() else 'top') or r['Package']!=str(f.GetFPID().GetLibItemName()):errors.append([ref,r,expected])
check('CPL/native XY rotation side package',not errors,errors)
errors=[]
for ref,r in bm.items():
 f=fps.get(ref)
 if f and (r['Value']!=f.GetValue() or r['Footprint'].split(':')[-1]!=str(f.GetFPID().GetLibItemName())):errors.append(ref)
check('BOM/native value footprint',not errors,errors)
dnp=sorted(ref for ref,f in fps.items() if f.IsDNP())
check('Native DNP has BOM quantity zero',all(bm[r]['Quantity']=='0' for r in dnp),dnp)
zero=sorted(r for r in bm if int(bm[r]['Quantity'])==0)
check('Default CPL excludes every zero-quantity/DNP reference',not set(zero)&set(pm),sorted(set(zero)&set(pm)))
# Prepare safe filtered assembly metadata; preserve original and document selection.
for filename,rows,fields in [('fabrication-populated-bom.csv',[r for r in bom if int(r['Quantity'])>0],list(bom[0])),('fabrication-populated-positions.csv',[r for r in pos if r['Ref'] in bm and int(bm[r['Ref']]['Quantity'])>0 and not fps[r['Ref']].IsDNP()],list(pos[0]))]:
 with (OUT/filename).open('w',newline='') as f:w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)
check('Positive BOM references present in CPL',all(ref in pm for ref in bm if int(bm[ref]['Quantity'])>0),sorted(ref for ref in bm if int(bm[ref]['Quantity'])>0 and ref not in pm))
# Native drill records normalized to center/diameter/slot total length.
def key(x,y,dx,dy):return tuple(round(z,6) for z in (x,y,min(dx,dy),max(dx,dy)))
native={'PTH':Counter(),'NPTH':Counter()}; ann=[]; pads=[]; via_types=Counter(); widths=[]
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA):
  x,y=v(t.GetPosition());d=mm(t.GetDrillValue());dia=min(mm(t.GetWidth(layer)) for layer in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]);native['PTH'][key(x,-y,d,d)]+=1;ann.append({'class':'via','reference':t.m_Uuid.AsString(),'diameter_mm':dia,'drill_mm':d,'annular_mm':round((dia-d)/2,6)});via_types[str(t.GetViaType())]+=1
 else:widths.append(mm(t.GetWidth()))
for ref,f in fps.items():
 for a in f.Pads():
  dx,dy=v(a.GetDrillSize());x,y=v(a.GetPosition());sx,sy=v(a.GetSize())
  if dx:
   cl='NPTH' if a.GetAttribute()==p.PAD_ATTRIB_NPTH else 'PTH';native[cl][key(x,-y,dx,dy)]+=1
   if cl=='PTH':ann.append({'class':'component_pad','reference':ref+'.'+a.GetNumber(),'diameter_mm':[sx,sy],'drill_mm':[dx,dy],'annular_mm':round(min((sx-dx)/2,(sy-dy)/2),6),'offset_mm':v(a.GetOffset())})
  if ref.startswith(('D','U','Q','J')) or 'CP_' in str(f.GetFPID().GetLibItemName()):pads.append({'reference':ref,'pad':a.GetNumber(),'net':a.GetNetname(),'xy_mm':[x,y],'side':'bottom' if f.IsFlipped() else 'top','rotation_deg':f.GetOrientationDegrees()})
for cl in native:
 tools={};found=Counter();tool=None
 for line in (FAB/f'quadcuber-{cl}.drl').read_text().splitlines():
  m=re.fullmatch(r'T(\d+)C([\d.]+)',line)
  if m:tools[m[1]]=float(m[2]);continue
  m=re.fullmatch(r'T(\d+)',line)
  if m:tool=m[1];continue
  m=re.fullmatch(r'X(-?[\d.]+)Y(-?[\d.]+)(?:G85X(-?[\d.]+)Y(-?[\d.]+))?',line)
  if m:
   x,y=float(m[1]),float(m[2]);d=tools[tool]
   if m[3]:ex,ey=float(m[3]),float(m[4]);found[key((x+ex)/2,(y+ey)/2,d,d+math.hypot(ex-x,ey-y))]+=1
   else:found[key(x,y,d,d)]+=1
 unmatched=list(found.elements()); deviations=[]; missing=[]
 for hole in native[cl].elements():
  candidates=[(max(abs(hole[i]-h[i]) for i in range(4)),j) for j,h in enumerate(unmatched) if abs(hole[2]-h[2])<1e-6 and abs(hole[3]-h[3])<1e-6]
  distance,j=min(candidates,default=(1e9,-1))
  if distance<=0.000501: deviations.append(distance);unmatched.pop(j)
  else:missing.append(hole)
 check(cl+' Excellon geometry/diameter/slot/count equals native',not missing and not unmatched,{'native_count':sum(native[cl].values()),'export_count':sum(found.values()),'coordinate_tolerance_mm':0.000501,'max_coordinate_quantization_mm':round(max(deviations,default=0),6),'native_only':missing,'export_only':unmatched,'diameter_histogram':dict(Counter({str(d):sum(n for k,n in found.items() if k[2]==d) for d in sorted({k[2] for k in found})}))})
# Verify every plotted image against independent fresh read-only exports, ignoring only timestamps.
def normalized(path):return '\n'.join(line for line in path.read_text().splitlines() if not any(s in line for s in ['TF.CreationDate','G04 Created by KiCad','; DRILL file KiCad']))
with tempfile.TemporaryDirectory(prefix='quadcuber-fabrication-') as td:
 env=dict(os.environ);env.update(XDG_CONFIG_HOME=td+'/config',XDG_DATA_HOME=td+'/data',XDG_CACHE_HOME=td+'/cache')
 for args in [['gerbers','--layers','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,F.Paste,B.Paste,Edge.Cuts','--subtract-soldermask'],['drill','--excellon-separate-th']]:
  proc=subprocess.run([str(APP),'kicad-cli','pcb','export',*args,'-o',td+'/',str(SRC)],env=env,capture_output=True,text=True)
  check('Fresh export '+args[0],proc.returncode==0,proc.stdout+proc.stderr)
 fresh_job=json.loads((Path(td)/'quadcuber-job.gbrjob').read_text());old_job=json.loads((FAB/'quadcuber-job.gbrjob').read_text())
 check('Gerber job native stackup/specs/rules fresh export',all(fresh_job[k]==old_job[k] for k in ['GeneralSpecs','MaterialStackup','DesignRules','FilesAttributes']),'CreationDate only excluded from job comparison')
 for old in sorted(FAB.iterdir()):
  if old.suffix in ['.gtl','.g1','.g2','.gbl','.gts','.gbs','.gto','.gbo','.gtp','.gbp','.gm1','.drl']:
   new=Path(td)/old.name;check('Export freshness '+old.name,new.exists() and normalized(old)==normalized(new),'Only creation timestamps ignored')
edge=[]
for item in b.GetDrawings():
 if item.GetLayer()==p.Edge_Cuts:edge.extend([v(item.GetStart()),v(item.GetEnd())])
xs=[a[0] for a in edge];ys=[a[1] for a in edge]
bounds=[min(xs),min(ys),max(xs),max(ys)];dims=[round(max(xs)-min(xs),6),round(max(ys)-min(ys),6)]
job=json.loads((FAB/'quadcuber-job.gbrjob').read_text());pro=json.loads((ROOT/'electronics/quadcuber.kicad_pro').read_text())
check('Copper layers/job/native',b.GetCopperLayerCount()==job['GeneralSpecs']['LayerNumber']==4,[x for x in job['FilesAttributes'] if x['FileFunction'].startswith('Copper')])
stack=job['MaterialStackup'];thick=sum(x.get('Thickness',0) for x in stack)
check('Stack total nominal thickness',abs(thick-job['GeneralSpecs']['BoardThickness'])<1e-8,thick)
check('Native source unchanged',sha(SRC)==before,sha(SRC))
report={'tool':p.Version(),'source_sha256':before,'checks':checks,'all_automatic_checks_pass':all(c['pass'] for c in checks),'native_footprints':len(fps),'bom_rows':len(bom),'cpl_rows':len(pos),'populated_quantity':sum(int(r['Quantity']) for r in bom),'dnp':dnp,'zero_quantity_in_original_cpl':sorted(set(zero)&set(pm)),'native_edge_centerline_bounds_mm':bounds,'native_edge_centerline_size_mm':dims,'gerber_job_stroke_bounding_size_mm':job['GeneralSpecs']['Size'],'stackup':stack,'design_rules':pro['board']['design_settings']['rules'],'mask_setup':{'expansion_mm':mm(b.GetDesignSettings().m_SolderMaskExpansion),'min_web_mm':mm(b.GetDesignSettings().m_SolderMaskMinWidth),'allow_bridges_in_footprints':b.GetDesignSettings().m_AllowSoldermaskBridgesInFPs},'minimum_track_width_mm':min(widths),'track_count':len(widths),'via_count':sum(via_types.values()),'dnp_cpl_risk':'Default export excludes DNP; positive BOM/CPL equality is checked. These outputs retain through-hole populated parts, not an SMT-only job; machine rotation and process still require assembly review.','annular_min_by_class':{cl:min((a for a in ann if a['class']==cl),key=lambda a:a['annular_mm']) for cl in ['via','component_pad']},'annular_distribution':dict(Counter(str(a['annular_mm']) for a in ann)),'plated_pad_offset_nonzero':[a for a in ann if a.get('offset_mm',[0,0])!=[0,0]],'via_types':dict(via_types),'original_files_sha256':{str(f.relative_to(ROOT)):sha(f) for f in [SRC,ROOT/'electronics/quadcuber.kicad_pro',ROOT/'generated/electronics/bom.csv',ROOT/'generated/electronics/positions.csv',*sorted(FAB.iterdir())] if f.is_file()},'polarity_limit':'Pad/net/position table is a static assembly aid, not independent MPN pin-1 or feeder rotation validation; connector user drawing still needs physical orientation and pin mapping verification.'}
(OUT/'fabrication-preflight.json').write_text(json.dumps(report,indent=2)+'\n')
with (OUT/'fabrication-polarity-padmap.csv').open('w',newline='') as f:w=csv.DictWriter(f,list(pads[0]));w.writeheader();w.writerows(pads)
print(json.dumps({k:report[k] for k in ['all_automatic_checks_pass','native_footprints','bom_rows','cpl_rows','populated_quantity','dnp','zero_quantity_in_original_cpl','native_edge_centerline_size_mm','annular_min_by_class','mask_setup','minimum_track_width_mm']},indent=2));print('FAILURES',json.dumps([c for c in checks if not c['pass']],indent=2))
raise SystemExit(0 if report['all_automatic_checks_pass'] else 1)
