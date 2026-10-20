"""把 circuit.SILK 的接口丝印加到板上；generate.py 与 label_interfaces.py 共用。"""
import pcbnew as p


def add_labels(b, silk, ox, oy):
    """先删同文字同位置的旧文字再加，重复运行结果不变。"""
    items = []
    for s, x, y, side, left in silk:
        pos = p.VECTOR2I(p.FromMM(ox + x), p.FromMM(oy + y))
        layer = p.F_SilkS if side == 'F' else p.B_SilkS
        items.append((s, pos, layer, left))
    keys = {(s, pos.x, pos.y, layer) for s, pos, layer, _ in items}
    for d in list(b.GetDrawings()):
        if isinstance(d, p.PCB_TEXT) and (d.GetText(), d.GetPosition().x, d.GetPosition().y, d.GetLayer()) in keys:
            b.Delete(d)
    for s, pos, layer, left in items:
        t = p.PCB_TEXT(b)
        t.SetText(s)
        t.SetPosition(pos)
        t.SetTextSize(p.VECTOR2I(p.FromMM(1.0), p.FromMM(1.0)))
        t.SetTextThickness(p.FromMM(0.15))
        t.SetLayer(layer)
        if layer == p.B_SilkS:
            t.SetMirrored(True)
        if left:
            t.SetHorizJustify(p.GR_TEXT_H_ALIGN_LEFT)
        b.Add(t)


def move_refs(b, moves, ox, oy):
    """把指定位号文字移到 (x, y)，角度为板上绝对角度。"""
    for f in b.GetFootprints():
        if f.GetReference() in moves:
            x, y, deg = moves[f.GetReference()]
            r = f.Reference()
            r.SetPosition(p.VECTOR2I(p.FromMM(ox + x), p.FromMM(oy + y)))
            r.SetTextAngleDegrees(deg)
