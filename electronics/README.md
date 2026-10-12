# 四臂集成单板控制器 A1（板载RP2040） — 工程评审，未制造放行

本目录是唯一电子源目录。打开 `quadcuber.kicad_pro`，包含原生可编辑原理图和四层 PCB、本地符号/封装库。本设计为**单块PCB，RP2040、QSPI Flash、晶振、USB-C、驱动和电源均直接焊接在板上**；A0的Pico H插装已移除。马达使用EV3裸插座。接线定义仍从 `../wiring/spec.py` 导入，固件未改动，也没有把 R/L 固件描述成已支持四臂控制。

**不得把当前 Gerber 下单。** `EV3_UserDrawing_PINMAP_HOLD` 已采用用户上传尺寸图：六个Ø0.79信号孔、1.02横向投影节距、2.54排距、两个Ø2.3定位孔及12 mm孔距；旧占位孔位已移除。详见[图纸及独立尺寸审查](sources/ev3-user-drawing-review.md)。图只有最右上孔明确标为6，其余1～5和元件面视向暂按相关视图推定。实际可采购料号、与图纸的对应关系、接点电流及固定耳完整外廓仍待核验，不能把本图认定为Adafruit4434，也不能用普通RJ12或DEC反向偏扣插座替代。ERC/DRC不能解除这些制造HOLD。

## 交付入口

- [KiCad工程](quadcuber.kicad_pro)、[原理图PDF](../generated/electronics/schematic.pdf)
- [正面板图](../generated/electronics/pcb-top.png)、[反面铜图（顶视透视）](../generated/electronics/pcb-bottom.png)、[正面装配图](../generated/electronics/assembly.png)、[反面装配图（顶视透视）](../generated/electronics/assembly-bottom.png)
- [汇总电子BOM](../generated/electronics/bom-grouped.csv)、[逐件BOM](../generated/electronics/bom.csv)、[贴装坐标](../generated/electronics/positions.csv)
- [ERC](../generated/electronics/erc.rpt)、[DRC](../generated/electronics/drc.rpt)、[状态与源哈希](../generated/electronics/release-status.json)、[独立复核](../generated/electronics/independent-review.md)
- [仅供检查的Gerber/钻孔](../generated/electronics/fabrication-preview-NOT-RELEASED/DO_NOT_FABRICATE.txt)，不具备下单放行状态。

正反面SVG/PNG沿同一KiCad顶视坐标系绘制，便于对照；实际从板底观察时需镜像，不可用透视图推断插座针序。

TP测试焊盘和安装孔是PCB内建特征，采购数量记为0；可选电容的DNP原因单独列在BOM备注中。

## 电源仿真状态

已完成[65个ngspice边界工况及热敏感性计算](simulation/README.md)，结果见[报告](../generated/electronics/simulation/report.md)。它们使用明确标注的简化模型；TPS54302原厂模型下载遇HTTP403，实际原厂模型运行次数仍为0。不能据此宣称降压环路或PCB通过验证，制造HOLD保持。

## 架构与器件

- **控制器：裸RP2040 QFN56+EP**。保留GPIO0～21、8个PIO状态机、12MHz时钟、2MiB Flash以及GP25指示灯，使用基于RPI_PICO的QUADCUBER_A1 MicroPython UF2，无需迁移MCU平台。GP22/23/26～29未用；GP24为USB VBUS分压检测。ROM BOOTSEL、RUN复位、UART和SWD均直接引出；SWD口3V3为参考电压，禁止外部注入供电。
- **Flash：W25Q16RVCNJQ**，CN 150mil SOP8，原厂在产替代，保留3.9mm窄体焊盘。使用[QUADCUBER_A1启动配置](firmware/README.md)，在现有MicroPython/Pico启动代码上修正QE位判断，避免RV状态寄存器差异造成反复写入；仍通过USB UF2烧录。选型、供货及逐命令兼容证据见[Flash复核](sources/flash-selection-review.md)。
- **12MHz ABM8-272-T3**，CL10pF、两颗15pF、XOUT串1k；RP2040每个电源脚配置100nF，内部稳压输入/输出各1µF。3.3V接IOVDD/ADC_AVDD/VREG_IN/USB_VDD；VREG_OUT仅接1.1V DVDD，TESTEN及EP接地。
- **USB4105-GF-A** USB-C USB2从设备，CC1/CC2各独立5.1k，下游数据通过USBLC6-2SC6和27Ω串阻。GCT原厂图与库的定位孔、壳脚槽和针序逐项核对；没有USB PD，也不向主机提供VBUS。

