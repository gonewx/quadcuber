# Quadcuber A1 唯一工程首板送厂包

设计基线 `3cfff7c8cb5a1b523186130fa96828cea1cd69d7`，J1 为 **Switchcraft RASPC722X DC5521**。本入口取代以下全部内容：旧 Phoenix、ENG-FULL、ENG-POWER-CONTROLLER 各变体，以及上一版 `db20b98` 包。不得从旧目录拼接 BOM、钻孔或 Gerber。

与 `db20b98` 相比，本包只改了正面两行丝印：
- `ENGINEERING HOLD` 改为 `PROTOTYPE`；
- `EV3 PINMAP/CURRENT UNVERIFIED - DO NOT FABRICATE` 改为 `VERIFY EV3 PINMAP BEFORE MOTOR USE`。

电路、铜、孔和布线没有变化，其余 Gerber 层只有时间戳不同。这是受控的工程首板 CAM 候选包，不代表工厂已接受、料已备齐或实板合格。

## 下载及使用

完整交付件是 [quadcuber-A1-first-board-3cfff7c.zip](quadcuber-A1-first-board-3cfff7c.zip)。外层 ZIP 的哈希写在仓库里同目录的 [SHA256SUMS](SHA256SUMS) 中，要和 ZIP 一起下载；它不放进 ZIP，是为了避免自引用。这个外层 ZIP 用于存档和交接，不要直接当 Gerber 上传。

解压后，每个文件都能用包内 `manifest.json` 的 `payload_sha256` 校验。在解压目录运行：

```sh
python -c 'import hashlib,json,pathlib; m=json.load(open("manifest.json")); bad=[n for n,h in m["payload_sha256"].items() if hashlib.sha256(pathlib.Path(n).read_bytes()).hexdigest()!=h]; print("PASS" if not bad else bad); raise SystemExit(bool(bad))'
```

1. **制板文件**：[fabrication/gerber-drill-only.zip](fabrication/gerber-drill-only.zip)，只含 11 层 Gerber、PTH/NPTH 钻孔和 Gerber job。订单参数：4 层、144×112 mm、板厚 1.6 mm、外层 2oz、内层 1oz。所有工艺确认项见 [订单与 CAM](docs/order-and-cam.md)。
2. **厂商双面贴装**：[SMT BOM](assembly/jlc-smt-bom.csv) 和 [CPL](assembly/jlc-smt-cpl.csv)，共 153 件，正面 138、底面 15。J5 是混合件：厂商贴 SMT 触点，还要确认并完成 4 个 PTH 屏蔽脚的补焊。
3. **用户采购和自焊**：[18 件通孔清单](assembly/hand-solder-purchase.csv)，数量按每块板计。C26/C36 不装，TP 测试点和 H 安装孔不需要采购。
4. **料号匹配**：[料号匹配表](assembly/part-matching.csv)。41 个型号中，39 个已在 LCSC 页面逐字符核对过 MPN 和品牌，编号已填入 SMT BOM。另外两个 LCSC/嘉立创没有上架，是**下单阻塞项**：W25Q16RVCNJQ 和 MF-MSMF110/16X-2，需要走全球代购或寄料，不得换后缀。有 6 个型号在核对当天库存为 0 或很低：0407008.WR、CSD18540Q5B、GRM155R61C105KA12D、RC0402FR-0727RL、RC0603FR-07511KL、LM74700QDBVRQ1。另有 3 个低库存型号：SRP1245A-100M、C0805C475K4PACTU、CRCW2512300RFKEG。以上都以下单页面实时库存为准。装配和极性见[装配/极性说明](docs/assembly-and-polarity.md)。
5. **收板后**：按 [首次上电步骤](docs/bring-up.md) 分级测试。指定的 UF2 在 `firmware/` 下，保持原文件；它不代表固件或实板已经运行验收。

`drawings/assembly.png` 是正面装配图。`assembly-bottom.png` 是从顶面透视看底面元件，**不是翻板后拍到的样子**。工厂要结合 Layer 字段和原生 pad/net 表核实底面，不要额外镜像 CPL。`drawings/schematic.pdf` 供对照。

## 核验与范围

`manifest.json` 绑定了以下内容：原生设计基线、源文件 SHA256、包内每个文件的 SHA256，以及分工数量。包含本包的 Git 提交就是交付提交，不把设计提交冒充为交付提交。

`validation/` 保存了对同一基线做的检查结果：30/30 项制造一致性检查、ERC/DRC 零错误、控制器/UF2 核验、电源边界计算和 JLC 几何检查。报告保留原始检查时间和忽略项。自动检查通过，不等于 CAM 已接受或硬件已验证。

需要工厂确认的项目：
- 工艺边和基准点（FID）；
- 28 个焊盘内散热孔的钢网或填孔方案；
- 2oz 外层下 0.15 mm 过孔铜环与 0.15/0.15 mm 线宽线距；
- J1/J5 镀槽；
- USB 局部阻焊；
- 实际叠层与 USB 阻抗；
- 精确料号、上下板面和旋转角度；
- J5 屏蔽脚工艺。

我们没有代用户上传、报价或采购。

重建方法（在完整 Git 仓库中，用 KiCad 10 自带的 Python/pcbnew）：运行 `python electronics/package_first_board.py`。默认复用本目录已归档的审核证据，脚本会重新校验输入哈希，并确认原生设计文件与固定设计提交逐字节一致；它不会重写 PCB。首次生成时可以用 `--audit-dir <审核输出目录>` 指定审核目录。不装 KiCad 的标准 Python 也可以运行 `python -m unittest discover -s electronics -p 'test_*.py' -v`，校验归档和分工；CI 不需要安装 KiCad。
