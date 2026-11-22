# 作业 1：DSH-Lens —— 观察 agent 在做什么

> 预计 6–10 小时。第 2 周发布，第 4 周截止，对应第 3–5 讲（DSH 导论、事件与会话日志、子 agent）。需要先完成作业 0。

用别人写的 agent 很容易，但想看清它每一步在干什么、为什么花这么多钱，就难多了。这个作业要你做一个网页，用 [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness)（DSH）的 Python SDK 驱动 agent，并**实时**把它的执行过程展示出来。后面几个作业都要靠这个工具来分析 agent 的行为。

## 你会学到
- 一个编码 agent 跑一轮会产生哪些事件：turn、step、助手消息、思考、工具调用和结果、子 agent。
- token 用量和前缀缓存在真实 agent 里是什么样子（完整 profile 的系统提示和工具定义约 1 万 token）。
- 事件流（实时、无用量信息）和会话日志（落盘、有用量信息）这两种数据源的区别。

## 准备
- 完成[作业 0](../assignment0/)，包括关卡 1 第 4 步（隔离网络和运行器镜像）。
- **必须在容器里运行。** 起始代码用的是 DSH 完整 profile，并设置了 `DSH_PERMISSION_MODE=danger-full-access`，agent 能执行任意 shell 命令，隔离全靠容器（第 1 讲讲过原因）。如果不在容器里，`app.py` 会拒绝启动。

**启动**（在仓库根目录执行）：
```bash
docker run --rm -it --name agentharness-a1 --cpus 4 --memory 8g --network agentharness-net \
  -e HTTPS_PROXY=http://agentharness-egress:8888 -e DEEPSEEK_API_KEY \
  -u "$(id -u):$(id -g)" -e HOME=/tmp -v "$PWD":/work agentharness-runner:0.1 \
  python -m uvicorn --app-dir assignment1/starter app:app --host 0.0.0.0 --port 8765
```
`--internal` 网络里的容器不能做端口映射。浏览器访问有两种方式：
- 查到容器的 IP（`docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' agentharness-a1`），在宿主机上打开 `http://<IP>:8765`。Linux 上可以直接访问，WSL2 下要在 WSL 里的浏览器或用 curl 访问。
- 或者启动一个只做端口转发的小容器，同时接入两个网络（WSL2 和远程主机推荐这种）。**不要**把 agent 容器本身接到普通网络上，那样做会让第三条白名单验证失效。
  ```bash
  docker run -d --name agentharness-portfwd --network bridge -p 127.0.0.1:8765:8765 \
    alpine/socat TCP-LISTEN:8765,fork TCP:agentharness-a1:8765
  docker network connect agentharness-net agentharness-portfwd
  curl -s 127.0.0.1:8765/ | head      # 能看到页面 HTML 就通了
  ```
  之后浏览器打开 `http://127.0.0.1:8765`（WSL2 下 Windows 浏览器一般也能直接访问；远程主机用 `ssh -L 8765:127.0.0.1:8765 <主机>` 再在本地打开）。用完执行 `docker rm -f agentharness-portfwd`。

  WSL2 下 Windows 浏览器打不开时：先在 WSL 里跑上面的 `curl`，这一步不通就是容器问题；WSL 里通而浏览器不通，检查 Docker Desktop → Settings → Resources → WSL integration 是否启用了你的发行版；还不行就在 PowerShell 执行 `wsl hostname -I`，用第一个 IP 打开 `http://<IP>:8765`。详见 [FAQ](../docs/faq.md)。

> **注意**：`-v "$PWD":/work` 让 agent 能读写整个仓库。提交前在宿主机上用 `git status` / `git diff` 看一眼 agent 有没有改动起始代码之外的文件；key 不要放在仓库里（见作业 0）。`-u` 让容器以你的用户身份运行，避免在仓库里留下 root 所有、宿主机删不掉的文件。

