# 机械源码：542 步 / 938 件

[整机 3D](../generated/site/index.html) · [逐步组装](../generated/site/integrated-assembly.html) · [542 页 PDF](../generated/mechanical/manual/manual.pdf) · [BOM](../generated/mechanical/final-BOM.csv)

`candidate.py` 为当前模型实现，`inputs/` 保存冻结输入与来源，`parts/` 保存所需零件定义，`assembly/` 保存装配配方、生成器和检查。唯一标准输出位于 `generated/mechanical/`，不应手工修改。GitHub 管理源码，Sites 仅接收构建产物。

整机为 120 件闭环底盘、668 件四臂、150 件支承，含 20 件重力复位杠杆。每臂 88 步，完整说明从单件开始覆盖 938 个实例。11个模型状态、542页PDF和120件底盘图解已随本次加固更新；四臂与150件支承几何保持原版。历史冻结证据保留，新版证据见generated/mechanical/release.json。

在仓库根执行：

```bash
python -m pip install -r mechanical/requirements.txt
python mechanical/build_candidate.py
python mechanical/generate_inventory.py
python -m unittest discover -s mechanical/assembly -p 'test_*.py' -v
python tools/check_rebuild.py
```

模型和清单可用 `QUADCUBER_MECHANICAL_OUTPUT=/绝对路径` 指定隔离输出。手册重渲染是显式维护操作，不能为普通路径整理覆盖已验证的 PDF／图解；运行前使用独立检出及隔离输出，先读 `assembly/REBUILD.md`。历史命令与 provenance 中原路径仅作为来源记录。

上位须持续按住外柄，夹头接管后缓松回落 40.8 mm。CAD 与软件验证不能证明实物装配、承载、插入力、防脱、冲击、手部隔离或带电联锁安全；控制标定和接线继续遵循原有安全说明。
