# 作业 3：DSH-Opt —— 让 agent 又好又省

> 预计 12–18 小时，第 7 周发布、第 10 周截止。对应第 11–15 讲：上下文工程、前缀缓存、插件开发、成本与可靠性、实验方法。
> 插件机制、模板插件、运行器和排行榜流程，课程团队都已经从头到尾实际跑通过（数据见下文）。

这个作业不改 DSH 源码，只用**配置补丁**和**自己写的插件**来优化 agent。有两条赛道，选一条即可，也可以两条都参加：

| 赛道 | 题集 | 排名方式 | 基线（试做阶段实测，`deepseek-flash`） |
|---|---|---|---|
| **解决率赛道** | [instances_hard.txt](../infra/swebench/instances_hard.txt)：难题集，20 道 Verified 题，预计修复耗时 1–4 小时及以上 | 解决数优先，其次是每题成本 | 自写 loop 10/20（每题 $0.045）；DSH `sdk-minimal` 8/20（每题 $0.037） |
| **效率赛道** | [instances.txt](../infra/swebench/instances.txt)：原 20 题 | 解决数不低于 17 的前提下，比每题成本 | DSH `sdk-minimal` 17/20，每题 $0.018，中位耗时 55 s，缓存命中率 95.8% |

## 你可以改什么
- **配置**（patch 文件）：preset、工具集与工具描述、系统提示、压缩策略、`maxParallelToolCalls`、思考强度、输出上限。用 DSH 运行时的 `--dump-config` 可以列出所有插件 id 和当前配置。
- **插件**（TypeScript，**无需编译，也不用装 Node**）：DSH 运行时可以按绝对路径直接加载 `.ts` 文件（第 13 讲）。常用的挂载点：
  - `tools/post-execute`（waterfall）：工具结果进入上下文之前，替换或裁剪它
  - `tools/pre-execute`（waterfall）：工具调用分发之前，决定拒绝还是放行
  - `agent/pre-step`（waterfall）：每一步开始前修改或拒绝本步消息，可以声明 `startsRequestSeries`
  - `agent/request-error`（waterfall）：模型请求失败后，决定是否重试
  - `session/event`（emit）：观察会话事件，可以用来做统计
  - ⚠️ `agent/request` 已弃用，不要基于它开发。
- 也可以继续用作业 2 的 madsLoop 参赛（`--agent madsloop`）。

## 插件模板（已验证）
[`templates/trim-tool-output.ts`](templates/trim-tool-output.ts)：工具输出超过阈值（默认 `maxChars: 2000`）时，只保留开头和结尾。patch 里插件路径必须是绝对路径，而小题（容器里，仓库在 `/work`）和 SWE 题（宿主机）看到的路径不同，所以准备了两份 patch 模板：[`templates/mini.patch.yml`](templates/mini.patch.yml) 和 [`templates/swe.patch.yml`](templates/swe.patch.yml)。在仓库根目录执行：
```bash
NICK=你的昵称
mkdir -p assignment3/submission/$NICK
cp assignment3/templates/trim-tool-output.ts assignment3/templates/mini.patch.yml assignment3/templates/swe.patch.yml \
   assignment3/submission/$NICK/
# 小题 patch：把 NICK 换成你的昵称 → /work/assignment3/submission/<昵称>/trim-tool-output.ts
sed -i "s|NICK|$NICK|" assignment3/submission/$NICK/mini.patch.yml
# SWE patch：HOST_REPO 换成宿主机上仓库的绝对路径，NICK 换成昵称
sed -i -e "s|HOST_REPO|$PWD|" -e "s|NICK|$NICK|" assignment3/submission/$NICK/swe.patch.yml
cat assignment3/submission/$NICK/*.patch.yml     # 确认路径对
```
替换后 `mini.patch.yml` 里的内容是：
```yaml
- insert:
    - id: trim-tool-output
      name: '/work/assignment3/submission/<昵称>/trim-tool-output.ts'
      config: { maxChars: 2000 }
```
在小实验里，它让成本降到约三分之一；放到 20 道 SWE-bench 题上，效果几乎为零。完整的复盘见第 16 讲。

**确认插件真的加载了**：路径写错时 DSH 不一定报错，结果和不加插件一模一样。插件裁剪时会在工具输出里插入一行 `…[已省略 N 个字符…`，这行文字会原样写进会话日志。跑完后搜一下：
```bash
python3 - <<'EOF'
import pathlib, zstandard
n = 0
for p in pathlib.Path("assignment2/results").glob("dsh-home*/**/session.v4.jsonl*"):
    b = p.read_bytes()
    if p.suffix == ".zstd":
        b = zstandard.ZstdDecompressor().decompressobj().decompress(b)
    n += b.decode(errors="ignore").count("已省略")
print("裁剪次数:", n)
EOF
```
开插件的一组应该大于 0（前提是有工具输出超过 2000 字符），关插件的一组应该是 0。也可以对比两组运行记录里的 `input_miss` / `cache_read`。注意 `dsh-home*/` 会被下一次运行覆盖，查完再跑下一组。

