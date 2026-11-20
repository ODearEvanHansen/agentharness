# 作业 3：DSH-Opt —— 让 agent 又好又省（草稿）

> 🚧 草稿：插件机制和第一个模板已经实测可用（数据见下文），排行榜和难题集还在建设中。
> 预计 10–15 小时，对应第 6–8 周课程（上下文工程、前缀缓存、成本与可靠性）。

在 DSH 上，你不改 DSH 的源码，只通过**配置补丁**和**自写插件**来优化 agent。目标有两条赛道（二选一，也可以都参加）：

| 赛道 | 题集 | 指标 |
|---|---|---|
| **解决率赛道** | [infra/swebench/instances_hard.txt](../infra/swebench/instances_hard.txt)（20 题，Verified 1–4h/>4h；M0 基线：自写 loop 10/20、DSH 8/20，每题约 $0.04） | 解决数；预算硬上限 |
| **效率赛道** | [infra/swebench/instances.txt](../infra/swebench/instances.txt)（20 题） | 解决率不低于基线的前提下，比每题成本和中位耗时 |

**基线**（M0 实测，`deepseek-flash`，DSH `sdk-minimal`）：17/20，每题 $0.018，中位耗时 55 s，缓存命中率 95.8%。

## 你可以改什么
- **配置**（`cordis.patch.yml`）：preset（Standard / PTC / Minimal）、工具集与工具描述、系统提示、压缩策略、`maxParallelToolCalls`、推理强度、输出上限。用 `dsh --profile <p> --dump-config` 可以查看所有插件 id 和当前配置。
- **插件**（TypeScript，**不需要编译、不需要 Node**）：DSH 运行时可以直接按绝对路径加载 `.ts` 文件。常用的挂载点：
  - `tools/post-execute`（waterfall）：在工具结果进入上下文之前，替换或裁剪它
  - `tools/pre-execute`（waterfall）：在工具调用分发前拒绝或放行
  - `agent/pre-step`（waterfall）：在每一步进入前修改或拒绝本步消息；可以声明 `startsRequestSeries`
  - `agent/request-error`（waterfall）：模型请求失败后决定是否重试
  - `session/event`（emit）：观察会话事件，可用于统计
  - ⚠️ `agent/request` 已被弃用，不要基于它开发。
- 你也可以继续使用作业 2 的 madsLoop 参赛。

## 插件模板（已验证）
[`templates/trim-tool-output.ts`](templates/trim-tool-output.ts)：工具输出超过阈值时，只保留开头和结尾。

加载方式（在你的 patch 文件里插入；路径必须是绝对路径）：
```yaml
- id: session-log-deepseek
  config: { enabled: false }
- insert:
    - id: trim-tool-output
      name: '/abs/path/to/assignment3/templates/trim-tool-output.ts'
      config: { maxChars: 2000 }
```

M0 实测（`sdk-minimal`，任务：运行一个输出 3000 行的脚本，再回答第 1、1500、3000 行分别是什么）：

| | 第一次工具结果 | 未命中输入 token | 成本 | 答案 |
|---|---|---|---|---|
| 不裁剪 | 17,174 字符 | 6,441 | $0.00259 | 正确 |
| 裁剪（2000 字符） | 2,500 字符 | 1,063 | $0.00088 | 正确（模型看到省略提示后，自己用了一条更精确的命令） |

成本降到约 1/3。但在 SWE-bench 上，裁剪会不会让模型错过关键的报错信息？**需要你自己测**。

## 关卡
| 关卡 | 内容 |
|---|---|
| L1 | 在 20 题上复现基线（用自己的 key 跑一轮，约 $0.4），报告和基线的差异，并分析差异来自哪里（随机性？） |
| L2 | 加载模板插件，在 20 题上对比打开和关闭两种情况，报告解决率、成本、缓存命中率的变化 |
| L3 | 至少实现 2 个自己的优化（插件或配置均可），每个都要有独立的对照实验 |
| L4 | 选一个赛道提交排行榜（提交格式即将公布） |

## 方法要求
- **每个结论都要有对照**：只改一个变量，并说明你如何处理运行之间的随机性，比如重复运行几次、报告方差。
- 成本按官方**高峰价**计算（`tools/usage_cost.py`），并单独报告缓存命中率。
- 不允许针对具体题目做特殊处理：插件不能读取题号或 issue 文本来走特殊分支。

## 运行与提交排行榜
```bash
# 1. 把你的 patch 和插件放进同一个目录（SWE 模式下这个目录会只读挂载进任务容器），patch 里用绝对路径引用插件
python assignment2/run.py --agent dsh --suite swe --parallel 3 \
    --patch $PWD/assignment3/submission/my.patch.yml --tag mine \
    --instances infra/swebench/instances.txt          # 解决率赛道改为 instances_hard.txt
# 2. 官方判分
python infra/swebench/make_dataset_cn.py --instances infra/swebench/instances.txt --out ds.json
python -m swebench.harness.run_evaluation -d ds.json -p assignment2/results/predictions-dsh-mine.jsonl -id mine
# 3. 生成提交文件，然后发起 PR
python assignment3/score.py --run assignment2/results/swe-dsh-mine.jsonl --report dsh-mine.mine.json \
    --track efficiency --config-dir assignment3/submission --name 你的昵称 > assignment3/submission/leaderboard.json
```
维护者会抽查复现：用你的配置重跑一遍，解决数允许相差 ±2。`config_sha` 用来核对配置是否一致。

## 提交物
`assignment3/` 目录：patch 文件、插件源码、运行记录，以及一篇博客形式的报告（`BLOG.md`，介绍你的优化思路和数据），可选一段视频。
