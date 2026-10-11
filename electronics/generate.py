#!/usr/bin/env python3
"""Explicit source regeneration. Uses KiCad 9 pcbnew; never called by export/check."""
import json,uuid,math,shutil,csv,re
from pathlib import Path
import pcbnew as p
from circuit import C
HERE=Path(__file__).resolve().parent; ROOT=HERE.parent; OUT=ROOT/'generated/electronics'; LIB=HERE/'lib/Quadcuber.pretty'
OUT.mkdir(exist_ok=True,parents=True);LIB.mkdir(exist_ok=True,parents=True)
def uid(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,'https://github.com/gonewx/quadcuber/pcb/'+s))
def q(s):return json.dumps(str(s),ensure_ascii=False)
def through_layers():
    ls=p.LSET.AllCuMask();ls.AddLayer(p.F_Mask);ls.AddLayer(p.B_Mask);return ls
def vec(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def effect(sz=1,extra=''):return f'(effects (font (size {sz} {sz})) {extra})'
# This deliberately named placeholder is NOT a verified 4434 land pattern.
# Body envelope provisionally taken from Adafruit drawing; tails intentionally flagged.
fp=p.FOOTPRINT(None);fp.SetFPID(p.LIB_ID('Quadcuber','EV3_4434_PROVISIONAL'));fp.SetReference('REF**');fp.SetValue('4434 HOLD - verify tails')
for num,(x,y) in enumerate([(-3.175,-5),(-1.905,-2.46),(-.635,-5),(.635,-2.46),(1.905,-5),(3.175,-2.46)],1):
    pad=p.PAD(fp);pad.SetNumber(str(num));pad.SetAttribute(p.PAD_ATTRIB_PTH);pad.SetShape(p.PAD_SHAPE_CIRCLE);pad.SetSize(vec(1.65,1.65));pad.SetDrillSize(vec(.9,.9));pad.SetLayerSet(through_layers());pad.SetPosition(vec(x,y));fp.Add(pad)
for x in [-5,5]:
    pad=p.PAD(fp);pad.SetAttribute(p.PAD_ATTRIB_NPTH);pad.SetShape(p.PAD_SHAPE_CIRCLE);pad.SetSize(vec(2,2));pad.SetDrillSize(vec(2,2));pad.SetLayerSet(through_layers());pad.SetPosition(vec(x,1));fp.Add(pad)
for layer,w,h,yo in [(p.F_Fab,12.24,14.65,-.325),(p.F_CrtYd,13.24,15.65,-.325),(p.F_SilkS,12.7,14.9,-.325)]:
    sh=p.PCB_SHAPE(fp);sh.SetShape(p.SHAPE_T_RECT);sh.SetStart(vec(-w/2,yo-h/2));sh.SetEnd(vec(w/2,yo+h/2));sh.SetLayer(layer);sh.SetWidth(p.FromMM(.15));fp.Add(sh)
p.PCB_IO_KICAD_SEXPR().FootprintSave(str(LIB),fp)
# Pico H socket pattern: Raspberry Pi mechanical drawing, 17.78mm rows / 2.54mm pitch.
pf=p.FOOTPRINT(None);pf.SetFPID(p.LIB_ID('Quadcuber','Pico_H_Sockets'));pf.SetReference('REF**');pf.SetValue('Pico H sockets')
for num in range(1,41):
    x=0 if num<=20 else 17.78;y=(num-1)*2.54 if num<=20 else (40-num)*2.54
    pad=p.PAD(pf);pad.SetNumber(str(num));pad.SetAttribute(p.PAD_ATTRIB_PTH);pad.SetShape(p.PAD_SHAPE_RECT if num==1 else p.PAD_SHAPE_CIRCLE);pad.SetSize(vec(1.8,1.8));pad.SetDrillSize(vec(1,1));pad.SetLayerSet(through_layers());pad.SetPosition(vec(x,y));pf.Add(pad)
for layer,start,end in [(p.F_Fab,(-1.61,-1.37),(19.39,49.63)),(p.F_CrtYd,(-2.11,-1.87),(19.89,50.13)),(p.F_SilkS,(-1.9,-1.7),(19.7,50))]:
    sh=p.PCB_SHAPE(pf);sh.SetShape(p.SHAPE_T_RECT);sh.SetStart(vec(*start));sh.SetEnd(vec(*end));sh.SetLayer(layer);sh.SetWidth(p.FromMM(.12));pf.Add(sh)
p.PCB_IO_KICAD_SEXPR().FootprintSave(str(LIB),pf)
# Snapshot exact KiCad library footprints so opening the project is independent of OS libraries.
for comp in C:
    lib,name=comp['fp'].split(':',1)
    if lib!='Quadcuber':
        src=Path('/usr/share/kicad/footprints')/(lib+'.pretty')/(name+'.kicad_mod')
        if not src.exists():raise FileNotFoundError(src)
        dst=LIB/(name+'.kicad_mod');shutil.copyfile(src,dst)
        if name=='RaspberryPi_Pico_Common_THT':
            pf=p.PCB_IO_KICAD_SEXPR().FootprintLoad(str(LIB),name)
            for pp in pf.Pads():
                if pp.GetShape()==p.PAD_SHAPE_CUSTOM:
                    pp.SetShape(p.PAD_SHAPE_CIRCLE);pp.SetSize(vec(1.8,1.8))
            p.PCB_IO_KICAD_SEXPR().FootprintSave(str(LIB),pf)
        comp['source_fp']=comp['fp'];comp['fp']='Quadcuber:'+name
(HERE/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "Quadcuber")(type "KiCad")(uri "${KIPRJMOD}/lib/Quadcuber.pretty")(options "")(descr "Pinned footprints; EV3 footprint explicitly provisional")))\n')
# Self-contained native symbols with real pin identities and electrical types.
# ICs retain explicit pad identities; passives use standard circuit graphics.
rootid=uid('root'); sections=['controller','power','buck1','buck2','arm_R','arm_L','arm_F','arm_B']; libsym={}
def pindefs(comp):
    pins=list(comp['pins']); n=len(pins);half=math.ceil(n/2); result=[]
    for i,num in enumerate(pins):
        side=0 if i<half else 1;j=i if side==0 else i-half
        yy=round((half-1)*1.27-j*2.54,3)
        result.append((num,-10.16 if side==0 else 10.16,yy,0 if side==0 else 180))
    return result
