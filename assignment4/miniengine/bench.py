#!/usr/bin/env python3
"""L4 测量：M1 单请求解码速度；M2 静态 vs 连续批处理；M3 分页 vs 连续预留 KV 的内存。结果写 assignment4/results/M*.json。
用法：python assignment4/miniengine/bench.py [--exp M1|M2|M3|all] [--threads 8]"""
import argparse, json, os, platform, sys, time
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--exp", default="all")
ap.add_argument("--threads", type=int, default=8)
ap.add_argument("--model-dir", default=os.environ.get("MINI_MODEL_DIR", Path(__file__).resolve().parents[2] / "models" / "Qwen3-0.6B"))
args = ap.parse_args()
for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[v] = str(args.threads)          # 必须在 import numpy 之前设置

from tokenizers import Tokenizer               # noqa: E402
from model import Qwen3                        # noqa: E402
from engine import Engine, Request             # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "results"
TOPICS = ["the history of the printing press", "how a compiler works", "why the sky is blue", "the rules of chess",
          "how vaccines train the immune system", "the life cycle of a star", "how TCP handles packet loss", "the water cycle"]


def workload(tok):
    """8 个请求，长短交替：短的生成 8 个 token，长的生成 64 个。"""
    return [Request(i, tok.encode(f"Write a short explanation of {t}.").ids, 64 if i % 2 else 8) for i, t in enumerate(TOPICS)]


def summarize(reqs, wall):
    n = sum(len(r.out) for r in reqs)
    return dict(requests=len(reqs), gen_tokens=n, wall_s=round(wall, 2), throughput_tok_s=round(n / wall, 2),
                mean_latency_s=round(sum(r.t_done for r in reqs) / len(reqs), 2),
                mean_ttft_s=round(sum(r.t_first for r in reqs) / len(reqs), 2))


def run(model, reqs, **kw):
    mode = kw.pop("mode")
    e = Engine(model, **kw)
    t = time.perf_counter()
    e.run(reqs, mode)
    return e, summarize(reqs, time.perf_counter() - t)


def main():
    model, tok = Qwen3(args.model_dir), Tokenizer.from_file(str(Path(args.model_dir) / "tokenizer.json"))
    exps = ["M1", "M2", "M3"] if args.exp == "all" else [args.exp]
    OUT.mkdir(exist_ok=True)
    for exp in exps:
        if exp == "M1":
            r = Request(0, tok.encode("The capital of France is").ids, 64)
            _, s = run(model, [r], mode="continuous", max_batch=1)
            res = dict(prompt_tokens=len(r.prompt), gen_tokens=64, ttft_s=round(r.t_first, 3),
                       decode_tok_s=round(63 / (r.t_done - r.t_first), 2))
        elif exp == "M2":
            res = {}
            for mode in ("static", "continuous"):
                e, res[mode] = run(model, workload(tok), mode=mode, max_batch=4)
                res[mode]["steps"] = e.steps
        else:
            res = {}
            for kv in ("contiguous", "paged"):
                e, s = run(model, workload(tok), mode="continuous", max_batch=4, kv=kv, max_len=1024, block_size=16)
                mb = e.bytes_per_token / 2**20
                res[kv] = dict(peak_used_tokens=e.peak_used, peak_reserved_tokens=e.peak_reserved,
                               peak_used_MB=round(e.peak_used * mb, 1), peak_reserved_MB=round(e.peak_reserved * mb, 1),
                               utilization=round(e.peak_used / e.peak_reserved, 3), throughput_tok_s=s["throughput_tok_s"])
        d = dict(exp=exp, threads=args.threads, cpu=platform.processor() or platform.machine(), results=res)
        (OUT / f"{exp}.json").write_text(json.dumps(d, indent=1, ensure_ascii=False))
        print(json.dumps(d, ensure_ascii=False))


if __name__ == "__main__":
    try:
        sys.exit(main())
    except NotImplementedError as e:
        sys.exit(f"❌ 还没实现：{e or '某个 TODO 函数'}。先完成 model.py / engine.py 里的 TODO，再运行 bench.py。")
