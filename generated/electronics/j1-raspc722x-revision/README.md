# RASPC722X J1 本地候选

基线 `cf614f3de777b39048b341b3983abcfe7e7962f3`。KiCad 10.0.7 原生编辑、导出与检查。本报告记录提交前验证；发布至PCB开发分支不构成制造放行。

J1 换为 Switchcraft RASPC722X，中心正，sleeve shunt 明确 NC；位置 `(95.5,50)`，mating face 对齐板顶边。三个推荐镀通槽使用原图英寸值乘25.4，铜环0.254 mm。三段1 mm VIN线改为两段1.8 mm，无新增过孔；只改VIN铜区轮廓，填充缓存由KiCad重算。

- `build.log`：完整工程导出，ERC/DRC/未连接/封装一致性检查。
- `scope-check.json`：独立可复算对照，199个非J1封装、2579条保留走线/过孔不变；原全部引脚网络保留，仅增加J1.3 NC。板框、项目及自定义规则未变。
- `fabrication-audit.log`：既有制造输出交叉检查；最终文件为上级 `release-preflight/fabrication-preflight.json`。PTH导出含正确的三个G85槽，未把槽孔误导出为圆孔。
- `repository-tests.log` / `electronics-tests.log`：154项仓库测试及7项电路测试。首次仓库测试因缺少未入Git的dist打包输出失败，执行仓库既有打包流程后通过；没有重做机械候选。
- `input-current-path.json`：按项目顶层70µm铜厚、1.8mm宽、12.214mm线长估算，20°C导线本身约1.67mΩ，5A时约8.36mV、41.8mW；未计插座接触/焊点/孔壁，也不是温升或载流认证。
- `toolchain-restore.json`：官方CERN链接、安装包完整大小/哈希及实际CLI/pcbnew版本。

独立只读审查者核对了原生PCB、原始S-expression差异、网表、BOM、三个Excellon槽和项目规则，未发现关键或重要实现缺陷。原保险、理想二极管及TVS保留。

原DC PDF由父线程实际渲染核验；本执行环境未取得可读原件，不能声称直接看图。源与限制见 `electronics/sources/raspc722x-review.md`。板厂槽孔工艺接受、实物配合和≤5A连续温升测试仍待完成。Bourns模型详见 `electronics/sources/bourns-3d-review/README.md`，错配/不确定模型均未装入PCB。
