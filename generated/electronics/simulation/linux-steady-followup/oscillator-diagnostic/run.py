from pathlib import Path
import subprocess,json,time,hashlib
root=Path(__file__).parent
original=Path('/workspace/tool-verification/ti-model/TPS54302_PSPICE_TRANS/TPS54302_TRANS.LIB')
lines=original.read_text().splitlines(True);extract=''.join(lines[195:217]);(root/'original-U3-extract.cirpart').write_text(extract)
results=[]
for name,options in [('default',''),('strict','.OPTIONS TIMEINT RELTOL=1e-5 ABSTOL=1e-9\n.OPTIONS NONLIN-TRAN RELTOL=1e-6 ABSTOL=1e-12\n')]:
 d=root/name;d.mkdir(exist_ok=True)
 s='Original TI U3 oscillator, unloaded SYSCLK, explicit SDWN=ULQ_MODE=0\n.INCLUDE "/workspace/tool-verification/xyce-reference/TPS54302_TRANS.xyce-init.LIB"\nVBOUND_SDWN SDWN 0 0\nVBOUND_ULQ ULQ_MODE 0 0\n'+extract+options+'.TRAN 20n 100u 0 20n\n.PRINT TRAN FORMAT=CSV V(SYSCLK) V(RAMP) V(U3_CLK_500K) V(U3_N16810628) V(U3_N16807586) V(U3_BLANK) V(U3_N16813790)\n.END\n'
 (d/'test.cir').write_text(s);start=time.monotonic()
 with (d/'stdout.log').open('w') as f:
  try:r=subprocess.run(['/workspace/tools/xyce-7.10/bin/Xyce','test.cir'],cwd=d,stdout=f,stderr=subprocess.STDOUT,timeout=90);code=r.returncode
  except subprocess.TimeoutExpired:code='timeout'
 rec={'case':name,'returncode':code,'elapsed_s':time.monotonic()-start,'options':options,'original_U3_lines':[196,217],'unchanged_extraction_sha256':hashlib.sha256(extract.encode()).hexdigest()};results.append(rec);(root/'runs.json').write_text(json.dumps(results,indent=2)+'\n');print(rec,flush=True)
