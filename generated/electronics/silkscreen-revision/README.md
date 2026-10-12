# A1 国内嘉立创丝印适配

当前 PCB SHA-256：`11b8502157f6d15a8be044557d35306fc5444240d9bb40ef5166bf3fedb1bb9e`。基线为已推送且CI成功的 `eb085ea`。本轮只本地提交；未重试受限域名、未上传、未收到报价或厂商DFM结论。制造状态仍为未放行。

## 实际范围与结果

- **52 处可见正面丝印**原为 0.8×0.8 mm，现为 **1×1 mm**。包括 BOOT/RESET、USB/SWD/UART、接口信号和极性、测试点、电源说明与工程限制文字。内容、方向、位置、字线宽全部保持；无需挪字。背面没有小于1mm的可见丝印文字。
- 另有 **202 处 0.8 mm F.Fab/B.Fab字段**不输出到丝印，其中38处隐藏（F.Fab25、B.Fab13）；全部保持。其他尺寸的制造层字和用户图层字亦保持。完整逐项清单：[修改前文字清单](before-text-inventory.json)。
- 原有0.12mm线宽保留。国内[官方工艺参数](https://www.jlc.com/portal/vtechnology.html)要求字符高度≥1mm、粗细≥0.1mm、到露铜焊盘间隙≥0.15mm。不能套用国际站0.15mm字符线宽或国际贴装服务名称。
- 按KiCad真实字形多边形检查52处放大后文字：最小开窗距离 **0.273551 mm**，最小其他丝印距离 **0.243447 mm**，均在板边内缩0.30mm的区域内；未依赖减去阻焊裁剪来掩盖重叠。近似边界误差0.0001mm，余量远大于此值。[逐字间距](placement-clearances.json)。

## 前后图与严格验证

[前后全板图](before-after.png)已人工检查；底面渲染逐像素相同。此图显示铜与丝印以便定位，并非厂商生产稿。

先运行红测，明确检出52处小字；改后绿测通过。独立契约将最终PCB与 `git show eb085ea:electronics/quadcuber.kicad_pcb` 比较，**恰只有52个 gr_text size字段改变，其余每个字节完全一致**。因此没有改电气、焊盘、走线、铜区缓存、板框、封装、极性图形、文本内容或隐藏字段。[green.json](green.json)。

KiCad **10.0.7** 全build完成：ERC0错误/0警告、DRC0、未连接0、封装错误0、539引脚设计合同0错误。制造独立30项检查全部通过；忽略创建日期后，11 Gerber+2钻孔中**只有 F.Silkscreen 内容改变**，其余铜、阻焊、锡膏、板框、钻孔不变。[制造差异](manufacturing-delta.json)。根目录154项与电路5项回归测试通过。原有机械/固件未改，本轮未重跑远端CI。

`generate.py` 的工程警示字和 `label_interfaces.py` 的标识尺寸同步为1mm；本轮没有运行全板生成器，避免重建放置/布线。今后更改布局仍应重跑间距检查。

## 当前审核资料

默认完整EV3候选为 `release-preflight/ENG-FULL-EV3-v3-CN-SILK`，BOM/CPL均171项，保留J10–J13、排除C26/C36，绑定上述PCB。旧v2/NO-EV3文件属于旧PCB，不能混用。只含Gerber、钻孔、job、BOM、CPL及审核备注的本地新包：`/workspace/tool-verification/jlc-authorized/A1-v3-CN-SILK-FULL-EV3-REVIEW-ONLY.zip`；[包内文件哈希](review-package-manifest.json)。没有生成或声称有云端可下载链接。

此修正只关闭上述小字问题，未替代国内CAM对QFN、实际层叠、热孔和双面/通孔装配的审核。工艺边/基准点仍为可移除拼板提案。完整EV3仍待实物六路通断/试配，载流及首板动态/热验证限制保留。

## 复核

`AppRun python3.11 electronics/verify_silkscreen.py` 检查当前PCB与git基线。几何检查先用KiCad10 Python运行 `extract-geometry.py <eb085ea导出的原板> <临时geometry.json>`，再用带Shapely的Python运行 `check-placement.py <geometry.json> <结果.json>`。它检验每处在原位置满足避让，否则失败，不自动批准移动。
