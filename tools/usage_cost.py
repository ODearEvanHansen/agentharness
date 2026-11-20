#!/usr/bin/env python3
"""Sum token usage from DSH session.v4.jsonl files and price them (DeepSeek official, USD / 1M tokens).

Usage: usage_cost.py <dsh_home> [model] [peak|offpeak]
"""
import json, sys
from pathlib import Path

PRICES = {  # cache-hit input, cache-miss input, output; (offpeak, peak) — api-docs.deepseek.com, 2026-11
    "deepseek-flash": {"offpeak": (0.003, 0.15, 0.6), "peak": (0.006, 0.30, 1.2)},
    "deepseek-v4-pro": {"offpeak": (0.022, 0.66, 1.98), "peak": (0.044, 1.32, 3.96)},
}


def find_usage(obj, acc):
    if isinstance(obj, dict):
        u = obj.get("usage")
        if isinstance(u, dict) and "inputTokens" in u and obj.get("type") != "chunk":
            acc.append(u)
            return
        for v in obj.values():
            find_usage(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            find_usage(v, acc)


def iter_session_lines(home, session_id=None):
    """Yield JSON records from plain and zstd-compressed DSH session logs."""
    pat = f"sessions/*/{session_id}/" if session_id else "sessions/**/"
    for f in list(Path(home).glob(pat + "session.v4.jsonl")) + list(Path(home).glob(pat + "session.v4.jsonl.zstd")):
        if f.suffix == ".zstd":
            from compression import zstd
            try:
                text = zstd.decompress(f.read_bytes()).decode()
            except Exception:
                continue  # file being written; caller retries later
        else:
            text = f.read_text()
        for line in text.splitlines():
            if line.strip():
                try:
                    yield json.loads(line)
                except ValueError:
                    pass


def summarize(home, model="deepseek-flash", tier="peak", session_id=None):
    hit_p, miss_p, out_p = PRICES[model][tier]
    tot = {"requests": 0, "input_miss": 0, "cache_read": 0, "output": 0}
    for rec in iter_session_lines(home, session_id):
        acc = []
        find_usage(rec, acc)
        if acc:
            u = acc[0]
            tot["requests"] += 1
            tot["input_miss"] += u.get("inputTokens", 0)
            tot["cache_read"] += u.get("cacheReadTokens", 0)
            tot["output"] += u.get("outputTokens", 0)
    total_in = tot["input_miss"] + tot["cache_read"]
    tot["cache_hit_rate"] = round(tot["cache_read"] / total_in, 3) if total_in else 0
    tot["usd"] = round((tot["input_miss"] * miss_p + tot["cache_read"] * hit_p + tot["output"] * out_p) / 1e6, 6)
    tot["model"], tot["tier"] = model, tier
    return tot


def main():
    home = Path(sys.argv[1])
    model = sys.argv[2] if len(sys.argv) > 2 else "deepseek-flash"
    tier = sys.argv[3] if len(sys.argv) > 3 else "peak"
    print(json.dumps(summarize(home, model, tier), ensure_ascii=False))


if __name__ == "__main__":
    main()
