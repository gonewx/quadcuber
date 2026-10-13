"""Quadcuber integrated four-arm PCB A1. Pin contract imported, never duplicated."""
from pathlib import Path
import runpy
ARMS=runpy.run_path(str(Path(__file__).resolve().parents[1]/'wiring/spec.py'))['ARMS']
C=[]
def add(ref,value,fp,pins,xy,mpn,mfr,section,names=None,types=None,note='',rot=0):
    C.append(dict(ref=ref,value=value,fp=fp,pins={str(k):v for k,v in pins.items()},xy=xy,mpn=mpn,mfr=mfr,section=section,names=names or {},types=types or {},note=note,rot=rot))
RFP='Resistor_SMD:R_0603_1608Metric'
CFP='Capacitor_SMD:C_0805_2012Metric'
def r(ref,v,a,b,xy,sec,mpn=None):
    codes={'100k':'100K','10k':'10K','100':'100R','220':'220R','43.2k':'43K2','100k 0.1%':'100K','13.3k':'13K3','511k':'511K','105k':'105K','49.9':'49R9','1k':'1K','5.1k':'5K1'}
    add(ref,v,RFP,{1:a,2:b},xy,mpn or 'RC0603FR-07'+codes[v]+'L','Yageo',sec)
def c(ref,v,a,b,xy,sec):
    spec={'100n':('GRM21BR71H104KA01L',CFP),'10u/25V':('GRM32DR71E106KA12L','Capacitor_SMD:C_1210_3225Metric'),'22u/25V':('GRM32ER71E226KE15L','Capacitor_SMD:C_1210_3225Metric'),'75p':('C0603C750J5GACTU','Capacitor_SMD:C_0603_1608Metric'),'470u/25V':('EEU-FR1E471','Capacitor_THT:CP_Radial_D10.0mm_P5.00mm'),'470u/10V':('EEU-FR1A471','Capacitor_THT:CP_Radial_D8.0mm_P3.50mm')}
    mpn,fp=spec[v];add(ref,v,fp,{1:a,2:b},xy,mpn,'Panasonic' if v.startswith('470') else ('KEMET' if v=='75p' else 'Murata'),sec,names={'1':'+' if v.startswith('470') else '1','2':'-' if v.startswith('470') else '2'})
def header(ref,nets,xy,sec,desc):
    n=len(nets);add(ref,desc,f'Connector_PinHeader_2.54mm:PinHeader_1x{n:02d}_P2.54mm_Vertical',dict(enumerate(nets,1)),xy,f'6130{n:02d}11121','Wurth Elektronik',sec)
