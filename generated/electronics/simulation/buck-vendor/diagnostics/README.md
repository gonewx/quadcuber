# 原厂 TPS54302 宏模型追加诊断

2026-10-12；在本地阶段提交 `9de8ff6b333dc250357ad0c6a2cfd4cf228b93c2` 后继续排查。**动态验证仍未完成；以下实验没有任何整芯片通过结果。** 未改变板上电路、BOM、保护阈值或制造 HOLD。

## 数值设置与实测结果

解包原厂 Startup/trans.sim 得到 ABSTOL=10n、VNTOL=10u、ITL1=1500、ITL2=400、ITL4=100，原 profile 最大步长20ns、结束6.5ms。将这些数值设置用于实际A1双路9V、输出容量系数1.0网表，保留25ms目标以包含12/18ms负载阶跃；不是运行原厂DSN测试台。以下各A1变体相对于此profile基线只改变表述项目，均保留既有XOR语义适配。

| 实验 | 最后时刻(ms) | 结果 |
|---|---:|---|
| ngspice44.2 + 原厂数值设置 | 0.761023844 | timestep too small，D_U5_D9 |
| ngspice47 + 同网表 | 0.761019214 | timestep too small，E_U5_ABM9 |
| 一阶Gear（后向欧拉） | 0.761022794 | timestep too small，D_U5_D9 |
| ITL4从100提高至1000 | 0.761023844 | timestep too small，D_U5_D9 |
| 仅消除EN初值表达式空格 | 0.761023844 | EN别名警告消失，仍timestep too small |
| 跳过初始工作点 UIC | 日志进度约0.763555 | 持续停滞后人为终止，无导出完整波形 |
| 自选12V最小测试台 + 原厂数值设置 | 报错0.204101 | timestep too small；并非原厂DSN测试台 |
| 单独钳位支路，2µs目标 | 0.002000 | 此局部诊断完成；不代表芯片通过 |

每个目录保存运行网表、完整日志、可获得的部分波形。`results.json`从波形提取结束点/点数；无波形项为null，不能视为零。ngspice返回0不表示瞬态完成。`sha256.json`记录证据文件校验值。

profile基线的最后一行：VM=6.84921460V，EN=1.36488472V，SDWN=0.50000000，U5_LOW_CLMP=0，SS_TR约−99.994µV，U11_ENAB=1；输出仍在微伏级。失败与SDWN穿越0.5的启动释放事件重合。报错节点随求解器改变，不能单凭它认定某一器件参数有误。由同一IF门槛、原二极管N=1e−5、18pF和4MΩ构成的独立钳位支路可完成，说明还需考虑完整宏模型的耦合事件/方言行为。

`V(EN )`→`V(EN)`的诊断副本只改一处空格，消除原先x1.en/x2.en不存在警告，但未解阻。该改动没有并入正式适配；model-change.txt记录生成方式及散列，不再分发模型本体。

## XOR记录修正

旧记录把“给两侧比较项先加括号后做幂运算”的1/0/1/1称为原式结果，不够准确。新增不加括号的原表达式独立测试得到0/0/0/1；两者均不符合XOR应得的0/1/1/0。正式适配的布尔不等式保持0/1/1/0。此修正没有改变主矩阵结果。

## 原厂对照路径及最小缺口

TI当前[TPS54302产品页](https://www.ti.com/product/TPS54302)提供PSpice瞬态模型SLVMBL9A。包内有OrCAD DSN/OLB/OPJ和Startup/Steady_State profile，没有可直接运行的导出.cir/.net。检查DSN的OLE目录也未发现导出网表流；未推断已经还原全部原厂连接。

最直接的受支持对照是[免费PSpice for TI](https://www.ti.com/tool/PSPICE-FOR-TI)：需要受支持的Windows环境、myTI登录/申请下载访问及安装期间网络。TI说明[不支持Linux/Wine](https://e2e.ti.com/support/tools/simulation-hardware-system-design-tools-group/sim-hw-system-design/f/simulation-hardware-system-design-tools-forum/932412/ti-version-of-spice-circuit-simulator)，并有[定期联网要求](https://e2e.ti.com/support/tools/simulation-hardware-system-design-tools-group/sim-hw-system-design-tools-forum/924877/faq-how-long-can-i-be-offline-while-running-the-pspice-for-ti-application)。当前仅有Linux执行环境，缺口不是购买商业许可证；本任务没有用户Windows会话或myTI认证。不得代用户注册/接受条款，也不能假装原厂仿真已运行。

取得该环境后，应先原样运行包内Startup/Steady_State测试台并导出网表/日志作基准，再代入实际双路BOM、9个电压/容量工况及负载阶跃；先确认启动和25ms结束点，再评价输出窗口/电感电流。理想电压源并联输入电容的限制仍然存在，输入源/线束阻抗动态验证需另行建模。

Linux其他途径仍属于未验证移植：[Xyce官方二进制页](https://xyce.sandia.gov/downloads/executables/)明确其RHEL RPM不适用于Debian/Ubuntu，本环境是Debian；官方二进制下载请求被拒绝，未取得文件。源码编译理论上可行，但当前缺少cmake/gfortran/bison/flex及所需Trilinos开发环境，且[Xyce不承诺完整SPICE方言兼容](https://xyce.sandia.gov/documentation-tutorials/frequently-asked-questions/)。不能把换工具当作已验证修复。TI没有在该产品页提供可核实的原生Linux/TINA模型替代品。

## 重现与边界

A1实验在目录内用对应ngspice执行 `ngspice -b test.cir`，需启用ps模式及官方analog/xtradev代码模型。保留的绝对模型路径是本次运行的真实路径；在别处重现时改为本地已校验模型路径。44.2包装器为 `/workspace/tools/bin/ngspice-44`，47为 `/workspace/tools/bin/ngspice-47`。minimal-profile是共享库驱动的早期最小测试，完整调用输出在日志中。

ngspice47来自Debian官方 `https://deb.debian.org/debian/pool/main/n/ngspice/ngspice_47+ds-1~bpo13+1_amd64.deb`。所有软件/模型均直接访问官方来源；没有绕过域名限制或第三方转发。本次追加工作没有推送。
