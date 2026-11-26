# 作业 0：环境自检

目标：确认你的机器能完成本课程的全部作业。预计 1–2 小时，大部分时间花在下载上。**第 1 周周末截止**，作业 1 要求先完成本作业。

**只支持 x86_64 Linux 和 Windows + WSL2，不支持 macOS**（Mac 用户见[环境搭建指南](../docs/setup.md)的“Mac 用户怎么办”）。不确定自己的机器行不行，可以先跑 `python3 assignment0/selfcheck.py`：它只检查、不安装，第一行就告诉你操作系统是否支持。

## 先认识几个词

| 词 | 意思 |
|---|---|
| 运行器（runner） | 课程的 Docker 镜像 `agentharness-runner:0.1`，agent 都在它里面跑 |
| `agentharness-net` | 一个 internal（不能直接上网）的 Docker 网络，agent 容器只接这个网络 |
| 出网代理（egress） | 唯一能上网的小容器，只放行 `api.deepseek.com` |
| SWE-bench 评测镜像 | 每道题一个镜像，里面装好了题目仓库和测试环境 |
| gold patch | 题目自带的标准答案补丁，用来检查评测链路是否正常 |

```text
宿主机（你的电脑）
 └─ agentharness-net（internal，不能直接上网）
      ├─ agent 容器（运行器）──HTTP 代理──┐
      └─ 出网代理 egress  ◄───────────────┘
            └─► 只放行 api.deepseek.com，其他地址一律拒绝
```

> 本课程所有命令都在**仓库根目录**下执行：`git clone https://github.com/ODearEvanHansen/agentharness && cd agentharness`。

## 关卡 1：基础环境

