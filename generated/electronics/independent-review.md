# 独立复核：四臂 PCB A1（板载 RP2040）

> 历史证据：以下为KiCad 9迁移前对象的独立审查，保留原始哈希与结论。KiCad 10.0.7迁移后的文件哈希已经改变，本报告不代表重新独立审查；当前ERC/DRC、契约和几何对照见 `kicad10-migration.json`、`release-status.json` 及新导出的检查报告。

复核日期：2026-10-12。对象为 `electronics/quadcuber.kicad_pcb`，SHA-256：

`c33afa92c1e76d124cc7d846db8a845486d428d554f05d406cef071aeb02e43b`

本报告替换旧 A0 报告。方法为只读 KiCad 9 `pcbnew` 原生对象，核查焊盘、线段、过孔、实填铜区、网络与器件方向，并与 A0 基线功率区域比较。另核读电气源、原厂参考和正式导出的检查报告。未修改 PCB；未制造、通电或进行信号完整性/热仿真。

## 检查证据与版本绑定

- `drc.rpt`：2026-10-12 02:29:08 UTC，0 DRC 违规、0 未连接、0 封装错误。`build-log.json` 确认使用 `pcb drc --schematic-parity`。
- `erc.rpt`：2026-10-12 02:29:06 UTC，0 错误、0 警告。
- `contract-check.json`：`contract_errors=[]`。契约检查证明工程内连接符合设计定义，不证明 EV3 实物针号正确。
- `release-status.json` 中全部原生文件 SHA-256 与复核时磁盘文件相符；`manufacturing_release=false`、`hardware_tested=false`。
- 复核时电气源哈希：`circuit.py` 为 `e90767906205461e028785313fd5f1c17ea48440ee5bd65a107c31c6d903ade2`；`generate.py` 为 `ed746824238bf450522211a66a0dbc0c484b085808a5441efb8adf8c2c5e56c2`；`check.py` 为 `93e008955795d047d81aed0f57c6fbb784073215a5319c882ab0afe9c11f5261`；`build.py` 为 `e974396186046a995a8dc7f6384e0fc75c4ed8ce87c0974e430f492c0ef86195`。

## RP2040、启动和供电

裸 RP2040 已替代 Pico 插座。IOVDD、ADC_AVDD、USB_VDD、VREG_IN 为3.3V；VREG_OUT仅供DVDD的1.1V，TESTEN及EP接地。W25Q16RVCNJQ为CN 150mil窄体SOIC8，保持SOIC-8_3.9x4.9mm_P1.27mm封装，避免CS宽体封装误用。12MHz ABM8-272-T3、两颗15pF、XOUT串1k、BOOTSEL串1k及RUN复位符合所引用的最小系统方案。采用QUADCUBER_A1的QE掩码适配boot2；本板UF2启动尚未实测。

USB和外部5V_A经独立SS14汇入VSYS，再由TLV75533PDBVR降至3.3V。USBLC6的上保护轨接VSYS并有C427，避免外供电时DP上拉通过该器件内部导向二极管给原始VBUS回灌。USB仅给逻辑供电。GP24只是检测分压；stock TinyUSB并不因此自动关闭上拉，断电主机数据脚保护路径仍须实测。SWD的3V3为参考电压，不能作为外部供电注入口。

## USB和晶振实际布线

|网络|线段铜长度合计/mm|信号过孔数|层/线宽|
|---|---:|---:|---|
|USB_DP（连接器至串阻侧，含合并支路）|15.722|0|F.Cu，0.20mm|
|USB_DM（连接器至串阻侧，含合并支路）|16.887|2|主要F.Cu，0.20mm；连接器附近1mm B.Cu跨接|
|USB_DP_MCU（27Ω之后）|2.301|0|F.Cu，0.15mm|
|USB_DM_MCU（27Ω之后）|2.053|0|F.Cu，0.15mm|
|XIN|9.020|0|F.Cu，0.15mm|
|XOUT|4.854|0|F.Cu，0.15mm|
|XOUT_DAMPED|4.947|0|F.Cu，0.15mm|

