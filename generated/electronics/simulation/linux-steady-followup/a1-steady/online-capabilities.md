# 官方能力只读核查（2026-10-12）

- https://www.ti.com/product/TPS54302 ：明确400kHz固定开关频率及扩频、轻载跳脉冲；提供slvmbl9a PSpice模型。本次时钟检查对照此公开指标，未提交任何项目参数。
- https://www.ti.com/tool/PSPICE-FOR-TI ：公开说明Cadence模拟引擎、TI模型/参考电路、可离线运行。页面需Request access再下载安装；本次未申请、登录、接受许可或安装。该页面本身不能证明Linux原生支持，不能把它当作当前Linux可执行替代。
- https://www.ti.com/tool/WEBENCH-CIRCUIT-DESIGNER ：公开说明可按用户需求生成设计，提供电气仿真、Monte Carlo/Corner分析及CAD导出。仅核查产品页；没有打开设计表单或提交真实BOM、输入范围、负载、工程文件。公开页不足以证明TPS54302特定模型能原样导入、能运行任意原厂DSN或能支持当前A1双路网表。
- 未通过第三方代理、域名中转或已拒绝地址绕过访问限制。

当前可获取的强对照证据是：官方原厂参考在原生PSpice环境的导出网表及首开关波形，或TI发布的同修订模型参考结果；这里尚未取得。无Windows前提下，本地Linux原生Xyce/ngspice兼容仍有局限；WEBENCH仅是待进一步授权和能力确认的在线候选，不是已经验证的代替方案。不得声称已穷尽所有Linux仿真器。
