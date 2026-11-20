#!/bin/bash
# DSH SDK 的 dsh_bin 包装：在任务容器（$DSH_CTR）里启动 DSH 运行时，SDK 通过本进程的 stdin/stdout 走 JSON-RPC。
# run.py 会设置 DSH_CTR 和 AH_PROXY；DEEPSEEK_API_KEY 从当前环境透传（不写入命令行）。
exec docker exec -i \
  -e DSH_HOME=/dshhome \
  -e DEEPSEEK_API_KEY \
  -e HTTPS_PROXY="$AH_PROXY" -e HTTP_PROXY="$AH_PROXY" \
  -e DSH_PERMISSION_MODE=danger-full-access \
  -e PATH=/opt/miniconda3/envs/testbed/bin:/opt/miniconda3/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  -w /testbed "$DSH_CTR" /dsh/deepseek-harness-sdk-runtime-linux-x64 "$@"
