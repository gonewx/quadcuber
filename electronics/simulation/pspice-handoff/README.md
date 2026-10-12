# A1 双 TPS54302：PSpice for TI 最小对照移交

日期：2026-10-12。**交付状态：准备完成，Windows/PSpice 未运行，全部九工况 NOT_RUN；不能声称工程可运行或动态验收通过。** 当前 Linux/ngspice 九工况均在启动期中止，见[已有结果](../../../generated/electronics/simulation/buck-vendor/report.md)和[追加诊断](../../../generated/electronics/simulation/buck-vendor/diagnostics/README.md)。本包不改变 PCB、BOM、保护设计或制造 NOT RELEASED 状态。

A1源基线为 `e34395e68b175cf9a279664fd4a13fd6573d95db`；本包据本地 `fab04782a22657a1abe33b5f5fbd95e2b93cc1d0` 的已记录网表准备。不是旧 main 的 Pico H 板。只验证两路降压，不替代RP2040/Flash/EV3、热、机械或整板验证。

## 1. 所需环境与官方入口

- [PSpice for TI 官方下载/申请页](https://www.ti.com/tool/PSPICE-FOR-TI)：软件免费，用户本人完成 myTI 登录、访问申请、下载安装和许可条款确认。本包不包含安装包、账户或许可证。
- [TI 官方系统要求答复](https://e2e.ti.com/support/tools/simulation-hardware-system-design-tools-group/sim-hw-system-design/f/simulation-hardware-system-design-tools-forum/1176649/operating-system-requirements-for-pspice-for)：2022年答复列出 Windows 10 64-bit Professional 和 Windows Server 版本。这是历史版本资料，不能当作2026年安装包的完整支持表；安装前以实际下载版本的安装说明/Release Notes核实Windows版本、内存、磁盘及权限。不要据此推断Windows 11已受支持或不受支持。
- [TI 对Linux/Wine支持的说明](https://e2e.ti.com/support/tools/simulation-hardware-system-design-tools-group/sim-hw-system-design/f/simulation-hardware-system-design-tools-forum/932412/ti-version-of-spice-circuit-simulator)；本次没有安装Windows或Wine。
- [TI 离线使用期限说明](https://e2e.ti.com/support/tools/simulation-hardware-system-design-tools-group/sim-hw-system-design/f/simulation-hardware-system-design-tools-forum/924877/faq-how-long-can-i-be-offline-while-running-the-pspice-for-ti-application)：需定期联网；具体授权行为以当前版本提示为准。登录、许可、下载审批或设备数量错误需用户本人处理并回传去敏后的错误文字，勿发送密码、访问密钥或会话令牌。
- [官方工作区教程](https://www.ti.com/video/6162737009001)、[官方模型导入教程](https://www.ti.com/video/6162754989001)。后者用于模型/符号导入，不等于把整个测试网表自动转换成原理图。

## 2. 两套电路必须分开

| 对象 | 来源/文件 | 目的与不可混淆之处 |
|---|---|---|
| TI原厂参考测试台 | 官方ZIP中的 `TPS54302_TRANS.OPJ`、`.DSN`、`TPS54302DDC_TRANS.OLB`、原始`.LIB`及Startup/Steady_State的`trans.sim` | 先验证模型在原厂求解器和原厂参考电路中能运行。它不是A1实际BOM，不套用A1的5V验收阈值。 |
| 本包A1对照测试台 | 九个`VIN*_C*.cir` | 实际双路A1降压BOM的PSpice文本测试网表，含约定的理想源、负载及寄生假设。是新准备的对照输入，尚未在Windows解析/运行。不是原厂DSN，也不是KiCad原理图的自动完整导出。 |

从[TI官方模型入口](https://www.ti.com/lit/zip/slvmbl9)下载（本次同域跳至slvmbl9a.zip），保留ZIP原件。ZIP SHA256：`d06e58535f99c35ee5da259e68c09c471b819d00c2fe98d4d5d1da49ea730f77`。

解包后 `TPS54302_TRANS.LIB` 的SHA256必须为：

`52a568f08f1eed44961238a1ff10b68c2ce1faa1cdf2c24659b17b1f820f0026`

用PowerShell `Get-FileHash -Algorithm SHA256 .\TPS54302_TRANS.LIB` 核对。其余原厂文件散列及九份本包网表散列见[source-manifest.json](source-manifest.json)。若TI更新版本导致散列不同，保留新包并标记版本差异，先回传，不冒称同一模型对照。

**PSpice必须使用原始LIB：不要拿ngspice适配LIB，不改XOR、EN空格、二极管参数、钳位或保护逻辑。** 本包不再分发TI模型/原厂工程本体，应从官方ZIP获取并保留版权信息。

## 3. 先运行原厂工程

1. 将官方ZIP完整解压至本地可写目录，另留一份只读原件。保持相对目录结构；在工作副本中用Capture的 `File > Open > Project` 打开 `TPS54302_TRANS.OPJ`。工程本身列有 `Startup-trans` 和 `Steady_State-trans` 两个profile。
2. 如发生旧版工程转换，允许在工作副本保存，保留转换提示及新旧文件；这不代表原始LIB可以修改。若库路径失效，将profile的库配置指向同包原始LIB，并使用同包OLB，不替换成名称近似的其他芯片。
3. 先选择 `Startup-trans`，检查对应Startup电路和原profile，再 `PSpice > Run`。原Startup profile记录结束6.5ms、最大步长20ns，ABSTOL=10n、VNTOL=10u、ITL1=1500、ITL2=400、ITL4=100。保持其他原厂设定，不把本包A1的25ms或负载值写进去。
4. 再选择 `Steady_State-trans`，确认切换了对应电路/profile，按该profile原值运行。不要把稳态预置模型用于A1冷启动验收。
5. 保存两个测试台的生成`.cir/.net`、完整`.out`/会话日志、`.dat`及可读波形。参考台先判“是否无致命错误且到达各自结束时间”，再按其实际输出/负载规格解释；不要预设两者都是A1参数。

若原厂工程本身失败，先回传原始工程转换/库加载/运行错误和所用版本，暂停A1结果的通过声明。没有必要通过改模型参数强行得到曲线。

## 4. A1网表与Capture路径

将九个本包`.cir`复制到一个独立工作目录，并将已校验的原始 `TPS54302_TRANS.LIB` 原样复制到该目录。每个网表用 `.LIB "TPS54302_TRANS.LIB"` 引用它。不要在原厂参考工程目录内覆盖文件。

若所装PSpice模拟器提供打开完整电路网表的入口，可在模拟器中按其本地帮助打开一个`.cir`运行；**本机未验证该版本是否开放此入口，不保证双击即可运行，也不提供猜测的可执行文件命令行。** 如不支持独立网表，采用下述Capture流程，不把顶层`.cir`错误地作为单个器件模型导入：

1. 新建 `Analog or Mixed A/D` 工程（命名 `A1_TPS54302_Compare`），添加同包 `TPS54302DDC_TRANS.OLB`，放置两个TPS54302符号。Simulation Settings的Configuration Files/Library配置原始LIB。
2. 按本包任一`.cir`的连接搭建双路电路；电压源VPWL的时间/电压对为 `(0,0)`、`(1ms,VIN)`，之后保持终值；地必须为PSpice节点0。GND/PH/VSENSE按下表映射，不按图形引脚左右顺序猜测。
3. 用PSpice模拟行为电流源GVALUE分别实现负载。A路表达式为 `LIMIT(V(b1out)/4,0,1)*(0.25+(1.5-0.25)*IF(TIME>12m,IF(TIME<18m,1,0),0))`；B路把节点改为b2out、0.25改为0.05。电流从输出流向地，低压时衰减，避免启动前被恒流负载抽负。该表达式仅替代ngspice外围B源的语法，芯片LIB不变。
4. 新建Time Domain (Transient) profile：运行25ms、开始保存0、最大步长20ns，温度27°C；不启用UIC/跳过初始工作点，不加载先前偏置点。数值选项用网表中的值，其中RELTOL=1e−4来自已有A1对照，其他五项来自原厂Startup profile。任何自动收敛设置变化应另存profile并记录，不能悄悄覆盖基准。
5. 分别建九个profile/工作副本，填下表VIN和电容值；生成网表后逐项对照本包`.cir`，特别核对两个X实例的节点次序、负载方向、DNP和容量单位。不要直接改Capture自动生成的网表来长期保存设计，它可能被下一次运行覆盖。
6. 先尝试VIN9_C0.8（矩阵中接近标称的一项），再运行其余八项。容量系数1.0不在九工况矩阵内；若额外做标称诊断，另命名而不能替代九项之一。

原始子电路顺序：`BOOT EN GND PH VIN VSENSE PARAMS: STEADY_STATE=0`。本包X1/X2不覆盖STEADY_STATE，保留默认0。

| 模型引脚 | A路节点 | B路节点 |
|---|---|---|
| BOOT | b1boot | b2boot |
| EN | b1en | b2en |
| GND | 0 | 0 |
| PH（SW） | b1sw | b2sw |
| VIN | vm | vm |
| VSENSE（FB） | b1fb | b2fb |

每路：输入主电容10µF×系数并100nF；电感10µH串DCR21.4mΩ典型；输出两颗22µF等效44µF×系数串等效ESR3mΩ（假设）；反馈100k/13.3k、前馈75pF；BOOT49.9Ω/100nF；EN511k/105k；C26/C36的470µF默认DNP，不装入仿真。网表中的R1/R2dcr和R1/R2esr是寄生等效，不是新增板上元件。两颗输出电容合并仅表示该测试模型的并联等效。

## 5. 九工况、时序与验收

| Case | VIN(V) | 容量系数 | 每路主输入(µF) | 每路总输出(µF) |
|---|---:|---:|---:|---:|
| VIN8.82_C0.4 | 8.82 | 0.4 | 4 | 17.6 |
| VIN8.82_C0.8 | 8.82 | 0.8 | 8 | 35.2 |
| VIN8.82_C1.2 | 8.82 | 1.2 | 12 | 52.8 |
| VIN9_C0.4 | 9 | 0.4 | 4 | 17.6 |
| VIN9_C0.8 | 9 | 0.8 | 8 | 35.2 |
| VIN9_C1.2 | 9 | 1.2 | 12 | 52.8 |
| VIN9.18_C0.4 | 9.18 | 0.4 | 4 | 17.6 |
| VIN9.18_C0.8 | 9.18 | 0.8 | 8 | 35.2 |
| VIN9.18_C1.2 | 9.18 | 1.2 | 12 | 52.8 |

两路同时启动。VM在0～1ms线性从0升至目标VIN；负载A/B初始0.25A/0.05A，在12ms后同时升至各1.5A，18ms恢复。低压负载系数`LIMIT(Vout/4,0,1)`全程保留。脉冲边沿为现有理想阶跃；若需有限边沿实验，应另名并记录边沿时长，不能替换主对照而不注明。

先判计算是否完整：无致命/abort/convergence错误，时间从0持续到25ms，数据有限且时间递增，两路所需波形齐全。只有完整结果才可逐路判断以下项目：

- 0～10ms内达到4.75V；10～25ms全区间输出不低于4.75V。
- 0～25ms全区间输出不超过5.25V（因此10～25ms窗口为4.75～5.25V）。
- 0～25ms两只电感各自的绝对电流峰值严格小于6A。
- 以上包含12ms增载、18ms卸载；不能只用最终值或一张稳态截图判断。

这些是本项目对照阈值，不是TI对整板的认证。容量0.4是严苛未知偏压敏感性，不是电容厂保证；ESR/DCR为所述假设/典型值，未覆盖全部容差。理想VM直接钳住输入电容，**本矩阵不能验证输入源/线束阻抗、VM纹波或输入电容动态容差**。也不构成相位裕量、温度、保护故障时序或实物热验证。

## 6. 必须回传的内容

按`reference-startup/`、`reference-steady-state/`及九个case目录整理，可压缩回传；失败项也保留。

1. `environment.txt`：Windows版本、PSpice for TI完整版本/build、运行日期、是否发生工程转换、实际库绝对路径、SHA256、数值/自动收敛设置变更。不要附登录信息或许可密钥。
2. 原厂两profile和A1工作工程：OPJ、DSN、SIM，以及运行时生成的CIR/NET（A1若直接跑文本则回传实际运行的CIR）。原模型可仅回传SHA256和官方版本，不必重复附LIB。
3. 完整`.out`和运行日志、错误/警告文字、原生`.dat`（及关联索引文件若生成）；保留未完成的部分波形并明确终止时间。不要只回传成功截图。
4. A1每项导出CSV/文本，列至少为 `time_s,vm_V,vout_A_V,vout_B_V,iL1_A,iL2_A,en_A_V,en_B_V`；注明电感电流正向为SW→输出。保留求解器自适应点/原生DAT以核对窄峰值，勿只提供重采样均值；`.PRINT TRAN`输出仅作可读补充，不能单独证明未漏峰值。若分批导出，保留各批独立时间列，勿按行号硬拼。
5. 启动0～10ms、增载12ms附近、卸载18ms附近的输出/电感曲线；在[cases-and-results.csv](cases-and-results.csv)填写最后时刻、是否完整、各路最小/最大值、电感峰值和结论。NOT_RUN、FAILED/INCOMPLETE、COMPLETED_FAIL、COMPLETED_PASS须区分。原厂参考台不使用该A1阈值表。

若软件报告探针/许可证限制，先保存准确提示，再依该版本许可和官方说明分批合法导出同一工况需要的通道；不要删掉必要通道后声称全部指标已验证。

## 7. 本机已做与未做

本机仅核对了：九份网表与已有A1九工况的被动元件/连接一致；原始LIB引用和六脚顺序；PSpice外围负载表达式在约定时点的数学等价；矩阵/阈值/来源散列。**未用Windows/PSpice解析或运行这些文件，未生成或假称已验证的A1二进制DSN。** 任何导入/语法/许可证问题应回传修正后再运行，不能从静态检查推断仿真成功。
