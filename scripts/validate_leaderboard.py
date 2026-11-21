#!/usr/bin/env python3
"""校验 leaderboard/*.json（字段与 assignment3/score.py 输出一致）。

用法：
  python scripts/validate_leaderboard.py leaderboard/*.json
  python scripts/validate_leaderboard.py --changed <PR 改动的路径...> -- leaderboard/*.json
--changed 里出现 baseline-*.json（新增/修改/删除）即报错：基线只能由课程团队维护。
"""
import json, re, sys
from pathlib import Path

TRACKS = ("accuracy", "efficiency")
EFFICIENCY_MIN = 17
NAME_RE = re.compile(r"^([A-Za-z0-9_.]+(?:-[A-Za-z0-9_.]+)*)-(accuracy|efficiency)\.json$")
BASELINE_RE = re.compile(r"^baseline-\d+\.json$")
NUM = (int, float)
# score.py 输出的字段 -> 类型
FIELDS = {
    "name": str, "track": str, "n": int, "resolved": int, "resolved_ids": list,
    "usd_total": NUM, "usd_per_task": NUM, "median_seconds": NUM, "cache_hit_rate": NUM,
    "models": list, "errors": int, "config_sha": str, "price_tier": str,
    "run_sha": str, "report_sha": str,
}
HEX = re.compile(r"^[0-9a-f]{16,64}$")


def bad_type(v, t):
    return isinstance(v, bool) or not isinstance(v, t)


def check_baseline(d):
    errs = [f"缺少字段或类型错误：{k}" for k, t in
            (("name", str), ("track", str), ("n", int), ("resolved", int), ("usd_per_task", NUM)) if bad_type(d.get(k), t)]
    if d.get("track") not in TRACKS:
        errs.append(f"track 必须是 {TRACKS} 之一")
    return errs


def check_entry(p: Path, d):
    m = NAME_RE.match(p.name)
    if not m:
        return ["文件名应为 <昵称>-<赛道>.json，赛道为 accuracy 或 efficiency（昵称只含字母、数字、_ . -）"]
    errs = [f"缺少字段：{k}" if k not in d else f"字段类型错误：{k}"
            for k, t in FIELDS.items() if bad_type(d.get(k), t)]
    if errs:
        return errs
    if "baseline" in d:
        errs.append("学员提交不能带 baseline 字段")
    if d["track"] not in TRACKS:
        errs.append(f"track 必须是 {TRACKS} 之一")
    elif d["track"] != m.group(2):
        errs.append(f"文件名赛道 {m.group(2)} 与 track 字段 {d['track']} 不一致")
    if d["n"] != 20:
        errs.append(f"n 应为 20（赛道题集大小），实际 {d['n']}")
    if not 0 <= d["resolved"] <= d["n"]:
        errs.append("resolved 超出范围")
    if len(set(d["resolved_ids"])) != d["resolved"] or len(d["resolved_ids"]) != d["resolved"]:
        errs.append("resolved_ids 数量与 resolved 不一致或有重复")
    if d["track"] == "efficiency" and d["resolved"] < EFFICIENCY_MIN:
        errs.append(f"效率赛道要求解决数 ≥ {EFFICIENCY_MIN}，实际 {d['resolved']}")
    if not HEX.match(d["config_sha"]):
        errs.append("config_sha 缺失或格式不对（应为 score.py 生成的十六进制哈希）")
    for k in ("run_sha", "report_sha"):
        if not HEX.match(d[k]):
            errs.append(f"{k} 格式不对")
    if d["price_tier"] != "peak":
        errs.append("price_tier 应为 peak（按高峰价计）")
    if not d["models"]:
        errs.append("models 不能为空")
    if min(d["usd_total"], d["usd_per_task"], d["median_seconds"]) < 0 or not 0 <= d["cache_hit_rate"] <= 1:
        errs.append("数值超出合理范围")
    return errs


def main(argv):
    changed, files = [], argv
    if argv and argv[0] == "--changed":
        sep = argv.index("--") if "--" in argv else len(argv)
        changed, files = argv[1:sep], argv[sep + 1:]
    bad = 0
    for c in changed:
        if BASELINE_RE.match(Path(c).name):
            print(f"✗ {c}: 不允许在 PR 中修改 baseline-*.json")
            bad += 1
    for f in files:
        p = Path(f)
        if p.suffix != ".json":
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"✗ {p}: 不是合法 JSON（{e}）"); bad += 1; continue
        if not isinstance(d, dict):
            print(f"✗ {p}: 顶层应为对象"); bad += 1; continue
        errs = check_baseline(d) if BASELINE_RE.match(p.name) else check_entry(p, d)
        for e in errs:
            print(f"✗ {p}: {e}")
        if errs:
            bad += 1
        else:
            print(f"✓ {p}")
    if bad:
        print(f"\n共 {bad} 处问题")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
