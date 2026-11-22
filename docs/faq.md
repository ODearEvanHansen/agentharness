# 常见问题

遇到问题先查这里和对应作业的 README。仍然解决不了：学习问题请到 [Discussions 的 Q&A](https://github.com/ODearEvanHansen/agentharness/discussions/new?category=q-a) 提问；脚本跑不通、内容有错请[提 Issue](https://github.com/ODearEvanHansen/agentharness/issues/new/choose)。不要贴 API key。

## Windows / macOS 能做吗？

Windows 可以：安装 Docker Desktop 并启用 WSL2 后端，之后**所有操作都在 WSL2 里进行**。macOS 不支持，请使用 x86_64 Linux 云主机，或 Windows + WSL2（见作业 0）。

### WSL2 内存和磁盘

WSL2 默认只分到 Windows 一部分内存，`selfcheck.py` 可能报内存不足 16GB。在 Windows 的 `%UserProfile%\.wslconfig` 写入：

```ini
[wsl2]
memory=14GB
swap=8GB
```

然后在 PowerShell 执行 `wsl --shutdown`，重新打开 WSL 终端。`memory` 不要超过 Windows 物理内存减 2GB。

Docker Desktop 的镜像都放在它的虚拟磁盘里（Docker Desktop → Settings → Resources → Advanced → Disk image location）。课程需要约 100GB，C 盘不够时把这个位置改到空间大的盘。

### 作业 1 的网页在 Windows 浏览器打不开

推荐用作业 1 README 里的端口转发小容器。打不开时按顺序排查：

1. **先在 WSL 里**执行 `curl -s 127.0.0.1:8765/ | head`。这里不通，问题在容器或转发容器，查 `docker ps` 和转发容器的日志。
2. WSL 里通、Windows 浏览器不通：确认 Docker Desktop → Settings → Resources → WSL integration 里启用了你的发行版。
3. 仍然不通：在 PowerShell 执行 `wsl hostname -I`，用输出的第一个 IP 打开 `http://<IP>:8765`。

## Docker Hub 不通怎么办？

**不能忽略**：运行器和出网代理镜像都从 Docker Hub 的基础镜像构建。两种办法任选一种：给 Docker 配置镜像加速（registry mirror）；或者直接拉课程预构建的 GHCR 镜像，再改成本地名字：

```bash
docker pull ghcr.io/odearevanhansen/agentharness-runner:0.1
docker pull ghcr.io/odearevanhansen/agentharness-egress:0.1
docker tag ghcr.io/odearevanhansen/agentharness-runner:0.1 agentharness-runner:0.1
docker tag ghcr.io/odearevanhansen/agentharness-egress:0.1 agentharness-egress:0.1
```

SWE-bench 评测镜像也已同步到 GHCR（`ghcr.io/odearevanhansen/swebench-x86_64:<实例>`），拉取无需登录。PyPI 慢时，构建运行器可以加 `--build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple`。详见[基础设施](infra.md)。

## 仓库里出现删不掉的 root 文件 / 报 EACCES

运行容器时漏了 `-u "$(id -u):$(id -g)" -e HOME=/tmp`。不加的话 agent 在仓库里创建的文件和目录归 root 所有，宿主机上删不掉，后续运行会报 EACCES。所有作业的容器运行命令都要带上这两个参数。

## 怎么查看花了多少钱？

- 课程脚本按 DeepSeek 官方**高峰价**计价：`tools/usage_cost.py <dsh_home> [model] [peak|offpeak]` 读取 DSH 会话日志（包括 `.zstd`），统计 token 和成本；作业 2/3 的运行记录里每题都有 `cny` 字段（单位元），`assignment3/score.py` 会汇总出 `cny_total` 和 `cny_per_task`。价格表见 `tools/usage_cost.py` 里的 `PRICES`，取自 [DeepSeek 官方人民币价格页](https://api-docs.deepseek.com/zh-cn/quick_start/pricing)。
- 实际扣费以 [DeepSeek 开放平台](https://platform.deepseek.com/)上的账户余额为准。
- 作业 3 参考：小题 8 道约 0.07 元，效率赛道 20 题约 2.7 元，难题集 20 题约 5.3 元。**先在小题上调试，跑通后再上 20 题。**

## API key 怎么放才安全？

- **为本课程单独创建一个 key，只充值少量余额，课程结束后删除。** 容器里的 agent 能拿到 key，出网白名单防不住它通过 `api.deepseek.com` 本身把数据发出去。
- key 放在仓库**之外**：`~/.config/agentharness/env`，权限 600。作业容器把仓库挂载成可写目录，所以不要在仓库根目录放 `.env`；也不要写进 `~/.bashrc`。千万不要提交到任何 git 仓库，提 Issue、贴日志时也要检查。
- 本地模型服务一定要加 `--api-key "$LOCAL_LLM_KEY"`，否则同一网络里的任何容器都能调用它。

## 为什么小题（或作业 1 的 app.py）拒绝运行？

小题会执行模型生成的 shell 命令；作业 1 的 agent 以 `danger-full-access` 权限运行，能执行任意 shell 命令。隔离全靠容器，所以不在运行器容器里时，运行器 / `app.py` 会拒绝执行。请按作业 README 里的写法（接入 `agentharness-net`、使用 `agentharness-runner:0.1` 镜像）在容器里运行。检查脚本（如 `check.py`）则在宿主机上运行。

## Qwen3 返回的 content 是空字符串

Qwen3 默认先思考。`max_tokens` 设得太小（例如 20）时，思考内容会把额度用光，`content` 返回空字符串，思考内容在 `reasoning` 字段里。把 `max_tokens` 调大再试。

## 本地模型服务"起来了"，但请求还是走了云端

判断就绪要看健康检查或日志，**不要只看进程在不在**。llama.cpp 要等 `docker logs -f agentharness-llm` 里出现 `listening on http://0.0.0.0:8091` 才算就绪。课程团队踩过这个坑：脚本用 `pgrep` 判断服务已经起来，结果匹配到的是脚本自己的命令行，本地服务其实没启动，6 道题全部退回到云端完成。

另外，agent 容器要设置 `NO_PROXY=<模型容器名>`，否则请求会被发给出网代理并被拒绝。

## 排行榜怎么提交？

用 `assignment3/score.py` 生成 `leaderboard/<昵称>-<赛道>.json`（赛道为 `accuracy` 或 `efficiency`），连同 `assignment3/submission/<昵称>/` 一起发 PR。PR 会自动运行 `scripts/validate_leaderboard.py` 校验：字段完整、文件名合规、效率赛道解决数 ≥ 17、带 `config_sha`、不修改 `baseline-*.json`。提交前可以先在本地运行 `python scripts/validate_leaderboard.py leaderboard/*.json`。
