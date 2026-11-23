# B 站投稿计划（AgentHarness 37 讲）

> 本文件只准备投稿材料，不生成视频。逐讲元数据的机器可读版本见 `meta.json`（已用脚本校验：标题 ≤80 字、简介 ≤250 字、标签 ≤10 个）。

## 总体建议

- **分区（已定）**：知识 > 校园学习（tid 208，2026-11-22 从投稿接口核对）。
- **平台（已定）**：只发 B 站；YouTube 暂不做。mp4 另挂 GitHub Releases 存档。
- **类型**：自制。**必须**在投稿页勾选“作者声明：含 AI 生成内容”（与画面右上角“AI 合成（含 AI 配音）”标识、片头说明、mp4 元数据一致，见 `videos/README.md`）。
- **单个多 P vs 分开投稿**：建议**每讲单独投稿**，再在创作中心建一个**合集**（如“AgentHarness 公开课”）把 37 个视频按讲次排序。理由：
  1. 网站每讲页面按 `videos/bilibili.json` 里**每讲一个 BV 号**嵌入播放器（`scripts/build_site.py` 的 `lecture_page`），多 P 只有一个 BV 号，无法给每讲独立链接/统计；
  2. 每讲独立标题、简介、标签，更利于搜索和推荐；
  3. 可以随课程进度逐讲发布、单独修正重传，不影响其他讲；合集仍提供连续观看体验。
- **封面**：统一模板（深色底 + 课程名 AgentHarness + 大字“第 N 讲” + 讲题 + 角标“AI 合成”），16:9，建议 1146×717 以上。各讲封面文字见下表。

## 逐讲材料

### 第 1 讲（l01）

- **标题**：【AgentHarness 第1讲】课程导论：agent 系统是什么
- **简介**：本讲：课程导论：agent 系统是什么——模型 + 循环 + 工具，以及为什么必须隔离。服务作业 A0/A1。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l01/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、智能体、SWE-bench、第1讲
- **服务作业**：A0/A1
- **封面文字**：第1讲 / 课程导论：agent 系统是什么
- **视频文件**：`videos/out/l01.mp4`（制作后）

### 第 2 讲（l02）

- **标题**：【AgentHarness 第2讲】DeepSeek API 入门
- **简介**：本讲：DeepSeek API 入门——Chat Completions、工具调用、思考模式、前缀缓存计价与最…。服务作业 A0/A1。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l02/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、智能体、SWE-bench、第2讲
- **服务作业**：A0/A1
- **封面文字**：第2讲 / DeepSeek API 入门
- **视频文件**：`videos/out/l02.mp4`（制作后）

### 第 3 讲（l03）

- **标题**：【AgentHarness 第3讲】用好编码 agent
- **简介**：本讲：用好编码 agent——DSH 实录、权限与审批、AGENTS.md、worktree 并行、外层循环、十个常见坑。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l03/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、智能体、第3讲
- **服务作业**：待定
- **封面文字**：第3讲 / 用好编码 agent
- **视频文件**：`videos/out/l03.mp4`（制作后）
- **状态**：新增讲次，讲稿待写

### 第 4 讲（l04）

- **标题**：【AgentHarness 第4讲】DSH 导论
- **简介**：本讲：DSH 导论——Cordis 插件架构、profile 与 patch、SDK 与运行时。服务作业 A1。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l04/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、智能体、SWE-bench、第4讲
- **服务作业**：A1
- **封面文字**：第4讲 / DSH 导论
- **视频文件**：`videos/out/l04.mp4`（制作后）

### 第 5 讲（l05）

- **标题**：【AgentHarness 第5讲】事件与会话日志
- **简介**：本讲：事件与会话日志——turn、step、tool 事件，会话日志 v4 与用量字段。服务作业 A1。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l05/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、智能体、SWE-bench、第5讲
- **服务作业**：A1
- **封面文字**：第5讲 / 事件与会话日志
- **视频文件**：`videos/out/l05.mp4`（制作后）

