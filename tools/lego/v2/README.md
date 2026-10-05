# 单臂原型 v2（转盘主轴承版）

v1 在上一级目录，保持不动。本目录是重新设计的 v2，说明书已发布在 https://claude.ai/artifact/9yGEt1ogaxxmStkyxYWYBL 。评估结论和设计推导见 `docs/lego/v2/README.md`。

| 文件 | 作用 |
| --- | --- |
| `model.py` | v2 模型：零件位置、朝向、搭建步骤和关键尺寸 |
| `run_check.py` | 全部检查（复用 `../check.py`，运行时补充新零件），问题数为 0 才算通过 |
| `booklet.py` | 生成 `docs/lego/v2/index.html`、步骤图和 `model.ldr`（渲染用 `../render/`） |

```bash
cd tools/lego/v2
python run_check.py
python ../render/server.py &
python booklet.py
```
