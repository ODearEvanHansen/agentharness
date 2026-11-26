# infra：课程基础设施

**本仓库的所有命令都在仓库根目录执行。**

| 文件 | 用途 |
|---|---|
| `course.patch.yml` | DSH 课程配置补丁，默认**关闭会话日志上传**（`session-log-deepseek.enabled: false`）。课程脚本会自动加载它；你自己用 SDK 时，通过 `patches=("/abs/path/course.patch.yml",)` 加载 |
| `egress/` | 出网白名单代理（tinyproxy），只放行 `api.deepseek.com`。作业容器接入 `--internal` 网络，并把 `HTTPS_PROXY` 指向这个代理 |
| `runner/` | 课程运行器镜像：Python 3.12 加课程锁定版本的 DSH SDK。A1 的 DSH-Lens、A2 和 A5 的小题都在这个镜像里运行 |
| `swebench/` | `instances.txt`（原 20 题）和 `instances_hard.txt`（难题集 20 题），以及对应的数据集 `dataset.json` / `dataset_hard.json`。数据集里的镜像地址已经改为 GHCR，可以直接交给官方评测，**不需要访问 Hugging Face**。另外还有 `make_dataset_cn.py`（为其他题目生成同样格式的 JSON）和 `pick_subset.py`（分层抽样，固定随机种子） |

## 隔离网络与出网白名单
```bash
docker build -t agentharness-egress:0.1 infra/egress
docker network create --internal agentharness-net
docker run -d --name agentharness-egress agentharness-egress:0.1
docker network connect agentharness-net agentharness-egress
```
**先完成下面“运行器镜像”一节的构建（或按“Docker Hub 不通时”拉取预构建镜像）**，再在隔离网络里的容器内验证（用运行器镜像，下面整段可直接复制），三条都必须满足：
```bash
docker run --rm --network agentharness-net -e HTTPS_PROXY=http://agentharness-egress:8888 \
  agentharness-runner:0.1 sh -c '
    echo "1) deepseek: HTTP $(curl -s -o /dev/null -w "%{http_code}" https://api.deepseek.com/)"
    curl -s -o /dev/null --max-time 15 https://github.com/; echo "2) github: rc=$?"
    curl -s -o /dev/null --max-time 15 --noproxy "*" https://example.com/; echo "3) noproxy example.com: rc=$?"'
```
预期输出：
```
1) deepseek: HTTP 401
2) github: rc=56        # 只要不是 0 就对（代理拒绝，常见 56 或 22）
3) noproxy example.com: rc=6   # 不是 0 就对；6 表示隔离网络里连 DNS 都解析不了
```
1. 返回 401：说明通过代理已经连通，只是请求没带 key。
2. github 的 rc ≠ 0：代理拒绝了白名单以外的域名。
3. rc ≠ 0（通常是 6）：说明网络本身是 `--internal`，绕过代理也出不去。**如果这一条 rc=0，白名单就形同虚设。**

白名单有一种情况**防不住**：容器里的 agent 能拿到你的 API key，它可以通过 `api.deepseek.com` 本身把数据发出去，比如发到攻击者自己的 DeepSeek 账号。所以请**为本课程单独创建一个 key，只充值少量余额，课程结束后删除**。

## Docker Hub 不通时
运行器和出网代理镜像都从 Docker Hub 上的基础镜像构建，Docker Hub 不通就构建不了。两种办法任选一种：
1. 给 Docker 配置镜像加速（`/etc/docker/daemon.json` 的 `registry-mirrors`），然后照常构建；
2. 直接拉课程预构建的镜像，改成本地名字，跳过两条 `docker build`：
   ```bash
   docker pull ghcr.io/odearevanhansen/agentharness-runner:0.1
   docker pull ghcr.io/odearevanhansen/agentharness-egress:0.1
   docker tag ghcr.io/odearevanhansen/agentharness-runner:0.1 agentharness-runner:0.1
   docker tag ghcr.io/odearevanhansen/agentharness-egress:0.1 agentharness-egress:0.1
   ```
PyPI 慢时，构建运行器可以换源：`docker build --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple -t agentharness-runner:0.1 infra/runner`。

## 运行器镜像
```bash
docker build -t agentharness-runner:0.1 infra/runner        # 需要正常网络，只构建一次
# 之后在隔离网络中运行，以作业 2 的小题为例：
docker run --rm -it --cpus 4 --memory 8g --network agentharness-net \
  -e HTTPS_PROXY=http://agentharness-egress:8888 -e DEEPSEEK_API_KEY \
  -u "$(id -u):$(id -g)" -e HOME=/tmp -v "$PWD":/work agentharness-runner:0.1 python assignment2/run.py --agent miniloop --suite mini
```
`-u "$(id -u):$(id -g)" -e HOME=/tmp` 让容器以你的用户身份运行，否则 agent 在仓库里创建的文件和目录归 root 所有，宿主机上删不掉、后续运行会报 EACCES。`-v "$PWD":/work` 让 agent 能写整个仓库：检查脚本请在宿主机上运行，key 不要放在仓库里（放在 `~/.config/agentharness/env`，权限 600，见作业 0）。

