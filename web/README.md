# 网页源码

本目录是四个当前阅读页面的唯一源码。保持现有 THREE/LDraw 版本，库与支承模板仍封装于 `native-presentation.json`，许可证见 `vendor/THREE-LICENSE`。

在仓库根运行 `python web/build_integrated_revision.py`，生成 `generated/site/`，页面引用唯一的 `generated/mechanical/`。用 `python -m http.server 8000` 服务仓库根，打开 `/generated/site/index.html`。

运行 `python tools/build_distribution.py` 生成 `dist/site/`、`dist/offline/` 和 `dist/downloads/full-revision.zip`。网站中的 `full-revision.zip` 是紧凑源码／模型／步骤数据包，不含 PNG 和 PDF；图解／PDF从同版资源树取得，或使用完整包。`dist/downloads/quadcuber-source-complete.zip` 另含已验证图解与 PDF，可独立重建完整页面，不复制进受单文件大小限制的网站目录。离线包可直接打开 `dist/offline/index.html`，图解与下载内容随包附带。所有分发副本均不入 Git。

发布路径保留 `index.html`、`integrated-assembly.html`、`integrated-operation.html`、`integrated-support.html`。运行构建命令不会部署 Sites。后续发布须从本仓库构建并记录 Git 提交；发布仍需单独授权。
