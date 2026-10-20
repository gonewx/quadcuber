# B1 底板（KiCad 工程）

方案和取舍见 [docs/b1-carrier-board.md](../docs/b1-carrier-board.md)。本目录是 B1 唯一的源文件目录，与 A1（`../electronics/`）完全独立，不引用 A1 的库文件。

- 2 层 FR-4，99×99mm，1.6mm，1oz。元件全部放在顶面，尽量用贴片件（0805 及以上、SOIC/SOT-223/TO-263/HSOP），自己用热风枪和烙铁手焊。只有排针、Pico 排母、DC 插座和 EV3 插座是通孔件。
- 树莓派 Pico H 插在两排 1×20 排母上，USB 朝板子上边。引脚与 `wiring/spec.py` 的 `ARMS` 一致，固件不用改。
- 四个 EV3 插座在下边，从左到右依次是 R / L / F / B。每个插座上方是该臂的舵机排针，自下而上为 G / + / S。
- 接口丝印（2026-10-20 补）：舵机排针右侧逐针印 `G` / `+` / `S`；J2 右侧印 `GND` / `TX` / `RX`、下方印 `UART`（不是舵机口）；EV3 插座背面在第 1 针（M1）旁印 `1`。**已生产的 B1 实物没有这些丝印**（首测时舵机插反、插进过 J2），实物上用记号笔在每个舵机排针的 G 针旁点标记。

## 文件

| 文件 | 作用 |
|---|---|
| `circuit.py` | 元件、网络和摆放位置的唯一来源 |
| `silk.py`、`label_interfaces.py` | 接口丝印（数据在 `circuit.py` 的 `SILK`/`REF_MOVES`）。`generate.py` 生成时就加上；`label_interfaces.py` 给已布线的 PCB 补加，只动丝印文字，可重复运行 |
| `generate.py` | 生成符号库、原理图、工程文件和未布线的 PCB。预先画好并锁定两条电源主干（VM 底层 2mm、舵机 5V 顶层 1.5mm），并给每个贴片接地脚加就近的接地过孔 |
| `route.py` | 导出 DSN（带显式线宽），用 freerouting 布线，导入 SES；填充两面地铜，再打地缝合过孔 |
| `build.py` | ERC/DRC（有错误就中止）、网表、Gerber+钻孔 ZIP、手焊 BOM、预览 SVG |
| `test_b1.py` | 不依赖 KiCad 的引脚映射回归测试：Pico 官方引脚、四臂引脚、电源路径、网表与 PCB 一致 |
| `lib/B1.pretty`、`lib/3dmodels` | 自包含的封装和 3D 模型：KiCad 标准库副本，以及 A1 已核对的 DRV8871、EV3 封装副本。3D 模型用 `${KIPRJMOD}` 引用，KiCad Lite 不装标准 3D 库也能显示 |

## 重建

装配图导出需要 Python 包 `cairosvg`（`python3 -m pip install cairosvg`）及系统 Cairo 运行库。构建会同时生成带固定深色背景的 SVG 和 2400×2400 PNG，便于直接打开查看。

```sh
export KICAD_APP_RUN=<KiCad 10.0.7 AppImage 解包目录>/AppRun
$KICAD_APP_RUN python3.11 electronics-b1/generate.py
$KICAD_APP_RUN python3.11 electronics-b1/route.py <freerouting-2.1.0.jar> 30
$KICAD_APP_RUN python3.11 electronics-b1/label_interfaces.py   # 只改丝印时从这一步开始，不用重新布线
python3 electronics-b1/build.py
python3 -m unittest electronics-b1/test_b1.py -v
```

freerouting 2.1.0 的下载地址和 SHA256 见 `../electronics/toolchain.json`。自动布线每次的结果可能略有不同；重新布线后必须重跑 `build.py` 和测试。

## 当前检查结果（2026-10-20，补接口丝印后）

- ERC：0 错误，0 警告。
- DRC：0 错误，0 个未连通焊盘。另有 19 条警告：16 处丝印重叠（位号文字压在相邻元件上；新加的接口丝印没有重叠），3 处是锁定电源主干的端点悬空。都不影响制板。
- `test_b1.py` 6/6 通过（新增：每条接口丝印都在 PCB 上，且与对应网络的焊盘同一行）。

## 焊前要核对的实物

1. **DC 插座**：封装用的是 KiCad 的 `BarrelJack_Horizontal`，后脚到前脚 6mm，侧脚偏出 4.7mm。焊前用卡尺核对手上的 DC-005，并试插匹配电源插头核通断；对不上先排查适配。
2. **EV3 插座**：同批的要够 4 个。

3. **L1 电感**：采购记录为 TDK SLF12575T-330M3R2-PF，板上是通用封装；焊前确认实际端子与焊盘搭接，详见焊接指南。

其他贴片件也需按 BOM 核型号、封装、数值及极性，不能只按外形大小装配。

## 焊接与上电

完整步骤见 **[B1 底板焊接与首次上电指南](../docs/b1-soldering-guide.md)**，包含正面元件图、逐颗极性、分阶段焊接、测点及验收记录。用户已于 2026-10-16 确认 PCB 和零件到手，实板焊接和上电尚待记录。

实际操作直接照[焊接批次总表](../docs/b1-soldering-guide.md#soldering-batches)逐行完成：每批列出工具、耗材、全部位号和数量，可勾选检查。

本次顺序：低矮贴片件（IC、电阻/陶瓷电容、二极管/保险丝）分区点锡浆并热风焊接 → L1 热风焊接 → 烙铁焊电解 → 烙铁焊排针排母及插座。Q1 和 DRV8871 都可优先用热风，区别是 Q1 只需给八脚上浆，DRV8871 还需给中心散热焊盘上浆。CSV 中原“焊接顺序”列仅保留作类别排序，操作以指南为准。DRV8871 的底部散热焊盘必须焊接；U1 散热片接地，U2 散热片接 5V_LOGIC。

首次上电先不插 Pico、不接 USB、电机或舵机，使用限流 0.3A 的稳压 9V 电源，按指南量 VM、两路 5V 和 VSYS。EV3 六路断电通断与编码器电平检查必须在连接 Pico 输入之前完成：10kΩ/20kΩ 分压在输入 5V 时计算值为 3.33V，不能假定必然低于 3.3V，超出指南筛查条件时先处理分压，不插 Pico。
