# 作业 2：miniLoop —— 自己写一个 agent loop

> 预计 15–20 小时。第 4 周发布，第 7 周截止。对应第 2 讲（最小 agent 循环）、第 7–9、14–16 讲（agent loop、评测基础设施、工具设计、评测；第 16 讲的重复次数、pass@k 与配对比较用于解读和报告结果）。

agent 本质上就是"模型 + 循环 + 工具"。这个作业要你只用 Python 标准库写一个最小的 agent loop，让它在隔离容器里解真实的 SWE-bench 题目，再和工业级 harness（DSH）做对照。

**参考数据**（试做阶段（开课前课程团队的完整试做）实测，`deepseek-flash`，20 道分层抽样的 Verified 题）：一个约 110 行的 loop 解出 18/20，DSH `sdk-minimal` 解出 17/20；loop 每题约 0.17 元，DSH 每题约 0.12 元。也就是说，你写的 loop 有能力解出大部分题，但你需要讲清楚它为什么更贵。

## 准备
- 完成[作业 0](../assignment0/)，包括隔离网络、运行器镜像和 GHCR 镜像拉取。
- **所有命令都在仓库根目录执行。**
- 宿主机上需要 `deepseek-harness-sdk==0.2.2rc2 swebench==5.0.2 zstandard`（作业 0 已经装过）。SWE 模式下运行器在宿主机上启动任务容器，官方评测也在宿主机上运行。
- **磁盘**：每道 SWE 题的镜像约 3GB，20 题约 60GB。磁盘紧张时，用 `--parallel 1`，并在每题评测完后执行 `docker rmi` 删除镜像。
- **内存**：`--parallel N` 会同时运行 N 个容器，每个上限 8GB。16GB 内存的机器请用 `--parallel 1`。

**运行器已验证**（课程参考实现）：小题 miniLoop 8/8（0.057 元）、DSH 8/8（0.043 元）；`django__django-15467` 两边都通过了官方评测（miniLoop 24 步 0.087 元，DSH 0.055 元）。

## Part A：实现 miniLoop（`miniloop/agent.py`）

| 关卡 | 内容 | 检查 |
|---|---|---|
| L1 | 写系统提示，定义 4 个工具（bash / read_file / edit_file / done），用 `Env` 实现 `run_tool` | 由 L2 的小题一并检查 |
| L2 | 主循环：调用模型、执行工具、累加 token 用量、判断何时停止 | 课程小题 ≥ 6/8 |
| L3 | 在 SWE 子集上运行（[instances.txt](../infra/swebench/instances.txt)，20 题），用官方评测判分 | 记录解决率 |

### 在容器里跑小题

**小题**会执行模型生成的 shell 命令，所以必须在运行器容器里跑（不在容器里时运行器会拒绝执行）：
```bash
docker run --rm -it --cpus 4 --memory 8g --network agentharness-net \
  -e HTTPS_PROXY=http://agentharness-egress:8888 -e DEEPSEEK_API_KEY \
  -u "$(id -u):$(id -g)" -e HOME=/tmp -v "$PWD":/work agentharness-runner:0.1 python assignment2/run.py --agent miniloop --suite mini
```
判分在一份干净副本里进行：只采用你对原有源文件的修改。新增的文件（例如 `conftest.py`）不会带入判分副本，改动 `test_task.py` 的解答直接判为不通过。

**SWE 题**：运行器在宿主机上为每道题启动一个隔离的任务容器，agent 只在任务容器里执行命令（新开终端先按 docs/setup.md 激活 `~/.venvs/agentharness` 并加载 `~/.config/agentharness/env`）：
```bash
python assignment2/run.py --agent miniloop --suite swe --parallel 1
python -m swebench.harness.run_evaluation -d infra/swebench/dataset.json \
  -p assignment2/results/predictions-miniloop.jsonl -id a2-mine
mv miniloop.a2-mine.json assignment2/results/     # 官方评测把报告写在当前目录（仓库根目录）
```
报告文件名是 `<模型名>.<run_id>.json`，模型名取自 predictions 里的 `model_name_or_path`（这里是 `miniloop`）；如果 `mv` 找不到文件，用 `ls *.a2-mine.json` 看实际名字。
**断点续跑**：结果按题追加写入 `assignment2/results/<suite>-<agent>[-<tag>].jsonl`。再次运行同样的命令时，已有无错误记录的题会跳过，并打印 `跳过 N 道已有记录的题（结果文件 ...）；要重跑请加 --fresh 或换 --tag`；出错的题会重跑。想全部重跑：加 `--fresh`（旧文件改名为 `<名字>.jsonl.bak-<时间戳>` 留作备份），或者换一个 `--tag` 写到新文件。改了 agent 代码之后一定要这么做，否则看到的还是旧结果。

数据集 `dataset.json` 已随仓库提供，**不需要访问 Hugging Face**。单题超时（`--timeout`，默认 1200 秒）后，运行器会删除该题的任务容器，agent 随之停止。

