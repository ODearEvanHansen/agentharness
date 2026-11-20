# 作业 5：DSH-Stack —— 云端模型和本地模型混合使用（草稿）

> 🚧 草稿：多模型路由已经实测打通（数据见下文），任务集和排行榜还在建设中。
> 预计 12–18 小时，对应第 13–14 周课程。

前面的作业里，你分别优化过 harness（作业 3）和推理服务（作业 4）。这个作业要把两者合起来：**主 agent 用 DeepSeek API，一部分子任务交给你在本机托管的模型**，在"解决率 × 成本 × 耗时"三个指标上一起优化。本地模型能力弱一些，但只要路由策略得当，就不会拖垮整体任务。

## 已验证的路由机制
DSH 的 `@deepseek-ai/dsh-tool-subagent` 插件可以多实例挂载。新挂一个实例，通过 `agentOptions` 把子 agent 固定到另一个 provider/model 上即可，模板在 [`templates/local-worker.patch.yml`](templates/local-worker.patch.yml)：

```yaml
- insert:
    - id: tool-subagent-local
      name: '@deepseek-ai/dsh-tool-subagent'
      config:
        provider: spawn
        toolName: local_worker
        agentOptions: { provider: local, model: qwen3-coder-30b-a3b, maxTokens: 4096 }
```

M0 实测（`sdk` 完整 profile；主 agent 用 `deepseek-flash`，子 agent 用本机 CPU 上的 Qwen3-Coder-30B-A3B；任务：派子 agent 统计文件里大于 50 的数有多少个）：

| | 请求数 | 输入 token（未命中 / 命中） | 成本 |
|---|---|---|---|
| 主 agent（DeepSeek） | 7 | 10,243 / 59,264 | $0.0046 |
| 子 agent（本地） | 6 | 14,635 / 65,691（llama.cpp 前缀复用） | $0 |

答案正确（245）。但要注意：**主 agent 拿到子 agent 的结果后，自己又算了一遍来复核**。这是混合路由的典型隐性成本："不信任"本地模型，就会把省下的钱又花回去。你的路由策略需要解决这个问题。

`tools/usage_cost.py` 的 `summarize()` 会按每次请求实际使用的模型分别计价（返回值里的 `by_model` 字段），本地模型按 $0 计算。

## 关卡（草案）
| 关卡 | 内容 |
|---|---|
| L1 | 复现上面的路由实验，确认子 agent 的请求确实打到了本地模型（看会话日志里的 `message.source.model` 和 llama-server 的日志） |
| L2 | 在作业 3 的 20 题上，比较三种配置：全部走 DeepSeek / 全部走本地 / 你设计的混合路由。报告解决率、成本和耗时 |
| L3 | 设计路由策略：哪类子任务交给本地模型（例如搜索代码、运行测试、总结日志），提示词和工具描述该怎么写，如何避免主 agent 重复劳动 |
| L4 | 协同优化：结合作业 4 的推理服务参数（`-np`、前缀复用、量化），让本地子 agent 更快 |
| L5 | 提交排行榜（主指标为解决率；成本和耗时作为第二、第三指标） |

## 关于耗时
本地 30B-A3B 模型在 CPU 上的预填充速度只有约 120 tok/s，子 agent 每次请求要带上约 1 万 token 的系统提示和工具定义。冷启动的第一次请求要花上百秒，之后依赖前缀复用（作业 4 的 E2）才能降下来。这是本作业最主要的权衡点。

## 提交物
路由配置和插件、运行记录、博客形式的报告（`BLOG.md`），以及可选的视频。
