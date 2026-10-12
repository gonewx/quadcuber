"""Read-only comparison after refilling the frozen baseline in memory.

Run with KiCad 10.0.7 AppRun python3.11; stdout is JSON. No board is saved.
"""
import argparse
import hashlib
import json
import pcbnew as p

ap = argparse.ArgumentParser()
ap.add_argument('baseline')
ap.add_argument('current')
args = ap.parse_args()
assert '10.0.7' in p.GetBuildVersion()
old = p.LoadBoard(args.baseline)
new = p.LoadBoard(args.current)
p.ZONE_FILLER(old).Fill(old.Zones())
before = {z.m_Uuid.AsString(): z for z in old.Zones()}
after = {z.m_Uuid.AsString(): z for z in new.Zones()}
assert before.keys() == after.keys()
threshold = 1e-6
windows = [[90, 80, 104, 96], [139, 80, 153, 96]]
rows = []
for key, zone in before.items():
    layer = zone.GetLayer()
    x = zone.GetFilledPolysList(layer)
    y = after[key].GetFilledPolysList(layer)
    for label, u, v in [('removed', x, y), ('added', y, x)]:
        diff = p.SHAPE_POLY_SET(u)
        diff.BooleanSubtract(v)
        outside = []
        total = 0
        for i in range(diff.OutlineCount()):
            poly = diff.COutline(i)
            points = [poly.CPoint(j) for j in range(poly.PointCount())]
            area = abs(sum(q.x*r.y-r.x*q.y for q, r in
                           zip(points, points[1:]+points[:1]))/2e12)
            box = [min(t.x for t in points)/1e6, min(t.y for t in points)/1e6,
                   max(t.x for t in points)/1e6, max(t.y for t in points)/1e6]
            total += area
            local = any(w[0] <= box[0] and w[1] <= box[1]
                        and box[2] <= w[2] and box[3] <= w[3] for w in windows)
            if not local:
                outside.append({'outer_area_mm2': area, 'bounds_mm': box})
        rows.append({'net': zone.GetNetname(), 'layer': new.GetLayerName(layer),
                     'operation': label, 'polygon_count': diff.OutlineCount(),
                     'sum_outer_area_mm2': total,
                     'outside_polygon_count': len(outside),
                     'outside_max_outer_area_mm2': max((r['outer_area_mm2'] for r in outside), default=0),
                     'outside_above_threshold': [r for r in outside if r['outer_area_mm2'] > threshold]})
report = {'kicad_version': p.GetBuildVersion(),
          'baseline_sha256': hashlib.sha256(open(args.baseline, 'rb').read()).hexdigest(),
          'current_sha256': hashlib.sha256(open(args.current, 'rb').read()).hexdigest(),
          'method': 'Refill baseline in memory, BooleanSubtract each filled zone in both directions, measure each outer polygon using integer-coordinate shoelace area. Holes are not subtracted; area is an upper bound per outer polygon.',
          'local_windows_mm': windows, 'threshold_mm2_per_polygon': threshold,
          'rows': rows,
          'pass': not any(r['outside_above_threshold'] for r in rows),
          'limits': 'Not byte equality; tiny slivers are inferred numerical residuals. Per-polygon threshold, not a bound on total residual area. No board saved; not an EMI/thermal/hardware proof.'}
print(json.dumps(report, indent=2))
