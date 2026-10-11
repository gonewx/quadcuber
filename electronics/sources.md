# A0 原厂依据（2026-10-11查阅）

|器件/接口|原厂资料|本设计使用的事实/边界|
|---|---|---|
|DRV8871|https://www.ti.com/lit/ds/symlink/drv8871.pdf |SLVSCY9B：DDA引脚表、6.5–45V、IN/IN真值表、43.2k限流公式；TI DDA PowerPAD落脚图与KiCad专用封装|
|DRV8833（对比）|https://www.ti.com/lit/ds/symlink/drv8833.pdf |SLVSAR1E：PWP/RTY与PW电流不同，VM最大推荐10.8V；不用于成品BOM|
|TPS54302|https://www.ti.com/lit/ds/symlink/tps54302.pdf |SLVSDG6C：DDC/SOT23-6引脚和5V参考电路，内部补偿、负载跃变和电感/电容设计|
|LM74700-Q1|https://www.ti.com/lit/ds/symlink/lm74700-q1.pdf |DBV引脚；VCAP跨ANODE；正向供电不受EN完全切断；外部NMOS理想二极管|
|CSD18540Q5B|https://www.ti.com/lit/ds/symlink/csd18540q5b.pdf |60V、4.5V栅压下max3.3mΩ；TDSON-8-1的1/2/3源、4栅、5大漏焊盘|
|SN74LVC2G17|https://www.ti.com/lit/ds/symlink/sn74lvc2g17.pdf |DBV6，5.5V输入容限、Ioff、非反相施密特整形|
|SN74AHCT1G125|https://www.ti.com/lit/ds/symlink/sn74ahct1g125.pdf |SCLS378P：TTL VIH=2V；输入漏电在VCC=0..5.5V规定；OE_N=1、A=2、GND=3、Y=4、VCC=5|
|Pico H|https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf |21×51mm、17.78mm行距、2.54mm孔距；原板VBUS肖特基、VSYS并供方案；没有裸MCU迁移|
|EV3插座4434|https://www.adafruit.com/product/4434 ; https://cdn-shop.adafruit.com/product-files/4434/4434-ds.pdf |品牌料号4434，偏置卡扣裸母座；公开图不足以确认焊孔/编号/接点电流，保持HOLD。没有编造底层厂商MPN|
|LEGO EV3电机口|https://www.lego.com/cdn/cs/set/assets/blt86e79bb287a0d0b1/Appendix_LEGO_MINDSTORMS_EV3_programmable_brick_main_hardware_schematics.pdf |输出口1/2电机、3GND、4+5V、5/6Tacho；不混用传感器口定义|
|EV3大马达|https://education.lego.com/en-us/product-resources/mindstorms-ev3/downloads/developer-kits/ |Hardware Developer Kit §16.1：9V空载175RPM/60mA、堵转1.8A。是选型基准不是本机实测|
|灰色Geekservo|https://www.kittenbot.cc/products/kittenbot-grey-geekservo-servo |3.3–6V，标称4.8V，堵转700mA；测试电压/容差未知，仍核用户实物标签|
|SRP1245A-100M|https://www.bourns.com/docs/product-datasheets/srp1245a.pdf |10µH±20%，Irms9A、Isat16A，14.2×5mm推荐焊盘外廓、8mm间隙；KiCad L_Bourns_SRP1245A|
|MF-MSMF|https://www.bourns.com/docs/product-datasheets/mf-msmf.pdf |各支路PTC保持/动作额定及温度降额，不能作为精密电子限流|
|SMBJ系列|https://www.littelfuse.com/products/overvoltage-protection/tvs-diodes/surface-mount/smbj |SMBJ12A/CA，12V反向工作、13.3V最小击穿、19.9V额定脉冲钳位；600W波形额定不等于持续功率|
|入口保险467系列|https://www.littelfuse.com/products/fuses-overcurrent-protection/fuses/surface-mount-fuses/nano2-fuses/467 |0467008.NR，1206、8A；温度/浪涌与实际电源仍须核验|
|Pico母座|https://www.we-online.com/components/products/datasheet/61302011821.pdf |20针、2.54mm、推荐孔1.02±0.15；两条板载母座|

封装独立审查已核TI主要芯片针号及Pico几何。电阻使用Yageo具体可订购编码（如RC0603FR-0743K2L），不是把四位阻值标码错误拼接成MPN。实际可采购状态、替代品额定及来料尺寸仍以采购时官方料页和样品为准。
