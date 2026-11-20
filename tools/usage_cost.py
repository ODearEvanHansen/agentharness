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


def record_model(rec):
    """The model that produced this assistant message (DSH records it in message.source)."""
    try:
        src = rec["data"]["message"]["source"]
        return src.get("model"), src.get("provider")
    except (KeyError, TypeError):
        return None, None


def summarize(home, model="deepseek-flash", tier="peak", session_id=None):
    """Sum usage; each request is priced by the model that served it (falls back to `model`).

    Models not in PRICES (e.g. a local llama-server / Ollama route) are counted but cost $0.
    `by_model` breaks requests/tokens/usd down per model — useful when subagents use other routes.
    """
    tot = {"requests": 0, "input_miss": 0, "cache_read": 0, "output": 0, "usd": 0.0}
    by_model = {}
    for rec in iter_session_lines(home, session_id):
        acc = []
        find_usage(rec, acc)
        if not acc:
            continue
        u = acc[0]
        m = record_model(rec)[0] or model
        hit_p, miss_p, out_p = PRICES[m][tier] if m in PRICES else (0, 0, 0)
        row = by_model.setdefault(m, {"requests": 0, "input_miss": 0, "cache_read": 0, "output": 0, "usd": 0.0})
        d = {"requests": 1, "input_miss": u.get("inputTokens", 0), "cache_read": u.get("cacheReadTokens", 0),
             "output": u.get("outputTokens", 0)}
        d["usd"] = (d["input_miss"] * miss_p + d["cache_read"] * hit_p + d["output"] * out_p) / 1e6
        for t in (tot, row):
            for k, v in d.items():
                t[k] += v
    total_in = tot["input_miss"] + tot["cache_read"]
    tot["cache_hit_rate"] = round(tot["cache_read"] / total_in, 3) if total_in else 0
    tot["usd"] = round(tot["usd"], 6)
    for row in by_model.values():
        row["usd"] = round(row["usd"], 6)
    tot["model"], tot["tier"], tot["by_model"] = model, tier, by_model
    return tot


def main():
    home = Path(sys.argv[1])
    model = sys.argv[2] if len(sys.argv) > 2 else "deepseek-flash"
    tier = sys.argv[3] if len(sys.argv) > 3 else "peak"
    print(json.dumps(summarize(home, model, tier), ensure_ascii=False))


if __name__ == "__main__":
    main()
