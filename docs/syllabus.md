# 课程大纲

共 14 周授课 + 2 周项目期，37 讲（第 2、3、8、10、12 周各 2 讲，其余每周 3 讲；第 3、6、12、13、16、22、31、35、36 讲为新增或重写中，讲稿待写）。**每讲由三部分组成**：一段 3–5 分钟的导读视频（B 站，程序合成，见文末说明），讲稿全文，以及必读材料加一个 10–20 分钟、写明预期结果的小练习。每周约 2 小时用于阅读和练习，加上作业时间，每周合计见下面的"学习节奏"。学习问题请到 [Discussions 的 Q&A](https://github.com/ODearEvanHansen/agentharness/discussions/new?category=q-a) 提问，脚本问题和内容错误请[提 Issue](https://github.com/ODearEvanHansen/agentharness/issues/new/choose)；作业 0 到 [Discussions](https://github.com/ODearEvanHansen/agentharness/discussions/new?category=show-and-tell&title=%E4%BD%9C%E4%B8%9A%200%20%E6%89%93%E5%8D%A1) 发帖打卡。

**先修**：熟练使用 Python；会用 git 和 Docker；了解 HTTP；能读简单的 HTML/JavaScript 和 TypeScript（作业 1 有前端部分，作业 2、3 需要读或写少量 TS）。**不要求**有 GPU 或机器学习背景。

**硬件**：需要 x86_64 Linux，或 Windows + WSL2，**不支持 macOS**；磁盘 100GB（每个 SWE-bench 评测镜像约 3GB，建议按题拉取、用完删除）。
- **16GB 内存**：可以完成作业 0–3，以及作业 4 的推理实验（8B 模型）。
- **32GB 内存**：作业 4 的 L3 和作业 5 需要（30B-A3B 模型常驻内存约 28GB）。内存不足 32GB 的学员，作业 5 可以改用课程团队提供的本地模型基线数据，评分只看路由设计和云端实验。

| 周 | 讲次 | 主题 | 要点 | 阅读 / 源码 | 作业 |
|---|---|---|---|---|---|
| 1 | L1 | 课程导论：agent 系统是什么 | agent = 模型 + 循环 + 工具；agent 即新型计算机（模型/上下文/工具/harness）；北极星指标：元/成功任务；agent 负载特点→系统问题地图（即课程顺序）；AI 编程六级；agent = 模型 × harness 与「让周围系统可靠」四条实践；期末十个定量问题；安全、隐私与 AI 使用约定 | CS2680 第 1 讲公开幻灯片（优化目标、workload→系统问题、Agentic Coding Levels、课程问题清单）；docs/setup.md《环境搭建指南》 | **发布 A0（本周末截止）** |
|  | L2 | DeepSeek API 入门 | Chat Completions 请求结构；API 无状态与上下文即工作记忆；工具调用由模型提议、调用方执行；思考模式回传 reasoning_content、思考按输出计费；最小 agent 循环；前缀缓存概念、50 倍计价差、前缀稳定原则；高峰/低峰价 | DeepSeek API 文档（Chat Completions、思考模式、上下文硬盘缓存）；tools/usage_cost.py |  |
|  | L3 | 用好编码 agent | 使用者视角：开工前上下文构成、仓库按需切片、模型提议 harness 执行（真实轨迹）；权限：沙箱模式 × 审批策略、失败即关闭；AGENTS.md 该写/别写清单与加载顺序；定义「做完」；流程即 harness（/plan、流程型 skill）；外层循环跑到可验证终态（DSH goal）；扩展三轴；git worktree 手工并行及其上限；十个常见坑与好的迭代循环 | CS2680 第 2、3 讲与作业复盘公开幻灯片；DSH docs/subsystems/permission-presets、approval、goal、worktrees；packages/context/agent-instructions/README |  |
| 2 | L4 | DSH 架构与扩展机制 | harness 与插件；单体/模块化/微内核三架构，DSH 一切皆插件（含 loop）；一个 step 的流水线与挂载点、「模型可见即已记录」；四种扩展机制 skill/MCP/hook/plugin 各答一个问题及在 loop 上的位置；skill 渐进披露、MCP 信任边界、hook 事件面、plugin 分发；六题分类练习；SDK、profile/patch、关闭日志上传 | CS2680 第 2 讲（扩展机制）与第 8 讲（harness 架构）公开幻灯片；DSH docs/architecture.zh.md、docs/subsystems/skills.zh.md、packages/mcp/README、experimental/hooks-claude-code/README | **发布 A1** |
|  | L5 | 观测：事件、日志与成本 | 可观测性是一等问题；嵌套轨迹 会话⊃轮次⊃步骤⊃请求/工具⊃子 agent；事件（直播、无用量）vs 会话日志（账本、可重建请求）；从日志算每步时间与成本；子 agent 建树与成本汇总；两个常见误区与 OTel；看日志的三个问题 | CS2680 第 1 讲 p43；DSH docs/subsystems/session、otel、token-meter；tools/usage_cost.py |  |
| 3 | L6 | 提示工程 | 提示/上下文/harness/目标四个「工程」层次；八种技术（零样本、少样本、角色、思维链、思维树、自洽、提示链、元提示）的适用与切换条件及选择路线；八种技术在 agent 中如何被 harness 吸收；对推理模型已过时的做法与思考预算；工具描述也是提示；五条写提示实践、换模型要重调 | CS2680 第 4 讲 p28–p40 公开幻灯片；DeepSeek-R1 技术报告（提示建议一节）；assignment2/run.py 任务提示 |  |
|  | L7 | Agent loop 剖析（上） | ReAct（只推理/只行动/交替）；二十行最小循环与停止规则；harness 设计者四个工作点与三组件同窗；Agent = Model × Harness；step 生命周期（组装→请求→分发→记录）、会话日志为唯一事实；组装稳定与前缀缓存；错误也是结果；贯穿例题（Django 后台空选项被覆盖）三种做法对照 | ReAct（Yao 等，arXiv 2210.03629）；DSH packages/core/agent-loop/README.md（dsh-v0.2.2-rc.2）；assignment2/README.md |  |
| 4 | L8 | Agent loop 剖析（下） | 停止规则四种（无调用、步数、成本/时间、卡住检测）；DSH guard：重复调用提醒与工具限时；tool_call 配对与 400；取消（ABORTED_BEFORE_DISPATCH）与失败（TOOL_OUTCOME_UNKNOWN / TOOL_NOT_STARTED）；请求层 vs loop 层重试、只自动重试幂等操作；并行上限与 exclusive barrier；ReAct 之外：Reflexion、计划后执行、树搜索 | DSH packages/core/agent-loop/README.md、packages/guard/README.md；Reflexion（Shinn 等，2023） | **A1 截止 · 发布 A2** |
|  | L9 | 工具设计 | 工具五类与风险梯度；找代码四法（grep/glob、语义索引与仓库地图、外部信号、LSP）；改代码四法（整文件、diff、查找替换、结构化）及成本×鲁棒性；DSH edit/apply_patch/write 与先读后写策略；shell 四属性与执行工具五要点；五种附加工具（含询问用户）；五条设计原则；小题 4.9 vs 2.3 请求、SWE 20 题对照、SWE-agent 消融 | SWE-agent（Yang 等，2024）；Aider repo map 文档；DSH docs/tool-catalog.zh.md |  |
|  | L10 | 上下文管理 | 上下文有限三理由（成本、延迟、注意力）；Lost in the Middle 与 Context Rot；窗口解剖；四级阶梯：准入、外置、变换、压缩（各含手段与外部例子）；每级的前缀缓存代价（本课补充）及例题算账；DSH 各级插件与阈值（spill、pruner 8192/4096/1024、compaction 0.8 与 16%）；五种上下文失败与修法 | Liu 等《Lost in the Middle》（TACL 2024）；Chroma《Context Rot》；Breunig《How Contexts Fail and How to Fix Them》（2025）；DSH packages/compaction、packages/spill README |  |
| 5 | L11 | 记忆：让 agent 记住该记的 | 上下文窗口 vs 记忆存储；一条记忆的六个决定与归属；写入四档光谱（明确请求、规则、分类器、定期复审）；四种形态与四种存储；读写时机与取回五信号；归纳与触发时机；遗忘、有效时间与出处；失败模式（过期、记忆幻觉、取回失败、过度归纳、持久注入、污染膨胀、泄露）与评估、LoCoMo/LongMemEval/BEAM；DSH 文件记忆；仓库笔记对照实验 | LoCoMo（ACL 2024）、LongMemEval（ICLR 2025）、BEAM（ICLR 2026）；Mem0、Graphiti 文档；DSH packages/context/agent-instructions | A3 选做 L6 |
|  | L12 | 多 agent 架构 | 多 agent 的四个理由；控制/通信/任务三张图；八种架构（监督者-工人、层级、流水线、市场、黑板、委员会、蜂群、动态拓扑）及典型弱点；六种切法与子任务规格八要素；粒度公式与六种拆分失败；通信四维度、类型化消息与幂等键；MCP vs A2A（Agent Card、任务生命周期）；DSH spawn/fork/maxDepth/wait_agent/Team；十六 agent C 编译器案例；单 agent vs 加子 agent 同题对照 | Anthropic「How we built our multi-agent research system」「Building a C compiler with a team of parallel Claudes」；Cognition「Don't Build Multi-Agents」；Towards a Science of Scaling Agent Systems；A2A 协议规范；DSH packages/subagent、team/agent-team |  |
|  | L13 | 可靠性：错在哪一层 | 误差复利 0.95ⁿ 与两条杠杆；日志实测：bash 非零退出 5.1%、错误不预测失败、步数与难度混杂；故障注入 p=0/0.1/0.2/卡住 结果与恢复策略；看得见 vs 静默失败；五层故障模型（规格、harness、模型、工具、环境）的例子与修法；检查点与回滚、DSH 先读后改与版本过期；步数/成本/时间预算、超时、阻塞扇出、幂等键；为失败而设计五句话 | Where LLM Agents Fail and How They Can Learn from Failures；Why Do Multi-Agent LLM Systems Fail?（MAST）；Beyond the Leaderboard；The Danger of Overthinking；DSH packages/fs/fs-observation-policy、shell/bash-local |  |
| 6 | L14 | 沙箱与评测基础设施 | 评测循环（重置→预算内行动→判分）与任务/试次/轨迹/结果四术语；agent harness 与评测 harness 分离（隐藏测试、只读挂载、拒绝符号链接）；容器+--internal 网络+出网白名单；隔离光谱（DSH bwrap/Landlock 三模式→容器/微虚拟机/远程执行，先沙箱后审批）；白名单防不住什么；镜像分发与坑；可复现性 | Harvard CS2680 notes/agent-evaluation（评测循环、两个 harness 分离）；infra/README.md；docs/setup.md；DSH packages/sandbox/README.md |  |
|  | L15 | 评测 I：SWE-bench | 五种评测目标；以 Django 后台空选项题为例讲 FAIL_TO_PASS/PASS_TO_PASS；端到端 vs 组件评测；课程 20 题分层抽样与结果（无 agent 14、loop 18、DSH 17、难题集 10/8）；基准地图（SWE-bench 变体、Terminal-Bench、OSWorld、τ-bench、GAIA）；单轮指令的局限；四层泄漏；饱和与对策 | Harvard CS2680 第 7 讲幻灯片与 notes/agent-evaluation；SWE-bench / SWE-bench Verified 论文；Terminal-Bench、τ-bench 说明页 |  |
|  | L16 | 评测 II：统计与方法 | 贯穿例子 sklearn 多输出概率预测题五次成三次；Task/Trial/Trajectory/Outcome；agent harness 与 evaluation harness 分离；pass@k vs pass^k（0.8/3 例）与无偏估计（3/5 → 0.90/0.30）；DSH 十题×五次：pass@1 0.48、pass@5 0.60、pass^5 0.40；重复次数 vs 题目数量两种噪声；评分器三类与偏差（LLM 裁判的位置/冗长/自偏好）；每次成功成本 0.295 元 vs 每次尝试 0.142 元；配对比较与配对 bootstrap（−0.32 [−0.60,−0.08] 及其局限）；为自己的 agent 设计评测五步与报告清单 | Harvard CS2680 第 7 讲幻灯片与 notes/agent-evaluation；Chen et al. 2021（Codex，pass@k 无偏估计）；Yao et al. 2024 τ-bench（pass^k）；Kapoor et al. AI Agents That Matter |  |
| 7 | L17 | 前缀缓存与 DSH | 命中:未命中:输出 = 1:50:200 的价格；追加式请求结构；Django 后台空选项题逐步命中曲线；怎样在会话日志读 usage 与找前缀断点；20 题汇总（命中率 95.8%，缓存保住后输出占近六成）；时间戳反例与 append 实验；DSH request series 与 in-history 追加；缓存清单（128 块、子 agent 冷启动、过期、缓存感知路由）；改写历史的反成本 | DSH packages/core/agent-loop/README.md（request series）；DeepSeek 上下文缓存文档；Harvard CS2680 第 8 讲（稳定前缀） |  |
|  | L18 | 插件开发 | 插件与钩子概念（扩展机制地图回指第 4 讲）；loop 上的插口位置（pre-step、request-error、pre/post-execute、turn-stopping）；挂载点→典型用途；最小插件；护栏插件（PreToolDecision 四种决定）；waterfall 规则；patch 加载与绝对路径；用基线验证护栏：注入 5/21→5/21→0/21，误拦 4 次，费用 0.16→0.21 元；好插件标准 | DSH docs/user/develop/basic、docs/subsystems/tools.md、docs/subsystems/core.md；assignment3/README.md 选做 L5；第 4 讲扩展机制地图 | **A2 截止 · 发布 A3** |
|  | L19 | 成本与速度 | 每次成功成本为北极星（含失败试次，0.144 元/成功）；六因子成本拆解；减轮次、减步数（并行读取实测仅 1/458 步）、真的需要 LLM 吗；输出才是大头（约 2% token 花 57% 钱）、输出约束与自适应推理强度；单价：缓存、低峰、三种路由；每项节省的反成本（本地路由、无 agent、笔记实测）；预算=成功试次 p95×2 与停滞即停；关键路径与工具时间（43%/60%）；编排提速四法；推测动作；单体/模块化/微内核与 DSH 的位置（一切皆插件、只追加日志、STALE 编辑检查、外部 harness 子 agent） | Harvard CS2680 第 8 讲幻灯片与 notes/cost-effective-agents；AI Agents That Matter；DSH README（everything-is-a-plugin）、agent-loop README |  |
| 8 | L20 | 实验方法 | 对照实验概念；六步迭代循环（先写预测、一次一改、无效即删）；基线阶梯（无 agent→默认→重跑→简单替代方案）；同配置两次的噪声（17/18 题，单题费用比 0.47–3.23）；逐题配对（回指第 16 讲 bootstrap）；事先定判断规则、不显著≠等价；统一计价与失败计入成本；运行卫生（输出目录、worktree、计时不干扰）；用轨迹做诊断与受控干预；报告清单 | Harvard CS2680 作业复盘（feedback_assignment）、notes/cost-effective-agents「公平成本实验」、notes/agent-evaluation「用轨迹决定改什么」；assignment3/README.md 方法要求 | **发布期末项目指南** |
|  | L21 | 案例：工具输出裁剪 | 工具输出裁剪的想法与基线；动手前先算上限（按命中/未命中/输出拆账单）；waterfall 实现；小实验成本降到约 1/3；SWE 20 题 17 题 2.27 元，落在两次基线 2.24–2.44 元之间；第一版解释未查日志而被推翻（方法教训）；该查的五个日志问题（作业三 L2 由学员自己找原因）；找最贵路径表；教训与反成本 | assignment3/templates/trim-tool-output.ts；Harvard CS2680 第 8 讲（反成本、优化循环）与 notes/cost-effective-agents「Find the expensive path」；DSH tool-bash-persistent README |  |
| 9 | L22 | LLM 内部：一句话在模型里走一遍 | 请求六阶段（分词→调度→预填充→解码→反分词→流式）；字节级 BPE 与 token 计费；采样参数与停止条件；Transformer 块（嵌入、RMSNorm、残差、注意力、SwiGLU 前馈、输出层）；Q/K/V 与因果掩码；注意力 O(n²) 与 FlashAttention；多头、GQA/MQA、KV 公式；MLA、滑动窗口、稀疏/线性注意力；参数分布与 2N FLOP/token | Harvard CS2680 L9 幻灯片（LLM 入门）；Vaswani et al. 2017《Attention Is All You Need》；Dao et al. 2022 FlashAttention；Ainslie et al. 2023 GQA；DeepSeek-V2 技术报告（MLA） |  |
|  | L23 | 推理性能估算：动手之前先算账 | 三种上限（算力/带宽/容量）；kernel 时间 ≈ max(字节÷带宽, 运算÷算力)；算术强度与脊点；预填充估算（2N FLOP/token）与解码上限（带宽÷(权重+KV)）；CPU roofline 实测；线程扩展；KV 随上下文增长；CPU vs GPU（H200）概念对照；MBU/MFU | Harvard CS2680 L10a/10b 幻灯片（GPU 入门）；Williams et al. 2009 Roofline；课程 exp/roofline.md；作业四 E2/E5 | **发布 A4**（每个实验标注了学完哪一讲再做） |
|  | L24 | 本地模型：跑起来，再证明它真在干活 | 本地推理的得失；Ollama vs llama-server；GGUF 与元数据；内存估算（权重 + 144 KiB×-c）与 OOM；静默失败（含静默退回云端）；就绪看 /health；读日志与 timings 对账；剖析方法：时间线→单点→假设→改一处再测；会推理≠会用工具 | docs/setup-local.md 第一、三部分；assignment4/README.md L1；llama.cpp server README；Harvard CS2680 L10b 剖析方法部分 |  |
| 10 | L25 | 批处理与调度：一个长提示卡住了谁 | LLM 服务为何特殊；TTFT/TBT/TPOT/E2E、P99 与 goodput；吞吐-交互性曲线（CPU 实测）；静态批 vs 连续批；选择性批（注意力不分摊）；预填充优先 vs 解码优先；分块预填充 CPU 实验；只看 P99 的陷阱；推理评测四个坑；对 agent 的启示（串行、-c÷-np、未缓存 token 作作业大小） | Harvard CS2680 L11 幻灯片；Yu et al. 2022 Orca；Agrawal et al. 2024 Sarathi-Serve；课程 exp/chunked.md、exp/batched_l25.txt；作业四 E1、L4 | **A3 截止** |
|  | L26 | 服务端前缀缓存 | 因果注意力→前缀 KV 可复用、只能精确匹配；E2 基线对照（40553→493 ms，cache_n 4617）；块哈希（vLLM，链式哈希、末块不共享）vs 基数树（SGLang RadixAttention）+ 自测；引用计数共享、LRU 及更好的淘汰准则（Marconi/SSM）；命中与公平冲突、工具调用间隙 KV 去留；llama-server 对应物（cache_prompt、--cache-ram、--cache-reuse、--slot-save-path）；agent 协同清单（含 DSH 压缩指令追加保前缀）；云端命中率 95.8% | SGLang/RadixAttention（Zheng et al.）；vLLM 自动前缀缓存文档；Marconi（混合模型前缀缓存）；选读 Parrot |  |
| 11 | L27 | KV 管理与压缩 | 多大：KV/token=2×层×KV头×头维×字节（Qwen3-8B 144 KiB，32k 4608 MiB；30B-A3B 3072 MiB 与日志对账），×长度×并发，KV 不能被批分摊；怎么管：三种浪费（预留/内部/外部碎片，公开 20–38%）、PagedAttention（M3：6.4%→90.6%）、共享与写时复制、满了排队/抢占重算/换出、按 KV 预算准入；怎么压：MHA/GQA/MLA、滑窗、稀疏注意力、SSM；KV 量化 E4（省 2158 MB 与公式 2160 吻合，但 pp 89.2→36.4、tg 10.21→9.23）及反转条件 | PagedAttention/vLLM（Kwon et al.）；MQA、GQA；DeepSeek-V2（MLA）；NSA；Mamba；KIVI |  |
|  | L28 | 推测解码 | 一轮四步（起草/验证/接受/补一个）；拒绝采样精确性证明（cat/dog/rat，α=0.7）；E=(1−α^{k+1})/(1−α)、S=E/(ck+1)、最优 k；用 free_text 数据检验公式（k=8 预测 2.43 实测 2.23，偏乐观约 9%）；验证何时免费（GPU 屋脊 206 vs CPU 约 17）；E3 k=16 反而慢；草稿器谱系（独立/自推测/Medusa/EAGLE/MTP/检索）；n-gram CPU 实验（改名任务 3.38× vs 0.6B 草稿 1.44×；写作任务负结果 0.47×）；负载决定 k、MoE/长上下文/树验证；agent 复制式推测（SuffixDecoding、Cursor、Predicted Outputs 计费） | Leviathan et al. 2023；Chen et al. 2023；Medusa；EAGLE-1/2/3；DeepSeek-V3 技术报告（MTP）；SuffixDecoding |  |
|  | L29 | 量化 | 数值格式（FP16/BF16/FP8 E4M3·E5M2/INT）；分组量化三步与 Q8_0 34 字节/32 权重；离群值与 LLM.int8()/AWQ/GPTQ/imatrix；E5 大小与速度、roofline 解释（12.57/7.34=1.71 ≈ 字节比 1.73）；W4A16 vs W8A8 vs KV 量化（KIVI、QServe）；质量三层：PPL（10.735 vs 11.169，误差 ±0.47 分不出）、KL/top-1（91.8%，P99 0.45、最大 5.8）、下游解决率（未测）；剪枝/2:4、QLoRA、更低比特（概念） | LLM.int8()；GPTQ；AWQ；FP8 Formats；KIVI；QServe；选读 QLoRA |  |
| 12 | L30 | MoE 与模型结构 | Transformer 层中前馈占大头；MoE 路由 top-k（30B-A3B：128 选 8，元数据）；从元数据估算总参数约 30.5B、激活约 3.35B；速度看激活（35.6 vs 17.25，约 2×，带宽对账约 73 GB/s）、内存看总参数（18.6 GB，32k 约 28 GB）；DeepSeek-V3 671B/37B、Mixtral vs Llama2 FLOPs；负载均衡（辅助损失、无辅助损失偏置、共享专家）；批处理与推测在 MoE 上收益变小（1.8× vs 2.5×，Cascade）；模型结构服务成本表（滑窗/稀疏/SSM/混合/MTP）；agent 小题 8/4/0 | DeepSeek-V3 技术报告（专家路由与负载均衡）；Mixtral of Experts；Switch Transformer（选读） | **A4 截止** |
|  | L31 | 分布式推理 | 下界 t_token ≥ 权重字节÷带宽（70B 140 GB，H200 约 29 ms）；集合通信（broadcast/all-gather/reduce-scatter/all-reduce/all-to-all）；DP/TP/PP/EP/SP 切什么传什么；TP vs PP 通信量（3.9 MB vs 16 KB）与气泡公式 (G−1)/(m+G−1)；llama.cpp --rpc CPU 演示（7.98 / 7.24 / 7.38，按层切不加速）；PD 分离（DistServe/Splitwise/Mooncake）与 KV 传输账（NVLink 44 ms、IB 400 ms、PCIe 625 ms；8B 32k 千兆网约 40 s）；自测：4 卡跑 70B 怎么切；对 agent：会话路由、工具间隙 KV 搬移 | Megatron-LM（张量并行）；DistServe；Splitwise；Mooncake；选读 Ring Attention、GPipe |  |
| 13 | L32 | 路由与负载均衡 | 路由两层（模型级/副本级）；LLM 服务的软状态与 web 负载均衡的区别；五种副本策略（轮询、最少负载、前缀亲和、缓存感知+负载、迁移）；CPU 实验：两台 llama-server 上轮询 vs 前缀哈希；热点、一致性哈希与迁移；按角色 vs 按难度（RouteLLM）的模型级路由与成本-质量曲线；作业五路由对照与“不信任”的隐性成本 | Preble；Llumnix；RouteLLM；SGLang router（cache-aware）；CS2680 第 11 讲课件 | **发布 A5** |
|  | L33 | 系统级优化 | 北极星指标：每道成功任务的成本；agent 负载画像（21.9 次请求、输入约为输出 48 倍、命中 95.8%）；负载特征→系统问题映射；工具间隙的 KV 去留；按请求 vs 按任务调度；分块预填充保护解码；缓存淘汰按复用价值；并发与关键路径；三指标、最简基线与帕累托前沿；排行榜方法 | Parrot；Agentix；Ayo（Teola）；Agentic AI Workload Characteristics；SGLang/RadixAttention；Marconi |  |
|  | L34 | agent 安全 | 最小代理原则；OWASP Agentic Top 10 全部十项（ASI01–ASI10）；注入载体实测（文字 0/15、脚本 5/6）；多 agent 控制流劫持与“安全不可组合”；pre-execute 拦截与两版实测；自适应攻击；六种防注入设计模式；CaMeL；指令层级与 AI Control；纵深防御清单 | OWASP Top 10 for Agentic Applications 2026；Greshake 间接提示注入；AgentPoison；Multi-Agent Systems Execute Arbitrary Malicious Code；The Attacker Moves Second；Instruction Hierarchy；CaMeL；Design Patterns for Securing LLM Agents；AI Control；AgentDojo | A3 选做 L5（第 14 周末前可单独补交） |
| 14 | L35 | 自我进化 harness | 自我进化四步循环（运行、评分、反思、修改）；改文字：Reflexion、Self-Refine；改代码：ADAS、Darwin Gödel Machine（约 $22,000/次、删日志得满分的目标黑客）；ACE 三角色、增量合并、简洁偏置与上下文坍塌；我们在 DSH+deepseek-flash 上的 ACE 复现（Reflector 只拿计数、泄题 0、贯穿例子 SymPy 模根漏零题 → 条目 b07）；训练批 1/4→2/4→2/4 属噪声；留出集因余额用完未跑，结论待定；Meta-Harness、AHE、Live-SWE-agent 与风险 | Harvard CS2680 readings（10 月 14 日）；Shinn et al. Reflexion；Madaan et al. Self-Refine；Hu et al. ADAS；Zhang et al. Darwin Gödel Machine；Zhang et al. ACE（arXiv 2510.04618）；Meta-Harness；Agentic Harness Engineering；Live-SWE-agent |  |
|  | L36 | 前沿问题与课程回顾 | 贯穿例子：同一 agent 随机题 17/20、难题 8/20；长任务与可靠性复利（0.95²⁰≈36%）、压缩与缓存冲突、轨迹即工件；多 agent 失败（MAST 十四种三类）；评测污染与钻评分器空子（DGM 删日志）；自我进化 harness 的风险（指向第 35 讲）；37 讲课程地图（五部分）；五条贯穿方法；开放问题→期末选题 | Where LLM Agents Fail；Why Do Multi-Agent LLM Systems Fail（MAST）；Darwin Gödel Machine；Meta-Harness；CS2680 第 1、6、7 讲 |  |
|  | L37 | 期末项目 | 贯穿例子“工具描述改短”走完五步：缩小问题、先写假设与基线、成对比较与重复、复现（一条命令、原始数据、锁版本、全新容器）、报告四段；五个实验坑；诚实与安全；提交物与评分 | docs/project.md；docs/setup-local.md（全新容器复现检查）；第 16、20 讲 | A5 与期末项目在**第 16 周末**截止 |

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
| 只做 A2（写 agent loop） | A0 | L1、L2、L7–L9、L14–L16 |
| 只做 A3（优化 DSH） | A0；A2 README 的\"准备\"和\"在容器里跑小题\"两节（学会用运行器跑题） | L1、L2、L4、L5、L10、L11、L14、L15、L17–L21 |
| 只做 A4（本地推理） | A0 关卡 1–2 | L22–L30 |
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
