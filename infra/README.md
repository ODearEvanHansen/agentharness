# infra：课程基础设施

| 文件 | 用途 |
|---|---|
| `course.patch.yml` | DSH 课程配置补丁，默认**关闭会话日志上传**（`session-log-deepseek.enabled: false`）。通过 SDK 的 `patches=("/abs/path/course.patch.yml",)` 加载 |
| `egress/` | 出网白名单代理（tinyproxy），只放行 `api.deepseek.com`。作业容器接入 `--internal` 网络，并设置 `HTTPS_PROXY` 指向这个代理 |
| `swebench/` | SWE-bench 国内镜像工具：`pick_subset.py`（分层抽样，固定随机种子）、`push_to_acr.sh`（维护者推送到 ACR）、`make_dataset_cn.py`（生成镜像地址指向 ACR 的本地数据集 JSON）、`instances.txt`（当前 20 道题） |

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

## SWE-bench 国内镜像
- 仓库：`crpi-wuyoxje33x46jb9c.cn-hangzhou.personal.cr.aliyuncs.com/agentharness/swebench-x86_64`，tag 取官方镜像名里的实例部分，例如 `django_1776_django-15467`。
- 官方评测：先运行 `python infra/swebench/make_dataset_cn.py --instances infra/swebench/instances.txt --out swe_cn.json`，再执行 `python -m swebench.harness.run_evaluation -d swe_cn.json -p preds.jsonl -id run1`。
- 注意：`swebench` 5.x 必须使用数据集名 `SWE-bench/SWE-bench_Verified`。
- 当前使用 ACR 个人版，仅用于流程验证，有限流。正式开课会更换分发方案。
