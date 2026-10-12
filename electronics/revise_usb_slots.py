#!/usr/bin/env python3
"""Apply the authorized A1 J5 2-oz shield-slot annulus revision only.

Run with KiCad10 Python and --apply. Does not regenerate the board or routing.
The adapter is also used by generate.py after copying the upstream USB footprint.
"""
import argparse,hashlib,json,re
from pathlib import Path
import pcbnew as p
NAME='USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal'

def adapt_usb_shield_slots(footprint):
    """Set four existing S1 oval pads to 0.254 mm rings; leave holes untouched.

    Accept only the frozen original or already-revised dimensions, so an upstream
    footprint geometry change cannot silently receive an incompatible adaptation.
    """
    if str(footprint.GetFPID().GetLibItemName())!=NAME:
        raise ValueError('USB shield adapter received a different footprint')
    pads=[a for a in footprint.Pads() if a.GetNumber()=='S1']
    if len(pads)!=4:
        raise ValueError('Expected exactly four S1 shield pads')
    expected={(600000,1700000):((1000000,2100000),(1108000,2208000)),
              (600000,1400000):((1000000,1800000),(1108000,1908000))}
    planned=[];counts={key:0 for key in expected}
    for a in pads:
        drill=(a.GetDrillSize().x,a.GetDrillSize().y)
        size=(a.GetSize().x,a.GetSize().y)
        if drill not in expected or a.GetShape()!=p.PAD_SHAPE_OVAL or a.GetAttribute()!=p.PAD_ATTRIB_PTH:
            raise ValueError('Unexpected S1 slot geometry; inspect upstream footprint')
        old,new=expected[drill];counts[drill]+=1
        if size not in [old,new]:
            raise ValueError('Unexpected S1 copper size; refusing to overwrite')
        if size!=new:planned.append((a,size,new))
    if sorted(counts.values())!=[2,2]:
        raise ValueError('Expected two long and two short shield slots')
    changed=[]
    for a,old,new in planned:
        a.SetSize(p.VECTOR2I(*new))
        changed.append({'uuid':a.m_Uuid.AsString(),'position_mm':[p.ToMM(a.GetPosition().x),p.ToMM(a.GetPosition().y)],'old_size_mm':[x/1e6 for x in old],'new_size_mm':[x/1e6 for x in new],'drill_mm':[p.ToMM(a.GetDrillSize().x),p.ToMM(a.GetDrillSize().y)],'net':a.GetNetname()})
    return changed

def adapt_usb_shield_slots_file(path):
    """Patch only four S1 size fields, preserving library format and all UUIDs."""
    path=Path(path);text=path.read_text()
    pattern=re.compile(r'(\(pad "S1" thru_hole oval\b[\s\S]*?\(size )([^)]+)(\)[\s\S]*?\(drill oval ([^)]+)\))')
    matches=list(pattern.finditer(text))
    if len(matches)!=4:raise ValueError('Expected exactly four S1 text records')
    targets={(600000,1700000):('1.108 2.208',(1000000,2100000)),(600000,1400000):('1.108 1.908',(1000000,1800000))}
    def replace(m):
        drill=tuple(round(float(v)*1e6) for v in m[4].split());size=tuple(round(float(v)*1e6) for v in m[2].split())
        if drill not in targets:raise ValueError('Unexpected slot drill in local library')
        target,old=targets[drill];new=tuple(round(float(v)*1e6) for v in target.split())
        if size not in [old,new]:raise ValueError('Unexpected S1 pad size in local library')
        return m[1]+target+m[3]
    updated=pattern.sub(replace,text)
    if updated!=text:path.write_text(updated)
    return updated!=text

def adapt_usb_vbus_clearance(board):
    """Move exactly three shared nodes +0.06 mm X to retain the 0.20 mm rule."""
    original={
        '1c9cde93-6b13-45a4-931d-3873bbf8384b':((75118500,55049600),(75118500,57659300)),
        '798bdb25-1303-4523-bcb3-bd55121a7036':((78812900,55049600),(75118500,55049600)),
        'cc9f98a0-4228-4c78-8163-aa595ae3845c':((75118500,55049600),(63025100,55049600)),
        'd45ae99b-2573-4fd8-8747-c22624b25667':((75118500,57659300),(74545700,58232100)),
        '83e1a1c5-9865-47ec-8c64-46ecab0ba978':((74545700,58232100),(72827100,58232100)),
    }
    nodes={(75118500,55049600),(75118500,57659300),(74545700,58232100)}
    move=lambda xy:(xy[0]+60000,xy[1]) if xy in nodes else xy
    tracks={t.m_Uuid.AsString():t for t in board.GetTracks()};planned=[]
    for ident,(a,b) in original.items():
        t=tracks[ident];old=(a,b);new=(move(a),move(b));actual=((t.GetStart().x,t.GetStart().y),(t.GetEnd().x,t.GetEnd().y))
        if t.GetNetname()!='USB_VBUS' or t.GetLayer()!=p.F_Cu or t.GetWidth()!=150000 or actual not in [old,new]:
            raise ValueError('Unexpected USB_VBUS route state: '+ident)
        if actual!=new:planned.append((t,old,new))
    changes=[]
    for t,old,new in planned:
        t.SetStart(p.VECTOR2I(*new[0]));t.SetEnd(p.VECTOR2I(*new[1]))
        changes.append({'uuid':t.m_Uuid.AsString(),'before_nm':old,'after_nm':new,'net':'USB_VBUS','width_mm':0.15})
    return changes

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true',required=True);parser.add_argument('--board',type=Path);parser.add_argument('--library-directory',type=Path);parser.add_argument('--report',type=Path);args=parser.parse_args()
    here=Path(__file__).resolve().parent;pcb=args.board or here/'quadcuber.kicad_pcb';lib=args.library_directory or here/'lib/Quadcuber.pretty';fpfile=lib/(NAME+'.kicad_mod')
    sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
    before={'board':sha(pcb),'footprint':sha(fpfile)}
    board=p.LoadBoard(str(pcb));fp=next(f for f in board.GetFootprints() if f.GetReference()=='J5')
    io=p.PCB_IO_KICAD_SEXPR();local=io.FootprintLoad(str(lib),NAME)
    changes={'native':adapt_usb_shield_slots(fp),'library':adapt_usb_shield_slots(local),'vbus_clearance_segments':adapt_usb_vbus_clearance(board)}
    if changes['native'] or changes['vbus_clearance_segments']:
        # Refills existing zone definitions only; no placement/routing generation.
        p.ZONE_FILLER(board).Fill(board.Zones())
        p.SaveBoard(str(pcb),board)
    if changes['library']:adapt_usb_shield_slots_file(fpfile)
    report={'state':'APPLIED' if any(changes.values()) else 'ALREADY_APPLIED','kicad':p.Version(),'changes':changes,'hashes_before':before,'hashes_after':{'board':sha(pcb),'footprint':sha(fpfile)},'scope':'Four J5 S1 copper/paste/mask sizes and five exact USB_VBUS segments at three shared nodes +0.06mm X; drill/slot, net and width unchanged; existing zones refilled. Whole-build ERC/DRC/export verification is a separate next step.'}
    out=here.parent/'generated/electronics/release-preflight/jlc-implementation';out.mkdir(parents=True,exist_ok=True)
    (args.report or out/'implementation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
