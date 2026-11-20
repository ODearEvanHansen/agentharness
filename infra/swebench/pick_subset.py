#!/usr/bin/env python3
"""Pick a reproducible 20-task subset of SWE-bench Verified for M0 cost baselining.

Stratified by difficulty label (Verified annotations): 10 "<15 min fix", 8 "15 min - 1 hour",
2 "1-4 hours"; at most 3 per repo; fixed seed. Writes swe_subset.json.
"""
import json, random
from collections import Counter, defaultdict
from datasets import load_dataset

ds = load_dataset("princeton-nlp/SWE-bench_Verified", split="test")
by = defaultdict(list)
for r in ds:
    by[r["difficulty"]].append(r)
print({k: len(v) for k, v in by.items()})
rng = random.Random(2680)
want = {"<15 min fix": 10, "15 min - 1 hour": 8, "1-4 hours": 2}
picked, per_repo = [], Counter()
for diff, n in want.items():
    pool = by[diff][:]
    rng.shuffle(pool)
    for r in pool:
        if sum(1 for p in picked if p["difficulty"] == diff) >= n:
            break
        if per_repo[r["repo"]] >= 3:
            continue
        per_repo[r["repo"]] += 1
        picked.append(r)
out = [{k: r[k] for k in ("instance_id", "repo", "difficulty", "problem_statement", "base_commit")} for r in picked]
json.dump(out, open("swe_subset.json", "w"), ensure_ascii=False, indent=1)
print(len(out), Counter(r["repo"] for r in out))
for r in out:
    print(r["difficulty"], r["instance_id"])
