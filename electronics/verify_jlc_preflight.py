#!/usr/bin/env python3
"""Read-only JLCPCB candidate audit. System Python + shapely 2.x; subprocess KiCad10.
Run PYTHONPATH=/tmp/quadcuber-jlc-audit-deps python electronics/verify_jlc_preflight.py
Optional --extract JSON is called internally using KiCad's Python3.11.
No board/project/design edits. Geometry approximation bound 0.0001 mm.
"""
import sys,os,json,hashlib,tempfile,subprocess,math
from pathlib import Path
from collections import Counter,defaultdict
ROOT=Path(__file__).resolve().parents[1];PCB=ROOT/'electronics/quadcuber.kicad_pcb';OUT=ROOT/'generated/electronics/release-preflight'
APP=os.environ.get('KICAD_APP_RUN','/workspace/tools/kicad-10.0.7/squashfs-root/AppRun')
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
if '--extract' in sys.argv:
 import pcbnew as p
 b=p.LoadBoard(str(PCB));mm=lambda x:p.ToMM(x);xy=lambda q:[mm(q.x),mm(q.y)]
 def poly(ps):
  def chain(c):return [xy(c.CPoint(i)) for i in range(c.PointCount())]
  return [{'outer':chain(ps.COutline(i)),'holes':[chain(ps.CHole(i,j)) for j in range(ps.HoleCount(i))]} for i in range(ps.OutlineCount())]
 def geom(item,layer,clearance=0):
  ps=p.SHAPE_POLY_SET();item.TransformShapeToPolygon(ps,layer,p.FromMM(clearance),100,p.ERROR_INSIDE);return poly(ps)
 data={'source_sha256':sha(PCB),'kicad':p.Version(),'copper':[],'holes':[],'mask':[],'paste':[],'silk':[],'footprints':[],'thermal':[],'edge':[]}
 def base(item,ref,kind):return {'id':item.m_Uuid.AsString(),'ref':ref,'kind':kind,'net':item.GetNetname() if hasattr(item,'GetNetname') else ''}
 layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]
 for f in b.GetFootprints():
  ref=f.GetReference();data['footprints'].append({'ref':ref,'footprint':str(f.GetFPID().GetLibItemName()),'side':'bottom' if f.IsFlipped() else 'top','dnp':f.IsDNP()})
  for a in f.Pads():
   name=ref+'.'+a.GetNumber();attrs=base(a,name,'pad');attrs.update(footprint_ref=ref,pad=a.GetNumber(),attribute=int(a.GetAttribute()),xy=xy(a.GetPosition()),size_mm=xy(a.GetSize()),drill_mm=xy(a.GetDrillSize()))
   dx,dy=xy(a.GetDrillSize());sx,sy=xy(a.GetSize())
   thermal=ref in ['U1','U10','U11','U12','U13'] and dx>0 and a.GetNumber() in ['57','9']
   if dx:
    ps=p.SHAPE_POLY_SET();a.TransformHoleToPolygon(ps,0,100,p.ERROR_INSIDE)
    cl='npth' if a.GetAttribute()==p.PAD_ATTRIB_NPTH else 'thermal_pad_via_function' if thermal else 'component_pth'
    data['holes'].append({**attrs,'class':cl,'geom':poly(ps),'ring_mm':min((sx-dx)/2,(sy-dy)/2)})
   for l in layers:
    if a.IsOnLayer(l) and a.GetAttribute()!=p.PAD_ATTRIB_NPTH:data['copper'].append({**attrs,'layer':p.LayerName(l),'geom':geom(a,l)})
   for l in [p.F_Mask,p.B_Mask]:
    if a.IsOnLayer(l):data['mask'].append({**attrs,'layer':p.LayerName(l),'geom':geom(a,l,mm(a.GetSolderMaskExpansion(l)))})
   for l in [p.F_Paste,p.B_Paste]:
    if a.IsOnLayer(l):
     margin=a.GetSolderPasteMargin(l)
     if margin.x!=margin.y:raise RuntimeError('Anisotropic paste margin needs exact extraction')
     data['paste'].append({**attrs,'layer':p.LayerName(l),'geom':geom(a,l,mm(margin.x))})
  for g in [*f.GraphicalItems(),f.Reference(),f.Value()]:
   l=g.GetLayer()
   if l not in [p.F_Mask,p.B_Mask,p.F_Paste,p.B_Paste,p.F_SilkS,p.B_SilkS]:continue
   if hasattr(g,'IsVisible') and not g.IsVisible():continue
   cl='mask' if l in [p.F_Mask,p.B_Mask] else 'paste' if l in [p.F_Paste,p.B_Paste] else 'silk'
   rec={**base(g,ref+'.graphic',g.GetClass()),'layer':p.LayerName(l),'geom':geom(g,l)}
   if hasattr(g,'GetText'):rec.update(text=g.GetShownText(False),height_mm=mm(g.GetTextHeight()),width_mm=mm(g.GetTextThickness()))
   elif hasattr(g,'GetWidth'):rec['width_mm']=mm(g.GetWidth())
   data[cl].append(rec)
 for t in b.GetTracks():
  if isinstance(t,p.PCB_VIA):
   attrs=base(t,'via:'+t.m_Uuid.AsString(),'via');d=mm(t.GetDrillValue());x,y=xy(t.GetPosition());dia=min(mm(t.GetWidth(l)) for l in layers)
   data['holes'].append({**attrs,'class':'native_via','xy':[x,y],'drill_mm':[d,d],'diameter_mm':dia,'ring_mm':(dia-d)/2,'circle':[x,y,d/2]})
   for l in layers:
    if t.IsOnLayer(l):data['copper'].append({**attrs,'layer':p.LayerName(l),'geom':geom(t,l)})
  else:data['copper'].append({**base(t,'track:'+t.m_Uuid.AsString(),'track'),'layer':p.LayerName(t.GetLayer()),'width_mm':mm(t.GetWidth()),'geom':geom(t,t.GetLayer())})
 for z in b.Zones():
  for l in layers:
   if z.HasFilledPolysForLayer(l):data['copper'].append({**base(z,'zone:'+z.m_Uuid.AsString(),'zone'),'layer':p.LayerName(l),'geom':poly(z.GetFilledPolysList(l))})
 for g in b.GetDrawings():
  l=g.GetLayer()
  if l==p.Edge_Cuts:data['edge'].append({'start':xy(g.GetStart()),'end':xy(g.GetEnd())})
  if l in [p.F_SilkS,p.B_SilkS]:
   rec={**base(g,'board-graphic',g.GetClass()),'layer':p.LayerName(l),'geom':geom(g,l)}
   if hasattr(g,'GetText'):rec.update(text=g.GetShownText(False),height_mm=mm(g.GetTextHeight()),width_mm=mm(g.GetTextThickness()))
   elif hasattr(g,'GetWidth'):rec['width_mm']=mm(g.GetWidth())
   data['silk'].append(rec)
 Path(sys.argv[-1]).write_text(json.dumps(data));sys.exit()
