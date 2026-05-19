# AGENTS.md

本文件只保留仓库特有、且不适合放进通用系统提示里的约束；项目结构、命令、架构说明统一以根目录 `README.md` 为准。

1. 为节省上下文，读取策略固定如下：
   - 会话开始时默认只读一次 `CLAUDE.md`、`README.md` 与 `.agent/skills/karpathy-guidelines/SKILL.md`。
   - 项目 skills 统一从 `.agent/skills/` 读取，按需命中后再读，不预读全部。
   - 能从代码、类型、测试或当前上下文直接确认的事实，不重复回读文档。

2. 每次任务中只要新增了图片文件，收尾前必须用 `python3 compress_images.py <新增图片路径>` 对新增 PNG 做 256 色有损量化压缩；非 PNG 图片需要指定 PNG 输出路径后再纳入结果。
