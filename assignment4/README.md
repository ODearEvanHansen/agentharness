# 作业 4：DSH-Serve —— 在自己的机器上跑模型

> 预计 16–22 小时（其中 L4 手写迷你推理引擎约 6–8 小时），第 9 周发布、第 12 周截止，对应第 17–24 讲。每个实验都注明了**学完哪一讲再做**，可以边学边做。
> 实验脚本 `engine/bench.py`（E1–E5）和自动检查 `check.py`，课程团队都已实际跑通，E1–E5 数据检查 5/5 通过（报告项需要你自己写）。参考结果放在 `assignment4/reference/E*.json`。

前三个作业里，模型对你来说是一个黑盒 API。这个作业要你在自己的机器上把模型跑起来，亲手调推理服务的参数，用数据解释每个参数为什么有效（或者为什么无效），最后把本地模型接回你的 agent。

> 模型下载与校验、Ollama / llama-server 容器、`/health` 就绪检查和本地 provider 配置的分步说明，见[本地模型与进阶工具](https://odearevanhansen.github.io/agentharness/setup-local/#一本地模型服务)（仓库内 [docs/setup-local.md](../docs/setup-local.md)）。

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

### L4 手写迷你推理引擎（numpy + Qwen3-0.6B；学完第 19、21 讲再做；约 6–8 小时）
L2 里你调的是别人写好的推理服务。这一关自己写一个：用 numpy 在 CPU 上跑 Qwen3-0.6B，再在上面加批处理调度和分页 KV 缓存。代码量不大（骨架连检查脚本不到 600 行，你要补的大约 120 行），目的是把第 17–21 讲的概念变成能跑、能测的东西。

**准备**（只需要 16GB 内存；权重转成 fp32 后常驻约 3.5GB）：
```bash
python3 -m venv .mini-venv && . .mini-venv/bin/activate
pip install numpy safetensors tokenizers          # 不需要 torch / transformers
python assignment4/miniengine/download.py          # 约 1.5GB，到 models/Qwen3-0.6B/；国内先 export HF_ENDPOINT=https://hf-mirror.com
```
模型结构从 `models/Qwen3-0.6B/config.json` 读：28 层，hidden 1024，16 个查询头、8 个 KV 头（GQA），head_dim 128，每个头的 q/k 先做 RMSNorm（`q_norm`/`k_norm`）再做 RoPE（`rope_theta` = 1e6），词嵌入和输出层共享（`tie_word_embeddings`）。

**步骤**（文件都在 `assignment4/miniengine/`，搜索 `TODO(L4-` 就能找到要补的地方）：
1. `model.py`（第 17、18 讲）：权重加载已经写好（直接解析 safetensors，bf16 转 fp32）。你补 `rmsnorm`、`rope`、带 GQA 和因果掩码的 `attention`，`mlp`（SwiGLU），以及 `forward` 里"把新 token 的 K/V 追加进缓存、再读出全部历史做注意力"这一段。`forward` 一次处理一批序列：所有序列的新 token 拼成一个矩阵做矩阵乘，注意力按序列分别算。预填充和解码用的是同一个函数，区别只是每条序列本步的 token 数不同。
2. `engine.py` 的 KV 部分（第 21 讲）：`ContiguousKV` 是对照组，每条序列一上来就按 `max_len` 预留连续内存。你补 `BlockAllocator`（固定大小的物理块池加空闲链表）和 `PagedKV`（块表，按需要块，序列结束时归还）。
3. `engine.py` 的调度部分（第 19 讲）：补 `Engine.admit`。静态批处理要等一批请求全部结束才接下一批；连续批处理每一步都把空出来的槽位补上（每步准入）。`step()` 已经写好：新请求本步做预填充，老请求本步解码 1 个 token，两者放在同一次 `forward` 里。准入时按"提示长度 + max_new_tokens"预先承诺块数，这样跑到一半不会缺块。vLLM 的做法不一样，它超额准入，块不够时抢占。
4. 测量：`python assignment4/miniengine/bench.py --threads 8`，生成 `results/M1.json`（单请求解码速度）、`M2.json`（8 个长短交替的请求，`max_batch=4`，静态批处理对比连续批处理）、`M3.json`（同一负载下连续预留和分页 KV 的峰值内存）。
5. 对照：用 L2 的 `llama-server`（Qwen3-0.6B Q8_0，`-t 8`，M2 再加 `-np 4`）跑同样的提示，记下速度。

**检查**：
```bash
python assignment4/miniengine/check.py
```
一共 10 项，逐项打印 ✅/❌ 和原因：四个基本块和朴素实现对比（不需要权重）；3 个提示各贪心生成 32 个 token，和课程团队参考实现提交的 `expected/greedy.json` 比较，一致的前缀要 ≥ 16；用假模型测调度器：连续批处理的平均完成步数必须比静态少，静态批处理的第二批不能提前开始；分页 KV 每一步占用的块不能超过"各序列实际长度按块取整 + 每条序列 1 块"，块表之间不能共用物理块，结束后块要全部归还，块池很小时请求要排队而不是报错；最后检查 `results/M1–M3.json` 是否齐全。

> ⚠️ 第一个坑：`x / np.sqrt(128)` 里的 `np.sqrt(128)` 是 `np.float64` 标量。按 numpy 2 的类型提升规则（NEP 50），float32 数组和它运算的结果会变成 float64，之后每次矩阵乘都要把权重临时转成 float64。课程团队试做时就踩了这个坑：解码从 24 tok/s 掉到 0.6 tok/s，单看输出完全正确。用 Python 的 float（`hd ** -0.5`）就没有这个问题。`check.py` 会检查 dtype。

**课程团队参考实现实测**（Xeon Gold 6354，`OPENBLAS_NUM_THREADS=8`，numpy 2 + OpenBLAS，fp32；llama.cpp 用同一台机器、`-t 8`、Qwen3-0.6B Q8_0）：

| 项目 | numpy 参考实现 | llama-server（Q8_0） |
|---|---|---|
| M1 单请求解码（提示 5 token，生成 64） | 24.3 tok/s，TTFT 0.12 s | 73.5 tok/s，预填充 30 ms |
| M2 静态批处理（8 个请求，长短交替生成 8/64 token，batch 4） | 25.1 tok/s，平均延迟 6.16 s，平均 TTFT 3.07 s，128 步 | — |
| M2 连续批处理（同上） | 37.3 tok/s，平均延迟 4.12 s，平均 TTFT 0.86 s，88 步 | `-np 4`：158.5 tok/s，平均延迟 1.17 s |
| M3 KV 峰值预留（连续批处理，同一负载；每 token 224 KB） | 连续预留（max_len 1024）：896 MB，实际只用 57 MB，利用率 6.4% | 分页（块 16）：63 MB，利用率 90.6% |

和 llama.cpp 的正确性对比（5 个提示各 64 token，贪心）：按 llama 生成的序列逐步喂给参考实现（teacher forcing），每一步 top-1 一致的比例是 **98.1%**（314/320）。如果两边各自自由生成，按位置逐个比较只有 61% 一致：其中 2 个提示完全相同，另外 2 个分别在第 3、5 个 token 处分叉，分叉之后两条续写就不再可比。原因是 Q8_0 把权重量化到 8 位，参考实现用的是 bf16 原始权重转 fp32。遇到两个候选 token 概率几乎相同的位置，量化误差就足以让两边选不同的 token。所以我们用 teacher forcing 的一致率（要求 ≥ 90%）做正确性证据，不要求逐 token 完全相同。`check.py` 对比的是同为 fp32 的参考实现，所以要求严格得多。

**报告必答**（写进 `WRITEUP.md`）：
- 同一台机器上，你的 numpy 实现比 llama.cpp 慢几倍？从三方面解释：**量化内核**（Q8_0 每个权重读 1 字节左右，fp32 要读 4 字节，而解码受内存带宽限制）、**线程与 SIMD**（OpenBLAS 只并行矩阵乘本身，RoPE、softmax、逐层的 Python 循环都是单线程）、**算子融合**（numpy 每个算子都要把中间结果写回内存，llama.cpp 把多个算子融合在一起）。用"每 token 读取的字节数 ÷ 解码耗时"估算两边的有效带宽。
- M2 里连续批处理的收益从哪里来？分别解释吞吐、平均延迟和平均 TTFT 的变化。负载换成所有请求一样长时，连续批处理还有优势吗？在单请求的 M1 里呢？
- 静态批处理里，已经结束的请求还占着槽位和 KV 内存，这部分浪费怎么从 M2/M3 的数据里看出来？
- 分页 KV：用 M3 的数据算内部碎片（每条序列最后一个块没用完的部分）和连续预留造成的浪费。块大小从 16 改成 1 或 256，会有什么取舍（块表长度、gather 开销、碎片）？为什么 `read` 每步把块拼回连续数组在 GPU 上不能接受？PagedAttention 是怎么避免的（第 21 讲）？

## 提交物
- `assignment4/engine/`：所有启动脚本和参数；
- `assignment4/results/`：你自己跑出的 E1–E5 的 JSON 以及 L3 的原始数据（不要提交 `reference/` 的副本）；
- `assignment4/miniengine/`：补完的 `model.py`、`engine.py`（L4），以及 `results/M1–M3.json`；
- `assignment4/WRITEUP.md`：L1 的原因分析、L2 的表格和必答题、L3 的对比结果和协同设计的证据、L4 的必答题。

## 讲座会讲、但本作业不做的内容
RadixAttention、抢占与换出、GPU 上的 PagedAttention 内核、生产级推理服务（SGLang/vLLM）。这些会结合论文和源码讲解；课程默认学员没有 GPU，所以不安排实验。连续批处理和分页 KV 的 CPU 简化版在 L4 里做。
