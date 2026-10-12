#!/usr/bin/env python3
"""Export the checked-in native KiCad files. Does not regenerate placement/routing."""
import json,subprocess,os,re,sys,hashlib,tempfile,shutil,csv
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parent;O=R/'generated/electronics';O.mkdir(exist_ok=True,parents=True)
SCH=H/'quadcuber.kicad_sch';PCB=H/'quadcuber.kicad_pcb'
# Consolidated assembly BOM; DNP parts remain explicit quantity zero.
groups={}
with (O/'bom.csv').open() as f:
    for row in csv.DictReader(f):
        key=tuple(row[k] for k in ['Value','Manufacturer','MPN','Footprint'])
        g=groups.setdefault(key,{'refs':[],'qty':0,'notes':set()})
        g['refs'].append(row['Reference']);g['qty']+=int(row['Quantity'])
        if row['Notes']:g['notes'].add(row['Notes'])
with (O/'bom-grouped.csv').open('w') as f:
    w=csv.writer(f,lineterminator="\n");w.writerow(['References','Value','Manufacturer','MPN','Footprint','Quantity','Notes'])
    for key,g in groups.items():w.writerow(['; '.join(g['refs']),*key,g['qty'],' | '.join(sorted(g['notes']))])

cache=Path(tempfile.gettempdir())/'quadcuber-kicad'
env=os.environ.copy()
for key,leaf in [('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache'),('XDG_DATA_HOME','data')]:
    d=cache/leaf;d.mkdir(parents=True,exist_ok=True);env[key]=str(d)
commands=[]
def run(*args):
    args=list(map(str,args));result=subprocess.run(args,cwd=R,env=env,text=True,capture_output=True)
    commands.append({'command':args,'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
    if result.returncode: print(result.stdout,result.stderr);raise RuntimeError(args)
    return result.stdout
run('kicad-cli','sch','erc','-o',O/'erc.rpt',SCH)
run('kicad-cli','sch','export','netlist','--format','kicadxml','-o',O/'netlist.xml',SCH)
run('kicad-cli','sch','export','pdf','-o',O/'schematic.pdf',SCH)
run('kicad-cli','sch','export','svg','-o',str(O/'schematic')+'/',SCH)
run('kicad-cli','pcb','drc','--schematic-parity','-o',O/'drc.rpt',PCB)
for name,layers in [('pcb-top','F.Cu,F.Silkscreen,Edge.Cuts'),('pcb-bottom','B.Cu,B.Silkscreen,Edge.Cuts'),('assembly','F.Fab,Edge.Cuts'),('assembly-bottom','B.Fab,Edge.Cuts'),('ground-plane','In1.Cu,Edge.Cuts'),('vm-plane','In2.Cu,Edge.Cuts')]:
    run('kicad-cli','pcb','export','svg','--mode-single','--fit-page-to-board','--exclude-drawing-sheet','--layers',layers,'-o',O/(name+'.svg'),PCB)
if shutil.which('inkscape'):
    for name in ['pcb-top','pcb-bottom','assembly','assembly-bottom']:
        run('inkscape',O/(name+'.svg'),'--export-type=png','--export-filename='+str(O/(name+'.png')),'--export-width=1440')
fab=O/'fabrication-preview-NOT-RELEASED';fab.mkdir(exist_ok=True)
run('kicad-cli','pcb','export','gerbers','--layers','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,F.Paste,B.Paste,Edge.Cuts','--subtract-soldermask','-o',str(fab)+'/',PCB)
run('kicad-cli','pcb','export','drill','--excellon-separate-th','--generate-map','--map-format','svg','-o',str(fab)+'/',PCB)
run('kicad-cli','pcb','export','pos','--format','csv','--units','mm','--side','both','-o',O/'positions.csv',PCB)
run('/usr/bin/python3',H/'check.py')
erc=(O/'erc.rpt').read_text();drc=(O/'drc.rpt').read_text()
count=lambda pat,txt:int(re.search(pat,txt).group(1)) if re.search(pat,txt) else None
status={'revision':'A1','manufacturing_release':False,'hardware_tested':False,'erc_errors':count(r'Errors (\d+)',erc),'erc_warnings':count(r'Warnings (\d+)',erc),'drc_violations':count(r'Found (\d+) DRC violations',drc),'footprint_errors':count(r'Found (\d+) Footprint errors',drc),'unconnected_pads':count(r'Found (\d+) unconnected',drc),'release_blockers':['EV3 hole geometry updated from user drawing; actual MPN, pin numbers 1-5/view, contact rating and full ear envelope remain unconfirmed','New mounting bracket/feet and cable-motion clearance not finalized','Prototype concurrent-load, regenerative transient, thermal and power-combination tests outstanding','First-board RP2040 UF2 boot and USB host-off data-pin backfeed tests outstanding; USB impedance stackup requires fabricator approval'],'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(p for p in H.glob('*.kicad_*') if p.suffix in ['.kicad_sch','.kicad_pcb','.kicad_pro','.kicad_dru'])},'tool_version':run('kicad-cli','version').strip()}
(O/'release-status.json').write_text(json.dumps(status,indent=2)+'\n')
(O/'build-log.json').write_text(json.dumps(commands,indent=2)+'\n')
(fab/'DO_NOT_FABRICATE.txt').write_text('ENGINEERING PREVIEW ONLY - NOT RELEASED\nEV3 geometry follows user drawing; PINMAP/MPN/CURRENT remain HOLD. Read electronics/README.md.\n'+json.dumps(status,indent=2)+'\n')
# KiCad SVG exporter leaves trailing spaces; normalize formatting only.
for svg in O.rglob('*.svg'):
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
print(json.dumps(status,indent=2))

if any(status[k] != 0 for k in ['erc_errors','erc_warnings','drc_violations','unconnected_pads','footprint_errors']):
    raise SystemExit('EDA checks failed; exported files remain engineering previews. See reports.')
