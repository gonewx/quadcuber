# Linux 原生 TI 参考电路验证：冷启动仍阻塞

2026-10-12；工程基线 `93c14bda0abd0146bacd13c8e34cf57c50289481`，A1 来源 `e34395e68b175cf9a279664fd4a13fd6573d95db`。本轮未改 PCB、原理图、BOM、固件或芯片参数，未推送，未向外部仿真服务上传任何项目数据。

## 结果

Linux 原生 Xyce 7.10 已从官方源码编译并运行。TI 原包中的两份 OrCAD 参考电路已由官方 KiCad 上游解析器恢复并检查全部69个器件引脚及107条连线。这是 **DSN 派生的可审计重建，不是 Cadence 导出的原始网表**。

在下述明确记录的兼容候选处理后，**稳态参考完整完成800 µs；冷启动参考没有完成6.5 ms**。没有独立 PSpice 波形对照，不能宣称两个求解器行为一致，也不能将“稳态完成”当作 A1 验收通过。

|参考/算法|结果|最后输出时刻|
|---|---|---:|
|稳态，默认积分，候选初值处理|退出0，5842个有限且严格递增的样本，完整完成|800 µs|
|冷启动，默认积分|退出1，步长过小|108.133711 µs|
|冷启动，Gear|退出1，步长过小|108.127792 µs|
|冷启动，阻尼 Newton|退出1，步长过小|108.133711 µs|
|冷启动，ERROPTION=1、DELMAX=20ns|退出1，最终线性矩阵奇异；仅诊断，不能作精度证据|113.974005 µs|
|冷启动，一阶 Gear（后向 Euler）|退出1，步长过小|648.454616 µs|

稳态按原 profile 只保存750～800 µs：VOUT=5.09295553～5.09980521 V，电感电流=2.74948226～3.25186809 A。启动前750 µs未保存，不据此断言全过程无过冲。输出默认8位精度，失败运行末尾出现重复打印时间；未删点掩盖此现象。

**Xyce 的 A1 九工况尚未运行**：用户要求先完整跑通原厂参考，冷启动前置条件仍未满足。之前 ngspice A1 九工况仍为0完整完成、0通过。制造状态继续 **NOT RELEASED**；EV3 PINMAP/MPN/CURRENT及实物验证 HOLD 不变。

## 来源与可追溯性

