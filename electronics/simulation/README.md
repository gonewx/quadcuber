# A1 电源仿真与边界分析

> 最新Linux诊断：Xyce原生运行了18项A1预初始化动态工况（轻载/工作负载各9），15项数值中止、3项超时，0完整完成/0通过。延长原参考发现时钟兼容异常，不能将800µs完成当周期稳态验证。详见[完整证据与停止点](../../generated/electronics/simulation/linux-steady-followup/README.md)。冷启动和制造验收仍阻塞。

> 历史基线：这些65工况对应F1/母线泄放修订之前的板。当前修订结果以 `generated/electronics/protection-analysis/report.md` 为准。
对象：PCB SHA256 `6744d5985d91ce30513bbd1519a60979390d3df1fe49eee5f9bb2e0b84a96c2d`，基于提交 `0623d035d1f25a2090b16c538a17157a3c693715` 的实际BOM。

**新增原厂模型验证：TI未加密模型已取得，ngspice44.2已运行9个实际双路BOM输入/电容工况，但全部在启动期间数值中止，0完成/0通过，尚未执行到负载阶跃。** [本轮报告、波形与日志](../../generated/electronics/simulation/buck-vendor/report.md)。历史65简化模型与108保护分析不能替代芯片动态验证。

[结果及限制](../../generated/electronics/simulation/report.md) · [机器状态](../../generated/electronics/simulation/run-status.json) · [模型来源](model-sources.json)

## 重建

依赖：ngspice44.2、Python3.12、numpy2.3.5、matplotlib3.10.8。Debian trixie提供ngspice44.2；可安装系统包，或`apt-get download ngspice`后`dpkg-deb -x`解压，无需全局安装。许可证副本见`ngspice-copyright.txt`。本次实际命令：

```sh
python electronics/simulation/run_boundaries.py --ngspice /tmp/eda/sim/toolchain/usr/bin/ngspice
```

结果写入`generated/electronics/simulation/`。每个case保留完整`test.cir`、ngspice日志和`waveform.txt.gz`（首列秒，后列标题含单位对应物理量）；`gzip -dc waveform.txt.gz`解压。网表可直接`ngspice -b test.cir`单独重跑，生成未压缩波形。汇总CSV、PNG及源哈希随之重建。脚本拒绝未完成/非有限波形，独立校验电容电荷及总能量守恒；不会使用旧波形冒充本次结果。

## 原厂降压模型：已取得，数值兼容仍阻塞

TI官方入口同域重定向slvmbl9a.zip，ZIP CRC通过，未加密LIB原SHA256为`52a568f08f1eed44961238a1ff10b68c2ce1faa1cdf2c24659b17b1f820f0026`。原厂模型本体不随Git再分发；保留版权与免责声明，未推断额外分发许可。

```sh
python electronics/simulation/run_buck_vendor.py --model /absolute/path/TPS54302_TRANS.LIB --ngspice /path/to/ngspice
python electronics/simulation/report_buck_vendor.py
python -m unittest discover -s electronics/simulation -p test_buck_vendor.py
```

原厂脚序BOOT/EN/GND/PH/VIN/VSENSE已显式核对。ngspice启用ps兼容与官方analog.cm/xtradev.cm；源码只保留一处经真值表验证的逻辑异或语义适配（PSpice `^` → 带括号的布尔`!=`），补丁/转换前后哈希/未采用实验见报告。未删除保护或修改芯片参数以制造通过。原模型内部EN初值节点映射警告仍完整保留。

实际矩阵为两路同时启动：VM 0→8.82/9/9.18V、1ms上升；陶瓷电容有效容量系数0.4/0.8/1.2；A/B空闲0.25/0.05A，12ms升至1.5A、18ms恢复，目标25ms。真实BOM为10µH、DCR21.4mΩ典型、44µF标称输出、100k/13.3k、75pF、BOOT49.9Ω/100nF、EN511k/105k，C26/C36默认DNP。输出ESR3mΩ和0.4容量系数为明确假设，不是器件保证。

VM由理想PWL电压源直接驱动，输入10µF/100nF与其并联；因此改变输入电容不能验证VM纹波、输入源阻抗或输入电容动态容差。该矩阵仅尝试输入电压和输出有效电容敏感性，后续必须加入有依据的电源/线束阻抗及输入电流测量。

九个工况均在0.458～0.779ms发生`Timestep too small`；保存完整日志及部分波形，进程虽返回0仍正确判失败。尚未到10ms启动验收点和12/18ms负载跃变，不能给出这些阶段的有效结果。阈值为10ms前达到4.75V、10ms后4.75～5.25V、全程最高≤5.25V、电感绝对峰值<6A。数值失败不证明实际PCB电路失效；需要TI支持的PSpice对照或进一步有依据的宏模型移植。

## 模型层级

- ngspice原厂模型：9个实际双路BOM工况已启动运行，0个完整完成、0个通过；无负载阶跃通过结论。
- ngspice边界电路：65个实际运行。理想单向入口/肖特基线性近似、SMBJ12A端点线性拟合、电容充放电；没有LM74700控制延迟、MOS栅极、电源电感、TVS热失效、USB数据线或实际马达机电模型。
- 代数损耗/温升：参数扫描；不是ngspice热网络，更不是3D热有限元。电源芯片热模型缺失，不能将它解释为板级实测温度。

当前不因数值失败或简化边界结果直接改板：先解决原厂模型动态兼容，并确认供电限流/线阻和回灌能量。现有TVS不能当持续制动耗能器；若实际回灌超出脉冲能力，需制动电阻/有源泄放及相应铜区，单纯加电容无法解决持续回灌。

## Windows/PSpice 对照移交

[最小移交包](pspice-handoff/README.md)：官方原工程获取/运行步骤、九份未运行的PSpice格式A1网表、工况与回传表。全部标为NOT_RUN，不代表Windows工程已验证可运行。
