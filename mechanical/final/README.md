# 最终机械设计：501 步 / 882 件

[整机 3D](site-source/dist/index.html) · [逐步组装](site-source/dist/integrated-assembly.html) · [501 页 PDF](manual/manual.pdf) · [BOM](final-BOM.csv) · [离线阅读](offline-viewer/index.html)

本目录是最终机械设计主源码；GitHub 管理源码与变更，Sites 只承担发布。整机由 64 件四角闭环底盘、668 件四臂、150 件支承总成组成。支承包含 130 件托座导向和 20 件重力复位杠杆／止挡。说明书从单件开始，覆盖四臂、转盘固定、后舵机架、竖支架和总装；每臂 88 步，先完成 165 件，再安装预留侧梁与销，形成 167 件。

上位须持续按住外柄，夹头接管后缓松，空托盘按设计关系回落 40.8 mm。这里保存的是设计审阅结果，尚未完成实体装配、插入力、防脱、承载、自重回落、冲击、手部隔离和带电联锁验收。成品电机、舵机按采购件处理。控制安全标定与接线仍遵循仓库原有文档，CAD 数据不能替代实测标定。

## 文件与来源

| 路径 | 内容 |
| --- | --- |
| `candidate.py`、`build_candidate.py`、`source/`、`parts/` | 冻结计算依赖与模型生成器，原始 LDraw 作者和许可证保留在文件内 |
| `models/`、`candidate-manifest.json` | 11 个原生 MPD；7 个整机状态均为 882 件 |
| `manual/guide.json`、`manual/manual.pdf` | 501 步图文、882 实例取件账本、图解与完整 PDF |
| `final-BOM.csv`、`subsystem-BOM.csv`、`instance-inventory.csv` | 整机、分组件／颜色及逐实例清单 |
| `site-source/` | Sites v27 Git 源码和已生成页面，保留旧动作 URL |
| `offline-viewer/` | 无需构建的本地阅读入口 |
| `PROVENANCE.json` | 精确 Git、Library 版本、SHA256 和原交付文件清单 |

Sites 原提交为 `da37e173c56301fad68e6ce4dff24ff8ebd19126`，独立根为 `f91fd649afedc1136062b8a8f32772cefe1a0043`。与 GitHub 基线 `723bdd9283d53b3dcf01d64fb80fcea4695bbe7a` 无共同祖先，使用 `git read-tree --prefix` 原样导入 664 个 Git 文件，未合并两个根。Library ZIP v18 为 72,175,636 字节，PDF v6 为 501 页；ZIP 内 34 个页面源文件与该 Git 提交完全一致。

ZIP 漏带的 `baseline-machine-899.mpd` 与 `github-current-model.py` 从同一 Sites Git 树中的 `dist/compact60483/candidate-with-manual.zip` 找回，均严格匹配原 `frozen-source-sha256.json`。`source/asset-order.json` 固定 v27 子文件顺序，使生成结果不依赖文件系统遍历顺序。机械坐标、零件和模型哈希不变。当前页面的紧凑源码下载由 `build_source_archive.py` 确定性生成，包含模型、生成器、冻结依赖与步骤数据；省略 PNG/PDF 派生物及离线成品，完整图解/PDF可从仓库取得或依 `manual/REBUILD.md` 重渲染。

当前薄梁 11478、32449、41677 均含十字端孔；不允许全圆孔薄梁。

## 本地阅读与重建

从仓库根运行 `python -m http.server 8000`，打开 `http://localhost:8000/mechanical/final/site-source/dist/`。桌面与手机使用同一入口；旧 `integrated-operation.html` 继续提供动作演示。本次同步不执行 Sites 发布。

```bash
python -m pip install -r mechanical/final/requirements.txt
python mechanical/final/build_candidate.py
python mechanical/final/generate_inventory.py
python mechanical/final/site-source/build_integrated_revision.py
python mechanical/final/check_rebuild.py
```

`check_rebuild.py` 在临时目录重建，要求 11 个 MPD 与全部 553 个发布文件逐字节不变。已包含的 501 页 PDF 和图解无需重渲染。图解／PDF 完整生成顺序见 [manual/REBUILD.md](manual/REBUILD.md)；跨平台字体和渲染依赖可能影响图像及 PDF 字节，不能据此替换冻结交付哈希。历史探索页面不参与当前入口，但保留于源码中。

## 验证

```bash
python -m unittest -v
python docs/wiring/build.py --check
python -m unittest discover -s mechanical/final/manual -p 'test_*.py' -v
python mechanical/final/site-source/test_final_presentation.py
python mechanical/final/site-source/test_integrated_bundle.py
cd mechanical/final/site-source
python viewer-dom-validation.py
node --test gravity-step-pose.test.cjs unified-reader.test.cjs viewer-workbench-ui.test.cjs operation-workbench-ui.test.cjs
node validate_integrated_models.cjs
```

上述检查覆盖冻结输入、11 模型哈希与内嵌依赖、七状态 BOM、882 实例／501 步、转盘固定顺序、禁止全圆孔薄梁、PDF 一致性、当前链接、页面交互和重建。测试通过不等于实机安全认证。
