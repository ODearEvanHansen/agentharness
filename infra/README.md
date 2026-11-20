# infra：课程基础设施

| 文件 | 用途 |
|---|---|
| `course.patch.yml` | DSH 课程配置补丁，默认**关闭会话日志上传**（`session-log-deepseek.enabled: false`）。通过 SDK 的 `patches=("/abs/path/course.patch.yml",)` 加载 |
| `egress/` | 出网白名单代理（tinyproxy），只放行 `api.deepseek.com`。作业容器接入 `--internal` 网络，并设置 `HTTPS_PROXY` 指向这个代理 |
| `swebench/` | SWE-bench 镜像工具：`pick_subset.py`（分层抽样，固定随机种子）、`make_dataset_cn.py`（生成镜像地址指向课程仓库的本地数据集 JSON）、`push_to_acr.sh`（旧的 ACR 方案）、`instances.txt`（当前 20 道题） |

## 出网白名单用法（示例）
```bash
docker build -t agentharness-egress:0.1 infra/egress
docker network create --internal agentharness-net
docker run -d --name agentharness-egress agentharness-egress:0.1
docker network connect agentharness-net agentharness-egress
# 作业容器：
docker run --network agentharness-net -e HTTPS_PROXY=http://agentharness-egress:8888 ...
```
验证：容器内 `curl https://api.deepseek.com/` 应返回 401，说明已连通，只是没带 key；`curl https://github.com/` 应失败。

## SWE-bench 评测镜像（GHCR）
- 仓库：`ghcr.io/odearevanhansen/swebench-x86_64`。所有实例放在同一个 package 里，每个实例一个 tag，tag 取官方镜像名中的实例部分，例如 `django_1776_django-15467`。
- 同步方式：由 GitHub Actions 工作流 [`.github/workflows/sync-swebench-images.yml`](../.github/workflows/sync-swebench-images.yml) 用 crane 直接从 Docker Hub 复制到 GHCR，不在本地中转。修改 `infra/swebench/instances*.txt` 并推送到 main 后会自动触发；也可以在 Actions 页面手动运行。
- 官方评测：先运行 `python infra/swebench/make_dataset_cn.py --instances infra/swebench/instances.txt --out swe_mirror.json`，再执行 `python -m swebench.harness.run_evaluation -d swe_mirror.json -p preds.jsonl -id run1`。
- 注意：`swebench` 5.x 必须使用数据集名 `SWE-bench/SWE-bench_Verified`。
- 国内访问：ghcr.io 在国内的速度不稳定，必要时请使用 GHCR 代理/镜像加速，具体方案待实测。
- `push_to_acr.sh` 是之前 ACR 方案留下的脚本，暂时保留。