## 本地模型服务（接入隔离网络）
作业 4 L1/L3 和作业 5 都要让容器里的 agent 访问本地模型。做法统一：**模型服务也以容器形式接入 `agentharness-net`**，agent 容器按容器名访问它，并把这个名字加进 `NO_PROXY`（否则请求会被发给出网代理并被拒绝）。不要把 agent 容器接到宿主机网络上。

**Ollama**（作业 4 L1）：
```bash
docker run -d --name agentharness-ollama --cpus 16 --memory 30g --network agentharness-net \
  -v "$HOME/.ollama":/root/.ollama ollama/ollama:0.12.6
# --internal 网络不能出网，模型要先在能联网的地方拉好放进 ~/.ollama，例如临时起一个普通网络的容器：
#   docker run --rm -v "$HOME/.ollama":/root/.ollama --entrypoint sh ollama/ollama:0.12.6 -c 'ollama serve & sleep 3; ollama pull qwen3:8b'
```
agent 容器里：`-e NO_PROXY=agentharness-ollama`，provider 地址 `http://agentharness-ollama:11434/v1`。镜像锁定 `0.12.6` 标签，换版本后行为可能不同。课程团队实测过这条链路（GHCR 运行器镜像以普通用户身份 → 隔离网络 → `ollama/ollama:0.12.6` 容器 + `qwen3:0.6b`），能正常返回。注意 Qwen3 默认先思考：`max_tokens` 设得太小（例如 20）时，思考内容会把额度用光，`content` 返回空字符串，思考内容在 `reasoning` 字段里。

**llama.cpp**（作业 4 L3、作业 5）：用 llama.cpp 官方服务镜像，锁定 digest：`ghcr.io/ggml-org/llama.cpp@sha256:ae28f5c2046de51dfd00c9116a36fe44b5e8703ef730d0aea69082781eecb1f7`（`server` 标签，构建版本 418fe97b，比作业 4 锁定编译的 commit `4783b1145c` 新）。一定要加 `--api-key`，否则同一网络里的任何容器都能调用它：
```bash
export LOCAL_LLM_KEY=$(openssl rand -hex 16)
docker run -d --name agentharness-llm --cpus 16 --memory 30g --network agentharness-net \
  -e LOCAL_LLM_KEY -v "$PWD/models":/models:ro \
  ghcr.io/ggml-org/llama.cpp@sha256:ae28f5c2046de51dfd00c9116a36fe44b5e8703ef730d0aea69082781eecb1f7 \
  --model /models/Qwen3-Coder-30B-A3B-Instruct-Q4_K_M.gguf --jinja -c 65536 -np 2 -t 16 \
  --host 0.0.0.0 --port 8091 --api-key "$LOCAL_LLM_KEY"
```
（`--api-key "$LOCAL_LLM_KEY"` 在宿主机 shell 里展开。）agent 容器里：`-e NO_PROXY=agentharness-llm -e LOCAL_LLM_KEY`，地址 `http://agentharness-llm:8091/v1`。课程团队用这条链路（运行器容器 → 隔离网络 → 按容器名访问 llama.cpp 容器）和一个 8B 模型跑过 1 道小题：解出，共 4 次本地请求。

## SWE-bench 评测镜像（GHCR）
- **仓库**：`ghcr.io/odearevanhansen/swebench-x86_64`。所有题目共用这一个仓库，每题对应一个 tag，例如 `django_1776_django-15467`。
- **同步方式**：GitHub Actions 工作流 [`.github/workflows/sync-swebench-images.yml`](../.github/workflows/sync-swebench-images.yml) 用 crane 把镜像从 Docker Hub 复制到 GHCR。修改 `infra/swebench/instances*.txt` 并推送到 main 分支后会自动运行。
- **官方评测**：`python -m swebench.harness.run_evaluation -d infra/swebench/dataset.json -p preds.jsonl -id run1`，难题集改用 `dataset_hard.json`。评测要调用宿主机上的 Docker，所以请在宿主机上运行，并先执行 `pip install swebench==5.0.2`。
- **来源与许可**：镜像原样复制自 Docker Hub 上 SWE-bench 官方的 `swebench/sweb.eval.x86_64.*`，没有做任何修改。SWE-bench 的数据集和工具采用 MIT 许可；镜像中的各上游项目（django、sympy 等）和系统软件包遵循它们各自的许可证。课程转存这些镜像只是为了方便国内访问，不主张任何额外权利。
- **国内访问**：课程团队在国内机器上实测过，GHCR 的下载速度可以接受。如果你那里很慢，可以把环境变量 `SWE_IMAGE_REPO` 和数据集 JSON 中的 `image` 字段改成你自己的镜像仓库（用 `make_dataset_cn.py --repo` 重新生成）。
- **注意**：仅在线从 Hugging Face 指定数据集时，`swebench` 5.x 必须使用数据集名 `SWE-bench/SWE-bench_Verified`；本课用本地的 `infra/swebench/dataset.json`，不涉及这一点。
