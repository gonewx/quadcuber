import pcbnew as p,json,sys
b=p.LoadBoard(sys.argv[1])
def geom(g,l,c=0):
 ps=p.SHAPE_POLY_SET();g.TransformShapeToPolygon(ps,l,c,100,p.ERROR_OUTSIDE)
 def pts(c):return [[p.ToMM(c.CPoint(i).x),p.ToMM(c.CPoint(i).y)] for i in range(c.PointCount())]
 return [{'outer':pts(ps.COutline(i)),'holes':[pts(ps.CHole(i,j)) for j in range(ps.HoleCount(i))]} for i in range(ps.OutlineCount())]
d={'mask':[],'silk':[],'texts':[]}
for f in b.GetFootprints():
 for a in f.Pads():
  if a.IsOnLayer(p.F_Mask):d['mask'].append(geom(a,p.F_Mask,a.GetSolderMaskExpansion(p.F_Mask)))
 for g in [*f.GraphicalItems(),*f.GetFields()]:
  if g.GetLayer()==p.F_SilkS and (not hasattr(g,'IsVisible') or g.IsVisible()):d['silk'].append(geom(g,p.F_SilkS))
for g in b.GetDrawings():
 if g.GetLayer()!=p.F_SilkS:continue
 if isinstance(g,p.PCB_TEXT) and g.IsVisible() and g.GetTextHeight()<1000000:
  r={'id':g.m_Uuid.AsString(),'text':g.GetText(),'xy':[p.ToMM(g.GetPosition().x),p.ToMM(g.GetPosition().y)],'before':geom(g,p.F_SilkS)}
  g.SetTextSize(p.VECTOR2I(1000000,1000000));r['after']=geom(g,p.F_SilkS);d['texts'].append(r)
 else:d['silk'].append(geom(g,p.F_SilkS))
open(sys.argv[2],'w').write(json.dumps(d))
print('texts',len(d['texts']))