### 第 6 讲（l06）

- **标题**：【AgentHarness 第6讲】提示工程
- **简介**：本讲：提示工程——八种技术，以及哪些对推理模型已过时。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l06/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、智能体、第6讲
- **服务作业**：待定
- **封面文字**：第6讲 / 提示工程
- **视频文件**：`videos/out/l06.mp4`（制作后）
- **状态**：新增讲次，讲稿待写

### 第 7 讲（l07）

- **标题**：【AgentHarness 第7讲】Agent loop 剖析（上）
- **简介**：本讲：Agent loop 剖析（上）——一个 step 的生命周期、请求组装、工具分发。服务作业 A1。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l07/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、智能体、SWE-bench、第7讲
- **服务作业**：A1
- **封面文字**：第7讲 / Agent loop 剖析（上）
- **视频文件**：`videos/out/l07.mp4`（制作后）

### 第 8 讲（l08）

- **标题**：【AgentHarness 第8讲】Agent loop 剖析（下）
- **简介**：本讲：Agent loop 剖析（下）——取消、失败恢复、配对补齐、并行工具调用。服务作业 A2。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l08/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、智能体、SWE-bench、第8讲
- **服务作业**：A2
- **封面文字**：第8讲 / Agent loop 剖析（下）
- **视频文件**：`videos/out/l08.mp4`（制作后）

### 第 9 讲（l09）

- **标题**：【AgentHarness 第9讲】工具设计
- **简介**：本讲：工具设计——工具粒度、编辑工具、输出截断。服务作业 A2。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l09/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、智能体、SWE-bench、第9讲
- **服务作业**：A2
- **封面文字**：第9讲 / 工具设计
- **视频文件**：`videos/out/l09.mp4`（制作后）

### 第 10 讲（l10）

- **标题**：【AgentHarness 第10讲】上下文工程
- **简介**：本讲：上下文工程——系统提示、压缩、工具结果裁剪：token 都花在了哪里。服务作业 A2。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l10/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、智能体、SWE-bench、第10讲
- **服务作业**：A2
- **封面文字**：第10讲 / 上下文工程
- **视频文件**：`videos/out/l10.mp4`（制作后）

### 第 11 讲（l11）

- **标题**：【AgentHarness 第11讲】记忆：让 agent 记住该记的
- **简介**：本讲：记忆：让 agent 记住该记的——项目说明文件、跨会话笔记与记忆的代价。服务作业 A3。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l11/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、智能体、SWE-bench、第11讲
- **服务作业**：A3
- **封面文字**：第11讲 / 记忆：让 agent 记住该记的
- **视频文件**：`videos/out/l11.mp4`（制作后）

### 第 12 讲（l12）

- **标题**：【AgentHarness 第12讲】子 agent 与编排
- **简介**：本讲：子 agent 与编排——spawn 与 fork、深度限制、结果回传。服务作业 A1。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l12/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、智能体、SWE-bench、第12讲
- **服务作业**：A1
- **封面文字**：第12讲 / 子 agent 与编排
- **视频文件**：`videos/out/l12.mp4`（制作后）

### 第 13 讲（l13）

- **标题**：【AgentHarness 第13讲】可靠性
- **简介**：本讲：可靠性——0.95ⁿ 复利、五层故障模型、检查点与回滚、超时。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l13/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、智能体、第13讲
- **服务作业**：待定
- **封面文字**：第13讲 / 可靠性
- **视频文件**：`videos/out/l13.mp4`（制作后）
- **状态**：新增讲次，讲稿待写

### 第 14 讲（l14）

- **标题**：【AgentHarness 第14讲】评测基础设施
- **简介**：本讲：评测基础设施——容器隔离、出网白名单、镜像分发与可复现性。服务作业 A2。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l14/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、智能体、SWE-bench、第14讲
- **服务作业**：A2
- **封面文字**：第14讲 / 评测基础设施
- **视频文件**：`videos/out/l14.mp4`（制作后）

