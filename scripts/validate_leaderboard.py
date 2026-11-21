#!/usr/bin/env python3
"""校验 leaderboard/*.json（字段与 assignment3/score.py 输出一致），并核对随 PR 提交的原始文件。

用法：
  python scripts/validate_leaderboard.py leaderboard/*.json
  python scripts/validate_leaderboard.py [--repo 仓库根] [--instances-dir 题集目录] \
      [--changed <PR 改动的路径...>] -- leaderboard/*.json

--changed 里出现 baseline-*.json（新增/修改/删除）即报错：基线只能由课程团队维护。

每个学员提交 leaderboard/<昵称>-<赛道>.json 都必须附带（由 score.py 自动复制）：
  assignment3/submission/<昵称>/artifacts/run.jsonl          run.py 运行记录
  assignment3/submission/<昵称>/artifacts/predictions.jsonl  导出的 predictions
  assignment3/submission/<昵称>/artifacts/report.json        swebench 官方评测报告
本脚本会重算这三份文件和配置目录的 sha256 并与 JSON 里的值比对，核对 resolved_ids 属于赛道题集且
确实出现在评测报告里，并扫描补丁里是否夹带 API key。
"""
import hashlib, json, re, sys
from pathlib import Path

TRACKS = ("accuracy", "efficiency")
TRACK_FILES = {"accuracy": "instances_hard.txt", "efficiency": "instances.txt"}
EFFICIENCY_MIN = 17
NAME_RE = re.compile(r"^([A-Za-z0-9_.]+(?:-[A-Za-z0-9_.]+)*)-(accuracy|efficiency)\.json$")
BASELINE_RE = re.compile(r"^baseline-\d+\.json$")
KEY_RE = re.compile(r"sk-[A-Za-z0-9]{20,}")
ARTIFACTS = {"run_sha": "run.jsonl", "predictions_sha": "predictions.jsonl", "report_sha": "report.json"}
NUM = (int, float)
# score.py 输出的字段 -> 类型
FIELDS = {
    "name": str, "track": str, "n": int, "resolved": int, "resolved_ids": list,
    "usd_total": NUM, "usd_per_task": NUM, "median_seconds": NUM, "cache_hit_rate": NUM,
    "models": list, "errors": int, "config_sha": str, "price_tier": str,
    "run_sha": str, "predictions_sha": str, "report_sha": str,
}
HEX = re.compile(r"^[0-9a-f]{16,64}$")


def config_hash(d: Path) -> str:
    """与 assignment3/score.py 保持一致：不含 artifacts/ 与 leaderboard.json。"""
    h = hashlib.sha256()
    for f in sorted(p for p in d.rglob("*") if p.is_file() and p.name != "leaderboard.json"
                    and p.relative_to(d).parts[0] != "artifacts"):
        h.update(str(f.relative_to(d)).encode() + b"\0" + f.read_bytes())
    return h.hexdigest()[:16]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read_ids(p: Path):
    return [l.strip() for l in p.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]


def read_jsonl(p: Path):
    out = []
    for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try:
                out.append(json.loads(line))
            except ValueError:
                raise ValueError(f"{p.name} 第 {i} 行不是合法 JSON")
    return out


def bad_type(v, t):
    return isinstance(v, bool) or not isinstance(v, t)


def check_baseline(d):
    errs = [f"缺少字段或类型错误：{k}" for k, t in
            (("name", str), ("track", str), ("n", int), ("resolved", int), ("usd_per_task", NUM)) if bad_type(d.get(k), t)]
    if d.get("track") not in TRACKS:
        errs.append(f"track 必须是 {TRACKS} 之一")
    return errs


