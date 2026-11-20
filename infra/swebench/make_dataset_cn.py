#!/usr/bin/env python3
"""生成"国内镜像版"SWE-bench 数据集 JSON：把每个实例的 image 字段改成 ACR 地址。

学员用法（无需重新打 tag，官方评测直接读本地 JSON）：
  python make_dataset_cn.py --instances instances.txt --out swe_verified_cn.json
  python -m swebench.harness.run_evaluation -d swe_verified_cn.json -p predictions.jsonl -id run1
  （拉取镜像走 ACR；数据集本身也可由课程方生成后随课程仓库分发，学员就不必访问 Hugging Face）
"""
import argparse, json
from datasets import load_dataset

ap = argparse.ArgumentParser()
ap.add_argument("--repo", default="crpi-wuyoxje33x46jb9c.cn-hangzhou.personal.cr.aliyuncs.com/agentharness/swebench-x86_64",
                help="完整仓库地址（不含 tag）")
ap.add_argument("--instances", help="只保留列表中的实例（每行一个 instance_id）")
ap.add_argument("--dataset", default="SWE-bench/SWE-bench_Verified")
ap.add_argument("--out", default="swe_verified_cn.json")
a = ap.parse_args()

keep = None
if a.instances:
    keep = {l.strip() for l in open(a.instances) if l.strip()}
rows = []
for r in load_dataset(a.dataset, split="test"):
    if keep is not None and r["instance_id"] not in keep:
        continue
    r = dict(r)
    suffix = r["instance_id"].replace("__", "_1776_")
    r["image_upstream"] = r.get("image")
    r["image"] = f"{a.repo}:{suffix}"
    rows.append(r)
json.dump(rows, open(a.out, "w"), ensure_ascii=False)
print(f"{len(rows)} instances -> {a.out}; example image: {rows[0]['image'] if rows else '-'}")
if keep is not None and len(rows) != len(keep):
    print("WARNING: missing instances:", sorted(keep - {r['instance_id'] for r in rows}))