### 第 15 讲（l15）

- **标题**：【AgentHarness 第15讲】评测
- **简介**：本讲：评测——SWE-bench、Verified 子集、官方 harness、数据污染与难题集。服务作业 A2。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l15/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、智能体、SWE-bench、第15讲
- **服务作业**：A2
- **封面文字**：第15讲 / 评测
- **视频文件**：`videos/out/l15.mp4`（制作后）

### 第 16 讲（l16）

- **标题**：【AgentHarness 第16讲】评测 II：统计与方法
- **简介**：本讲：评测 II：统计与方法——pass@k 与 pass^k、评分器偏差、配对比较与 bootstrap、每次成功成本、数据泄漏。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l16/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、智能体、第16讲
- **服务作业**：待定
- **封面文字**：第16讲 / 评测 II：统计与方法
- **视频文件**：`videos/out/l16.mp4`（制作后）
- **状态**：新增讲次，讲稿待写

### 第 17 讲（l17）

- **标题**：【AgentHarness 第17讲】前缀缓存与 request series
- **简介**：本讲：前缀缓存与 request series——追加还是改写？“每一步都写入当前时间”的代价。服务作业 A2。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l17/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、智能体、SWE-bench、第17讲
- **服务作业**：A2
- **封面文字**：第17讲 / 前缀缓存与 request series
- **视频文件**：`videos/out/l17.mp4`（制作后）

### 第 18 讲（l18）

- **标题**：【AgentHarness 第18讲】插件开发
- **简介**：本讲：插件开发——tools/post-execute、agent/pre-step、agent/request-e…。服务作业 A3。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l18/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、智能体、SWE-bench、第18讲
- **服务作业**：A3
- **封面文字**：第18讲 / 插件开发
- **视频文件**：`videos/out/l18.mp4`（制作后）

### 第 19 讲（l19）

- **标题**：【AgentHarness 第19讲】成本与可靠性
- **简介**：本讲：成本与可靠性——重试策略、预算控制、模型选择。服务作业 A3。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l19/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、智能体、SWE-bench、第19讲
- **服务作业**：A3
- **封面文字**：第19讲 / 成本与可靠性
- **视频文件**：`videos/out/l19.mp4`（制作后）

### 第 20 讲（l20）

- **标题**：【AgentHarness 第20讲】实验方法
- **简介**：本讲：实验方法——对照实验、只改一个变量、重复与方差、统一计价。服务作业 A3/期末项目。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l20/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、智能体、SWE-bench、第20讲
- **服务作业**：A3/期末项目
- **封面文字**：第20讲 / 实验方法
- **视频文件**：`videos/out/l20.mp4`（制作后）

### 第 21 讲（l21）

- **标题**：【AgentHarness 第21讲】课程团队方案复盘
- **简介**：本讲：课程团队方案复盘——一个在小实验里有效、在真实任务上无效的插件。服务作业 A3/期末项目。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l21/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、智能体、SWE-bench、第21讲
- **服务作业**：A3/期末项目
- **封面文字**：第21讲 / 课程团队方案复盘
- **视频文件**：`videos/out/l21.mp4`（制作后）

### 第 22 讲（l22）

- **标题**：【AgentHarness 第22讲】LLM 内部
- **简介**：本讲：LLM 内部——请求六阶段、Transformer 块、注意力与 FlashAttention、GQA/MLA。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l22/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、智能体、第22讲
- **服务作业**：待定
- **封面文字**：第22讲 / LLM 内部
- **视频文件**：`videos/out/l22.mp4`（制作后）
- **状态**：新增讲次，讲稿待写

### 第 23 讲（l23）

- **标题**：【AgentHarness 第23讲】推理基础：预填充与解码
- **简介**：本讲：推理基础：预填充与解码——KV cache、算力瓶颈与访存瓶颈。服务作业 A4。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l23/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、大模型推理、本地部署、第23讲
- **服务作业**：A4
- **封面文字**：第23讲 / 推理基础：预填充与解码
- **视频文件**：`videos/out/l23.mp4`（制作后）

