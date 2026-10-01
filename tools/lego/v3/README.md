# 四臂整机 v3（按 CubeStormer 3 的思路重新设计）

v1（上一级目录）和 v2（`../v2/`）都保持不动。本目录是四臂整机 v3，说明书在 `docs/lego/v3/index.html`。评估结论和设计推导见 `docs/lego/v3/README.md`。

| 文件 | 作用 |
| --- | --- |
| `model.py` | v3 模型：一个机械手模块（模块坐标）+ 底座 + 四个模块的摆放，搭建步骤和关键尺寸 |
| `run_check.py` | 单模块夹紧/松开、夹指中间行程、整机的干涉和连接检查（复用 `../check.py`），问题数为 0 才算通过 |
| `four_arm.py` | 四臂转动干涉扫描（相邻臂 16 种状态组合 × 每 5° 一格）和魔方扫掠间隙 |
| `mechanical_audit.py` | 连续包络、后部碰撞复现与薄梁受力估算；当前模型有干涉，预期退出 1 |
| `booklet.py` | 生成 `docs/lego/v3/index.html`、步骤图和 `model.ldr`（渲染用 `../render/`） |

```bash
cd tools/lego/v3
python run_check.py          # 约 1 分钟
python four_arm.py           # 约 1 分钟
python ../render/server.py &
python booklet.py
```

**改模型后必须运行 `run_check.py`、`four_arm.py`、`verify_pressure_pads.py` 和 `mechanical_audit.py`。** 当前后部干涉已加入 `run_check.py`，不能再以旧离散检查 0 问题宣称通过。审查报告在 `docs/lego/v3/mechanical_audit.md`；实物刚度另行验收。`four_arm.py` 仍用于筛查邻臂竖直/水平状态，保留 `no_adjacent_horizontal` 约束。