for comp in C:
    if not comp['pins']:continue
    ref=comp['ref'];pins=pindefs(comp);hh=max(3.81,math.ceil(len(pins)/2)*1.27+1.27)
    ss=f'(symbol "Quadcuber:{ref}" (pin_names (offset 0.508)) (in_bom yes)(on_board yes) (property "Reference" "{ref}" (at 0 {hh+2.54} 0) {effect()}) (property "Value" {q(comp["value"])} (at 0 {-hh-2.54} 0) {effect()}) (property "Footprint" {q(comp["fp"])} (at 0 0 0) {effect(extra="(hide yes)")}) (symbol "{ref}_0_1" (rectangle (start -7.62 {hh})(end 7.62 {-hh})(stroke (width 0.254)(type default))(fill (type background)))) (symbol "{ref}_1_1" '
    if len(pins)==2 and ref[0] in 'RCLDF':
        stroke='(stroke(width .254)(type default))'
        def line(x1,y1,x2,y2):return f'(polyline(pts(xy {x1} {y1})(xy {x2} {y2})){stroke}(fill(type none)))'
        if ref[0]=='C':
            graphic=line(-7.62,0,-1.27,0)+line(1.27,0,7.62,0)+line(-1.27,-3.81,-1.27,3.81)+line(1.27,-3.81,1.27,3.81)
            if comp['value'].startswith('470'):graphic+=line(-4.5,2.5,-2.5,2.5)+line(-3.5,1.5,-3.5,3.5)
        elif ref[0]=='D':
            graphic=line(-7.62,0,-2.54,0)+line(2.54,0,7.62,0)+line(-2.54,-2.54,-2.54,2.54)+f'(polyline(pts(xy -2.54 0)(xy 2.54 -2.54)(xy 2.54 2.54)(xy -2.54 0)){stroke}(fill(type none)))'
        elif ref[0]=='L':
            graphic=line(-7.62,0,-5.08,0)+line(5.08,0,7.62,0)
            for xx in [-5.08,-2.54,0,2.54]:graphic+=f'(arc(start {xx} 0)(mid {xx+1.27} 1.27)(end {xx+2.54} 0){stroke}(fill(type none)))'
        else:
            graphic=line(-7.62,0,-3.81,0)+line(3.81,0,7.62,0)+f'(rectangle(start -3.81 1.27)(end 3.81 -1.27){stroke}(fill(type none)))'
            if ref[0]=='F':graphic+=line(-3.81,0,3.81,0)
        old=f'(rectangle (start -7.62 {hh})(end 7.62 {-hh})(stroke (width 0.254)(type default))(fill (type background)))'
        ss=ss.replace(old,graphic).replace('(pin_names (offset 0.508))','(pin_names (offset 0.508) hide)')
    for num,x,y,a in pins:
        typ=comp['types'].get(num,'passive');name=comp['names'].get(num,num)
        ss+=f'(pin {typ} line (at {x} {y} {a})(length 2.54)(name {q(name)} {effect(.75)})(number {q(num)} {effect(.75)}))'
    libsym[ref]=ss+'))'
