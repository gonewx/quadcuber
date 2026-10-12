from pathlib import Path
import csv, math
p=Path(__file__).parent
for name,expr in [('xor_exact','V(YTD) > 0.5 ^ V(IN) > .5'),('xor_parenthesized','(V(YTD) > 0.5) ^ (V(IN) > .5)'),('xor_adapted','(V(YTD) > 0.5) != (V(IN) > .5)')]:
 (p/(name+'.cir')).write_text(f'''{name}: four boolean combinations plus threshold boundaries
VYTD YTD 0 0
VIN IN 0 0
EXOR P 0 VALUE={{IF({expr}, 1, 0)}}
RLOAD P 0 1k
.DC VYTD 0 1 0.5 VIN 0 1 0.5
.PRINT DC FORMAT=CSV V(YTD) V(IN) V(P)
.END
''')
(p/'logic_value.cir').write_text('''Logic spellings, nested braces, IF and E/G VALUE optional equals
VA A 0 0
VB B 0 0
EAND1 AS 0 VALUE {{IF(V(A)>0.5 & V(B)>0.5,1,0)}}
EAND2 AD 0 VALUE={IF(V(A)>0.5 && V(B)>0.5,1,0)}
EOR1 OS 0 VALUE {{IF(V(A)>0.5 | V(B)>0.5,1,0)}}
EOR2 OD 0 VALUE={IF(V(A)>0.5 || V(B)>0.5,1,0)}
G1 0 GS VALUE {IF(V(A)>0.5,2m,-1m)}
G2 0 GE VALUE = {{IF(V(A)>0.5,2m,-1m)}}
RGS GS 0 1k
RGE GE 0 1k
.DC VA 0 1 0.5 VB 0 1 0.5
.PRINT DC FORMAT=CSV V(A) V(B) V(AS) V(AD) V(OS) V(OD) V(GS) V(GE)
.END
''')
(p/'switch_transfer.cir').write_text('''Continuous VSWITCH transfer using unchanged TI Driver_U8_S31 model values
VCTRL CTRL 0 0
VTEST P 0 1
S1 P 0 CTRL 0 _U8_S31
.MODEL _U8_S31 VSWITCH Roff=10e6 Ron=40m Voff=0.4 Von=1.1
.DC VCTRL 0.3 1.2 0.05
.PRINT DC FORMAT=CSV V(CTRL) I(VTEST)
.END
''')
for name,ic in [('ic_alias_space','.IC V(EN )=0\n.IC V(COMP)={STEADY_STATE*1.3695}'),('ic_alias_compact','.IC V(EN)=0\n.IC V(COMP)={STEADY_STATE*1.3695}')]:
 (p/(name+'.cir')).write_text(f'''{name}: original TI formal pin names, renamed actual nets, nonzero parameter value
VBIAS BIAS 0 1
X1 ACTUAL_EN ACTUAL_COMP TESTIC PARAMS: STEADY_STATE=1
.SUBCKT TESTIC EN COMP PARAMS: STEADY_STATE=0
RE BIAS EN 1k
CE EN 0 1u
RC COMP 0 1k
CC COMP 0 1u
{ic}
.ENDS TESTIC
.GLOBAL BIAS
.TRAN 1u 1m 0 1u UIC
.PRINT TRAN FORMAT=CSV V(ACTUAL_EN) V(ACTUAL_COMP)
.END
''')
for name,ic in [('ic_no_equals','.IC V(Qint) {VSS}'),('ic_with_equals','.IC V(Qint)={VSS}')]:
 (p/(name+'.cir')).write_text(f'''{name}: exact TI latch IC syntax versus equals-only repair
X1 OUT TESTIC PARAMS: VSS=0.25
.SUBCKT TESTIC OUT PARAMS: VSS=0
RQ Qint 0 1k
CQ Qint 0 1u
EOUT OUT 0 VALUE={{V(Qint)}}
{ic}
.ENDS TESTIC
.TRAN 1u 1m 0 1u UIC
.PRINT TRAN FORMAT=CSV V(OUT)
.END
''')
for mode in ['op','uic','noop']:
 for useic in [False,True]:
  suffix='_ic' if useic else '_noic'
  (p/f'rc_{mode}{suffix}.cir').write_text(f'''Tiny RC {mode} {suffix}: 1 V source, tau=1 ms
VS IN 0 1
R1 IN OUT 1k
C1 OUT 0 1u
{'.IC V(OUT)=0.25' if useic else ''}
.TRAN 1u 1m 0 1u {mode.upper() if mode!='op' else ''}
.PRINT TRAN FORMAT=CSV V(OUT)
.END
''')
with (p/'switch_expected.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['control_V','resistance_ohm','I_VTEST_A'])
 for i in range(19):
  v=.3+i*.05; x=(v-.4)/(.7)
  if x<=0:r=1e7
  elif x>=1:r=.04
  else:
   s=2*x-1;r=math.exp(math.log(math.sqrt(.04*1e7))+.75*math.log(.04/1e7)*s-.25*math.log(.04/1e7)*s**3)
  w.writerow([v,r,-1/r])
with (p/'xor_expected.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['YTD','IN','P'])
 for b in [0,.5,1]:
  for a in [0,.5,1]:w.writerow([a,b,int((a>.5)!=(b>.5))])
