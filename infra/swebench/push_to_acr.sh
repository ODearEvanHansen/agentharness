#!/usr/bin/env bash
# 把本机已有的 SWE-bench 官方评测镜像推到课程的阿里云 ACR 仓库（维护者在宿主机上执行，需先登录 ACR，见 README）。
#
# 用法：./push_to_acr.sh instances.txt          # 默认推到课程仓库；可用 ACR_REPO=... 覆盖
#
# 约定：所有实例放在同一个仓库 ACR_REPO，tag = 官方镜像名的实例部分，例如
#   swebench/sweb.eval.x86_64.django_1776_django-15467:latest -> $ACR_REPO:django_1776_django-15467
# 本地缺少的镜像会先从 Docker Hub 拉取。可重复执行，已推送的 tag 会跳过。个人版有限流，逐个顺序推送。
set -euo pipefail
REPO="${ACR_REPO:-crpi-wuyoxje33x46jb9c.cn-hangzhou.personal.cr.aliyuncs.com/agentharness/swebench-x86_64}"
LIST="${1:-instances.txt}"
LOG="push_$(date +%Y%m%d_%H%M%S).log"
ok=0; fail=0
while read -r iid; do
  [ -z "$iid" ] && continue
  suffix="${iid//__/_1776_}"
  src="swebench/sweb.eval.x86_64.${suffix}:latest"
  dst="${REPO}:${suffix}"
  if docker manifest inspect "$dst" >/dev/null 2>&1; then
    echo "skip   $iid (already in ACR)" | tee -a "$LOG"; ok=$((ok+1)); continue
  fi
  docker image inspect "$src" >/dev/null 2>&1 || docker pull -q "$src"
  docker tag "$src" "$dst"
  if docker push -q "$dst" >>"$LOG" 2>&1; then
    echo "pushed $iid -> $dst" | tee -a "$LOG"; ok=$((ok+1))
  else
    echo "FAILED $iid (see $LOG)" | tee -a "$LOG"; fail=$((fail+1))
  fi
  docker rmi "$dst" >/dev/null 2>&1 || true   # 只删多出来的 tag，不删原镜像
done < "$LIST"
echo "done: ok=$ok failed=$fail  (log: $LOG)"
