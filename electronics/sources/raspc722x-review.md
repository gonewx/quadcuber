# J1 RASPC722X 本地候选审查

基线：PCB 分支 `cf614f3de777b39048b341b3983abcfe7e7962f3`。本地候选，未放行制造。

## 图纸来源与边界

原图为 [Switchcraft RASPC722X_CD.pdf](https://www.switchcraft.com/assets/1/24/RASPC722X_CD.pdf?11475=)。本执行环境正常请求得到 212 字节防护 HTML；没有绕过。用户 Library 文件 `libfile_90ad2441d4ac8191beef0790a5ac6bb1`、`RASPC722X_CD.pdf`、89153 字节，经官方材料化首次及一次本地目的重试均下载失败。

**尺寸依据是父线程对上述原件单页 2200px 渲染的视觉核验及其明确传递的数据，不是本执行环境直接看图。** 父线程已核实 `RECOMMENDED PC BOARD LAYOUT (COMPONENT SIDE)`、mating face/PCB edge、center pin / sleeve / sleeve shunt。原始 PDF 尚待本地归档；发布前再次通过官方 Library 材料化流程尝试，下载仍失败。该厂家图标明尺寸 reference only。

## 几何与项目引脚

以插口 mating face 为 y=0，center/sleeve 中线为 x=0，朝板内为 +y。英寸为控制值，下面 mm 是直接乘 25.4，并非从图中四舍五入的 mm 反推。

| 项目 pad | 接点与网络 | 中心 x,y / inch | 镀通槽 x×y / inch | 中心 x,y / mm | 槽 x×y / mm |
|---|---|---|---|---|---|
| 1 | center → VIN | 0,.541 | .140×.040 | 0,13.7414 | 3.556×1.016 |
| 2 | sleeve → GND | 0,.295 | .120×.030 | 0,7.493 | 3.048×.762 |
| 3 | sleeve shunt → NC | .189,.423 | .030×.120 | 4.8006,10.7442 | .762×3.048 |

1/2/3 是项目编号，不冒充厂家端子编号。铜焊盘在槽四周增加 0.254 mm 环宽。使用推荐槽，未采用 alternate 圆孔。封装原点就是 mating face；PCB 位置 `(95.5,50)`、0°，板顶边 y=50。相较最初位置向右 0.5 mm，避开 GP21 和 D2 courtyard。板框与其他器件不动。

父核外形：9.0 mm 宽、14.5 mm 深、11.0 mm 高，轴高 6.5 mm，中心针 2.0 mm，脚出 3.4 mm typ。Fab 矩形为名义本体；courtyard 包含伸出的 shunt 铜焊盘。实际插拔、线缆弯折、壳体开口及 PCB 背面引脚净空仍需机械样机核查。

## 配对、电流与保护

用户指定 5.5/2.1 mm、中心正、稳压 9 V、连续输入预算 ≤5 A。父核官方配对插头 762/762Z，5.5 OD、2.1 ID、9.5 mm 筒长；插座 2.0 mm 针不是“不兼容 2.1 mm 插头”的证据。父核厂家额定为 5 A carrying / 24 V；这不是大电流热插拔或整机连续温升认证。

J1→F1 的三段 1 mm 顶层 VIN 线改为两段 1.8 mm 顶层线，无新增过孔，同时局部调整 VIN 铜区。center/sleeve 使用实连接铜区，避免细热焊盘辐条作为唯一电流路径；sleeve 仍由镀通孔连接 GND 层。未使用的 shunt 有镀通焊盘但无铜线，原理图明确 NC。

原 F1 `0407008.WR` 8 A 时滞保险、U4 `LM74700QDBVRQ1`、Q1 `CSD18540Q5B`、D4 输入 TVS、D3 母线 TVS、母线电容与泄放电阻均保留。8 A 保险并不保证把插座电流限制在 5 A；继续要求限流 9 V 源及 ≤5 A 整机预算。1.8 mm 走线和 DRC 只证明几何连接，不证明接触电阻、焊接或连续温升合格。

## 复现与核验

运行 `revise_j1_input.py --baseline <基线>/quadcuber.kicad_pcb --output <候选>/quadcuber.kicad_pcb`。基线目录必须同时包含同提交的 `.kicad_pro` 和 `.kicad_dru`，否则 pcbnew 会使用默认规则。脚本仅执行本地布局修订；不调用全板生成器。KiCad CLI 和 pcbnew 必须为 10.0.7。

`circuit.py`、J1 符号库、power 原理图、PCB、circuit JSON、BOM 和接口丝印源已同步。`check.py` 独立检查极性、槽孔、环宽、位置、NC 和 VIN 最小线宽；`test_j1_source.py` 保留原保护网络合同。当前导出与证据在 `generated/electronics/j1-raspc722x-revision/`，提交与推送仅发布开发分支，不构成制造放行。
