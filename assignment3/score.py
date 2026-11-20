#!/usr/bin/env python3
"""作业 3/5 排行榜：把运行记录 + 官方评测报告合成一份提交文件。

  python assignment3/score.py --run assignment2/results/swe-dsh-mine.jsonl \
      --report dsh-mine.<run_id>.json --track efficiency --config-dir assignment3/submission \
      --name 你的昵称 > assignment3/submission/leaderboard.json

  --run     run.py 生成的 jsonl（每题的用量、耗时）
  --report  swebench 官方评测生成的 <model_name>.<run_id>.json
  --track   accuracy（instances_hard.txt）或 efficiency（instances.txt）

提交方式：把 leaderboard.json、patch 和插件放进 assignment3/submission/ 目录，然后向课程仓库发起 PR。
维护者会抽查复现：用你的配置重跑，允许解决数相差 ±2（模型本身有随机性）。
"""
import argparse, hashlib, json, statistics, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TRACKS = {"accuracy": REPO / "infra/swebench/instances_hard.txt", "efficiency": REPO / "infra/swebench/instances.txt"}


def config_hash(d: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(p for p in d.rglob("*") if p.is_file() and p.name != "leaderboard.json"):
        h.update(str(f.relative_to(d)).encode() + b"\0" + f.read_bytes())
    return h.hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--track", choices=TRACKS, required=True)
    ap.add_argument("--config-dir", required=True)
    ap.add_argument("--name", required=True)
    a = ap.parse_args()

    want = [l.strip() for l in open(TRACKS[a.track]) if l.strip() and not l.startswith("#")]
    recs = {r["id"]: r for r in map(json.loads, open(a.run))}
    missing = [i for i in want if i not in recs]
    if missing:
        sys.exit(f"运行记录缺少 {len(missing)} 题，例如 {missing[:3]}（排行榜要求跑完整个题集）")
    report = json.load(open(a.report))
    resolved = sorted(set(report.get("resolved_ids", [])) & set(want))
    rs = [recs[i] for i in want]
    miss, hit = sum(r["input_miss"] for r in rs), sum(r["cache_read"] for r in rs)
    out = {
        "name": a.name, "track": a.track, "n": len(want), "resolved": len(resolved), "resolved_ids": resolved,
        "usd_total": round(sum(r["usd"] for r in rs), 4), "usd_per_task": round(sum(r["usd"] for r in rs) / len(rs), 5),
        "median_seconds": statistics.median(r["seconds"] for r in rs),
        "cache_hit_rate": round(hit / (hit + miss), 3) if hit + miss else 0,
        "models": sorted({r["model"] for r in rs}), "errors": sum(1 for r in rs if r.get("error")),
        "config_sha": config_hash(Path(a.config_dir)), "price_tier": "peak",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
