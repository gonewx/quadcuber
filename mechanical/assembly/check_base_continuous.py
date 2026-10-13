import sys,json,math
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]));import candidate as c
from paths import OUTPUT
out=OUTPUT/'base-stiffening'
lo,hi=math.asin(-32.8/112),math.asin(9.6/112);angles=np.array([lo,(lo+hi)/2,hi]);A=np.array([[1,math.sin(a),math.cos(a)] for a in angles]);boards=[c.lever_parts(112*math.sin(a)+32.8) for a in angles]
maxima={};resid=0
for i,p in enumerate(boards[0]):
 ys=np.stack([c.world(ps[i])[...,1].reshape(-1) for ps in boards]);co=np.linalg.solve(A,ys);a,b,d=co
 top=np.maximum(ys[0],ys[2]);crit=np.arctan2(b,d)
 for shift in [-2*math.pi,-math.pi,0,math.pi,2*math.pi]:
  t=crit+shift;valid=(t>=lo)&(t<=hi);top=np.maximum(top,np.where(valid,a+b*np.sin(t)+d*np.cos(t),-np.inf))
 for angle in [lo*.73+hi*.27,lo*.19+hi*.81]:
  actual=c.world(c.lever_parts(112*math.sin(angle)+32.8)[i])[...,1].reshape(-1);resid=max(resid,float(np.max(np.abs(actual-(a+b*math.sin(angle)+d*math.cos(angle))))))
 maxima[p.note]=float(top.max())
assert resid<1e-8
moving_ids={r['id'] for r in c.rows if r['role']=='moving'};tray=max(float(c.world(p)[...,1].max())+40.8 for p in c.core_parts(0) if p.note in moving_ids)
r={'method':'Per native lever-mesh vertex y=a+b*sin(phi)+c*cos(phi), interval endpoints and stationary points. Formula checked at two independent interior angles. Tray is exact +40.8mm translation. No elastic deformation included.','phi_interval_degrees':[lo*180/math.pi,hi*180/math.pi],'independent_fit_residual_mm':resid,'part_max_y_mm':maxima,'all_lever_max_y_mm':max(maxima.values()),'moving_tray_max_y_mm':tray,'new_structure_min_y_mm':116,'lever_to_new_structure_vertical_separation_mm':116-max(maxima.values()),'tray_to_new_structure_vertical_separation_mm':116-tray,'table_y_mm':140,'outer_handle_to_table_mm':140-maxima['outer_handle']}
(out/'continuous-bounds.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
proposal=json.loads((out/'geometry-check.json').read_text());swept=[];overlaps=[]
for i,p in enumerate(boards[0]):
 xyz=np.stack([c.world(ps[i]).reshape(-1,3) for ps in boards]);co=np.linalg.solve(A,xyz.reshape(3,-1));a,b,d=co
 bot=np.minimum(xyz[0].reshape(-1),xyz[2].reshape(-1));top=np.maximum(xyz[0].reshape(-1),xyz[2].reshape(-1));crit=np.arctan2(b,d)
 for shift in [-2*math.pi,-math.pi,0,math.pi,2*math.pi]:
  t=crit+shift;valid=(t>=lo)&(t<=hi);val=a+b*np.sin(t)+d*np.cos(t);top=np.maximum(top,np.where(valid,val,-np.inf));bot=np.minimum(bot,np.where(valid,val,np.inf))
 low,high=bot.reshape(-1,3).min(0),top.reshape(-1,3).max(0);swept.append({'name':p.note,'bbox':[low.tolist(),high.tolist()]})
for p in c.core_parts(0):
 if p.note not in moving_ids:continue
 v=c.world(p).reshape(-1,3);low,high=v.min(0),v.max(0);high[1]+=40.8;swept.append({'name':p.note,'bbox':[low.tolist(),high.tolist()]})
for old in swept:
 low,high=np.array(old['bbox'])
 for new in proposal['parts']:
  a,b=np.array(new['bbox_mm'])
  if np.all(np.minimum(high,b)-np.maximum(low,a)>1e-7):overlaps.append([old['name'],new['id']])
assert not overlaps,overlaps
(out/'swept-clearance.json').write_text(json.dumps({'method':'Continuous trig bounds for lever; full translation bounds for moving tray. Swept AABBs vs all added parts including pins. No overlap is conservative separation, not a proof of complete machine operation.','overlaps':overlaps,'moving_bounds':swept},indent=2))
print('Continuous swept AABBs vs all72 added parts: zero overlaps')