- TI 官方包：[slvmbl9](https://www.ti.com/lit/zip/slvmbl9)，仅跳转同域 slvmbl9a，ZIP SHA256 `d06e58535f99c35ee5da259e68c09c471b819d00c2fe98d4d5d1da49ea730f77`。
- 原模型 SHA256 `52a568f08f1eed44961238a1ff10b68c2ce1faa1cdf2c24659b17b1f820f0026`；未覆盖、未随 Git 再分发。
- [KiCad 官方源码](https://github.com/KiCad/kicad-source-mirror/tree/0616634034fa1a8c92c141c293342cbef2f68dff/eeschema/sch_io/orcad)提交 `0616634034fa1a8c92c141c293342cbef2f68dff`，18份解析器依赖原样使用。`reference-recovery/parser-source-provenance.json`含每文件固定来源与哈希；本目录保存本地 C++ harness、导出器、原始解析结果、完整连接表、恢复网表和核验结果。解析器文件可按固定来源恢复；不需要运行 Windows。KiCad10.0.7发布版本身不支持此 OrCAD 导入，不能混淆发布版能力和上游解析器。
- [Xyce 官方源码](https://github.com/Xyce/Xyce/tree/Release-7.10.0)提交 `a592a42ae7472151d1c8e3bca0ca62d27476f2f3`；[Trilinos 官方源码](https://github.com/trilinos/Trilinos/tree/975307431d60d0859ebaa27c9169cbb1d4287513)提交见链接。未改求解器源码。Debian依赖包按官方索引SHA256核验。`xyce-build/`保存配置、依赖哈希、编译日志和可执行文件哈希。
- 安装路径 `/workspace/tools/xyce-7.10/bin/Xyce`；串行 Release，ADMS/Neuron/FFT关闭（该模型未用），CURL和遥测地址关闭。Trilinos使用官方基础配置、Fortran关闭及官方说明的 GCC14 C 编译兼容参数。没有账户、付费或新许可证交互。
- `api.anaconda.org`曾被域名策略拒绝，停止该路径；没有代理、中转或绕域名限制。之后直接使用官方 GitHub 源码构建，未重新请求被拒地址。

## 兼容候选处理及边界

`xyce-reference/adaptation.json`、两份 `.patch` 和 `input-sha256.json`记录源输入和变更：

1. `.LIB 单文件`改为 `.INCLUDE`；DSN符号名 `TPS54302DDC_TRANS` 与包内LIB定义 `TPS54302_TRANS` 不同，用外部六脚同位置别名包装，并原样传递 STEADY_STATE。PH=SW、VSENSE=FB。
2. 四处 `.IC V(Qint) {VSS}`仅补等号。原语法确实报错；单元实验直接观察Qint初值及解析RC轨迹。UIC下派生输出OUT在t=0未同步，原输出检查失败被保留，不能宣称单元矩阵全部通过。
3. `.IC V(COMP)={STEADY_STATE*1.3695}`改为对 `N16888001` 的同值约束。原模型0V理想源把两节点连接，故意图上的电压约束相同。原COMP行无结构对角元素，Xyce施加IC后该行全零，导致DCOP奇异；560×560矩阵和节点名可复核。双层层级最小RC实验复现问题，改约束目标后两节点初值均为0.25V且全轨迹相等，解析误差<7.5e-7V。
4. 该处理仅是**正常DCOP、保留当前双层层级**的候选兼容处理。另发现Xyce层级电压源识别缺陷；顶层/一层IC可能被忽略，UIC两目标导致不同电容初始电荷。反例全部保留在 `zero-v-ic-validation.md` 和对应运行中。不能声称跨层级/UIC等价或完全原样运行TI模型。
5. 正数20ns `.TRAN`打印间隔代替PSpice的0，原stop/start/maxstep不变。去除不支持的PSpice数值 `.OPTIONS` 和 `.PROBE`，使用Xyce默认数值容差和显式 `.PRINT`。**不是相同数值求解配置**；原profile参数仍在恢复网表和审计中。

原 XOR、连续VSWITCH转移函数、器件参数、连接、内部二极管和保护功能均保留；不启用SMOOTHBSRC，不启用UIC，不启用HSPICE math模式。原CESR电容IC本来被注释，未擅自启用。

`xyce-compatibility/`保存18项原始语法/数值运行及额外层级初值反例。原XOR真值表、E/G VALUE、逻辑、连续VSWITCH、RC和空格别名检查通过；HSPICE math是故意的错误语义负对照。`actual-validation.json`的 `all_expected_checks_pass=false`保留了t=0派生输出异常，不能改写为全通过。

## 复查与复现

先阅读 `xyce-reference/results.json`；每个阶段有独立netlist/log，长波形以确定性gzip保存，解压后即原始字节。部分文件中的绝对路径刻意保留为本次运行记录；迁移环境需获得同哈希TI模型并重建同路径或在新驱动中明确记录路径替换，不要直接当作便携脚本运行。

- `reference-recovery/assessment.txt`说明恢复流程及原电路关键值；该文件记录的是恢复子任务当时状态（未运行solver），本报告和 `results.json`记录随后实际结果。
- `xyce-reference/Startup/Failed_Matrix1.mm`、`node-names.txt`及 `xyce-compatibility/zero-v-ic-detailed-validation.json`支持初值矩阵诊断。
- `ngspice-reference/`：恢复参考电路的ngspice47启动50秒超时、稳态初始点中止；退出0并不代表成功。`continuation/`两份KLU日志：实际启用KLU后IC矩阵构造失败，报出的out-of-memory不证明主机耗尽内存。
- `manifest-sha256.json`覆盖本目录证据。未保存求解器二进制、下载包或TI完整模型到Git。

后续阻塞是冷启动切换处的数值问题，以及缺少独立原生PSpice对照。继续工作应基于原节点/矩阵和最小复现定位，不能通过修改器件物理参数、平滑开关或忽略求解失败获得“通过”。
