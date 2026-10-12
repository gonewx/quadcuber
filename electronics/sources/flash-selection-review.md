# A1 Flash选型关闭记录（2026-10-12）

U7由 **W25Q16JVSNIQ** 替换为 **W25Q16RVCNJQ**（Winbond，管装，16Mbit/2MiB，CN 150mil SOP8）。这项替换已进入电气源、BOM、原理图和PCB，不再保留“量产前另选Flash”尾项。

## 生命周期及供应证据

- [Winbond Z200-PCN-DM202601-03-A及AN0000070 Rev1.2](https://www.anglia.com/registration/pcn_ptn/docs/ptn/PTNW25Q16J280126%20%282%29.pdf)：2026-01-21原厂迁移通知，表1包含原SNIQ；PDF第7页表5给出SNIQ到RVCNJQ的150mil替代映射。通知拟首次发货2026-01-30。原SNIQ的确切最后订购/交付日期未核实；不将其他封装的EOL截止日套用，也不将渠道库存等同仍在生产。
- [Winbond 2026产品指南](https://www.winbond.com/export/sites/winbond/product-selection-guide/file/2026-Product-Selection-Guide-Winbond-Code-Storage-Flash-Memory.pdf)：PDF第29页工业级W25Q16RV为P（Mass Production）。
- [Mouser确切管装料号454-W25Q16RVCNJQ](https://www.mouser.jp/en/ProductDetail/Winbond/W25Q16RVCNJQ?qs=fQuHqd5sRUjQgmLEOK%2FjDA%3D%3D)：核查时New Product、15颗现货、MOQ1、可立即发货。超出现货部分36周工厂交期。仅记录供应证据，未下单，不保证未来库存或目的地交付。
- [DigiKey确切管装料号](https://www.digikey.com/en/products/detail/winbond-electronics/W25Q16RVCNJQ/29806955)：Active、可预订、当时0现货，不能称其为现货渠道。

## 电气、封装与命令核对

依据[Winbond W25Q16RV Rev H](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/9004/256_W25Q16RV.pdf)，核对2.7–3.6V、133MHz、2MiB；CN主体3.9×4.85mm名义、最大4.0×5.0mm、1.27mm脚距、总引脚跨度5.8–6.2mm。现有SOIC-8_3.9x4.9mm_P1.27mm焊盘及庭院适配，U7位置、朝向、8针网络和所有铜不变。不能采购CS宽体或1.8V型号替代。

针1～8依次为CS、IO1、IO2、GND、IO0、CLK、IO3、VCC。0xEB连续四线读默认6个等待时钟包含2个mode时钟和4个高阻dummy；mode 0xA0满足M5:4=10；0x02页编程及0x20/0xD8擦除不变。Q后缀QE固定1。

迁移指南指出RV的SR2默认06h，旧JV-Q为02h；01h的第二数据字节不再写SR2。因此不能笼统宣称旧启动代码完全等同兼容。

## MicroPython适配和验证边界

[MicroPython v1.27.0](https://github.com/micropython/micropython/tree/v1.27.0/ports/rp2/boards/RPI_PICO)提交78ff170de9e32c79db6e64d3e33d2bd60002bdcd，其pico-sdk子模块固定为9a4113fbbae65ee82d8cd6537963bc3d3b14bcca。

该SDK的[pico.h](https://github.com/raspberrypi/pico-sdk/blob/9a4113fbbae65ee82d8cd6537963bc3d3b14bcca/src/boards/include/boards/pico.h)选择W25Q080 boot2、2MiB及SPI分频2。[boot2源码](https://github.com/raspberrypi/pico-sdk/blob/9a4113fbbae65ee82d8cd6537963bc3d3b14bcca/src/rp2040/boot_stage2/boot2_w25q080.S)原来比较整个SR2是否等于02h；RV的06h会进入01h状态写路径，SDK在Flash写后也会再次调用boot2。本工程将两条指令改为只测试QE位（tst/bne），06h与02h均直接跳过状态写，避免无必要的非易失寄存器磨损和延迟。

外部board配置仍使用PICO_BOARD=pico、rp2040和原RPI_PICO的1408KiB文件系统配置，只替换boot2并改显示名称。QSPI初始03h ROM读取、USB BOOTSEL、GPIO/PIO、Python程序接口不变。构建方法及二进制证据见[固件说明](../firmware/README.md)。必须使用本工程QUADCUBER_A1构建，不将官方未修改RPI_PICO UF2宣称为已适配版本，也不接受M后缀替代。

编译、反汇编及EDA通过只能确认静态设计和构建；未烧录硬件，首次UF2启动、读写与断电恢复仍需首板测试。