前端会用到少量 HTML/JavaScript：`EventSource`（SSE）、`fetch` 和简单的 DOM 操作。不熟悉的话，先读 MDN 的 [Server-sent events](https://developer.mozilla.org/zh-CN/docs/Web/API/Server-sent_events)（约 20 分钟）。

## 起始代码里已经有的
- `app.py`：启动 DSH（加载课程配置，**关闭会话日志上传**）；`POST /api/run` 提交 prompt 或续聊；`GET /api/stream/{sid}` 用 SSE 按顺序推送这个会话树的全部原始事件，支持 `?since=N` 断点续传。
- `static/index.html`：能提交任务，能把原始事件打印出来。
- `../../tools/usage_cost.py`：读取 DSH 会话日志（包括 `.zstd` 压缩格式），统计 token 和成本。

## 关卡

| 关卡 | 内容 | 自动检查 |
|---|---|---|
| L1 | 跑通起始代码，在页面上看到原始事件 | ✅ |
| L2 | **轨迹渲染**：助手文本用 markdown 显示，思考内容可折叠；每个工具调用显示为可折叠卡片（参数 + 结果） | ✅（后端部分） |
| L3 | **状态**：单个调用 pending → ok/error；整轮 running → completed；**续聊**（同一会话多轮） | ✅ |
| L4 | **成本**：请求数、未命中输入 / 缓存命中 / 输出 token、缓存命中率、成本（元）、耗时、轮数 | ✅ |
| L5 | **子 agent 树**：子 agent 的事件挂在对应节点下，侧边栏显示树结构 | ✅ |
| 加做 | 见下文 | — |

### 后端契约（自动检查依赖它）
实现 `GET /api/sessions/{sid}/summary`，返回：
```json
{
  "session_id": "session-...",
  "status": "idle | running",
  "turns": [{"n": 1, "status": "completed", "seconds": 12.3}],
  "tool_calls": [{"call_id": "call_...", "name": "bash", "status": "pending | ok | error", "session_id": "所属会话（根或子 agent）"}],
  "usage": {"requests": 9, "input_miss": 3008, "cache_read": 84992, "output": 1590, "cny": 0.022},
  "agents": [{"session_id": "session-...", "parent": null}, {"session_id": "...", "parent": "session-..."}]
}
```
`usage` 要把根会话和所有子会话加起来，价格按 DeepSeek 官方高峰价计算（`usage_cost.PRICES`）。

### 运行自动检查
```bash
docker exec agentharness-a1 python assignment1/check.py --url http://127.0.0.1:8765 --dsh-home assignment1/starter/.dsh-home
```
检查会真实调用 API，跑 2 轮对话，其中包括一次子 agent，花费约 0.02 元。全部 ✅ 才算通过 L1–L5。

用没改过的起始代码跑，只有 L1 能通过：summary 等接口还没实现，会看到 `❌ L2+ 接口 /api/sessions/<id>/summary 返回 500` 之类的提示，脚本随即以非零退出码结束。这是正常的，实现完接口再跑。

## 你会踩的坑（提前告诉你）
1. **事件里没有 token 用量。** `step/end` 只有轮次和步数编号。用量只记录在会话日志 `$DSH_HOME/sessions/**/session.v4.jsonl(.zstd)` 里，每次请求对应一条 `assistant/message` 记录的 `usage` 字段（`inputTokens` 是**未命中缓存**的输入，`cacheReadTokens` 是命中的部分）。
2. **子 agent 的归属**：用 `subagent.started` 事件的 `parentSessionId` / `childSessionId` 建立父子关系；子 agent 的 `session.event` 带着它自己的 `sessionId`。
3. **工具调用配对**：`tool/call.data.callId` ↔ `tool/result.data.message.toolCallId`。
4. **前端依赖**（markdown 渲染等）请下载到 `static/` 本地引用，国内学员加载 CDN 很慢。

## 加做（任选，体现在报告里）
DSH 自带的 Web 工作台已经能显示基本轨迹，下面这些是它**没有**的功能：
- **上下文构成**：每次请求的输入里，系统提示、工具定义、历史消息、工具结果各占多少 token。
- **缓存命中曲线**：随步数变化的命中率；它在哪里下降，为什么。
- **两次运行对比**：同一任务换配置（例如 `reasoning_effort`）后，步数、token 和成本的差异。

## 提交物
提交到 `assignment1/` 目录下：
1. 代码，`check.py` 全部通过。
2. `WRITEUP.md`（1–2 页）：
   - 你的设计取舍：数据从哪里来、怎么保证实时、怎么处理断线续传；
   - **用你的工具分析一个真实任务**，例如让 agent 修复一个小 bug：贴截图，回答"成本主要花在哪里""缓存命中率为什么是这个数""子 agent 值不值"。
3. 3 分钟演示视频（可选）。

## 学术诚信
可以阅读 DSH 自带 Web 工作台的源码作为参考，但**不要复制它的前端代码**。评审看重的是你的设计取舍和分析，而不是界面好不好看。
