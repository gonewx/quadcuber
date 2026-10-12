# A1 JLC 局部适配：最终验证

2026-10-12。基于 `da5fc42`；最终 PCB SHA-256 `b04859e7a282eb648943abfbf70d00e488a887627a74470aab24ffc20d637d44`。本轮允许本地提交，未推送、上传厂商或下单。制造资料仍为候选，`manufacturing_release=false`。

## 已实施

四个 J5 S1 屏蔽槽焊盘每边扩大 0.054 mm，名义环宽 0.254 mm；孔位、孔径和槽长不变。本地封装和生成器同步。只扩大焊盘会产生两项项目 0.20 mm 间距违规，因此三个相邻 VBUS 节点向 +X 平移 0.06 mm，恰影响五条既有 0.15 mm 走线，规则、网络和其余放置/布线保持。最终顶层最近其他网铜距离 0.210998 mm，内层铜区重铺后为 0.2505 mm。详见 [实施差异](implementation-summary.md)。

默认 CPL 导出新增 `--exclude-dnp`，避免误装 C26/C36。完整 EV3 候选 BOM/CPL 各 171 项，NO-EV3 候选各 167 项，两组 v2-JLC manifest 均绑定上述 PCB。旧 v1 已标记 SUPERSEDED_NOT_FOR_MANUFACTURE。

## 实际验证结果

- KiCad **10.0.7** 完整 build 成功：ERC 0 错误/0 警告，DRC 0，未连接 0，封装错误 0，设计合同通过；见 [build.log](build.log) 和 [release-status.json](../../release-status.json)。
- 精确变更合同 **23/23** 通过；保留红测、仅焊盘版失败和最终绿测，见 [green.json](green.json)。铜区远离 USB 的变化仅为最多 1 nm 重铺量化，原始零容差结果亦保留。
- 制造一致性 **30/30**：11 Gerber、2 钻孔文件与独立重导出一致；BOM/坐标/面别/角度/钻孔均闭合，见 [fabrication-preflight.json](../fabrication-preflight.json)。
- 最终 JLC 几何检查：普通 PTH 最小焊环 0.254 mm，无不达标项；孔距、孔到走线、内层孔到铜和阻焊到异网走线检查无违规；见 [jlc-preflight.json](../jlc-preflight.json)。本专项没有全铜间距独立扫描，该项以 KiCad 原规则 DRC 为证。
- 回归测试 **191 项通过**：根目录154、电路5、仿真14、机械6、网页12；日志在本目录。网页测试有既存未关闭文件 ResourceWarning，无失败。
- 控制器54元件/180引脚与电源37位号合同重新通过；UF2保持原交付版本。没有把模型数值失败或缺少实板测量改写为通过。

## 工艺与使用边界

RP2040 的 0.20 mm 焊盘宽度符合原厂推荐，不为通用能力条目盲目扩宽；0.12 mm 丝印/0.8 mm 字高属于可读性问题，优先确保极性、pin1、BOOT/RESET标签，见 [独立复核](fine-pitch-review.md)。

可移除工艺边/基准点仍为制造拼板提案，不改变功能板；需要 CAM 确认窄焊盘、热孔开放/填孔方案、模板、双面装配与实际层叠。完整 EV3 在制板前仍需同批插座六路断电通断/试配，不再索要不存在的供应商资料。NO-EV3 仅限明确标记的电源/控制器台架用途。首板再验证 MLCC、5V动态/PVT、联合输入预算、回生/温升、实际启动和装机条件，见 [总评估](../README.md)。

## 复核命令

`electronics/build.py` 通过 `KICAD_APP_RUN` 使用官方 KiCad 10.0.7 AppRun；`verify_fabrication_preflight.py` 与 `verify_usb_slot_revision.py` 使用该 AppRun 的 python3.11。JLC 检查需要 Shapely。USB 变更合同的基线可从 `git show da5fc42:electronics/quadcuber.kicad_pcb` 及同提交 USB `.kicad_mod` 导出到独立目录，再通过 `--baseline` 指定；不要用全板生成器覆盖现有布线。
