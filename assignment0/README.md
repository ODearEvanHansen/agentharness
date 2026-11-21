# 作业 0：环境自检

目标：确认你的机器能完成本课程的全部作业。预计 1–2 小时，大部分时间花在下载上。**第 1 周周末截止**，作业 1 要求先完成本作业。

> 本课程所有命令都在**仓库根目录**下执行：`git clone https://github.com/ODearEvanHansen/agentharness && cd agentharness`。

## 关卡 1：基础环境
1. 安装 Docker。Linux 用户安装 Docker Engine，并把当前用户加入 `docker` 组；Windows 用户安装 Docker Desktop 并启用 WSL2 后端，之后**所有操作都在 WSL2 里进行**。
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
source ~/.venvs/agentharness/bin/activate && set -a && . ~/.config/agentharness/env && set +a && python assignment0/selfcheck.py
```
所有 ❌ 都必须修好，⚠️ 按提示处理。常见问题：

| 现象 | 处理 |
|---|---|
| PyPI / Hugging Face 慢或不通 | pip 换国内源；Hugging Face 一般用不到（课程已把数据集随仓库分发），确实需要时设置 `HF_ENDPOINT=https://hf-mirror.com` |
| GHCR 不通或很慢 | 见 [infra/README.md](../infra/README.md) 的"国内访问"一节 |
| Docker Hub 不通 | **不能忽略**：运行器和出网代理镜像都从 Docker Hub 的基础镜像构建。请配置镜像加速，或拉取 `ghcr.io/odearevanhansen/agentharness-runner:0.1` 和 `ghcr.io/odearevanhansen/agentharness-egress:0.1` 后用 `docker tag` 改成本地名字，见 [infra/README.md](../infra/README.md) |
| `DEEPSEEK_API_KEY` 格式警告 | 官方 key 以 `sk-` 开头，检查是不是误复制了其他平台的 key |
| 内存 ⚠️（16–32GB） | 可以完成 A0–A3，以及 A4 的 8B 实验；A4 L3 和 A5 需要 32GB，A5 可以改用课程提供的本地基线数据 |
| macOS | 不支持，请使用 x86_64 Linux 云主机，或 Windows + WSL2 |

## 关卡 3：拉取评测镜像，跑通一道题的评测
课程已把 SWE-bench 评测镜像同步到 GHCR，拉取无需登录：`ghcr.io/odearevanhansen/swebench-x86_64:<实例>`。

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
3. 用官方评测工具验证"标准答案补丁"（gold patch）能通过测试，这一步会把整条评测链路跑一遍。第一次运行要准备评测环境，大约需要 5–10 分钟：
   ```bash
   python -m swebench.harness.run_evaluation -d infra/swebench/dataset.json -p gold \
     -i django__django-15467 -id a0-check
   ```
   输出里出现 `Instances resolved: 1` 就算通过。
4. 清理（可选）：`docker rmi ghcr.io/odearevanhansen/swebench-x86_64:django_1776_django-15467`。之后每道题的镜像都按需拉取，用完就删，100GB 磁盘就够用。

## 完成标准
在课程讨论区的"作业 0 打卡"帖里贴出以下内容：
- `selfcheck.py` 的完整输出（不要包含 key）；
- 关卡 3 第 2 步和第 3 步的输出；
- `infra/README.md` 中白名单三条验证的输出。
