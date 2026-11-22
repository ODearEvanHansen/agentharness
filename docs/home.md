<!-- 本文件由 scripts/build_site.py 用于生成网站，站内链接在 GitHub 仓库里直接浏览会失效，请访问 https://odearevanhansen.github.io/agentharness/ -->
# AgentHarness · Agent 系统公开课

**基于 [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) 的中文公开课：把一个编码 agent 从上到下拆开，看清它、写出它、优化它，再亲手部署它背后的推理服务。**

<div class="grid cards" markdown>

- :material-eye-outline: **观察**

    做一个网页，实时看清 agent 每一步的上下文、工具调用和成本。[作业 1](assignments/a1.md)

- :material-code-braces: **从零实现**

    用约 110 行 Python 写一个 agent loop，去解真实的 SWE-bench 题目。[作业 2](assignments/a2.md)

- :material-speedometer: **优化**

    只用配置和插件优化 DSH，参加排行榜，比解决率或者比成本。[作业 3](assignments/a3.md)

- :material-server: **本地推理**

    在 CPU 上部署模型，动手实验批处理、前缀复用、推测解码和量化。[作业 4](assignments/a4.md)

- :material-layers-triple: **全栈**

    主 agent 用云端模型，子 agent 用本地模型，同时优化解决率、成本和耗时。[作业 5](assignments/a5.md)

- :material-flag-checkered: **期末项目**

    自选题目，要求可复现，并写成公开报告。[项目指南](project.md)

</div>

## 这门课有什么不同

- **数据都是真实测出来的**：讲义和视频里的每个数字，都来自课程团队实际运行的结果，我们会公开命令和原始输出。例如，一个约 110 行的 loop 在 20 道 SWE-bench Verified 题上解决了 18 道，每题约 $0.026。
- **不需要 GPU**：除了 DeepSeek API，其余环节都能在一台普通 Linux 电脑上完成，本地推理部分全部在 CPU 上做。
- **每关都有自动检查**：作业拆成多个可以独立完成的关卡，跑完自动检查就知道这一关过没过。
- **安全优先**：agent 会执行真实命令，所以所有作业都在容器里运行，网络只放行 DeepSeek API，会话日志也不会上传。

## 开始学习

本课程按自己的进度学，**没有统一开课日期**，你开始的那天就是第 1 周。

1. 阅读[课程大纲](syllabus.md)：14 周授课 + 2 周项目期，共 28 讲，每讲 3–5 分钟视频，配讲稿全文。每周约 3–10 小时，全课约 85–110 小时（不含期末项目）；每周时间少于 6 小时，可以按大纲里的 [24 周节奏](syllabus.md#学习节奏)学。
2. 完成[作业 0：环境自检](assignments/a0.md)，在 [Discussions](https://github.com/ODearEvanHansen/agentharness/discussions/new?category=show-and-tell&title=%E4%BD%9C%E4%B8%9A%200%20%E6%89%93%E5%8D%A1) 发帖打卡。
3. 从[第 1 讲](lectures/l01.md)开始。只想做其中某个作业，见[按需学习路线](syllabus.md#按需学习路线)。

学习问题请到 [Discussions 的 Q&A](https://github.com/ODearEvanHansen/agentharness/discussions/new?category=q-a) 提问；脚本跑不通或内容有错，请[提 Issue](https://github.com/ODearEvanHansen/agentharness/issues/new/choose)。

## 需要准备什么

| | |
|---|---|
| 电脑 | x86_64 Linux，或 Windows + WSL2；内存至少 16GB（作业 4、5 推荐 32GB）；磁盘 100GB；Docker |
| API | 自己的 [DeepSeek API key](https://platform.deepseek.com/)。API 费用分项估算（试做阶段实测，按官方高峰价）：A0–A1 几元；A2 不到 $2；A3 必做部分约 $5（约 35 元），大量调试可能到 $50–70（约 350–500 元），所以请先在小题或子集上调试，重跑同样计费；按[最低预算路线](syllabus.md#最低预算路线)全课（不含期末项目）约 80 元。建议只预充一笔固定小额余额作为硬上限；A5 必做部分的云端花费不到 $1；期末项目建议控制在 100 元以内。全课总额要等外部试学员做完后再校准公布 |
| 先修 | 熟练使用 Python，会用 git 和 Docker，了解 HTTP。不需要机器学习背景 |

!!! warning "当前状态"
    课程正在建设中：作业 0–5 均已可完成（课程团队已完整跑通，等待外部试学员校准耗时与花费），讲座视频制作中。进展请关注 [GitHub 仓库](https://github.com/ODearEvanHansen/agentharness)。

---

课程结构参考了 Harvard [CS2680 Modern AI Systems](https://cs2680.seas.harvard.edu/)，在此致谢。本课程的讲义、作业和代码均为独立编写，**与哈佛大学及 CS2680 课程团队没有任何关联，也未获其背书**。代码采用 MIT 许可，讲义采用 CC BY-SA 4.0 许可。