# Explicit power flags describe supply provenance; not ERC suppressions.
for i,net in enumerate(['GND','VM','VIN_FUSED','VSYS','R_SERVO_5V','L_SERVO_5V','F_SERVO_5V','B_SERVO_5V']):
    ref='#FLG'+str(i+1)
    cc=dict(ref=ref,pins={'1':net},names={'1':'SUPPLIED_'+net},types={'1':'power_out'},value='PWR_FLAG',fp='',xy=(0,0),mpn='',mfr='',section='power',note='',rot=0)
    C.append(cc)
    libsym[ref]=f'(symbol "Quadcuber:{ref}" (in_bom no)(on_board no)(property "Reference" "{ref}" (at 0 0 0) {effect(extra="(hide yes)")})(property "Value" "PWR_FLAG" (at 0 2.54 0) {effect()})(symbol "{ref}_0_1" (rectangle(start -1.27 1.27)(end 1.27 -1.27)(stroke(width .254)(type default))(fill(type none))))(symbol "{ref}_1_1"(pin power_out line(at -10.16 0 0)(length 8.89)(name "SUPPLY" {effect(.75)})(number "1" {effect(.75)}))))'
(HERE/'lib/Quadcuber.kicad_sym').write_text('(kicad_symbol_lib(version 20241209)(generator "kicad_symbol_editor")'+''.join(v.replace('Quadcuber:','',1) for v in libsym.values())+')')
(HERE/'sym-lib-table').write_text('(sym_lib_table(version 7)(lib(name "Quadcuber")(type "KiCad")(uri "${KIPRJMOD}/lib/Quadcuber.kicad_sym")(options "")(descr "Self-contained explicit pin definitions")))')

