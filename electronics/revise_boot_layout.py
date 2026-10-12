#!/usr/bin/env python3
"""Apply the approved local BOOT revision to the frozen native KiCad 10 A1 board.

Run with KiCad 10 AppRun python3.11. Requires an explicit baseline/output;
refuses any baseline other than the reviewed A1 SHA256. Does not invoke the
whole-board generator. Refilled copper is checked separately by project DRC.
Example:
  AppRun python3.11 electronics/revise_boot_layout.py --baseline OLD.kicad_pcb \
    --output electronics/quadcuber.kicad_pcb --evidence generated/electronics/boot-direct-revision
"""
import argparse, hashlib, html, json, math, uuid
from pathlib import Path
import pcbnew as p
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--baseline',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--evidence',type=Path,required=True)
args=parser.parse_args()
BASE_SHA='9e55fcbee01241fc6ec3682fde79daaacd6bc623ecfc311809600e001099350a'
assert hashlib.sha256(args.baseline.read_bytes()).hexdigest()==BASE_SHA, 'Unreviewed baseline'
assert '10.0.7' in p.GetBuildVersion(), 'Requires KiCad 10.0.7'
args.evidence.mkdir(parents=True,exist_ok=True)
b=p.LoadBoard(str(args.baseline))
serial=0
def stable_id(item):
 global serial
 serial+=1
 item.SetUuid(p.KIID(str(uuid.uuid5(uuid.NAMESPACE_URL,'quadcuber/a1-direct-boot-v1/'+str(serial)))))

def pt(x,y):return p.VECTOR2I(round(x*1e6),round(y*1e6))
def xy(q):return [q.x/1e6,q.y/1e6]
def tr(net,pts,layer=p.F_Cu,w=.25):
 for a,z in zip(pts,pts[1:]):
  t=p.PCB_TRACK(b);t.SetStart(pt(*a));t.SetEnd(pt(*z));t.SetWidth(round(w*1e6));t.SetLayer(layer);t.SetNetCode(b.FindNet(net).GetNetCode());stable_id(t);b.Add(t)
def via(net,x,y):
 t=p.PCB_VIA(b);t.SetPosition(pt(x,y));t.SetWidth(600000);t.SetDrill(300000);t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNetCode(b.FindNet(net).GetNetCode());stable_id(t);b.Add(t)
# Keep Python references alive until save: removing a temporary SWIG wrapper
# immediately can invalidate subsequent collection iteration in this binding.
removed=[]
for n,dx in [(1,0),(2,49)]:
 pre=f'B{n}_'; ref=lambda a:f'{a[0]}{int(a[1:])+10*(n-1)}'
 removed.append(next(f for f in b.GetFootprints() if f.GetReference()==ref('R20')))
 c=next(f for f in b.GetFootprints() if f.GetReference()==ref('C22'));c.SetOrientationDegrees(0);c.SetPosition(pt(98.0+dx,91.9))
 for pad in c.Pads():pad.SetNet(b.FindNet(pre+('BOOT' if pad.GetNumber()=='1' else 'SW')))
 for t in list(b.GetTracks()):
  net=t.GetNetname();a=xy(t.GetStart());z=xy(t.GetEnd());a[0]-=dx;z[0]-=dx
  if net in [pre+'BOOT',pre+'BOOT_CAP'] or (n==1 and net==pre+'FB' and (max(a[1],z[1])<=89.357 or min(a[0],z[0])>95.5747 and max(a[0],z[0])>98)) or (net==pre+'SW' and not (abs(a[0]-100.1375)<.0001 and abs(z[0]-105.45)<.0001)):removed.append(t)
 # Only B needs its existing two GND escapes moved clear of the new capacitor.
 if n==2:
  for t in b.GetTracks():
   if t.GetNetname()=='GND':
    a=xy(t.GetStart());z=xy(t.GetEnd())
    for old,new in [([148.296,90.9825],[148.3597,90.1141]),([149.138,91.15],[149.411,90.3231])]:
     if a==old:t.SetStart(pt(*new))
     if z==old:t.SetEnd(pt(*new))
 def T(s,pts,layer=p.F_Cu,w=.25):tr(pre+s,[(x+dx,y)for x,y in pts],layer,w)
 def V(s,x,y):via(pre+s,x+dx,y)
 # A's original FB line cuts across the required short SW return.
 # Preserve B's distinct existing FB routing entirely.
 if n==1:
  T('FB',[(97.8625,87.05),(97.2,86.55)]);V('FB',97.2,86.55)
  T('FB',[(97.2,86.55),(96.7,87.05),(96.7,91.3),(95.5748,92.65)],p.B_Cu);V('FB',95.5748,92.65);T('FB',[(95.5748,92.65),(94.825,92.65)])
 T('BOOT',[(97.8625,88.95),(97.05,89.7625),(97.05,91.9)])
 T('SW',[(100.1375,88),(99.05,88),(99.05,89.1),(98.55,89.6),(98.55,91.9),(98.95,91.9)],w=.25)
 removed.append(b.FindNet(pre+'BOOT_CAP'))
