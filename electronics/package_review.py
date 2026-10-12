#!/usr/bin/env python3
"""Package an explicitly non-released engineering review; no remote publishing."""
from pathlib import Path
import hashlib,json,subprocess,zipfile,shutil
R=Path(__file__).resolve().parents[1];O=R/'output/electronics';O.mkdir(parents=True,exist_ok=True)
name='quadcuber-A1-ENGINEERING-REVIEW-EV3-UNVERIFIED-DO-NOT-FABRICATE'
sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
files=[p for folder in [R/'electronics',R/'generated/electronics'] for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ['.pyc','.kicad_prl','.lck']]
files.append(R/'wiring/spec.py')
warning='''工程评审版 / ENGINEERING REVIEW ONLY / DO NOT FABRICATE

架构：单PCB，RP2040/Flash/晶振/USB-C直接焊接，与四臂驱动、电源转换和接口集成；无Pico插装。

EV3插座孔位已按用户尺寸图更新；实际料号、针号/视向和载流额定尚未确认。
EV3_UserDrawing_PINMAP_HOLD 保存图示孔位；普通RJ12不能替代。
包含的Gerber、钻孔文件仅用于工程审查，不是制造发布，禁止据此下单。
尚需安装托架/双面器件净空验证及并发负载、回灌、热、USB组合供电实测。

打开 electronics/quadcuber.kicad_pro。说明 electronics/README.md。
原理图PDF、BOM、双面板图、ERC/DRC及制造预览位于 generated/electronics/。
KiCad 9.0.2；原生工程可独立编辑和导出。wiring/spec.py随包提供用于电子契约检查。
完整软件回归与机械复核需要同一提交的完整仓库；本包不重复打包机械模型。
制造状态 false、硬件实测 false；软件59项通过不等于PCB实测通过。
'''
manifest={'git_commit':sha,'manufacturing_release':False,'hardware_tested':False,'files':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}}
zpath=O/(name+'.zip')
with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 z.writestr('00-ENGINEERING-REVIEW-DO-NOT-FABRICATE.txt',warning+'\nCommit: '+sha+'\n')
 z.writestr('manifest.json',json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
 for p in sorted(files):z.write(p,p.relative_to(R))
with zipfile.ZipFile(zpath) as z:
 assert z.testzip() is None
 assert 'electronics/quadcuber.kicad_pcb' in z.namelist()
 assert 'generated/electronics/erc.rpt' in z.namelist()
 assert len(z.namelist())==len(files)+2
out=[zpath]
for side in ['top','bottom']:
 dst=O/(name+'-pcb-'+side+'.png');shutil.copyfile(R/'generated/electronics'/('pcb-'+side+'.png'),dst);out.append(dst)
result={'git_commit':sha,'files':[{'path':str(p),'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in out]}
(O/'delivery-manifest.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
