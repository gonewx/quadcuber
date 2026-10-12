import csv,hashlib,json,runpy,re,struct,xml.etree.ElementTree as E
from pathlib import Path
R=Path('/workspace/quadcuber'); O=R/'generated/electronics/release-preflight/controller'
C={p['ref']:p for p in runpy.run_path(str(R/'electronics/circuit.py'))['C']}
J={p['ref']:p for p in json.loads((R/'generated/electronics/circuit.json').read_text())}
B={p['Reference']:p for p in csv.DictReader((R/'generated/electronics/bom.csv').open())}
T=E.parse(O/'current-netlist.xml'); N={(p.get('ref'),p.get('pin')):n.get('name') for n in T.findall('./nets/net') for p in n.findall('node')}
# Parse native board without modifying/resaving its KiCad 10 syntax.
toks=iter(re.findall(r'"(?:\\.|[^"\\])*"|[^\s()]+|[()]',(R/'electronics/quadcuber.kicad_pcb').read_text()))
def parse():
 out=[]
 for x in toks:
  if x==')':return out
  out.append(parse() if x=='(' else json.loads(x) if x.startswith('"') else x)
 return out
board=parse()[0]
def children(x,k):return [v for v in x if isinstance(v,list) and v and v[0]==k]
def one(x,k):return children(x,k)[0]
F={one(f,'property')[2]:f for f in children(board,'footprint')}
refs=[r for r,p in C.items() if p['section'] in ['controller','controller_power','flash_clock','usb']]
checks=0
for r in refs:
 p=C[r]
 assert p['mpn']==J[r]['mpn']==B[r]['MPN'],r
 pads=children(F[r],'pad')
 for pin,net in p['pins'].items():
  if net is None:continue
  assert N[r,pin]==J[r]['pins'][pin]==net,(r,pin,net,N.get((r,pin)))
  actual=[one(q,'net')[-1] for q in pads if q[1]==pin]
  assert actual and set(actual)=={net},(r,pin,actual,net)
  checks+=1
expected={str(p):'3V3' for p in [1,10,22,33,42,43,44,48,49]}
expected.update({str(p):'1V1' for p in [23,45,50]});expected.update({'19':'GND','57':'GND','46':'USB_DM_MCU','47':'USB_DP_MCU','51':'QSPI_SD3','52':'QSPI_SCLK','53':'QSPI_SD0','54':'QSPI_SD2','55':'QSPI_SD1','56':'QSPI_SS'})
for pin,net in expected.items():assert C['U1']['pins'][pin]==net
u=(R/'generated/electronics/firmware/quadcuber-a1-micropython-v1.27.0.uf2').read_bytes();blocks={}
for off in range(0,len(u),512):
 b=u[off:off+512];m0,m1,flags,addr,n,i,total,fam=struct.unpack('<8I',b[:32]);assert (m0,m1,struct.unpack('<I',b[508:])[0])==(0x0a324655,0x9e5d5157,0x0ab16f30);assert flags&0x2000 and fam==0xe48bff56 and n==256 and total==len(u)//512;assert i not in blocks;blocks[i]=(addr,b[32:288])
assert sorted(blocks)==list(range(len(blocks)))
assert all(blocks[i][0]==0x10000000+i*256 and blocks[i][0]+256<=0x10200000 for i in blocks)
b=blocks[0][1];crc=0xffffffff
for v in b[:252]:
 crc^=v<<24
 for _ in range(8):crc=((crc<<1)^(0x04c11db7 if crc&0x80000000 else 0))&0xffffffff
assert struct.unpack('<I',b[252:])[0]==crc
# Independently decode QE mask/test/conditional branch straight from actual UF2.
assert b[0x34:0x38]==bytes.fromhex('02221042')
h=struct.unpack('<H',b[0x38:0x3a])[0];assert h>>8==0xd1
imm=h&255;target=0x38+4+2*(imm if imm<128 else imm-256);assert target==0x64
report=json.loads((R/'generated/electronics/firmware/firmware-check.json').read_text())
assert hashlib.sha256(u).hexdigest()==report['uf2_sha256']
for f,h in report['board_source_sha256'].items():assert hashlib.sha256((R/'electronics/firmware/QUADCUBER_A1'/f).read_bytes()).hexdigest()==h
out={'pass':True,'component_count':len(refs),'pin_crosschecks':checks,'uf2_blocks':len(blocks),'crc':hex(crc),'QE_branch_target':hex(target),'sha256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [R/'electronics/quadcuber.kicad_pcb',R/'electronics/circuit.py',R/'generated/electronics/bom.csv',R/'generated/electronics/firmware/quadcuber-a1-micropython-v1.27.0.uf2']},'limits':'No hardware executed; fixed upstream build tree absent; UF2 integrity and QE instructions independently checked without rebuilding.'}
(O/'checks.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
