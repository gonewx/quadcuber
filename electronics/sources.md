# A1 原厂依据（2026-10-12复核）

|器件/接口|原厂资料|本设计使用的事实/边界|
|---|---|---|
|DRV8871|https://www.ti.com/lit/ds/symlink/drv8871.pdf |SLVSCY9B：DDA引脚表、6.5–45V、IN/IN真值表、43.2k限流公式；TI DDA PowerPAD落脚图与KiCad专用封装|
|DRV8833（对比）|https://www.ti.com/lit/ds/symlink/drv8833.pdf |SLVSAR1E：PWP/RTY与PW电流不同，VM最大推荐10.8V；不用于成品BOM|
|TPS54302|https://www.ti.com/lit/ds/symlink/tps54302.pdf |SLVSDG6C：DDC/SOT23-6引脚和5V参考电路，内部补偿、负载跃变和电感/电容设计|
|LM74700-Q1|https://www.ti.com/lit/ds/symlink/lm74700-q1.pdf |DBV引脚；VCAP跨ANODE；正向供电不受EN完全切断；外部NMOS理想二极管|
|CSD18540Q5B|https://www.ti.com/lit/ds/symlink/csd18540q5b.pdf |60V、4.5V栅压下max3.3mΩ；TDSON-8-1的1/2/3源、4栅、5大漏焊盘|
|SN74LVC2G17|https://www.ti.com/lit/ds/symlink/sn74lvc2g17.pdf |DBV6，5.5V输入容限、Ioff、非反相施密特整形|
|SN74AHCT1G125|https://www.ti.com/lit/ds/symlink/sn74ahct1g125.pdf |SCLS378P：TTL VIH=2V；输入漏电在VCC=0..5.5V规定；OE_N=1、A=2、GND=3、Y=4、VCC=5|
|早期EV3候选4434（未选定）|https://www.adafruit.com/product/4434 ; https://cdn-shop.adafruit.com/product-files/4434/4434-ds.pdf |历史候选，仅确认偏置卡扣；没有证据证明与用户新图同型号，不用于新封装尺寸或BOM型号确认|
|LEGO EV3电机口|https://www.lego.com/cdn/cs/set/assets/blt86e79bb287a0d0b1/Appendix_LEGO_MINDSTORMS_EV3_programmable_brick_main_hardware_schematics.pdf |输出口1/2电机、3GND、4+5V、5/6Tacho；不混用传感器口定义|
|EV3大马达|https://education.lego.com/en-us/product-resources/mindstorms-ev3/downloads/developer-kits/ |Hardware Developer Kit §16.1：9V空载175RPM/60mA、堵转1.8A。是选型基准不是本机实测|
|灰色Geekservo|https://www.kittenbot.cc/products/kittenbot-grey-geekservo-servo |3.3–6V，标称4.8V，堵转700mA；测试电压/容差未知，仍核用户实物标签|
|SRP1245A-100M|https://www.bourns.com/docs/product-datasheets/srp1245a.pdf |10µH±20%，Irms9A、Isat16A，14.2×5mm推荐焊盘外廓、8mm间隙；KiCad L_Bourns_SRP1245A|
|MF-MSMF|https://www.bourns.com/docs/product-datasheets/mf-msmf.pdf |各支路PTC保持/动作额定及温度降额，不能作为精密电子限流|
|SMBJ系列|https://www.littelfuse.com/products/overvoltage-protection/tvs-diodes/surface-mount/smbj |SMBJ12A/CA，12V反向工作、13.3V最小击穿、19.9V额定脉冲钳位；600W波形额定不等于持续功率|
|入口保险467系列|https://www.littelfuse.com/products/fuses-overcurrent-protection/fuses/surface-mount-fuses/nano2-fuses/467 |0467008.NR，1206、8A；温度/浪涌与实际电源仍须核验|

封装独立审查已核TI主要芯片针号及RP2040/GCT USB封装。电阻使用Yageo具体可订购编码（如RC0603FR-0743K2L），不是把四位阻值标码错误拼接成MPN。实际可采购状态、替代品额定及来料尺寸仍以采购时官方料页和样品为准。

## A1 板载控制器原厂资料

|器件/约束|原厂资料（部分由授权分销商托管原厂PDF）|核对内容|
|---|---|---|
|RP2040|https://pip.raspberrypi.com/documents/RP-008371-DS-rp2040-datasheet.pdf |QFN56+EP57；各供电组、TESTEN、USB、QSPI、晶振、SWD真实引脚|
|最小系统参考|https://pip.raspberrypi.com/documents/RP-008279-DS-hardware-design-with-rp2040.pdf |每电源100n、LDO输入/输出1u；12MHz ABM8-272-T3/15p/1k；USB27Ω、90Ω差分目标|
|Flash|https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/9004/256_W25Q16RV.pdf |Winbond RV Rev H，CN 150mil，W25Q16RVCNJQ；选型/生命周期/命令差异见 sources/flash-selection-review.md|
|Pico boot2|https://raw.githubusercontent.com/raspberrypi/pico-sdk/9a4113fbbae65ee82d8cd6537963bc3d3b14bcca/src/rp2040/boot_stage2/boot2_w25q080.S |固定MicroPython v1.27.0的SDK来源；RV的QE位判断补丁见firmware/，未实板测试|
|3V3 LDO|https://www.ti.com/lit/ds/symlink/tlv755p.pdf |TLV75533PDBVR的DBV脚位、输入范围、输出电容及231.1°C/W热阻|
|USB-C|https://www.mouser.com/catalog/specsheets/Global_Connector_Technology_usb4105.pdf |GCT原厂B3图：NPTHØ0.65/横距5.78；壳槽横距8.64/前后距4.18；槽0.6×1.7及0.6×1.4；细脚0.5pitch。与KiCad封装一致|
|USB ESD|https://www.st.com/resource/en/datasheet/usblc6-2.pdf |IO1=1/6，IO2=3/4，GND2，上轨5；内部上导向二极管要求外供电时避免连接原始USB VBUS|

原厂库QFN热孔由Ø0.20改Ø0.30 mm、焊盘Ø0.60，EP和外围焊盘未缩改；需要板厂确认热孔塞/盖与锡膏工艺。USB4105定位NPTH到自身焊盘实际0.1944mm，小于默认0.25mm孔铜间距；仅此器件按原厂图设0.18mm规则，未全局豁免。

## 用户EV3尺寸图

[原图](sources/ev3-connector-user-drawing.png)与[独立审查](sources/ev3-user-drawing-review.md)记录来源、SHA-256、孔位和观察面解释。封装已落实图示名义几何，原厂身份/型号、电气针号和载流不由该图自动证明。
