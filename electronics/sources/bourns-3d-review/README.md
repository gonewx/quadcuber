# Bourns 原厂模型下载与核查

2026-10-13 正常 HTTPS 下载成功；模型来源 URL 与原始哈希见 `model-results.json`，本目录全部原件哈希见 `checksums.json`。三个文件均以 `ISO-10303-21` 开始并正确结束，OpenCascade/CadQuery 导入实体有效，非 HTML。

| 目标 | 官方下载 | 核查结论 |
|---|---|---|
| F2/F3 MF-MSMF050-2 | mf-msmf050.stp | PRODUCT/FILE_NAME 为 MF-MSMF050；1 实体，包围盒 3.24×0.70×4.55 mm。已渲染官方 mf-msmf.pdf 第 4、7、11 页，尺寸符合 Style 1，-2 为卷带包装。型号、文件与名义外形对应；本轮未把模型装入 PCB，仍需轴向/原点对齐验证。 |
| F10–13 MF-MSMF110/16X-2 | MF-MSMF110_16X.stp | 精确原厂目录链接实际返回与 050 完全相同的字节，PRODUCT 仍为 MF-MSMF050。官方 PDF 第 5、7 页把 110/16X 列为 Style 2，端子形状与 Style 1 不同。不得当作精确 110 模型安装，也未用相似模型代替。 |
| L1/L2 SRP1245A-100M | SRP1245A series.stp | 原厂目录只有系列模型。有效 8 实体，总包围盒 12.9×12.5×5.005 mm；内部名 TMPC1205HP-Series 仅作为溯源疑点，不单独判无效。已渲染 SRP1245A.pdf 第 1 页，-100M 属于 Lead Frame，总跨度标 13.5±0.5 mm，另一边 12.5±0.3、高4.8±0.2。模型 12.9 mm 总跨度低于图示13.0 mm下限，需原厂确认版本/适用性；不缩放、不假定为已核精确模型。 |

原厂资料：[SRP1245A](https://www.bourns.com/docs/Product-Datasheets/SRP1245A.pdf)、[MF-MSMF](https://www.bourns.com/docs/product-datasheets/mf-msmf.pdf)。本目录保存其余原始下载与错配证据；错配的 `MF-MSMF110_16X.stp` 不随提交发布，原始哈希保留在 `model-results.json`，下载原件仅保留在执行环境的下载区。不代表模型已附加或完成整板3D碰撞检查。J10–13 EV3、C26/C36 DNP、F1 Littelfuse 不在这份 Bourns 核查中替换。
