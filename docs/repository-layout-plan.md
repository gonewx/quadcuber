# 仓库目录整理实施计划

**目标：** 落实已批准的功能目录方案，只改变文件组织、资源引用和构建边界，保留现有机械与控制行为。

**目录结构：** `mechanical/`、`wiring/`、`web/` 是唯一功能源码；`generated/` 保存一份标准生成物；`dist/` 是不入 Git 的分发输出。沿用现有 Python/Node 生成器，不新增框架，不引入顶层 `src/`。

**运行环境：** Python 3.11、Node 22、现有锁定机械依赖、现有 THREE/LDraw、浏览器验证。

**设计依据：** [已批准目录设计](repository-layout-design.md)。按以下顺序分批实施，最后进行独立审阅。

## 不变项与授权范围

- 501 步、882 件、11 个模型及原 501 页 PDF 保持一致；不改变机械设计、控制算法、标定或接线功能。
- PDF SHA256：`39bcef11c358ee797d2f606880a1b1bc37db8c4589c87290bc6748168605af52`。
- 固件、实测资料和独立接线基准原位；冻结输入和许可证不得误去重；禁止全部长度的全圆孔薄梁。
- Git 基线为 `e9d56112fa59c3301faa3b19b167e14e95b1e212`；实施前再读取工作树状态，保留用户改动。
- 授权仅含本地整理、可恢复删除和提交。不得推送、开 PR、合并、部署或刷硬件。
- 不新增 final/v27/任务名产品目录；`docs/` 为人工文档，`tests/` 为回归测试及独立基准。

## 重点检查项

1. 从非仓库工作目录运行、解压到新目录：构建不得读取作者路径或旧工作树（步骤 2、4）。
2. 老链接带 query/hash、第 501 步锚点：转向保持参数并抵达正确页面（步骤 5）。
3. 离线及手机窄屏：脚本、图解、3D、装卸动作仍可用，无横向溢出（步骤 4、6）。
4. 名称像历史输出的真实输入：模板、步骤配方、冻结基线不能被清理（步骤 1、5）。
5. 两份相同接线数据：独立测试基准不能改为读取生成结果；R+L 限制不变（步骤 3）。

---

## 步骤 1: 冻结基线与迁移清单

**涉及文件：** 新建 `mechanical/inputs/layout-baseline.json`、`tests/test_repository_layout.py`；读取既有设计和 `AGENTS.md`。

**输入输出约定：** 基线 JSON 的 `base_commit` 为字符串，`files` 为条目列表，每项含 `old_path`、`new_path`、`role`、`sha256`；从 Git 基线读取原始字节，禁止以迁移后的结果回填预期值。后续每批消费这份固定映射。

- [ ] 记录 11 个模型、全部图解、guide、PDF、BOM/台账、冻结输入、固件、实测证据、接线 fixture 和许可证的原始哈希；列出生成器 import/读文件依赖，特别保留当前模板与手册配方。
- [ ] 新增有意义的布局检查：模型和 PDF 字节不变、固定目录职责、历史生成器不能覆盖当前入口、固件和接线基准不变。先运行并确认新布局相关断言因目标未迁移而失败；不为简单移动堆叠重复测试。
- [ ] 跑原根回归与接线检查，保存本次真实基线：`python -m unittest -v`、`python docs/wiring/build.py --check`。预期 113 项根测试通过、接线检查退出 0；新布局测试单独运行，不混入原基线计数。
- [ ] 本地提交设计、计划及冻结清单；新增布局测试随对应实现批次提交，避免提交故意失败的全套测试。

**回滚点:** 基线提交；执行前若出现非本任务变更，逐文件保护，不使用 reset --hard 或全目录清理。

## 步骤 2: 机械源码与唯一标准输出

**涉及文件：** `mechanical/final/` → `mechanical/`、`mechanical/inputs/`、`mechanical/assembly/`、`generated/mechanical/`；更新 `tests/test_final_mechanics.py`、相关生成器和 `.github/workflows/test.yml` 的机械路径。

**输入输出约定：** 模型和清单统一以 `generated/mechanical/` 为输出根，manifest 中 `models/...` 相对关系保持；手册 `guide.json` 图片相对结构保留。生成器解析仓库根，输入来自 `mechanical/inputs/`；输出目录支持由调用方显式指定，以便隔离重建。

- [ ] 移动源码、冻结输入及现有生成物，按设计表区分配方和生成结果；重复 baseline 仅保留原字节的一份，改用冻结哈希校验。
- [ ] 修复生成器输入输出路径、测试 import 和 CI；不改几何计算、渲染算法、零件顺序或依赖版本。
- [ ] 运行 `python -m unittest tests.test_final_mechanics -v`、`python -m unittest discover -s mechanical/assembly -p 'test_*.py' -v`；预期全部通过。在临时目录重建 11 模型及清单，与冻结基线逐项比较；核验原 PDF 和全部图解未变。
- [ ] 运行相关布局断言并提交本批变更。依赖此批的网页路径在步骤 4 完成，期间不宣称整仓库已通过。

**回滚点:** 本批独立本地提交；必要时以 revert 恢复，保留冻结基线。

## 步骤 3: 接线源码与输出分离

**涉及文件：** `docs/wiring/{spec,build,direct_wiring,perfboard_layout,check_browser}.py` → `wiring/`；生成文件 → `generated/wiring/`；更新 `tests/test_wiring.py`、工作流和人工说明引用。