> 第一次装 Docker / WSL2？先按[环境搭建指南](https://odearevanhansen.github.io/agentharness/setup/)（仓库内 [docs/setup.md](../docs/setup.md)）一步步做，包括国内镜像源、WSL2 内存设置和常见报错。

1. 安装 Docker。Linux 用户安装 Docker Engine，并把当前用户加入 `docker` 组；Windows 用户在 WSL2 里安装 Docker Engine（推荐）或使用 Docker Desktop 的 WSL2 后端（两种方式的取舍见环境搭建指南），之后**所有操作都在 WSL2 里进行**。
   - **WSL2 用户先调内存**：WSL2 默认只分到部分内存。在 Windows 的 `%UserProfile%\.wslconfig` 写入下面三行，再在 PowerShell 执行 `wsl --shutdown`，重新打开 WSL 终端：
     ```ini
     [wsl2]
     memory=14GB
     swap=8GB
     ```
   - **WSL2 用户检查磁盘**：Docker Desktop 的镜像存在它的虚拟磁盘里，位置在 Docker Desktop → Settings → Resources → Advanced → Disk image location。课程需要约 100GB，C 盘不够就把它改到空间大的盘。
2. 安装 Python ≥ 3.10，以及课程锁定版本的依赖：
   ```bash
   python3 -m venv ~/.venvs/agentharness && source ~/.venvs/agentharness/bin/activate
   pip install deepseek-harness-sdk==0.2.2rc2 swebench==5.0.2 zstandard   # 国内可加 -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```
3. **为本课程单独创建一个 API key**：在 [platform.deepseek.com](https://platform.deepseek.com/) 新建 key，只充值少量金额，课程结束后删除。原因是 agent 在容器里运行不可信代码时能读到这个 key。然后执行：
   ```bash
   mkdir -p ~/.config/agentharness
   printf 'export DEEPSEEK_API_KEY=%s\n' 'sk-...' > ~/.config/agentharness/env   # 换成你的 key
   chmod 600 ~/.config/agentharness/env
   source ~/.config/agentharness/env   # 每次开新终端时执行
   ```
   key 放在仓库**之外**：作业容器会把仓库挂载成可写目录，agent 能读写仓库里的任何文件，所以不要在仓库根目录放 `.env`；也不要写进 `~/.bashrc`（很多工具会读取或打印它）。千万不要提交到任何 git 仓库。
4. 搭建隔离网络并构建运行器镜像，详见 [infra/README.md](../infra/README.md)。共四条 `docker` 命令，再加一条 `docker build`。两个镜像都基于 Docker Hub 上的基础镜像构建：Docker Hub 不通时，要么给 Docker 配置镜像加速（registry mirror），要么直接拉课程预构建的镜像再改成本地名字（见 infra/README.md 的"Docker Hub 不通时"一节）。PyPI 慢时，构建运行器可以加 `--build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple`。之后的作业都会用到它们，**请按 README 里的三条验证逐一确认**。

## 关卡 2：运行自检
新开的终端要先激活虚拟环境、载入 key，再运行：
```bash
source ~/.venvs/agentharness/bin/activate && source ~/.config/agentharness/env && python assignment0/selfcheck.py
```
所有 ❌ 都必须修好，⚠️ 按提示处理。常见问题：

| 现象 | 处理 |
|---|---|
| PyPI / Hugging Face 慢或不通 | pip 换国内源；Hugging Face 一般用不到（课程已把数据集随仓库分发），确实需要时设置 `HF_ENDPOINT=https://hf-mirror.com` |
| GHCR 不通或很慢 | 见 [infra/README.md](../infra/README.md) “SWE-bench 评测镜像”一节里的“国内访问”一条 |
| Docker Hub 不通 | **不能忽略**：运行器和出网代理镜像都从 Docker Hub 的基础镜像构建。请配置镜像加速，或拉取 `ghcr.io/odearevanhansen/agentharness-runner:0.1` 和 `ghcr.io/odearevanhansen/agentharness-egress:0.1` 后用 `docker tag` 改成本地名字，见 [infra/README.md](../infra/README.md) |
| `DEEPSEEK_API_KEY` 格式警告 | 官方 key 以 `sk-` 开头，检查是不是误复制了其他平台的 key |
| 内存 ⚠️（WSL2 下不足 16GB） | 按关卡 1 写 `.wslconfig` 并 `wsl --shutdown` |
| 内存 ⚠️（16–32GB） | 可以完成 A0–A3，以及 A4 的 8B 实验；A4 L3 和 A5 需要 32GB，A5 走小内存路线（Qwen3-4B）亲手完成 |
| macOS | 不支持，请使用 x86_64 Linux 云主机，或 Windows + WSL2 |

## 选做：第一次调用（5 分钟）
关卡 2 通过后，可以先体验一下 agent 循环。下面是第 2 讲那个最小循环的简化版：只用标准库，模型唯一能用的工具是做加法，**不会执行任何命令**，所以直接在宿主机上跑就行。存成仓库外的 `~/first_call.py`，然后 `python3 ~/first_call.py`：

```python
import json, os, urllib.request
def chat(messages):
    body = {"model": "deepseek-flash", "messages": messages, "tools": [{"type": "function", "function": {
        "name": "add", "description": "两个整数相加", "parameters": {"type": "object",
        "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}}, "required": ["a", "b"]}}}]}
    req = urllib.request.Request("https://api.deepseek.com/chat/completions", json.dumps(body).encode(),
        {"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["DEEPSEEK_API_KEY"]})
    return json.load(urllib.request.urlopen(req, timeout=120))
messages, cny = [{"role": "user", "content": "用 add 工具算 1234+5678，再用一句话告诉我结果"}], 0.0
for step in range(5):
    r = chat(messages); u = r["usage"]; msg = r["choices"][0]["message"]
    cny += (u.get("prompt_cache_hit_tokens", 0) * 0.04 + u.get("prompt_cache_miss_tokens", 0) * 2
            + u["completion_tokens"] * 8) / 1e6             # 高峰价（元 / 百万 token），与 tools/usage_cost.py 一致
    messages.append(msg)
    if not msg.get("tool_calls"):
        print("回复：", msg["content"]); break
    for c in msg["tool_calls"]:
        a = json.loads(c["function"]["arguments"])
        messages.append({"role": "tool", "tool_call_id": c["id"], "content": str(a["a"] + a["b"])})
print(f"共 {step + 1} 次请求，花费约 {cny:.4f} 元")
```

正常会看到两次请求：第一次模型调用 `add`，第二次给出答案 6912，花费不到 0.01 元。这就是 agent 的全部骨架：请求、执行工具、把结果放回历史、再请求。

## 关卡 3：拉取评测镜像，跑通一道题的评测
课程已把 SWE-bench 评测镜像同步到 GHCR，拉取无需登录：`ghcr.io/odearevanhansen/swebench-x86_64:<实例>`。仓库里的 `infra/swebench/dataset.json` 已经指向这些 GHCR 镜像，不用自己改。

1. 拉取示例镜像（约 3GB）：
   ```bash
   docker pull ghcr.io/odearevanhansen/swebench-x86_64:django_1776_django-15467
   ```
2. 在**断网**容器里确认环境可用。仓库位于 `/testbed`，Python 环境名为 `testbed`：
   ```bash
   docker run --rm --network none --cpus 2 --memory 4g \
     ghcr.io/odearevanhansen/swebench-x86_64:django_1776_django-15467 \
     bash -lc 'source /opt/miniconda3/bin/activate testbed && cd /testbed && git log --oneline -1 && python -c "import django; print(django.get_version())"'
   ```
   能打印出一条 commit 和 Django 版本号，就算通过。
3. 用官方评测工具验证"标准答案补丁"（gold patch）能通过测试。gold patch 是题目自带的正确修改，一定能让测试通过；用它跑一遍，如果没通过，问题就出在你的环境（镜像、Docker、磁盘），而不是答案。以后 agent 没解出题时，你就能先排除环境原因。这一步会把整条评测链路跑一遍。第一次运行要准备评测环境，大约需要 5–10 分钟：
   ```bash
   python -m swebench.harness.run_evaluation -d infra/swebench/dataset.json -p gold \
     -i django__django-15467 -id a0-check
   ```
   输出里出现 `Instances resolved: 1` 就算通过。
   没通过时，先看日志 `logs/run_evaluation/a0-check/gold/django__django-15467/run_instance.log`（测试输出在同目录的 `test_output.txt`）：

   | 现象 | 处理 |
   |---|---|
   | 拉取镜像超时 | 先单独 `docker pull` 第 1 步的镜像；GHCR 慢见 [infra/README.md](../infra/README.md) “SWE-bench 评测镜像”一节里的“国内访问”一条 |
   | 找不到镜像（not found / manifest unknown） | 确认用的是仓库里的 `infra/swebench/dataset.json`，并且机器是 x86_64 |
   | `Instances resolved: 0` | 打开 `test_output.txt` 看哪条测试失败；常见原因是内存不足或上次中断留下的同名容器，用 `docker ps -a` 找到并删掉后重跑 |
   | 磁盘满（no space left on device） | `docker system df` 查看占用，用 `docker image prune` 清理不用的镜像；WSL2 用户检查 Docker Desktop 的磁盘位置（见关卡 1） |

4. 清理（可选）：`docker rmi ghcr.io/odearevanhansen/swebench-x86_64:django_1776_django-15467`。之后每道题的镜像都按需拉取，用完就删，100GB 磁盘就够用。

## 完成标准
到 [Discussions 的 Show and tell 分类](https://github.com/ODearEvanHansen/agentharness/discussions/new?category=show-and-tell&title=%E4%BD%9C%E4%B8%9A%200%20%E6%89%93%E5%8D%A1)发一个标题为“作业 0 打卡”的帖子，贴出以下内容（有问题请发到 [Q&A 分类](https://github.com/ODearEvanHansen/agentharness/discussions/new?category=q-a)）：
- `selfcheck.py` 的完整输出（不要包含 key；新版本不再打印余额数字）；
- 关卡 3 第 2 步和第 3 步的输出；
- `infra/README.md` 中白名单三条验证的输出。
