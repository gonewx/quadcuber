# A1 direct-boot-precision-v1 实施与验证

用户于2026-10-12明确批准：删除R20/R30，100nF C22/C32直接跨BOOT–SW并靠近芯片，反馈100k/13.3k不变、使用0.1%精确MPN。基线提交2d01805，PCB基线SHA256 `9e55fcbee01241fc6ec3682fde79daaacd6bc623ecfc311809600e001099350a`。仅局部修改；不推送、不发布制造。

## 电气与元数据

- U2.6—C22.1=`B1_BOOT`；C22.2—U2.2=`B1_SW`。B路对应U3/C32。
- 删除R20/R30及两路BOOT_CAP中间网；BOOT与SW仍由电容隔开，绝非铜短接。
- R21/R31=`RT0603BRD07100KL`（100kΩ），R22/R32=`RT0603BRD0713K3L`（13.3kΩ）。均0603、0.1%、±25ppm/°C。阻值、EN、Cff及输出电容DNP策略不变。
- 不运行全板生成器；通过 `electronics/revise_buck_metadata.py` 定向同步原理图、专用库条目、源快照和BOM。`electronics/verify_buck_revision.py`交叉检查源、JSON、BOM和实际导出网表。KiCad `check.py`另外独立核对PCB焊盘和引脚合同。

## 已执行测试

- 源回归测试3项先因旧串阻、BOOT_CAP和1%MPN失败（source-red.log），修正后3/3通过；独立审阅发现末尾placement覆盖新坐标，新增第4项测试先失败后修正，最终4/4通过（source-tests.log）。
- 仿真测试14/14通过（simulation-tests.log），含新连接契约、旧料号/旧节点拒绝及直接bootstrap网表。
- 全项目 `python -m unittest discover`：154/154通过（project-tests.log）。
- 补充web 12/12、机械装配6/6通过；web原有未关闭BOM文件的ResourceWarning保留在日志，未修改无关代码。环境未安装pytest，使用项目现有unittest运行器。
- 新版九份PSpice交接仅静态验证，均NOT_RUN，不继承旧失败/通过状态。

## 布局与KiCad结果

[前后局部图](layout-before-after.svg)以实际板对象绘制；[对象差异及路径数据](layout-comparison.json)记录所有改动。平面填铜为易读性未画入局部图，真实PCB已重新填充并检查。

| 几何量（mm） | A修改前 | A修改后 | B修改前 | B修改后 |
|---|---:|---:|---:|---:|
| BOOT至电容引线 |12.775|3.287|13.412|3.287|
| 该引线过孔数 |0|0|2|0|
| 电容SW端至芯片返回线 |8.853|5.595|10.762|5.595|
| 两段引线合计 |21.627|8.881|24.173|8.881|

修改前BOOT长度采用铜线段合计加原电阻焊盘中心间距1.65mm；修改后采用铜线中心线长度。均不计电容内部、IC内部和过孔孔壁长度，旧版有微小重复段，故是布局几何比较，不是寄生电感或完整回路面积测量。

C22=(98,91.9)mm、C32=(147,91.9)mm，均F.Cu、0°。SW主功率连接保持；为让出短回路，A路FB局部改走B.Cu并增加两个反馈信号过孔，B路FB保持，B路两个GND过孔及对应引线局部平移而不增加数量。两路BOOT及新增SW返回支路本身均零过孔。内层铜平面隔开正面SW与背面反馈，但这不替代噪声/稳定性实测。

对象差异检查：194个封装所有已记录字段不变，四只反馈封装仅MPN字段改变，另两只电容移动、两只电阻删除；2557个原铜线/过孔对象不变。板框、层数、铜区边界保持；全部铜区填充均由KiCad10重新计算。独立审阅另将旧基线用同版本重填后比较：VIN/VIN_FUSED/3V3差异归零；两路降压局部矩形之外，没有面积超过0.000001mm²的差异块，剩余极小细片按数值舍入残差理解，非逐字节完全一致。见[独立审阅](independent-review.md)。

完整 `electronics/build.py` 已实际执行成功：KiCad10.0.7 ERC错误/警告0，DRC违规0，未连焊盘0，封装错误0，schematic parity通过；`contract-check.json`独立引脚合同0错误。详见[构建日志](build.log)、[ERC](../erc.rpt)、[DRC](../drc.rpt)、[交叉检查](cross-check.json)。

## 新版宏模型有界诊断

使用未改参数的官方TPS54302模型、既有一处布尔XOR语法适配及ngspice44.2，运行一次9V/C0.8工况，单工况20s超时上限。实际约3.092s运行后，瞬态在0.000761902267s停止，9091点，报 `Timestep too small` / `trouble with node b2boot`；未达到25ms终点，脚本正确返回失败并标记INCOMPLETE_NUMERICAL_FAILURE。没有改成理想时钟、放宽验收或追加盲扫。

[本修订运行状态](../simulation/buck-vendor-direct-boot-precision-v1/run-status.json)及其目录中的网表、日志、有限波形独立保存。它证明当前Linux数值求解仍未完成，不能推出实物通过或失败，更不能把停止点电压当稳态结果。PSpice新版九工况仍是NOT_RUN。

## 制造与动态边界

静态初始容差计算4.940693–5.214182V，未覆盖电阻温漂/老化、偏置电流、线/负载调节和瞬态。实际MLCC偏压/ESR曲线仍缺；精度升级和DRC均不能代替实际BOOT电压、开关边沿、启动、规定负载阶跃与温升测试。

旧PSpice交接、WEBENCH用户PDF评审、ngspice/Xyce失败证据均保留，不冒充本修订结果。EV3 PINMAP/MPN/CURRENT、热和机械HOLD不变。完整制造状态仍NOT RELEASED。

## 独立审阅与保存

独立审阅实际检查源/网表/BOM、新仿真契约、PCB对象差异、同版本填铜对照和前后PNG。发现的源放置表覆盖问题已用失败测试复现并修复，最终源4、仿真14、项目154、web12、机械6，共190项测试通过。原理图删节点造成的行尾空白已清理，重跑完整KiCad构建及交叉核对通过。无未处理的重要审阅问题；尚未解决的动态/实物风险见上文。

## 复算入口

旧板可从本地基线提交提取：`git show 2d01805:electronics/quadcuber.kicad_pcb > /tmp/a1-before.kicad_pcb`（先核SHA256）。以KiCad10.0.7的Python运行 `electronics/revise_boot_layout.py --baseline /tmp/a1-before.kicad_pcb --output /tmp/a1-reproduced.kicad_pcb --evidence /tmp/a1-reproduced-evidence`，不会覆盖正式板。`layout-reproduction.log`记录此次脚本重生成与正式板逐字节相同。完整工程导出使用已配置的KiCad10环境运行 `python electronics/build.py`；这会更新工程预览和报告，不会重建布线。
