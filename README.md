> 机械结构已基本定型为 **v4 四臂整机**（反向连杆拉紧、转盘内 39793 导向、竖墙与舵机侧加固，已合入主干 `main`）。
> [图文搭建说明](docs/lego/v4/index.html) · [设计与改装说明](docs/lego/v4/README.md) · [零件清单](docs/lego/v4/bom.csv) · [库存记录](docs/lego/inventory.md)
> 当前机械模型与说明书以 `tools/lego/v4/`、`docs/lego/v4/` 为准；历史单臂原型与中间探索版本已归档至 [`docs/lego/archive/`](docs/lego/archive/)。


# quadcuber

四机械手乐高魔方机器人（参考 CubeStormer 3 的思路），目前包含**动作规划器**、**模拟器**，以及**单臂原型的 Pico 测试程序**。

* 规划器：把求解器给出的转动序列（如 `R U R' U'`）翻译成 4 个机械手的动作序列，并使总耗时最短。

* 模拟器：在 54 个贴纸的魔方模型上按物理动作逐步重放，检查每一步是否满足机械约束，以及最后魔方是否还原。

* 单臂测试程序（`firmware/pico/`，MicroPython）：测机械手转 90° 的耗时、到位精度和夹持可靠性，结果汇总后替换规划器的耗时估算值。接线和测试步骤见 [docs/single\_arm.md](docs/single_arm.md)，乐高机械手的结构思路和尺寸要求见 [docs/arm\_concept.md](docs/arm_concept.md)，**搭建说明书**见 [docs/lego/v4/index.html](docs/lego/v4/index.html)（四臂整机定型版，总入口 [docs/lego/index.html](docs/lego/index.html)）。

规划器纯 Python 实现，不依赖第三方库，可以在 PC 或树莓派 Zero W 上运行。

## 电路与硬件验证

从[电路总览](docs/wiring/README.md)进入：当前使用面包板＋动力直连，洞洞板是可选装配方案。EV3 大马达＋DRV8833 的空载闭环已通过，范围见[实测记录](docs/single_arm-results.md)；这不等于 v4 机械头、舵机、带魔方动作或四臂供电已验收。接下来需要实物标定和分级测试。

当前硬件：EV3 大马达、DRV8833（名义 9V，实测不得超过 10.8V）、每路 10kΩ/20kΩ 编码器分压（`ENC_PULLUP = False`）、灰色 270° Geekservo。调试时 Pico 由 USB 供电，舵机由独立 5V 降压供电，所有模块共地。接线以 `docs/wiring/spec.py` 及其生成图表为准。

