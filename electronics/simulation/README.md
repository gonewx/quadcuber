# A1 电源仿真与边界分析

> 历史基线：这些65工况对应F1/母线泄放修订之前的板。当前修订结果以 `generated/electronics/protection-analysis/report.md` 为准。
对象：PCB SHA256 `6744d5985d91ce30513bbd1519a60979390d3df1fe49eee5f9bb2e0b84a96c2d`，基于提交 `0623d035d1f25a2090b16c538a17157a3c693715` 的实际BOM。

**当前只完成65个简化电路瞬态工况及代数热扫描。TPS54302原厂模型尚未取得，原厂模型仿真次数为0。不能据此宣称双降压、四臂并发或PCB验证通过。**

[结果及限制](../../generated/electronics/simulation/report.md) · [机器状态](../../generated/electronics/simulation/run-status.json) · [模型来源](model-sources.json)

## 重建

依赖：ngspice44.2、Python3.12、numpy2.3.5、matplotlib3.10.8。Debian trixie提供ngspice44.2；可安装系统包，或`apt-get download ngspice`后`dpkg-deb -x`解压，无需全局安装。许可证副本见`ngspice-copyright.txt`。本次实际命令：

```sh
python electronics/simulation/run_boundaries.py --ngspice /tmp/eda/sim/toolchain/usr/bin/ngspice
```

结果写入`generated/electronics/simulation/`。每个case保留完整`test.cir`、ngspice日志和`waveform.txt.gz`（首列秒，后列标题含单位对应物理量）；`gzip -dc waveform.txt.gz`解压。网表可直接`ngspice -b test.cir`单独重跑，生成未压缩波形。汇总CSV、PNG及源哈希随之重建。脚本拒绝未完成/非有限波形，独立校验电容电荷及总能量守恒；不会使用旧波形冒充本次结果。

## 原厂降压模型：阻塞，未运行

官方模型地址：https://www.ti.com/lit/zip/slvmbl9 ，产品页标为SLVMBL9A、103KB、未加密PSpice瞬态。执行环境经下载代理访问ti.com、ti.com.cn及官方直链均403；日志保留在`model-download.log`。这是获取失败，**不是已证明ngspice不兼容**。不能绕过授权、解密模型或拿其他芯片模型替代。

模型可用后，先检查模型头部及许可，再运行：

```sh
python electronics/simulation/run_buck_vendor.py --model /absolute/path/TPS54302_TRANS.LIB --ngspice ngspice
```

该脚本目前仅通过Python语法检查，**未经过原厂模型运行验证**。它要求可识别的6脚原厂`.SUBCKT`，读取原始脚序，不猜测脚序；启用ngspice PSpice兼容模式，不擅自改变模型。任何语法/收敛错误都必须先审查原始模型并保存明确的适配补丁及哈希，不能删保护逻辑以制造“通过”。原厂文件未随仓库再分发，许可未检查。

预设矩阵：双路同时启动，VM 0→8.82/9/9.18V、1ms上升；A/B空闲负载0.25/0.05A，12ms同时升至1.5A、18ms恢复，结束25ms；有效陶瓷容量系数0.4/0.8/1.2，共9个双路工况。0.4为未知DC偏压效应的敏感性参数，非Murata特性保证。实际BOM：10µH，DCR21.4mΩ典型，44µF标称输出，100k/13.3k，75pF，BOOT49.9Ω/100nF，EN511k/105k；C26/C36默认DNP。输出ESR3mΩ是假设，尚需扩展L±20%、电容ESR、反馈电阻容差及源阻抗联合扫描。

接受准则：10ms后输出4.75～5.25V，启动全程最高≤5.25V、10ms前达到4.75V，全程电感峰值<6A。它只是正常启动/阶跃初筛，不证明相位裕量、OCP/OVP故障时序或温度边界。6A是故障限流上界参考，正常1.5A负载出现接近6A的结果还须逐波形调查。

## 模型层级

- 原厂模型：0个实际运行；没有把可下载链接等同于兼容验证。
- ngspice边界电路：65个实际运行。理想单向入口/肖特基线性近似、SMBJ12A端点线性拟合、电容充放电；没有LM74700控制延迟、MOS栅极、电源电感、TVS热失效、USB数据线或实际马达机电模型。
- 代数损耗/温升：参数扫描；不是ngspice热网络，更不是3D热有限元。电源芯片热模型缺失，不能将它解释为板级实测温度。

当前不因这些边界结果直接改板：先取得TPS54302原厂模型，确认供电限流/线阻和回灌能量。现有TVS不能当持续制动耗能器；若实际回灌超出脉冲能力，需制动电阻/有源泄放及相应铜区，单纯加电容无法解决持续回灌。