for item in removed:b.Remove(item)
for f in b.GetFootprints():
 if f.GetReference() in ['R21','R31','R22','R32']:
  f.GetField('MPN').SetText('RT0603BRD07100KL' if f.GetReference() in ['R21','R31'] else 'RT0603BRD0713K3L')
p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(args.output),b)

# Geometry accounting is independent of DRC. Filled polygons legitimately change
# after local edits; zone boundaries/layers and all unrelated items must not.
def uid(item):return item.m_Uuid.AsString()
def poly(a):
 def line(q):return [xy(q.CPoint(i)) for i in range(q.PointCount())]
 return [{'outline':line(a.COutline(i)),'holes':[line(a.CHole(i,h)) for h in range(a.HoleCount(i))]} for i in range(a.OutlineCount())]
def tracks(board):
 result={}
 for t in board.GetTracks():
  row={'type':t.GetClass(),'net':t.GetNetname(),'a_mm':xy(t.GetStart()),'b_mm':xy(t.GetEnd()),'layer':board.GetLayerName(t.GetLayer()),'width_mm':(t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth())/1e6}
  if isinstance(t,p.PCB_VIA):row.update(drill_mm=t.GetDrillValue()/1e6,layer_pair=[t.TopLayer(),t.BottomLayer()])
  if isinstance(t,p.PCB_ARC):row['mid_mm']=xy(t.GetMid())
  result[uid(t)]=row
 return result
def footprints(board):
 result={}
 for f in board.GetFootprints():
  pads=[{'number':q.GetNumber(),'net':q.GetNetname(),'position_mm':xy(q.GetPosition()),'size_mm':xy(q.GetSize()),'drill_mm':xy(q.GetDrillSize()),'shape':q.GetShape(),'rotation':q.GetOrientationDegrees(),'layers':list(q.GetLayerSet().Seq())} for q in f.Pads()]
  fields=[{'name':q.GetName(),'text':q.GetText(),'position_mm':xy(q.GetPosition()),'visible':q.IsVisible()} for q in f.GetFields()]
  result[f.GetReference()]={'position_mm':xy(f.GetPosition()),'rotation':f.GetOrientationDegrees(),'layer':f.GetLayer(),'footprint':str(f.GetFPID().GetLibItemName()),'pads':sorted(pads,key=str),'fields':sorted(fields,key=str)}
 return result
def fixed(board):
 return {'copper_layers':board.GetCopperLayerCount(),'zones':sorted([{'net':z.GetNetname(),'layers':list(z.GetLayerSet().Seq()),'outline':poly(z.Outline())} for z in board.Zones()],key=str),'edge_cuts':sorted([[d.GetShape(),xy(d.GetStart()),xy(d.GetEnd()),d.GetWidth()]for d in board.GetDrawings()if d.GetLayer()==p.Edge_Cuts and isinstance(d,p.PCB_SHAPE)],key=str)}
a_board=p.LoadBoard(str(args.baseline));z_board=p.LoadBoard(str(args.output))
a=tracks(a_board);z=tracks(z_board);af=footprints(a_board);zf=footprints(z_board)
changed=[{'uuid':k,'before':a[k],'after':z[k]}for k in a.keys()&z.keys()if a[k]!=z[k]]
deleted=[{'uuid':k,**a[k]}for k in a.keys()-z.keys()]
added=[{'uuid':k,**z[k]}for k in z.keys()-a.keys()]
allowed_removed={'B1_BOOT','B1_BOOT_CAP','B1_SW','B1_FB','B2_BOOT','B2_BOOT_CAP','B2_SW'}
assert all(row['net'] in allowed_removed for row in deleted)
assert len(changed)==4 and all(r['before']['net']==r['after']['net']=='GND' for r in changed)
assert all(row['net'] in {'B1_BOOT','B1_SW','B1_FB','B2_BOOT','B2_SW'}for row in added)
fp_changed=sorted(k for k in af.keys()&zf.keys()if af[k]!=zf[k])
assert fp_changed==['C22','C32','R21','R22','R31','R32'],fp_changed
assert af.keys()-zf.keys()=={'R20','R30'} and not zf.keys()-af.keys()
assert fixed(a_board)==fixed(z_board)
for ref in ['R21','R22','R31','R32']:
 original=dict(af[ref]);current=dict(zf[ref]);original.pop('fields');current.pop('fields');assert original==current
 for old,new in zip(af[ref]['fields'],zf[ref]['fields']):
  if old['name']=='MPN':
   new=dict(new);new['text']=old['text']
  assert old==new