from shapely.geometry import Polygon,Point,box
from shapely.ops import unary_union,clip_by_rect
from shapely.strtree import STRtree
from shapely import make_valid
from shapely.errors import GEOSException
def local_clip(shape,x0,y0,x1,y1):
 try:return clip_by_rect(shape,x0,y0,x1,y1)
 except GEOSException:return make_valid(shape).intersection(box(x0,y0,x1,y1))
with tempfile.TemporaryDirectory(prefix='jlc-audit-') as td:
 env=dict(os.environ);env.pop('PYTHONPATH',None);env.update(XDG_CONFIG_HOME=td+'/config',XDG_DATA_HOME=td+'/data',XDG_CACHE_HOME=td+'/cache')
 subprocess.run([APP,'python3.11',str(Path(__file__).resolve()),'--extract',td+'/geometry.json'],env=env,check=True)
 data=json.loads(Path(td+'/geometry.json').read_text())
def geometry(r):
 if 'circle' in r:x,y,d=r['circle'];return Point(x,y).buffer(d,quad_segs=128)
 return unary_union([make_valid(Polygon(q['outer'],q['holes'])) for q in r['geom'] if len(q['outer'])>=3])
for cl in ['copper','holes','mask','paste','silk']:
 for r in data[cl]:r['shape']=geometry(r)
