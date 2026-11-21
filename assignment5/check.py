#!/usr/bin/env python3
"""作业 5 自动检查（课程小题路由实验）。

先运行（需要 llama-server 在 8091 端口托管本地模型，见 README）：
  export LOCAL_LLM_KEY=none DSH_PERMISSION_MODE=danger-full-access   # 务必在容器内
  python assignment2/run.py --agent dsh --suite mini --profile sdk \
      --patch $PWD/assignment5/templates/local-worker.patch.yml \
      --prompt-suffix-file assignment5/templates/routing-hint.txt --tag a5
  python assignment5/check.py assignment2/results/mini-dsh-a5.jsonl

检查：解决 ≥ 6/8；至少一半的题目确实把请求路由到了本地模型；同时报告 DeepSeek 侧成本，与不路由的基线（mini-dsh.jsonl，如果存在）对比。
"""
import json, sys
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
print(f"   云端请求 {cloud_req} 次 ${cloud:.4f}；本地请求 {local_req} 次；中位耗时 {sorted(r['seconds'] for r in rs)[len(rs)//2]}s")
base = f.with_name("mini-dsh.jsonl")
if base.exists():
    b = list({r["id"]: r for r in map(json.loads, base.open())}.values())
    print(f"   对照（不路由）：解决 {sum(r['solved'] for r in b)}/{len(b)}，云端 ${sum(r['usd'] for r in b):.4f}，"
          f"中位耗时 {sorted(r['seconds'] for r in b)[len(b)//2]}s")
sys.exit(0 if ok else 1)