USB两根信号分别经过正确ESD通道和27Ω电阻，电阻在MCU附近；ESD后的主要并行段中心距约0.4mm，0.20mm线宽对应约0.20mm间隙。连接器合并支路、ESD封装扇出和MCU扇出并非全程等间距，DM还有连接器附近换层。因此表中带分支的总铜长度不能直接当作差分点到点长度或时延失配，更不能据此宣称90Ω阻抗合格。板厂实际四层介质/铜厚和USB首板测试仍是放行检查项。

晶振三条信号网均没有信号过孔；长度包含负载电容分支，不能把三项相加冒充单根时钟线。晶振地焊盘和负载电容接GND。首板仍需验证起振、启动重复性及频率。

## 1.1V、去耦与地回流

1.1V仅在控制器局部连接，有3颗信号/电源过孔，线宽0.15～0.30mm，不与3.3V/VM平面混接。DVDD23的C418、DVDD50的C419对应电源焊盘直线距离分别约0.237和0.200mm；VREG_OUT的C421约1.281mm。C410/C412/C418的极性无关焊盘方向调整后，地端均实际落入B.Cu地填充，未再被孤立。

C410～C421的地端均在B.Cu实填GND内；最近接地穿孔（包括RP2040 EP热孔）直线距离约0.737～2.362mm。这是几何复核，不是每个回流环路的电感测量。并非所有指定去耦电容都紧贴对应电源脚：C417至IOVDD49约3.704mm，C414至IOVDD42约2.600mm；相关3.3V为同一平面，邻近电容也参与去耦，不能将本布局描述成“每颗都在1mm以内”。

In1.Cu没有任何走线，GND实填保持一个连续轮廓。In2.Cu有131段控制器局部走线，包围范围X=61.425～86.546mm、Y=71.850～109.175mm，全部位于允许的控制器区域；未伸入其他功率区域。其3.3V岛和VM各保持一个实填轮廓。F.Cu/B.Cu地填充分别有36/6个轮廓，不能称为完整无切割表层地面；主要连续参考地是In1.Cu。

## 原功率路径保留

- J1→F1的VIN、F1→Q1源极的VIN_FUSED、Q1漏极VM正面专用铜区均保持一个连续实填轮廓。J1.1/F1.1、F1.2/Q1源1/2/3、Q1漏5实际落在各自铜区内。J1地仍与正反面及In1地铜相连。
- 四颗DRV8871的VM短接并联过孔数仍为3/3/3/2，PGND每颗2个，孔径0.4mm、短接线宽0.6～0.8mm。各EP仍有6颗Ø0.33接地热孔。
- U2 VIN/GND各3个近端Ø0.4过孔；U3 VIN为2个、GND为3个。短线宽0.45/0.65mm，与A0改进后的路径一致。
- C20/C30保留B.Cu近端输入电容位置及0.8mm短线；两端连接长度分别约1.504/1.585mm和1.433/1.955mm。U2/U3至电感的原0.8mm短主干保留。

没有发现A1控制器布局破坏上述A0功率路径的确定性错误。当前已收紧为5A持续预算，仍依赖外铜2oz、内铜1oz、孔壁电镀及实际热环境；铜区连续不代表已经完成载流或温升认证。LM74700不是正向断电开关，也不提供浪涌限流；TVS不适合持续消耗机械回灌能量。

## EV3新图落实与制造HOLD

J10～J13实际封装为`EV3_UserDrawing_PINMAP_HOLD`，中心分别为(66,156)、(99,156)、(133,156)、(167,156)mm，均旋转180°。六个信号孔Ø0.79、两个定位孔Ø2.3、定位孔距12mm、交错横向节距1.02mm及排距2.54mm已落实。旋转后局部孔1/6分别位于(+2.55,−4.84)/(−2.55,−2.30)mm；按当前视向解释，插口朝板底边，主体前端名义到Y=162mm。

用户图仅明确标注孔6；1～5连续编号及元件面观察方向仍是推定，不能写成原厂或实物已验证。图有Coorle水印但没有完整制造商料号，不能认定为Adafruit4434。图示12.2×15mm是主体而非包括固定耳、插头和卡扣空间的完整包络。