固件的开／合端点及安全工作区间（`SERVO_OPEN_US`、`SERVO_CLOSE_US`、`SERVO_MIN_US`、`SERVO_MAX_US`）默认均为 `None`，`SERVO_CALIBRATED = False`。未完成实物标定时，普通动力命令会拒绝执行；仅在确认无魔方、机构全行程自由且供电接线已核验后，可显式进入 `motor_test unloaded` 做空载马达验证，该模式不允许舵机开合或带载测试。按[单臂标定步骤](docs/single_arm.md#servo-calibration)先脱开连杆、声明手动会话，再逐步测量舵机端点及安全区间，最后人工记录 `v4`／`R` 标定身份并启用标志。启动不发送舵机脉冲，但不能保证上电硬件不抖动；旧脉宽和 CAD 角度不能充当实测值。

舵机时序另行确认：默认 `SERVO_MOVE_MS = None`、`SERVO_TIMING_CONFIRMED = False`。端点、安全区间和身份确认后，人工选定保守的临时等待时长（1～5000ms 整数，不沿用旧 120ms），仅用单次 `open` / `close` 录像测量，确认完全停稳才发下一条。此时 `grip`、`cycle` 和普通旋转仍被锁定，显式空载马达模式是例外。实测完整开／合的较慢值加余量后回填等待时间、设置 `SERVO_TIMING_CONFIRMED = True`，上传并 Ctrl+D 重载，才进入连续及联合测试；机构或供电变化后重新确认。

```bash
python docs/wiring/build.py          # 生成全部电路文档及图纸
python docs/wiring/build.py --check  # 检查配置、网络和生成文件是否同步
```

## 机器模型

```
        B
        |
  L --[魔方]-- R      U 面朝上（留给摄像头），D 面朝下；这两个面没有机械手
        |
        F
```

* 4 个机械手分别位于 R / L / F / B 方向，每个机械手可以**夹紧 / 松开**，也可以**旋转**（90° 的整数倍）。
* 夹爪是一根横跨面中间一行或一列的“夹条”。机械手角度为偶数（包括 0）时夹条竖直，为奇数时水平。
* 约束（实现见 `quadcuber/machine.py` 的 `Machine.check`）：
  1. **支撑**：任何时刻 L、R 都夹紧，或 F、B 都夹紧，否则魔方会掉落。
  2. **拧面**：拧某个面时，与它垂直且夹紧的机械手，夹条必须竖直，否则会挡住转动；并且至少有一个这样的机械手夹紧，用来固定中间层。相对的两个面可以在同一步同时拧。
  3. **整体翻转**：一对机械手夹紧并同向旋转，把 U/D 面换到有机械手的位置；此时另一对必须松开。
  4. **空转**：松开的机械手可以旋转来调整夹条方向，并且可以和其他动作同时进行。
  5. **相邻臂避碰（v4 必须）**：相邻两臂不能同时水平；任一臂旋转时，相邻两臂必须保持竖直且不在同一步旋转。拧面、空转、整体翻转以及经过水平位置的 180° 动作都适用，松开夹爪不能解除这条约束。
  6. **角度限制（可选）**：`angle_limit` 默认仍为 `None`。v4 舵机固定在平台上，不随机械头转动，不因舵机缠线强加角度上限。其他需要累计角度边界的结构可显式使用 `--angle-limit`。

`Machine()` 和 CLI 的 `plan` / `bench` 默认使用 `profile="v4"`，强制启用 `no_adjacent_horizontal=True`，不能在 v4 profile 下显式关闭。`Machine(profile="generic")` / `--profile generic` 保留旧抽象模型，仅供明确的非 v4 用途；generic 仍可用 `--no-adjacent-horizontal` 增加约束。规划器的检查不代替实物避让、刚度、保持力与耗时标定。

## 使用

```bash
# 规划一个转动序列，并在模拟器中验证
python -m quadcuber plan "R U R' U' F2 D"

# 同时输出 JSON，供下位机（Pico）执行
python -m quadcuber plan "R U R' U'" --json plan.json

# 随机 20 步序列的统计，--compare 同时对比“不做任何并行”的基准方案
python -m quadcuber bench --count 20 --compare

# 使用实测的动作耗时
python -m quadcuber bench --timing timing.json

# 仅用于非 v4 结构的旧抽象模型；不要用它驱动当前 v4
python -m quadcuber plan "R U R' U'" --profile generic
# generic 也可显式启用更严格的相邻臂约束
python -m quadcuber bench --profile generic --no-adjacent-horizontal
```

`timing.json` 的字段见 `quadcuber/machine.py` 中的 `Timing`，单位为秒。**默认值是估算值**，搭好单臂原型后应替换成实测值（可以用 `python -m quadcuber armlog arm.log -o timing.json` 从单臂测试日志生成）：

```json
{"turn90": 0.18, "turn180": 0.30, "open": 0.10, "close": 0.10,
 "rotate90": 0.15, "rotate180": 0.25, "cube90": 0.22, "cube180": 0.35}
```

## 规划算法

* 在（已完成的转动，机器状态）空间中做 A\* 搜索，代价为总耗时。每一步是一组同时执行的动作。
* 连续的同轴转动（例如 `R L'`）会合并为一组，可以按任意顺序执行，也可以同时执行。
* 默认使用**滚动窗口**：每次对接下来的 4 组转动求最优，只采用前 2 组的动作。实测比全局最优（`--full`）只慢 1~2%，但速度快得多。
* 有角度限制时，先按不限角度规划，再用动态规划选择旋转方向（必要时顺带退绕）；只有无法满足限制的窗口才做完整的受限搜索。

历史旧抽象模型在开发机上的测量（30 个随机 20 步序列、估算耗时参数，未包含当前默认的 v4 相邻臂约束；不是 v4 实物数据）：

| 情况 | 动作总耗时（平均） | 规划 CPU 时间（平均） |
| --- | --- | --- |
| 不限角度 | 7.9 s | 0.8 s |
| 角度限制 ±180° | 8.0 s | 11 s |

角度受限时规划仍然偏慢，树莓派 Zero W 上预计还要慢一个数量级。建议优先采用不需要角度限制的夹爪结构。

## 测试

```bash
python -m unittest -v
```

测试覆盖：魔方模型、各条机器约束，以及随机序列经规划后能在模拟器中还原；Pico 固件在模拟环境（马达模型 + PIO 解释器，`tests/pico_sim.py`）中的编码器计数、位置控制和各条测试命令；日志汇总工具。

## 目录

| 路径 | 内容 |
| --- | --- |
| `quadcuber/cube.py` | 贴纸魔方模型、转动记号解析 |
| `quadcuber/machine.py` | 机器状态、动作、约束、耗时参数 |
| `quadcuber/planner.py` | 动作规划器 |
| `quadcuber/simulate.py` | 模拟器 / 验证 |
| `quadcuber/armlog.py` | 单臂测试日志汇总，生成 `timing.json` |
| `quadcuber/__main__.py` | 命令行 |
| `firmware/pico/` | 单臂测试程序（MicroPython）：配置、PIO 编码器、马达/舵机驱动、位置控制、串口命令行 |
| `docs/single_arm.md` | 单臂原型的接线、测试步骤和待验证假设 |
| `docs/arm_concept.md` | 乐高机械手的概念设计：叉子 + 滑块结构、关键尺寸、单臂测试的魔方固定方法 |
| `docs/wiring/` | 单臂原型的图解接线指南（`build.py` 生成 `index.html`，内嵌 SVG） |
| `docs/perfboard.md` | 可拔插洞洞板设计：逐孔安装、镜像焊接图、模块排针座及上电验收 |
| `docs/lego/` | 乐高搭建说明书与模型文档：当前四臂整机定型版见 `v4/`（[说明书](docs/lego/v4/index.html)），历史单臂原型与探索方案归档于 `archive/` |
| `tools/lego/` | 搭建图工具：模型定义、干涉/连接检查、渲染（见其中的 README） |
| `tests/` | 单元测试 |

## Prompts

* gpt-6-astra high

现在的设计还是不理想, 设计结构复杂,但实际效果看着也不行. 我有思路需要你评估和验证: 需要在上一版本整体结构上主要优化方向是推杆到夹指的传力,要能将舵机的力量传递到夹指前端, 而不是像现在这样中间的连接是无摩擦销,导致力量无法传递, 所有现在的夹指整体的平行的设计理念 ,也导致总是间隙, 因为乐高结构和尺寸决定了现在这样的设计必然无法夹紧. 所以夹紧状态应该是现在的夹指部分不用完全 平行于魔方, 但夹指前端必须有新的结构件能自然贴合魔方, 达到夹紧的效果.
