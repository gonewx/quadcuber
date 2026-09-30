# 用 Uno 和 Bricktronics Motor Driver 交叉检查编码器

> 独立排障工具：用于 Uno＋Bricktronics 测试台，不属于当前 Pico 接线方案。当前接线及实测状态见[电路总览](wiring/README.md)。

适用器材：5V Arduino Uno、带两个 LEGO 插座及 EN/DIR/PWM/T1/T2 标识的 Bricktronics Motor Driver、一只 EV3 大马达、一只中马达、至少两根完整 EV3 线。

目标：用同一测试台对比马达、线缆及接口。只检查编码器供电、信号和正交顺序，不检查电机带载能力或闭环性能。两只未知状态的马达都失败时，不能直接断定两只都损坏。

## 1. 接线（只做一次）

先断开所有电源。旧 Pico、BSS138、DRV8833 和原剪线支路均不参与这次测试。选两根**两头插头完整**的 EV3 线，标记 C1、C2。

| Bricktronics 板 | Uno / 处理 |
| --- | --- |
| VCC | Uno **5V**，不是 VIN，也不是 3.3V |
| GND | Uno GND |
| VM（两个同名针） | 留空，不接 9V，也不接 Uno 5V |
| 端口 1 的 T1 | Uno 数字 **D2** |
| 端口 1 的 T2 | Uno 数字 **D3** |
| 两个端口的 EN | 都接 GND，禁止驱动 |
| 两个端口的 DIR、PWM | 都接 GND，固定逻辑输入 |

只把一只马达用完整线插到端口 1。Uno 用 USB 供电；5V 只供板上逻辑和编码器，不供电机转动。轻缓手转输出轴，不用电钻或外部动力高速反拖。此时马达不会被程序主动驱动。

同名 GND 可通过面包板公共地连接；多个 VM 不接。不要凭排针左右位置猜顺序，以板上丝印为准。

厂家说明支持 EV3、大/中马达编码器反馈及 5V 微控制器。[产品说明](https://www.wayneandlayne.com/projects/bricktronics-motor-driver/)

v2 原理图显示：VCC 接马达插座 4 脚，GND 接 3 脚，T1/T2 直接引出 5/6 脚，没有外部信号上拉或电平转换。因此可接 5V Uno 的高阻数字输入；本测试不使用 `INPUT_PULLUP`。马达驱动的 VM 与编码器 VCC 是不同电源网络。[厂家原理图](https://www.wayneandlayne.com/files/bricktronics/motor_driver/bricktronics_motor_driver-schematic-v2.png)

## 2. 上传和读取

程序：[ev3_encoder_test.ino](../firmware/uno/ev3_encoder_test/ev3_encoder_test.ino)。无需额外库。

1. Arduino IDE 打开上面的 `.ino`。
2. 选择实际 Uno 型号和对应串口。已编译验证的目标为经典 Uno（ATmega328P），FQBN 为 `arduino:avr:uno`；若是 Uno R4 则选择实际 R4 板型。
3. 上传，打开串口监视器，波特率 **115200**。
4. 保持静止约 2 秒，然后连续缓慢朝一个方向转轴约 5 秒，再反向约 5 秒。

无需在串口输入命令，也不要粘贴 Python 或 `mpremote` 命令。

命令行编译示例（只编译，不自动上传）：

```bash
arduino-cli compile --fqbn arduino:avr:uno firmware/uno/ev3_encoder_test
```

输出格式示例（不是实测数据）：

```text
A=80 B=80 bad=0 delta=160 pos=160 state=00
A=76 B=76 bad=0 delta=-152 pos=8 state=00
```

- `A`、`B`：这一秒的两路电平变化次数。静止时为 0 正常；持续转轴时两路都应有变化，数量大致相当。
- `bad`：采到两位同时变化的次数。低速干净信号应为 0；持续增加要考虑接触、电气噪声或采样跟不上，不能直接判定马达坏。
- `delta`：这一秒的带方向计数；同向连续转时主要保持同号，反转后变号。
- `pos`：累计计数。手动来回转可能抵消，不能只看这个数字。
- `state`：打印瞬间的 A/B 状态，不需要等待某个固定值。

程序在两根输入上使用 CHANGE 中断。Uno D2/D3 支持外部中断。[Arduino 文档](https://docs.arduino.cc/language-reference/en/functions/external-interrupts/attachInterrupt/)

## 3. 最少交叉试验

每次换线、马达或板端口都拔掉 Uno USB，换完再上电。每组保存静止、同向转动、反向转动各几行；不要要求两只不同型号马达转相同手动角度就必须产生相同次数。

先保持端口 1：

| 编号 | 马达 | 线 | 记录 |
| --- | --- | --- | --- |
| T1 | 大 | C1 | A/B、bad、delta 是否正常 |
| T2 | 中 | C1 | 同上 |
| T3 | 大 | C2 | 同上 |
| T4 | 中 | C2 | 同上 |

- 某根线对两只马达均失败，另一根均成功：故障定位到该线缆或其插头接触，不能仅凭通断排除。
- 某只马达用两根线均失败，另一只均成功：故障定位到该马达总成（包括插座和内部编码器），不能进一步区分内部元件而不拆机测量。
- 四组都成功：这些完整线及两只马达的编码器在此测试条件下正常；原 BSS138/剪线/转接路径需要修订。
- 四组都失败：测试台尚未建立正常基准，优先检查板上供电、读数程序和端口，不能同时判坏马达和线。
- 只有某一组异常：重复插拔后复测，可能是特定插头配合或间歇接触问题，暂不下结论。

若需区分端口：断电，将同一马达、同一线移到端口 2，同时把接 Uno D2/D3 的两根线从端口 1 的 T1/T2 移到端口 2 的 T1/T2；其他接法不变。只有一个端口持续异常时查该端口及其接点。

已经剪开的线不能直接插入本测试台；只有复现它的原转接链路才能单独验收它，不能把“完整备用线通过”写成“原剪线也通过”。

## 4. 当前验证状态

Uno 程序完成经典 Uno 编译检查；主机测试调用同一份解码函数，覆盖正转、反转、单相抵消、非法跳变及重复状态。还没有上传到用户的 Uno，也没有取得实物交叉试验结果。
