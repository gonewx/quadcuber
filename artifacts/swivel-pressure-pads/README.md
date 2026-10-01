# 轮胎压头统一分支交付

本项工作统一使用主目录 `/mnt/disk0/project/cube/quadcuber` 的 `research/self-aligning-jaws` 分支。

- [当前搭建说明](../../docs/lego/v3/index.html)
- [机械审查与明确的双侧支承结论](../../docs/lego/v3/mechanical_audit.md)
- [实测记录表](../../docs/lego/v3/load_test_template.csv)
- [完整源码快照](source.zip)
- [分支 Git 包](branch.bundle)

旧工作区中的未提交草稿已保存于提交 `58e6bb4`，最新轮胎压头及审查提交 `dd830e5` 已合入统一分支。日常只维护 `tools/lego/v3/` 与 `docs/lego/v3/`；旧路径 `docs/lego/swivel-pressure-pads/` 为指向 v3 的目录链接。

当前模型仍是单侧薄梁审查基线，存在后部曲柄轴与推杆干涉。后续设计结论为改用双侧薄梁支承；双侧连接件和避让尚待设计验证。实物刚度与保持力未测试。

下载包从统一分支生成。`branch.bundle` 需要基础提交 `4e7d3ca4cf1f7bae73762caabbf1f2c7f82c4da7`，`source.zip` 无此要求。本机直接使用主目录即可。
