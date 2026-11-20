# 作业 0：环境自检

目标：确认你的机器能完成本课程的全部作业。预计 1–2 小时，大部分时间花在下载上。

## 关卡 1：基础环境
1. 安装 Docker。Linux 安装 Docker Engine 并把当前用户加入 `docker` 组；Windows 安装 Docker Desktop 并启用 WSL2 后端，之后**所有操作都在 WSL2 里进行**。
2. 安装 Python ≥ 3.10，然后安装课程锁定版本的 DSH SDK：
   ```bash
   python3 -m venv ~/.venvs/agentharness && source ~/.venvs/agentharness/bin/activate
   pip install deepseek-harness-sdk==0.2.2rc2      # 国内可加 -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```
3. 在 [platform.deepseek.com](https://platform.deepseek.com/) 创建 API key，充值少量金额，并建议设置消费上限。然后在终端里设置：
   ```bash
   export DEEPSEEK_API_KEY=...        # 写进 ~/.bashrc 也可以，但千万不要提交进任何 git 仓库
   ```

## 关卡 2：运行自检
```bash
python3 assignment0/selfcheck.py
```
所有 ❌ 项都必须修好，⚠️ 项按提示处理。常见问题：

| 现象 | 处理 |
|---|---|
| Docker Hub / PyPI / Hugging Face 访问慢或不通 | Docker 配置 `registry-mirrors`；pip 改用国内源；设置 `HF_ENDPOINT=https://hf-mirror.com` |
| `DEEPSEEK_API_KEY` 格式警告 | 官方 key 以 `sk-` 开头，检查是不是复制成了其他平台的 key |
| macOS | 本课程不支持，请使用 x86_64 Linux 云主机或 Windows + WSL2 |

## 关卡 3：拉取一个评测镜像（即将开放）
课程把 SWE-bench 评测镜像同步到了国内镜像仓库，学员无需登录即可拉取。镜像同步完成后，这里会补上具体命令，并提供 1 道示例题的跑通步骤。

## 完成标准
把 `selfcheck.py` 的完整输出（不包含 key）贴到课程讨论区的"作业 0 打卡"帖。
