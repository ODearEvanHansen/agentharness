# 作业 4：DSH-Serve —— 在自己的机器上跑模型

> 预计 10–14 小时，第 9 周发布、第 12 周截止，对应第 17–24 讲。每个实验都注明了**学完哪一讲再做**，可以边学边做。
> 实验脚本 `engine/bench.py`（E1–E5）和自动检查 `check.py`，课程团队都已实际跑通，E1–E5 数据检查 5/5 通过（报告项需要你自己写）。参考结果放在 `assignment4/reference/E*.json`。

前三个作业里，模型对你来说是一个黑盒 API。这个作业要你在自己的机器上把模型跑起来，亲手调推理服务的参数，用数据解释每个参数为什么有效（或者为什么无效），最后把本地模型接回你的 agent。

## 准备

### 硬件与模型
| 内存 | 模型 | 能做的 |
|---|---|---|
| 16GB | Qwen3-8B（Q4_K_M 5.0GB、Q8_0 8.7GB）+ Qwen3-0.6B Q8_0（草稿模型，0.6GB） | L1（换成 8B 模型）和 L2 的全部实验 |
| ≥ 32GB | 再加上 **Qwen3-Coder-30B-A3B-Instruct Q4_K_M**（18.6GB，运行时常驻内存约 28GB） | L3：把本地模型接回 agent；E5 的 MoE 对比 |

为什么不用 DeepSeek 自家的蒸馏模型？试做阶段实测，DeepSeek-R1-Distill-Qwen-7B 在 30 次请求里**一次工具调用都没有发出**，没法当 agent 用。这本身就值得想一想："会推理"和"会用工具"是两回事。

**下载**：模型都放在仓库根目录的 `models/` 下（已被 `.gitignore` 忽略）。先装下载工具，二选一：`pip install -U "huggingface_hub[cli]"`（命令是 `hf`；旧版本叫 `huggingface-cli`，参数相同），或 `pip install modelscope`。

Hugging Face（国内可先 `export HF_ENDPOINT=https://hf-mirror.com`）：
```bash
hf download Qwen/Qwen3-8B-GGUF Qwen3-8B-Q4_K_M.gguf --local-dir models
hf download Qwen/Qwen3-8B-GGUF Qwen3-8B-Q8_0.gguf --local-dir models
hf download Qwen/Qwen3-0.6B-GGUF Qwen3-0.6B-Q8_0.gguf --local-dir models
hf download unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF Qwen3-Coder-30B-A3B-Instruct-Q4_K_M.gguf --local-dir models   # 32GB 才需要
```
或者 ModelScope（同名仓库）：
```bash
modelscope download --model Qwen/Qwen3-8B-GGUF Qwen3-8B-Q4_K_M.gguf --local_dir models
modelscope download --model Qwen/Qwen3-8B-GGUF Qwen3-8B-Q8_0.gguf --local_dir models
modelscope download --model Qwen/Qwen3-0.6B-GGUF Qwen3-0.6B-Q8_0.gguf --local_dir models
modelscope download --model unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF Qwen3-Coder-30B-A3B-Instruct-Q4_K_M.gguf --local_dir models
```
下载后核对 sha256（下面是课程团队所用文件的值，没下载的文件会报找不到，忽略即可）。用别的文件也能做实验，只是数据不能和参考结果直接比较：
```bash
cd models && sha256sum -c --ignore-missing <<'EOF'
731ece8d06dc7eda6f6572997feb9ee1258db0784827e642909d9b565641937b  DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf
9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031  Qwen3-0.6B-Q8_0.gguf
d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785  Qwen3-8B-Q4_K_M.gguf
408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6  Qwen3-8B-Q8_0.gguf
fadc3e5f8d42bf7e894a785b05082e47daee4df26680389817e2093056f088ad  Qwen3-Coder-30B-A3B-Instruct-Q4_K_M.gguf
EOF
cd ..
```
DeepSeek-R1-Distill-Qwen-7B 只用于复现上面"一次工具调用都没有"的观察，可以不下载。