# Root sheets.
root=f'(kicad_sch (version 20250114)(generator "eeschema")(uuid {rootid})(paper "A3")(title_block(title "Quadcuber four-arm integrated controller - A0 ENGINEERING HOLD")(rev "A0")(company "gonewx/quadcuber"))(lib_symbols)'
root+=f'(text "Integrated motor drivers, dual buck supplies, encoder conditioning and Pico H.\\nEV3 jack land pattern is PROVISIONAL. Manufacturing release is blocked.\\nUse electronics/README.md and generated/electronics/release-status.json." (at 25.4 25.4 0) {effect(1.5,"(justify left)")}(uuid {uid("title")}))'
for i,sec in enumerate(sections):
    x=25.4+(i%4)*91.44;y=60.96+(i//4)*60.96; sid=uid('sheet-'+sec)
    root+=f'(sheet(at {x} {y})(size 71.12 35.56)(fields_autoplaced)(stroke(width 0.1524)(type solid))(fill(color 0 0 0 0))(uuid {sid})(property "Sheetname" {q(sec)}(at {x} {y-1.27} 0){effect(1.27,"(justify left bottom)")})(property "Sheetfile" {q(sec+".kicad_sch")}(at {x} {y+36.83} 0){effect(1.27,"(justify left top)")})(instances(project "quadcuber"(path "/{rootid}"(page "{i+2}")))))'
root+='(sheet_instances(path "/"(page "1")))(embedded_fonts no))'
(HERE/'quadcuber.kicad_sch').write_text(root)
for si,sec in enumerate(sections):
    comps=[cc for cc in C if cc['section']==sec and cc['pins']];sid=uid('sheet-'+sec); allsym=''.join(libsym[cc['ref']] for cc in comps)
    s=f'(kicad_sch(version 20250114)(generator "eeschema")(uuid {uid("doc-"+sec)})(paper "A3")(title_block(title {q("Quadcuber A0 / "+sec+" / ENGINEERING HOLD")})(rev "A0"))(lib_symbols {allsym})'
    for i,comp in enumerate(comps):
        ref=comp['ref'];cx=35.56+(i%6)*63.5;cy=38.1+(i//6)*40.64
        if sec=='controller':
            if ref=='U1':cx=45.72;cy=63.5
            else:cx=132.08+((i-1)%4)*66.04;cy=38.1+((i-1)//4)*40.64
        hh=max(3.81,math.ceil(len(comp['pins'])/2)*1.27+1.27)
        s+=f'(symbol(lib_id "Quadcuber:{ref}")(at {cx} {cy} 0)(unit 1)(in_bom {'no' if ref.startswith('#') else 'yes'})(on_board {'no' if ref.startswith('#') else 'yes'})(dnp {"yes" if comp.get("dnp") else "no"})(uuid {uid(ref)})'
        for prop,val,dy,hide in [('Reference',ref,-hh-3.81,False),('Value',comp['value'],hh+3.81,False),('Footprint',comp['fp'],0,True),('MPN',comp['mpn'],0,True),('Manufacturer',comp['mfr'],0,True)]:
            s+=f'(property {q(prop)} {q(val)}(at {cx} {cy+dy} 0){effect(1.27,"(hide yes)" if hide else "")})'
        for num,xx,yy,ang in pindefs(comp):s+=f'(pin {q(num)}(uuid {uid(ref+"-"+num)}))'
        s+=f'(instances(project "quadcuber"(path "/{rootid}/{sid}"(reference "{ref}")(unit 1)))))'
        for num,xx,yy,ang in pindefs(comp):
            x=cx+xx;y=cy-yy;net=comp['pins'][num]
            if net is None:s+=f'(no_connect(at {x} {y})(uuid {uid(ref+num+"nc")}))';continue
            endx=x+(-5.08 if xx<0 else 5.08)
            s+=f'(wire(pts(xy {x} {y})(xy {endx} {y}))(stroke(width 0)(type default))(uuid {uid(ref+num+"wire")}))'
            a=0 if xx<0 else 180
            s+=f'(global_label {q(net)}(shape bidirectional)(at {endx} {y} {a}){effect(.8)}(uuid {uid(ref+num+"label")})(property "Intersheetrefs" "${{INTERSHEET_REFS}}"(at {endx} {y} {a}){effect(.8,"(hide yes)")}))'
    s+='(embedded_fonts no))';(HERE/(sec+'.kicad_sch')).write_text(s)
# Common project rules. No intentional DRC exclusion.
classes=[]
for name,width in [('Default',.25),('Motor',1.0),('PowerBranch',1.0),('PowerBus',1.0),('Ground',.3)]:
    classes.append(dict(name=name,clearance=.2,track_width=width,via_diameter=.7,via_drill=.35,microvia_diameter=.3,microvia_drill=.1,diff_pair_width=.25,diff_pair_gap=.2,diff_pair_via_gap=.25,pcb_color='rgba(0, 0, 0, 0.000)',schematic_color='rgba(0, 0, 0, 0.000)',wire_width=6,bus_width=12,line_style=0))
patterns=[{'netclass':'PowerBus','pattern':n} for n in ['VIN','VIN_FUSED','VM']]+[{'netclass':'Ground','pattern':'GND'}]+[{'netclass':'PowerBranch','pattern':n} for n in ['5V_A','5V_B','5V_ENC','*_SERVO_5V','B?_SW']]+[{'netclass':'Motor','pattern':'*_M?'}]
project={'meta':{'filename':'quadcuber.kicad_pro','version':1},'net_settings':{'classes':classes,'meta':{'version':3},'netclass_patterns':patterns},'board':{'design_settings':{'rules':{'min_clearance':.2,'min_track_width':.2,'min_via_diameter':.6,'min_through_hole_diameter':.3,'min_copper_edge_clearance':.3,'solder_mask_to_copper_clearance':0},'rule_severities':{'silk_over_copper':'warning','silk_overlap':'warning'}}}}
(HERE/'quadcuber.kicad_pro').write_text(json.dumps(project,indent=2)+'\n')
# Initial placement; routed PCB is subsequently edited in KiCad and is authoritative.
import sys
if '--metadata-only' not in sys.argv:
    b=p.BOARD();b.SetCopperLayerCount(4);b.SetFileName(str(HERE/'quadcuber.kicad_pcb'))
    netnames=sorted({net for cc in C for net in cc['pins'].values() if net}); nets={}
    for name in netnames:
        n=p.NETINFO_ITEM(b,name);b.Add(n);nets[name]=n
    for comp in C:
        if comp['ref'].startswith('#'):continue
        _,name=comp['fp'].split(':',1); f=p.PCB_IO_KICAD_SEXPR().FootprintLoad(str(LIB),name)
        if not f:raise ValueError(comp['fp'])
        f.SetDNP(bool(comp.get('dnp')));f.SetReference(comp['ref']);f.SetValue(comp['value']);f.SetFPID(p.LIB_ID('Quadcuber',name));f.SetPath(p.KIID_PATH('/'+rootid+'/'+uid('sheet-'+comp['section'])+'/'+uid(comp['ref'])))
        x,y=comp['xy'];f.SetPosition(vec(x+50,y+50));f.SetOrientationDegrees(comp['rot']);f.Value().SetVisible(False);f.Reference().SetTextSize(vec(.8,.8));f.Reference().SetTextThickness(p.FromMM(.12));f.Reference().SetPosition(vec(x+50,y+50-3.5));f.Reference().SetLayer(p.F_Fab)
        for pad in f.Pads():
            num=pad.GetNumber();net=comp['pins'].get(num)
            if net:pad.SetNet(nets[net])
        b.Add(f)
    for start,end in [((50,50),(194,50)),((194,50),(194,162)),((194,162),(50,162)),((50,162),(50,50))]:
        sh=p.PCB_SHAPE();sh.SetShape(p.SHAPE_T_SEGMENT);sh.SetStart(vec(*start));sh.SetEnd(vec(*end));sh.SetLayer(p.Edge_Cuts);sh.SetWidth(p.FromMM(.05));b.Add(sh)
    def txt(text,x,y,sz=1,layer=p.F_SilkS):
        t=p.PCB_TEXT(b);t.SetText(text);t.SetPosition(vec(x+50,y+50));t.SetTextSize(vec(sz,sz));t.SetTextThickness(p.FromMM(.15));t.SetLayer(layer);b.Add(t)
    txt('QUADCUBER A0  /  ENGINEERING HOLD',105,20,1.1)
    txt('9V ONLY   USB = PICO ONLY',87,28,1)
    txt('4434 JACK TAILS UNVERIFIED - DO NOT FABRICATE',95,58,.8)
    for idx,arm in enumerate(['R','L','F','B']):txt(arm,27+34*idx,109,1.5)
    txt('G + S',132,106,.8)
    p.SaveBoard(str(HERE/'quadcuber.kicad_pcb'),b)
(OUT/'circuit.json').write_text(json.dumps(C,indent=2,ensure_ascii=False)+'\n')
with (OUT/'bom.csv').open('w') as f:
    w=csv.writer(f,lineterminator="\n");w.writerow(['Reference','Value','Manufacturer','MPN','Footprint','Quantity','Notes'])
    for cc in C:
        if cc['ref'].startswith('#'):continue
        w.writerow([cc['ref'],cc['value'],cc['mfr'],cc['mpn'],cc['fp'],0 if cc.get('dnp') else 1,cc['note']])
    w.writerow(['U1 sockets','1x20 female 2.54mm','Wurth Elektronik','61302011821','U1 holes',2,'Pico socket rows; do not solder Pico module directly'])
print(f'Generated {len(C)} components, 9 schematic sheets, 144x112mm PCB')