def item(r):return {k:v for k,v in r.items() if k not in ['shape','geom']}
def issue(a,b,d,limit):return {'a':item(a),'b':item(b),'clearance_mm':round(d,6),'limit_mm':limit}
report={'source_sha256':data['source_sha256'],'kicad':data['kicad'],'geometry_tolerance_mm':0.0001,'source_urls':['https://jlcpcb.com/capabilities/pcb-capabilities','https://jlcpcb.com/capabilities/pcb-assembly-capabilities','https://jlcpcb.com/help/article/pcb-via-covering'],'limits_note':'Different-net copper only for hole-to-copper/track; same-net copper intentionally connected to its plated barrel is excluded. Thermal pads are reported separately from ordinary component PTH. Borderline distances within 0.0003mm polygon approximation tolerance are not flagged.'}
EPS=.0003
holes=data['holes'];copper=data['copper'];mask=data['mask'];tracks=[r for r in copper if r['kind']=='track']
report['hole_classes']=dict(Counter(h['class'] for h in holes))
report['component_pth_min_ring_by_ref']={ref:min(h['ring_mm'] for h in holes if h['class']=='component_pth' and h['footprint_ref']==ref) for ref in sorted({h['footprint_ref'] for h in holes if h['class']=='component_pth'})}
report['smd_pads_narrower_than_025mm']=[item(a) for a in copper if a['kind']=='pad' and a['attribute']==1 and a['layer'] in ['F.Cu','B.Cu'] and min(a['size_mm'])<.25-EPS]
report['annular_by_class']={cl:{'minimum_mm':min(h['ring_mm'] for h in holes if h['class']==cl),'below_2oz_component_rule':[item(h) for h in holes if h['class']==cl and h['ring_mm']<.254-EPS]} for cl in ['component_pth','thermal_pad_via_function','native_via']}
report['via_diameter_minus_drill_min_mm']=min(2*h['ring_mm'] for h in holes if h['class'] in ['native_via','thermal_pad_via_function'])
# Hole edge-to-edge, retaining differing interpretations of native thermal PADs.
hole_pairs=[]
for i,a in enumerate(holes):
 for b in holes[i+1:]:
  d=a['shape'].distance(b['shape']);limit=.2 if a['class'] in ['native_via','thermal_pad_via_function'] and b['class'] in ['native_via','thermal_pad_via_function'] else .45
  if d<limit-EPS:hole_pairs.append(issue(a,b,d,limit))
report['hole_spacing_violations']=hole_pairs
report['native_thermal_pad_strict_045mm_pairs']=[]
for i,a in enumerate(holes):
 if a['class']!='thermal_pad_via_function':continue
 for b in holes[i+1:]:
  d=a['shape'].distance(b['shape'])
  if d<.45-EPS:report['native_thermal_pad_strict_045mm_pairs'].append(issue(a,b,d,.45))
# Indexed nearest different-net copper and track checks.
trees={l:(rows:= [r for r in copper if r['layer']==l],STRtree([r['shape'] for r in rows])) for l in ['F.Cu','In1.Cu','In2.Cu','B.Cu']}
# Mask-only EP apertures have no native electrical net. Infer only a unique
# overlapping same-footprint copper-pad net, and retain original net in metadata.
for a in mask:
 a['effective_net']=a['net']
 if not a['net'] and 'footprint_ref' in a:
  l='F.Cu' if a['layer']=='F.Mask' else 'B.Cu';rows,tree=trees[l]
  nets={rows[i]['net'] for i in tree.query(a['shape']) if rows[i]['kind']=='pad' and rows[i].get('footprint_ref')==a['footprint_ref'] and rows[i]['shape'].intersection(a['shape']).area>1e-7 and rows[i]['net']}
  if len(nets)==1:a['effective_net']=next(iter(nets));a['net_inference']='unique overlapping same-footprint copper pad net'