# Direct RP2040: official pin identities, 12MHz/2MiB Pico-compatible boot hardware.
gp={0:2,1:3,2:4,3:5,4:6,5:7,6:8,7:9,8:11,9:12,10:13,11:14,12:15,13:16,14:17,15:18,16:27,17:28,18:29,19:30,20:31,21:32,22:34,23:35,24:36,25:37,26:38,27:39,28:40,29:41}
pins={i:None for i in range(1,58)}
for g,pin in gp.items():pins[pin]=f'GP{g}' if g in list(range(22))+[24,25] else None
for pin in [1,10,22,33,42,43,44,48,49]:pins[pin]='3V3'
for pin in [23,45,50]:pins[pin]='1V1'
pins.update({19:'GND',20:'XIN',21:'XOUT',24:'SWCLK',25:'SWDIO',26:'RUN',46:'USB_DM_MCU',47:'USB_DP_MCU',51:'QSPI_SD3',52:'QSPI_SCLK',53:'QSPI_SD0',54:'QSPI_SD2',55:'QSPI_SD1',56:'QSPI_SS',57:'GND'})
names={str(pin):f'GPIO{g}' for g,pin in gp.items()}
names.update({str(i):n for i,n in {1:'IOVDD',10:'IOVDD',22:'IOVDD',33:'IOVDD',42:'IOVDD',49:'IOVDD',43:'ADC_AVDD',44:'VREG_IN',45:'VREG_OUT',48:'USB_VDD',23:'DVDD',50:'DVDD',19:'TESTEN',20:'XIN',21:'XOUT',24:'SWCLK',25:'SWDIO',26:'RUN',46:'USB_DM',47:'USB_DP',51:'QSPI_SD3',52:'QSPI_SCLK',53:'QSPI_SD0',54:'QSPI_SD2',55:'QSPI_SD1',56:'QSPI_SS',57:'GND_EP'}.items()})
types={str(i):'power_in' for i in [1,10,22,23,33,42,43,44,48,49,50,57]};types.update({'45':'power_out','19':'input','26':'input','24':'input','25':'bidirectional','20':'input','21':'output'})
for g,pin in gp.items():types[str(pin)]='bidirectional'
add('U1','RP2040','Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm_ThermalVias',pins,(20,27),'RP2040','Raspberry Pi','controller',names=names,types=types,note='Bare RP2040, not a Pico module. EP57 and TESTEN19 ground; DVDD23/50 supplied only by VREG_OUT45.')
header('J2',['GND','GP0','GP1'],(7,57),'controller','UART GND TX RX')
header('J3',['RUN','GND'],(25,61),'controller','RESET')
header('J4',['3V3','SWDIO','GND','SWCLK'],(15,55),'controller','SWD VREF D G C')
C[-1]['rot']=90
r('R400','10k','3V3','RUN',(8,37),'controller')
add('S2','RUN RESET','Button_Switch_SMD:SW_SPST_TL3342',{1:'RUN',2:'GND'},(7,43),'TL3342F160QG','E-Switch','controller')
def cc(ref,value,a,b,xy,sec,rot=0):
 specs={'100n':('GRM155R71C104KA88D','Capacitor_SMD:C_0402_1005Metric'),'1u':('GRM155R61C105KA12D','Capacitor_SMD:C_0402_1005Metric'),'15p':('GRM1555C1H150JA01D','Capacitor_SMD:C_0402_1005Metric'),'1u/16V':('GRM21BR71C105KA01L','Capacitor_SMD:C_0805_2012Metric'),'4.7u/16V':('C0805C475K4PACTU','Capacitor_SMD:C_0805_2012Metric')}
 mpn,fp=specs[value];add(ref,value,fp,{1:a,2:b},xy,mpn,'KEMET' if value=='4.7u/16V' else 'Murata',sec,rot=rot)
cc('C400','100n','RUN','GND',(11,37),'controller')
# One local 100n per supply pin; internal LDO in/out each additionally has 1uF.
for i,pin in enumerate([1,10,22,33,42,43,48,49,23,50]):
 cc(f'C{410+i}','100n','1V1' if pin in [23,50] else '3V3','GND',(10+i*2,25),'controller_power')
 C[-1]['decouple_pin']=pin;C[-1]['side']='B.Cu'
for ref,pin in [('C420',44),('C421',45)]:
 cc(ref,'1u','3V3' if pin==44 else '1V1','GND',(28,20),'controller_power');C[-1]['decouple_pin']=pin;C[-1]['side']='B.Cu'
