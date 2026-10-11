# 源码包使用

`full-revision.zip` 是用于网站下载的紧凑包：包含机械与网页生成代码、冻结模型、BOM、步骤数据和输入，**不含 PNG 图解及 PDF**。解压后安装 `mechanical/requirements.txt`，运行 `python mechanical/build_candidate.py` 和 `python mechanical/generate_inventory.py` 可独立重建 11 个冻结模型及清单。

需要完整图解／PDF和独立网页重建时，使用 `quadcuber-source-complete.zip`，或使用同版 Git 仓库的完整 `generated/mechanical/manual/` 资源树。完整包解压后可运行 `python web/build_integrated_revision.py`；在解压根目录启动 `python -m http.server 8000`，浏览 `generated/site/index.html`。`python tools/check_rebuild.py` 验证模型、页面及再次打包的独立重建。完整包超过网站单文件上限，只生成到 `dist/downloads/` 供独立交付，不进入 `dist/site/`。

这两个包只覆盖机械和阅读页面，非完整控制项目。固件、标定、实测资料与控制运行库以 GitHub 项目仓库为准。PDF、图解的实物验证限制不因可重建而改变。