### 第 24 讲（l24）

- **标题**：【AgentHarness 第24讲】本地推理入门：Ollama 与 llama.cpp
- **简介**：本讲：本地推理入门：Ollama 与 llama.cpp——GGUF 格式，以及静默失败的排查方法。服务作业 A4。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l24/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、大模型推理、本地部署、第24讲
- **服务作业**：A4
- **封面文字**：第24讲 / 本地推理入门：Ollama 与 llama.cpp
- **视频文件**：`videos/out/l24.mp4`（制作后）

### 第 25 讲（l25）

- **标题**：【AgentHarness 第25讲】批处理与调度
- **简介**：本讲：批处理与调度——静态批、连续批与 -np 并发槽位。服务作业 A4。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l25/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、大模型推理、本地部署、第25讲
- **服务作业**：A4
- **封面文字**：第25讲 / 批处理与调度
- **视频文件**：`videos/out/l25.mp4`（制作后）

### 第 26 讲（l26）

- **标题**：【AgentHarness 第26讲】前缀复用
- **简介**：本讲：前缀复用——cache_prompt、RadixAttention，以及 agent 与推理服务的协同设计。服务作业 A4。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l26/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、大模型推理、本地部署、第26讲
- **服务作业**：A4
- **封面文字**：第26讲 / 前缀复用
- **视频文件**：`videos/out/l26.mp4`（制作后）

### 第 27 讲（l27）

- **标题**：【AgentHarness 第27讲】显存与内存管理
- **简介**：本讲：显存与内存管理——PagedAttention 与 KV 量化。服务作业 A4。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l27/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、大模型推理、本地部署、第27讲
- **服务作业**：A4
- **封面文字**：第27讲 / 显存与内存管理
- **视频文件**：`videos/out/l27.mp4`（制作后）

### 第 28 讲（l28）

- **标题**：【AgentHarness 第28讲】推测解码
- **简介**：本讲：推测解码——草稿模型、接受率与加速比，草稿长度怎么选。服务作业 A4。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l28/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、大模型推理、本地部署、第28讲
- **服务作业**：A4
- **封面文字**：第28讲 / 推测解码
- **视频文件**：`videos/out/l28.mp4`（制作后）

### 第 29 讲（l29）

- **标题**：【AgentHarness 第29讲】量化
- **简介**：本讲：量化——权重量化档位，以及量化对速度和质量的影响。服务作业 A4。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l29/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、大模型推理、本地部署、第29讲
- **服务作业**：A4
- **封面文字**：第29讲 / 量化
- **视频文件**：`videos/out/l29.mp4`（制作后）

### 第 30 讲（l30）

- **标题**：【AgentHarness 第30讲】MoE：混合专家模型
- **简介**：本讲：MoE：混合专家模型——激活参数和总参数，为什么 30B-A3B 生成快但占内存大。服务作业 A4。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l30/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、大模型推理、本地部署、第30讲
- **服务作业**：A4
- **封面文字**：第30讲 / MoE：混合专家模型
- **视频文件**：`videos/out/l30.mp4`（制作后）

### 第 31 讲（l31）

- **标题**：【AgentHarness 第31讲】分布式推理
- **简介**：本讲：分布式推理——DP/TP/PP/EP、通信、预填充/解码分离。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l31/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、智能体、第31讲
- **服务作业**：待定
- **封面文字**：第31讲 / 分布式推理
- **视频文件**：`videos/out/l31.mp4`（制作后）
- **状态**：新增讲次，讲稿待写

### 第 32 讲（l32）