# 5V_A and USB independently diode-OR into VSYS; neither can feed the other source.
add('D2','SS14 external logic isolation','Diode_SMD:D_SMA',{1:'VSYS',2:'5V_A'},(37,14),'SS14-E3/61T','Vishay','controller_power',names={'1':'K','2':'A'})
add('D5','SS14 USB isolation','Diode_SMD:D_SMA',{1:'VSYS',2:'USB_FUSED'},(32,13),'SS14-E3/61T','Vishay','usb',names={'1':'K','2':'A'})
C[-1]['side']='B.Cu'
cc('C1','1u/16V','VSYS','GND',(27.2,20),'controller_power',rot=180)
add('U5','TLV75533PDBVR','Package_TO_SOT_SMD:SOT-23-5',{1:'VSYS',2:'GND',3:'VSYS',4:None,5:'3V3'},(31,22),'TLV75533PDBVR','Texas Instruments','controller_power',names={'1':'IN','2':'GND','3':'EN','4':'NC','5':'OUT'},types={'1':'power_in','2':'power_in','3':'input','5':'power_out'},note='3.3V/500mA IC rating; controller continuous design target <=150mA; no external 3V3 injection.')
cc('C422','4.7u/16V','3V3','GND',(35,20),'controller_power')
# USB-C USB2 UFP only: independent 5.1k CC resistors, no PD and no host power sourcing.
up={'A1':'GND','A4':'USB_VBUS','A5':'USB_CC1','A6':'USB_DP','A7':'USB_DM','A8':None,'A9':'USB_VBUS','A12':'GND','B1':'GND','B4':'USB_VBUS','B5':'USB_CC2','B6':'USB_DP','B7':'USB_DM','B8':None,'B9':'USB_VBUS','B12':'GND','S1':'GND'}
add('J5','USB-C data / BOOTSEL','Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal',up,(20,3.675),'USB4105-GF-A','GCT','usb',rot=180,note='USB2 device only. CC1/CC2 each 5.1k to ground. Shell ground. No PD.')
r('R401','5.1k','USB_CC1','GND',(12,8),'usb');r('R402','5.1k','USB_CC2','GND',(28,9),'usb')
add('F3','0.5A USB PTC','Fuse:Fuse_1812_4532Metric',{1:'USB_VBUS',2:'USB_FUSED'},(32,4),'MF-MSMF050-2','Bourns','usb')
cc('C423','1u/16V','USB_VBUS','GND',(37,4),'usb')
add('U6','USBLC6-2SC6','Package_TO_SOT_SMD:SOT-23-6',{1:'USB_DP',2:'GND',3:'USB_DM',4:'USB_DM',5:'VSYS',6:'USB_DP'},(20,12),'USBLC6-2SC6','STMicroelectronics','usb',names={'1':'IO1','2':'GND','3':'IO2','4':'IO2','5':'VBUS','6':'IO1'},rot=90)
for ref,a,b,xy in [('R403','USB_DM','USB_DM_MCU',(21.4,21)),('R404','USB_DP','USB_DP_MCU',(20.4,21))]:
 add(ref,'27','Resistor_SMD:R_0402_1005Metric',{1:a,2:b},xy,'RC0402FR-0727RL','Yageo','usb',rot=270)
