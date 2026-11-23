# AgentHarness：基于 DeepSeek Harness 的 Agent 系统公开课

> 🚧 建设中。课程网站：<https://odearevanhansen.github.io/agentharness/>　课程大纲：[docs/syllabus.md](docs/syllabus.md)

这是一门中文在线公开课。课程围绕一个 agent 系统，从上到下逐层拆开来讲：

1. **观察**：看清编码 agent 每一步的上下文、工具调用和成本（A1）
2. **从零实现**：写一个约 110 行、能解 SWE-bench 题目的 agent loop，并和工业级 harness 做对照（A2）
3. **优化**：在 [DeepSeek Harness (DSH)](https://github.com/deepseek-ai/deepseek-harness) 上优化 agent 的成本、步数和前缀缓存命中率（A3）
4. **本地推理**：在自己的机器上部署本地模型，动手实验批处理、前缀复用、推测解码和量化（A4）
5. **全栈**：同时优化 agent 和推理服务两侧（A5）

课程结构参考了 Harvard [CS2680 Modern AI Systems](https://cs2680.seas.harvard.edu/)，在此致谢。本课程的讲义、作业和代码均为独立编写，**与哈佛大学及 CS2680 课程团队没有任何关联，也未获其背书**。本课程为非官方课程，与 DeepSeek 官方亦无关联；作业二的 miniLoop 等名称均为本课程自拟。

## 15 分钟上手（不需要 Docker，支持 macOS）

```bash
git clone https://github.com/ODearEvanHansen/agentharness && cd agentharness
export DEEPSEEK_API_KEY=sk-...
python3 quickstart/quickstart.py
```

一个约 150 行、只用标准库的 coding agent，在 3 道小题上跑完，打印你的解决率和花费（通常几分钱）。说明见 [quickstart/README.md](quickstart/README.md)。

## 学员需要准备（完整课程）

- x86_64 Linux，或 Windows + WSL2，**不支持 macOS**；100GB 磁盘；Docker。
- 内存：16GB 可以完成 A0–A3 和 A4 的 8B 实验；A4 L3 和 A5 需要 32GB（内存不足的学员，A5 可以使用课程提供的本地基线）。
- 先修：熟练使用 Python，会用 git 和 Docker，能读简单的 HTML/JS 和 TypeScript。
- **为本课程单独创建**的 [DeepSeek API key](https://platform.deepseek.com/)，只充值少量金额，课程结束后删除。花费估算见[课程大纲](docs/syllabus.md#预计花费deepseek-api)。
- 从 [作业 0：环境自检](assignment0/) 开始。

> ⚠️ **安全与隐私**：
>
> - agent 会执行 shell 命令，所以课程的所有作业都在 Docker 容器中运行，网络只放行 DeepSeek API（见 [infra/](infra/)）。课程脚本检测到自己不在容器里时，会拒绝运行 agent。
> - 出网白名单防不住通过 `api.deepseek.com` 本身外传数据，所以请务必使用单独创建、限定额度的 key。
> - DSH 默认会把会话日志随请求上传给 DeepSeek。课程配置（[infra/course.patch.yml](infra/course.patch.yml)）关闭了这一行为，课程的所有脚本都会自动加载这份配置。
> - 不要把 API key 提交到 git。

## 仓库结构

**所有命令都在仓库根目录执行。**

| 目录 | 内容 |
|---|---|
| `assignment0/`–`assignment5/` | 作业 0–5：说明、起始代码和自动检查 |
| `infra/` | 课程基础设施：DSH 课程配置、出网白名单代理、运行器镜像、SWE-bench 数据集与 GHCR 镜像 |
| `tools/` | 通用工具，例如从 DSH 会话日志统计 token 用量和成本 |
| `videos/` | 讲座视频的讲稿和合成引擎 |
| `leaderboard/` | 排行榜提交 |
| `docs/` | 网站页面和课程设计文档 |

## 许可

- 代码：[MIT](LICENSE)
- 讲义、讲稿（`videos/lectures/` 中的文字）、文档和生成的视频：[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
- SWE-bench 数据集与工具采用 MIT 许可；评测镜像中的上游项目代码和软件包遵循各自的许可证（见 [infra/README.md](infra/README.md)）
- 本地模型（Qwen3 系列）采用 Apache-2.0 许可，由学员自行下载