- **四路 DRV8871DDAR**，每马达一颗，HTSOP-8 PowerPAD，热焊盘接地、有原厂推荐热孔。IN1/IN2 真值表与现有慢衰减 PWM 一致，00滑行/休眠、01反转、10正转、11刹车。现有20 kHz PWM符合器件范围；休眠后首次唤醒最多50 µs，样机须重测低速定位。不沿用 DRV8833 名义模块电流：DRV8833 PWP/RTY 每桥1.5 A RMS，而PW只有0.5 A，且10.8 V推荐上限不利于9 V母线回灌。DRV8871的6.5～45 V供电裕量更合适，**3.6 A只是峰值，不是整板持续额定**。
- 每桥 **43.2 kΩ ±1%**，64 kV/R 名义1.481 A；按59～69 kV及电阻容差推算1.352～1.613 A。该门限不是所有PWM/电感工况下的精密峰值保证。9 V EV3大马达原厂堵转1.8 A，因此设计有意限流降低堵转扭矩，带载夹持须验证。
- **两路 TPS54302DDCR**，5 V基准电路，R上100k/下13.3k、10µH电感、双22µF/25V输出及75pF前馈（C26/C36可选470µF默认DNP，须验证环路后才装）。每路带两个舵机，A路还带编码器与RP2040。电感 **SRP1245A-100M** 为10µH、9 A RMS、16 A饱和额定，避免饱和电流低于控制器6 A故障限流上界。芯片3 A额定不等于封闭机箱持续3 A；设计负载预算见下。
- **八路 SN74LVC2G17 施密特整形**：每输入1k串联、100k下拉，5 V容限、3.3 V供电。替代旧10k/20k分压，避免5 V边缘直接到RP2040；不反相、保持`ENC_PULLUP=False`，PIO资源不变。器件Ioff保证断电输出不会把编码器5 V送入3.3V供电。马达pin4由独立0.5 A PTC保护的5V_ENC供电。
- 舵机每路1.1 A PTC、**SN74AHCT1G125**（由该路PTC后供电）、220Ω输出串阻、GPIO及输出下拉。3.3 V输入符合TTL阈值；原厂输入漏电在VCC=0时也有规格，避免USB-only的高GPIO经舵机信号反向供电。此处不声称输出端可任意外灌电压；不接外部5 V到舵机端口。

## 电源、回灌与默认态

J1只接**稳压9 V ±2%直流电源**，设计以约6 A正常持续输入、8 A入口保险为边界。不能接12 V，也不能接未评估的3串锂电。外部电源应有限流功能，动力断开应通过入口物理开关/拔电；USB仅用于逻辑和烧录，不能带动电机、舵机。

入口为8 A熔断器、LM74700QDBVRQ1+CSD18540Q5B理想二极管。MOS源极接VIN_FUSED、漏极及大焊盘接VM；LM74700的VCAP电容跨VCAP和ANODE，不能误接到地。保护反极性、阻止VM倒流到电源，避免串联肖特基8 A时约4.26 W的发热。**EN不是正向断电开关**，体二极管仍可供电；该电路也没有浪涌限流。

输入SMBJ12CA吸收正负瞬态，输出SMBJ12A吸收回灌脉冲。输出TVS的12 V是反向工作电压，不是钳位电压；额定脉冲钳位19.9 V，相对于驱动45 V、降压28 V和VM电容25 V有裕量，但必须实测布线寄生尖峰。TVS不适合持续消耗制动功率，也不保护电机不受任何过压：只允许9 V供电，禁止持续外力反拖。控制应以慢衰减刹车优先，回灌测试必须观察VM、电机端、电源端与TVS温升。

母线六只470µF/25 V共2820µF，储能9→12 V约0.0888 J，9→13.3 V约0.135 J；它不是四马达机械动能的保证。首次上电和热插拔也要核验电容浪涌与保险I²t。没有把旧R空载实测当作这块新驱动板的试验结果。

5V_A经D2（SS14），USB VBUS经F3（0.5A PTC）和D5（SS14），分别单向汇入VSYS，再由TLV75533PDBVR产生3.3V。两路源的阳极独立、阴极均接VSYS，外部5V不能直接进入USB VBUS。USBLC6的上保护轨接VSYS、就近100nF，避免外供电时DP上拉经ESD导向二极管绕过D5回灌VBUS。所有GND共地，USB地不承担动力回流。

GP24的100k/100k分压用于遥测。Stock TinyUSB通常强制认为VBUS存在，分压本身不会关闭USB上拉；断电主机的数据脚输入保护路径尚须验证，因此不声称通过USB规范或零微安回流认证。首板须分别测VBUS及DP/DM对断电主机的电压/电流。USB仅给逻辑供电，F3不构成USB枚举电流协商。