- **标题**：【AgentHarness 第32讲】全栈：多模型路由
- **简介**：本讲：全栈：多模型路由——主 agent 用云端模型，子 agent 用本地模型。服务作业 A5/期末项目。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l32/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、智能体、模型路由、第32讲
- **服务作业**：A5/期末项目
- **封面文字**：第32讲 / 全栈：多模型路由
- **视频文件**：`videos/out/l32.mp4`（制作后）

### 第 33 讲（l33）

- **标题**：【AgentHarness 第33讲】全栈：系统级优化
- **简介**：本讲：全栈：系统级优化——解决率、成本、耗时三者的取舍；排行榜方法论。服务作业 A5/期末项目。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l33/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、智能体、模型路由、第33讲
- **服务作业**：A5/期末项目
- **封面文字**：第33讲 / 全栈：系统级优化
- **视频文件**：`videos/out/l33.mp4`（制作后）

### 第 34 讲（l34）

- **标题**：【AgentHarness 第34讲】agent 安全：提示注入与防护
- **简介**：本讲：agent 安全：提示注入与防护——间接注入、越界动作、pre-execute 防护插件的效果与误拦。服务作业 A3 选做 L5/期末项目。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l34/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、智能体、智能体安全、提示注入、第34讲
- **服务作业**：A3 选做 L5/期末项目
- **封面文字**：第34讲 / agent 安全：提示注入与防护
- **视频文件**：`videos/out/l34.mp4`（制作后）

### 第 35 讲（l35）

- **标题**：【AgentHarness 第35讲】自我进化 harness
- **简介**：本讲：自我进化 harness——Reflexion、ADAS、ACE，以及 ACE 在 DeepSeek 上的复现。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l35/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、智能体、第35讲
- **服务作业**：待定
- **封面文字**：第35讲 / 自我进化 harness
- **视频文件**：`videos/out/l35.mp4`（制作后）
- **状态**：新增讲次，讲稿待写

### 第 36 讲（l36）

- **标题**：【AgentHarness 第36讲】前沿问题与课程回顾
- **简介**：本讲：前沿问题与课程回顾——长任务、多 agent、评测污染；学员使用日志复盘。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l36/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、智能体、第36讲
- **服务作业**：待定
- **封面文字**：第36讲 / 前沿问题与课程回顾
- **视频文件**：`videos/out/l36.mp4`（制作后）
- **状态**：新增讲次，讲稿待写

### 第 37 讲（l37）

- **标题**：【AgentHarness 第37讲】期末项目答疑与展示安排
- **简介**：本讲：期末项目答疑与展示安排——复现要求、报告与展示形式。服务作业 A5/期末项目。讲稿：https://odearevanhansen.github.io/agentharness/lectures/l37/ 仓库：https://github.com/ODearEvanHansen/agentharness 画面由程序生成，配音由 DeepSeek TTS 合成（AI合成）。与哈佛大学及 CS2680 无关联。许可 CC BY-SA 4.0
- **标签**：AI Agent、DeepSeek、大模型、公开课、编程、人工智能、智能体、模型路由、第37讲
- **服务作业**：A5/期末项目
- **封面文字**：第37讲 / 期末项目答疑与展示安排
- **视频文件**：`videos/out/l37.mp4`（制作后）

## 上传方式

### 方式一：网页手动上传（推荐，官方渠道）

1. 登录 B 站 → 创作中心（https://member.bilibili.com/platform/upload/video/frame）→ 投稿 → 上传视频；
2. 上传 `videos/out/lXX.mp4`，从 `meta.json` 复制标题、简介、标签；类型选“自制”，分区按上面的建议选；
3. 上传封面；在“更多设置/创作声明”中勾选“含 AI 生成内容”（作者声明：使用 AI 生成）；
4. 提交审核；通过后在创作中心 → 合集管理 中新建/选择合集“AgentHarness 公开课”，按讲次加入；
5. 记录 BV 号（稿件管理页或视频网址 `https://www.bilibili.com/video/BVxxxx`）。

### 方式二（已采用并验证）：服务器上的 social-auto-upload

