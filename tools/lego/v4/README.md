# 四臂整机 v4（反向连杆＋推杆导向）

在 v3 的“双侧轮胎压头＋防翻折限位”版（提交 `b9aa5d5`）上修改：十字接头移到连杆前方，往后拉夹紧、往前推张开；推杆导向为一个 39793 连接块，卡在转盘上半两个凸耳之间（4 根蓝色长销同时连接侧板、凸耳和导向块）；转盘下半用 6 根蓝色长销从框架外侧固定；侧板内侧梁中段让给连杆；导向框和舵机回到最初位置（前移 2 孔），推杆改为一根 12 号轴（只用导向框前孔）；舵机侧名义夹紧点在曲柄折叠死点前 25°，舵机连杆改用 7 孔粗梁第 1、7 孔。机械头长度、底座、竖墙、马达不变。v1、v2、v3 目录都不改。说明与验证结果见 `docs/lego/v4/README.md`。

| 文件 | 作用 |
| --- | --- |
| `model.py` | v4 模型：模块、底座、四个模块的摆放、搭建步骤 |
| `run_check.py` | 单模块夹紧／松开／中间行程与整机的干涉、连接、装配顺序检查，问题数为 0 才算通过 |
| `four_arm.py` | 四臂转动干涉扫描和魔方扫掠间隙 |
| `mesh_clearance.py` | 81 个开度的三角网格检查，以及 288 个回转姿态对邻臂的检查 |
| `mechanical_audit.py` | 曲柄与推杆、连续回转包络、后部避让 |
| `verify_pressure_pads.py` | 压头避让与用量（压头未改） |
| `booklet.py` | 生成 `docs/lego/v4/` 说明书（渲染用 `../render/`） |
| `assembly_instructions.py` | 按真实模型零件生成乐高式分步装配卡片（`docs/lego/v4/img/assembly/`，123 张），并校验每个零件恰好装一次；`booklet.py` 渲染后自动调用 |

```bash
cd tools/lego/v4
python run_check.py
python four_arm.py
python mesh_clearance.py
python mechanical_audit.py
python ../render/server.py &
python booklet.py   # 需要 pillow；单独重生成分步图：python assembly_instructions.py [--step 14]
```

- 基准版的 `verify_open_stops.py` 按旧连杆方向计算翻折点，不适用于 v4，未复制。
- `mechanical_audit.py` 的曲柄检查改为按无限长推杆计算径向余量（夹紧时曲柄朝后折叠，超出推杆后端），`verify_pressure_pads.py` 的推杆断言改为一体 12 号轴：只要求导向框前孔和舵机侧十字块在推杆范围内。
- 渲染需要 Playwright 和版本匹配的 Chromium。`render.js` 读取 `PLAYWRIGHT_MODULE`；本机浏览器版本不匹配时，可以临时给 `chromium.launch` 传 `executablePath`。