for n in [1,2]:
 assert not any(t['net']==f'B{n}_BOOT_CAP' for t in z.values())
 assert not any(q['net']==f'B{n}_BOOT_CAP'for f in zf.values()for q in f['pads'])
 cap=zf[f'C{12+10*n}'];assert {q['number']:q['net']for q in cap['pads']}=={'1':f'B{n}_BOOT','2':f'B{n}_SW'}
 assert all(t['type']=='PCB_TRACK' and t['layer']=='F.Cu'for t in z.values()if t['net']==f'B{n}_BOOT')

# Centreline graph: split collinear and crossing segments, quantize at 1 um to
# reconcile older sub-micron duplicate endpoints. Vias count separately; no
# barrel length, pad extent or electromagnetic loop inductance is claimed.
def shortest(board,net,start,end):
 import heapq
 lines=[(xy(t.GetStart()),xy(t.GetEnd()))for t in board.GetTracks()if t.GetNetname()==net and not isinstance(t,p.PCB_VIA)]
 points=[start,end]+[q for seg in lines for q in seg]
 cross=lambda a,b:a[0]*b[1]-a[1]*b[0]
 sub=lambda a,b:[a[0]-b[0],a[1]-b[1]]
 for i,(q,r0)in enumerate(lines):
  r=sub(r0,q)
  for s0,s1 in lines[i+1:]:
   s=sub(s1,s0);den=cross(r,s)
   if abs(den)<1e-10:continue
   v=sub(s0,q);t=cross(v,s)/den;u=cross(v,r)/den
   if 0<=t<=1 and 0<=u<=1:points.append([q[0]+t*r[0],q[1]+t*r[1]])
 key=lambda q:tuple(round(v,3)for v in q)
 graph={key(q):{}for q in points}
 for q,r in lines:
  dx=r[0]-q[0];dy=r[1]-q[1];ll=dx*dx+dy*dy
  if ll<1e-10:continue
  on=[]
  for v in points:
   t=((v[0]-q[0])*dx+(v[1]-q[1])*dy)/ll
   distance=abs(dx*(q[1]-v[1])-(q[0]-v[0])*dy)/math.sqrt(ll)
   if -.002<=t<=1.002 and distance<.002:on.append((t,key(v)))
  on=sorted(set(on))
  for (_,v),(_,w)in zip(on,on[1:]):
   d=math.dist(v,w);graph[v][w]=d;graph[w][v]=d
 todo=[(0,key(start))];seen={}
 while todo:
  d,q=heapq.heappop(todo)
  if q in seen:continue
  seen[q]=d
  if q==key(end):return d
  for v,w in graph[q].items():
   if v not in seen:heapq.heappush(todo,(d+w,v))
 raise AssertionError(('No centreline route',net,start,end))
metrics=[]
for n,dx in [(1,0),(2,49)]:
 pre=f'B{n}_';old_boot=[t for t in a.values()if t['net']in[pre+'BOOT',pre+'BOOT_CAP']];new_boot=[t for t in z.values()if t['net']==pre+'BOOT']
 old_boot_length=sum(math.dist(t['a_mm'],t['b_mm'])for t in old_boot)+1.65
 new_boot_length=sum(math.dist(t['a_mm'],t['b_mm'])for t in new_boot)
 sw_start=[100.1375+dx,88]
 old_sw=shortest(a_board,pre+'SW',sw_start,[97.95+dx,84])
 new_sw=sum(math.dist(t['a_mm'],t['b_mm'])for t in added if t['net']==pre+'SW')
 metrics.append({'channel':n,'before':{'boot_lead_copper_sum_plus_resistor_pad_span_mm':old_boot_length,'boot_vias':sum(t['type']=='PCB_VIA'for t in old_boot),'sw_return_shortest_centerline_mm':old_sw,'sum_leads_mm':old_boot_length+old_sw},'after':{'boot_lead_centerline_mm':new_boot_length,'boot_vias':sum(t['type']=='PCB_VIA'for t in new_boot),'sw_return_centerline_mm':new_sw,'sw_return_vias':0,'sum_leads_mm':new_boot_length+new_sw,'capacitor_position_mm':[98+dx,91.9],'capacitor_rotation_degrees':0}})
