#!/usr/bin/env python3
"""作业 4 自动检查：确认 E1–E5 的结果文件齐全、数据自洽。只检查"实验做了、数据像真的"，结论对错由报告评审。"""
import json, sys
from pathlib import Path

R = Path(__file__).resolve().parent / "results"
ok_all = True


def check(name, cond, msg):
    global ok_all
    ok_all &= bool(cond)
    print(("✅" if cond else "❌"), name, msg)


def load(e):
    f = R / f"{e}.json"
    return json.loads(f.read_text())["results"] if f.exists() else None


e1 = load("E1")
check("E1", e1 and {"np1", "np4"} <= e1.keys() and all(v["total_tokens"] > 0 for v in e1.values()),
      "np1/np4 都有数据" + (f"：吞吐 {e1['np1']['agg_tok_s']} → {e1['np4']['agg_tok_s']} tok/s" if e1 else ""))
e2 = load("E2")
check("E2", e2 and (e2["cache_on"].get("second_cache_n") or 0) > 0 and e2["cache_on"]["second_prompt_n"] < e2["cache_off"]["second_prompt_n"],
      "开启 cache_prompt 后第二次请求确实复用了前缀" + (f"：{e2['cache_off']['second_prompt_ms']} → {e2['cache_on']['second_prompt_ms']} ms" if e2 else ""))
e3 = load("E3")
check("E3", e3 and {"baseline", "draft_n3", "draft_n16"} <= e3.keys() and all(e3[k]["draft_n"] for k in ("draft_n3", "draft_n16")),
      "有基线和两种草稿长度，草稿确实生效" + (f"：接受率 {e3['draft_n3']['accept_rate']} / {e3['draft_n16']['accept_rate']}" if e3 else ""))
e4 = load("E4")
check("E4", e4 and {"kv_f16", "kv_q8_0"} <= e4.keys() and all(v["rss_mb"] for v in e4.values()), "f16/q8_0 都有内存和速度数据")
e5 = load("E5")
check("E5", e5 and len(e5) >= 2 and all("pp512" in v and "tg128" in v for v in e5.values()), "至少两个模型的 llama-bench 数据")
check("报告", (Path(__file__).resolve().parent / "WRITEUP.md").exists(), "WRITEUP.md 存在")
sys.exit(0 if ok_all else 1)