许可：Qwen3 系列为 Apache-2.0。30B 的 GGUF 不是 Qwen 官方发布的，是第三方 unsloth 对 Apache-2.0 的 Qwen3-Coder-30B-A3B-Instruct 重新量化的版本（[unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF](https://huggingface.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF)）。

### 构建 llama.cpp（锁定版本）
llama.cpp 的参数名会变，比如 `--draft-max` 已经改名为 `--spec-draft-n-max`，所以课程锁定一个 commit：
```bash
git clone https://github.com/ggml-org/llama.cpp && cd llama.cpp
git checkout 4783b1145c7073bb809f4c282ff4853cbfe42954
cmake -B build -DGGML_NATIVE=ON -DLLAMA_CURL=OFF
cmake --build build -j --target llama-server llama-bench
cd ..
```
需要 cmake 和 C++ 编译器（`sudo apt install build-essential cmake`）。整个作业只用 CPU。

> **安全**：llama-server 只是推理服务，不会执行命令，可以直接在宿主机上运行。但 L3 里接回的 agent **必须**在容器里跑，原因同作业 2。

## 怎么跑
```bash
S=llama.cpp/build/bin/llama-server
python assignment4/engine/bench.py --exp E1 --model models/Qwen3-8B-Q4_K_M.gguf --server $S
python assignment4/engine/bench.py --exp E3 --model models/Qwen3-8B-Q4_K_M.gguf --draft models/Qwen3-0.6B-Q8_0.gguf --server $S
python assignment4/engine/bench.py --exp E5 --model models/Qwen3-8B-Q4_K_M.gguf --model models/Qwen3-8B-Q8_0.gguf \
       [--model models/Qwen3-Coder-30B-A3B-Instruct-Q4_K_M.gguf] --server $S
python assignment4/check.py
```
线程数默认取 CPU 核数的一半（`--threads` 可改）。结果写入 `assignment4/results/E*.json`，提交时一并提交。课程团队的参考结果在 `assignment4/reference/E*.json`；`check.py` 只读 `results/`，如果某个结果文件和参考文件一模一样（CPU 和耗时都相同），会判为不通过。

## 关卡

### L1 入门：用 Ollama 接入 DSH（学完第 18 讲再做；1–2 小时）
1. 用容器运行 Ollama（锁定版本标签 `ollama/ollama:0.12.6`），名字 `agentharness-ollama`，接入 `agentharness-net`，模型放在挂载卷里。先拉好 `qwen3-coder:30b`（16GB 内存改用 `qwen3:8b`）。完整命令见 [infra/README.md 的"本地模型服务"一节](../infra/README.md#本地模型服务接入隔离网络)。
2. 在 DSH 的 `llm-pi-ai` 里加一个 `openai-completions` 类型的 provider，地址 `http://agentharness-ollama:11434/v1`，用完整 profile 让 agent 写一个脚本并运行它。agent 在运行器容器里跑，启动时加 `-e NO_PROXY=agentharness-ollama`。
3. **你会发现 agent 只回了一句 "Hello! How can I assist you today?"**。用第 18 讲介绍的排查方法找出原因并修好。报告里要回答：是什么机制导致的？为什么它"静默"发生、没有任何报错？

### L2 推理服务实验（`llama-server`）
每个实验都要给出**可复现的命令**、**原始数据**和**一段解释**。参考结果来自课程团队的机器（Xeon Gold 6354，32 核，`-t 16`，Qwen3-8B Q4_K_M）。你的数字会不一样，但应该能看到同样的趋势，或者能解释为什么不一样。

| 实验 | 学完哪讲 | 变量 | 参考结果 |
|---|---|---|---|
| E1 批处理 | 第 19 讲 | `-np 1` 对比 `-np 4`，同时发 4 个请求 | 总吞吐 16.6 → 41.1 tok/s（约 2.5 倍，远不到 4 倍）；平均延迟 19.3 → 12.4 s |
| E2 前缀复用 | 第 20 讲 | `cache_prompt` 关 / 开（各自冷启动），共享约 4.6k token 的前缀 | 两次请求共享 4632 token 前缀：关闭时第二次预填充仍要 40.6 s；开启后 0.49 s（复用 4617 token） |
| E3 推测解码 | 第 22 讲 | 0.6B 草稿模型，草稿长度 3 对比 16 | 基线 17.9 tok/s；长度 3：接受率 54%，提升到 20.8；长度 16：接受率 21%，**降到** 11.6 |
| E4 KV 量化 | 第 21 讲 | f16 对比 q8_0（`-fa on`，32k 上下文） | 常驻内存 12.8 → 10.6 GB（KV 量化后约省一半）；预填充 89 → 36 tok/s，生成 10.2 → 9.2 tok/s，在 CPU 上**都变慢了** |
| E5 权重量化与架构 | 第 23、24 讲 | Q4 对比 Q8；稠密 8B 对比 MoE 30B-A3B | Q8 的生成速度比 Q4 慢约 38%（17.3 → 10.7 tok/s）；试做阶段测得 30B-A3B 的生成速度约为 8B 的 2 倍 |

> ⚠️ 推测解码只给 `-md` 不会生效，必须同时设置 `--spec-type draft-simple`。脚本已经替你加好了，但报告里要说明你怎么确认草稿确实在工作。

必答问题：
- E1：为什么 4 个槽位换不来 4 倍的吞吐？
- E3：接受率和草稿长度是什么关系？推一个估算加速比的公式，并用你的数据验证。
- E4：算一算 8B 模型在 32k 上下文下 f16 KV cache 的大小，和你测到的内存差值对得上吗？为什么在 CPU 上反而变慢？换成 GPU、更长的上下文或更高的并发，结论会不会反过来？
- E5：MoE 每生成一个 token 只激活约 3B 参数，为什么内存却要按 30B 来算？用"生成速度 × 每 token 读取的字节数"估算一下你机器的有效内存带宽。

### L3 接回 agent（需要 32GB；学完第 20 讲再做）
1. 用 `llama-server --jinja` 托管 30B-A3B 模型（容器写法见 [infra/README.md 的"本地模型服务"一节](../infra/README.md#本地模型服务接入隔离网络)，带 `--api-key`），让你的 madsLoop（作业 2）和 DSH 分别接上它，跑课程小题。madsLoop 通过环境变量 `MADS_API=http://agentharness-llm:8091/v1/chat/completions` 指向本地服务，`DEEPSEEK_API_KEY` 填 `$LOCAL_LLM_KEY` 的值，并设置 `NO_PROXY=agentharness-llm`。注意：llama.cpp 返回的用量字段和 DeepSeek 不同，用量统计需要你自己适配。
2. 测量解决率、单题耗时和每题 token 数，和 `deepseek-flash` 做对比。
3. **agent 与推理服务协同设计**：利用 E2 的结论修改你的 agent，让前缀复用的效果最大化，例如保持系统提示和工具定义不变、不改写历史消息。证明修改后预填充时间下降了，并且解决率没有变差。

## 提交物
- `assignment4/engine/`：所有启动脚本和参数；
- `assignment4/results/`：你自己跑出的 E1–E5 的 JSON 以及 L3 的原始数据（不要提交 `reference/` 的副本）；
- `assignment4/WRITEUP.md`：L1 的原因分析、L2 的表格和必答题、L3 的对比结果和协同设计的证据。

## 讲座会讲、但本作业不做的内容
PagedAttention、RadixAttention、连续批处理调度、生产级推理服务（SGLang/vLLM）。这些会结合论文和源码讲解；课程默认学员没有 GPU，所以不安排实验。
