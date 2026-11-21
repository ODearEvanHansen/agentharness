#!/usr/bin/env python3
"""作业 4 推理服务实验（llama.cpp `llama-server`）。每个实验会自己启动和停止服务器。

  python assignment4/engine/bench.py --exp E1 --model models/Qwen3-8B-Q4_K_M.gguf
  python assignment4/engine/bench.py --exp E3 --model models/Qwen3-8B-Q4_K_M.gguf --draft models/Qwen3-0.6B-Q8_0.gguf
  python assignment4/engine/bench.py --exp E5 --model a.gguf --model b.gguf        # 每个模型跑一遍 llama-bench

实验：
  E1 批处理：-np 1 对比 -np 4，同时发 4 个请求 → 总吞吐、平均延迟
  E2 前缀复用：cache_prompt 关/开（各自冷启动），第二个请求与第一个共享约 4.6k token 前缀 → 预填充时间
  E3 推测解码：无草稿 / 草稿长度 3 / 草稿长度 16 → 生成速度、接受率
  E4 KV 量化：f16 对比 q8_0（-fa on）→ 常驻内存、预填充和生成速度
  E5 权重量化与架构：llama-bench pp512/tg128
结果写入 assignment4/results/<实验>.json。check.py 会检查这些文件。
"""
import argparse, concurrent.futures as cf, json, os, platform, subprocess, time, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "results"
CODE_PROMPT = ("Write a Python function that parses an ISO-8601 duration like P1DT2H3M4S into seconds, "
               "with docstring and 5 doctests.\n```python\n")
# 约 4.6k token（Qwen3 分词）的"agent 风格"共享前缀：系统提示 + 工具定义 + 一段代码
LONG_PREFIX = ("You are a coding agent. Tools: bash(command), read_file(path), edit_file(path, old, new), done(summary).\n"
               + "\n".join(f"def helper_{i}(x):\n    '''Helper number {i}: returns x transformed.'''\n    return (x * {i} + {i % 7}) % 9973\n"
                           for i in range(120)))


