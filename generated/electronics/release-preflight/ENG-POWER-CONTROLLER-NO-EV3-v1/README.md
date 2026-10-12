# ENG-POWER-CONTROLLER-NO-EV3-v1

**仅用于电源/控制器台架验证的候选装配变体，未制造放行、未下单。**

- BOM与CPL各167项，位号集合已自动核对相等。
- 明确不装：J10、J11、J12、J13、C26、C36。不可用上级目录171项完整装配表替代本变体。
- 功能PCB仍为基线 `da5fc42b5e0c6352c827f9ae905eb891fe0dd12b`；未改任何孔位、铜形、器件网络。精确哈希及文件清单见 `manifest.json`。
- 不接电机、舵机或编码器。先用9V受控限流电源、0.5A初始限流、无外接负载检查；后续电子负载遵守上级 `power-review.md` 的分级测试。
- USB连接时主机须有有效VBUS；主机关机前拔线。使用已验证的A1专用UF2。
- 嘉立创局部DFM缺口仍须处理；本变体只消除EV3装配/接线的不确定性，不会使原PCB自动满足制造规则。
- EV3实物针序可暂缓核验，但这批板不能用于EV3功能声明；如果核验结果与原图推导不同，仍可能需要改板。

重建：`python generated/electronics/release-preflight/prepare_no_ev3_variant.py`。重建脚本锁定PCB哈希，禁止对未知新板静默沿用此装配选择。
