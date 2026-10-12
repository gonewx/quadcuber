> 最终局部 JLC 适配后已重跑合同；PCB `b04859e7a282eb648943abfbf70d00e488a887627a74470aab24ffc20d637d44`。下文工程限制继续有效，未做实板测量。

# A1 控制器制造前复核（2026-10-12）

结论：控制器部分可进入**受控首板验证**，没有发现必须先重画控制器PCB的确定性引脚/供电/Flash错误；这不是整板投产放行。前提是锁定下述电源/USB使用限制和指定UF2。外部供电且USB连接已关机主机，不能宣称已支持；不能用“首板再测”替代这一限制。EV3、功率级和整体DFM由其他报告决定。

## 已执行的证据

`check.py`使用当前KiCad10新导出XML，并直接解析当前PCB；54颗控制器相关元件、180个接脚的源文件/生成JSON/原理图/PCB网络一致，精确MPN与BOM一致。RP2040特殊脚另以独立期望表检查。通过的结果和输入SHA256见`checks.json`。PCB SHA256仍为`aa17fa9b22cc113f423552e96b39004e5b6b77cb64c0e49f54233de939642a5a`。

实际交付UF2重新验证：1318块、全部连续地址位于2MiB窗口、RP2040 family、ROM CRC `9a195ca8`、实际指令`movs r2,#2; tst r0,r2; bne`跳至boot2偏移0x64，避开SR写路径；板级源文件哈希与既有构建记录一致。UF2 SHA256 `ce965d9bd597be5377bd1bbb1f83bb69894be7ad3f3dac80cdbe60615d143eb9`。没有重新编译或替换二进制。本环境原构建树/ELF已不存在，故没有虚称本轮全量重建或实机启动通过。

## 静态结论与量化边界

