# AgentHarness：基于 DeepSeek Harness 的 Agent 系统公开课

> 🚧 建设中。课程网站：<https://odearevanhansen.github.io/agentharness/>　课程大纲：[docs/syllabus.md](docs/syllabus.md)

本课程是一门中文在线公开课，围绕一个 agent 系统，从上到下逐层拆开：

1. **观察**：读懂编码 agent 每一步的上下文、工具调用和成本（A1）
2. **从零实现**：写一个约 100 行、能解 SWE-bench 题目的 agent loop，并与工业级 harness 对照（A2）
3. **优化**：在 [DeepSeek Harness (DSH)](https://github.com/deepseek-ai/deepseek-harness) 上优化 agent 的成本、步数和前缀缓存命中率（A3）
4. **本地推理**：在自己的机器上部署本地模型，动手实验批处理、前缀复用、推测解码和量化（A4）
5. **全栈**：同时优化 agent 和推理服务两侧（A5）

课程结构参考了 Harvard [CS2680 Modern AI Systems](https://cs2680.seas.harvard.edu/)，在此致谢。本课程的讲义、作业和代码均为独立编写。

## 学员需要准备

- x86_64 Linux 机器，或 Windows + WSL2；至少 16GB 内存，A4/A5 推荐 32GB；100GB 磁盘空间；Docker
- 自己的 [DeepSeek API key](https://platform.deepseek.com/)。全课 API 费用预计在 100 元以内，最终数字会在试做阶段校准后公布
- 从 [作业 0：环境自检](assignment0/) 开始

> ⚠️ **安全与隐私**：
>
> - agent 会在你的机器上执行 shell 命令，所以课程的所有作业都在 Docker 容器中运行。
> - DSH 默认会把会话日志随请求上传给 DeepSeek。课程配置（[infra/course.patch.yml](infra/course.patch.yml)）默认关闭这一行为，详见第 1 讲。
> - 不要把 API key 提交到 git。

## 仓库结构

| 目录 | 内容 |
|---|---|
| `assignment0/` | 作业 0：环境自检 |
| `assignment1/` | 作业 1 DSH-Lens：起始代码 + 自动检查（可做） |
| `assignment2/` | 作业 2 madsLoop：起始代码 + 运行器 + 源码阅读题（可做） |
| `assignment3/`–`assignment5/` | 作业 3–5：草稿（机制已实测，排行榜建设中） |
| `infra/` | 课程基础设施：DSH 课程配置、只放行 DeepSeek 的出网白名单代理、SWE-bench 国内镜像工具 |
| `tools/` | 通用工具，例如从 DSH 会话日志统计 token 用量和成本 |
| `docs/design/` | 课程设计文档 |

## 许可

- 代码：[MIT](LICENSE)
- 讲义与文档：[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
- SWE-bench 及其评测镜像中包含的上游代码遵循各自的许可证