TLV755的500mA是芯片额定，本板逻辑3.3V连续预算≤150mA。DBV封装按TI给出的231.1°C/W估算：VSYS约4.7V、150mA时0.21W、约49°C温升，40°C环境约89°C结温；这只是估算，首板必须测满负载与最高环境温度，不能套用其他封装的热阻。

输入下拉令RP2040未启动/复位时电机00、舵机无脉冲。供电瞬态下舵机内部仍可能抖动，PTC不会瞬时切断精确电流，驱动自动热恢复也不是锁存式急停。固件原有未标定锁定保持不变。

## 负载与热边界

四电机同时到名义限流约5.92 A；四只灰色270°Geekservo原厂标称堵转各700mA，总2.8 A@5 V（原厂没有给测试电压和容差，不是保证上限）。另按逻辑/编码器0.25 A@5 V、降压效率85%估算，输入约7.91 A，已经接近8 A保险，**不允许把全堵转当持续工作模式**。设计正常工况预算：马达各≤1 A持续、两个5 V支路各≤1.5 A持续（A路包含逻辑预算），合计9 V输入约5.96 A；短时峰值和温升须实测。PTC1.1 A是25°C保持电流，热环境下降额，不能用它来承诺舵机启动上限。

DRV8871在1 A时以0.565Ω典型桥阻估算0.565 W；升温后桥阻上升，1.48 A时仅导通损耗即约1.24 W。TI 41.1 K/W是规定测试板结果，不能直接当本板热阻。每颗留独立散热区域，热焊盘/热孔/地铜必须焊接完整；环境40°C下目标结温<125°C，需同时四路负载热测确认。若达不到，应降连续电流/占空比或增加散热，不能提高限流电阻之外的额定宣传。

入口J1→F1→Q1源极设宽铜区，Q1漏极以12颗Ø0.4 mm过孔连接VM内平面。DRV每颗6个原封装热孔接地，VM及PGND增加并联过孔；上下层地铜与内层地面共同散热。实际铜区需结合样机温升核验，不把理想走线公式当额定。两颗主输入10µF置于降压芯片背面近旁，以0.8 mm短线接邻近VIN/GND孔，最长1.956 mm；记录见`buck-loop.json`。

## 板形、装配与机械安装

144×112 mm矩形，四个Ø3.2 NPTH孔，坐标(4,4)、(140,4)、(4,108)、(140,108)，孔距136×104 mm均为8 mm网格。四个34 mm臂单元（J10为避开左安装孔额外右移1 mm）容纳12.2×15 mm插座主体和至少15.3 mm固定耳预留宽度、直插线缆、舵机排针、驱动散热区；上部为USB-C及板载RP2040最小系统、两套降压和电源入口。小于这一宽度会挤占接口及功率单元余量，因此没有沿用洞洞板尺寸。

它不是直接卡入现有乐高销孔的板。通过**新增绝缘托架**底挂，主要元件面朝下，反面（含C20/C30输入电容、RP2040去耦及USB供电二极管）基板表面置于模型Y=124 mm；X/Z以机器人中心为板中心。LDraw Y朝下，模型全机最大Y=116 mm；独立审查扫描臂0..355°每5°及开/合两端、支承0/20.4/40.8 mm，下方8 mm空隙成立。**这只证明裸基板与模型分离，不证明托架、反面电容、紧固件、线缆或公差完成安装验证**。

**双面装配**：C20/C30、RP2040去耦和USB供电D5等位于B.Cu；反面朝机器人，必须从8 mm净距中扣除反面最高器件的实际最大高度、焊脚及装配公差，不能把8 mm称为器件净空。最终双面装配以`positions.csv`的Side列及反面装配图为准。

需新增足够高度的脚及底部防护，按最高电容、双面器件高度、焊脚剪切和至少5 mm防护空隙确定，初始为板上方8 mm、板下约25 mm及防护的40 mm级抬高预算。托架机械设计未冻结，因此不能声称机械集成已完成。USB一侧留至少15 mm插拔空间，马达口外预留25 mm直出区再弯线，按实际线材弯曲半径调整；不将未确认的线长写成BOM事实。舵机口丝印G/+ /S，**棕/黑GND，中间红+5 V，信号S**；排针本身无防呆，插前按实际线序确认。

## 重建与编辑