class Server:
    def __init__(self, a, extra, ctx=16384):
        self.a = a
        cmd = [a.server, "-m", a.model[0], "-t", str(a.threads), "-c", str(ctx), "--host", "127.0.0.1",
               "--port", str(a.port), *extra]
        print("$", " ".join(cmd), flush=True)
        self.p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(600):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{a.port}/health", timeout=2) as r:
                    if r.status == 200:
                        return
            except Exception:
                time.sleep(1)
        self.p.kill()
        raise RuntimeError("llama-server 没能启动：" + " ".join(extra))

    def complete(self, prompt, n=128, **kw):
        body = {"prompt": prompt, "n_predict": n, "temperature": 0, "cache_prompt": True, **kw}
        req = urllib.request.Request(f"http://127.0.0.1:{self.a.port}/completion", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        t = time.time()
        with urllib.request.urlopen(req, timeout=1800) as r:
            d = json.load(r)
        d["_wall"] = time.time() - t
        return d

    def rss_mb(self):
        try:
            for line in open(f"/proc/{self.p.pid}/status", encoding="utf-8"):
                if line.startswith("VmRSS"):
                    return int(line.split()[1]) // 1024
        except OSError:
            pass
        try:   # 没有 /proc（macOS 等）：用 ps，单位 KB
            r = subprocess.run(["ps", "-o", "rss=", "-p", str(self.p.pid)], capture_output=True, text=True, timeout=10)
            return int(r.stdout.split()[0]) // 1024 if r.stdout.split() else None
        except (OSError, ValueError, subprocess.SubprocessError):
            return None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.p.terminate()
        try:
            self.p.wait(30)
        except subprocess.TimeoutExpired:
            self.p.kill()


def e1(a):
    res = {}
    for np_ in (1, 4):
        with Server(a, ["-np", str(np_)]) as s:
            s.complete("warmup", 8)
            t = time.time()
            with cf.ThreadPoolExecutor(4) as ex:
                outs = list(ex.map(lambda i: s.complete(f"# Task {i}\n" + CODE_PROMPT, 128), range(4)))
            wall = time.time() - t
            toks = sum(o["timings"]["predicted_n"] for o in outs)
            res[f"np{np_}"] = {"wall_s": round(wall, 1), "total_tokens": toks, "agg_tok_s": round(toks / wall, 2),
                               "mean_latency_s": round(sum(o["_wall"] for o in outs) / 4, 1)}
    return res


def e2(a):
    """每种配置各自重启服务器，保证第一次请求是冷启动；两次请求共享同一段前缀，只有结尾的问题不同。"""
    res = {}
    for cache in (False, True):
        with Server(a, ["-np", "1"]) as s:
            x = s.complete(LONG_PREFIX + "\n\nQ1: what does helper_3 return for x=1?\nA:", 16, cache_prompt=cache)
            y = s.complete(LONG_PREFIX + "\n\nQ2: what does helper_5 return for x=2?\nA:", 16, cache_prompt=cache)
            res["cache_on" if cache else "cache_off"] = {
                "first_prompt_ms": round(x["timings"]["prompt_ms"]), "first_prompt_n": x["timings"]["prompt_n"],
                "second_prompt_ms": round(y["timings"]["prompt_ms"]), "second_prompt_n": y["timings"]["prompt_n"],
                "second_cache_n": y["timings"].get("cache_n")}
    return res


def e3(a):
    if not a.draft:
        raise SystemExit("E3 需要 --draft（同一系列的小模型，例如 Qwen3-0.6B）")
    res = {}
    for name, extra in (("baseline", []),
                        ("draft_n3", ["-md", a.draft, "--spec-type", "draft-simple", "--spec-draft-n-max", "3", "--spec-draft-n-min", "1"]),
                        ("draft_n16", ["-md", a.draft, "--spec-type", "draft-simple", "--spec-draft-n-max", "16", "--spec-draft-n-min", "2"])):
        with Server(a, ["-np", "1", *extra]) as s:
            s.complete("warmup", 8)
            tm = s.complete(CODE_PROMPT, 256)["timings"]
            d, acc = tm.get("draft_n"), tm.get("draft_n_accepted")
            res[name] = {"tg_tok_s": round(tm["predicted_per_second"], 2), "predicted_n": tm["predicted_n"],
                         "draft_n": d, "draft_accepted": acc,
                         "accept_rate": round(acc / d, 3) if d else None}
    return res


def e4(a):
    res = {}
    for name, extra in (("kv_f16", ["-fa", "on"]),
                        ("kv_q8_0", ["-fa", "on", "--cache-type-k", "q8_0", "--cache-type-v", "q8_0"])):
        with Server(a, ["-np", "1", *extra], ctx=32768) as s:
            tm = s.complete(LONG_PREFIX + "\n\nSummarize.\nA:", 64, cache_prompt=False)["timings"]
            res[name] = {"rss_mb": s.rss_mb(), "pp_tok_s": round(tm["prompt_per_second"], 1),
                         "tg_tok_s": round(tm["predicted_per_second"], 2)}
    return res


def e5(a):
    bench = str(Path(a.server).with_name("llama-bench"))
    res = {}
    for m in a.model:
        p = subprocess.run([bench, "-m", m, "-t", str(a.threads), "-p", "512", "-n", "128", "-o", "json"],
                           capture_output=True, text=True, check=True)
        rows = json.loads(p.stdout)
        res[Path(m).name] = {("pp512" if r["n_prompt"] else "tg128"): round(r["avg_ts"], 2) for r in rows}
        res[Path(m).name]["size_gb"] = round(rows[0]["model_size"] / 1e9, 2)
    return res


def cpu_name():
    """CPU 型号：/proc/cpuinfo → platform.processor() → "?"。任何异常都不影响结果保存。"""
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as f:
            for l in f:
                if l.startswith("model name"):
                    return l.split(":", 1)[1].strip()
    except OSError:
        pass
    try:
        return platform.processor() or platform.machine() or "?"
    except Exception:
        return "?"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exp", choices=["E1", "E2", "E3", "E4", "E5"], required=True)
    ap.add_argument("--model", action="append", required=True)
    ap.add_argument("--draft")
    ap.add_argument("--server", default=os.environ.get("LLAMA_SERVER", "llama.cpp/build/bin/llama-server"))
    ap.add_argument("--threads", type=int, default=max(1, (os.cpu_count() or 2) // 2))
    ap.add_argument("--port", type=int, default=8099)
    a = ap.parse_args()
    t0 = time.time()
    data = {"E1": e1, "E2": e2, "E3": e3, "E4": e4, "E5": e5}[a.exp](a)
    out = {"exp": a.exp, "model": [Path(m).name for m in a.model], "threads": a.threads,
           "cpu": cpu_name(), "seconds": round(time.time() - t0), "results": data}
    OUT.mkdir(exist_ok=True)
    (OUT / f"{a.exp}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