## 关卡
| 关卡 | 内容 |
|---|---|
| L1 | 先在 8 道小题上跑通（几美分，命令见下），再在效率赛道的 20 题上复现基线（约 $0.4）。报告你的结果和基线差多少，并分析原因 |
| L2 | 必做：加载模板插件，在 8 道小题上跑开启和关闭两组，复现"成本明显下降"的效果；再结合第 16 讲解释为什么这个效果在 20 道 SWE 题上几乎消失。选做：在 20 题上也跑开、关两组，用数据验证你的解释 |
| L3 | 至少实现 2 个你自己的优化（插件或配置都可以），每个都要有单独的对照实验 |
| L4 | 选一条赛道，按下面的流程提交排行榜 |

L1 小题（在运行器容器里跑，和作业 2 的写法一致）：
```bash
NICK=你的昵称
# 把容器参数包成一个 shell 函数（每开一个新终端定义一次）
ahrun() {
  docker run --rm -it --cpus 4 --memory 8g --network agentharness-net \
    -e HTTPS_PROXY=http://agentharness-egress:8888 -e DEEPSEEK_API_KEY \
    -u "$(id -u):$(id -g)" -e HOME=/tmp -v "$PWD":/work agentharness-runner:0.1 "$@"
}
# 关插件（基线）
ahrun python assignment2/run.py --agent dsh --suite mini --tag $NICK-off
# 开插件：用 mini.patch.yml
ahrun python assignment2/run.py --agent dsh --suite mini --tag $NICK-on \
  --patch /work/assignment3/submission/$NICK/mini.patch.yml
```
容器里仓库挂在 `/work`，所以小题用 `mini.patch.yml`（`/work/...` 路径）；SWE 模式在宿主机上运行，用 `swe.patch.yml`（宿主机绝对路径）。

**重复实验**：运行器会跳过结果文件里已有记录的题（见作业 2「断点续跑」）。同一配置重复跑多次时，每次换一个 `--tag`（例如 `$NICK-on-r2`），或者加 `--fresh`（旧文件会被改名备份）。

## 预算建议
单次运行的成本约为：小题 8 道 $0.01，效率赛道 20 题 $0.4，难题集 20 题 $0.8。例如 2 个优化，每个做开、关两组，每组重复 3 次，在效率赛道上总共约 $5（约 35 元）。**先在小题上调试，确认能跑通后再上 20 题。**

## 方法要求
- **每个结论都要有对照**：一次只改一个变量，并说明你如何处理运行间的随机性（重复了几次、方差多大）。见第 15 讲。
- 成本按官方**高峰价**计算（`tools/usage_cost.py`），缓存命中率单独报告。
- 不允许针对具体题目特殊处理：插件不能读取题号或 issue 文本来走特殊分支。

## 运行与提交排行榜
所有命令都在仓库根目录执行。把你的 patch 和插件放在 `assignment3/submission/<昵称>/` 下：SWE 模式会把这个目录只读挂载进任务容器，所以 patch 里要用绝对路径引用插件。

```bash
NICK=你的昵称
TRACK=efficiency; SET=infra/swebench/instances.txt;      DS=infra/swebench/dataset.json
# 解决率赛道改用：TRACK=accuracy; SET=infra/swebench/instances_hard.txt; DS=infra/swebench/dataset_hard.json

# 1. 运行
python assignment2/run.py --agent dsh --suite swe --parallel 1 --instances $SET \
    --patch $PWD/assignment3/submission/$NICK/swe.patch.yml --tag $NICK
# 2. 官方判分。报告 dsh-$NICK.$NICK.json 写在当前目录，移进 results/
python -m swebench.harness.run_evaluation -d $DS -p assignment2/results/predictions-dsh-$NICK.jsonl -id $NICK
mv dsh-$NICK.$NICK.json assignment2/results/
# 3. 生成提交文件，然后发起 PR（提交 leaderboard/ 下的 JSON 和 submission/$NICK/ 目录）
python assignment3/score.py --run assignment2/results/swe-dsh-$NICK.jsonl --report assignment2/results/dsh-$NICK.$NICK.json \
    --track $TRACK --config-dir assignment3/submission/$NICK --name $NICK > leaderboard/$NICK-$TRACK.json
```
`score.py` 会做以下检查：运行记录是否覆盖整个题集、评测报告是否与运行记录对应、有没有运行出错的题。维护者会抽查复现：用你的配置重跑一遍，解决数允许相差 ±2；`config_sha` 用来核对配置是否一致。提交后的结果显示在[排行榜](../docs/leaderboard.md)页面。

## 提交物
- `assignment3/submission/<昵称>/`：patch 文件和插件源码；
- `leaderboard/<昵称>-<赛道>.json`；
- `assignment2/results/` 下对应的运行记录 `swe-dsh-<昵称>.jsonl`、`predictions-dsh-<昵称>.jsonl` 和评测报告 `dsh-<昵称>.<昵称>.json`；
- 一篇博客形式的报告 `assignment3/submission/<昵称>/BLOG.md`，写你的优化思路和数据；
- 视频可选。
