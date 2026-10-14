"""轮胎转 90° 压头（第 2 版）整机核算：静态姿态、装料流程过渡、整圈回转、邻层余量、夹紧几何。

用法：python mechanical/review/run_review.py [输出目录]，默认写到 generated/mechanical/tyre-rot90/。
全部基于真实 LDraw 网格的名义几何；不含弹性变形、公差和实物装配力。
"""
import json
import math
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from review.scene import C, samples, front_clearance  # noqa: E402
from review.motion import machine, front_ids, full_turn_clearance, AXIS, ADJ  # noqa: E402
from review import sweep_margin  # noqa: E402

OS = C.m.OPEN_S
DROP = 40.8


def designed_pairs(front):
    """同一臂内按设计相互插接/贴面的零件对（编号为 candidate.module 的 1 起序号）。"""
    pairs = set()

    def chain(*ids):
        for i in ids:
            for j in ids:
                if i < j:
                    pairs.add(frozenset((i, j)))
    if front == 'rot90':
        for jaw, r, wbush in ((121, 137, 168), (129, 146, 169)):
            pm, pp, ax3, h3m, h3p, ax1, spacer, hub, tyre = range(r, r + 9)
            chain(ax1, pm, jaw, pp)
            chain(ax3, h3m, pm, jaw, pp, h3p)
            chain(hub, pm, pp, spacer, wbush, tyre, jaw)
            chain(spacer, wbush, tyre)
            chain(pm, pp, jaw)
    else:
        for jaw, r in ((121, 137), (129, 146)):
            bm, bp, ax, h0, h1, pin, wax, hub, tyre = range(r, r + 9)
            chain(ax, bm, bp, h0, h1, jaw)
            chain(pin, bm, bp, jaw)
            chain(wax, bm, bp, hub, tyre)
    return pairs


def split(mach, movers, front):
    F = front_ids(front)
    DP = designed_pairs(front)
    A = [(arm, i, it) for arm, i, it in mach if arm is not None and arm in movers and it.group.endswith('head') and i in F]
    others = [(arm, i, it) for arm, i, it in mach if not (arm is not None and arm in movers and it.group.endswith('head') and i in F)]
    key = {id(it): (arm, i) for arm, i, it in mach}

    def skip(a, b):
        (aa, ia), (ab, ib) = key[id(a)], key[id(b)]
        return aa == ab and frozenset((ia, ib)) in DP
    return [it for _, _, it in A], [it for _, _, it in others], skip


def clearance(state, drop, front, movers='LRFB', rmax=4.0, top=12):
    mach = machine(state, drop, front)
    A, B, skip = split(mach, movers, front)
    return [dict(mm=round(d, 3), penetrating=x, part=a, other=b) for d, x, a, b in
            front_clearance(A, B, rmax=rmax, top=top, skip=skip)]


def S(lr, fb):
    return {'L': lr, 'R': lr, 'F': fb, 'B': fb}


STATES = {
    'loading-all50': (S((OS, 50.), (OS, 50.)), 0),
    'FB0-open': (S((OS, 50.), (OS, 0.)), 0),
    'FB0-held': (S((OS, 50.), (0., 0.)), 0),
    'support-down40_8': (S((OS, 50.), (0., 0.)), DROP),
    'LR90-open': (S((OS, 90.), (0., 0.)), DROP),
    'both-held': (S((0., 90.), (0., 0.)), DROP),
}


def task(args):
    kind, front, name, *rest = args
    if kind == 'state':
        st, drop = STATES[name]
        return (kind, front, name, clearance(st, drop, front))
    if kind == 'fbroll':
        ang, = rest
        return (kind, front, ang, clearance(S((OS, 50.), (OS, float(ang))), 0, front, movers='FB'))
    if kind == 'lrroll':
        ang, = rest
        return (kind, front, ang, clearance(S((OS, float(ang)), (0., 0.)), DROP, front, movers='LR'))
    if kind == 'fbclose':
        f, = rest
        return (kind, front, f, clearance(S((OS, 50.), (OS * f, 0.)), 0, front, movers='FB'))
    if kind == 'lrclose':
        f, = rest
        return (kind, front, f, clearance(S((OS * f, 90.), (0., 0.)), DROP, front, movers='LR'))
    if kind == 'drop':
        d, = rest
        return (kind, front, d, clearance(S((OS, 50.), (0., 0.)), d, front, movers='LRFB'))
    if kind in ('fblever', 'fbcloselever'):
        val, = rest
        st = S((OS, 50.), (OS, float(val))) if kind == 'fblever' else S((OS, 50.), (OS * val, 0.))
        mach = machine(st, 0, front)
        A, B, skip = split(mach, 'FB', front)
        lever_notes = {p.note for p in C.lever_parts()}
        out = {}
        for name, group in (('lever', [b for b in B if b.group == 'support' and b.part.note in lever_notes]),
                            ('other', [b for b in B if not (b.group == 'support' and b.part.note in lever_notes)])):
            r = front_clearance(A, group, rmax=4.0, top=1, skip=skip)
            out[name] = dict(mm=round(r[0][0], 3), penetrating=r[0][1], part=r[0][2], other=r[0][3]) if r else None
        return (kind, front, val, out)
    if kind == 'fullturn':
        arm, own_open, adj_open, drop = rest
        st = {}
        for a in C.m.ARMS:
            if a == arm:
                st[a] = (OS if own_open else 0., 0.)
            elif a in ADJ[arm]:
                st[a] = (OS if adj_open else 0., 0.)
            else:
                st[a] = (OS if adj_open else 0., 0.)
        mach = machine(st, drop, front)
        F = front_ids(front)
        mov_front = [it for a, i, it in mach if a == arm and it.group.endswith('head') and i in F]
        mov_rest = [it for a, i, it in mach if a == arm and it.group.endswith('head') and i not in F]
        not_arm = [it for a, i, it in mach if a != arm]
        own_fixed = [it for a, i, it in mach if a == arm and not it.group.endswith('head')]
        ax = C.m.ARM_ROT[arm] @ np.array([1., 0, 0])
        r1 = full_turn_clearance(mov_front, not_arm + own_fixed, ax, rmax=6.0, top=4)
        r2 = full_turn_clearance(mov_rest, [it for a, i, it in mach if a != arm and a is not None and it.group.endswith('head') and i in F], ax, rmax=6.0, top=4)
        return (kind, front, (arm, own_open, adj_open, drop), dict(front_sweep=r1, head_sweep_vs_neighbour_fronts=r2))


