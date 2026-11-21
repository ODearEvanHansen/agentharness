#!/usr/bin/env python3
"""作业 5 自动检查（课程小题路由实验）。

先运行（需要 llama-server 在 8091 端口托管本地模型，见 README）：
  export LOCAL_LLM_KEY=$(openssl rand -hex 16)   # 与 llama-server 的 api key 一致；务必在容器内运行
  （命令见 assignment5/README.md：先跑对照组 --tag sdkfull，再跑路由组 --tag a5）
  python assignment5/check.py assignment2/results/mini-dsh-a5.jsonl assignment2/results/mini-dsh-sdkfull.jsonl

检查：8 道小题全部有无错误的记录；解决 ≥ 6/8；至少一半的题目确实把请求路由到了本地模型；
并与同一 profile、不路由的对照组（必须存在且题目齐全）比较云端成本和耗时。
"""
import json, statistics, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from usage_cost import PRICES  # noqa: E402  云端模型 = 有官方价格的模型，其余视为本地

TASKS = {p.name for p in (REPO / "assignment2" / "tasks").iterdir() if p.is_dir()}   # 与 run.py mini_tasks() 一致
ok = True


def check(name, cond, msg):
    global ok
    ok &= bool(cond)
    print(("✅" if cond else "❌"), name, msg)


def load(f: Path, label):
    """读取结果文件（同一题以最后一条为准）；坏行跳过并提示。文件缺失/为空返回 None。"""
    if not f.is_file():
        print(f"❌ {label}：找不到 {f}（先按 README 跑完这一组）")
        return None
    recs, bad = {}, 0
    for line in f.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
            recs[r["id"]] = r
        except (ValueError, KeyError, TypeError):
            bad += 1
    if bad:
        print(f"⚠️  {f}：跳过 {bad} 行无法解析的记录（可能是运行中断导致的半行）")
    if not recs:
        print(f"❌ {label}：{f} 里没有有效记录")
        return None
    return list(recs.values())


def complete(rs, label):
    ids = {r["id"] for r in rs}
    errs = [r["id"] for r in rs if r.get("error")]
    check(label, ids == TASKS and not errs,
          f"记录覆盖全部 {len(TASKS)} 道小题且无错误" + (f"（缺 {sorted(TASKS - ids)}）" if TASKS - ids else "")
          + (f"（多出 {sorted(ids - TASKS)}）" if ids - TASKS else "") + (f"（出错 {errs}，请断点续跑补齐）" if errs else ""))


def split(rs):
    cloud_usd = cloud_req = local_req = 0
    for r in rs:
        for m, v in (r.get("by_model") or {}).items():
            if not isinstance(v, dict):
                continue
            if m in PRICES:
                cloud_usd += v.get("usd", 0); cloud_req += v.get("requests", 0)
            else:
                local_req += v.get("requests", 0)
    return cloud_usd, cloud_req, local_req


def med(rs):
    xs = [r.get("seconds", 0) for r in rs]
    return statistics.median(xs) if xs else 0


def main():
    f = Path(sys.argv[1] if len(sys.argv) > 1 else "assignment2/results/mini-dsh-a5.jsonl")
    base = Path(sys.argv[2]) if len(sys.argv) > 2 else f.with_name("mini-dsh-sdkfull.jsonl")
    rs = load(f, "路由组")
    if rs is None:
        sys.exit(1)
    complete(rs, "L1")
    solved = sum(1 for r in rs if r.get("solved") is True)
    check("L1", solved >= 6, f"解决 {solved}/{len(TASKS)}（要求 ≥ 6）")
    routed = [r for r in rs if any(m not in PRICES and isinstance(v, dict) and v.get("requests", 0) > 0
                                   for m, v in (r.get("by_model") or {}).items())]
    check("L1", len(routed) >= len(TASKS) / 2, f"{len(routed)}/{len(TASKS)} 题有请求路由到本地模型")
    cloud, cloud_req, local_req = split(rs)
    print(f"   云端请求 {cloud_req} 次 ${cloud:.4f}；本地请求 {local_req} 次；中位耗时 {med(rs):.1f}s")
    b = load(base, "对照组")
    if b is None:
        check("对照", False, "缺少对照组结果（同 profile、不路由，--tag sdkfull）")
    else:
        complete(b, "对照")
        bc = sum(r.get("usd", 0) for r in b)
        print(f"   对照（同 profile、不路由）：解决 {sum(1 for r in b if r.get('solved') is True)}/{len(b)}，"
              f"云端 ${bc:.4f}，中位耗时 {med(b):.1f}s")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
