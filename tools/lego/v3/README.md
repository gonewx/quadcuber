# 四臂整机 v3（按 CubeStormer 3 的思路重新设计）

v1（上一级目录）和 v2（`../v2/`）都保持不动。本目录是四臂整机 v3，说明书在 `docs/lego/v3/index.html`。评估结论和设计推导见 `docs/lego/v3/README.md`。

| 文件 | 作用 |
| --- | --- |
| `model.py` | v3 模型：一个机械手模块（模块坐标）+ 底座 + 四个模块的摆放，搭建步骤和关键尺寸 |
| `run_check.py` | 单模块夹紧/松开、夹指中间行程、整机的干涉和连接检查（复用 `../check.py`），问题数为 0 才算通过 |
| `four_arm.py` | 四臂转动干涉扫描（相邻臂 16 种状态组合 × 每 5° 一格）和魔方扫掠间隙 |
| `mechanical_audit.py` | 连续回转包络、后部避让与薄梁受力估算 |
| `mesh_clearance.py` | 81 个开度的新增件 FCL 检查，以及 288 个新前端回转姿态的网格外包盒／FCL 检查 |
| `verify_open_stops.py` | 独立旋转主臂检查挡止、双解与截面方向敏感性 |
| `test_open_stops.py` | 无实体限位和允许超程的回归检查 |
| `test_dual_support.py` | 双侧贯穿轴与后部两处旧碰撞的回归测试 |
| `booklet.py` | 生成 `docs/lego/v3/index.html`、步骤图和 `model.ldr`（渲染用 `../render/`） |
| `assembly_instructions.py` | 生成179张分步装配图及公共轴叠层示意，核对新增件与模型清单 |

## 更新分步图

分步图使用模型的真实 LDraw 网格，浅色为已装件、实色为本次加件。图中爆炸平移只用于解释装配方向。前23个主步骤有分步图，第24步放魔方保留整机图；主步骤编号与3D查看器不变。

```bash
tools/lego/.cache/venv/bin/python tools/lego/v3/assembly_instructions.py --check
tools/lego/.cache/venv/bin/python tools/lego/v3/assembly_instructions.py
tools/lego/.cache/venv/bin/python tools/lego/v3/booklet.py --no-render
```

生成器默认使用3个渲染进程；`--workers 1`可降低并行开销。只调整图解时可用`--step 19`重画该步。模型改变后须全量生成，不能合并旧模型的图。SVG自包含，网页支持点击放大、手机浏览和打印；`assembly.json`记录小步骤、零件数量和模型指纹。渲染缓存放在`tools/lego/.cache/assembly/`。

```bash
cd tools/lego/v3
python run_check.py          # 约 1 分钟
python four_arm.py           # 约 1 分钟
python ../render/server.py &
python booklet.py
```

**改模型后必须运行 `run_check.py`、`four_arm.py`、`verify_pressure_pads.py`、`mesh_clearance.py` 和 `mechanical_audit.py`。** 后部连续回转检查已加入 `run_check.py`；`mesh_clearance.py` 补查新增件附近的三角网格。审查报告在 `docs/lego/v3/mechanical_audit.md`；实物刚度另行验收。`four_arm.py` 仍用于筛查邻臂竖直/水平状态，保留 `no_adjacent_horizontal` 约束。
