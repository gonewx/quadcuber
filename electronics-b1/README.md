# B1 底板（KiCad 工程）

方案和取舍见 [docs/b1-carrier-board.md](../docs/b1-carrier-board.md)。本目录是 B1 唯一的源文件目录，与 A1（`../electronics/`）完全独立，不引用 A1 的库文件。

- 2 层 FR-4，99×99mm，1.6mm，1oz。元件全部放在顶面，尽量用贴片件（0805 及以上、SOIC/SOT-223/TO-263/HSOP），自己用热风枪和烙铁手焊。只有排针、Pico 排母、DC 插座和 EV3 插座是通孔件。
- 树莓派 Pico H 插在两排 1×20 排母上，USB 朝板子上边。引脚与 `wiring/spec.py` 的 `ARMS` 一致，固件不用改。
- 四个 EV3 插座在下边，从左到右依次是 R / L / F / B。每个插座上方是该臂的舵机排针，自下而上为 G / + / S。

## 文件

| 文件 | 作用 |
|---|---|
| `circuit.py` | 元件、网络和摆放位置的唯一来源 |
| `generate.py` | 生成符号库、原理图、工程文件和未布线的 PCB。预先画好并锁定两条电源主干（VM 底层 2mm、舵机 5V 顶层 1.5mm），并给每个贴片接地脚加就近的接地过孔 |
| `route.py` | 导出 DSN（带显式线宽），用 freerouting 布线，导入 SES；填充两面地铜，再打地缝合过孔 |
| `build.py` | ERC/DRC（有错误就中止）、网表、Gerber+钻孔 ZIP、手焊 BOM、预览 SVG |
| `test_b1.py` | 不依赖 KiCad 的引脚映射回归测试：Pico 官方引脚、四臂引脚、电源路径、网表与 PCB 一致 |
| `lib/B1.pretty`、`lib/3dmodels` | 自包含的封装和 3D 模型：KiCad 标准库副本，以及 A1 已核对的 DRV8871、EV3 封装副本。3D 模型用 `${KIPRJMOD}` 引用，KiCad Lite 不装标准 3D 库也能显示 |

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
- DRC：0 错误，0 个未连通焊盘。另有 26 条警告：23 处丝印重叠（位号文字压在相邻元件上），3 处是锁定电源主干的端点悬空。都不影响制板。
- `test_b1.py` 5/5 通过。

## 下单前要核对的实物

1. **DC 插座**：封装用的是 KiCad 的 `BarrelJack_Horizontal`，后脚到前脚 6mm，侧脚偏出 4.7mm。下单前用卡尺量一下手上的 DC-005，对不上就告诉我改封装。
2. **EV3 插座**：同批的要够 4 个。

其余元件都是标准贴片封装（0805、1206、2512、SOD-123、SMA、SMB、SOIC-8、SOT-223、TO-263-5、贴片电解 6.3/8/10mm、12×12 功率电感），淘宝买对应规格即可。

## 焊接与上电

焊接顺序见 `generated/electronics-b1/bom-hand-solder.csv`：贴片 IC（热风枪）→ 0805/2512 → 二极管 → 保险丝 → 贴片电解 → 电感 → 排针排母 → 插座。

第一次上电：
1. **先不插 Pico，不接电机和舵机**，用可限流的 9V 电源，限流先设 0.3A。
2. 依次量 VM≈9V、舵机 5V（任一舵机排针的 + 脚）≈5.0V、5V_LOGIC（AMS1117 输出）≈5.0V，再量 Pico 排母第 39 脚，应约 4.6V（扣掉了 SS14 的压降）。
3. 断电，插上 Pico；再插 EV3 线，量编码器分压点，任何时候都不能超过 3.3V。
4. 接电机前，先做 EV3 插座断电六路通断检查（针序还没用实物核实）。
