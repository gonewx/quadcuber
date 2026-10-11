# 最终机械页面源码（Sites v27）

当前入口：`dist/index.html`（整机 3D）、`dist/integrated-assembly.html`（501 步组装）。原 `integrated-operation.html` 保留为 17 阶段动作演示；`integrated-support.html` 保留为支承查看器。

完整来源、模型生成、测试、离线运行和验收范围见 [../README.md](../README.md)。本目录从真实 Sites Git 提交 `da37e173c56301fad68e6ce4dff24ff8ebd19126` 按子目录导入；主源码现在由 GitHub 管理。`.openai/hosting.json` 仅保留发布目标身份，本次同步不部署 Sites。

`python build_integrated_revision.py` 使用父目录的冻结模型与完整说明书，重建当前页面。原探索页面和旧测试保留用于历史追溯，不作为最终版入口；当前验收命令见父目录 README。