- RP2040：IOVDD 1/10/22/33/42/49、ADC_AVDD43、VREG_IN44、USB_VDD48均3V3；VREG_OUT45仅供DVDD23/50的1V1；TESTEN19、EP57接地。SWD/RESET与USB_DM46/DP47、QSPI51–56一致。十颗100nF及VREG输入/输出各1uF齐全；这证明网络与数量，不证明MLCC带偏压容量和装配品质。[RP2040原厂手册](https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf)
- USB-C：两路独立5.1k Rd，双面D+/D−合并正确，27Ω串联在MCU附近。USBLC6-2SC6的1/6=DP、3/4=DM、2=GND、5=VSYS，未误接；VSYS正常约4–5V，偏置合理，100nF本地旁路。内部导流方向是数据线向正电源轨，VSYS不会经它的上钳位二极管正向供电到数据线。它不等于VBUS反向隔离器。ST的器件ESD指标不能当整板认证。[ST原厂](https://www.st.com/resource/en/datasheet/usblc6-2.pdf)
- USB布局抽取的铜段总长（含分支，非端到端时延）：DP=15.722mm、DM=16.887mm；27Ω至MCU分别2.301/2.052mm。未建立板厂叠层/90Ω阻抗模型，因此只能放行12Mbit/s首板功能验证，不能声称USB合规眼图通过。
- D2、D5阴极均VSYS，分别防止主要电流流回5V_A/USB_FUSED；USB不应带动电机/舵机。SS14在额定反向电压的最大漏电为25°C 0.2mA、100°C 6mA（实际约5V反压通常更低，但无此工作点保证值）。VBUS到地仅R405+R406=200kΩ，24uA就足以抬升到4.8V，故悬空VBUS电压及GP24高电平不能单独证明存在主机。应测反灌电流并连接规定负载，不能只拿高阻表测电压。[Vishay原厂](https://www.vishay.com/docs/88746/ss12.pdf)
- 主机关机另有D+上拉路径：现有board仅改boot2，没有GP24门控USB补丁；上游RP2040 TinyUSB驱动明确强制VBUS存在。由于本环境缺失固定TinyUSB子模块，现阶段这是有明确上游依据的未关闭行为风险，不冒充已逐字确认本UF2相同。典型1.5k上拉向被钳至0.3V的主机可注入约(3.3−0.3)/(1500+27)=1.96mA。电源二极管无法消除此通路。[TinyUSB当前原厂驱动](https://raw.githubusercontent.com/hathach/tinyusb/master/src/portable/raspberrypi/rp2040/dcd_rp2040.c)；[MicroPython v1.27.0启动路径](https://raw.githubusercontent.com/micropython/micropython/v1.27.0/ports/rp2/main.c)。最低无硬件改动处置：首板规定USB接通时主机必须供VBUS，主机断电/睡眠撤VBUS前拔线；ROM BOOTSEL也遵守。未来完整支持需验证固定驱动、运行/复位/BOOTSEL各阶段；固件门控仅解决运行阶段，不能自动保证ROM阶段。
- Y1精确ABM8-272-T3，12MHz/CL10pF/ESR≤50Ω；两15pF形成7.5pF，寄生取2–3pF时9.5–10.5pF，1k串阻匹配原厂推荐。PCB铜段总长XIN9.020mm、XOUT4.854mm、阻后4.947mm；寄生未经提取，不能保证等于原Pico。此配置足以支持首板，无理由凭猜测改电容；验证时输出分频时钟测频，避免普通探头直接加载XIN。[Raspberry Pi硬件设计§2.3](https://datasheets.raspberrypi.com/rp2040/hardware-design-with-rp2040.pdf)
- W25Q16RVCNJQ：2.7–3.6V、16Mbit/2MiB、CN窄体SOIC8；8脚和现有封装匹配；只允许Q后缀，不允许M/1.8V/宽体随意替代。RV-Q的SR2=06h对应QE=1，交付boot2按位检查跳过写状态。ROM 03h取boot2、后续EB/A0连续读的兼容依据已在`electronics/sources/flash-selection-review.md`；本次独立确认二进制修补确实在交付UF2，而非只有源码改动。采购仍必须锁定精确料号。
- TLV75533PDBVR网络和封装正确，1uF输入、4.7uF输出。板级150mA连续上限应保留。以USB接头4.40V、PTC 1Ω和SS14 0.50V作保守室温估算，VSYS≥3.75V，较3.3V余0.45V；TI全温500mA最大压差238mV仍余约212mV。PTC1Ω须以具体温度实测复核，此非所有温度/线缆的保证。VSYS5.25V时150mA功耗约0.293W；500mA则约0.975W，不能以芯片500mA额定值放宽板级预算。禁止SWD或外部3V3反向供电。慢上升或退出dropout可能过冲，是首板波形验收项目。[TI原厂](https://www.ti.com/lit/ds/symlink/tlv755p.pdf)

## 下单前控制器范围的条件

1. 保留精确Flash/晶振/LDO/ESD MPN并向装配方提供指定UF2，禁止通用RPI_PICO镜像替代；原型不宣称USB/EMC认证。
2. 首板明确四种状态：USB独供（仅逻辑）、9V独供、双供且主机VBUS有效、全断电。外部供电+失电主机连接列为禁止的普通使用状态，只能用受保护测试夹具专项测量。
3. 原型限控制器3V3连续≤150mA；不注入外部3V3；9V电源及整板其他条件由整板复核决定。没有必须向用户新增索取的控制器参数。

## 首板后可执行验收（不是下单前必须已有的实测）

- 不连接电脑先以限流电源供电：确认3V3稳态3.20–3.40V、任何瞬态不超过3.60V；1V1按RP2040工作范围并以1.05–1.15V作板级筛选窗。检查内部电源/Flash没有错误短路。
- 四种允许供电状态及两电源插拔，各100次冷启动/复位/枚举；无启动失败或锁死。源端从最低预期电压扫到上限，记录VSYS、3V3和RUN。移除全部电源后真正降至接近0V，再算冷启动。
- 在约20–30°C和预期最高环境温度，各测0/50/150mA控制器负载、LDO温升和瞬态；在应用负载阶跃及电机/舵机活动下3V3不得越过3.0–3.6V，且无复位/USB断线。验收时不得使结温接近热关断；先用125°C以下作保守结温上限，按实际热模型修订。
- BOOTSEL枚举/UF2下载/复位，JEDEC容量身份和SR2读回，文件写入-哈希-重启读回、擦除后重写；至少100次正常断电循环。写中断电可能损坏正在写的文件，不要求不可能的原子性；要求可以通过BOOTSEL恢复并说明应用持久化恢复策略。
- 晶振用缓冲分频输出频率确认12MHz等效值和冷启动可靠性，不直接把重负载探头挂晶振端。初筛频差≤±100ppm；要求更严格USB合规时再执行规范测试。
- 专项host-off只接电流表/受保护模拟端，不先接贵重电脑：记录USB_VBUS与DP/DM反向电流、GP24状态，室温及温热条件。此测试用于决定未来修改，不能以“电流小”直接宣布通用主机安全/USB符合性。
