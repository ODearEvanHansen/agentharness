# 15 分钟轻量入口：用约 150 行代码跑一个 coding agent，算出解决率和花费

不需要 Docker，不需要 GPU，macOS / Linux / Windows 都可以，只要 Python 3.9+ 和一个 DeepSeek API key。

```bash
git clone https://github.com/ODearEvanHansen/agentharness && cd agentharness
export DEEPSEEK_API_KEY=sk-...        # 建议为本课程单独创建 key，只充值少量金额
python3 quickstart/quickstart.py
```

不需要 pip 安装任何依赖（只用标准库）。跑完会打印每道题是否通过、请求次数、花费（元），以及总解决率和缓存命中率。3 道题合计通常只要几分钱。

## 这 150 行在做什么

`quickstart.py` 就是一个完整的 agent loop：

1. 把题目和系统提示放进 `messages` 列表，带上 4 个工具（读文件、写文件、运行测试、完成）请求模型；
2. 模型返回工具调用 → 本地执行 → 把结果作为 `tool` 消息追加回去；
3. 重复，直到模型调用 `done` 或步数用完；
4. 最后用**原始测试文件**重新判分，并按官方人民币价目把 token 用量换算成费用。

每一轮都把整段历史重新发给模型，前缀不变的部分会命中 DeepSeek 的前缀缓存，价格只有未命中部分的约 2%：这就是输出里"缓存命中率"的意义。

## 安全说明

agent 只有读文件、写文件、运行该题测试三个工具，没有任意 shell；文件操作被限制在系统临时目录里的题目副本中。所以不需要 Docker 隔离。完整课程里的 agent 有 shell 权限，那时才需要容器。

## 接下来

- 换个模型：`python3 quickstart/quickstart.py --model deepseek-v4-pro`，对比解决率和花费。
- 只跑一道：`--tasks t05_parse_duration`。
- 想自己写这个 loop、在真实 SWE-bench 题上和工业级 harness 对比：看[作业 2](https://odearevanhansen.github.io/agentharness/assignments/a2/)（需要 Linux/WSL2 + Docker）。
