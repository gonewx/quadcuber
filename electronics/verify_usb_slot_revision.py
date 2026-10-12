#!/usr/bin/env python3
"""Independent USB shield-slot regression contract. Run under KiCad10 Python.
Baseline defaults to /workspace/a1-jlc-baseline; --label red/green names evidence.
Permitted delta: four S1 pad sizes, five enumerated USB_VBUS segments, refilled polygons.
"""
import argparse,ast,hashlib,json,re,sys
from decimal import Decimal,InvalidOperation
from pathlib import Path
import pcbnew as p
H=Path(__file__).resolve().parent;ROOT=H.parent
NAME='USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal'
parser=argparse.ArgumentParser();parser.add_argument('--baseline',type=Path,default=Path('/workspace/a1-jlc-baseline'));parser.add_argument('--label',default='green');args=parser.parse_args()
OUT=ROOT/'generated/electronics/release-preflight/jlc-implementation';OUT.mkdir(exist_ok=True,parents=True)
checks=[]
def check(name,ok,detail=None):checks.append({'check':name,'pass':bool(ok),'detail':detail})
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
vec=lambda x:[x.x,x.y]
def padrow(a):
 return {'uuid':a.m_Uuid.AsString(),'number':a.GetNumber(),'size_nm':vec(a.GetSize()),'drill_nm':vec(a.GetDrillSize()),'position_nm':vec(a.GetPosition()),'offset_nm':vec(a.GetOffset()),'orientation':a.GetOrientationDegrees(),'layers':list(a.GetLayerSet().Seq()),'net':a.GetNetname(),'shape':int(a.GetShape()),'attribute':int(a.GetAttribute()),'drill_shape':int(a.GetDrillShape())}
def rows(fp):
 result={}
 for a in fp.Pads():
  row=padrow(a);row.pop('uuid');key=str((row['number'],row['position_nm'],row['drill_nm']));result[key]=row
 return result
def shields(fp):return [a for a in fp.Pads() if a.GetNumber()=='S1']
IO=p.PCB_IO_KICAD_SEXPR()
def footprint(path):return IO.FootprintLoad(str(path.parent),path.stem)
oldpcb=args.baseline/'quadcuber.kicad_pcb';newpcb=H/'quadcuber.kicad_pcb';oldlib=args.baseline/(NAME+'.kicad_mod');newlib=H/'lib/Quadcuber.pretty'/(NAME+'.kicad_mod')
oldb=p.LoadBoard(str(oldpcb));newb=p.LoadBoard(str(newpcb));oldfp=next(f for f in oldb.GetFootprints() if f.GetReference()=='J5');newfp=next(f for f in newb.GetFootprints() if f.GetReference()=='J5')
oldlf=footprint(oldlib);newlf=footprint(newlib);expected_target_sizes={(600000,1700000):[1108000,2208000],(600000,1400000):[1108000,1908000]}
VBUS_SEGMENTS={
 '1c9cde93-6b13-45a4-931d-3873bbf8384b':([75118500,55049600],[75118500,57659300]),
 '798bdb25-1303-4523-bcb3-bd55121a7036':([78812900,55049600],[75118500,55049600]),
 'cc9f98a0-4228-4c78-8163-aa595ae3845c':([75118500,55049600],[63025100,55049600]),
 'd45ae99b-2573-4fd8-8747-c22624b25667':([75118500,57659300],[74545700,58232100]),
 '83e1a1c5-9865-47ec-8c64-46ecab0ba978':([74545700,58232100],[72827100,58232100]),
}
MOVED_NODES={(75118500,55049600),(75118500,57659300),(74545700,58232100)}
def moved(point):return [point[0]+60000,point[1]] if tuple(point) in MOVED_NODES else point
changes={}
for scope,old,new in [('native',oldfp,newfp),('library',oldlf,newlf)]:
 a,b=rows(old),rows(new);changed=[];geometry_ok=a.keys()==b.keys();check(scope+' exactly four S1 shield pads',len(shields(new))==4,len(shields(new)))
 for pad in shields(new):
  row=padrow(pad);target=expected_target_sizes.get(tuple(row['drill_nm']));ring=min((s-d)/2e6 for s,d in zip(row['size_nm'],row['drill_nm']))
  check(scope+' shield target '+row['uuid'],row['size_nm']==target and abs(ring-.254)<1e-9,{'size_mm':[s/1e6 for s in row['size_nm']],'drill_mm':[d/1e6 for d in row['drill_nm']],'ring_mm':ring,'position_mm':[x/1e6 for x in row['position_nm']]})
 for ident in a.keys()&b.keys():
  if a[ident]!=b[ident]:changed.append({'before':a[ident],'after':b[ident]})
  expected=dict(a[ident])
  if a[ident]['number']=='S1':expected['size_nm']=expected_target_sizes[tuple(a[ident]['drill_nm'])]
  geometry_ok &= b[ident]==expected
 check(scope+' exactly four changed pads, only permitted size delta',geometry_ok and len(changed)==4,{'changed_pad_count':len(changed)})
 changes[scope]=changed
