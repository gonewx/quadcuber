# 仓库目录整理设计（待确认）

本轮只审计并提出设计，尚未迁移、删除或修改任何程序、模型、生成物和发布页面。建议采用方案 A：按功能组织唯一源码，将可复用生成物集中保存，将网站、离线包、下载包视为同一源码的分发结果。目录不再包含 `final`、`v27` 或任务名称。

审计基线：`main` 的 `e9d56112fa59c3301faa3b19b167e14e95b1e212`，即已合并的 [PR #4](https://github.com/gonewx/quadcuber/pull/4)。设计在本地分支 `refactor/repository-layout` 编写。下一阶段须先确认方案；本设计不授权推送、PR、合并或部署。

## 1. 目标和不变量

- GitHub 仓库是唯一开发源码；Sites 仅接收构建好的发布内容，不再形成另一条维护源码的路径。
- 一个功能只有一个源码入口；模型、图解、PDF、网页各有明确生成命令和输出位置。不同交付格式可以包含生成的副本，不允许人工分别维护。
- 保留 501 步、501 页 PDF、882 件逐实例台账与 BOM、11 个模型状态、四臂、底座、转盘固定、后舵机架及竖支架、20 件重力复位杠杆，以及整机／装配／支承／装卸动作阅读器。
- 目录调整不改变机械设计、运动关系、控制算法、标定参数或接线。遵守根 `AGENTS.md`：禁止全部长度的全圆孔薄梁，不能用十字轴孔随意替换需要自由转动的连接。
- 保留 PR #2 控制安全、PR #3 接线和后续配置；R 单臂与 R+L 的适用条件继续明确。`test_v4_safety.py` 是当前控制安全测试，不能因文件名有 v4 而归档。
- 历史方案原则上交给 Git 保存；不可重建的实测数据、照片、标定证据和当前构建所依赖的冻结输入仍留在工作树。
- 保持用户常用入口及 `integrated-operation.html` 兼容。不重新部署 Sites、不刷硬件、不改变实机标定；软件检查不构成实机安全认证。

## 2. 现状：实际文件和依赖

统计针对基线的 Git 跟踪文件，不含 `.git`、缓存、安装依赖。共 2,105 个文件，约 436.80 MiB；MiB 按 1,048,576 字节计算。

| 目录 | 文件数 | 约 MiB | 实际职责与问题 |
| --- | ---: | ---: | --- |
| `mechanical/final/` | 986 | 322.75 | 当前模型源码、冻结输入、手册、网站源码、网站输出、离线副本全部嵌套在一起 |
| `docs/lego/` | 826 | 80.87 | 当前导航、库存说明、v4 输出，以及 601 个旧方案归档文件混居 |
| `docs/wiring/` | 21 | 4.08 | 接线规范、生成程序、HTML/SVG/PNG/netlist 混居 |
| `docs/measurements/` | 43 | 12.66 | 实测日志、参数快照、照片；属于原始证据，应保留 |
| `docs/` 根部 | 9 | 0.10 | 控制、实测和装配相关说明 |
| `tools/lego/` | 69 | 0.77 | 多代模型、手册、渲染器和验证脚本；大部分不在当前构建链 |
| `artifacts/` | 116 | 15.38 | 多轮机械实验的源码、模型、图片、审阅页面混合存放 |
| `firmware/` | 8 | 0.04 | Pico 固件、Uno 编码器测试；不应跟随机械目录整理改动 |
| `quadcuber/` | 7 | 0.05 | Python 规划／仿真运行库；与机械生成依赖分离 |
| `tests/` | 13 | 0.07 | 当前回归测试及接线独立基准 |
| 根文件与 `.github/` | 7 | <0.01 | 项目元数据、工作流等 |

`mechanical/final/` 内部进一步分为：根部 23 文件，`manual/` 264 文件／76.12 MiB，`models/` 11 文件／6.92 MiB，`offline-viewer/` 4 文件／18.62 MiB，`site-source/` 665 文件／219.04 MiB，`source/` 15 文件，`parts/` 4 文件。其中 `site-source/dist/` 独占 553 文件／210.15 MiB，既有当前页面，又有历史输出。

### 2.1 逐字节重复与不能盲目合并的内容

以文件内容 SHA256 分组发现 376 组重复内容，保留每组一份时理论多余字节为 93,377,038（约 89.05 MiB）。这不是可直接删除的容量承诺：部分副本是必要测试基准或交付格式内的派生内容。

| 对象 | 审计结论 | 处理原则 |
| --- | --- | --- |
| `manual/manual.pdf` 与 `dist/integrated/manual.pdf` | 完全相同，单份 25,013,922 字节 | 仓库只跟踪一份权威 PDF；发布时复制 |
| `manual/guide.json` 与 `dist/integrated/guide.json` | 完全相同，单份 7,191,707 字节 | 保留一份生成数据，网页构建读取它 |
| 11 个 MPD 与网站内对应模型 | 完全相同 | 保留一个模型输出目录；发布包再复制 |
| 手册图解、清单、manifest 的网站副本 | 多处完全相同 | 按实际内容及依赖映射处理，不按文件名判断 |
| 旧 v3/v4/v5 页面内 THREE、LDrawLoader、OrbitControls | 多个版本目录重复携带库 | 旧页面移交 Git；当前库保持现有版本及许可证，不借机升级 |
| `source/baseline_model.py` 与 `source/github-current-model.py` | 完全相同的冻结输入 | 一份冻结源码加原始哈希即可；替换“两份互相比对”的检查 |
| `tools/lego/v4/model.py` 与上述冻结源码 | 相差一个末尾换行，哈希不同 | 保留当前冻结输入原始字节，不能直接指向旧 v4 文件 |
| 当前 R 接线 netlist 与 `tests/fixtures/direct-breadboard-r.json` | 完全相同，但基准用途独立 | **两份保留**，防止测试变成生成器与自身比较 |
| 四份离线 HTML 与在线 HTML | 路径、内嵌内容和路由不同，非简单重复 | 同一模板按输出模式生成；不能替换为需要联网的快捷链接 |
| 空 `__init__.py` 与空日志 | 字节相同但语义不同 | 不按重复哈希删除模块初始化文件 |

冻结模型源码当前 SHA256 为 `ed1b9d8d71aed8f34e93dce32fcb35a33a16203360bfdbd1064282600c72d7fc`；旧 `tools/lego/v4/model.py` 为 `108aa92fd36c8f43a5978e3a46ec98c98aab92a348a613ca7d68f72ac4a0917f`。这一差异说明“同功能”与“可替换输入”不是同一件事。

### 2.2 当前依赖链

```text
冻结基线模型／MPD、装配输入、零件定义、asset-order.json
  → candidate.py → build_candidate.py / generate_inventory.py
  → 11 个 MPD、manifest、BOM、逐实例台账

底盘／支承／机械头步骤配方 + 冻结手册输入 + 当前模型
  → manual 内生成与渲染程序
  → guide.json、图解、manual.md、501 页 PDF

模型与手册输出 + site-source 的模板／JS／CSS／内嵌库
  → build_integrated_revision.py → viewer/operation workbench
  → 四个当前网页、页面数据、源码下载 ZIP

docs/wiring/spec.py + 固件配置校验
  → direct_wiring.py / perfboard_layout.py / build.py
  → R、R+L、洞洞板文档与 netlist，以及指定 Markdown 表格区域
```

- 当前机械构建依赖的是 `mechanical/final/source/` 中的冻结输入，不需要把旧 `tools/lego/v4/` 留作第二套可编辑模型。
- `base-steps.json`、`support-steps.json`、机械头配方及 `source/manual-inputs/` 是当前完整手册的输入。名字包含旧步数并不意味着可删。
- `asset-order.json` 控制 MPD 内嵌零件顺序，删除会破坏逐字节复现。
- 当前网页明确读取 `operation-template.json`、`operation-guide.html/css`、`candidate-colors.ldr`、多个 candidate/operation JS、`native-presentation.json`，以及两个 workbench 生成器。`operation-guide.html` 虽名字像旧输出，实际是当前模板，必须保留。
- `native-presentation.json` 同时包含依赖库、支承模板与样式。第一阶段保持其字节，拆分库与模板不是目录迁移的前置条件。
- 当前重建检查会先复制现有 `dist`，再生成当前页面；553 文件对比包含未重新生成的历史页面。下一阶段应增加**从空输出目录构建当前资源闭包**，不能把“复制旧输出后相同”当作完整清洁构建证明。
- 没有在当前 Python 生成器中找到统一生成 `offline-viewer/` 四页的入口。离线产物应先冻结保留；补上同源生成及验证后，才能删除跟踪副本。
- 接线 `build.py` 会更新 `docs/perfboard.md` 和 `docs/single_arm.md` 的指定表格区域；浏览器 PNG 导出由 `check_browser.py` 负责，不能误以为 `build.py --check` 已验证 PNG。

### 2.3 实际入口冲突

根 README 和 `docs/lego/index.html` 已指向最终整机，但 `docs/lego/README.md` 仍将 772 件、22 步、125 卡片的 v4 描述为当前版，归档 README 也仍指回 v4。`tools/lego/README.md` 描述旧 20／26 步原型，其生成命令可写入现在的 `docs/lego/index.html`。这是需要消除的多入口维护风险。

`artifacts/` 的夹头架构、头部原型、头部重设计、后架实验等是方案研究；`docs/lego/archive/` 的 v1、medium、v2、v3、v3-baseline、v5、research 是历史展示。迁移实施前逐文件核验当前 import、文件读取和文档引用；未证明脱离当前构建的输入不能归档删除。

## 3. 两个可选方案

| 对比 | A：功能源码 + 集中生成物（推荐） | B：沿用 tools/docs 双层布局 |
| --- | --- | --- |
| 机械源码 | `mechanical/` | `tools/lego/`，去掉 v2/v3/v4/v5 |
| 接线源码 | `wiring/` | `tools/wiring/` |
| 网页源码 | `web/` | `tools/web/` |
| 唯一跟踪生成物 | `generated/mechanical/`、`generated/wiring/`、`generated/site/` | `docs/lego/`、`docs/wiring/` 存放各自生成物 |
| 人工文档 | `docs/` | `docs/`，仍与输出混合但分子目录约定 |
| 发布／离线／下载包 | 不跟踪的 `dist/` | 同左 |
| 优点 | 功能边界直观；源码、证据、生成物清楚；不再依赖“最新版本目录” | 沿用原有习惯和部分 URL，初始链接修改较少 |
| 代价 | 首次路径迁移较多，必须集中更新构建和兼容入口 | 机械功能被称为工具，源码与说明需跨树查找；docs 职责仍较复杂 |

推荐 A。项目已经不只是 LEGO 小工具：存在完整机械生成、网页阅读器和接线生成系统。用固定功能目录承接现有实现，比继续整理多个版本子目录更持久。无需引入新框架、包管理体系、服务或大型任务调度器。

## 4. 推荐目标目录及所有权

```text
quadcuber/
├── AGENTS.md、README.md、pyproject.toml、LICENSE 等项目文件
├── quadcuber/                 现有规划／仿真运行库，保持不动
├── firmware/                  现有 Pico／Uno 源码与配置，保持不动
├── mechanical/
│   ├── README.md、requirements.txt
│   ├── candidate.py、build_candidate.py、generate_inventory.py
│   ├── inputs/                冻结基线、装配输入、asset-order、来源信息
│   ├── parts/                 当前构建所需四个零件定义，保留来源
│   └── assembly/              步骤配方、手册生成／渲染／验证程序
├── wiring/                    spec、接线／洞洞板生成器、浏览器校验
├── web/                       当前模板、JS/CSS、构建与网页测试
│   └── native-presentation.json  初次迁移保留现有封装与依赖版本
├── generated/                 跟踪、不可手改；唯一标准输出
│   ├── mechanical/
│   │   ├── models/            11 个 MPD
│   │   ├── manual/            guide、PNG 图解、Markdown、PDF
│   │   └── 清单与 BOM、逐实例台账、验证结果
│   ├── wiring/                HTML、SVG、PNG、netlist
│   └── site/                  四个当前 HTML 及必要网页派生数据
├── docs/                      人工维护的说明、库存、控制与接线文档
│   ├── measurements/          原始实测证据，原路径保留
│   ├── history.md             历史方案与冻结提交索引
│   └── lego/、wiring/          仅必要旧 URL 的轻量兼容页／README
├── tests/                     现有测试和独立回归基准
├── tools/                     少量跨功能构建／校验／打包入口
├── dist/                      忽略；site/、offline/、downloads/ 分发副本
└── .github/workflows/         CI
```

`generated/` 必须跟踪的理由：501 页 PDF、已验证图解、模型应可直接取得，不强迫使用者安装渲染依赖；迁移不要求重渲染原交付物。它是生成结果，不是第二套源码。`dist/` 是可清空后重建的发布组装区，不再提交一整套重复图片、PDF、模型和 ZIP。

本地网页从 `generated/site/` 引用 `../mechanical/` 的标准输出；使用仓库根静态服务器浏览。网页中因离线加载需要而内嵌的模型／脚本属于明确的生成数据，不人工维护。分发构建按 URL 配置复制资源到 `dist/site/integrated/`，保留现有线上路由。离线模式将所需脚本和数据内嵌并携带图解，必须实测断网／本地打开能力，不能只测试 HTTP 模式。

暂不为目录整齐批量改 `candidate.py`、`assembly132.json` 等文件名；冻结输入名称保留在功能目录内即可。版本来源记录在元数据和 Git 中，而非再增加 final/v27 层。

## 5. 旧路径 → 新路径及退出策略

| 旧位置／内容 | 目标 | 删除或兼容条件 |
| --- | --- | --- |
| `mechanical/final/candidate.py`、模型／库存生成程序、requirements | `mechanical/` | 仅更新显式输入输出路径，不改算法 |
| `mechanical/final/source/` | `mechanical/inputs/` | 保留冻结输入字节、原始哈希与来源；重复 baseline 副本合并后改为哈希校验 |
| `mechanical/final/parts/` | `mechanical/parts/` | 不换零件版本 |
| `manual/` 内配方、生成器、渲染器、测试 | `mechanical/assembly/` | 逐文件区分输入与输出，不整体移动后再猜测 |
| `manual/` 的图片、guide、PDF、生成 Markdown、审计结果 | `generated/mechanical/manual/` | 图片相对路径结构不变，尽可能保证 guide 与 PDF 原字节 |
| `models/`、生成 BOM／manifest／台账 | `generated/mechanical/` | 路径在 manifest 中仍以该输出根为基准 |
| PROVENANCE、frozen hashes、原始重建说明 | `mechanical/inputs/` 及 `mechanical/README.md` | 原来源记录不伪装成新发布记录；新增路径映射记录 |
| `site-source/` 当前构建闭包、模板、JS/CSS、测试 | `web/` | 依据运行时读文件和 import 闭包筛选，保留伪装成历史文件的当前模板 |
| `site-source/dist/` 当前页面及派生数据 | `generated/site/` | 资源改指唯一输出；公共发布仍使用原路由 |
| `site-source/dist/integrated/` 的重复 PDF／MPD／图片／清单 | 标准输出 + `dist/site/integrated/` 临时副本 | 对应哈希和全部链接验证通过后移除跟踪副本 |
| `site-source/dist/` 的 history、compact60483、candidate132、steps219 等历史输出 | Git 历史 + `docs/history.md` | 先排除当前模板／测试依赖；有旧入口则保留薄兼容页 |
| `offline-viewer/` 四页 | `dist/offline/` | 同源生成器及离线验收完成前保持原文件；迁移不能先删后补 |
| `build_source_archive.py`、`check_rebuild.py` | `tools/` 中打包／重建入口 | 打包采用明确输入清单，验证包内可独立构建 |
| `docs/wiring/` 五个 Python 源文件 | `wiring/` | spec 唯一；更新测试 import，保留固件一致性校验 |
| `docs/wiring/` HTML/SVG/PNG/netlist | `generated/wiring/` | 旧页面入口留转向页；PNG 单独浏览器验证 |
| `docs/wiring/README.md` | 原位保留人工说明及新入口 | 不再含会覆盖兼容目录的构建命令 |
| `tests/fixtures/direct-breadboard-r.json` | 不动 | 独立黄金基准，不合并到生成目录 |
| `docs/lego/inventory.md` | 不动 | AGENTS 的库存权威链接继续有效 |
| `docs/lego/index.html`、README | 原位薄导航／说明 | 指向当前生成网页与模型；清除“v4 当前版”说法 |
| `docs/lego/v4/`、`docs/lego/archive/` | Git 历史 + 历史索引 | 必要 HTML 入口标注历史并链接冻结提交，不把旧步骤冒充当前步骤 |
| `tools/lego/v2/v3/v4/v5`、旧根生成器／渲染器 | 历史 Git；确有当前依赖者按功能迁移 | 先核验依赖。旧研究测试的运行方式写入历史索引，不计作当前覆盖 |
| `tools/lego/parts/`、render 第三方依赖 | 依赖者保留；其余随旧工具归档 | 核验当前 MPD 内嵌依赖与许可证，不能仅凭重名删库 |
| `artifacts/` 各机械研究目录 | Git 历史 + 研究索引 | 当前冻结输入若引用它们，先保留该输入及 provenance；未证明可退出者暂留 |
| `docs/measurements/`、firmware、quadcuber、控制说明 | 不动 | 不可重建证据与安全参数不纳入此次去重 |

逐文件迁移清单须在实施时记录旧路径、新路径、角色、旧 SHA256、允许的变更类别。当前表是目录级设计，不构成对所有历史文件的批量删除授权。所有物理删除均需在同一审阅中给出 Git 永久链接或等价保留依据。

## 6. 兼容、构建和文档约定

### 6.1 链接兼容

1. 网站继续输出 `index.html`、`integrated-assembly.html`、`integrated-operation.html`、`integrated-support.html`；旧装卸动作入口不能只保留文件名却显示另一种阅读器。
2. 仓库常用 HTML 旧入口保留小型转向页，并保留 query/hash（例如第 501 步锚点）；同时给出可点击的新入口，以支持脚本禁用场景。兼容页只指向目标，不再内嵌模型、库和手册副本。
3. 对旧 v4／研究页面提供明确“历史方案”说明及固定提交链接。历史浏览不能悄悄跳入不同机械设计的当前步骤。
4. GitHub raw 的旧 PDF、MPD 等路径无法靠 HTML 实现真正 HTTP 重定向。更新仓库内引用，历史索引提供基线提交的永久文件链接；若发现外部关键下载依赖，单独保留最少文件并说明理由。不能承诺所有旧 raw URL 自动兼容。
5. README 第一屏指向当前整机、501 步阅读、PDF、BOM、接线和构建说明。`docs/lego/`、工具 README、归档索引同步修正，不再存在多个“当前版”。

### 6.2 构建调整

复用现有生成器，只更新显式输入输出路径；路径从仓库根解析，不依赖当前工作目录或作者绝对路径。机械依赖保持独立于运行库依赖，CI 继续 Python 3.11、Node 22 和现有依赖锁定。本次不引入新的构建框架或统一调度器。

机械生成器写入 `generated/mechanical/`，接线生成器写入 `generated/wiring/`，网页生成器读取上述输出并写入 `generated/site/`。发布／离线／下载打包使用明确输入清单，输出到不跟踪的 `dist/`。重建检查改为临时空目录，并验证下载源码包解压后可独立构建。手册重渲染保留为显式操作，迁移阶段不覆盖原 PDF 和图解。

`dist/` 不提交不意味着本轮上传 Release 或部署 Sites。后续发布使用仓库构建产物，并记录 Git SHA；部署仍需另行授权。

## 7. 迁移证明与测试门槛

本轮没有执行迁移测试。以下为实施后必须重新跑的验收，不能引用 PR #4 的旧结果代替。

| 检查 | 必须证明 |
| --- | --- |
| 机械文件基线 | 11 个 MPD 逐字节 SHA256 不变；四臂／底座／转盘固定／后架及竖支架／杠杆实例齐全 |
| 装配与库存 | 501 步、882 个唯一实例、最终 BOM 与各组件／颜色库存一致；原顺序和运动状态不变 |
| PDF 与图解 | 原 PDF SHA256 `39bcef11c358ee797d2f606880a1b1bc37db8c4589c87290bc6748168605af52` 不变、501 页；所有已交付图解逐文件哈希不变 |
| 冻结输入 | baseline、MPD、asset-order、手册输入及外部零件字节不变；原 provenance 可追溯 |
| 标准数据 | guide、台账、BOM 尽量逐字节不变；必要资源路径变化只能按显式映射比较，不做宽泛“忽略不同字段” |
| 控制与接线 | firmware 和实测配置零差异；R 独立 fixture 不变，R+L 语义／引脚／限制不变；接线 build check 与浏览器输出校验通过 |
| 既有自动测试 | 根 unittest 当前 113 项，手册 6 项、最终展示 8 项、整合包 4 项、Node 21 项全部保留并重跑；更新路径不能减少断言 |
| 原生模型 | 11 模型加载成功，外部几何请求为零，保留全圆孔薄梁禁用与几何一致性断言 |
| 干净构建 | 空输出构建当前资源闭包；从打包源码另起临时目录构建；不读取旧 dist、作者路径或历史工作树 |
| 网页与离线 | 桌面 1440 与手机 390 宽度；四路由、第 501 步、局部 3D、装卸动作阶段与按钮；无横向溢出、脚本错误或资源缺失；离线另验 |
| 兼容与链接 | 旧导航、integrated-operation、query/hash、PDF/BOM/源码包下载；仓库内全部相对引用和分发内引用闭合 |
| 仓库边界 | 只存在一套当前源码入口；历史生成器不再覆盖当前输出；无凭据、缓存、第三方依赖目录或 dist 打包副本误入提交 |

工作流需要更新 `.github/workflows/test.yml` 的 requirements、手册测试、网页工作目录、重建入口和接线命令；同步更新 `tests/test_final_mechanics.py`、`tests/test_wiring.py` 及网页测试中的路径。`test_control`、`pico_sim` 和 Uno 测试的固件路径应保持不变。旧 `tools/lego/v3/test_*.py` 当前不属于上述默认 CI；其历史可运行方式要保留，不能把删掉旧研究测试说成当前覆盖没有损失之外的全面等价证明。

## 8. 实施顺序、审阅和退出条件

确认方案后再制定实施提交：先冻结逐文件清单与验收基准；迁移当前源码并显式化输入输出；迁移标准生成物并消除网站副本；补齐发布／离线／下载的同源构建；最后处理已证明无当前依赖的历史树和兼容入口。每一步保持可验证，不把机械变更夹带进路径修改。

首次迁移不重写渲染算法，不升级 THREE，不合并控制和机械依赖，不改变目录之外的安全语义。尚不能证明可删除的历史输入保留并列明原因；不能用“研究目录”标签代替依赖证据。

迁移完成后提供路径清单、哈希对照、真实新测试结果和浏览器证据供审阅。只有后续获得明确授权，才进行提交推送、PR 或合并；Sites 发布不属于本设计的执行范围。

待确认的核心选择是 A 或 B。推荐确认 A，同时接受“跟踪一份标准生成物、分发副本不入 Git、历史以固定提交索引保留”的边界。若需要保留某个外部依赖的旧下载 URL，在实施前将其纳入兼容清单，而不是保留整棵重复目录。