cc('C427','100n','VSYS','GND',(24,11),'usb')
r('R405','100k','USB_VBUS','GP24',(34,31),'controller');r('R406','100k','GP24','GND',(34,35),'controller')
# Flash, clock, BOOTSEL; 2MiB W25Q16RV; see firmware/QUADCUBER_A1 for QE-bit-aware W25Q080 boot2.
add('U7','W25Q16RVCNJQ 2MiB','Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',{1:'QSPI_SS',2:'QSPI_SD1',3:'QSPI_SD2',4:'GND',5:'QSPI_SD0',6:'QSPI_SCLK',7:'QSPI_SD3',8:'3V3'},(10,23),'W25Q16RVCNJQ','Winbond','flash_clock',note='Current-production RV successor per Winbond PCN DM202601-03-A / AN0000070. CN 150mil SOP8; use QUADCUBER_A1 MicroPython boot2 QE-mask adaptation.',names={'1':'CS_N','2':'DO_IO1','3':'WP_IO2','4':'GND','5':'DI_IO0','6':'CLK','7':'HOLD_IO3','8':'VCC'})
cc('C424','100n','3V3','GND',(14,20),'flash_clock')
r('R407','10k','3V3','QSPI_SS',(13,16.5),'flash_clock');r('R408','1k','QSPI_SS','BOOT_BUTTON',(7,9),'flash_clock')
add('S1','BOOTSEL','Button_Switch_SMD:SW_SPST_TL3342',{1:'BOOT_BUTTON',2:'GND'},(7,13),'TL3342F160QG','E-Switch','flash_clock')
add('Y1','12MHz CL10pF','Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm',{1:'XIN',2:'GND',3:'XOUT_DAMPED',4:'GND'},(20,34),'ABM8-272-T3','Abracon','flash_clock')
add('R409','1k','Resistor_SMD:R_0402_1005Metric',{1:'XOUT',2:'XOUT_DAMPED'},(24,32),'RC0402FR-071KL','Yageo','flash_clock')
cc('C425','15p','XIN','GND',(16.7,34.95),'flash_clock',rot=180);cc('C426','15p','XOUT_DAMPED','GND',(23.2,33.5),'flash_clock')
add('D7','USER LED GP25','LED_SMD:LED_0603_1608Metric',{1:'GND',2:'LED_ANODE'},(28,16),'LTST-C190KGKT','Lite-On','controller',names={'1':'K','2':'A'})
r('R410','1k','GP25','LED_ANODE',(25,16),'controller')
# Main 9V path: fuse + ideal diode; external physical disconnect is still required.
add('J1','9V DC center-positive','Quadcuber:Jack_DC_Switchcraft_RASPC722X',{1:'VIN',2:'GND',3:None},(45.5,0),'RASPC722X','Switchcraft','power',names={'1':'CENTER_9V','2':'SLEEVE_GND','3':'SLEEVE_SHUNT_NC'},note='5.5/2.1 mm mating plug 762/762Z, 9.5 mm barrel; 5A carrying rating, regulated 9V continuous input budget <=5A. Project pins 1=center, 2=sleeve, 3=sleeve shunt NC. Drawing visually verified by parent thread; original PDF pending local archive. See sources/raspc722x-review.md.')
add('F1','8A 24V time-lag fuse','Quadcuber:Fuse_Littelfuse_407_1206',{1:'VIN',2:'VIN_FUSED'},(57,9),'0407008.WR','Littelfuse','power',note='407 time-lag; 24VDC, 60A interrupt, nominal melting I2t24.12A2s; not fast semiconductor protection. Continuous input design budget <=5A; current-limited 9V source required.')
add('U4','LM74700QDBVRQ1','Package_TO_SOT_SMD:SOT-23-6',{1:'IDEAL_VCAP',2:'GND',3:'VIN_FUSED',4:'VM',5:'IDEAL_GATE',6:'VIN_FUSED'},(67,22),'LM74700QDBVRQ1','Texas Instruments','power',names={'1':'VCAP','2':'GND','3':'EN','4':'CATHODE','5':'GATE','6':'ANODE'},types={'1':'passive','2':'power_in','3':'input','4':'input','5':'output','6':'power_in'},note='Ideal diode / reverse polarity. EN is NOT a power disconnect.')
add('Q1','CSD18540Q5B','Package_TO_SOT_SMD:TDSON-8-1',{1:'VIN_FUSED',2:'VIN_FUSED',3:'VIN_FUSED',4:'IDEAL_GATE',5:'VM'},(67,13),'CSD18540Q5B','Texas Instruments','power',names={'1':'S','2':'S','3':'S','4':'G','5':'D_EP'})
c('C4','100n','IDEAL_VCAP','VIN_FUSED',(62,25),'power')
c('C5','100n','VIN_FUSED','GND',(72,22),'power')
add('D4','SMBJ12CA input transient','Diode_SMD:D_SMB',{1:'VIN_FUSED',2:'GND'},(56,19),'SMBJ12CA','Littelfuse','power',names={'1':'BI','2':'BI'})
add('D3','SMBJ12A transient clamp','Diode_SMD:D_SMB',{1:'VM',2:'GND'},(84,13),'SMBJ12A','Littelfuse','power',names={'1':'K','2':'A'},note='12V stand-off, 19.9V rated pulse clamp. Pulse-only; never sustained 12V input.')
c('C2','470u/25V','VM','GND',(91,10),'power')
c('C3','470u/25V','VM','GND',(107,10),'power')
# Defined minimum VM load: prevents repeated small regen events accumulating on bulk caps.
for ref,xy in [('R500',(125,9)),('R501',(125,24))]:
    add(ref,'300R 1W VM bleed','Resistor_SMD:R_2512_6332Metric',{1:'VM',2:'GND'},xy,'CRCW2512300RFKEG','Vishay','power',note='Two 300R/1% in parallel:150R VM bleed, 0.562W total at9.18V. Operating envelope total regen <=0.05J/event and <=5Hz; verify actual energy and resistor film temperature. Not a full-power brake.')