**2026-10-12二次放大勘误：上一段漏读了左下信号孔旁的“1”。原图明确标1和6，中间2～5为端点与导体排列支持的连续顺序推导；底面图与PCB LAYOUT的互补视图支持元件面解释。** 同批样品六路断电通断与试配可关闭实物映射/配合，不把缺完整MPN或另份图纸单独作为受控打样门槛。触点电流仍须额定或受控实验依据。详细更正见 `electronics/sources/ev3-user-drawing-review.md`；本历史报告原板哈希与旧测试范围不变。

以下项目继续阻止制造放行：

1. 插座实际料号、观察面及1～5针序、逐接点至EV3线缆的映射、接点载流、焊尾配孔和固定耳完整外廓。
2. 托架、支脚、线缆运动、插拔操作和底部防护；本次未重做整机机械扫描。双面电容及其他背面器件需从原裸板间隙扣除真实高度与公差。
3. RP2040 ROM/UF2启动、Flash读写、USB组合供电和断电主机回灌、降压启动与跃变、四桥并发热测、制动回灌、浪涌和PTC降额。
4. 板厂堆叠、USB阻抗、2oz外层细间距能力、RP2040/驱动热孔与锡膏工艺。Flash选型尾项已通过下述替换关闭；库存与交期仍需在采购时核实。

## Flash选型及启动适配增量复核

早先Flash选型增量复核确认当时PCB与提交`bff3f69`的原生PCB相比，严格等于仅替换字符串`W25Q16JVSNIQ`→`W25Q16RVCNJQ`；所有铜、器件位置和焊盘网络未改变。该结论仅适用于当时Flash增量；当前保险丝、PTC和泄放增量见下节，不能继续称当前PCB仅改了Flash字符串。电气源、逐件BOM、原生原理图和PCB均已更新为CNJQ，无旧SNIQ器件值残留。

