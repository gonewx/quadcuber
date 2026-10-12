#!/usr/bin/env python3
"""Verify UF2 family, address range, boot2 CRC and QE branch in the built binary."""
import argparse, hashlib, json, re, shutil, struct, subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('build',type=Path);p.add_argument('--objdump',default='arm-none-eabi-objdump');a=p.parse_args()
out=Path(__file__).resolve().parents[2]/'generated/electronics/firmware';out.mkdir(parents=True,exist_ok=True)
u=(a.build/'firmware.uf2').read_bytes();assert len(u)%512==0
blocks={};family=0xe48bff56
for off in range(0,len(u),512):
 b=u[off:off+512];m0,m1,flags,addr,n,idx,count,fam=struct.unpack('<8I',b[:32])
 assert (m0,m1,struct.unpack('<I',b[508:])[0])==(0x0a324655,0x9e5d5157,0x0ab16f30)
 assert flags&0x2000 and fam==family and n==256 and count==len(u)//512
 assert 0x10000000<=addr and addr+n<=0x10200000 and idx not in blocks
 blocks[idx]=(addr,b[32:32+n])
assert sorted(blocks)==list(range(len(blocks)))
assert all(blocks[i][0]==0x10000000+i*256 for i in blocks)
boot=blocks[0][1];raw=(a.build/'pico-sdk/src/rp2040/boot_stage2/bs2_default.bin').read_bytes()
assert len(raw)<=252 and boot[:len(raw)]==raw and not any(boot[len(raw):252])
# RP2040 ROM CRC: non-reflected polynomial, seed FFFFFFFF, no final xor.
crc=0xffffffff
for value in boot[:252]:
 crc ^= value<<24
 for _ in range(8):crc=((crc<<1)^ (0x04c11db7 if crc&0x80000000 else 0))&0xffffffff
assert struct.unpack('<I',boot[252:])[0]==crc
elf=a.build/'pico-sdk/src/rp2040/boot_stage2/bs2_default.elf'
dis=subprocess.check_output([a.objdump,'-d',str(elf)],text=True)
assert re.search(r'4210\s+tst\s+r0, r2\s*\n[^\n]+d1[0-9a-f]{2}\s+bne\.n\s+[0-9a-f]+ <skip_sreg_programming>',dis)
# Confirm the branch targets the skip label, beyond all status-register writes.
match=re.search(r'([0-9a-f]+):\s+d1([0-9a-f]{2})\s+bne\.n\s+([0-9a-f]+) <skip_sreg_programming>',dis)
pc,imm,target=[int(x,16) for x in match.groups()];assert pc+4+2*(imm if imm<128 else imm-256)==target
assert boot[pc-int(re.search(r'([0-9a-f]+) <_stage2_boot>',dis)[1],16)-4:][:4]==b'\x02\x22\x10\x42'
shutil.copyfile(a.build/'firmware.uf2',out/'quadcuber-a1-micropython-v1.27.0.uf2')
(out/'boot2-disassembly.txt').write_text(dis.replace(str(a.build),'<BUILD>'))
report={'checks_passed':True,'hardware_tested':False,'micropython_commit':'78ff170de9e32c79db6e64d3e33d2bd60002bdcd','pico_sdk_commit':'9a4113fbbae65ee82d8cd6537963bc3d3b14bcca','flash_mpn':'W25Q16RVCNJQ','uf2_sha256':hashlib.sha256(u).hexdigest(),'uf2_bytes':len(u),'uf2_blocks':len(blocks),'family_id':hex(family),'flash_address_end_exclusive':hex(blocks[len(blocks)-1][0]+256),'boot2_raw_bytes':len(raw),'boot2_crc32':hex(crc),'qe_test':'binary TST r0,r2 then BNE to skip_sreg_programming; QE mask 0x02 accepts SR2=0x02 and 0x06','board_source_sha256':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted((Path(__file__).parent/'QUADCUBER_A1').glob('*')) if f.is_file()}}
(out/'firmware-check.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
