# B1 底板（KiCad 工程）

方案和取舍见 [docs/b1-carrier-board.md](../docs/b1-carrier-board.md)。本目录是 B1 唯一的源文件目录，与 A1（`../electronics/`）完全独立，不引用 A1 的库文件。

- 2 层 FR-4，99×99mm，1.6mm，1oz。全部通孔件手焊，只有 4 颗 DRV8871 是贴片（用热风枪焊）。
- 树莓派 Pico H 插在两排 1×20 排母上，USB 朝板子上边。引脚与 `wiring/spec.py` 的 `ARMS` 一致，固件不用改。
- 四个 EV3 插座在下边，从左到右依次是 R / L / F / B。每个插座上方是该臂的舵机排针，自下而上为 G / + / S。

## 文件

| 文件 | 作用 |
|---|---|
| `circuit.py` | 元件、网络和摆放位置的唯一来源 |
| `generate.py` | 生成符号库、原理图、工程文件和未布线的 PCB；预先画好并锁定两条电源主干：VM（底层 2mm）、舵机 5V（顶层 1.5mm） |
| `route.py` | 导出 DSN（带显式线宽），用 freerouting 布线，导入 SES，再填充两面地铜 |
| `build.py` | ERC/DRC（有错误就中止）、网表、Gerber+钻孔 ZIP、手焊 BOM、预览 SVG |
| `test_b1.py` | 不依赖 KiCad 的引脚映射回归测试：Pico 官方引脚、四臂引脚、电源路径、网表与 PCB 一致 |
| `lib/B1.pretty` | 自包含封装：KiCad 标准库副本；A1 已核对的 DRV8871 和 EV3 封装副本；自建的 PTC 封装 |

## 重建

```sh
export KICAD_APP_RUN=<KiCad 10.0.7 AppImage 解包目录>/AppRun
$KICAD_APP_RUN python3.11 electronics-b1/generate.py
$KICAD_APP_RUN python3.11 electronics-b1/route.py <freerouting-2.1.0.jar> 30
python3 electronics-b1/build.py
python3 -m unittest electronics-b1/test_b1.py -v
```

freerouting 2.1.0 的下载地址和 SHA256 见 `../electronics/toolchain.json`。自动布线每次的结果可能略有不同；重新布线后必须重跑 `build.py` 和测试。

## 当前检查结果（2026-10-14）

- ERC：0 错误，0 警告。
- DRC：0 错误，0 个未连通焊盘。另有 34 条警告：32 处丝印重叠（位号文字压在相邻元件上），2 处是锁定电源主干的端点悬空。都不影响制板。
- `test_b1.py` 4/4 通过。

## 下单前要核对的实物

1. **DC 插座**：封装用的是 KiCad 的 `BarrelJack_Horizontal`，孔距为后脚到前脚 6mm、侧脚偏 4.7mm。下单前用卡尺量一下手上 DC-005 的引脚，对不上就告诉我改封装。
2. **LM2596T-5.0**：用的是 TO-220-5 错排引脚（单排 1.7mm 间距，前后两排相距 3.7mm）的立式封装。买的时候确认是 T 型（直插、错排）。
3. **自恢复保险丝**：按引脚间距 5.1mm 画的，RXEF500 一类都是这个间距。
4. **33µH 电感**：按直径 10mm、引脚间距 5mm 的工字电感画的。

## 焊接与上电

焊接顺序见 `generated/electronics-b1/bom-hand-solder.csv`：DRV8871 → 电阻 → 二极管 → 瓷片电容 → 排针排母 → 保险丝 → 电解电容 → TO-220 → 电感 → 插座。

第一次上电：
1. **先不插 Pico，不接电机和舵机**，用可限流的 9V 电源，限流先设 0.3A。
2. 依次量 VM≈9V、舵机 5V（任一舵机排针的 + 脚）≈5.0V、5V_LOGIC（7805 输出）≈5.0V，再量 Pico 排母第 39 脚，应约 4.7V（扣掉了 1N5819 的压降）。
3. 断电，插上 Pico；再插 EV3 线，量编码器分压点，任何时候都不能超过 3.3V。
4. 接电机前，先做 EV3 插座断电六路通断检查（针序还没用实物核实）。
