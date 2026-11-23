# 课程大纲

共 14 周授课 + 2 周项目期，37 讲（第 2、3、8、10、12 周各 2 讲，其余每周 3 讲；第 3、6、12、13、16、22、31、35、36 讲为新增或重写中，讲稿待写）。**每讲由三部分组成**：一段 3–5 分钟的导读视频（B 站，程序合成，见文末说明），讲稿全文，以及必读材料加一个 10–20 分钟、写明预期结果的小练习。每周约 2 小时用于阅读和练习，加上作业时间，每周合计见下面的"学习节奏"。学习问题请到 [Discussions 的 Q&A](https://github.com/ODearEvanHansen/agentharness/discussions/new?category=q-a) 提问，脚本问题和内容错误请[提 Issue](https://github.com/ODearEvanHansen/agentharness/issues/new/choose)；作业 0 到 [Discussions](https://github.com/ODearEvanHansen/agentharness/discussions/new?category=show-and-tell&title=%E4%BD%9C%E4%B8%9A%200%20%E6%89%93%E5%8D%A1) 发帖打卡。

**先修**：熟练使用 Python；会用 git 和 Docker；了解 HTTP；能读简单的 HTML/JavaScript 和 TypeScript（作业 1 有前端部分，作业 2、3 需要读或写少量 TS）。**不要求**有 GPU 或机器学习背景。

**硬件**：需要 x86_64 Linux，或 Windows + WSL2，**不支持 macOS**；磁盘 100GB（每个 SWE-bench 评测镜像约 3GB，建议按题拉取、用完删除）。
- **16GB 内存**：可以完成作业 0–3，以及作业 4 的推理实验（8B 模型）。
- **32GB 内存**：作业 4 的 L3 和作业 5 需要（30B-A3B 模型常驻内存约 28GB）。内存不足 32GB 的学员，作业 5 可以改用课程团队提供的本地模型基线数据，评分只看路由设计和云端实验。

| 周 | 讲次 | 主题 | 要点 | 阅读 / 源码 | 作业 |
|---|---|---|---|---|---|
| 1 | L1 | 课程导论：agent 系统是什么 | 模型 + 循环 + 工具；本课路线；**安全**：隔离、key 泄露、提示注入 | DSH README（中文版） | **发布 A0（本周末截止）** |
|  | L2 | DeepSeek API 入门 | tool calling、思考模式与 `reasoning_content`、前缀缓存计价、一个约 20 行的最小 agent 循环 | DeepSeek API 文档 |  |
|  | L3 | 用好编码 agent | DSH 实录、权限与审批、AGENTS.md 写法、worktree 多会话并行、跑到可验证终态的外层循环、十个常见坑 | [CS2680 第 2 讲幻灯片](https://cs2680.seas.harvard.edu/slides/2_agent_use_1.pdf)、[CS2680 第 3 讲幻灯片](https://cs2680.seas.harvard.edu/slides/3_agent_use_2.pdf) |  |
| 2 | L4 | DSH 导论 | Cordis 插件架构、profile 与 patch、SDK 与运行时；如何关闭会话日志上传 | DSH `docs/user`、`python-sdk.md` | **发布 A1** |
|  | L5 | 事件与会话日志 | turn/step/tool 事件、session.v4 日志、用量字段；子 agent 事件的最小示例 | `framework/events.md` |  |
| 3 | L6 | 提示工程 | 八种技术；哪些对推理模型已过时 | [CS2680 第 4 讲幻灯片](https://cs2680.seas.harvard.edu/slides/4_agent_design_1.pdf) |  |
|  | L7 | Agent loop 剖析（上） | 一个 step 的生命周期、请求组装、工具分发 | `agent-loop/README.md` |  |
| 4 | L8 | Agent loop 剖析（下） | 取消、失败恢复、配对补齐、并行工具调用 | `agent-loop/src/agent.ts` | **A1 截止 · 发布 A2** |
|  | L9 | 工具设计 | 工具粒度对步数的影响、编辑工具、输出截断 | DSH `tools` 子系统文档 |  |
|  | L10 | 上下文工程 | 系统提示、压缩、工具结果裁剪；token 都花在了哪里 | `compaction` 子系统 |  |
| 5 | L11 | 记忆：让 agent 记住该记的 | 上下文窗口与记忆存储；一条记忆的六个决定（写不写、表示、存储、读写时机与取回、归纳、遗忘）与归属；有效时间与出处；失败模式与评估；DSH 的 AGENTS.md 只追加刷新；有/无笔记对照：只记模型推不出来的 | [CS2680 第 2 讲](https://cs2680.seas.harvard.edu/slides/2_agent_use_1.pdf)、[第 6 讲](https://cs2680.seas.harvard.edu/slides/6_agent_design_3.pdf)幻灯片、[MemGPT](https://arxiv.org/abs/2310.08560)、[CoALA](https://arxiv.org/abs/2309.02427) | A3 选做 L6 |
|  | L12 | 多 agent 架构（讲稿待重写，暂为原「子 agent 与编排」） | 八种架构、任务拆分、子任务描述、六种拆分失败、通信、MCP vs A2A；实验：单 agent vs 双子 agent 同题对照；DSH 的 spawn/fork、深度上限、结果回传 | `subagent/README.md`、[CS2680 第 5 讲幻灯片](https://cs2680.seas.harvard.edu/slides/5_agent_design_2.pdf) |  |
|  | L13 | 可靠性 | 0.95ⁿ 复利、五层故障模型与修法、检查点/回滚、超时 | [CS2680 第 6 讲幻灯片](https://cs2680.seas.harvard.edu/slides/6_agent_design_3.pdf) |  |
| 6 | L14 | 评测基础设施 | 容器隔离、出网白名单（以及它防不住什么）、镜像分发、可复现性 | `infra/` |  |
|  | L15 | 评测 | SWE-bench 的任务形态（issue → patch → 测试）、Verified 子集、数据污染、为什么需要难题集 | SWE-bench 论文 |  |
|  | L16 | 评测 II：统计与方法 | pass@k 与 pass^k、评测与被测分离、评分器偏差、配对比较与 bootstrap、每次成功成本、四层数据泄漏、代表性基准 | [CS2680 第 7 讲幻灯片](https://cs2680.seas.harvard.edu/slides/7_agent_design_4.pdf) |  |
| 7 | L17 | 前缀缓存与 request series | 追加与改写的区别；在每一步写入当前时间的代价 | `agent-loop` README |  |
|  | L18 | 插件开发 | `tools/post-execute`、`agent/pre-step`、`agent/request-error`；`.ts` 免编译加载 | `develop/basic` | **A2 截止 · 发布 A3** |
|  | L19 | 成本与可靠性 | 重试、预算、flash 和 pro 怎么选 |  |  |
| 8 | L20 | 实验方法 | 对照、只改一个变量、重复与方差、统一计价口径 |  | **发布期末项目指南** |
|  | L21 | 课程团队方案复盘 | 一个在小实验里有效、在真实任务上无效的插件 |  |  |
| 9 | L22 | LLM 内部 | 请求六阶段、Transformer 块、注意力 O(n²) 与 FlashAttention、GQA/MLA | [CS2680 第 9 讲幻灯片](https://cs2680.seas.harvard.edu/slides/9_llm_serving_basics_1.pdf) |  |
|  | L23 | 推理基础 | 预填充与解码、KV cache、算力瓶颈与访存瓶颈 |  | **发布 A4**（每个实验标注了学完哪一讲再做） |
|  | L24 | 本地推理入门 | Ollama 和 llama.cpp、GGUF；静默截断类问题的排查方法 | llama.cpp README |  |
| 10 | L25 | 批处理与调度 | 静态批处理与连续批处理、并发槽位 | Orca 论文 | **A3 截止** |
|  | L26 | 前缀复用 | `cache_prompt`、RadixAttention、agent 与推理服务的协同设计 | SGLang 论文（只讲不做） |  |
| 11 | L27 | 显存与内存管理 | PagedAttention、KV 量化 | vLLM 论文（只讲不做） |  |
|  | L28 | 推测解码 | 草稿模型、接受率与加速比 | Leviathan et al. |  |
|  | L29 | 量化 | 权重量化档位与质量 | GPTQ/AWQ 导读 |  |
| 12 | L30 | MoE | 激活参数与总参数 | DeepSeek-V3 技术报告 | **A4 截止** |
|  | L31 | 分布式推理 | DP/TP/PP/EP、通信、预填充/解码分离（只讲概念；选做 llama.cpp `--rpc` 双机演示） | [CS2680 第 10 讲幻灯片](https://cs2680.seas.harvard.edu/slides/10_llm_serving_basics_2b.pdf)、[CS2680 第 11 讲幻灯片](https://cs2680.seas.harvard.edu/slides/11_llm_serving_basics_3.pdf) |  |
| 13 | L32 | 多模型路由 | 主 agent 用云端模型、子 agent 用本地模型；"不信任"带来的重复劳动 | `tool-subagent` 模型选择 | **发布 A5** |
|  | L33 | 系统级优化 | 解决率、成本、耗时三者的取舍；排行榜方法论 |  |  |
|  | L34 | agent 安全：提示注入与防护 | 间接注入与越界动作、`tools/pre-execute` 防护插件的效果与误拦；末尾速览前沿开放问题（长任务、记忆、多 agent、评测污染） | [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/llm-top-10/)（LLM01、LLM06）；[OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/) | A3 选做 L5（第 14 周末前可单独补交） |
| 14 | L35 | 自我进化 harness | Reflexion、ADAS、ACE；ACE 在 DeepSeek 上复现 | [CS2680 第 4 讲幻灯片](https://cs2680.seas.harvard.edu/slides/4_agent_design_1.pdf) |  |
|  | L36 | 前沿问题与课程回顾 | 长任务、多 agent、评测污染；学员使用日志复盘 | [CS2680 第 8 讲幻灯片](https://cs2680.seas.harvard.edu/slides/8_agent_design_5.pdf) |  |
|  | L37 | 期末项目答疑与展示安排 | 复现要求、报告与展示形式 |  | A5 与期末项目在**第 16 周末**截止 |

## 学习节奏

本课程是自学进度，**没有统一开课日期**：你开始学的那一天就是第 1 周。表中的\"截止\"只是建议节奏，没有人会因为你晚交而扣分。

每周时间 = 阅读和练习约 2 小时 + 作业时间。作业时间按各作业 README 的估算（A0 1–2 小时，A1 6–10，A2 15–20，A3 12–18，A4 16–22，A5 12–18）平均摊到它的发布周到截止周：

| 周 | 当周作业 | 每周合计（小时） |
|---|---|---|
| 1 | A0 | 3–4 |
| 2–3 | A1 | 5–7 |
| 4–6 | A2 | 7–9 |
| 7–8 | A3 | 5–6.5 |
| 9–10 | A3 + A4 | 9–12 |
| 11–12 | A4 | 6–7.5 |
| 13–14 | A5 | 5–6.5 |
| 15–16 | A5 + 期末项目 | 3–4.5，另加期末项目 |

全课合计约 **91–119 小时**（阅读 29 + 作业 62–90），不含期末项目。

**每周不到 6 小时？用 24 周节奏**：把原来每 2 周的内容摊到 3 周，每周约 3.5–4.5 小时。

| 原节奏 | 1–2 周 | 3–4 | 5–6 | 7–8 | 9–10 | 11–12 | 13–14 | 15–16 |
|---|---|---|---|---|---|---|---|---|
| 24 周节奏 | 1–3 周 | 4–6 | 7–9 | 10–12 | 13–15 | 16–18 | 19–21 | 22–24 |

## 按需学习路线

不打算学完全课，也可以只做其中一部分。所有路线都要先完成[作业 0](assignments/a0.md) 关卡 1–3。

| 只想做 | 需要的作业部分 | 建议看的讲次 |
|---|---|---|
| 只做 A1（看清 agent） | A0 | L1、L2、L4、L5 |
| 只做 A2（写 agent loop） | A0 | L1、L2、L7–L9、L14、L15 |
| 只做 A3（优化 DSH） | A0；A2 README 的\"准备\"和\"在容器里跑小题\"两节（学会用运行器跑题） | L1、L2、L4、L5、L10、L11、L14、L15、L17–L21 |
| 只做 A4（本地推理） | A0 关卡 1–2 | L23–L30 |
| 只做 A5（全栈） | A0；A4 的 L1（Ollama 接入 DSH），内存不足 32GB 时改用 A5 提供的本地基线 | L4、L5、L12、L23、L24、L32、L33 |

## 评分权重（用于自评，不计学分）
A0 是必做项，只判是否完成，作业 1 以它为前置。A1 占 10%，A2 占 15%，A3 占 20%，A4 占 20%，A5 占 15%，期末项目占 20%。每个作业都有自动检查和报告两部分。排行榜只做展示，不计入分数。

## 预计花费（DeepSeek API）
以下数字来自试做阶段（开课前课程团队的完整试做）的实测，按官方高峰价计算：原 20 题每题约 0.13 元（跑一遍约 2.7 元），难题集每题约 0.27 元（跑一遍约 5.3 元），作业 1 跑一次自动检查约 0.02 元。

| 部分 | 估算 |
|---|---|
| A0–A1 | 几元 |
| A2 | 不到 13 元 |
| A3 | 必做部分约 33 元；如果每天在 20 题上调试 10 轮、持续两周（140 轮 × 每轮 2.4–3.4 元），会到 **340–480 元** |
| A4 | 只用本地模型，不花 API 费用 |
| A5 | 必做部分的云端花费不到 7 元 |
| 期末项目 | 建议控制在 100 元以内 |

调试请先在 8 道小题或几道题的子集上进行，跑通后再上 20 题。**重跑同样要计费**：每次重跑 20 题都是一轮完整的花费。全课总额要等外部试学员做完后才能校准，届时公布。

### 最低预算路线

按下面的做法，全课（不含期末项目）的 API 花费大约 **75 元**：

| 部分 | 做法 | 估算 |
|---|---|---|
| A0–A1 | 照常做 | 约 7 元 |
| A2 | 照常做 | 不到 13 元 |
| A3 | 调试只用 8 道小题或 5 题子集（约 20 轮 × 5 题 × 0.13 元 ≈ 13 元），最后只跑 1–2 次完整的 20 题 | 必做约 33 元 + 调试约 13 元 ≈ 46 元 |
| A4 | 只用本地模型 | 0 |
| A5 | 只跑必做部分 | 不到 7 元 |

假设：按 DeepSeek 官方人民币高峰价（deepseek-flash 每百万 token：缓存命中输入 0.04 元、未命中输入 2 元、输出 8 元；低峰价减半），每题花费与试做阶段相近（原 20 题每题约 0.13 元）。你的 agent 步数更多时花费会更高。

**建议预充一笔固定的小额余额（例如 100 元）作为硬上限**，不开自动充值。余额用完 API 会直接报错，不会超支。

## 关于视频
导读视频由程序合成：画面和字幕由脚本生成，配音由 DeepSeek TTS 合成，视频里的演示数据都来自真实运行。完整内容以讲稿和阅读材料为准。

本课程的结构参考了 Harvard CS2680，但与哈佛大学及 CS2680 课程团队没有任何关联，也未获其背书。