已安装/使用KiCad 9.0.2、系统Python3的pcbnew；外部布线工具从[Freerouting官方v2.1.0发布](https://github.com/freerouting/freerouting/releases/tag/v2.1.0)下载。无需购买模块、运行云端EDA或迁移固件。

```sh
# 如环境HOME只读，可把XDG配置/缓存指向可写临时目录（build.py已自动处理）。
export XDG_CONFIG_HOME=/tmp/quadcuber-kicad/config
export XDG_CACHE_HOME=/tmp/quadcuber-kicad/cache
export XDG_DATA_HOME=/tmp/quadcuber-kicad/data
# 正常编辑：直接用KiCad编辑原理图/PCB，再导出验证。
/usr/bin/python3 electronics/build.py
/usr/bin/python3 electronics/check.py
python tools/build_distribution.py
python -m unittest tests.test_wiring tests.test_arm_selection tests.test_firmware tests.test_repository_layout -q

# 仅重建原理图/BOM，不动已布线PCB：
/usr/bin/python3 electronics/generate.py --metadata-only
# 从零研究布局才运行以下命令；它会覆盖已布线PCB，并不重现最终走线。
/usr/bin/python3 electronics/generate.py
```

`build.py`使用现存KiCad源，不会重置布局。标准输出唯一位于`generated/electronics/`：BOM、网表、SVG/PDF原理图、板图、ERC/DRC、制造预览文件、审查状态。`generate.py`与`circuit.json`中的坐标是初始布局，最终位置和双面装配以native PCB及其导出的`positions.csv`为准。自动布线结果可能不同，控制器由update_controller.py重新放置背面去耦并建立In2局部3V3岛；其操作会删除该区域走线，不能当普通导出步骤。控制器细间距扇出、去耦朝向和局部地回流已在native PCB中进一步修正；辅助布局脚本仅用于重新研究布局。In1始终保留完整地参考，In2只在控制器局部允许少量信号与1.1V出线，VM功率区不作信号通道。后处理脚本含历史A0特定废线清理；重新布线后必须重新审查并修正，而不是保证一键得到相同铜形。只有native PCB是最终布线事实；`generate.py`保存可重做初始布局的方法，不承诺重现自动布线每个拐点。

## 实际验证记录

本次正式导出：ERC 0错误/0警告；包含原理图一致性检查的DRC 0违规、0未连接、0封装错误；539个已连接符号引脚与PCB的网络契约核对为0错误。报告和源哈希见交付入口。独立审查已复核电源铜路、热孔和双面输入电容，记录在`generated/electronics/independent-review.md`，绑定PCB哈希。既有接线/R-L选择/固件51项测试通过。按仓库命令`python tools/build_distribution.py`补建分发产物后，相关51项与仓库布局8项合计**59项全部通过**，没有修改测试断言；这不等同四臂软件或PCB实物通过。

## 放行清单

1. **EV3料号、针号/视向与接点额定**：孔位已按用户图落实；核对实物接点到焊尾的1～6通断及观察面，确认实际型号、触点电流、成品孔配合和固定耳完整外廓。如映射改变，更新封装网络并重跑ERC/DRC。
2. **电源/热原型**：9 V台式电源限流，从无马达到单路负载再四路，测5 V启动、负载跃变、编码器波形和20 kHz电机电流；禁长时堵转。验证TVS能量、VM瞬态、铜温、驱动结温估算、输入保险及PTC降额。
3. **控制器与USB组合**：首次按住BOOTSEL插USB，确认ROM盘枚举及QUADCUBER_A1 UF2刷写；RUN复位、SWD读写、12MHz时钟、1.1/3.3V启动、QSPI读写及编码器/舵机默认态。USB-only、9V-only、两者同时、动力掉电/恢复，确认无反向供电、复位失控或异常舵机脉冲。
4. **机械**：托架与脚、USB/马达插拔、线缆运动包络、反面绝缘、安装螺钉不触铜、USB插头与BOOTSEL/RUN按键可达性。
5. **制造**：板厂确认4层1.6 mm，外铜2 oz/内铜1 oz，RP2040细间距和USB差分阻抗需板厂复核，逻辑最小0.15 mm线宽/间距（其余网络0.20 mm），USB连接器原厂孔到焊盘间隙按专用0.18 mm规则，最小0.30 mm成品孔；驱动热孔工艺和锡膏分窗按TI，检查焊孔与排针实际料样。当前没有做过PCB实物测试。

## 资料与许可证

详细依据见 `sources.md`。本地拷贝KiCad标准封装来自本环境KiCad9库，遵守[KiCad Libraries License](https://www.kicad.org/libraries/license/)的CC-BY-SA4.0及PCB设计例外；RP2040封装保留原厂焊盘并将EP热孔改为Ø0.30/焊盘Ø0.60 mm，以匹配板厂工艺；EV3自建封装明确标注未核部分。不把公开资料的缺失字段编造成制造商规格。

工程评审附件由`python electronics/package_review.py`生成到被忽略的`output/electronics/`，含原生工程、BOM、说明、报告与明确标注不可制造的Gerber预览；同时输出两张独立PNG及SHA-256清单。包内manifest绑定当前完整Git提交。
