# 作业 5：DSH-Stack —— 云端模型和本地模型混合使用

> 预计 12–18 小时。第 13 周发布，**第 16 周末**截止，对应第 32、33 讲。
> 课程团队已经完整跑通了路由机制、运行器和自动检查，数据见下文。

作业 3 优化的是 harness，作业 4 优化的是推理服务。这个作业把两者合起来：**主 agent 用 DeepSeek API，一部分子任务交给你在本机托管的模型**，在解决率、成本和耗时三个指标上一起优化。

> 本地模型服务、`/health` 就绪检查、provider 配置和 `usage_cost.py` 的分步说明，见[本地模型与进阶工具](https://odearevanhansen.github.io/agentharness/setup-local/#一本地模型服务)（仓库内 [docs/setup-local.md](../docs/setup-local.md)）。

## 先看课程团队的实测结果：路由不一定省钱

实验在 8 道课程小题上进行。主 agent 用 `deepseek-flash`，子 agent 用 CPU 上的 Qwen3-Coder-30B-A3B（Xeon Gold 6354，`-t 16`）。两组都用 `sdk` 完整 profile，唯一的区别是路由组多了 `local_worker` 工具和一段路由提示：

| 配置 | 解决 | 云端请求 | 本地请求 | 云端成本 | 中位耗时 |
|---|---|---|---|---|---|
| 不路由（对照） | 8/8 | — | 0 | 0.111 元 | 11.9 s |
| 路由（模板 + 示例提示） | 8/8 | 58 | 34 | **0.154 元** | **168 s** |

按模板路由后，云端成本**反而高了约 38%**，耗时则变成原来的十几倍。原因有三点：
- 每委派一次，主 agent 都要多发几次请求：写任务说明、等结果、读结果。
- 小题本身只要五六步就能做完，委派省下的工作量抵不过这些额外开销。
- 本地 30B 模型在 CPU 上预填充约 1 万 token 的系统提示，要一分多钟。

除此之外还有一个隐性成本。第 32 讲的例子里，主 agent 拿到子 agent 的结果后又自己算了一遍来复核：主 agent 不信任本地模型，就会重复劳动。

**你的任务是找出路由真正划算的条件，或者证明在什么条件下它不划算。**

## 准备
- 完成作业 0–4。默认路线（Qwen3-Coder-30B-A3B）需要 32GB 内存；16GB 的学员走下文的"小内存路线"（Qwen3-4B），同样亲手完成 L1–L4。课程团队两条路线的原始记录都在 [`baseline/`](baseline/)。
- 本地模型以容器形式跑在课程的隔离网络里，agent 容器通过容器名 `agentharness-llm` 访问它。**不要**把 agent 容器接到宿主机网络上。
```bash
export LOCAL_LLM_KEY=$(openssl rand -hex 16)     # 随机 key，同一网络里的其他容器拿不到就用不了
docker run -d --name agentharness-llm --cpus 16 --memory 30g --network agentharness-net \
  -e LOCAL_LLM_KEY -v "$PWD/models":/models:ro \
  ghcr.io/ggml-org/llama.cpp@sha256:ae28f5c2046de51dfd00c9116a36fe44b5e8703ef730d0aea69082781eecb1f7 \
  --model /models/Qwen3-Coder-30B-A3B-Instruct-Q4_K_M.gguf --jinja -c 65536 -np 2 -t 16 \
  --host 0.0.0.0 --port 8091 --api-key "$LOCAL_LLM_KEY"
```
  `--cpus 16` 和 `-t 16` 按 16 核写；本机核数更少时改成可用核数（例如 12 核用 `--cpus 12`、`-t 12`），否则 Docker 会拒绝启动。
  等模型加载完再继续：`docker logs -f agentharness-llm` 里出现 `listening on http://0.0.0.0:8091` 才算就绪。判断就绪要看健康检查或日志，**不要只看进程在不在**。课程团队就踩过这个坑：脚本用 `pgrep` 判断服务已经起来，结果匹配到的是脚本自己的命令行，本地服务其实没启动，6 道题全部退回到云端完成。
- 上面用的是 llama.cpp 官方镜像，锁定 digest（`server` 标签，构建版本 418fe97b），比作业 4 锁定编译的 commit `4783b1145c` 新，所以性能数字只在本作业内部互相比较。这个本地模型服务的通用写法见 [infra/README.md 的"本地模型服务"一节](../infra/README.md#本地模型服务接入隔离网络)。课程团队用这条链路（运行器容器 → 隔离网络 → 按容器名访问 llama.cpp 容器）和一个 8B 模型跑过 1 道小题：解出，共 4 次本地请求。

## 运行（所有命令都在仓库根目录执行）
```bash
# 把容器参数包成一个 shell 函数（每开一个新终端定义一次）
ahrun() {
  docker run --rm -it --cpus 4 --memory 8g --network agentharness-net \
    -e HTTPS_PROXY=http://agentharness-egress:8888 -e NO_PROXY=agentharness-llm \
    -e DEEPSEEK_API_KEY -e LOCAL_LLM_KEY -u "$(id -u):$(id -g)" -e HOME=/tmp \
    -v "$PWD":/work agentharness-runner:0.1 "$@"
}
# 对照组：完整 profile，不路由
ahrun python assignment2/run.py --agent dsh --suite mini --profile sdk --tag sdkfull --parallel 4
# 路由组：模板配置 + 路由提示（这两个文件就是你要改进的对象）
ahrun python assignment2/run.py --agent dsh --suite mini --profile sdk --tag a5 --parallel 2 --timeout 1800 \
  --patch /work/assignment5/templates/local-worker.patch.yml \
  --prompt-suffix-file assignment5/templates/routing-hint.txt
python assignment5/check.py assignment2/results/mini-dsh-a5.jsonl assignment2/results/mini-dsh-sdkfull.jsonl
```
改了路由配置后重跑，记得加 `--fresh` 或换 `--tag`，否则已有记录的题会被跳过（见作业 2「断点续跑」）。

`check.py` 在宿主机上运行（容器把仓库挂载成可写目录，agent 能改动仓库里的文件，所以检查以宿主机上的结果为准；key 不要放在仓库里，见作业 0）。

**耗时估算**：课程团队的机器上，路由组 8 题（`-np 2`）墙钟约 26 分钟，对照组约 1 分钟。跑 20 题的加做之前先估算：本地耗时 ≈ 本地请求步数 × 每步预填充 token 数 ÷ 预填充速度（tok/s，用作业 4 E5 的 pp512 或 llama-server 日志里的 prompt eval 速度），再加上生成时间；用小题的 `by_model` 和日志算出这几个数，按题数放大。

**日志证据**：`.gitignore` 虽然忽略 `*.log`，但 `assignment*/submission/` 下的 `.log` 例外，会被保留，不用改扩展名。例如 `docker logs agentharness-llm > assignment5/submission/<昵称>/llama-server.log 2>&1`。

`tools/usage_cost.py` 会按每次请求实际用到的模型分别计价，写在运行记录的 `by_model` 字段里，本地模型按 0 元计。

## 小内存路线：Qwen3-4B（16GB 电脑可以亲手跑）

内存不到 32GB 的学员把本地模型换成 `Qwen3-4B-Q4_K_M.gguf`（2.5GB，官方仓库 `Qwen/Qwen3-4B-GGUF`，sha256 `7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5`）。启动命令同上，只改三处：`--model /models/Qwen3-4B-Q4_K_M.gguf`、`-c 24576 -np 1`、加 `-fa on`，容器 `--memory 8g` 就够；`--cpus 16` 和 `-t 16` 改成本机可用核数（如 8 核机器用 `--cpus 8`、`-t 8`，否则 Docker 会拒绝启动）；patch 里的模型 id 改成 `qwen3-4b`（共两处：`models` 下的 `id` 与 `agentOptions.model`），运行器用 `--parallel 1`。

**先算 KV 占多少内存，再定上下文。** Qwen3-4B 的 f16 KV 约 144KB/token（36 层 × 8 个 KV 头 × 128 维 × K、V 两份 × 2 字节）。课程团队第一次用 `-c 65536 -np 2`，光 KV 就要约 9GB，容器在加载时被 OOM 杀掉。**DSH 没有报错，8 道题全部由云端悄悄解完**，`by_model` 里一次本地请求都没有。所以每次跑完都要看 `by_model`。

**课程团队实测**（8 核、8GB 容器、单槽位，机器上没有其他任务）：

| 配置 | 解决 | 云端请求 | 本地请求 | 云端成本 | 中位耗时 | 8 题合计 |
|---|---|---|---|---|---|---|
| 不路由（对照，同上表） | 8/8 | — | 0 | 0.111 元 | 11.9 s | 约 1 分钟 |
| 路由到 Qwen3-4B | 8/8 | 72 | 28 | 0.204 元 | 424 s | 约 63 分钟 |

原始记录在 [`baseline/mini-dsh-a5-qwen3-4b.jsonl`](baseline/mini-dsh-a5-qwen3-4b.jsonl)。

**另一台机器上的复测（同样 8 核、8GB、`-np 1`，一次学员试做）**：路由组 8/8（第一轮 7/8），云端 82 次、本地 24 次请求，云端成本 0.212 元；**单题中位 768 s（304–1492 s），8 题墙钟约 2.2 小时**，llama-server 日志里预填充中位只有 19.8 tok/s。所以 4B 路线请按 **1–2.5 小时**预留，并**先只跑 1 题**（`--only t01_sum_range`）估时。

**超时与断点续跑**：单题可能撞上 `--timeout 1800`（上面那次 t05 就是），这道题记为出错，`check.py` 会报「出错 [...]」。不用加 `--fresh`，原命令再跑一遍，运行器只重跑出错的题，补齐后 `check.py` 即可通过；慢机器也可以直接把 `--timeout` 调到 3600。超时的题**钱已经花了**：运行器会在超时时从该题的 DSH 会话日志统计已花费用并写进记录（行末会印「超时前已花费 … 元」）；但续跑成功后，同一题的记录会被新记录取代，汇总里只算最后一次。要核对总花费，以账户余额的前后差为准。

为什么 4B 也这么慢：子 agent 每次请求都带着约 1 万 token 的系统提示和工具定义。`llama-bench`（8 线程）实测，4B 在短上下文时生成 23 tok/s、预填充 142 tok/s；已有 1 万 token 上下文时，生成降到 6–8 tok/s，预填充降到 27–45 tok/s。**模型变小了，但上下文没变短，路由照样慢。** 这也是 L2 要回答的问题之一。

## 关卡
| 关卡 | 内容 | 检查 |
|---|---|---|
| L1 | 复现上面两组实验（约 30 分钟，见耗时估算），确认子 agent 的请求确实打到了本地模型（看 `by_model` 和 llama-server 日志） | `check.py`：解决 ≥ 6/8，且至少一半的题有本地请求 |
| L2 | 分析模板路由为什么更贵：把多出来的云端请求按用途分类（委派、等待、复核……），用作业 1 的离线载入（L6）打开运行器保存的 DSH home 找证据。**必答：推导划算条件**：写出一次委派的云端成本变化和耗时变化的公式（变量至少包括：委派引入的额外云端请求数与 token、子任务本来要花的云端 token、本地预填充速度、子 agent 上下文长度），代入你的实测值，算出"本地预填充速度至少多少 / 子 agent 上下文至多多长 / 子任务至少多大"路由才划算，并用 30B-A3B 和 4B 两组数据检验 | 报告 |
| L3 | 改进路由策略（改提示词、改工具描述或写插件），目标是解决率不下降、云端成本低于对照组。至少做两个版本，每个版本都要有对照 | `check.py` + 报告 |
| L4 | 协同优化：结合作业 4 的推理服务参数（`-np`、前缀复用、量化）缩短本地子 agent 的耗时，并说明它对云端成本有没有影响 | 报告 |
| 加做 | 在作业 3 的 20 题上做 L3 的实验。每题都要启动任务容器，所以 `agentharness-llm` 需要和任务容器在同一个网络里，并设置 `NO_PROXY`。CPU 推理可能要跑好几个小时，请先按上面的公式估算时间 | 报告 |

## 提交物
- `assignment5/submission/<昵称>/`：路由配置、提示词、插件；
- `assignment2/results/` 下对应的运行记录；llama-server 日志放在 `submission/<昵称>/`（`.log` 会被保留）；
- 博客形式的报告 `BLOG.md`。负面结果同样有价值，例如"在小题上路由永远不划算，原因是……"，前提是有数据支撑。
