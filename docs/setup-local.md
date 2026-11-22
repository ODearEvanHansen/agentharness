# 本地模型与进阶工具

这一页接着[环境搭建指南](setup.md)，把作业 3–5 和期末项目要用到、但散落在各作业 README 里的操作串成分步指南：

1. [本地模型服务](#一本地模型服务)：Ollama（作业 4 L1）和 llama.cpp `llama-server`（作业 4 L2/L3、作业 5），接入课程隔离网络；
2. [用 `tools/usage_cost.py` 统计自己会话的花费](#二用-toolsusage_costpy-统计会话花费)；
3. [在 DSH 里加一个 `openai-completions` provider](#三在-dsh-里接入本地-provider)；
4. [patch 文件与插件加载](#四patch-文件与插件加载)（作业 3、5）；
5. [期末项目：在全新容器里检查可复现性](#五期末项目在全新容器里检查可复现性)。

!!! note "以各作业 README 为准"
    下面的命令都抄自仓库里的 [infra/README.md](infra.md)、[作业 3](assignments/a3.md)、[作业 4](assignments/a4.md)、[作业 5](assignments/a5.md) 和 llama.cpp 官方文档（[server README](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)）。两边不一致时以作业 README 为准，也欢迎[提 Issue](https://github.com/ODearEvanHansen/agentharness/issues/new/choose)。所有命令都在**仓库根目录**执行，并且已经按[基础设施](infra.md#隔离网络与出网白名单)一节建好了 `agentharness-net` 和 `agentharness-egress`。

## 一、本地模型服务

### 0. 先看内存，选路线

| 内存 | 作业 4 | 作业 5 |
|---|---|---|
| 16GB | Qwen3-8B（Q4_K_M 5.0GB、Q8_0 8.7GB）+ Qwen3-0.6B Q8_0（草稿模型，0.6GB）：L1（用 8B）、L2 | 小内存路线：Qwen3-4B Q4_K_M（2.5GB），`-c 24576 -np 1 -fa on`，容器 `--memory 8g` |
| ≥ 32GB | 再加 Qwen3-Coder-30B-A3B-Instruct Q4_K_M（18.6GB，运行时常驻约 28GB）：L3、E5 | 默认路线：Qwen3-Coder-30B-A3B，`-c 65536 -np 2`，容器 `--memory 30g` |

### 1. 下载 GGUF 模型并核对 sha256

模型统一放在仓库根目录的 `models/`（已被 `.gitignore` 忽略）。下载工具二选一：`pip install -U "huggingface_hub[cli]"`（命令 `hf`）或 `pip install modelscope`。

```bash
# Hugging Face；国内先设镜像
export HF_ENDPOINT=https://hf-mirror.com
hf download Qwen/Qwen3-8B-GGUF Qwen3-8B-Q4_K_M.gguf --local-dir models
hf download Qwen/Qwen3-0.6B-GGUF Qwen3-0.6B-Q8_0.gguf --local-dir models
hf download unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF Qwen3-Coder-30B-A3B-Instruct-Q4_K_M.gguf --local-dir models   # 32GB 路线
hf download Qwen/Qwen3-4B-GGUF Qwen3-4B-Q4_K_M.gguf --local-dir models                                             # 作业 5 小内存路线

# 或 ModelScope（同名仓库，注意参数是 --local_dir）
modelscope download --model Qwen/Qwen3-8B-GGUF Qwen3-8B-Q4_K_M.gguf --local_dir models
```

下载完核对 sha256（值来自作业 4、5 README；没下载的文件忽略）：

```bash
cd models && sha256sum -c --ignore-missing <<'EOF'
9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031  Qwen3-0.6B-Q8_0.gguf
d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785  Qwen3-8B-Q4_K_M.gguf
408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6  Qwen3-8B-Q8_0.gguf
fadc3e5f8d42bf7e894a785b05082e47daee4df26680389817e2093056f088ad  Qwen3-Coder-30B-A3B-Instruct-Q4_K_M.gguf
7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5  Qwen3-4B-Q4_K_M.gguf
EOF
cd ..
```

每个文件都应显示 `OK`。显示 `FAILED` 就删掉重下（多半是下载中断）；换了别的文件也能做实验，只是数字不能和参考结果直接比。

### 2. 路线 A：Ollama 容器（作业 4 L1）

`--internal` 网络不能出网，所以**先在普通网络里把模型拉进 `~/.ollama`**，再在隔离网络里起服务：

```bash
# ① 拉模型（临时容器，普通网络）；16GB 用 qwen3:8b，32GB 用 qwen3-coder:30b
docker run --rm -v "$HOME/.ollama":/root/.ollama --entrypoint sh ollama/ollama:0.12.6 \
  -c 'ollama serve & sleep 3; ollama pull qwen3:8b'
# ② 在隔离网络里起服务（镜像锁定 0.12.6）
docker run -d --name agentharness-ollama --cpus 16 --memory 30g --network agentharness-net \
  -v "$HOME/.ollama":/root/.ollama ollama/ollama:0.12.6
```

agent 容器里要加 `-e NO_PROXY=agentharness-ollama`，provider 地址是 `http://agentharness-ollama:11434/v1`（配置写法见[第三部分](#三在-dsh-里接入本地-provider)）。

### 3. 路线 B：llama.cpp `llama-server`

**作业 4 L2（宿主机上跑，源码编译、锁定 commit）**：llama-server 只做推理、不执行命令，可以直接在宿主机运行；L2 的实验脚本 `assignment4/engine/bench.py` 会自己启动它。

```bash
sudo apt install build-essential cmake
git clone https://github.com/ggml-org/llama.cpp && cd llama.cpp
git checkout 4783b1145c7073bb809f4c282ff4853cbfe42954
cmake -B build -DGGML_NATIVE=ON -DLLAMA_CURL=OFF
cmake --build build -j --target llama-server llama-bench
cd ..
llama.cpp/build/bin/llama-server --version     # 确认能运行
```

**作业 4 L3、作业 5（容器，锁定 digest，接入隔离网络）**：agent 要访问它，所以用官方镜像起成容器：

```bash
export LOCAL_LLM_KEY=$(openssl rand -hex 16)     # 必须设 --api-key，否则同一网络里任何容器都能调用
docker run -d --name agentharness-llm --cpus 16 --memory 30g --network agentharness-net \
  -e LOCAL_LLM_KEY -v "$PWD/models":/models:ro \
  ghcr.io/ggml-org/llama.cpp@sha256:ae28f5c2046de51dfd00c9116a36fe44b5e8703ef730d0aea69082781eecb1f7 \
  --model /models/Qwen3-Coder-30B-A3B-Instruct-Q4_K_M.gguf --jinja -c 65536 -np 2 -t 16 \
  --host 0.0.0.0 --port 8091 --api-key "$LOCAL_LLM_KEY"
```

16GB 小内存路线（作业 5）只改三处：`--model /models/Qwen3-4B-Q4_K_M.gguf`、`-c 24576 -np 1`、加 `-fa on`，容器 `--memory 8g`。

参数含义（来自 llama.cpp server README）：

| 参数 | 含义 |
|---|---|
| `-c N` | 上下文总长度（所有槽位共享）；KV 内存和它成正比 |
| `-np N` | 槽位数，即同时处理的请求数；每个槽位分到约 `c / np` 的上下文 |
| `-fa on` | 开启 Flash Attention |
| `-t N` | 生成用的 CPU 线程数，和容器 `--cpus` 对齐 |
| `--jinja` | 用模型自带的 chat 模板（工具调用需要） |
| `--api-key KEY` | 请求必须带 `Authorization: Bearer KEY` |

**先算 KV 内存再定 `-c`**：Qwen3-4B 的 f16 KV 约 144KB/token（36 层 × 8 个 KV 头 × 128 维 × K、V 两份 × 2 字节），`-c 65536` 光 KV 就约 9GB，8GB 容器在加载时会被 OOM 杀掉。

### 4. 确认就绪：看 `/health`，不要看进程

`/health` 是公开端点（不检查 API key）：模型还在加载时返回 503（`Loading model`），加载完成返回 200 和 `{"status":"ok"}`。从隔离网络里用运行器镜像检查，这同时验证了 agent 容器能按容器名访问它：

```bash
docker run --rm --network agentharness-net -e NO_PROXY=agentharness-llm -e LOCAL_LLM_KEY \
  agentharness-runner:0.1 sh -c '
    until [ "$(curl -s -o /dev/null -w "%{http_code}" http://agentharness-llm:8091/health)" = 200 ]; do
      echo "loading..."; sleep 5; done
    curl -s http://agentharness-llm:8091/health; echo
    curl -s http://agentharness-llm:8091/v1/models -H "Authorization: Bearer $LOCAL_LLM_KEY" | head -c 300; echo'
```

也可以 `docker logs -f agentharness-llm`，出现 `listening on http://0.0.0.0:8091` 才算就绪。一直是 `loading...` 时看 `docker ps -a` / `docker logs`：容器退出了多半是 OOM（`docker inspect -f '{{.State.OOMKilled}}' agentharness-llm`）。Ollama 同理，把地址换成 `http://agentharness-ollama:11434/v1/models`。

### 5. 让 agent 容器访问本地服务

规则只有两条（见[基础设施 · 本地模型服务](infra.md#本地模型服务接入隔离网络)）：

1. 模型服务和 agent 都在 `agentharness-net` 里，**按容器名**访问；不要把 agent 容器接到宿主机网络。
2. 把模型服务的容器名加进 `NO_PROXY`，否则请求会被发给出网代理并被拒绝。

作业 5 的写法：

```bash
ahrun() {
  docker run --rm -it --cpus 4 --memory 8g --network agentharness-net \
    -e HTTPS_PROXY=http://agentharness-egress:8888 -e NO_PROXY=agentharness-llm \
    -e DEEPSEEK_API_KEY -e LOCAL_LLM_KEY -u "$(id -u):$(id -g)" -e HOME=/tmp \
    -v "$PWD":/work agentharness-runner:0.1 "$@"
}
```

用 Ollama 时把 `NO_PROXY` 改成 `agentharness-ollama`。

### 6. 常见坑

| 现象 | 原因 | 处理 |
|---|---|---|
| `content` 是空字符串，`reasoning` 字段里有内容 | Qwen3 默认先思考，`max_tokens` 太小（如 20）时额度被思考用光 | 调大 `max_tokens`；调试时先看 `reasoning` 字段 |
| 跑完一看全部解出，但 `by_model` 里**没有本地请求** | 本地服务没起来或被 OOM 杀掉，DSH 不报错，**静默退回云端** | 每次跑完都看运行记录的 `by_model` 和 llama-server 日志；按上面的 KV 公式减小 `-c` / `-np` |
| 脚本说"服务已启动"，其实没有 | 用 `pgrep` 判断，匹配到了脚本自己的命令行 | 只认 `/health` 返回 200 或日志里的 `listening on` |
| agent 请求本地服务报代理错误 | 容器名没进 `NO_PROXY` | 加 `-e NO_PROXY=<容器名>` |
| 401 | 没带或带错 key | agent 容器里加 `-e LOCAL_LLM_KEY`，和启动服务时是同一个 shell |
| 本地子 agent 很慢 | 每次请求都带约 1 万 token 的系统提示和工具定义，CPU 预填充慢 | 见作业 5 的"耗时估算"，先估算再跑 |

## 二、用 `tools/usage_cost.py` 统计会话花费

`tools/usage_cost.py` 读取一个 DSH home 目录下所有 `sessions/**/session.v4.jsonl`（以及 zstd 压缩的 `session.v4.jsonl.zstd`），按 DeepSeek 官方人民币价格（元 / 百万 token）计价。**每次请求按实际服务它的模型计价**；不在价格表里的模型（本地 llama-server / Ollama）照常计数，按 0 元计。

用法（位置参数，没有 `--` 选项）：

```text
python3 tools/usage_cost.py <dsh_home> [model] [peak|offpeak]
```

- `dsh_home`：DSH 的 home 目录（里面有 `sessions/`）。课程运行器的位置：小题在 `assignment2/results/dsh-home-mini/<题目>/`，SWE 题在 `assignment2/results/dsh-homes/<容器名>/`；你自己用 SDK 时就是传给 `DeepSeekHarness(dsh_home=...)` 的目录。
- `model`：会话日志里没记录模型时的兜底模型，默认 `deepseek-flash`；
- 第三个参数：`peak`（默认，课程统一按高峰价）或 `offpeak`（低谷价，高峰价的一半）。
- 日志是 `.zstd` 时需要 `pip install zstandard`（运行器镜像里已装）。

示例（课程团队一次作业 2 运行的真实输出）：

```bash
python3 tools/usage_cost.py assignment2/results/dsh-homes/dsh-course-a2-dsh-django_1776_django-15467-98b13e/
```

```json
{"requests": 14, "input_miss": 6547, "cache_read": 75008, "output": 4827, "cny": 0.05471, "usd": 0.008207, "cache_hit_rate": 0.92, "model": "deepseek-flash", "tier": "peak", "by_model": {"deepseek-flash": {"requests": 14, "input_miss": 6547, "cache_read": 75008, "output": 4827, "cny": 0.05471, "usd": 0.008207}}}
```

同一目录加 `deepseek-flash offpeak` 时 `cny` 变成 `0.027355`。字段含义：

| 字段 | 含义 |
|---|---|
| `requests` | 模型请求次数（含子 agent） |
| `input_miss` / `cache_read` | 未命中缓存 / 命中缓存的输入 token |
| `output` | 输出 token |
| `cny` | **花费，单位元**（看这个） |
| `usd` | 已弃用，只为兼容旧记录保留，不要使用 |
| `cache_hit_rate` | `cache_read / (input_miss + cache_read)` |
| `by_model` | 按模型拆分；作业 5 用它确认本地模型确实被调用（本地模型那一行 `cny` 为 0） |

统计多个目录：

```bash
for d in assignment2/results/dsh-home-mini/*/; do
  printf '%s ' "$(basename "$d")"; python3 tools/usage_cost.py "$d" | python3 -c 'import json,sys; r=json.load(sys.stdin); print(r["requests"], r["cny"], r["cache_hit_rate"])'
done
```

注意：`dsh-home*/` 会被下一次运行覆盖，要保留的数据先复制出来。

## 三、在 DSH 里接入本地 provider

DSH 的模型供应商配置在 `llm-pi-ai` 插件的 `providers` 里。用一个 patch 文件给它加一个 `openai-completions` 类型的 provider，这是作业 5 模板 [`assignment5/templates/local-worker.patch.yml`](https://github.com/ODearEvanHansen/agentharness/blob/main/assignment5/templates/local-worker.patch.yml) 的写法：

```yaml
- id: llm-pi-ai
  config:
    providers:
      local:                                   # provider 名，后面按这个名字引用
        apiKeyEnv: LOCAL_LLM_KEY               # 从这个环境变量读 key（和 llama-server --api-key 相同）
        api: openai-completions
        baseURL: http://agentharness-llm:8091/v1
        models:
          - id: qwen3-coder-30b-a3b            # 小内存路线改成 qwen3-4b
```

作业 5 再用 `@deepseek-ai/dsh-tool-subagent` 插件把子 agent 指向这个 provider（同一文件的后半部分：`agentOptions: { provider: local, model: qwen3-coder-30b-a3b }`）。

作业 4 L1 换成 Ollama 时，把 `baseURL` 改成 `http://agentharness-ollama:11434/v1`，`models` 的 `id` 改成你 `ollama pull` 的模型名（如 `qwen3:8b`）。Ollama 不校验 key；`apiKeyEnv` 可以指向任意一个非空的环境变量。

加载方式：

- 课程运行器：`--patch /work/<你的 patch 路径>`（可重复；容器里仓库在 `/work`，见作业 5 的运行命令）；
- 自己用 SDK：`DeepSeekHarness(..., patches=("/abs/path/infra/course.patch.yml", "/abs/path/my.patch.yml"))`。

验证：跑完后用[第二部分](#二用-toolsusage_costpy-统计会话花费)的脚本看 `by_model` 里是否出现了本地模型 id，同时看 `docker logs agentharness-llm` 里有没有请求。作业 4 L1 的"agent 只回一句 Hello"是故意留的排查题，这里不给答案。

## 四、patch 文件与插件加载

作业 3 只用**配置补丁**和**插件**优化 agent，不改 DSH 源码。完整说明见[作业 3](assignments/a3.md#插件模板已验证)，最短路径如下：

1. **准备文件**：

    ```bash
    NICK=你的昵称
    mkdir -p assignment3/submission/$NICK
    cp assignment3/templates/trim-tool-output.ts assignment3/templates/mini.patch.yml assignment3/templates/swe.patch.yml \
       assignment3/submission/$NICK/
    sed -i "s|NICK|$NICK|" assignment3/submission/$NICK/mini.patch.yml
    sed -i -e "s|HOST_REPO|$PWD|" -e "s|NICK|$NICK|" assignment3/submission/$NICK/swe.patch.yml
    cat assignment3/submission/$NICK/*.patch.yml     # 确认路径对
    ```

2. **patch 的格式**：一个 YAML 列表。`- id: <插件 id>` + `config:` 修改已有插件的配置（如上一节的 `llm-pi-ai`）；`- insert:` 插入新插件，`name` 可以是包名（`'@deepseek-ai/dsh-tool-subagent'`）或 `.ts` 文件的**绝对路径**：

    ```yaml
    - insert:
        - id: trim-tool-output
          name: '/work/assignment3/submission/<昵称>/trim-tool-output.ts'
          config: { maxChars: 2000 }
    ```

    插件是 TypeScript 文件，**不需要编译，也不用装 Node**。用 DSH 运行时的 `--dump-config` 可以列出所有插件 id 和当前配置。

3. **路径**：小题在运行器容器里跑，仓库挂在 `/work`，用 `mini.patch.yml`；SWE 题在宿主机上跑，用 `swe.patch.yml`（宿主机绝对路径，这个目录会按同一路径只读挂进任务容器）。
4. **运行**：在作业 2 的运行命令后加 `--patch`（可重复，例如同时加 `mini.patch.yml` 和 `guard.patch.yml`）。课程配置 `infra/course.patch.yml` 会被自动加载，不用自己加。
5. **确认插件真的加载了**：路径写错时 DSH 不一定报错，结果和没加插件一模一样。`trim-tool-output` 生效时会在会话日志里留下 `已省略`，用[作业 3](assignments/a3.md#插件模板已验证) 里的脚本数一下；guard 插件看 `guard-blocks.jsonl`。开插件的一组计数应大于 0。

## 五、期末项目：在全新容器里检查可复现性

期末项目要求"一条命令或一个脚本就能重跑主要实验"（[期末项目指南](project.md#要求)）。提交前在**全新克隆 + 全新容器**里跑一遍，能发现"只在我电脑上能跑"的问题：漏提交的文件、写死的绝对路径、只装在你 venv 里的依赖、依赖旧的 `dsh-home` 状态。

```bash
# 1. 在空目录里重新克隆你的公开仓库（不要用平时的工作目录）
FRESH=$(mktemp -d)
git clone https://github.com/<你>/<项目仓库>.git "$FRESH/repo"
# 2. 用课程运行器镜像起一次性容器，只挂这份新克隆，走隔离网络 + 出网白名单
docker run --rm -it --cpus 4 --memory 8g --network agentharness-net \
  -e HTTPS_PROXY=http://agentharness-egress:8888 -e DEEPSEEK_API_KEY \
  -u "$(id -u):$(id -g)" -e HOME=/tmp -v "$FRESH/repo":/work agentharness-runner:0.1 \
  sh -c 'python --version && pip list 2>/dev/null | grep -i deepseek && bash reproduce.sh'   # 换成你 README 里写的那条命令
```

检查清单：

- [ ] 容器里只有运行器镜像自带的依赖（Python 3.12、`deepseek-harness-sdk`、`zstandard`、git、curl）。需要别的包，就在复现脚本里显式安装并锁版本；但隔离网络只放行 `api.deepseek.com`，装不了包，这时另做一个基于 `agentharness-runner:0.1` 的 Dockerfile 并写进 README。
- [ ] 复现脚本只用相对路径，不依赖 `$HOME` 下的文件或之前运行留下的 `dsh-home*/`。
- [ ] 用到本地模型时，README 写清模型文件、sha256、启动命令和 `/health` 检查（按[第一部分](#一本地模型服务)），并在 docker run 里加 `-e NO_PROXY=<模型容器名>`。
- [ ] 跑完用 `tools/usage_cost.py` 算出花费（元），和你报告里的数字对得上量级。
- [ ] 仓库和日志里没有 API key（`git grep -n "sk-"` 应该为空）。
- [ ] 结束后 `rm -rf "$FRESH"`。

先用最小规模（1–2 道题）跑通再放大，避免在复现检查上花太多 API 费用。
