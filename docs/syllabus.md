# 课程大纲（草案）

共 14 周，每周 2 讲，每讲 20–40 分钟录播，配讲义和阅读材料。讲义在 B 站和 GitHub 同步发布，答疑在 GitHub Discussions 和学习群进行。
**先修**：Python 熟练，会用 git 和 Docker，了解 HTTP。**不要求**有 GPU 或机器学习背景。

| 周 | 讲次 | 主题 | 要点 | 阅读 / 源码 | 作业 |
|---|---|---|---|---|---|
| 1 | L1 | 课程导论：agent 系统是什么 | 模型 + 循环 + 工具；本课的"自上而下"路线；**安全**：agent 会执行 shell，所以要隔离，并注意 key 泄露和提示注入 | CS2680 课程说明；DSH README（中文版） | 发布 A0 |
| | L2 | DeepSeek API 入门 | Chat Completions 接口、tool calling、思考模式和 `reasoning_content`、前缀缓存与计价（命中和未命中相差 50 倍）、高峰和低峰价格 | DeepSeek API 文档 | |
| 2 | L3 | DSH 导论 | Cordis 插件架构、profile 与 patch、SDK 与运行时；默认上传会话日志及如何关闭 | DSH `docs/user`、`python-sdk.md` | 发布 A1 |
| | L4 | 事件与会话日志 | turn/step/tool 事件、会话日志 v4 格式、用量字段；事件流和日志两种数据源的区别 | `framework/events.md` | |
| 3 | L5 | Agent loop 剖析（上） | 一个 step 的生命周期、请求组装、工具分发 | `agent-loop/README.md` | A1 截止，发布 A2 |
| | L6 | Agent loop 剖析（下） | 取消、失败恢复、配对补齐（`ABORTED_BEFORE_DISPATCH` / `TOOL_OUTCOME_UNKNOWN`）、并行工具调用和 exclusive barrier | `agent-loop/src/agent.ts` | |
| 4 | L7 | 工具设计 | 工具粒度对步数的影响（M0：loop 每题 4.9 步，DSH 2.3 步）；编辑工具的设计；输出截断 | DSH `tools` 子系统文档 | |
| | L8 | 评测 | SWE-bench 与 Verified 子集、官方 harness、数据污染、为什么要用难题集（原 20 题 18/20，难题集 10/20） | SWE-bench 论文 | |
| 5 | L9 | 评测基础设施 | 容器隔离、出网白名单、镜像分发（GHCR）、可复现性与方差 | `infra/` | A2 截止 |
| | L10 | 子 agent 与编排 | spawn/fork、深度和并发限制、结果回传；子 agent 什么时候值得用 | `subagent/README.md` | |
| 6 | L11 | 上下文工程 | 系统提示、压缩、工具结果裁剪；token 都花在了哪里 | `compaction` 子系统 | 发布 A3 |
| | L12 | 前缀缓存与 request series | 追加和改写对缓存的影响；"每一步都写入当前时间"的代价 | `agent-loop` L122/L166 | |
| 7 | L13 | 插件开发 | `tools/post-execute`、`agent/pre-step`、`agent/request-error`；用 `.ts` 免编译加载 | `develop/basic` | |
| | L14 | 成本与可靠性 | 重试策略、预算控制、模型选择（flash 和 pro 怎么选） | | |
| 8 | L15 | 实验方法 | 对照实验、只改一个变量、重复次数与方差、按高峰价统一计价 | | |
| | L16 | 案例复盘 | A3 优秀方案分享（往届或课程团队） | | A3 截止 |
| 9 | L17 | 推理基础 | 预填充与解码、KV cache、算力瓶颈与访存瓶颈 | | 发布 A4 |
| | L18 | 本地推理入门 | Ollama 和 llama.cpp；GGUF 格式；`OLLAMA_CONTEXT_LENGTH` 导致的静默截断 | llama.cpp README | |
| 10 | L19 | 批处理与调度 | 静态批、连续批、`-np` 并发槽位 | Orca 论文 | |
| | L20 | 前缀复用 | `cache_prompt`、RadixAttention；agent 与推理服务的协同设计 | SGLang 论文（只讲不做） | |
| 11 | L21 | 显存与内存管理 | PagedAttention、KV 量化（为什么在 CPU 上反而变慢） | vLLM 论文（只讲不做） | |
| | L22 | 推测解码 | 草稿模型、接受率与加速比、草稿长度怎么选 | Leviathan et al. | |
| 12 | L23 | 量化 | 权重量化档位、量化对质量的影响 | GPTQ/AWQ 导读 | |
| | L24 | MoE | 激活参数和总参数、为什么 30B-A3B 生成快但占内存大 | DeepSeek-V3 技术报告 | A4 截止 |
| 13 | L25 | 全栈：多模型路由 | 主 agent 用云端模型、子 agent 用本地模型；"不信任"带来的重复劳动 | `tool-subagent` 模型选择 | 发布 A5 |
| | L26 | 全栈：系统级优化 | 解决率、成本、耗时三者的取舍；排行榜方法论 | | |
| 14 | L27 | 前沿与开放问题 | 长任务、记忆、多 agent、评测污染 | | A5 截止 |
| | L28 | 期末项目指南 | 选题建议、复现要求、展示形式 | | 期末项目（可选，获取证书需要） |

## 评分（证书用，非学分）
A1 10%，A2 15%，A3 20%，A4 20%，A5 15%，期末项目 20%。各作业都有自动检查加报告；排行榜只用来展示，不计入分数。

## 预计花费
整门课的 DeepSeek API 费用预计在 100 元以内。M0 实测：原 20 题每题约 $0.02，难题集每题约 $0.04，A1 的自动检查每次约 $0.003。最终数字会在试做阶段校准后公布。
