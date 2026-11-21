# 作业 5：DSH-Stack —— 云端模型和本地模型混合使用

> 预计 12–18 小时。第 13 周发布，**第 16 周末**截止，对应第 25–26 讲。
> 课程团队已经完整跑通了路由机制、运行器和自动检查，数据见下文。

作业 3 优化的是 harness，作业 4 优化的是推理服务。这个作业把两者合起来：**主 agent 用 DeepSeek API，一部分子任务交给你在本机托管的模型**，在解决率、成本和耗时三个指标上一起优化。

## 先看课程团队的实测结果：路由不一定省钱

实验在 8 道课程小题上进行。主 agent 用 `deepseek-flash`，子 agent 用 CPU 上的 Qwen3-Coder-30B-A3B（Xeon Gold 6354，`-t 16`）。两组都用 `sdk` 完整 profile，唯一的区别是路由组多了 `local_worker` 工具和一段路由提示：

| 配置 | 解决 | 云端请求 | 本地请求 | 云端成本 | 中位耗时 |
|---|---|---|---|---|---|
| 不路由（对照） | 8/8 | — | 0 | $0.0167 | 12.8 s |
| 路由（模板 + 示例提示） | 8/8 | 58 | 34 | **$0.0231** | **204 s** |

按模板路由后，云端成本**反而高了约 38%**，耗时则变成原来的十几倍。原因有三点：
- 每委派一次，主 agent 都要多发几次请求：写任务说明、等结果、读结果。
- 小题本身只要五六步就能做完，委派省下的工作量抵不过这些额外开销。
- 本地 30B 模型在 CPU 上预填充约 1 万 token 的系统提示，要一分多钟。

除此之外还有一个隐性成本。第 25 讲的例子里，主 agent 拿到子 agent 的结果后又自己算了一遍来复核：主 agent 不信任本地模型，就会重复劳动。

**你的任务是找出路由真正划算的条件，或者证明在什么条件下它不划算。**

## 准备
- 完成作业 0–4，需要 32GB 内存。内存不足的学员可以跳过 L1 的本地运行，直接使用课程团队提供的本地基线（上表，原始记录在 [`baseline/`](baseline/)），完成 L2–L4 的设计和云端实验部分，评分只看这些部分。
- 本地模型以容器形式跑在课程的隔离网络里，agent 容器通过容器名 `agentharness-llm` 访问它。**不要**把 agent 容器接到宿主机网络上。
```bash
docker run -d --name agentharness-llm --cpus 16 --memory 30g --network agentharness-net \
  -v "$PWD/models":/models:ro ghcr.io/ggml-org/llama.cpp:server \
  --model /models/Qwen3-Coder-30B-A3B-Instruct-Q4_K_M.gguf --jinja -c 65536 -np 2 -t 16 --host 0.0.0.0 --port 8091
```
  等模型加载完再继续：`docker logs -f agentharness-llm` 里出现 `listening on http://0.0.0.0:8091` 才算就绪。判断就绪要看健康检查或日志，**不要只看进程在不在**。课程团队就踩过这个坑：脚本用 `pgrep` 判断服务已经起来，结果匹配到的是脚本自己的命令行，本地服务其实没启动，6 道题全部退回到云端完成。
- 上面用的是 llama.cpp 官方镜像，版本可能和作业 4 里你自己编译的不同，所以性能数字只在本作业内部互相比较。

## 运行（所有命令都在仓库根目录执行）
```bash
RUN="docker run --rm -it --cpus 4 --memory 8g --network agentharness-net \
  -e HTTPS_PROXY=http://agentharness-egress:8888 -e NO_PROXY=agentharness-llm \
  -e DEEPSEEK_API_KEY -e LOCAL_LLM_KEY=none -v $PWD:/work agentharness-runner:0.1"
# 对照组：完整 profile，不路由
$RUN python assignment2/run.py --agent dsh --suite mini --profile sdk --tag sdkfull --parallel 4
# 路由组：模板配置 + 路由提示（这两个文件就是你要改进的对象）
$RUN python assignment2/run.py --agent dsh --suite mini --profile sdk --tag a5 --parallel 2 --timeout 1800 \
  --patch /work/assignment5/templates/local-worker.patch.yml \
  --prompt-suffix-file assignment5/templates/routing-hint.txt
python assignment5/check.py assignment2/results/mini-dsh-a5.jsonl assignment2/results/mini-dsh-sdkfull.jsonl
```
`tools/usage_cost.py` 会按每次请求实际用到的模型分别计价，写在运行记录的 `by_model` 字段里，本地模型按 $0 计。

## 关卡
| 关卡 | 内容 | 检查 |
|---|---|---|
| L1 | 复现上面两组实验，确认子 agent 的请求确实打到了本地模型（看 `by_model` 和 llama-server 日志） | `check.py`：解决 ≥ 6/8，且至少一半的题有本地请求 |
| L2 | 分析模板路由为什么更贵：把多出来的云端请求按用途分类（委派、等待、复核……），用作业 1 的工具找证据 | 报告 |
| L3 | 改进路由策略（改提示词、改工具描述或写插件），目标是解决率不下降、云端成本低于对照组。至少做两个版本，每个版本都要有对照 | `check.py` + 报告 |
| L4 | 协同优化：结合作业 4 的推理服务参数（`-np`、前缀复用、量化）缩短本地子 agent 的耗时，并说明它对云端成本有没有影响 | 报告 |
| 加做 | 在作业 3 的 20 题上做 L3 的实验。每题都要启动任务容器，所以 `agentharness-llm` 需要和任务容器在同一个网络里，并设置 `NO_PROXY`。CPU 推理可能要跑好几个小时，请先估算时间 | 报告 |

## 提交物
- `assignment5/submission/<昵称>/`：路由配置、提示词、插件；
- `assignment2/results/` 下对应的运行记录；
- 博客形式的报告 `BLOG.md`。负面结果同样有价值，例如"在小题上路由永远不划算，原因是……"，前提是有数据支撑。