**输入输出约定：** `wiring/spec.py` 为唯一接线规范；生成输出根为 `generated/wiring/`；继续更新 `docs/perfboard.md` 与 `docs/single_arm.md` 的受控区域；fixture 仍读取 `tests/fixtures/direct-breadboard-r.json`。

- [ ] 更新路径并为独立 fixture、R/R+L 引脚及适用条件保留断言；规范和固件参数字节不变。
- [ ] 运行 `python -m unittest tests.test_wiring -v`、`python wiring/build.py --check`；预期全部通过、退出 0。按现有浏览器脚本接口检查 R/R+L 切换、PNG 输出，不能以文本生成检查代替。
- [ ] 对比固件与实测证据哈希，提交本批变更。

**回滚点:** 接线批次提交；不得重录 fixture 来消除迁移失败。

## 步骤 4: 网页、离线与下载同源构建

**涉及文件：** 当前 `site-source/` 依赖闭包 → `web/`；页面 → `generated/site/`；`build_source_archive.py`、`check_rebuild.py` → `tools/`；更新 `.gitignore`、网页 Python/Node 测试。

**输入输出约定：** 网页构建读取步骤 2 的标准输出；本地页面引用 `../mechanical/`。分发构建 `python tools/build_distribution.py --output DIR` 从空 DIR 生成 `site/`、`offline/`、`downloads/`；源码打包使用明确输入清单。`python tools/check_rebuild.py` 在临时目录验证构建和包内独立重建。

- [ ] 先补失败用例：无旧 dist 时可生成全部当前资源，下载源码包在独立目录可构建，离线模式不请求网络；确认失败来自现有构建边界。
- [ ] 移动当前网页生成器、模板、JS/CSS及测试，保持内嵌依赖版本；显式设置输入输出路径。
- [ ] 实现小型分发组装脚本，复用既有生成器；保留四个线上文件名及 `integrated/` 资源路由；同一模板生成离线版，保留四页与完整资源。
- [ ] 运行 `python web/test_final_presentation.py`、`python web/test_integrated_bundle.py`、`python web/viewer-dom-validation.py`，以及在 `web/` 执行现有 4 组 Node 测试和 `node validate_integrated_models.cjs`。预期原 8+4+21 测试保留且通过，11 模型外部几何请求为零。
- [ ] 运行 `python tools/check_rebuild.py`；预期空输出构建、下载包独立解压构建及标准资源一致性全通过。离线验收完成后才移除旧离线副本，提交本批变更。

**回滚点:** 网页／分发批次提交；原 PDF、图解及未验证离线文件不提前删除。

## 步骤 5: 历史清理、兼容和文档

**涉及文件：** 处理 `docs/lego/v4/`、`docs/lego/archive/`、`tools/lego/`、`artifacts/`、网页历史输出；更新根 README、功能 README、`docs/history.md` 和必要旧 HTML 入口。

**输入输出约定：** 历史索引使用基线提交永久链接；兼容页指向新标准输出并保留 query/hash。旧二进制 raw 路径无法 HTML 重定向，使用固定提交文件链接，发现关键外部依赖则明确保留例外。

- [ ] 对每个拟移除文件验证：已在 Git 基线存在、当前构建／测试无读取依赖、许可证与必要来源证据已保留。未证明者暂留并记录理由。
- [ ] 移除已核验历史树与重复分发资源；保留最少旧入口。新增锚点／query 兼容测试并观察失败，再实现转向。
- [ ] 更新 README 第一屏及全部当前构建命令，消除“v4 当前版”；扫描相对链接及失效旧路径，区分合法历史说明与实际运行引用。
- [ ] 运行布局与链接检查，确认不再跟踪 dist 副本；提交本批变更。

**回滚点:** 清理批次提交；历史源码和旧研究测试可按固定 Git 提交恢复。

## 步骤 6: 全量验证、独立审阅、本地交付

**涉及文件：** 全部分支差异、CI、所有测试；仅修复审阅发现的本次迁移问题。

- [ ] 重跑根 unittest、接线检查、手册 6 项、展示 8 项、整合 4 项、Node 21 项、原生模型检查、空目录重建及解压重建；记录真实计数和退出状态，新测试另列。任何旧断言减少都须解释，不能把路径变更当作删测试理由。
- [ ] 实测桌面 1440、手机 390：四页面、501 步跳转、局部 3D、装卸动作阶段与前后切换、资源下载、旧入口 query/hash；另用离线模式验证无网络依赖。检查控制台、缺失资源和横向溢出。
- [ ] 最终哈希核对模型、PDF、图解、冻结输入、固件、实测与 fixture；`git diff --check` 通过，`git status` 只含预期变更。
- [ ] 对整个分支进行一次独立代码审阅，修复重要问题并跑对应回归；本地提交修复与实际验证记录。
- [ ] 交付本地提交 SHA、迁移摘要、测试证据及剩余问题。停止在本地，不推送、不开 PR、不合并、不部署。

**回滚点:** 各批提交可单独 revert；最终交付保留全部本地历史。不得删除分支或强制改写基线。

## 计划自检

设计要求已分别落入步骤 1–6；机械输出根、网页消费者和分发根一致；接线 fixture 与固件路径保持不变；历史清理在依赖核验和当前构建完成之后。新增产物仅为现有功能所需的基线清单、分发脚本及验证，不增加框架。尚未执行任何迁移；实施前由用户审阅以下步骤、检查及回滚安排。