# SMD pad-to-pad and actual mask aperture gaps. Same-net coincident USB pads are merged/ignored.
report['mask_gap_below_02mm']=[];report['focus_pad_spacing']={}
for ref in ['U1','J5']:
 ps=[r for r in copper if r['layer']=='F.Cu' and r['kind']=='pad' and r['footprint_ref']==ref and r['attribute']==1]
 distances=[]
 for i,a in enumerate(ps):
  for b in ps[i+1:]:
   if a['net']==b['net'] and a['shape'].intersects(b['shape']):continue
   distances.append(issue(a,b,a['shape'].distance(b['shape']),.2))
 report['focus_pad_spacing'][ref]=sorted(distances,key=lambda r:r['clearance_mm'])[:12]
for l in ['F.Mask','B.Mask']:
 rows=[r for r in mask if r['layer']==l];tree=STRtree([r['shape'] for r in rows])
 for i,a in enumerate(rows):
  for j in tree.query(a['shape'].buffer(.2)):
   if j<=i:continue
   b=rows[j];d=a['shape'].distance(b['shape'])
   if d<EPS and a['effective_net']==b['effective_net']:continue
   if d<.2-EPS:report['mask_gap_below_02mm'].append(issue(a,b,d,.2))
report['mask_to_other_net_track_below_009mm']=[]
for a in mask:
 l='F.Cu' if a['layer']=='F.Mask' else 'B.Cu';rows,tree=trees[l]
 for i in tree.query(a['shape'].buffer(.09)):
  b=rows[i]
  if b['kind']!='track' or a['effective_net']==b['net']:continue
  d=a['shape'].distance(b['shape'])
  if d<.09-EPS:report['mask_to_other_net_track_below_009mm'].append(issue(a,b,d,.09))
mask_union={l:unary_union([r['shape'] for r in mask if r['layer']==l]) for l in ['F.Mask','B.Mask']}
paste_union={l:unary_union([r['shape'] for r in data['paste'] if r['layer']==l]) for l in ['F.Paste','B.Paste']}
report['thermal_holes']=[]
for h in holes:
 if h['class']=='thermal_pad_via_function':
  report['thermal_holes'].append({**item(h),'front_mask_open_fraction':round(h['shape'].intersection(mask_union['F.Mask']).area/h['shape'].area,6),'back_mask_open_fraction':round(h['shape'].intersection(mask_union['B.Mask']).area/h['shape'].area,6),'front_paste_overlap_fraction':round(h['shape'].intersection(paste_union['F.Paste']).area/h['shape'].area,6)})
# True copper-to-outline and copper-to-copper (different nets) with polygon approximation.
edge=box(50,50,194,162);report['copper_edge_minimum']={};report['copper_spacing_violations']=None
for l,(rows,tree) in trees.items():
 edge_dist=[(r['shape'].distance(edge.boundary) if edge.covers(r['shape']) else -r['shape'].difference(edge).area,r) for r in rows]
 d,r=min(edge_dist,key=lambda t:t[0]);report['copper_edge_minimum'][l]={'clearance_mm':round(d,6),'object':item(r),'routed_limit_mm':.2,'vcut_limit_mm':.4}
report['copper_spacing_check']='Full different-net copper-to-copper sweep not completed here; existing native DRC has 0.15mm constraints. Actual hole/copper, pad/mask and outline checks below are independent.'
report['track_width_min_mm']=min(t['width_mm'] for t in tracks)
report['silk_line_below_015mm']=[item(r) for r in data['silk'] if r.get('width_mm',1)<.15-EPS]
report['silk_text_below_1mm']=[item(r) for r in data['silk'] if r.get('height_mm',1)<1-EPS]
report['silk_after_mask_clip_close_to_mask']=[]
for a in data['silk']:
 mu=mask_union['F.Mask' if a['layer']=='F.Silkscreen' else 'B.Mask'];x0,y0,x1,y1=a['shape'].bounds;mu=local_clip(mu,x0-.16,y0-.16,x1+.16,y1+.16);ink=a['shape'].difference(mu)
 if not ink.is_empty:
  d=ink.distance(mu)
  if d<.15-EPS:report['silk_after_mask_clip_close_to_mask'].append({'object':item(a),'clearance_mm':round(d,6)})
