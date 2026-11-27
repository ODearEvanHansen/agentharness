#!/usr/bin/env python3
"""选做：无 agent 基线（no-agent baseline）——同一个模型，不给工具、不循环，一次请求直接作答。

  python assignment2/noagent.py --suite swe                 # SWE 子集：一次请求 → unified diff → predictions → 官方评测
  python assignment2/noagent.py --suite swe --judge         # 同上，并直接调用官方评测、汇总解决率
  （小题必须在运行器容器里跑，命令见 assignment2/README.md「选做：无 agent 基线」）
  python assignment2/noagent.py --suite mini

SWE 设定是 SWE-bench 论文里的 "oracle retrieval"：把金标准补丁改动到的文件全文直接塞给模型。
现实中用户并不知道该改哪些文件，所以这是无 agent 方案的**宽松上界**。
文件内容按 base_commit 从 GitHub raw 下载（缓存在 results/noagent/oracle_cache/），
国内访问不了时可设置 AH_RAW_BASE 指向镜像（形如 https://<mirror>/{repo}/{commit}/{path}）。

小题设定：题面 + 题目目录里所有文件全文，模型按固定格式返回改动后的完整文件；
只采纳对原有源文件（不含 test_task.py）的修改，在干净副本里运行 test_task.py 判分（与 run.py 相同）。
"""
import argparse, concurrent.futures as cf, json, os, re, shutil, statistics, subprocess, sys, tempfile, time
import urllib.error, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path[:0] = [str(REPO / "tools")]
import usage_cost  # noqa: E402

API = os.environ.get("MINI_API", "https://api.deepseek.com/chat/completions")
RAW = os.environ.get("AH_RAW_BASE", "https://raw.githubusercontent.com/{repo}/{commit}/{path}")

SWE_PROMPT = """You are given a GitHub issue and the full contents of the relevant source files of the repository.
Write a patch that resolves the issue. Do not modify tests.
Reply with a single unified diff (as produced by `git diff`, paths prefixed a/ and b/, with correct @@ hunk headers
and enough context lines) inside one ```diff code block. Output nothing else after the code block.

<issue>
{issue}
</issue>

{files}"""

MINI_PROMPT = """You are given a small programming task and every file in its directory. You cannot run anything.
Solve the task by rewriting source files. Do not modify test_task.py.
For every file you change, output its COMPLETE new content in exactly this format (nothing else is parsed):

=== FILE: <relative path> ===
<full file content>
=== END FILE ===

<task>
{task}
</task>

{files}"""


