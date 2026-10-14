# 装配分工、料号和旋转审核

每块板171个装配位号：厂商152个纯SMT位号+J5混合连接器=153；用户18个通孔位号。这个结果来自逐封装焊盘类型和明确的J5例外，不是按“有孔就自焊”或硬切数量：QFN/DRV的散热孔不是器件引脚，也不改变其SMT分工。

## 提交厂商

- `assembly/jlc-smt-bom.csv`：分组BOM，含Comment、Designator、Footprint、精确MPN、Manufacturer、每板Quantity及LCSC Part #。
- `assembly/jlc-smt-cpl.csv`：153行，138 Top、15 Bottom；单位mm，Mid X=KiCad PosX，Mid Y=KiCad导出PosY（即原生板Y取负）；Rotation仅将原角度规范到0–360，没有擅自旋转或镜像底面。
- `assembly/part-matching.csv`：每个制造商MPN的目录核查及下单状态；空白LCSC编号就是未核，不是任意替换许可。已核目录号也不保证库存或嘉立创当前可贴。
- `assembly/process-by-reference.csv`：每个装配位号的焊盘工艺证据与责任方。
- `assembly/polarity-padmap.csv`：所有装配件的原生pad编号、网络、正面统一坐标及面别，用于与厂家预览逐项比对。制造商卷带零度不能仅由该表推断。

## 需要重点逐项比对

|器件|板上定义/审核动作|
|---|---|
|U1 RP2040|核pin1标记与实际料库，EP57接GND；不接受Pico模块或未核兼容芯片|
|U7 W25Q16RVCNJQ|CN窄SOIC8、3V、Q后缀，2MiB；不允许JV/M/1.8V/宽体随意替代。使用指定QUADCUBER_A1 UF2，不能拿通用Pico镜像代替|
|U2/U3 TPS54302DDCR|核6脚方向与BOOT/SW引脚；C22/C32是100n直接跨BOOT–SW；不装旧R20/R30|
|U4/Q1/DRV/LDO/逻辑IC|按`polarity-padmap.csv`逐引脚核pin1、G/D/S和EP；散热孔不可误判为手焊件|
|D2/D5|pad1阴极=VSYS，pad2分别为5V_A/USB_FUSED；D5在底面|
|D3 SMBJ12A|pad1阴极=VM、pad2=GND；D4 SMBJ12CA双向无极性但不得与D3换料|
|D7 LED|pad1阴极=GND，pad2=LED_ANODE|
|J5 USB4105-GF-A|连接器开口朝板顶边；SMT数据/电源脚由厂商回流，4个PTH屏蔽脚也由厂商确认并完成补焊；非用户手焊项|
|Y1 ABM8-272-T3|精确12MHz/CL10pF；2/4接地，1/3晶振路径；不能只按3225外形替代|
|F10–13|必须MF-MSMF110/16X-2，不是MSMF050；3D显示块不提供料号替代依据|

## 用户自行焊接（18件）

1个RASPC722X DC口；4个现有图对应的EV3口；7个排针J2/J3/J4/J20–J23；6个EEU-FR1E471电解C2/C3/C102/C122/C142/C162。见独立`hand-solder-purchase.csv`，全部数量按每块板计。电解长脚/壳体负极带与板上pad1正、pad2负逐一核对。DC项目pad1中心正9V、pad2 sleeve GND、pad3 shunt不接；不得把厂家接点编号与项目编号混淆。

EV3没有精确采购MPN：使用用户已有图/同批供货件，不换普通RJ12。已接受名义孔位与主体适配的首板风险；不再索取不存在的完整厂家图号。在接电机之前，完成同批样品六路断电通断、焊尾和定位孔试配。四个接口项目脚1=M1、2=M2、3=GND、4=5V_ENC、5/6编码器。不得带电猜针序。

C26/C36明确DNP，TP*和H*为裸焊盘/安装孔，不是漏件；支脚/螺丝和插头线缆不计入171位号。自焊清单之外还需5.5/2.1中心正匹配插头/线材（官方配762/762Z、筒长9.5mm）、9V可限流电源及绝缘台架，按实际样品准备。

## 原始资料核查，不冒充实时备料

2026-10-14目录核到TPS54302DDCR=C311983、USB4105-GF-A=C3020560；链接在part-matching.csv。网页目录信息不等于当前工厂库存。USB条目存在库存/规格摘要限制，须核完整原厂图和实际可供后缀。W25Q16RVCNJQ原厂页面存在，但本轮没有确认嘉立创对应编号，不填写猜测值。其余未核项保留精确MPN，请订单BOM匹配时确认现货/代购/寄料，替代必须先评审。

格式依据：[JLC BOM](https://jlcpcb.com/help/article/bill-of-materials-for-pcb-assembly)、[JLC CPL](https://jlcpcb.com/help/article/pick-place-file-for-pcb-assembly)。导入成功不是旋转、工艺、料号审核通过。
