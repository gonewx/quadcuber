# A1 J5 嘉立创工艺适配实施证据

已实施用户授权的四个 S1 屏蔽槽焊盘扩大，并为闭合项目原有 **0.20 mm** 净距规则实施主线程明确授权的局部 USB_VBUS 避让。未放宽规则、改变孔位/孔径/槽长、改变线宽/网络或移动器件。未提交、推送、上传厂商或下单；主线程负责完整 build、审计整合及本地提交。

## 具体变化

- 两个长槽铜盘：1.000×2.100 → **1.108×2.208 mm**；孔保持 0.600×1.700 mm。
- 两个短槽铜盘：1.000×1.800 → **1.108×1.908 mm**；孔保持 0.600×1.400 mm。
- 名义环宽均为 **0.254 mm**。铜盘的既有 F.Paste/Mask 属性与扩展规则不变，尺寸跟随焊盘更新。
- 本地 `.kicad_mod` 最终严格只有四个 size 行变化，保留原文件格式、UUID、图形、丝印及模型信息。
- `generate.py` 在复制指定 USB4105 上游封装后调用 `adapt_usb_shield_slots_file()`，防止今后重生成恢复旧尺寸；本轮没有执行全板生成器。
- 仅五个既有 F.Cu / USB_VBUS / 0.15 mm 线段的三个共享节点向 +X 移动 **0.060 mm**，保留水平/垂直/45° 连接：

| 原共享节点 mm | 新共享节点 mm |
|---|---|
| (75.1185, 55.0496) | (75.1785, 55.0496) |
| (75.1185, 57.6593) | (75.1785, 57.6593) |
| (74.5457, 58.2321) | (74.6057, 58.2321) |

五段 UUID 为 `1c9cde93-6b13-45a4-931d-3873bbf8384b`、`798bdb25-1303-4523-bcb3-bd55121a7036`、`cc9f98a0-4228-4c78-8163-aa595ae3845c`、`d45ae99b-2573-4fd8-8747-c22624b25667`、`83e1a1c5-9865-47ec-8c64-46ecab0ba978`；完整前后端点见 `green.json`。

只扩大焊盘时，实际完整 DRC 找到相邻两段走线的 0.1695/0.1685 mm 净距不足本地 0.20 mm，虽然它们仍高于 JLC 多层 2 oz 的通用 0.15 mm。故没有宣称“仅四焊盘便 DRC0”，也没有以厂商极限豁免项目规则。局部避让先在独立临时工程验证，得到 **0 DRC violations /0 unconnected pads /0 footprint errors**，然后才应用同样变化并重铺铜。

## 红测、绿测和严格差异证据

- `red.json`：修改前实际原板/本地封装的四槽环宽失败，生成器持久适配缺失；属于预期失败，非运行异常。
- `pad-only-green.json`：四焊盘尺寸阶段的 17 项契约通过，**不代表该阶段完整 DRC 通过**。
- `vbus-red.json`：加入明确避让契约后，五条线段的目标位置检查按预期失败。
- `candidate-drc.rpt` / `candidate-drc.log`：临时板加入最小避让并重铺铜后，完整 PCB DRC 零违规、零未连接、零封装错误。
- `green.json`：最终 **23 项全部通过**。实际读取 native PCB、本地封装；验证四个尺寸与所有孔不变、五个精确段端点、其余语义数据不变、生成器持久适配；实际执行尺寸/文件/走线适配器并验证幂等性。
- `zone-fill-delta.json`：独立比较前后实际填充铜多边形；量化 USB 附近变化，并单独保留远处重铺铜计算量化误差，不把它混入走线修改。

PCB 与封装语义比较仅允许上面四个 pad size、五段明确端点和重铺铜生成的 `filled_polygon`/`fill_segments` 缓存变化；区轮廓、网络、层、孔、其他所有焊盘、走线、图形、规则及层叠均参加比较。KiCad 保存会重排部分同层 segment 的序列化顺序，比较使用无序对象集合，未把排序变化冒充走线变化。

首次本地封装 `FootprintSave` 会升级文件版本及重生 UUID，严格检查检测到这一副作用；随后恢复 baseline 原文，仅替换四个尺寸。最终 `green.json` 和文件 diff 是最终状态证据；`pad-only-intermediate-implementation.json` 仅保留中间过程，不应拿其库哈希作为交付版本。

## 版本与复现

- 冻结板/封装目录：`/workspace/a1-jlc-baseline`。
- 原板 SHA-256：`aa17fa9b22cc113f423552e96b39004e5b6b77cb64c0e49f54233de939642a5a`。
- 最终板 SHA-256：`b04859e7a282eb648943abfbf70d00e488a887627a74470aab24ffc20d637d44`。

```sh
# 写入已批准的精确变化（对已更新板幂等）；之后必须执行完整 build。
XDG_CONFIG_HOME=/tmp/quadcuber-fabrication-config XDG_DATA_HOME=/tmp/quadcuber-fabrication-data XDG_CACHE_HOME=/tmp/quadcuber-fabrication-cache /workspace/tools/kicad-10.0.7/squashfs-root/AppRun python3.11 electronics/revise_usb_slots.py --apply

# 独立只读契约；默认使用冻结 baseline。
XDG_CONFIG_HOME=/tmp/quadcuber-fabrication-config XDG_DATA_HOME=/tmp/quadcuber-fabrication-data XDG_CACHE_HOME=/tmp/quadcuber-fabrication-cache /workspace/tools/kicad-10.0.7/squashfs-root/AppRun python3.11 electronics/verify_usb_slot_revision.py --label green
```

本实施者未运行全 build；主线程将在最终 PCB 上统一执行 ERC/DRC、制造导出及 JLC/装配审计。工艺受理、开放热孔与模板/空洞策略、丝印改善、工艺边/基准点和首板验证仍是相应制造/试验阶段的任务，不由这次局部修改自动放行。
