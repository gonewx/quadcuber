# 模型工具链实验记录

原LIB SHA256：52a568f08f1eed44961238a1ff10b68c2ce1faa1cdf2c24659b17b1f820f0026。
TI ZIP SHA256：d06e58535f99c35ee5da259e68c09c471b819d00c2fe98d4d5d1da49ea730f77。

- original.log：共享库初始缺代码模型，无法加载。
- original-with-codemodel.log：analog.cm不足；所需pswitch在xtradev.cm。
- original-with-xtradev.log：模型加载成功，自选12V基线在0.654881ms失败。基线不是原厂DSN导出、不是A1。
- gear.log：同基线Gear在0.209081ms附近停滞，手动终止。没有产生有效完成数据。
- a1-original-nominal：真实BOM的未修改原模型，Trap失败。
- a1-gear-nominal：真实BOM的未修改原模型，Gear失败。
- a1-n1e-3-nominal：仅D_D二极管理想因子放宽，未解决；弃用。
- xor-native/adapted：四组合独立真值表，确认^为幂运算，!=才实现所需异或。
- a1-xor-nominal：修正异或后的真实BOM，仍数值失败；该语义修正保留在正式9工况。
- a1-smooth-nominal：异或修正并平滑SDWN低端钳位，未解决；弃用。

实验子目录仅保存历史元数据、网表、日志及部分波形；原厂LIB及实验LIB没有随Git分发。各次模型SHA已记录，补丁用于复核。历史run-status中的state/error沿用当时工具，不能把state字符串或进程0返回码视为通过。所有实验均未完成完整25ms动态验收。原始共享库脚本曾误在未达到5ms时调用meas并收到0值，这些测量明确无效；正式工具已拒绝这种情况。

正式矩阵及最新结论只看上级run-status.json和report.md。当前环境安装入口 /workspace/tools/bin/ngspice-44；依赖Debian官方ngspice_44.2+ds-1_amd64.deb。共享库与CLI均44.2。