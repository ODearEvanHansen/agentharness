# 作业 2：madsLoop —— 自己写一个 agent loop

> 预计 10–12 小时。对应第 3–5 周的课程（agent loop、工具设计、评测）。

所谓 agent，本质上就是"模型 + 循环 + 工具"。在这个作业里，你只用 Python 标准库写一个最小的 agent loop，让它在隔离容器里解真实的 SWE-bench 题目，然后和工业级 harness（DSH）做对照。

**参考数据**（课程 M0 实测，`deepseek-flash`，20 道分层抽样的 Verified 题）：一个约 110 行的 loop 解决了 18/20，DSH `sdk-minimal` 解决了 17/20；loop 每题约 $0.026，DSH 每题约 $0.018。所以你写的 loop 有能力解出大部分题，但你得说清楚它为什么更贵。

## 准备
- 完成[作业 0](../assignment0/)，包括关卡 3（拉取 GHCR 镜像）。
- SWE 题目要在隔离网络中运行：按照 [infra/README.md](../infra/README.md) 建好 `agentharness-net` 和出网白名单代理 `agentharness-egress`。
- `export DEEPSEEK_API_KEY=...`

## Part A：实现 madsLoop（`madsloop/agent.py`）

| 关卡 | 内容 | 检查 |
|---|---|---|
| L1 | 写系统提示、定义 4 个工具（bash / read_file / edit_file / done），用 `Env` 实现 `run_tool` | 单元检查 |
| L2 | 主循环：调用模型、执行工具、累加 token 用量、判断停止条件 | 课程小题 ≥ 6/8 |
| L3 | 在 SWE 子集（[infra/swebench/instances.txt](../infra/swebench/instances.txt)，20 题）上运行，并用官方评测判分 | 记录解决率 |

```bash
cd assignment2
python make_tasks.py                                   # 生成 8 道课程小题到 tasks/
python run.py --agent madsloop --suite mini            # 小题：运行即判分
python run.py --agent madsloop --suite swe --parallel 3
python ../infra/swebench/make_dataset_cn.py --instances ../infra/swebench/instances.txt --out ds.json
python -m swebench.harness.run_evaluation -d ds.json -p results/predictions-madsloop.jsonl -id a2-mine
```

**容易踩的坑（提前告诉你）**
1. **思考模式**：DeepSeek 默认开启思考模式。带 `tool_calls` 的 assistant 消息必须原样带回 `reasoning_content`，否则下一次请求会返回 400。
2. **用量字段**：`prompt_cache_hit_tokens` 是命中缓存的输入，`prompt_cache_miss_tokens` 是未命中的输入，两者价格相差约 50 倍。
3. **模型没有调用工具**：这时 loop 该怎么继续？不同的处理方式对步数和成本的影响很大。
4. **输出截断**：`Env.bash` 只返回最后 8000 个字符。你要考虑模型读大文件时会发生什么。

## Part B：阅读 DSH 的 loop
回答 [QUESTIONS.md](QUESTIONS.md) 里的 B1–B5。

## Part C：对照实验
```bash
python run.py --agent dsh --suite mini
python run.py --agent dsh --suite swe --parallel 3
```
在同一批题上比较 madsLoop 和 DSH，写一页分析，至少包括：
- 解决率、平均步数、输入/输出 token、缓存命中率、每题成本、中位耗时（表格）；
- **一道两边结果不同的题**：用作业 1 的工具对比两边的轨迹，解释差别是怎么来的；
- 工具设计对步数的影响：DSH 在一次 bash 调用里同时写文件和运行，你的 loop 是怎么做的？

## 贡献题目（社区题库）
每人提交 2–3 道新的小题，格式和 `tasks/` 一致：`PROMPT.txt` 加上 `test_task.py`（退出码 0 表示通过），另外附一句话说明这道题考察什么能力。审核通过的题会进入课程题库，并署名。要求：
- 修复前测试必须失败；
- 不依赖网络；
- 正常解法在 10 步以内。

## 提交物
提交到 `assignment2/` 目录：
1. `madsloop/agent.py`，以及 `results/` 下的运行记录（jsonl 文件和官方评测报告）；
2. `WRITEUP.md`：Part B 的回答 + Part C 的分析，共 2–4 页；
3. `contrib/` 目录下你贡献的 2–3 道题。

## 规则
- madsLoop 只能用标准库和起始代码里提供的 `chat()`，不能用任何 agent 框架。
- 禁止针对具体题目硬编码，比如在提示词里写入某个 issue 的修复方法。
- 运行器会检查 `test_task.py` 有没有被修改，改测试文件的解答不算数。
