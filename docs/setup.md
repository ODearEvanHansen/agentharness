# 环境搭建指南

这一页一步步带你装好课程需要的环境：**Docker + Python 虚拟环境 + DeepSeek API key**，最后用[作业 0](assignments/a0.md) 的自检脚本确认。只支持两种平台：

- **x86_64 Linux**（Ubuntu / Debian），看[第一部分](#一ubuntu--debian-原生安装)；
- **Windows 10/11 + WSL2**，看[第二部分](#二windows--wsl2)。**不支持 macOS**，Mac 用户请用一台 x86_64 Linux 云主机。

两种平台装好 Docker 之后，都接着做[第三部分](#三python-虚拟环境与-api-key)和[第四部分](#四验证清单)。

作业 3–5 和期末项目还需要本地模型服务（Ollama / llama.cpp）、花费统计脚本、provider 配置、插件加载和复现检查，见[本地模型与进阶工具](setup-local.md)。

!!! note "命令出处"
    下面的命令照抄自官方文档，每一节都给了链接。官方文档更新后如果和这里不一致，**以官方文档为准**，也欢迎[提 Issue](https://github.com/ODearEvanHansen/agentharness/issues/new/choose) 告诉我们。

## 一、Ubuntu / Debian 原生安装

### 1. 卸载冲突的旧包

发行版自带的 `docker.io` 等非官方包会和官方包冲突，先卸掉（提示一个都没装也没关系）。出处：[Install Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu/)。

```bash
sudo apt remove $(dpkg --get-selections docker.io docker-compose docker-compose-v2 docker-doc docker-buildx podman-docker containerd runc | cut -f1)
```

### 2. 添加 Docker 官方 apt 仓库并安装

Ubuntu（出处同上）：

```bash
# 添加 Docker 官方 GPG 公钥
sudo apt update
sudo apt install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# 添加 apt 软件源
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
sudo apt update

# 安装
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

**Debian**：把上面两处 `linux/ubuntu` 换成 `linux/debian`，`Suites:` 一行改成 `$(. /etc/os-release && echo "$VERSION_CODENAME")`。出处：[Install Docker Engine on Debian](https://docs.docker.com/engine/install/debian/)。

#### 国内：download.docker.com 慢或不通时

国内几个开源镜像站完整同步了 `download.docker.com` 的 `docker-ce` 目录（注意：它们**不是** Docker Hub 镜像，只解决"装 Docker"，不解决"拉镜像"）。把上面命令里的 `https://download.docker.com` 前缀（GPG 公钥地址和 `URIs:` 两处）整体替换成下面任意一个即可，其余不变：

| 镜像站 | 替换成 | 说明 |
|---|---|---|
| 清华 TUNA | `https://mirrors.tuna.tsinghua.edu.cn/docker-ce` | [使用帮助](https://mirrors.tuna.tsinghua.edu.cn/help/docker-ce/) |
| 中科大 USTC | `https://mirrors.ustc.edu.cn/docker-ce` | [使用帮助](https://mirrors.ustc.edu.cn/help/docker-ce.html) |
| 阿里云 | `https://mirrors.aliyun.com/docker-ce` | [镜像站](https://developer.aliyun.com/mirror/docker-ce) |

例如 GPG 公钥地址变成 `https://mirrors.tuna.tsinghua.edu.cn/docker-ce/linux/ubuntu/gpg`，`URIs:` 变成 `https://mirrors.tuna.tsinghua.edu.cn/docker-ce/linux/ubuntu`。镜像站分发的是同一把官方公钥，apt 仍会校验签名。

### 3. 安装后设置：免 sudo 使用 docker

出处：[Linux post-installation steps](https://docs.docker.com/engine/install/linux-postinstall/)。

```bash
sudo groupadd docker          # 提示组已存在就忽略
sudo usermod -aG docker $USER
newgrp docker                 # 或者注销后重新登录（虚拟机里可能需要重启）
```

!!! warning "docker 组等同 root"
    官方文档特别提醒：`docker` 组的成员拥有相当于 root 的权限。这台机器只给自己用时这样设置没问题；这也是课程坚持让 agent 跑在容器里、而不是把 Docker socket 交给 agent 的原因之一。

### 4. 验证 Docker

```bash
docker version                # Client 和 Server 两段都要有输出
docker run --rm hello-world   # 从 Docker Hub 拉一个测试镜像
```

**Docker Hub 不通时**（`hello-world` 卡住或报 `timeout`），换成从 GHCR 拉课程镜像来验证，它同时也是后面要用的运行器镜像：

```bash
docker pull ghcr.io/odearevanhansen/agentharness-runner:0.1
docker run --rm --network none ghcr.io/odearevanhansen/agentharness-runner:0.1 python3 --version
```

能打印出 Python 版本就说明 Docker 本身工作正常。Docker Hub 不通对课程的影响和处理办法见下一节。

### 5. Docker Hub 不通：镜像加速（registry mirror）的注意事项

运行器和出网代理镜像都从 Docker Hub 上的基础镜像构建，所以 Docker Hub 不通**不能忽略**。两种办法：

1. **推荐：直接用课程预构建的 GHCR 镜像**，改成本地名字即可，不依赖任何第三方加速服务，步骤见[基础设施](infra.md)的"Docker Hub 不通时"一节，或[常见问题](faq.md#docker-hub-不通怎么办)。
2. **配置镜像加速**：在 `/etc/docker/daemon.json` 写入 `registry-mirrors`，然后 `sudo systemctl restart docker`。格式见官方文档 [Registry mirror](https://docs.docker.com/docker-hub/image-library/mirror/)：

    ```json
    {
      "registry-mirrors": ["https://<你的加速地址>"]
    }
    ```

    注意：
    - `registry-mirrors` **只对 Docker Hub 生效**，对 `ghcr.io` 等其他仓库不起作用；
    - 国内公开的 Docker Hub 加速地址经常变动或停止服务，课程不推荐具体某一个；请使用你所在单位、云厂商（例如云主机自带的加速地址）或你自己信任的服务；
    - 加速服务能看到你拉取了哪些镜像，也理论上可以替换镜像内容，只用可信的来源；
    - 改完用 `docker info` 查看输出里的 `Registry Mirrors` 一项，确认已生效。

### 6. 需要代理时

如果你通过 HTTP 代理上网，要分清两处：

- **拉镜像**（`docker pull`）走的是 Docker 守护进程，在 shell 里 `export HTTPS_PROXY` 对它**无效**，要按 [Daemon proxy configuration](https://docs.docker.com/engine/daemon/proxy/) 配置守护进程的代理，然后重启 Docker；
- **`docker build` 里的 `pip install`** 走的是构建容器，需要 `--build-arg` 传入代理，或者用国内 PyPI 源（作业 0 已给出 `PIP_INDEX_URL` 写法）。

课程的出网代理容器本身不需要也不应该配置你的上网代理之外的东西；作业里 agent 只能访问 `api.deepseek.com`。

## 二、Windows + WSL2

### 1. 启用 WSL2 并安装 Ubuntu

在**管理员** PowerShell 里执行（出处：[Install WSL](https://learn.microsoft.com/en-us/windows/wsl/install)）：

```powershell
wsl --install
```

默认会启用 WSL2 并安装 Ubuntu，按提示重启电脑，再在 Ubuntu 窗口里设置 Linux 用户名和密码。已经装过 WSL 的，确认版本：

```powershell
wsl --update
wsl -l -v        # VERSION 一列必须是 2
```

**之后所有课程命令都在 WSL 的 Ubuntu 终端里执行**，仓库也要 clone 到 WSL 的 Linux 文件系统（例如 `~/agentharness`），不要放在 `/mnt/c/...` 下——跨文件系统访问很慢，权限也会出问题。

### 2. 调整 WSL2 内存和交换空间

WSL2 默认只分到 Windows 一部分内存，作业需要至少 16GB 的机器把大部分内存给 WSL。在 Windows 的 `%UserProfile%\.wslconfig`（例如 `C:\Users\你的用户名\.wslconfig`）写入（出处：[Advanced settings configuration in WSL](https://learn.microsoft.com/en-us/windows/wsl/wsl-config)）：

```ini
[wsl2]
memory=14GB
swap=8GB
```

这是 16GB 机器的建议值；32GB 机器可以写 `memory=28GB`。`memory` 不要超过物理内存减 2GB。保存后在 PowerShell 执行 `wsl --shutdown`，重新打开 WSL 终端，用 `free -g` 确认。

### 3. 安装 Docker：两种方式任选其一

| | **A. WSL 里直接装 Docker Engine（推荐）** | B. Docker Desktop + WSL 集成 |
|---|---|---|
| 安装 | 和 Linux 完全一样，照[第一部分](#一ubuntu--debian-原生安装)做 | 安装 Windows 版 Docker Desktop，启用 WSL2 后端 |
| 许可 | 开源，免费 | 大型企业（员工超过 250 人或年收入超过 1000 万美元）商用需付费订阅，见 [Docker Desktop license agreement](https://docs.docker.com/subscription/desktop-license/)；个人学习免费 |
| 资源 | 只有一个 WSL 发行版，内存全按 `.wslconfig` 分配 | 额外运行一个 `docker-desktop` 发行版和 Windows 端程序，占用更多内存 |
| 镜像存储 | 在 Ubuntu 发行版的虚拟磁盘里 | 在 Docker Desktop 自己的虚拟磁盘里 |
| 前提 | WSL 需开启 systemd（下面第 4 步） | 无 |
| 适合 | 想让命令与课程文档、Linux 用户完全一致 | 已经在用 Docker Desktop，或更习惯图形界面 |

我们推荐 **A**：命令和 Linux 用户完全一致，排错时少一层，也没有许可问题。两种方式**不要同时用**——装了 Docker Desktop 并开启了 WSL 集成后，再在同一发行版里装 Docker Engine，会出现两个 `docker` 互相抢的情况。

#### 方式 A：在 WSL 里安装 Docker Engine

先确认 systemd 已开启（Docker Engine 由 systemd 启动）。出处：[Use systemd to manage Linux services with WSL](https://learn.microsoft.com/en-us/windows/wsl/systemd)。用 `wsl --install` 新装的 Ubuntu 默认已开启；检查：

```bash
cat /etc/wsl.conf
```

如果没有下面两行，用 `sudo nano /etc/wsl.conf` 加上：

```ini
[boot]
systemd=true
```

然后在 PowerShell 执行 `wsl --shutdown`，重新打开 Ubuntu，`systemctl status` 能显示 running 即可。微软文档要求 WSL 版本不低于 0.67.6（`wsl --version` 查看，旧了就 `wsl --update`）。

接着**照[第一部分](#一ubuntu--debian-原生安装)第 1–6 步**安装和验证 Docker Engine。

#### 方式 B：Docker Desktop

按 [Docker Desktop WSL 2 backend](https://docs.docker.com/desktop/features/wsl/) 安装：安装时勾选使用 WSL 2，装好后在 Settings → Resources → WSL integration 里**打开你的 Ubuntu 发行版**。然后在 WSL 终端里执行[第一部分第 4 步](#4-验证-docker)的验证命令。不要在 WSL 里再执行第一部分的 apt 安装。

### 4. 磁盘位置

课程需要约 100GB 磁盘（每个 SWE-bench 评测镜像约 3GB）。

- **方式 A**：镜像存在 Ubuntu 发行版的虚拟磁盘（`ext4.vhdx`）里，默认在 C 盘。C 盘不够时，可以用 `wsl --export` 把发行版导出，再用 `wsl --import` 导入到空间大的盘，见 [Basic commands for WSL](https://learn.microsoft.com/en-us/windows/wsl/basic-commands)。
- **方式 B**：位置在 Docker Desktop → Settings → Resources → Advanced → Disk image location，C 盘不够就改到大盘。

## 三、Python 虚拟环境与 API key

以下与[作业 0](assignments/a0.md) 关卡 1 完全一致，Linux 和 WSL 里都一样。

```bash
# 1. 克隆仓库（以后所有命令都在仓库根目录执行）
git clone https://github.com/ODearEvanHansen/agentharness && cd agentharness

# 2. 虚拟环境（Python ≥ 3.10；Ubuntu 上缺 venv 模块时先 sudo apt install python3-venv）
python3 -m venv ~/.venvs/agentharness && source ~/.venvs/agentharness/bin/activate
pip install deepseek-harness-sdk==0.2.2rc2 swebench==5.0.2 zstandard   # 国内可加 -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3. API key：为本课程单独新建一个 key，只充少量金额
mkdir -p ~/.config/agentharness
printf 'export DEEPSEEK_API_KEY=%s\n' 'sk-...' > ~/.config/agentharness/env   # 换成你的 key
chmod 600 ~/.config/agentharness/env
```

key 文件放在仓库**之外**：作业容器会把仓库挂载成可写目录，所以不要在仓库里放 `.env`，也不要写进 `~/.bashrc`。每次开新终端：

```bash
source ~/.venvs/agentharness/bin/activate && set -a && . ~/.config/agentharness/env && set +a
```

## 四、验证清单

按顺序逐项打勾，全部通过再进入作业 0 的后续关卡：

- [ ] `uname -m` 输出 `x86_64`
- [ ] `free -g` 的 total 不少于 14（WSL2 下取决于 `.wslconfig`）
- [ ] `df -h ~` 剩余空间不少于 100GB（方式 B 看 Docker Desktop 的磁盘位置）
- [ ] `docker version` 有 Client 和 Server 两段，且**不需要 sudo**
- [ ] `docker run --rm hello-world` 成功，或 Docker Hub 不通时 GHCR 运行器镜像能运行（[第一部分第 4 步](#4-验证-docker)）
- [ ] `python --version` ≥ 3.10，且 `which python` 指向 `~/.venvs/agentharness/`
- [ ] `ls -l ~/.config/agentharness/env` 显示 `-rw-------`
- [ ] 按 [infra/README.md](infra.md) 搭好 `agentharness-net`、出网代理和运行器，三条验证都通过
- [ ] 最后运行作业 0 自检，所有 ❌ 都修好：

```bash
python assignment0/selfcheck.py
```

## 五、常见问题排查

| 现象 | 原因 | 处理 |
|---|---|---|
| `permission denied while trying to connect to the Docker daemon socket` | 当前用户不在 `docker` 组，或加组后没重新登录 | 执行第一部分第 3 步，然后 `newgrp docker` 或注销重登；WSL 里可以 `wsl --shutdown` 后重开 |
| `WARNING: Error loading config file: ~/.docker/config.json ... permission denied` | 之前用 `sudo docker` 跑过 | 按[官方文档](https://docs.docker.com/engine/install/linux-postinstall/)执行 `sudo chown "$USER":"$USER" ~/.docker -R` |
| WSL 里 `Cannot connect to the Docker daemon` | 方式 A：systemd 没开或 Docker 没启动；方式 B：Docker Desktop 没运行或没开 WSL 集成 | A：检查 `/etc/wsl.conf`，`sudo systemctl start docker`；B：启动 Docker Desktop，检查 WSL integration |
| selfcheck 内存 ⚠️，或容器被 OOM 杀掉 | WSL2 默认内存不够 | 写 `.wslconfig`（第二部分第 2 步）后 `wsl --shutdown` |
| `docker pull` / `hello-world` 超时，`registry-1.docker.io` 连不上 | Docker Hub 在国内不稳定 | 改用 GHCR 课程镜像（[常见问题](faq.md#docker-hub-不通怎么办)），或配置可信的镜像加速 |
| 设置了 `HTTPS_PROXY` 但 `docker pull` 仍不走代理 | shell 的环境变量对 Docker 守护进程无效 | 按 [Daemon proxy configuration](https://docs.docker.com/engine/daemon/proxy/) 配置守护进程代理 |
| `apt update` 访问 `download.docker.com` 失败 | 网络问题 | 换成清华 / 中科大 / 阿里云镜像（第一部分第 2 步） |
| `no space left on device` | 评测镜像每个约 3GB，越积越多 | `docker system df` 查看占用，`docker image prune` 清理不用的镜像；SWE-bench 镜像按题拉取、用完删除；WSL 用户检查虚拟磁盘所在盘 |
| pip 安装很慢或超时 | PyPI 访问慢 | 加 `-i https://pypi.tuna.tsinghua.edu.cn/simple` |

其他问题见[常见问题](faq.md)，或到 [Discussions 的 Q&A](https://github.com/ODearEvanHansen/agentharness/discussions/new?category=q-a) 提问（贴日志前先检查里面有没有 API key）。