def margins():
    return {f: sweep_margin.table(f) for f in ('previous', 'rot90')}


def clamp_geometry():
    m = C.m

    def boxdist(P):
        q = np.abs(P) - 28.0
        return float((np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(1), 0)).min())
    out = {}
    for front, tyre, others in (('previous', 145, (143, 144)), ('rot90', 145, (143, 144, 168))):
        rec = {}
        for s, lab in ((0., 'clamp'), (OS, 'open25')):
            pp = C.module(s, 0, front=front)
            rec[lab] = dict(tyre_to_cube_mm=round(boxdist(samples(pp[tyre - 1])), 3),
                            hardware_to_cube_mm=round(min(boxdist(samples(pp[i - 1])) for i in others), 3))
        lo, hi = 0., OS
        for _ in range(40):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if boxdist(samples(C.module(mid, 0, front=front)[tyre - 1])) <= 0 else (lo, mid)
        rec['contact_onset_jaw_deg'] = round(math.degrees(m.jaw_beta(lo)), 3)
        rec['contact_onset_stroke_mm'] = round(lo * .4, 3)
        out[front] = rec
    th0, th1 = (math.degrees(m.servo_theta_for(x)[0]) for x in (0, OS))
    out['common'] = dict(clamp_jaw_deg=round(math.degrees(m.CLAMP_BETA), 4), open_jaw_deg=25.0,
                         pushrod_stroke_mm=round(OS * .4, 3), servo_crank_deg=[round(th0, 2), round(th1, 2)])
    return out


def main(outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    jobs = []
    for front in ('previous', 'rot90'):
        jobs += [('state', front, n) for n in STATES]
        step = 2 if front == 'rot90' else 10
        jobs += [('fbroll', front, a, a) for a in range(0, 51, step)]
        jobs += [('lrroll', front, a, a) for a in range(50, 91, step)]
        jobs += [('fbclose', front, f, f) for f in (0.0, 0.25, 0.5, 0.75)]
        jobs += [('lrclose', front, f, f) for f in (0.0, 0.25, 0.5, 0.75)]
        jobs += [('drop', front, d, d) for d in (0.0, 10.0, 20.0, 30.0, 40.8)]
        jobs += [('fblever', front, a, a) for a in range(0, 32, 2)]
        jobs += [('fbcloselever', front, f, f) for f in (0.0, 0.25, 0.5, 0.75)]
        for arm in (('L', 'F') if front == 'rot90' else ()):
            for own in (False, True):
                for adj in (False, True):
                    for drop in (DROP, 0.0):
                        jobs.append(('fullturn', front, f'{arm}-{own}-{adj}-{drop}', arm, own, adj, drop))
    res = {}
    done_file = outdir / 'partial.jsonl'
    done = set()
    if done_file.exists():
        for line in done_file.read_text().splitlines():
            kind, front, key, val = json.loads(line)
            res.setdefault(front, {}).setdefault(kind, {})[key] = val
            done.add((kind, front, key))
    jobs = [j for j in jobs if (j[0], j[1], str(j[2])) not in done]
    with Pool(4, maxtasksperchild=4) as pool, done_file.open('a') as log:
        for kind, front, key, val in pool.imap_unordered(task, jobs):
            res.setdefault(front, {}).setdefault(kind, {})[str(key)] = val
            log.write(json.dumps([kind, front, str(key), val], ensure_ascii=False) + '\n')
            log.flush()
            print(kind, front, key, json.dumps(val, ensure_ascii=False)[:160], flush=True)
    report = dict(method='真实 LDraw 网格名义几何。静态与部分回转：顶点＋0.3mm 棱线采样到三角形的精确距离；'
                         '回转扫描每 2°；整圈回转用子午面二维距离（精确回转体）。同臂内按设计插接/贴面的零件对不计入。',
                  margins=margins(), clamp=clamp_geometry(), results=res)
    (outdir / 'review.json').write_text(json.dumps(report, ensure_ascii=False, indent=1))
    print('written', outdir / 'review.json')


if __name__ == '__main__':
    from paths import OUTPUT
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else OUTPUT / 'tyre-rot90')