# Independent TPS54302 converters: each feeds two servos; A also powers encoder/logic.
for idx,(x,y) in enumerate([(49,38),(98,38)]):
    n=idx+1; sec=f'buck{n}'; rail='5V_'+('A' if idx==0 else 'B'); pre=f'B{n}_'; u=2+idx
    add(f'U{u}','TPS54302DDCR','Package_TO_SOT_SMD:SOT-23-6',{1:'GND',2:pre+'SW',3:'VM',4:pre+'FB',5:pre+'EN',6:pre+'BOOT'},(x,y),'TPS54302DDCR','Texas Instruments',sec,names={'1':'GND','2':'SW','3':'VIN','4':'FB','5':'EN','6':'BOOT'},types={'1':'power_in','2':'output','3':'power_in','4':'input','5':'input','6':'passive'})
    c(f'C{10+n*10}','10u/25V','VM','GND',(x-5,y-2),sec)
    c(f'C{11+n*10}','100n','VM','GND',(x-5,y+2),sec)
    c(f'C{12+n*10}','100n',pre+'BOOT',pre+'SW',(x-1,y+3.9),sec)
    add(f'L{n}','10uH 9A Isat16A','Inductor_SMD:L_Bourns_SRP1245A',{1:pre+'SW',2:rail},(x+12,y),'SRP1245A-100M','Bourns',sec)
    c(f'C{13+n*10}','22u/25V',rail,'GND',(x+22,y-3),sec)
    c(f'C{14+n*10}','22u/25V',rail,'GND',(x+22,y+2),sec)
    r(f'R{11+n*10}','100k',rail,pre+'FB',(x+8,y+10),sec,mpn='RT0603BRD07100KL')
    r(f'R{12+n*10}','13.3k',pre+'FB','GND',(x+3,y+10),sec,mpn='RT0603BRD0713K3L')
    c(f'C{15+n*10}','75p',rail,pre+'FB',(x+8,y+14),sec)
    r(f'R{13+n*10}','511k','VM',pre+'EN',(x-7,y+10),sec)
    r(f'R{14+n*10}','105k',pre+'EN','GND',(x-2,y+14),sec)
    c(f'C{16+n*10}','470u/10V',rail,'GND',(x+25,y+12),sec)
add('F2','0.5A encoder PTC','Fuse:Fuse_1812_4532Metric',{1:'5V_A',2:'5V_ENC'},(36,58),'MF-MSMF050-2','Bourns','controller')
# 4 identical arm cells 34mm pitch. Motor jack footprint remains explicit provisional.
for idx,(arm,(motor,enc,servo,sm)) in enumerate(ARMS.items()):
    x=15+34*idx; sec='arm_'+arm; base=100+idx*20; rail='5V_A' if idx<2 else '5V_B'; en=f'{arm}_'; drv=10+idx; buf=20+idx
    add(f'U{drv}','DRV8871DDAR','Package_SO:Texas_HTSOP-8-1EP_3.9x4.9mm_P1.27mm_EP2.95x4.9mm_Mask2.4x3.1mm_ThermalVias',{1:'GND',2:f'GP{motor[1]}',3:f'GP{motor[0]}',4:en+'ILIM',5:'VM',6:en+'M1',7:'GND',8:en+'M2',9:'GND'},(x,77),'DRV8871DDAR','Texas Instruments',sec,names={'1':'GND','2':'IN2','3':'IN1','4':'ILIM','5':'VM','6':'OUT1','7':'PGND','8':'OUT2','9':'EP_GND'},types={'1':'power_in','2':'input','3':'input','4':'input','5':'power_in','6':'output','7':'power_in','8':'output','9':'power_in'})
    r(f'R{base}','43.2k',en+'ILIM','GND',(x-3,83),sec)
    r(f'R{base+1}','100k',f'GP{motor[0]}','GND',(x-7,74),sec)
    r(f'R{base+2}','100k',f'GP{motor[1]}','GND',(x-7,78),sec)
    c(f'C{base}','100n','VM','GND',(x+7,76),sec)
    c(f'C{base+1}','10u/25V','VM','GND',(x+8,81),sec)
    c(f'C{base+2}','470u/25V','VM','GND',(x+14,70),sec)
    add(f'J{10+idx}',f'EV3 {arm} PINMAP HOLD','Quadcuber:EV3_UserDrawing_PINMAP_HOLD',{1:en+'M1',2:en+'M2',3:'GND',4:'5V_ENC',5:en+'ENC_A_RAW',6:en+'ENC_B_RAW'},(x+(1 if idx==0 else 0),106),'UNCONFIRMED user drawing','Unconfirmed (Coorle watermark)',sec,names={'1':'M1','2':'M2','3':'GND','4':'+5V','5':'TACHO0','6':'TACHO1'},rot=180,note='Nominal hole geometry from user drawing. HOLD: actual MPN, numbering 1-5, observation side, contact current and ear envelope require confirmation. See sources/ev3-user-drawing-review.md.')
    add(f'U{buf}','SN74LVC2G17DBVR','Package_TO_SOT_SMD:SOT-23-6',{1:en+'ENC_A_F',2:'GND',3:en+'ENC_B_F',4:f'GP{enc[1]}',5:'3V3',6:f'GP{enc[0]}'},(x-6,91),'SN74LVC2G17DBVR','Texas Instruments',sec,names={'1':'1A','2':'GND','3':'2A','4':'2Y','5':'VCC','6':'1Y'},types={'1':'input','2':'power_in','3':'input','4':'output','5':'power_in','6':'output'})
    for j,ab in enumerate(('A','B')):
        r(f'R{base+3+j}','1k',en+f'ENC_{ab}_RAW',en+f'ENC_{ab}_F',(x-12,88+j*4),sec)
        r(f'R{base+5+j}','100k',en+f'ENC_{ab}_F','GND',(x-1,88+j*4),sec)
    c(f'C{base+3}','100n','3V3','GND',(x-6,86),sec)
    c(f'C{base+4}','100n','5V_ENC','GND',(x+5,89),sec)
    add(f'F{10+idx}','1.1A servo PTC','Quadcuber:Fuse_Bourns_MF_MSMF_Style2_1812',{1:rail,2:en+'SERVO_5V'},(x+14,87),'MF-MSMF110/16X-2','Bourns',sec)
    header(f'J{20+idx}',['GND',en+'SERVO_5V',en+'SERVO_PWM'],(x+13,97),sec,f'{arm} SERVO G + S')
    add(f'U{30+idx}','SN74AHCT1G125DBVR','Package_TO_SOT_SMD:SOT-23-5',{1:'GND',2:f'GP{servo[0]}',3:'GND',4:en+'SERVO_BUF',5:en+'SERVO_5V'},(x+20,97),'SN74AHCT1G125DBVR','Texas Instruments',sec,names={'1':'OE_N','2':'A','3':'GND','4':'Y','5':'VCC'},types={'1':'input','2':'input','3':'power_in','4':'output','5':'power_in'},note='Input leakage specified at VCC=0; prevents USB-only GPIO phantom servo supply.')
    c(f'C{base+5}','100n',en+'SERVO_5V','GND',(x+24,97),sec)
    r(f'R{base+9}','100k',f'GP{servo[0]}','GND',(x+20,84),sec)
    r(f'R{base+7}','220',en+'SERVO_BUF',en+'SERVO_PWM',(x+18,103),sec)
    r(f'R{base+8}','100k',en+'SERVO_PWM','GND',(x+17,93),sec)
