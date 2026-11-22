#!/usr/bin/env python3
"""Sum token usage from DSH session.v4.jsonl files and price them (DeepSeek official CNY / 元 per 1M tokens).

Output: `cny` (元) is the cost field. `usd` is DEPRECATED — kept only for backward compatibility,
computed from the old official USD table (USD_PRICES); do not show it to learners.

Usage: usage_cost.py <dsh_home> [model] [peak|offpeak]
"""
import json, sys
from pathlib import Path

# 元 / 1M tokens: (cache-hit input, cache-miss input, output).
# Source: https://api-docs.deepseek.com/zh-cn/quick_start/pricing (fetched 2026-11-22).
# Peak = Beijing time Mon–Fri 9:00–12:00 and 14:00–18:00 (excl. holidays); off-peak = half of peak.
PRICES = {
    "deepseek-flash": {"offpeak": (0.02, 1, 4), "peak": (0.04, 2, 8)},
    "deepseek-v4-pro": {"offpeak": (0.15, 4.5, 13.5), "peak": (0.30, 9.0, 27.0)},
}
# DEPRECATED: official USD / 1M tokens, only used to fill the legacy `usd` field.
USD_PRICES = {
    "deepseek-flash": {"offpeak": (0.003, 0.15, 0.6), "peak": (0.006, 0.30, 1.2)},
    "deepseek-v4-pro": {"offpeak": (0.022, 0.66, 1.98), "peak": (0.044, 1.32, 3.96)},
}


# Official CNY/USD price ratio per model (identical for all three price columns). Used ONLY to back-fill `cny`
# for legacy records that carry just `usd` — this is the official price ratio, not an exchange rate.
CNY_PER_USD_PRICE = {"deepseek-flash": 20 / 3, "deepseek-v4-pro": 75 / 11}


def record_cny(r, model=None):
    """Cost of a run record / by_model row in 元: `cny` if present, else legacy `usd` × official price ratio."""
    if not isinstance(r, dict):
        return 0.0
    if r.get("cny") is not None:
        return r["cny"]
    m = model or r.get("model") or "deepseek-flash"
    return (r.get("usd") or 0) * CNY_PER_USD_PRICE.get(m, 0)


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


def _zstd_decompress(data: bytes) -> bytes:
    try:
        from compression import zstd          # Python ≥ 3.14
        return zstd.decompress(data)
    except ImportError:
        pass
    try:
        import io, zstandard                  # Python < 3.14
    except ImportError:
        raise ImportError("会话日志是 zstd 压缩的（session.v4.jsonl.zstd），需要先安装解压库：pip install zstandard") from None
    return zstandard.ZstdDecompressor().stream_reader(io.BytesIO(data)).read()


def iter_session_lines(home, session_id=None):
    """Yield JSON records from plain and zstd-compressed DSH session logs."""
    pat = f"sessions/*/{session_id}/" if session_id else "sessions/**/"
    zfound = zparsed = 0
    for f in list(Path(home).glob(pat + "session.v4.jsonl")) + list(Path(home).glob(pat + "session.v4.jsonl.zstd")):
        if f.suffix == ".zstd":
            zfound += 1
            try:
                text = _zstd_decompress(f.read_bytes()).decode("utf-8", errors="replace")
            except ImportError:
                raise
            except Exception:
                continue  # file being written; caller retries later
            zparsed += 1
        else:
            text = f.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            if line.strip():
                try:
                    yield json.loads(line)
                except ValueError:
                    pass
    if zfound and not zparsed:
        print(f"警告：找到 {zfound} 个 zstd 压缩的会话日志，但一个都没能解压（文件可能还在写入或已损坏），用量按 0 计",
              file=sys.stderr)


def record_model(rec):
    """The model that produced this assistant message (DSH records it in message.source)."""
    try:
        src = rec["data"]["message"]["source"]
        return src.get("model"), src.get("provider")
    except (KeyError, TypeError):
        return None, None


def summarize(home, model="deepseek-flash", tier="peak", session_id=None):
    """Sum usage; each request is priced by the model that served it (falls back to `model`).

    Models not in PRICES (e.g. a local llama-server / Ollama route) are counted but cost 0 元.
    `by_model` breaks requests/tokens/cny down per model — useful when subagents use other routes.
    """
    tot = {"requests": 0, "input_miss": 0, "cache_read": 0, "output": 0, "cny": 0.0, "usd": 0.0}
    by_model = {}
    for rec in iter_session_lines(home, session_id):
        acc = []
        find_usage(rec, acc)
        if not acc:
            continue
        u = acc[0]
        m = record_model(rec)[0] or model
        hit_p, miss_p, out_p = PRICES[m][tier] if m in PRICES else (0, 0, 0)
        uh, um, uo = USD_PRICES[m][tier] if m in USD_PRICES else (0, 0, 0)
        row = by_model.setdefault(m, {"requests": 0, "input_miss": 0, "cache_read": 0, "output": 0, "cny": 0.0, "usd": 0.0})
        d = {"requests": 1, "input_miss": u.get("inputTokens", 0), "cache_read": u.get("cacheReadTokens", 0),
             "output": u.get("outputTokens", 0)}
        d["cny"] = (d["input_miss"] * miss_p + d["cache_read"] * hit_p + d["output"] * out_p) / 1e6
        d["usd"] = (d["input_miss"] * um + d["cache_read"] * uh + d["output"] * uo) / 1e6  # deprecated
        for t in (tot, row):
            for k, v in d.items():
                t[k] += v
    total_in = tot["input_miss"] + tot["cache_read"]
    tot["cache_hit_rate"] = round(tot["cache_read"] / total_in, 3) if total_in else 0
    for t in [tot, *by_model.values()]:
        t["cny"], t["usd"] = round(t["cny"], 6), round(t["usd"], 6)
    tot["model"], tot["tier"], tot["by_model"] = model, tier, by_model
    return tot


def main():
    home = Path(sys.argv[1])
    model = sys.argv[2] if len(sys.argv) > 2 else "deepseek-flash"
    tier = sys.argv[3] if len(sys.argv) > 3 else "peak"
    print(json.dumps(summarize(home, model, tier), ensure_ascii=False))


if __name__ == "__main__":
    main()
