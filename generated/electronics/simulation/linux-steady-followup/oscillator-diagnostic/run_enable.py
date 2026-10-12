from pathlib import Path
import subprocess,time,json
root=Path(__file__).parent;results=[]
for mode in ['default','strict']:
 name='enable_'+mode;d=root/name;d.mkdir(exist_ok=True)
 s=(root/mode/'test.cir').read_text().replace('VBOUND_SDWN SDWN 0 0','VBOUND_SDWN SDWN 0 PWL(0 1 1u 1 1.001u 0)')
 (d/'test.cir').write_text(s);start=time.monotonic()
 with (d/'stdout.log').open('w') as f:
  try:r=subprocess.run(['/workspace/tools/xyce-7.10/bin/Xyce','test.cir'],cwd=d,stdout=f,stderr=subprocess.STDOUT,timeout=90);code=r.returncode
  except subprocess.TimeoutExpired:code='timeout'
 rec={'case':name,'returncode':code,'elapsed_s':time.monotonic()-start,'boundary':'SDWN=1 for OP and 1us, ramps to zero over 1ns; ULQ_MODE=0'};results.append(rec);(root/'enable-runs.json').write_text(json.dumps(results,indent=2)+'\n');print(rec,flush=True)