课程维护者在服务器上用 [social-auto-upload](https://github.com/dreammis/social-auto-upload)（底层 biliup）自动投稿，账号已扫码登录（凭据只存在服务器本地，权限 600）。2026-11-22 用 8 秒测试视频验证：上传成功、进入审核、稿件列表可查到 BV 号。实测限制：
- 只能定时发布，不能设"仅自己可见"；
- 删除稿件需要人工过验证码（接口返回 340022），要在创作中心手动删；
- 没有"含 AI 生成内容"声明参数：发布后由账号所有者在创作中心逐个勾选（或手动投稿时勾选）。

发布流程：渲染 → `meta.json` 取标题/简介/标签 → `sau bilibili upload-video --tid 208 --schedule ...` → 查稿件列表拿 BV 号写入 `videos/bilibili.json` → 重建网站。

### 方式三：biliup 原生命令行（备选，有风险）

- **项目现状**：原独立 CLI 仓库 `biliup/biliup-rs` 已归档，README 提示后续开发迁至 `biliup/biliup`（MIT）。来源：https://github.com/biliup/biliup-rs ，https://github.com/biliup/biliup
- **安装**：从 biliup/biliup 的 Releases 下载对应平台 `biliupR-*` 二进制并放进 PATH，或 `npm i -g @biliup/cli`（见 biliup/biliup README）。
- **登录（使用你自己的账号，生成 cookie 文件）**：`biliup login`（支持扫码、短信、浏览器、网页 Cookie 等方式），登录信息保存到 cookie 文件；可用 `biliup -u cookies.json login` 指定路径，`biliup renew` 刷新。**cookie 等同账号凭证，切勿提交到仓库**（建议加入 `.gitignore`）。
- **上传示例**（参数取自 biliup-rs 归档 README 的 `biliup help upload`；新版可能有变化，使用前先运行 `biliup upload --help` 核对）：

```bash
biliup -u cookies.json upload videos/out/l01.mp4 \
  --copyright 1 --tid <分区ID> --cover cover/l01.jpg \
  --title "【AgentHarness 第1讲】课程导论：agent 系统是什么" \
  --desc "$(jq -r '.lectures[0].desc' videos/bilibili/meta.json)" \
  --tag "$(jq -r '.lectures[0].tags|join(",")' videos/bilibili/meta.json)"
```

  其他可用参数：`--dtime`（定时发布，10 位时间戳，需距提交 >4 小时）、`--line`（上传线路）、`-c config.yaml`（配置文件批量投稿）、`append`（向已有稿件追加分 P）、`list`/`show`（查看稿件）。`--tid` 默认 171，**必须改成 208（知识 > 校园学习）**。
- **AI 声明**：CLI 的参数列表中没有明确的“AI 生成内容”声明开关（可能需 `--extra-fields`，未核实）。用 CLI 上传后，**务必到创作中心编辑稿件补勾“含 AI 生成内容”**，合集也需在网页端添加。
- **风险**：非官方工具，调用的是未公开接口，可能随时失效；自动化投稿可能触发风控，存在违反 B 站用户协议、导致限流或封号的风险；项目自身声明“仅供个人学习研究、后果自负”。课程官方账号建议优先用网页手动上传。

## 上传后：把 BV 号写回网站

`scripts/build_site.py` 读取 `videos/bilibili.json`，格式是**讲次 id → BV 号**的扁平对象（键必须是 `l01`…`l29`，与讲稿文件名一致）：

```json
{
  "l01": "BV1xxxxxxxxx",
  "l02": "BV1yyyyyyyyy"
}
```

- 有 BV 号的讲：讲座页嵌入 `https://player.bilibili.com/player.html?bvid=<BV>` 播放器并附“在 B 站观看”链接，讲座索引显示 ▶️；没有的显示“制作中”。可以逐讲增量添加。
- 只填 BV 号字符串（不要填完整 URL 或 av 号）；然后运行 `python scripts/build_site.py` 重建站点并检查对应讲座页。
