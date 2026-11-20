# 作业 0：环境自检

目标：确认你的机器能完成本课程的全部作业。预计 1–2 小时，大部分时间花在下载上。

## 关卡 1：基础环境
1. 安装 Docker。Linux 用户安装 Docker Engine，并把当前用户加入 `docker` 组；Windows 用户安装 Docker Desktop 并启用 WSL2 后端，之后**所有操作都在 WSL2 里进行**。
2. 安装 Python ≥ 3.10，再安装课程锁定版本的 DSH SDK：
   ```bash
   python3 -m venv ~/.venvs/agentharness && source ~/.venvs/agentharness/bin/activate
   pip install deepseek-harness-sdk==0.2.2rc2      # 国内可加 -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```
3. 在 [platform.deepseek.com](https://platform.deepseek.com/) 创建 API key，充值少量金额，建议同时设置消费上限。然后：
   ```bash
   export DEEPSEEK_API_KEY=...        # 写进 ~/.bashrc 也行，但千万不要提交进任何 git 仓库
   ```

## 关卡 2：运行自检
```bash
python3 assignment0/selfcheck.py
```
所有 ❌ 项必须修好，⚠️ 项按提示处理。常见问题：

| 现象 | 处理 |
|---|---|
| Docker Hub / PyPI / Hugging Face 慢或不通 | Docker 配置 `registry-mirrors`；pip 换国内源；设置 `HF_ENDPOINT=https://hf-mirror.com` |
| `DEEPSEEK_API_KEY` 格式警告 | 官方 key 以 `sk-` 开头，检查是不是复制成了其他平台的 key |
| macOS | 不支持，请使用 x86_64 Linux 云主机或 Windows + WSL2 |

## 关卡 3：拉取评测镜像并跑一道题的测试
课程把 SWE-bench 评测镜像同步到了 GHCR（无需登录）：`ghcr.io/odearevanhansen/swebench-x86_64:<实例>`。

1. 拉取示例镜像（约 3GB）：
   ```bash
   docker pull ghcr.io/odearevanhansen/swebench-x86_64:django_1776_django-15467
   ```
2. 在**断网**容器里确认环境可用：仓库位于 `/testbed`，Python 环境名为 `testbed`。
   ```bash
   docker run --rm --network none --cpus 2 --memory 4g \
     ghcr.io/odearevanhansen/swebench-x86_64:django_1776_django-15467 \
     bash -lc 'source /opt/miniconda3/bin/activate testbed && cd /testbed && git log --oneline -1 && python -c "import django; print(django.get_version())"'
   ```
   能打印出一条 commit 和 Django 版本号，就算通过。
3. （可选）用官方评测工具验证"金标准补丁"能通过测试。这一步会测通整条评测链路：
   ```bash
   pip install swebench
   python infra/swebench/make_dataset_cn.py --instances <(echo django__django-15467) --out /tmp/one.json
   python -m swebench.harness.run_evaluation -d /tmp/one.json -p gold -id a0-check
   ```
   输出中出现 `Instances resolved: 1` 即为通过。

## 完成标准
在课程讨论区的"作业 0 打卡"帖里贴出：
- `selfcheck.py` 的完整输出（不要包含 key）；
- 关卡 3 第 2 步的输出。
