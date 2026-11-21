#!/usr/bin/env python3
"""作业 5 自动检查（课程小题路由实验）。

先运行（需要 llama-server 在 8091 端口托管本地模型，见 README）：
  export LOCAL_LLM_KEY=$(openssl rand -hex 16)   # 与 llama-server --api-key 相同；agent 务必在容器内运行
  （命令见 assignment5/README.md：先跑对照组 --tag sdkfull，再跑路由组 --tag a5）
  python assignment5/check.py assignment2/results/mini-dsh-a5.jsonl assignment2/results/mini-dsh-sdkfull.jsonl

检查：解决 ≥ 6/8；至少一半的题目确实把请求路由到了本地模型；并与同一 profile、不路由的对照组比较云端成本和耗时。
"""
import json, statistics, sys
from pathlib import Path

f = Path(sys.argv[1] if len(sys.argv) > 1 else "assignment2/results/mini-dsh-a5.jsonl")
rs = list({r["id"]: r for r in map(json.loads, f.open())}.values())
ok = True


def check(name, cond, msg):
    global ok
    ok &= bool(cond)
    print(("✅" if cond else "❌"), name, msg)


solved = sum(1 for r in rs if r["solved"])
check("L1", solved >= 6, f"解决 {solved}/{len(rs)}（要求 ≥ 6）")
routed = [r for r in rs if any(m not in ("deepseek-flash", "deepseek-v4-pro") and v["requests"] > 0
                               for m, v in (r.get("by_model") or {}).items())]
check("L1", len(routed) >= len(rs) / 2, f"{len(routed)}/{len(rs)} 题有请求路由到本地模型")
cloud = sum(v["usd"] for r in rs for m, v in (r.get("by_model") or {}).items() if m.startswith("deepseek"))
local_req = sum(v["requests"] for r in rs for m, v in (r.get("by_model") or {}).items() if not m.startswith("deepseek"))
cloud_req = sum(v["requests"] for r in rs for m, v in (r.get("by_model") or {}).items() if m.startswith("deepseek"))
print(f"   云端请求 {cloud_req} 次 ${cloud:.4f}；本地请求 {local_req} 次；中位耗时 {statistics.median(r['seconds'] for r in rs):.1f}s")
base = Path(sys.argv[2]) if len(sys.argv) > 2 else f.with_name("mini-dsh-sdkfull.jsonl")
if base.exists():
    b = list({r["id"]: r for r in map(json.loads, base.open())}.values())
    print(f"   对照（同 profile、不路由）：解决 {sum(r['solved'] for r in b)}/{len(b)}，云端 ${sum(r['usd'] for r in b):.4f}，"
          f"中位耗时 {statistics.median(r['seconds'] for r in b):.1f}s")
sys.exit(0 if ok else 1)
