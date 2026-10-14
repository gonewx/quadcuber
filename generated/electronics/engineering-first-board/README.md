# Quadcuber A1 唯一工程首板送厂包

设计基线 `db20b983d23d1dedc107f435f8ece6b734b3bd6b`，J1 **Switchcraft RASPC722X DC5521**。本入口取代所有旧 Phoenix / ENG-FULL / ENG-POWER-CONTROLLER 变体。不得从旧目录拼接BOM、钻孔或Gerber。

这是已整理的受控工程首板 CAM 候选包；未声称工厂已接受、料已齐或实板合格。原板 HOLD / DO NOT FABRICATE 丝印完整保留，须按 [CAM说明](docs/order-and-cam.md)明确解释及确认。电路、铜、孔、布线、丝印均没有因本包修改。

## 下载及使用

完整交付：[quadcuber-A1-first-board-db20b98.zip](quadcuber-A1-first-board-db20b98.zip)。仓库旁置 [SHA256SUMS](SHA256SUMS) 含外层ZIP哈希，应与ZIP一并下载；它不在ZIP内部，以免自引用。该外层ZIP供存档/交接；不要作为Gerber直接上传。

解压后的每个文件可用包内 `manifest.json` 的 `payload_sha256` 检查。在解压目录运行：

```sh
python -c 'import hashlib,json,pathlib; m=json.load(open("manifest.json")); bad=[n for n,h in m["payload_sha256"].items() if hashlib.sha256(pathlib.Path(n).read_bytes()).hexdigest()!=h]; print("PASS" if not bad else bad); raise SystemExit(bool(bad))'
```

1. 制板文件：[fabrication/gerber-drill-only.zip](fabrication/gerber-drill-only.zip)，仅包含11层Gerber、PTH/NPTH钻孔和Gerber job。订单采用4层144×112mm、1.6mm、外2oz内1oz；全部工艺确认见 [订单与CAM](docs/order-and-cam.md)。
2. 厂商双面装配：[SMT BOM](assembly/jlc-smt-bom.csv) 和 [CPL](assembly/jlc-smt-cpl.csv)，153件，Top138/Bottom15。J5是混合件，厂商既贴SMT触点又须确认并完成4个PTH屏蔽脚补焊。
3. 用户采购/自焊：[18件通孔清单](assembly/hand-solder-purchase.csv)，按每块板计。C26/C36不装，TP/H不采购。
4. [料号匹配待核表](assembly/part-matching.csv)与[装配/极性说明](docs/assembly-and-polarity.md)：空白料库编号不是替代许可。两个目录编号已核但库存、所选服务和机器旋转仍待订单确认；没有猜测其余料号或库存。
5. 收板后按 [首次上电步骤](docs/bring-up.md) 分级测试。指定UF2在 `firmware/`，保持原文件，不代表固件或实板已经运行验收。

`drawings/assembly.png` 为正面装配图，`assembly-bottom.png` 为底面元件的顶视透视，**不是翻板后的相机视图**。工厂须结合Layer字段和原生pad/net表核实底面，不额外镜像CPL。`drawings/schematic.pdf`供对照。

## 核验与范围

`manifest.json`绑定原生设计基线、源文件SHA256、包内每个文件SHA256及分工数量；Git仓库中包含本包的提交即交付提交，不把设计提交冒充交付提交。`validation/`保存对相同基线完成的30/30制造一致性检查、ERC/DRC零错误、控制器/UF2核验、电源边界及JLC几何检查。报告保留原检查时间和忽略项，自动检查通过不等于CAM接受或硬件验证通过。

工厂确认项目具体包括：工艺边/FID、28个焊盘内热孔与钢网/填孔方案、J1/J5镀槽、USB局部阻焊、实际叠层/USB阻抗、精确料号/上下板面/旋转、J5屏蔽脚工艺、保留风险丝印。没有代用户上传、报价或采购。

重建（在完整Git仓库中，用KiCad10的Python/pcbnew）：`python electronics/package_first_board.py`。默认复用本目录已归档审核证据，脚本重新检查其输入哈希和原生文件与固定设计提交逐字节一致；不会重写PCB。首次生成可指定 `--audit-dir <审核输出目录>`。标准Python可运行 `python -m unittest discover -s electronics -p 'test_*.py' -v` 验证归档与分工；不要求CI安装KiCad。