old_tracks={t.m_Uuid.AsString():t for t in oldb.GetTracks()};new_tracks={t.m_Uuid.AsString():t for t in newb.GetTracks()}
route_changes=[]
for ident,(start,end) in VBUS_SEGMENTS.items():
 a=old_tracks[ident];b=new_tracks[ident];actual={'start_nm':vec(b.GetStart()),'end_nm':vec(b.GetEnd()),'width_nm':b.GetWidth(),'layer':p.LayerName(b.GetLayer()),'net':b.GetNetname()}
 ok=vec(a.GetStart())==start and vec(a.GetEnd())==end and actual=={'start_nm':moved(start),'end_nm':moved(end),'width_nm':150000,'layer':'F.Cu','net':'USB_VBUS'}
 check('authorized VBUS clearance segment '+ident,ok,actual)
 route_changes.append({'uuid':ident,'before':{'start_nm':vec(a.GetStart()),'end_nm':vec(a.GetEnd())},'after':actual})
changes['vbus_clearance_segments']=route_changes
# Semantic S-expression comparison: do not hide any other routing, artwork,
# footprint geometry, net, layer, stackup or design-rule change.
def sexpr(path):
 toks=re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',path.read_text());stack=[];root=None
 for t in toks:
  if t=='(':
   a=[]
   if stack:stack[-1].append(a)
   else:root=a
   stack.append(a)
  elif t==')':stack.pop()
  else:
   try:t=str(Decimal(t).normalize())
   except InvalidOperation:pass
   stack[-1].append(t)
 return root
def tag(a):return a[0] if isinstance(a,list) and a else None
def normalize(tree,library=False):
 def walk(node,in_target=False):
  if not isinstance(node,list):return node
  if tag(node)=='footprint':in_target=library or any(tag(x)=='property' and x[1:3]==['"Reference"','"J5"'] for x in node if isinstance(x,list))
  if tag(node)=='segment':
   ident=next((x[1].strip('"') for x in node if tag(x)=='uuid'),None)
   if ident in VBUS_SEGMENTS:
    start,end=VBUS_SEGMENTS[ident];original={'start':start,'end':end}
    node=[([x[0],*[str(Decimal(v)/Decimal(1000000)) for v in original[x[0]]]] if tag(x) in original else x) for x in node]
  if in_target and tag(node)=='pad' and node[1]=='"S1"':
   node=[x for x in node];drill=next(x for x in node if tag(x)=='drill');oldheight='2.1' if drill[-1]=='1.7' else '1.8'
   node=[['size','1',oldheight] if tag(x)=='size' else x for x in node]
  result=[walk(x,in_target) for x in node if tag(x) not in ['filled_polygon','fill_segments']]
  if tag(node) in ['kicad_pcb','footprint']:
   scalars=[x for x in result if not isinstance(x,list)];children=[x for x in result if isinstance(x,list)];result=scalars+sorted(children,key=lambda x:json.dumps(x,sort_keys=True))
  return result
 return walk(tree,library)
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
def differences(a,b,path='root'):
 if type(a)!=type(b):return [path+': type']
 if isinstance(a,list):
  out=[]
  if len(a)!=len(b):out.append(path+f': length {len(a)} vs {len(b)}')
  for i,(x,y) in enumerate(zip(a,b)):
   if x!=y:out+=differences(x,y,path+f'/{i}')
   if len(out)>30:break
  return out
 return [] if a==b else [path+f': {a!r} vs {b!r}']