# Hypothetical expansion only as needed to reach 0.254mm ring; already adapted boards stay unchanged.
report['j5_slot_target_ring_0254mm']=[]
for a in copper:
 if a['ref']!='J5.S1':continue
 ring=min((s-d)/2 for s,d in zip(a['size_mm'],a['drill_mm']))
 delta=max(0.0,round(.254-ring,9));expanded=a['shape'].buffer(delta) if delta else a['shape'];near=[]
 for h in holes:
  if h['id']==a['id'] or h['net']==a['net'] and h['class']!='npth':continue
  d=expanded.distance(h['shape'])
  if d<1:near.append({'ref':h['ref'],'class':h['class'],'clearance_mm':round(d,6)})
 for c in copper:
  if c['layer']!=a['layer'] or c['id']==a['id'] or c['net']==a['net']:continue
  cs=c['shape']
  if c['kind']=='zone':
   x0,y0,x1,y1=expanded.bounds;cs=local_clip(cs,x0-.4,y0-.4,x1+.4,y1+.4)
   if cs.is_empty:continue
  d=expanded.distance(cs)
  if d<.4:near.append({'ref':c['ref'],'class':c['kind'],'clearance_mm':round(d,6)})
 report['j5_slot_target_ring_0254mm'].append({'slot':item(a),'additional_expansion_mm':delta,'neighbors':sorted(near,key=lambda r:r['clearance_mm'])})
report['fiducial_footprints']=[f for f in data['footprints'] if 'fiducial' in f['footprint'].lower() or f['ref'].startswith('FID')]
report['edge_segment_count']=len(data['edge']);report['populated_sides']=dict(Counter(f['side'] for f in data['footprints'] if not f['dnp'] and not f['ref'].startswith(('TP','H'))))
OUT.mkdir(exist_ok=True,parents=True)
(OUT/'jlc-preflight.json').write_text(json.dumps(report,indent=2)+'\n')
print('TARGETED RESULTS WRITTEN',flush=True)
report['hole_to_track_violations']=[];report['inner_hole_to_copper_violations']=[]
for h in holes:
 for l,(rows,tree) in trees.items():
  for idx in tree.query(h['shape'].buffer(.36)):
   c=rows[idx]
   if h['net'] and h['net']==c['net']:continue
   near_shape=c['shape']
   if c['kind']=='zone':
    x0,y0,x1,y1=h['shape'].bounds;near_shape=local_clip(near_shape,x0-.36,y0-.36,x1+.36,y1+.36)
    if near_shape.is_empty:continue
   d=h['shape'].distance(near_shape);via=h['class'] in ['native_via','thermal_pad_via_function']
   if c['kind']=='track':
    limit=.2 if via or h['class']=='npth' else .28
    if d<limit-EPS:report['hole_to_track_violations'].append(issue(h,c,d,limit))
   if l.startswith('In') and h['class']!='npth':
    limit=.2 if via else .3
    if d<limit-EPS:report['inner_hole_to_copper_violations'].append(issue(h,c,d,limit))
report['unchanged_source']=sha(PCB)==data['source_sha256'];OUT.mkdir(exist_ok=True,parents=True)
(OUT/'jlc-preflight.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:(len(v) if isinstance(v,list) else v) for k,v in report.items() if k not in ['annular_by_class','thermal_holes','focus_pad_spacing','silk_line_below_015mm','silk_text_below_1mm','j5_slot_target_ring_0254mm']},indent=2))
print('PTH ring fails',[(r['ref'],r['ring_mm']) for r in report['annular_by_class']['component_pth']['below_2oz_component_rule']]);print('Expansion',json.dumps(report['j5_slot_target_ring_0254mm'],indent=2));print('THERMAL',Counter((h['front_mask_open_fraction'],h['back_mask_open_fraction'],h['front_paste_overlap_fraction']) for h in report['thermal_holes']))
