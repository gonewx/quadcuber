# A1 direct-boot-precision-v1 独立审阅

2026-10-12；审查工作树相对HEAD `2d01805`及外部完整快照。最终PCB SHA256：`aa17fa9b22cc113f423552e96b39004e5b6b77cb64c0e49f54233de939642a5a`。结论：未发现尚未解决的重要实现问题，可完成本地修订；不是制造放行或动态验收。

## 已解决发现

- `electronics/circuit.py`末尾placement映射仍覆盖C22/C32新坐标，且保留已删除R20/R30位置。已由主代理新增测试复现RED，再修正最终映射至C22=(48,41.9)、C32=(97,41.9)、0°（PCB坐标整体+50mm），删除过期R映射。独立重跑源测试4/4 GREEN；PCB坐标分别(98,91.9)/(147,91.9)。见placement-red.log、source-tests.log。
- 全板zone refill改变了远离buck的旧填充缓存；仅区域边界相同不足以声称填充铜完全相同。已用同版本基线重填对照区分，结果如下。报告应保留此限制。
- 旧历史报告的重现命令指向现已更新的runner；当前simulation README已增加旧commit隔离重现说明，历史证据本身不改写。

## 独立核验

- 比较导出网表语义：仅R20/R30四端点删除、C22.1/C32.1由BOOT_CAP改BOOT；其他引脚网络不变。两路BOOT分别仅含U2.6/C22.1和U3.6/C32.1，电容另一端为各自SW，无BOOT–SW直接同网错误。
- 阻值仍100k/13.3k；源、JSON、BOM、网表使用RT0603BRD07100KL/RT0603BRD0713K3L。KiCad原生读取PCB确认四只反馈电阻隐藏MPN也正确，字段保持隐藏。
- PCB位置/角度/层/焊盘几何与网络差异仅两只电容移动与两只电阻删除；铜对象增删限两路BOOT/BOOT_CAP/SW和A路FB，共同UUID铜仅B路两GND过孔及其两条引线移动。其他2557个走线/过孔对象保持；区域边界、板框、层数保持。参见layout-comparison.json。
- BOOT各3.28655mm、零过孔；SW电容支路各5.59461mm、零过孔，原0.8mm芯片至电感主干保留。A路FB背层两过孔用于避让，B路FB不变。已目视layout-before-after.png；未发现悬空电容、错误短路或不必要BOOT过孔。
- 独立执行源4项及仿真14项单测通过。读取最终pcb-drc.json：violations、unconnected_items、schematic_parity均为0。源/PCB交叉检查与新版PSpice静态文件哈希已核实指向当前文件。
- 与外部快照逐文件比较时，既有生成仿真证据无修改或删除，旧PSpice与WEBENCH证据保留；旧提案仅追加批准状态。新版静态交接没有借用历史动态成功结论。

## Zone fill定量对照

复算脚本：[review-zone-fill.py](review-zone-fill.py)；实际结果：[review-zone-fill.json](review-zone-fill.json)。KiCad10.0.7读取原始快照，在内存中对原板执行与修订相同的ZONE_FILLER，不保存原板或正式板。逐UUID区域比较同层filled polygons，双向BooleanSubtract，再用整数坐标shoelace计算每个差异外多边形面积；不扣holes，故为该多边形面积上界。

局部窗口A：x=90–104、y=80–96mm；B：x=139–153、y=80–96mm。窗口外未发现单个差异多边形面积大于`1e-6 mm²`；VIN、VIN_FUSED及3V3区域在同版本重填后差异归零。窗口外剩余微小细片推断为整数布尔/曲线离散数值残差，不宣称逐字节相等。阈值针对单个多边形，不是累计残差总面积上限。

复算：

```sh
XDG_CONFIG_HOME=/tmp/kicad-review-config /workspace/tools/kicad-10.0.7/squashfs-root/AppRun python3.11 generated/electronics/boot-direct-revision/review-zone-fill.py /workspace/a1-boot-baseline/electronics/quadcuber.kicad_pcb electronics/quadcuber.kicad_pcb
```

## 未覆盖边界

几何和静态契约不能证明开关耦合、稳定性、EMI、温漂、实物BOOT电压或启动/负载瞬态。宏模型动态完整验收、器件实际偏压容量、热和EV3等既有HOLD继续保留；制造仍NOT RELEASED。最终build后的文本重导出由主代理完成，PCB未再变化。