def check_artifacts(d, nick, repo: Path, inst_dir: Path, want):
    """核对随 PR 提交的原始文件。返回错误列表。"""
    errs = []
    sub = repo / "assignment3" / "submission" / nick
    art = sub / "artifacts"
    if not sub.is_dir():
        return [f"缺少配置目录 assignment3/submission/{nick}/"]
    if config_hash(sub) != d["config_sha"]:
        errs.append("config_sha 与 assignment3/submission/<昵称>/ 的内容不符（改过配置后请重新运行 score.py）")
    paths = {}
    for k, fn in ARTIFACTS.items():
        p = art / fn
        if not p.is_file() or p.is_symlink():
            errs.append(f"缺少 assignment3/submission/{nick}/artifacts/{fn}（score.py 会自动复制，请一并提交）")
            continue
        if sha(p) != d[k]:
            errs.append(f"{k} 与 artifacts/{fn} 的 sha256 不一致（文件被改过，或不是生成这份 JSON 的那次运行）")
        paths[k] = p
    if len(paths) != len(ARTIFACTS):
        return errs
    try:
        run = read_jsonl(paths["run_sha"])
        preds = read_jsonl(paths["predictions_sha"])
        report = json.loads(paths["report_sha"].read_text(encoding="utf-8"))
    except (ValueError, UnicodeDecodeError) as e:
        return errs + [f"原始文件无法解析：{e}"]
    if not isinstance(report, dict):
        return errs + ["report.json 顶层应为对象"]
    run_ids = {r.get("id") for r in run if isinstance(r, dict) and not r.get("error")}
    if not set(want) <= run_ids:
        errs.append(f"run.jsonl 没有覆盖整个赛道题集（缺 {len(set(want) - run_ids)} 题或有出错记录）")
    pred_ids = {p.get("instance_id") for p in preds if isinstance(p, dict)}
    if not set(want) <= pred_ids:
        errs.append("predictions.jsonl 没有覆盖整个赛道题集")
    rep_resolved = set(report.get("resolved_ids") or [])
    if not set(d["resolved_ids"]) <= rep_resolved:
        errs.append("resolved_ids 里有评测报告中未解决的题")
    if sorted(rep_resolved & set(want)) != sorted(d["resolved_ids"]):
        errs.append("resolved_ids 与评测报告不一致")
    for rec in [*preds, *run]:
        if isinstance(rec, dict) and KEY_RE.search(str(rec.get("model_patch") or "")):
            errs.append(f"{rec.get('instance_id') or rec.get('id')} 的 model_patch 里疑似含 API key（sk-...），"
                        "请立即作废该 key，并去掉后重新提交")
            break
    for f in sub.rglob("*"):
        if f.is_file() and f.stat().st_size < 5_000_000:
            try:
                if KEY_RE.search(f.read_text(encoding="utf-8", errors="ignore")):
                    errs.append(f"{f.relative_to(repo)} 疑似含 API key（sk-...）")
            except OSError:
                pass
    return errs


def check_entry(p: Path, d, repo: Path, inst_dir: Path):
    m = NAME_RE.match(p.name)
    if not m:
        return ["文件名应为 <昵称>-<赛道>.json，赛道为 accuracy 或 efficiency（昵称只含字母、数字、_ . -）"]
    errs = [f"缺少字段：{k}" if k not in d else f"字段类型错误：{k}"
            for k, t in FIELDS.items() if bad_type(d.get(k), t)]
    if errs:
        return errs
    nick = m.group(1)
    if d["name"] != nick:
        errs.append(f"name 字段 {d['name']} 与文件名里的昵称 {nick} 不一致")
    if "baseline" in d:
        errs.append("学员提交不能带 baseline 字段")
    if d["track"] not in TRACKS:
        return errs + [f"track 必须是 {TRACKS} 之一"]
    if d["track"] != m.group(2):
        errs.append(f"文件名赛道 {m.group(2)} 与 track 字段 {d['track']} 不一致")
    want = read_ids(inst_dir / TRACK_FILES[d["track"]])
    if d["n"] != len(want):
        errs.append(f"n 应为 {len(want)}（赛道题集大小），实际 {d['n']}")
    if not 0 <= d["resolved"] <= d["n"]:
        errs.append("resolved 超出范围")
    ids = d["resolved_ids"]
    if not all(isinstance(i, str) for i in ids) or len(set(ids)) != d["resolved"] or len(ids) != d["resolved"]:
        errs.append("resolved_ids 数量与 resolved 不一致或有重复")
    fake = [i for i in ids if i not in set(want)]
    if fake:
        errs.append(f"resolved_ids 里有不属于 {d['track']} 赛道题集的题：{fake[:3]}")
    if d["track"] == "efficiency" and d["resolved"] < EFFICIENCY_MIN:
        errs.append(f"效率赛道要求解决数 ≥ {EFFICIENCY_MIN}，实际 {d['resolved']}")
    if not HEX.match(d["config_sha"]):
        errs.append("config_sha 缺失或格式不对（应为 score.py 生成的十六进制哈希）")
    for k in ARTIFACTS:
        if not HEX.match(d[k]):
            errs.append(f"{k} 格式不对")
    if d["price_tier"] != "peak":
        errs.append("price_tier 应为 peak（按高峰价计）")
    if not d["models"]:
        errs.append("models 不能为空")
    if min(d["usd_total"], d["usd_per_task"], d["median_seconds"]) < 0 or not 0 <= d["cache_hit_rate"] <= 1:
        errs.append("数值超出合理范围")
    if errs:
        return errs
    return check_artifacts(d, nick, repo, inst_dir, want)


def main(argv):
    repo = Path(__file__).resolve().parent.parent
    inst_dir = None
    changed, files = [], []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--repo":
            repo = Path(argv[i + 1]).resolve(); i += 2
        elif a == "--instances-dir":
            inst_dir = Path(argv[i + 1]); i += 2
        elif a == "--changed":
            j = argv.index("--", i) if "--" in argv[i:] else len(argv)
            changed, files = argv[i + 1:j], argv[j + 1:]
            break
        elif a == "--":
            files = argv[i + 1:]
            break
        else:
            files = argv[i:]
            break
    inst_dir = inst_dir or repo / "infra" / "swebench"
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
        try:
            errs = check_baseline(d) if BASELINE_RE.match(p.name) else check_entry(p, d, repo, inst_dir)
        except Exception as e:  # 防御：任何意外都算不通过，而不是崩溃
            errs = [f"校验出错：{type(e).__name__}: {e}"]
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
