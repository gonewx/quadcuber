"""Run only when a built Xyce binary is supplied. Every attempt gets an isolated log."""
import argparse, pathlib, subprocess, json, shutil
p=argparse.ArgumentParser();p.add_argument('xyce');p.add_argument('--hspice-negative-control',action='store_true');a=p.parse_args()
root=pathlib.Path(__file__).resolve().parent
binary=str(pathlib.Path(a.xyce).resolve())
records=[]
for net in sorted(root.glob('*.cir')):
 modes=[('default',[])]
 if a.hspice_negative_control and net.stem.startswith('xor_'):
  modes.append(('hspice_math',['-hspice-ext','math']))
 for mode,args in modes:
  out=root/'runs'/mode/net.stem;out.mkdir(parents=True,exist_ok=True)
  shutil.copy2(net,out/net.name)
  cmd=[binary,*args,net.name]
  with (out/'stdout.log').open('w') as log:
   try:
    result=subprocess.run(cmd,cwd=out,stdout=log,stderr=subprocess.STDOUT,timeout=60)
    status=result.returncode
   except subprocess.TimeoutExpired:status='timeout'
  records.append({'netlist':net.name,'mode':mode,'command':cmd,'returncode':status,'log':str(out/'stdout.log')})
(root/'runs'/'results.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(records,indent=2))