**容易踩的坑（提前告诉你）**
1. **思考模式**：DeepSeek 默认开启思考模式。带 `tool_calls` 的 assistant 消息必须原样带回 `reasoning_content`，否则下一次请求会返回 400。
2. **用量字段**：`prompt_cache_hit_tokens` 是命中缓存的输入，`prompt_cache_miss_tokens` 是未命中的输入，两者价格相差 50 倍。
3. **模型没有调用工具**：这时 loop 该怎么继续？不同的处理方式对步数和成本影响很大。
4. **输出截断**：`Env.bash` 只返回输出的最后 8000 个字符。想一想模型读大文件时会发生什么。

## Part B：阅读 DSH 的 loop
回答 [QUESTIONS.md](QUESTIONS.md) 里的 B1–B4。B5 选做（加分）。源码是 TypeScript，只需要能读懂函数结构和控制流，第 7、8 讲会带你读一遍。

## Part C：对照实验
```bash
docker run --rm -it --cpus 4 --memory 8g --network agentharness-net \
  -e HTTPS_PROXY=http://agentharness-egress:8888 -e DEEPSEEK_API_KEY \
  -u "$(id -u):$(id -g)" -e HOME=/tmp -v "$PWD":/work agentharness-runner:0.1 python assignment2/run.py --agent dsh --suite mini
python assignment2/run.py --agent dsh --suite swe --parallel 1
python -m swebench.harness.run_evaluation -d infra/swebench/dataset.json \
  -p assignment2/results/predictions-dsh.jsonl -id a2-mine
mv dsh.a2-mine.json assignment2/results/
```
在同一批题上比较 miniLoop 和 DSH，写一页分析，至少包括：
- 一张表：解决率、平均步数、输入/输出 token、缓存命中率、每题成本、中位耗时；
- **一道两边结果不同的题**：用作业 1 的工具对比两边的轨迹，解释差别从哪里来；
- 工具设计对步数的影响：DSH 一次 bash 调用就能同时写文件和运行，你的 loop 是怎么做的？

> 解读差异时参考第 16 讲：每边各跑一次时，差一两道题通常在随机波动内；按题配对对比，并在报告里写明各跑了几次。不要求为此额外重复运行（不增加 API 花费）。

## 贡献题目（选做，加分）
提交 2–3 道新的小题，格式和 `tasks/` 一致：`PROMPT.txt` 加 `test_task.py`（退出码为 0 表示通过），并用一句话说明这道题考察什么能力。审核通过的题会署名进入课程题库。要求：
- 修复前测试必须失败；
- 不依赖网络；
- 正常解法在 10 步以内。

## 提交物
提交到 `assignment2/` 目录：
1. `miniloop/agent.py`；
2. `results/` 下的结果文件（`git add assignment2/results/` 即可，中间产物已被 `.gitignore` 忽略）：
   - **要提交**：`mini-*.jsonl`、`swe-*.jsonl`、`predictions-*.jsonl`，以及官方评测报告 `*.a2-mine.json`；
   - **不提交（已忽略）**：`results/work/`、`results/judge/`（小题工作副本和判分副本）、`results/dsh-home*/`、`results/dsh-homes/`（DSH 会话日志）、`--fresh` 留下的 `*.bak-*` 备份，以及仓库根目录下评测生成的 `logs/`；
3. `WRITEUP.md`：Part B 的回答加 Part C 的分析，共 2–4 页；
4. （选做）`contrib/` 下你贡献的题目。

## 规则
- miniLoop 只能使用标准库和起始代码提供的 `chat()`，不能使用任何 agent 框架。
- 禁止针对具体题目硬编码，例如在提示词里写入某个 issue 的修法。

## 选做：无 agent 基线（no-agent baseline）
同一个模型，不给工具、不循环，一次请求直接作答——用来回答"agent 到底多做了什么"。脚本：[noagent.py](noagent.py)。
```bash
# SWE 子集：issue + 金标准补丁改动到的文件全文（"oracle 文件"）→ 一个 unified diff → 官方评测
python assignment2/noagent.py --suite swe --judge
# 小题：题面 + 题目目录所有文件 → 模型按固定格式返回完整新文件 → 干净副本里跑 test_task.py（必须在容器里）
docker run --rm -it --cpus 4 --memory 8g --network agentharness-net \
  -e HTTPS_PROXY=http://agentharness-egress:8888 -e DEEPSEEK_API_KEY \
  -u "$(id -u):$(id -g)" -e HOME=/tmp -v "$PWD":/work agentharness-runner:0.1 python assignment2/noagent.py --suite mini
```
结果写在 `assignment2/results/noagent/`。**注意**：oracle 文件设定是无 agent 方案的宽松上界——现实中没人告诉模型该改哪些文件，agent 要自己找。

课程组跑了一次（deepseek-flash，思考模式，`--max-tokens 32768`，按高峰价）：

| 题集 | 无 agent | 成本 | 中位耗时 | 对照：自写 loop / DSH |
|---|---|---|---|---|
| SWE 20 题（oracle 文件） | 14/20 | 3.19 元（每题 0.16 元） | 65 s | 18/20 / 17/20 |
| 课程小题 8 题 | 8/8 | 0.03 元 | 2 s | — / 8/8 |

SWE 的 6 道失败里有 5 道是思考过程用满 32768 个输出 token、一行答案都没给（这 5 道就花了约 1.58 元）；另有 2 道模型给的 diff 漏了 `---/+++` 文件头，脚本按唯一的 oracle 文件补头后通过（不补头是 12/20）。只跑了一次，方差未测。
