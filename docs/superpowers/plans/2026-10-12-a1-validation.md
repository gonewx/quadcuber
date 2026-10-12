# A1 KiCad 10 与原厂降压模型验证计划

> **For agentic workers:** Use superpowers:executing-plans for sequential implementation; KiCad migration is independently delegated.

**Goal:** 在已授权的 e34395e68b175cf9a279664fd4a13fd6573d95db A1 工程上完成 KiCad 10.0.7 验证和真实 BOM 的 TI TPS54302 模型测试，留下可复核证据。

**Architecture:** 保持既有原生设计及固件。KiCad迁移/导出和原厂仿真分开实施，最终核对源文件哈希；实际完成时间和错误日志决定仿真状态。

**Tech Stack:** KiCad 10.0.7 Lite、Debian ngspice 44.2、Python、TI slvmbl9a 未加密模型。

**Spec:** 本次授权：使用上述A1分支，本地实施/测试/提交，不推送；electronics/README.md、electronics/simulation/README.md、electronics/sources/bom-exact-part-audit.md。

## Global Constraints

- 不将main/A0当作A1；不重新设计或退回Flash/固件修订。
- 保留EV3针序/视向/型号/载流、实物热与机械等HOLD。
- Lite缺少预装3D库；不得宣称完整3D或制造放行。
- 仅本地提交；原厂模型和转换均带哈希、来源、限制。

## Review Focus

- ngspice返回0但瞬态提前中止：必须检查末时刻、日志、有限数据。
- 原厂引脚PH/VSENSE与实际器件SW/FB：显式审查映射，不猜。
- 输入和电容容差、启动和负载阶跃：两路真实BOM全覆盖，失败也保存结果。
- 10版原生存盘/解析与旧版Python混用：记录真实版本，重跑引脚契约及一致性DRC。
- 更改源文件后旧报告/哈希失配：更新验证元数据，旧独立审查不得冒充新审查。

## Tasks

- [x] KiCad迁移：原生重存、修库/工具选择，ERC/DRC含一致性、引脚契约与59项回归；修改build.py/check.py及必要原生文件，输出generated/electronics。
- [x] 原厂模型基线：仓库外保留未修改TI文件，记录ps兼容模式/XSPICE依赖，验证启动与收敛；不将其当A1。
- [ ] A1模型测试：更新electronics/simulation/run_buck_vendor.py，显式引脚映射和失败判据、记录BOM假设及转换；9输入/电容组合、双路启动和阶跃，输出日志/波形/机器可读状态及报告。
- [ ] 汇总审查：源哈希、阈值、局限、实际完成项；检查git diff，提交本地结果而不推送。

## 执行记录

- 基线已核对，分支a1-kicad10-validation，当前环境为本任务独立执行环境，按授权在当前检出本地实施。
- KiCad10迁移/库字段同步后ERC/DRC/一致性/543引脚契约全零；59相关回归通过。
- 原厂模型取得；最小基线已测试但数值失败。实际A1矩阵9工况均在0.458～0.779ms数值失败，0完整完成/0通过。因此上方实际动态验收任务保持未完成。
- Ruling: 不将无法收敛的原厂宏模型修改至看似通过；仅保留独立真值表确认的异或语义转换，放宽二极管/平滑实验均弃用。代价：启动/负载阶跃验收仍阻塞，须后续PSpice对照或有依据的移植。
- 原厂模型本体不随Git再分发；补丁、哈希、部分波形、日志和声明明确的失败报告随本次本地提交保存。

- Final review ruling: 理想VM源使输入电容动态影响不可辨识，已补明确模型限制；未擅自加入未知源阻抗。代价：输入源阻抗/输入电容动态验证也仍未完成。
- Final review: 无Critical/未处理Important；10单测通过，原厂模型/源SHA/9波形/EDA证据独立复核一致。Minor deferred：诊断报告生成器的文字专门针对本次Timestep too small，未来不同失败类型应同步修改/加强输入约束。
- 用户追加要求：保存阶段提交后继续合法模型兼容/参考testbench诊断；不以失败记录充当仿真任务完成。