report={'schema':'quadcuber.boot-local-revision.v1','kicad_version':p.GetBuildVersion(),'baseline_sha256':BASE_SHA,'output_sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(),'unchanged_tracks_and_vias':sum(a[k]==z[k]for k in a.keys()&z.keys()),'unchanged_footprints':sum(af[k]==zf[k]for k in af.keys()&zf.keys()),'changed_footprints':{k:{'before':af[k],'after':zf[k]}for k in fp_changed},'removed_footprints':['R20','R30'],'changed_tracks_and_vias':sorted(changed,key=lambda r:r['uuid']),'removed_tracks_and_vias':sorted(deleted,key=lambda r:r['uuid']),'added_tracks_and_vias':sorted(added,key=lambda r:r['uuid']),'zone_outlines_board_outline_copper_layers_identical':True,'zone_fill_policy':'All zones refilled with KiCad 10.0.7. Filled copper polygons are not claimed identical outside the edits; outlines/settings retained. See independent review for old-cache versus fresh-fill comparison.','metrics':metrics,'limits':'Geometry/centreline lengths only. SVG omits filled planes for clarity. Local FB route on B.Cu is separated from top SW copper by internal planes. DRC and schematic parity are separate checks; stability/EMI/hardware validation still required. Before BOOT count uses copper sum plus the 1.65 mm resistor pad span; excludes via barrel lengths and includes sub-micron duplicate old segments.'}
(args.evidence/'layout-comparison.json').write_text(json.dumps(report,indent=2)+'\n')

# Four aligned geometry views from the actual boards, not an illustrative circuit.
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="1130" viewBox="0 0 1100 1130"><rect width="1100" height="1130" fill="#101725"/>']
svg.append('<text x="20" y="26" fill="white" font-family="sans-serif" font-size="19">A1 BOOT revision — actual PCB geometry; mm coordinates</text>')
svg.append('<text x="20" y="48" fill="#cbd5e1" font-family="sans-serif" font-size="13">BOOT yellow · SW red · FB cyan · GND grey · dashed=B.Cu · circles=vias; planes omitted</text>')
for n,dx in [(1,0),(2,49)]:
 for col,(board,title)in enumerate([(a_board,'BEFORE'),(z_board,'AFTER')]):
  ox=20+col*550;oy=70+(n-1)*520;scale=29
  svg.append(f'<text x="{ox}" y="{oy+20}" fill="white" font-family="sans-serif" font-size="17">{title} — channel {n}</text>')
  svg.append(f'<svg overflow="hidden" x="{ox}" y="{oy+35}" width="520" height="470" viewBox="{90+dx} 81 18 16.2">')
  svg.append(f'<defs><clipPath id="clip-{n}-{col}"><rect x="{90+dx}" y="81" width="18" height="16.2"/></clipPath></defs><g clip-path="url(#clip-{n}-{col})">')
  def color(net):
   return '#ffdf54'if 'BOOT'in net else '#ff6868'if net==f'B{n}_SW' else '#63ddec'if net==f'B{n}_FB'else '#a0a8b3'if net=='GND'else '#536979'
  for t in board.GetTracks():
   q=xy(t.GetStart());r=xy(t.GetEnd());c=color(t.GetNetname())
   if isinstance(t,p.PCB_VIA):
    svg.append(f'<circle cx="{q[0]}" cy="{q[1]}" r="{t.GetWidth(p.F_Cu)/2e6}" fill="{c}"/><circle cx="{q[0]}" cy="{q[1]}" r="{t.GetDrillValue()/2e6}" fill="#101725"/>')
   else:
    dash='stroke-dasharray="0.22 0.18"'if t.GetLayer()==p.B_Cu else ''
    svg.append(f'<path d="M{q[0]} {q[1]} L{r[0]} {r[1]}" stroke="{c}" stroke-width="{t.GetWidth()/1e6}" stroke-linecap="round" {dash}/>')
  for f in board.GetFootprints():
   pos=xy(f.GetPosition())
   if not(90+dx<=pos[0]<=108+dx and 81<=pos[1]<=97.2):continue
   for q in f.Pads():
    posq=xy(q.GetPosition());w,h=xy(q.GetSize());c=color(q.GetNetname());opacity='.4'if f.GetLayer()==p.B_Cu else '1'
    svg.append(f'<rect x="{posq[0]-w/2}" y="{posq[1]-h/2}" width="{w}" height="{h}" rx="0.08" fill="{c}" opacity="{opacity}" transform="rotate({-q.GetOrientationDegrees()} {posq[0]} {posq[1]})"/>')
   svg.append(f'<text x="{pos[0]}" y="{pos[1]-.2}" text-anchor="middle" fill="white" stroke="#101725" stroke-width="0.04" paint-order="stroke" font-family="sans-serif" font-size="0.42">{html.escape(f.GetReference())}</text>')
  svg.append('</g></svg>')
svg.append('</svg>');(args.evidence/'layout-before-after.svg').write_text(''.join(svg))
print(json.dumps({'output':str(args.output),'metrics':metrics,'unrelated_geometry_preserved':True},indent=2))
