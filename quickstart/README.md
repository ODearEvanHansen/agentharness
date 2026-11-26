# 15 分钟轻量入口：用约 150 行代码跑一个 coding agent，算出解决率和花费

不需要 Docker，不需要 GPU，macOS / Linux / Windows 都可以，只要 Python 3.9+ 和一个 DeepSeek API key（在 [platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys) 申请）。

已实测：Linux / Python 3.9、3.14；macOS 14（Apple Silicon）/ Homebrew Python 3.14，3/3 通过。

```bash
git clone https://github.com/ODearEvanHansen/agentharness && cd agentharness
export DEEPSEEK_API_KEY=sk-...        # 建议为本课程单独创建 key，只充值少量金额
python3 quickstart/quickstart.py
```

不需要 pip 安装任何依赖（只用标准库）。跑完会打印每道题是否通过、请求次数、花费（元），以及总解决率和缓存命中率。3 道题合计约 1 分钱（低峰实测 0.007–0.008 元，白天高峰约 0.015 元，原因见下文）。

## 正常输出长什么样

```text
[t01_sum_range]
    · read_file mathx.py
    · write_file mathx.py
    · run_tests
    · done
    → 通过  请求 4 次  0.0025 元
...
模型 deepseek-flash（低峰价）
解决率 3/3   总花费 0.0074 元   缓存命中率 78%
```

题目名、行数和金额每次会略有不同。几点说明：

- **"请求 N 次"比工具调用行数少是正常的**：模型一次回复可以同时发起多个工具调用，每个工具调用打印一行。
- **高峰价 / 低峰价**：DeepSeek 在北京时间工作日 9–12、14–18 点按高峰价计费，其余时间是低峰价，低峰价是高峰价的一半。脚本按运行时刻自动选择（不判断节假日），所以白天跑花费大约翻倍。

## 这 150 行在做什么

`quickstart.py` 就是一个完整的 agent loop：

1. 把题目和系统提示放进 `messages` 列表，带上 4 个工具（读文件、写文件、运行测试、完成）请求模型；
2. 模型返回工具调用 → 本地执行 → 把结果作为 `tool` 消息追加回去；
3. 重复，直到模型调用 `done` 或步数用完；
4. 最后用**原始测试文件**重新判分，并按官方人民币价目把 token 用量换算成费用。

每一轮都把整段历史重新发给模型，前缀不变的部分会命中 DeepSeek 的前缀缓存，价格只有未命中部分的约 2%：这就是输出里"缓存命中率"的意义。

## 安全说明

agent 只有读文件、写文件、运行该题测试三个工具，没有任意 shell；文件操作被限制在系统临时目录里的题目副本中。但要清楚：`write_file` 能写 `.py`，`run_tests` 会在你的机器上运行这些 Python 代码，所以它其实仍能在宿主机执行任意 Python。这里不用 Docker，只是因为这 3 道小题是课程自带的可信代码、不含外部不可信内容；对真实仓库跑 agent 仍然需要 Docker 隔离。完整课程里的 agent 有 shell 权限，那时才需要容器。

## 接下来

- 换个模型：`python3 quickstart/quickstart.py --model deepseek-v4-pro`，对比花费和耗时（这三道题两个模型通常都能全解，差别主要在价格）。
- 只跑一道：`--tasks t05_parse_duration`。
- 想自己写这个 loop、在真实 SWE-bench 题上和工业级 harness 对比：看[作业 2](https://odearevanhansen.github.io/agentharness/assignments/a2/)（需要 Linux/WSL2 + Docker）。