# Accessible scope pads, including motor outputs and encoders.
for i,net in enumerate(['GND','VM','5V_A','5V_B','5V_ENC','3V3','VSYS']):
    add(f'TP{i+1}',net,'TestPoint:TestPoint_Pad_D2.0mm',{1:net},(84+i*7,61),'N/A PCB copper','PCB','controller')
for idx,(arm,a) in enumerate(ARMS.items()):
    for j,net in enumerate([f'{arm}_M1',f'{arm}_M2',f'GP{a[1][0]}',f'GP{a[1][1]}']):
        add(f'TP{10+idx*4+j}',net,'TestPoint:TestPoint_Pad_D1.5mm',{1:net},(6+idx*34+j*5,67),'N/A PCB copper','PCB','arm_'+arm)
for i,xy in enumerate([(4,4),(140,4),(4,108),(140,108)],1):
    add(f'H{i}','M3 insulated standoff','MountingHole:MountingHole_3.2mm_M3',{},xy,'N/A NPTH','PCB','mechanical')

# Optional bulk pads: default DNP preserves the TI 44uF/75pF compensated reference.
for comp in C:
    if comp['ref'] in ('C26','C36'):
        comp['dnp']=True
        comp['note']='DNP by default. Populate only after loop/step-response verification with added 470uF.'
# Buck placement follows the switching loop, with SW facing the inductor.
for i,x in [(1,49),(2,98)]:
    loc={f'U{i+1}':(x,38,180),f'C{10+i*10}':(x+3,46.5,270),f'C{11+i*10}':(x+3.5,41.5,270),f'C{12+i*10}':(x-1,41.9,0),f'R{11+i*10}':(x-5,45,0),f'R{12+i*10}':(x-5,41,0),f'C{15+i*10}':(x-9,45,0),f'R{13+i*10}':(x-8,29,0),f'R{14+i*10}':(x-10,35,0)}
    for comp in C:
        if comp['ref'] in loc:
            xx,yy,rr=loc[comp['ref']];comp['xy']=(xx,yy);comp['rot']=rr
