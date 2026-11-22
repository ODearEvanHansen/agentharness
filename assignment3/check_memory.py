#!/usr/bin/env python3
"""作业 3 选做 L6：检查记忆笔记有没有「泄题」。

  python assignment3/check_memory.py assignment3/submission/<昵称>/memory-notes [--dataset infra/swebench/dataset.json]

对题集里每道题的参考补丁（gold patch，只用于检查，不会给 agent 看）做三项比对：
  1. 笔记里出现题号或 issue 编号（例如 django-10914、#10914）
  2. 笔记里出现参考补丁改动的文件路径（例如 django/conf/global_settings.py）
  3. 笔记里出现参考补丁新增的代码行（去掉空白后 ≥ 12 个字符的行）
第 1、3 项命中直接判为泄题（退出码 1）；第 2 项是警告：仓库布局说明难免提到常用文件，
但提到「恰好要改的那个文件」就是在暗示答案，请改成目录级描述或删掉。
"""
import argparse, json, re, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("notes_dir")
    ap.add_argument("--dataset", action="append", help="默认同时检查 dataset.json 和 dataset_hard.json")
    a = ap.parse_args()
    notes = {p.name: p.read_text(encoding="utf-8") for p in sorted(Path(a.notes_dir).glob("*.md"))}
    if not notes:
        sys.exit(f"{a.notes_dir} 下没有 .md 笔记")
    blob = "\n".join(notes.values())
    flat = re.sub(r"\s+", "", blob)
    dsets = a.dataset or [REPO / "infra/swebench/dataset.json", REPO / "infra/swebench/dataset_hard.json"]
    leaks, warns = [], []
    for ds in dsets:
        for r in json.loads(Path(ds).read_text(encoding="utf-8")):
            iid, patch = r["instance_id"], r["patch"]
            num = iid.rsplit("-", 1)[-1]
            if iid in blob or re.search(rf"(#|-){num}\b", blob):
                leaks.append(f"{iid}: 笔记里出现了题号 {num}")
            for f in sorted(set(re.findall(r"^\+\+\+ b/(\S+)", patch, re.M))):
                if f in blob:
                    warns.append(f"{iid}: 笔记提到了参考补丁要改的文件 {f}")
            for line in patch.splitlines():
                if line.startswith("+") and not line.startswith("+++"):
                    s = re.sub(r"\s+", "", line[1:])
                    if len(s) >= 12 and s in flat:
                        leaks.append(f"{iid}: 笔记里出现了参考补丁的新增代码 {line[1:].strip()[:60]!r}")
    for w in warns:
        print("警告", w)
    for l in leaks:
        print("泄题", l)
    print(f"检查了 {len(notes)} 个笔记文件：泄题 {len(leaks)} 处，警告 {len(warns)} 处")
    sys.exit(1 if leaks else 0)


if __name__ == "__main__":
    main()
