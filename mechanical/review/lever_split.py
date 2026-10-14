"""托座上位时 FB 张开回转段（0°~30°）和 FB 合拢段：把 U 形杠杆与其余零件分开统计，现方案与新方案对比。

现有发布模型在这一段本身就与杠杆内臂、11L 端轴、2L 隔套相交（见报告“现有模型问题”），
因此单独列出“除杠杆外”的最小间隙，判断新压头是否引入新的干涉。
"""
import json
import sys
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from review.run_review import C, S, OS, machine, split, front_clearance  # noqa: E402

LEVER = {p.note for p in C.lever_parts()}


def job(args):
    front, kind, val = args
    st = S((OS, 50.), (OS, float(val))) if kind == 'roll' else S((OS, 50.), (OS * val, 0.))
    mach = machine(st, 0, front)
    A, B, skip = split(mach, 'FB', front)
    lever = [b for b in B if b.group == 'support' and b.part.note in LEVER]
    rest = [b for b in B if not (b.group == 'support' and b.part.note in LEVER)]
    out = {}
    for name, group in (('lever', lever), ('other', rest)):
        r = front_clearance(A, group, rmax=4.0, top=1, skip=skip)
        out[name] = dict(mm=round(r[0][0], 3), penetrating=r[0][1], part=r[0][2], other=r[0][3]) if r else None
    return front, kind, val, out


if __name__ == '__main__':
    jobs = [(f, 'roll', a) for f in ('previous', 'rot90') for a in range(0, 32, 2)]
    jobs += [(f, 'close', s) for f in ('previous', 'rot90') for s in (0.0, 0.25, 0.5, 0.75)]
    res = {}
    with Pool(4) as pool:
        for front, kind, val, out in pool.imap_unordered(job, jobs):
            res.setdefault(front, {}).setdefault(kind, {})[str(val)] = out
            print(front, kind, val, out, flush=True)
    Path(sys.argv[1]).write_text(json.dumps(res, ensure_ascii=False, indent=1))
