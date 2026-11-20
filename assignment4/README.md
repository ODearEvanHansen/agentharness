# 作业 4：DSH-Serve —— 在自己的机器上跑模型（草稿）

> 实验脚本 `engine/bench.py`（E1–E5）和自动检查 `check.py` 已经可用：课程团队用 Qwen3-8B Q4 在 32 核 CPU 上跑过一遍，check 6/6 通过。
> E3 复现结果：草稿长度 3 时接受率 54%、17.9 → 20.8 tok/s；草稿长度 16 时接受率 21%、降到 11.6 tok/s。
> 预计 10–14 小时，对应第 9–12 周的课程（推理基础、批处理与调度、量化、推测解码、MoE）。

前三个作业里，模型对你来说是一个黑盒 API。这个作业你要在自己的机器上把模型跑起来，亲手调整推理服务的参数，用数据解释每个参数为什么有效（或者为什么无效），最后把本地模型接回你的 agent。

## 硬件与模型

| 内存 | 模型 | 能做的事 |
|---|---|---|
| ≥ 32GB | **Qwen3-Coder-30B-A3B-Instruct Q4_K_M**（18.6GB） | 全部实验，并接回 agent。M0 实测：课程小题 8/8，CPU 生成约 35 tok/s |
| 16GB | Qwen3-8B Q4_K_M（5GB） | 只做推理服务实验（L2）。拿它做 agent 不够用：小题只能解 4/8，而且很慢 |

> 为什么不用 DeepSeek 自家的蒸馏模型？M0 实测 DeepSeek-R1-Distill-Qwen-7B 在 30 次请求里**一次工具调用都没有发出**，没法当 agent 用。这本身就是一个值得思考的问题：模型"会推理"和"会用工具"是两回事。

软件：llama.cpp（课程锁定 commit `4783b11`，因为参数名会改，例如 `--draft-max` 已经改成 `--spec-draft-n-max`），Ollama ≥ 0.40。

## 怎么跑
```bash
python assignment4/engine/bench.py --exp E1 --model models/Qwen3-8B-Q4_K_M.gguf --server llama.cpp/build/bin/llama-server
# E3 需要 --draft；E5 需要传两个以上 --model
python assignment4/check.py
```
> ⚠️ 推测解码只给 `-md` 不会生效，必须同时设置 `--spec-type draft-simple`。脚本已经替你加好了，但报告里要说明你是怎么确认草稿确实在工作的。

## 关卡

### L1 入门：Ollama 接入 DSH（1–2 小时）
1. 安装 Ollama：Linux 安装包现在是 `ollama-linux-amd64.tar.zst`，解压到用户目录即可，不需要 root。然后运行 `ollama pull qwen3-coder:30b`。
2. 通过 DSH 的 `llm-pi-ai` 新增一个 `openai-completions` 类型的 provider，指向 `http://127.0.0.1:11434/v1`，用完整 profile 让 agent 写一个脚本并运行它。
3. **你会发现 agent 只会回一句 "Hello! How can I assist you today?"。** 找出原因，提示：看 Ollama 的日志。修好它，并在报告里说明：是什么机制导致了这个现象？为什么它是"静默"发生的，没有任何报错？

### L2 推理服务实验（`llama-server`）
每个实验都要给出**可复现的命令**、**原始数据**，以及**一段解释**。下表右列是 M0 在 32 核 Xeon CPU 上的结果，你的机器上数字会不同，但应该能看到同样的趋势，或者能解释为什么不一样。

| 实验 | 变量 | M0 参考结果 |
|---|---|---|
| E1 批处理 | `-np 1` 对比 `-np 4`，4 个并发请求 | 总吞吐 30 → 54 tok/s（×1.8），平均延迟 11.0 → 9.5 s |
| E2 前缀复用 | `cache_prompt` 关/开，约 2.2k token 的共享前缀 | 第二次请求的预填充时间 15.0 s → 0.24 s |
| E3 推测解码 | 8B 主模型 + 0.6B 草稿模型，`--spec-type draft-simple`，草稿长度 3 对比 16 | 长度 16：接受率约 20%，**变慢**（18.6 → 11 tok/s）；长度 3：接受率 55%，提速 +20% |
| E4 KV 量化 | f16 对比 q8_0（`-fa on`） | CPU 上**更慢**（生成 25 → 19 tok/s），常驻内存几乎不变 |
| E5 权重量化与架构 | Q4 对比 Q8；稠密 8B 对比 MoE 30B-A3B | Q8 比 Q4 慢约 40%；MoE 的生成速度约为 8B 的 2 倍 |

必答问题：
- E3：接受率和草稿长度之间是什么关系？给出一个估算加速比的公式，并用你的数据验证。
- E4：为什么 KV 量化在 CPU 上反而变慢、也不省内存？在 GPU、长上下文、高并发这几种场景下，结论会不会反过来？
- E5：MoE 每生成一个 token 只激活约 3B 参数，为什么占用的内存却要按 30B 来算？

### L3 接回 agent
1. 用 `llama-server --jinja` 托管 30B-A3B 模型，让你的 madsLoop（作业 2）和 DSH 各自接上这个本地模型，跑课程小题。
2. 测量解决率、单题耗时和每题 token 数，和 `deepseek-flash` 做对比。
3. **agent 和推理服务协同设计**：利用 E2 的结论，修改你的 agent，让前缀复用的效果最大化，比如保持系统提示和工具定义不变、避免修改历史消息。证明修改后预填充时间下降了，前提是解决率不能变差。

## 提交物
- `assignment4/engine/`：所有启动脚本和参数；
- `assignment4/results/`：原始数据（JSON 或 CSV）；
- `WRITEUP.md`：L1 的原因分析、L2 的表格和对必答问题的回答、L3 的对比结果和协同设计的证据。

## 讲座中会讲、但本作业不做的内容
PagedAttention、RadixAttention、连续批处理调度、生产级推理服务（SGLang/vLLM）。这些内容会结合论文和源码讲解，课程默认学员没有 GPU，所以不安排实验。
