#!/usr/bin/env python3
"""作业 3/5 排行榜：把运行记录 + 官方评测报告合成一份提交文件。

  python assignment3/score.py --run assignment2/results/swe-dsh-<昵称>.jsonl \
      --report dsh-<昵称>.<run_id>.json --track efficiency --config-dir assignment3/submission/<昵称> \
      --name <昵称> > leaderboard/<昵称>-efficiency.json

  --run     run.py 生成的 jsonl（每题的用量、耗时）
  --report  swebench 官方评测生成的 <model_name>.<run_id>.json
  --track   accuracy（instances_hard.txt）或 efficiency（instances.txt）

提交方式：leaderboard/<昵称>-<赛道>.json 加上 assignment3/submission/<昵称>/（patch、插件、BLOG.md），向课程仓库发起 PR。
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
    errs = [i for i in want if recs[i].get("error")]
    if errs:
        sys.exit(f"有 {len(errs)} 题运行出错（例如 {errs[:3]}）：请用 run.py 断点续跑把它们补跑成功后再提交")
    names = {r.get("model_name_or_path") for r in recs.values() if r.get("model_name_or_path")}
    report = json.load(open(a.report))
    rep_ids = set(report.get("submitted_ids", [])) or set(report.get("completed_ids", [])) | set(report.get("empty_patch_ids", []))
    if rep_ids and not set(want) <= rep_ids | set(report.get("empty_patch_ids", [])) | set(report.get("error_ids", [])):
        sys.exit("评测报告与赛道题集不符：请用该赛道对应的数据集（dataset.json / dataset_hard.json）评测")
    tag = Path(a.run).stem.split("-", 2)[-1] if Path(a.run).stem.count("-") >= 2 else ""
    if tag and tag not in Path(a.report).name:
        print(f"警告：报告文件名 {Path(a.report).name} 与运行记录标签 {tag} 不一致，请确认没有拿错报告", file=sys.stderr)
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
        "run_sha": hashlib.sha256(Path(a.run).read_bytes()).hexdigest()[:16],
        "report_sha": hashlib.sha256(Path(a.report).read_bytes()).hexdigest()[:16],
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