for scope,old,new,library in [('native',oldpcb,newpcb,False),('library',oldlib,newlib,True)]:
 a=normalize(sexpr(old),library);b=normalize(sexpr(new),library)
 check(scope+' all other semantic data unchanged',a==b,{'baseline_digest':digest(a),'current_digest':digest(b),'differences':differences(a,b)})
# Persistent source contract: actual generator must apply adapter after sourcing
# exactly this footprint, rather than only patching the checked-in output.
tree=ast.parse((H/'generate.py').read_text().split('# Self-contained native symbols')[0]);imported=any(isinstance(n,ast.ImportFrom) and n.module=='revise_usb_slots' and any(a.name=='adapt_usb_shield_slots_file' for a in n.names) for n in ast.walk(tree))
branches=[n for n in ast.walk(tree) if isinstance(n,ast.If) and any(isinstance(c,ast.Constant) and c.value==NAME for c in ast.walk(n.test))]
sourceok=imported and any(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='adapt_usb_shield_slots_file' for n in ast.walk(branch)) for branch in branches)
check('generator persists exact USB footprint text adapter',sourceok,{'adapter_import':imported,'matching_branches':len(branches)})
module=H/'revise_usb_slots.py'
if module.exists():
 import importlib.util
 spec=importlib.util.spec_from_file_location('usb_slot_adapter_under_test',module);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 specimen=footprint(oldlib);before=rows(specimen);mod.adapt_usb_shield_slots(specimen);first=rows(specimen);mod.adapt_usb_shield_slots(specimen);second=rows(specimen)
 expected={k:dict(v) for k,v in before.items()}
 for row in expected.values():
  if row['number']=='S1':row['size_nm']=expected_target_sizes[tuple(row['drill_nm'])]
 check('real adapter changes only target four pad sizes and is idempotent',first==expected and second==first)
 def track_rows(board):
  return {t.m_Uuid.AsString():{'start_nm':vec(t.GetStart()),'end_nm':vec(t.GetEnd()),'net':t.GetNetname(),'layer':t.GetLayer(),'width_nm':t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth(),'locked':t.IsLocked()} for t in board.GetTracks()}
 route_specimen=p.LoadBoard(str(oldpcb));route_expected=track_rows(route_specimen)
 for ident,(start,end) in VBUS_SEGMENTS.items():route_expected[ident]['start_nm']=moved(start);route_expected[ident]['end_nm']=moved(end)
 if hasattr(mod,'adapt_usb_vbus_clearance'):
  mod.adapt_usb_vbus_clearance(route_specimen);route_first=track_rows(route_specimen);mod.adapt_usb_vbus_clearance(route_specimen)
  check('real VBUS adapter changes only five allowed segments and is idempotent',route_first==route_expected and track_rows(route_specimen)==route_first)
 else:check('real VBUS adapter changes only five allowed segments and is idempotent',False,'route adapter absent')

 import tempfile
 with tempfile.TemporaryDirectory(prefix='usb-slot-contract-') as td:
  specimen_file=Path(td)/(NAME+'.kicad_mod');specimen_file.write_bytes(oldlib.read_bytes());mod.adapt_usb_shield_slots_file(specimen_file);once=specimen_file.read_bytes();mod.adapt_usb_shield_slots_file(specimen_file)
  check('file adapter changes only four size fields and is idempotent',normalize(sexpr(specimen_file),True)==normalize(sexpr(oldlib),True) and specimen_file.read_bytes()==once and len(re.findall(r'\(size 1\.108 (?:2\.208|1\.908)\)',once.decode()))==4)

else:check('real adapter changes only target four pad sizes and is idempotent',False,'adapter implementation absent in red phase')
report={'state':'PASS' if all(c['pass'] for c in checks) else 'FAIL','kicad':p.Version(),'baseline_dir':str(args.baseline),'label':args.label,'checks':checks,'changes':changes,'hashes':{str(f):sha(f) for f in [oldpcb,newpcb,oldlib,newlib,H/'generate.py']},'scope':'Only four S1 copper/paste/mask pad dimensions and five enumerated USB_VBUS segment endpoints may change. Zone filled_polygon/fill_segments caches may change upon refill; all other parsed PCB and footprint semantic data must match the frozen baseline.'}
(OUT/(args.label+'.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'state':report['state'],'checks':len(checks),'failures':[c for c in checks if not c['pass']]},indent=2));sys.exit(0 if report['state']=='PASS' else 1)
