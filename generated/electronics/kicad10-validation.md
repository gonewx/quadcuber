# A1 KiCad 10.0.7 迁移验证

日期：2026-10-12。基线：`e34395e68b175cf9a279664fd4a13fd6573d95db`。
使用用户批准的官方10.0.7 Lite AppImage解包安装；不包含完整标准3D模型库。

## 原生迁移

- 用 `kicad-cli pcb upgrade --force electronics/quadcuber.kicad_pcb` 原生重存PCB。
- 对 `electronics/*.kicad_sch` 全部12张原理图运行 `kicad-cli sch upgrade --force`。未手改格式版本号。
- 10版首次schematic parity发现198个缺失MPN字段。由10.0.7 `pcbnew.FOOTPRINT.SetField` 将网表中已有的MPN和Manufacturer写入PCB隐藏字段，共396个；随后 `pcbnew.SaveBoard` 原生保存。未改网络、器件摆放、铜路或固件。
- 当前PCB SHA-256：`9e55fcbee01241fc6ec3682fde79daaacd6bc623ecfc311809600e001099350a`。
- `electronics/verify_kicad10_migration.py` 直接读取冻结Git基线，用10版原生对象比较器件/焊盘位置、方向、尺寸、钻孔、网络、走线与过孔、铜区轮廓/填充及板框。结果见 `kicad10-migration.json`。J5两个无编号Ø0.65 mm NPTH的层掩码被原生保存展开为全部铜层；孔位/孔径未变，物理对照明确归一该项，不声称文本完全一致。
- 新旧导出网表的已连接符号引脚集合完全相同：543个。历史README的539为过期数字。

## 执行与结果

```sh
export KICAD_APP_RUN=/workspace/tools/kicad-10.0.7/squashfs-root/AppRun
export XDG_CONFIG_HOME=/workspace/tools/xdg/config
export XDG_CACHE_HOME=/workspace/tools/xdg/cache
export XDG_DATA_HOME=/workspace/tools/xdg/data
python3 electronics/build.py
"$KICAD_APP_RUN" python3.11 electronics/verify_kicad10_migration.py
python3 tools/build_distribution.py
python3 -m unittest tests.test_wiring tests.test_arm_selection tests.test_firmware tests.test_repository_layout -q
```

- build.py全部21个命令成功，完整命令和stdout/stderr见 `build-log.json`；版本为10.0.7。
- ERC：0错误、0警告。
- DRC（含 `--schematic-parity`）：0违规、0未连接、0封装一致性错误。
- 引脚契约：0错误；543个已连接符号引脚；202个封装、2602段走线/过孔、4层铜。
- 原理图PDF为12页；原理图SVG、板图SVG/PNG、正反装配图、内部铜层图、Gerber/钻孔制造预览、坐标表已重新导出。人工查看顶层与反面装配PNG可正常显示。
- 先重建分发，再跑既有相关回归：59项全部通过（未修改测试断言）。
- 另用 `KICAD_CLI` + `KICAD_PYTHON` 配置单独执行check.py成功；版本保护明确拒绝9.0.2。
- `git diff --check` 通过。

## 边界

`independent-review.md` 是绑定迁移前哈希的历史独立审查，已标注，不能冒充本次重新独立审查。当前证据只覆盖以上EDA及选定几何/网表验证。未进行完整3D检查、制造、通电、热/再生瞬态/USB反灌实测。Flash仍为W25Q16RVCNJQ，MicroPython固件未改；EV3用户图纸孔位保留，PINMAP/MPN/CURRENT仍HOLD，制造预览仍NOT RELEASED。电源仿真由独立工作负责，本迁移未触碰其目录。