[Winbond PCN及迁移指南AN0000070](https://www.anglia.com/registration/pcn_ptn/docs/ptn/PTNW25Q16J280126%20%282%29.pdf)的表1明确包含旧SNIQ，PDF第7页表5列出150mil CNJQ替代型号；原SNIQ最后订购/交付日期仍未核实，未套用其他封装EOL日期。[Winbond 2026产品指南](https://www.winbond.com/export/sites/winbond/product-selection-guide/file/2026-Product-Selection-Guide-Winbond-Code-Storage-Flash-Memory.pdf)PDF第29页确认工业级W25Q16RV为Mass Production。[Rev H数据表](https://cdn.ozdisan.com/public/product/assets/W25Q16RV_SPI_QPI%20RevH%2010232025.pdf)的CN尺寸、2.7～3.6V、2MiB和引脚分配与当前封装/电路一致。生命周期选型HOLD已关闭。

[Mouser确切管装454-W25Q16RVCNJQ](https://www.mouser.jp/en/ProductDetail/Winbond/W25Q16RVCNJQ?qs=fQuHqd5sRUjQgmLEOK%2FjDA%3D%3D)单品页及列表独立交叉核对：15颗现货、可立即发货、MOQ1；超现货36周估计工期。这是查询时的小量供应证据，不代表已经购买或锁定库存。DigiKey CNJQ的Active/可预订与0现货不得混淆。

本地`boot2_w25q16rv.S`与pico-sdk提交`9a4113fbbae65ee82d8cd6537963bc3d3b14bcca`原`boot2_w25q080.S`独立逐行比较：除来源及解释注释外，仅`cmp r0,r2; beq`变为`tst r0,r2; bne`。`SREG_DATA=0x02`，所以SR2=0x02和0x06均跳过状态写，SR2=0x00/0x04仍进入原状态写路径；不接受QE默认0的M后缀替代。该修改正确避免RV-Q新增LB0使整字节比较失败而触发多余非易失SR1写。修改没有变更0xEB、0xA0模式、4个高阻dummy时钟或QSPI连接。

外部board配置继续为`PICO_BOARD=pico`、`PICO_PLATFORM=rp2040`、1408KiB文件系统，仅指定定制boot2及板名。复核时boot2源SHA-256为`bc6bed8ea6832293d9b9dd6ec5953e1477a136cd0eab550d0d6fd0dcc3721b69`。必须区分本适配版与未修改的官方RPI_PICO UF2。随后独立读取实际UF2并重新计算SHA、逐块检查UF2头/家族ID/连续地址、重新计算boot2 CRC及核对机器码：全部通过。UF2 SHA-256为`ce965d9bd597be5377bd1bbb1f83bb69894be7ad3f3dac80cdbe60615d143eb9`，674816字节、1318块，family=`0xe48bff56`，Flash末端不含边界地址`0x10052600`。boot2原始240字节、补零到252字节，末尾CRC为`0x9a195ca8`。UF2启动区偏移0x34包含`movs r2,#2; tst r0,r2; bne`，分支由0x38正确跳至0x64的`skip_sreg_programming`，与反汇编一致；不是只凭源码或JSON推定补丁已进入产物。board源哈希与`firmware-check.json`逐一吻合。

`firmware-build.log`显示固件链接及100%构建完成；新`tests.log`显示59项测试全部通过（8.869s）。这些是构建与静态验证，不等于已经在CNJQ实物上启动、写入或完成掉电恢复测试；`hardware_tested=false`保持不变。

## 最终保护及BOM修订复核（02:29导出）

独立通过KiCad原生对象读取确认F1为407本地封装，焊盘1.0×1.8mm、中心±1.25mm；F10～F13为Bourns Style2本地封装，焊盘1.5×3.2mm、中心±2.1mm、内隙2.7mm。GP8/GP9局部避让后的正式DRC报告为零。PTC尺寸依据原厂文本与端子覆盖推定，未获得原厂图形箭头目视复核，不伪称完成该项。

原生原理图MPN字段逐数核对：0407008.WR×1、MF-MSMF110/16X-2×4、GRM32DR71E106KA12L×6、GRM155R61C105KA12D×2、C0805C475K4PACTU×1、C0603C750J5GACTU×2、CRCW2512300RFKEG×2，均与源及BOM一致。C422标4.7u/16V且两类新KEMET器件厂商字段正确。PCB使用对应名义值/封装，不保存每件MPN属性；确切采购身份来自原理图和电子BOM，不能声称PCB中有不存在的MPN字段。

新增R500/R501均为2512、300Ω/1W，连接VM至GND，并联150Ω。电解D10/P5与D8/P3.5已由Panasonic精确产品页核实。此前不存在有效证据的10µF料号及已知旧PTC/MLCC生命周期选型尾项已按[独立BOM审查](../../electronics/sources/bom-exact-part-audit.md)闭合；两项KEMET Active来自授权渠道，不表示供应保证。LED极性图、新PTC/F1图形箭头仍保留资料复核限制。

重新计算USB与晶振七网的线长/过孔数量，逐项与上表相符；In1走线数仍为零。全部release-status原生文件哈希逐一吻合。读取正式ERC为0错误/0警告，DRC为0违规/0未连接/0封装错误，契约错误列表为空；本轮不是只凭父代理口头结果。

108个输入RLC/制动边界模型的独立数值核算见[保护边界复核](protection-analysis/independent-review.md)：模型限定≤0.05J/次、≤5Hz、5～100ms时无需TVS周期耗能，不能作为实际机器人能量已达标的证据；199.97A窄峰与低名义保险I²t比例不免除接点、MOS SOA、栅极建立及短路协调验证。持续入口预算5A、初始单臂热测试目标0.75 Arms，未通过固件自动执行。

本轮未发现替代落地导致的另一项确定性强制电气错误；既有EV3、机械、供应/实物核对与原型测试HOLD不变。BOM SHA-256：`f0c5cf2bb3d012858dbd02ae2211c91f72e71067c471840734001006346a683a`。

本报告结论为：所查A1工程连接与几何检查通过，未发现上述范围内新的确定性电气错误；**不等于制造放行或实板测试通过**。PCB或关键电气源改变后，须更新哈希和对应复核。
