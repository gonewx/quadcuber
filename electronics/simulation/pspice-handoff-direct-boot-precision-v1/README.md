# A1 direct-boot-precision-v1：当前PSpice交接

删除R20/R30；100nF C22/C32直接跨BOOT–SW。反馈阻值保持100k/13.3k，精确MPN分别RT0603BRD07100KL与RT0603BRD0713K3L，0.1%。这份网表不包含PCB走线寄生，不能验证自举布局。

九份网表全部 **NOT_RUN**，原厂PSpice语法尚未在Windows验证。静态契约核对源定义的两路IC脚序、自举端点、无BOOT_CAP中间网名、反馈端点和精确MPN；源/PCB哈希与网表哈希见static-validation.json。重建：

```sh
python electronics/simulation/prepare_buck_revision.py
python -m unittest discover -s electronics/simulation -p 'test_buck*.py'
```

原始TI未加密模型应独立从 https://www.ti.com/lit/zip/slvmbl9 获取，SHA256须为52a568f08f1eed44961238a1ff10b68c2ce1faa1cdf2c24659b17b1f820f0026；将原LIB置于运行工作目录。未再分发模型。PSpice使用未修改模型；ngspice脚本沿用已审查的一处XOR兼容修正。

与旧版相同的九工况：VIN=8.82/9/9.18V，1ms斜坡；容量系数0.4/0.8/1.2；A/B负载0.25/0.05A，12ms升到1.5A，18ms恢复，25ms结束。验收要求10ms前达到4.75V、10ms后不低于4.75V、全程不超过5.25V、|IL|<6A。输出ESR3mΩ与容量系数仍是假设，理想VIN不能验证输入阻抗/纹波。

反馈独立初始容差和Vref极限范围4.940693–5.214182V；这不是含温漂、老化、输入偏置、线/负载调节与瞬态的保证。SPICE网表仍用标称电阻，没有执行反馈容差扫描。

TDD记录：实施前四项新增测试均失败（缺少契约/共享网表生成函数）；源同步后14项仿真测试全部通过，包含共享生成、真实源契约与拒绝错误连接/料号检查。最终测试输出由总验证记录归档。

旧pspice-handoff九份网表、WEBENCH评审、旧Linux数值失败与部分波形原样保留，均不是本修订的动态结果。**完整原厂动态验收待完成；制造NOT RELEASED。**
