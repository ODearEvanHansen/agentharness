#!/usr/bin/env python3
"""作业 3 排行榜：把运行记录 + predictions + 官方评测报告合成一份提交文件。

  python assignment3/score.py --run assignment2/results/swe-dsh-<昵称>.jsonl \\
      --report assignment2/results/dsh-<昵称>.<run_id>.json --track efficiency \\
      --config-dir assignment3/submission/<昵称> --name <昵称> > leaderboard/<昵称>-efficiency.json

  --run          run.py 生成的 jsonl（每题的用量、耗时）
  --predictions  run.py 导出的 predictions（默认：与 --run 同目录的 predictions-<agent>-<tag>.jsonl）
  --report       swebench 官方评测生成的 <model_name_or_path>.<run_id>.json
  --track        accuracy（instances_hard.txt）或 efficiency（instances.txt）

score.py 会把三份原始文件复制到 <config-dir>/artifacts/（run.jsonl、predictions.jsonl、report.json），
它们要和 leaderboard JSON 一起提交；CI 会重算 sha256 核对。artifacts/ 不计入 config_sha。
维护者会抽查复现（尤其是排名靠前的提交）：用你的配置重跑，允许解决数相差 ±2（模型本身有随机性）。
"""
import argparse, hashlib, json, shutil, statistics, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import usage_cost  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
TRACKS = {"accuracy": REPO / "infra/swebench/instances_hard.txt", "efficiency": REPO / "infra/swebench/instances.txt"}


def config_hash(d: Path) -> str:
    """与 scripts/validate_leaderboard.py 保持一致：不含 artifacts/ 与 leaderboard.json。"""
    h = hashlib.sha256()
    for f in sorted(p for p in d.rglob("*") if p.is_file() and p.name != "leaderboard.json"
                    and p.relative_to(d).parts[0] != "artifacts"):
        h.update(str(f.relative_to(d)).encode() + b"\0" + f.read_bytes())
    return h.hexdigest()[:16]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read_jsonl(p: Path):
    out = []
    for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                out.append(json.loads(line))
            except ValueError:
                sys.exit(f"{p} 第 {i} 行不是合法 JSON：文件可能被截断，请用 run.py 断点续跑补齐后再生成")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--predictions")
    ap.add_argument("--report", required=True)
    ap.add_argument("--track", choices=TRACKS, required=True)
    ap.add_argument("--config-dir", required=True)
    ap.add_argument("--name", required=True)
    a = ap.parse_args()
    run_p, rep_p, cfg = Path(a.run), Path(a.report), Path(a.config_dir)
    pred_p = Path(a.predictions) if a.predictions else run_p.with_name(run_p.name.replace("swe-", "predictions-", 1))
    for p in (run_p, pred_p, rep_p):
        if not p.is_file():
            sys.exit(f"找不到文件 {p}")
    if not cfg.is_dir():
        sys.exit(f"找不到配置目录 {cfg}")

    want = [l.strip() for l in TRACKS[a.track].read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    recs = {r["id"]: r for r in read_jsonl(run_p)}
    missing = [i for i in want if i not in recs]
    if missing:
        sys.exit(f"运行记录缺少 {len(missing)} 题，例如 {missing[:3]}（排行榜要求跑完整个题集）")
    errs = [i for i in want if recs[i].get("error")]
    if errs:
        sys.exit(f"有 {len(errs)} 题运行出错（例如 {errs[:3]}）：请用 run.py 断点续跑把它们补跑成功后再提交")

    # 核对 predictions / 报告确实来自这次运行：model_name_or_path = <agent>-<tag>，报告名 = <model_name_or_path>.<run_id>.json
    preds = read_jsonl(pred_p)
    names = {p.get("model_name_or_path") for p in preds}
    agents = {r.get("agent") for r in recs.values()}
    expect = run_p.stem[len("swe-"):] if run_p.stem.startswith("swe-") else None
    if len(names) != 1 or (expect and names != {expect}):
        sys.exit(f"predictions 的 model_name_or_path={sorted(map(str, names))} 与运行记录 {run_p.name} 不对应（应为 {expect}）")
    model_name = names.pop()
    if not any(model_name == ag or model_name.startswith(f"{ag}-") for ag in agents):
        sys.exit(f"predictions 的 model_name_or_path={model_name} 与运行记录里的 agent {sorted(map(str, agents))} 不对应")
    if not rep_p.name.startswith(model_name + ".") or rep_p.suffix != ".json":
        sys.exit(f"评测报告 {rep_p.name} 不是 {model_name}.<run_id>.json：请确认没有拿错报告（-p 用的是这次的 predictions）")
    if not set(want) <= {p.get("instance_id") for p in preds}:
        sys.exit("predictions 没有覆盖整个赛道题集")
    try:
        report = json.loads(rep_p.read_text(encoding="utf-8"))
    except ValueError as e:
        sys.exit(f"评测报告不是合法 JSON：{e}")
    rep_ids = set(report.get("submitted_ids", [])) or set(report.get("completed_ids", [])) | set(report.get("empty_patch_ids", []))
    if not rep_ids or not set(want) <= rep_ids | set(report.get("error_ids", [])):
        sys.exit("评测报告与赛道题集不符：请用该赛道对应的数据集（dataset.json / dataset_hard.json）评测")

    resolved = sorted(set(report.get("resolved_ids", [])) & set(want))
    rs = [recs[i] for i in want]
    miss, hit = sum(r["input_miss"] for r in rs), sum(r["cache_read"] for r in rs)
    cny = sum(usage_cost.record_cny(r) for r in rs)
    usd = sum(r.get("usd") or 0 for r in rs)  # 已弃用，仅为兼容旧字段

    art = cfg / "artifacts"
    art.mkdir(exist_ok=True)
    for src, fn in ((run_p, "run.jsonl"), (pred_p, "predictions.jsonl"), (rep_p, "report.json")):
        if src.resolve() != (art / fn).resolve():
            shutil.copyfile(src, art / fn)
    out = {
        "name": a.name, "track": a.track, "n": len(want), "resolved": len(resolved), "resolved_ids": resolved,
        "cny_total": round(cny, 4), "cny_per_task": round(cny / len(rs), 5),
        "usd_total": round(usd, 4), "usd_per_task": round(usd / len(rs), 5),
        "median_seconds": statistics.median(r["seconds"] for r in rs),
        "cache_hit_rate": round(hit / (hit + miss), 3) if hit + miss else 0,
        "models": sorted({r["model"] for r in rs}), "errors": 0,
        "config_sha": config_hash(cfg), "price_tier": "peak",
        "run_sha": sha(art / "run.jsonl"),
        "predictions_sha": sha(art / "predictions.jsonl"),
        "report_sha": sha(art / "report.json"),
    }
    print(f"已复制原始文件到 {art}/，请和 leaderboard JSON 一起提交", file=sys.stderr)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
