# 历史机械方案与来源

当前唯一源码入口是 [mechanical](../mechanical/README.md)、[wiring](../wiring/README.md) 和 [web](../web/README.md)。当前装配为 501 步、882 件。下面记录用于历史研究，不应替代当前装配步骤或实机标定。

历史基线固定为 `e9d56112fa59c3301faa3b19b167e14e95b1e212`，文件可在 Git 中完整恢复：

| 历史内容 | 原始文件 |
| --- | --- |
| v4 机械头与说明 | [docs/lego/v4](https://github.com/gonewx/quadcuber/tree/e9d56112fa59c3301faa3b19b167e14e95b1e212/docs/lego/v4) |
| v1、medium、v2、v3、v5、压头研究 | [docs/lego/archive](https://github.com/gonewx/quadcuber/tree/e9d56112fa59c3301faa3b19b167e14e95b1e212/docs/lego/archive) |
| 旧模型、渲染器、研究检查程序 | [tools/lego](https://github.com/gonewx/quadcuber/tree/e9d56112fa59c3301faa3b19b167e14e95b1e212/tools/lego) |
| 夹头／后架等结构实验 | [artifacts](https://github.com/gonewx/quadcuber/tree/e9d56112fa59c3301faa3b19b167e14e95b1e212/artifacts) |
| Sites 导入前后完整源码及旧输出 | [mechanical/final](https://github.com/gonewx/quadcuber/tree/e9d56112fa59c3301faa3b19b167e14e95b1e212/mechanical/final) |

旧研究测试不属于当前默认 CI。需要复查时，在单独检出的上述提交运行对应 README 的命令；例如 `python -m unittest discover -s tools/lego/v3 -p 'test_*.py'`。不要把旧生成器复制回当前输出目录运行。

Sites 原始提交为 `da37e173c56301fad68e6ce4dff24ff8ebd19126`，来源信息及原交付哈希见 [PROVENANCE](../mechanical/inputs/PROVENANCE.json)。该文件保留当时的原路径；目录整理的映射与冻结字节见 [layout-baseline.json](../mechanical/inputs/layout-baseline.json)。记录中的旧路径并非当前构建入口。

当前必需的基线源码、原 MPD、步骤配方和手册输入已保留；第三方 THREE 许可证保留在 [web/vendor](../web/vendor/THREE-LICENSE)，LDraw 作者与许可证仍在零件及内嵌模型中。实测日志、照片和配置继续保存在 `docs/measurements/`。

旧 raw PDF、MPD 等二进制地址无法用 HTML 重定向；需要固定旧内容时使用上述提交的永久文件链接。常用 HTML 导航保留薄兼容入口，发布网站仍输出 `integrated-operation.html` 等四个既有路由。