def chat(prompt, model, max_tokens):
    body = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens}
    req = urllib.request.Request(API, data=json.dumps(body).encode(), headers={
        "Authorization": f"Bearer {os.environ['DEEPSEEK_API_KEY']}", "Content-Type": "application/json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=900) as r:
                return json.loads(r.read())
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt == 3:
                raise
            print(f"  请求失败（{e}），重试…", file=sys.stderr, flush=True)
            time.sleep(5 * (attempt + 1))


def usage_of(resp, model):
    u = resp.get("usage") or {}
    rec = {"requests": 1, "input_miss": u.get("prompt_cache_miss_tokens", u.get("prompt_tokens", 0)),
           "cache_read": u.get("prompt_cache_hit_tokens", 0), "output": u.get("completion_tokens", 0),
           "prompt_tokens": u.get("prompt_tokens", 0)}
    hit, miss, out = usage_cost.PRICES.get(model, {"peak": (0, 0, 0)})["peak"]   # 与 run.py 一样按高峰价
    rec["cny"] = round((rec["input_miss"] * miss + rec["cache_read"] * hit + rec["output"] * out) / 1e6, 6)
    return rec


def fence(path, text):
    return f'<file path="{path}">\n{text}\n</file>'


# ---------------- SWE ----------------
def load_ds():
    ds = {}
    for f in sorted((REPO / "infra" / "swebench").glob("dataset*.json")):
        ds.update({r["instance_id"]: r for r in json.loads(f.read_text(encoding="utf-8"))})
    return ds


def oracle_files(inst, cache):
    paths = re.findall(r"^diff --git a/(\S+) b/", inst["patch"], flags=re.M)
    out = []
    for p in dict.fromkeys(paths):
        c = cache / inst["instance_id"] / p
        if not c.exists():
            url = RAW.format(repo=inst["repo"], commit=inst["base_commit"], path=p)
            try:
                with urllib.request.urlopen(url, timeout=60) as r:
                    data = r.read()
            except urllib.error.HTTPError as e:
                if e.code == 404:          # 补丁新建的文件
                    continue
                raise
            c.parent.mkdir(parents=True, exist_ok=True)
            c.write_bytes(data)
        out.append((p, c.read_text(encoding="utf-8", errors="replace")))
    return out


def extract_diff(text, oracle_paths=()):
    blocks = re.findall(r"```(?:diff|patch)?[^\n]*\n(.*?)```", text, flags=re.S)
    cand = [b for b in blocks if "--- " in b and "+++ " in b] or ([text] if "--- " in text else [])
    if not cand and len(oracle_paths) == 1:
        # 模型常漏掉 ---/+++ 文件头只给 @@ 块；只有一个 oracle 文件时文件是确定的，补上文件头
        hunks = [b for b in blocks if re.search(r"^@@ ", b, flags=re.M)]
        if hunks:
            p = oracle_paths[0]
            cand = [f"--- a/{p}\n+++ b/{p}\n" + max(hunks, key=len)]
    if not cand:
        return ""
    d = max(cand, key=len)
    if not d.lstrip().startswith("diff --git"):      # 只有 ---/+++ 时补上 git 头，官方评测的 git apply 更稳
        d = re.sub(r"^--- (?:a/)?(\S+).*\n\+\+\+ (?:b/)?(\S+).*$",
                   lambda m: f"diff --git a/{m[1]} b/{m[2]}\n--- a/{m[1]}\n+++ b/{m[2]}", d, flags=re.M)
    return d if d.endswith("\n") else d + "\n"


def run_swe_one(iid, ds, model, outdir, max_tokens):
    inst = ds[iid]
    files = oracle_files(inst, outdir / "oracle_cache")
    prompt = SWE_PROMPT.format(issue=inst["problem_statement"], files="\n\n".join(fence(p, t) for p, t in files))
    resp = chat(prompt, model, max_tokens)
    msg = resp["choices"][0]["message"]
    (outdir / "raw").mkdir(parents=True, exist_ok=True)
    (outdir / "raw" / f"{iid}.json").write_text(json.dumps(resp, ensure_ascii=False, indent=1), encoding="utf-8")
    patch = extract_diff(msg.get("content") or "", [p for p, _ in files])
    return {"solved": None, "usage": usage_of(resp, model), "model_patch": patch,
            "finish_reason": resp["choices"][0].get("finish_reason"), "oracle_files": [p for p, _ in files]}


def judge_swe(preds, run_id, ds_file, outdir):
    """与 README 相同的官方评测：python -m swebench.harness.run_evaluation（镜像取 dataset.json 里的 GHCR image）。"""
    cmd = [os.environ.get("SWE_PYTHON", sys.executable), "-m", "swebench.harness.run_evaluation",
           "-d", str(ds_file), "-p", str(preds), "-id", run_id, "--max_workers", os.environ.get("SWE_WORKERS", "4")]
    print("判分：", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=REPO, check=False)
    reps = list(REPO.glob(f"*.{run_id}.json"))
    if not reps:
        print("没找到评测报告", file=sys.stderr)
        return None
    rep = outdir / reps[0].name
    shutil.move(str(reps[0]), rep)
    return set(json.loads(rep.read_text())["resolved_ids"])


# ---------------- mini ----------------
def in_container():
    if Path("/var/run/docker.sock").exists():
        return False
    return Path("/.dockerenv").exists() or os.environ.get("AH_IN_CONTAINER") == "1"


def run_mini_one(tid, tasks_dir, model, outdir, max_tokens):
    src = tasks_dir / tid
    files = {str(f.relative_to(src)): f.read_text(encoding="utf-8") for f in sorted(src.rglob("*"))
             if f.is_file() and "__pycache__" not in f.parts and f.name != "PROMPT.txt"}
    prompt = MINI_PROMPT.format(task=(src / "PROMPT.txt").read_text(encoding="utf-8"),
                                files="\n\n".join(fence(p, t) for p, t in files.items()))
    resp = chat(prompt, model, max_tokens)
    text = resp["choices"][0]["message"].get("content") or ""
    (outdir / "raw").mkdir(parents=True, exist_ok=True)
    (outdir / "raw" / f"{tid}.json").write_text(json.dumps(resp, ensure_ascii=False, indent=1), encoding="utf-8")
    edits = {p.strip(): c for p, c in re.findall(r"=== FILE: (.+?) ===\n(.*?)\n?=== END FILE ===", text, flags=re.S)}
    with tempfile.TemporaryDirectory() as tmp:
        judge = Path(tmp) / tid
        shutil.copytree(src, judge)
        applied = []
        for p, c in edits.items():
            if p in files and p != "test_task.py":     # 只采纳对原有源文件的修改
                (judge / p).write_text(c if c.endswith("\n") else c + "\n", encoding="utf-8")
                applied.append(p)
        try:
            r = subprocess.run([sys.executable, "test_task.py"], cwd=judge, capture_output=True, text=True, timeout=60)
            ok, tail = r.returncode == 0, (r.stdout + r.stderr)[-500:]
        except subprocess.TimeoutExpired:
            ok, tail = False, "timeout"
    return {"solved": ok, "usage": usage_of(resp, model), "applied": applied, "test_tail": tail,
            "finish_reason": resp["choices"][0].get("finish_reason")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", choices=["mini", "swe"], required=True)
    ap.add_argument("--instances", default=str(REPO / "infra" / "swebench" / "instances.txt"))
    ap.add_argument("--suite-dir", default=str(HERE / "tasks"))
    ap.add_argument("--model", default=os.environ.get("MODEL", "deepseek-flash"))
    ap.add_argument("--parallel", type=int, default=4)
    ap.add_argument("--max-tokens", type=int, default=32768)
    ap.add_argument("--out", default=str(HERE / "results" / "noagent"))
    ap.add_argument("--tag", default="")
    ap.add_argument("--judge", action="store_true", help="SWE：生成 predictions 后直接跑官方评测")
    a = ap.parse_args()
    if "DEEPSEEK_API_KEY" not in os.environ:
        sys.exit("请先设置 DEEPSEEK_API_KEY")
    tag = f"-{a.tag}" if a.tag else ""
    outdir = Path(a.out) / f"{a.suite}{tag}"
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / f"{a.suite}-noagent{tag}.jsonl"
    out.unlink(missing_ok=True)

    if a.suite == "mini":
        if not in_container():
            sys.exit("小题判分会在本机执行模型写的代码，必须在运行器容器里跑（见 assignment2/README.md「选做：无 agent 基线」）。")
        tdir = Path(a.suite_dir)
        ids = [p.name for p in sorted(tdir.iterdir()) if p.is_dir()]
        fn = lambda i: run_mini_one(i, tdir, a.model, outdir, a.max_tokens)  # noqa: E731
    else:
        ds = load_ds()
        ids = [l.strip() for l in open(a.instances, encoding="utf-8") if l.strip() and not l.startswith("#")]
        fn = lambda i: run_swe_one(i, ds, a.model, outdir, a.max_tokens)  # noqa: E731

    recs = {}

    def one(i):
        t0 = time.time()
        try:
            r, err = fn(i), None
        except Exception as e:
            r, err = {"solved": False if a.suite == "mini" else None, "usage": {"cny": 0}}, f"{type(e).__name__}: {str(e)[:300]}"
        rec = {"id": i, "agent": "noagent", "model": a.model, "seconds": round(time.time() - t0, 1),
               "solved": r["solved"], "steps": 1, "tool_calls": 0, **r["usage"], "error": err,
               **{k: v for k, v in r.items() if k not in ("solved", "usage")}}
        recs[i] = rec
        print(f"{i:40} solved={rec['solved']!s:5} {rec['seconds']:7}s prompt={rec.get('prompt_tokens', 0):6} "
              f"out={rec.get('output', 0):6} {rec.get('cny', 0):.4f} 元 {err or ''}", flush=True)

    with cf.ThreadPoolExecutor(a.parallel) as ex:
        list(ex.map(one, ids))

    if a.suite == "swe":
        preds = outdir / f"predictions-noagent{tag}.jsonl"
        with preds.open("w", encoding="utf-8") as f:
            for i in ids:
                f.write(json.dumps({"instance_id": i, "model_name_or_path": f"noagent{tag}",
                                    "model_patch": recs[i].get("model_patch", "")}) + "\n")
        ds_file = REPO / "infra" / "swebench" / ("dataset_hard.json" if "hard" in Path(a.instances).name else "dataset.json")
        print(f"predictions -> {preds}")
        if a.judge:
            resolved = judge_swe(preds, f"noagent{tag}", ds_file, outdir)
            if resolved is not None:
                for i in ids:
                    recs[i]["solved"] = i in resolved
        else:
            print(f"判分：python -m swebench.harness.run_evaluation -d {ds_file.relative_to(REPO)} -p {preds} -id noagent{tag}")

    with out.open("w", encoding="utf-8") as f:
        for i in ids:
            f.write(json.dumps(recs[i], ensure_ascii=False) + "\n")
    rs = [recs[i] for i in ids]
    cost = sum(r.get("cny", 0) for r in rs)
    judged = [r for r in rs if r["solved"] is not None]
    solved = f"solved {sum(bool(r['solved']) for r in judged)}/{len(rs)}" if judged else "未判分（加 --judge 或按上面的命令判分）"
    print(f"\nnoagent {a.suite}: {solved}  {cost:.4f} 元（每题 {cost / len(rs):.4f} 元）  "
          f"中位耗时 {statistics.median(r['seconds'] for r in rs):.1f}s  "
          f"prompt tokens 合计 {sum(r.get('prompt_tokens', 0) for r in rs)}（中位 {statistics.median(r.get('prompt_tokens', 0) for r in rs):.0f}）"
          f"  结果 -> {out}")


if __name__ == "__main__":
    main()
