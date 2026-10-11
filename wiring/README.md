# 接线源码

`spec.py` 保存唯一引脚规范；`direct_wiring.py`、`perfboard_layout.py`、`build.py` 生成 R 单臂、条件式 R+L 及可选洞洞板图纸。标准输出为 `generated/wiring/`，人工说明在 `docs/`，独立 R 回归基准在 `tests/fixtures/`。

```bash
python wiring/build.py
python wiring/build.py --check
python -m unittest tests.test_wiring -v
python wiring/check_browser.py --screenshots /tmp/wiring-review
```

构建同时校验固件配置并更新文档中的受控引脚区域。PNG 如需更新须显式使用 `--export-png`。R+L 的适用条件和安全限制见 [接线说明](../docs/wiring/README.md)；目录移动不代表新硬件验收。
