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
搭好后在容器内验证，下面三条都必须满足：
1. `curl https://api.deepseek.com/` 返回 401：说明通过代理已经连通，只是请求没带 key。
2. `curl https://github.com/` 失败：代理拒绝了白名单以外的域名。
3. `curl --noproxy '*' https://example.com/` 失败：说明网络本身是 `--internal`，绕过代理也出不去。**如果这一条能成功，白名单就形同虚设。**

白名单有一种情况**防不住**：容器里的 agent 能拿到你的 API key，它可以通过 `api.deepseek.com` 本身把数据发出去，比如发到攻击者自己的 DeepSeek 账号。所以请**为本课程单独创建一个 key，只充值少量余额，课程结束后删除**。

## 运行器镜像
```bash
docker build -t agentharness-runner:0.1 infra/runner        # 需要正常网络，只构建一次
# 之后在隔离网络中运行，以作业 2 的小题为例：
docker run --rm -it --cpus 4 --memory 8g --network agentharness-net \
  -e HTTPS_PROXY=http://agentharness-egress:8888 -e DEEPSEEK_API_KEY \
  -v "$PWD":/work agentharness-runner:0.1 python assignment2/run.py --agent madsloop --suite mini
```

## SWE-bench 评测镜像（GHCR）
- **仓库**：`ghcr.io/odearevanhansen/swebench-x86_64`。所有题目共用这一个仓库，每题对应一个 tag，例如 `django_1776_django-15467`。
- **同步方式**：GitHub Actions 工作流 [`.github/workflows/sync-swebench-images.yml`](../.github/workflows/sync-swebench-images.yml) 用 crane 把镜像从 Docker Hub 复制到 GHCR。修改 `infra/swebench/instances*.txt` 并推送到 main 分支后会自动运行。
- **官方评测**：`python -m swebench.harness.run_evaluation -d infra/swebench/dataset.json -p preds.jsonl -id run1`，难题集改用 `dataset_hard.json`。评测要调用宿主机上的 Docker，所以请在宿主机上运行，并先执行 `pip install swebench==5.0.2`。
- **来源与许可**：镜像原样复制自 Docker Hub 上 SWE-bench 官方的 `swebench/sweb.eval.x86_64.*`，没有做任何修改。SWE-bench 的数据集和工具采用 MIT 许可；镜像中的各上游项目（django、sympy 等）和系统软件包遵循它们各自的许可证。课程转存这些镜像只是为了方便国内访问，不主张任何额外权利。
- **国内访问**：课程团队在国内机器上实测过，GHCR 的下载速度可以接受。如果你那里很慢，可以把环境变量 `SWE_IMAGE_REPO` 和数据集 JSON 中的 `image` 字段改成你自己的镜像仓库（用 `make_dataset_cn.py --repo` 重新生成）。
- **注意**：`swebench` 5.x 必须使用数据集名 `SWE-bench/SWE-bench_Verified`。
