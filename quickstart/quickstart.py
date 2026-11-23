#!/usr/bin/env python3
"""AgentHarness 15 分钟轻量入口：一个约 150 行的最小 coding agent，在 3 道小题上算出你的解决率和花费。

只用 Python 标准库（3.9+），不需要 Docker，macOS / Linux / Windows 都能跑。
    export DEEPSEEK_API_KEY=sk-...      # Windows PowerShell: $env:DEEPSEEK_API_KEY="sk-..."
    python3 quickstart/quickstart.py    # 可选：--model deepseek-v4-pro  --tasks t01_sum_range

安全：agent 只有 读文件 / 写文件 / 运行该题测试 三个工具，没有任意 shell，
所有文件操作限制在系统临时目录下的题目副本里，不会碰你的其他文件。
"""
import argparse, datetime, json, os, shutil, subprocess, sys, tempfile, time
import urllib.error, urllib.request
from pathlib import Path

API = os.environ.get("DEEPSEEK_API_BASE", "https://api.deepseek.com") + "/chat/completions"
HERE = Path(__file__).resolve().parent
TASKS = HERE / "tasks"
# 元 / 1M tokens：(缓存命中输入, 未命中输入, 输出)。来源 api-docs.deepseek.com/zh-cn/quick_start/pricing（2026-11-22）
PRICES = {"deepseek-flash": (0.04, 2, 8), "deepseek-v4-pro": (0.30, 9.0, 27.0)}  # 高峰价；低谷价减半

SYSTEM = ("你是一个编码 agent。工作目录里有一道小题：先读题目涉及的源文件和 test_task.py，"
          "再用 write_file 修改源文件，用 run_tests 验证；测试通过后调用 done。不要修改 test_task.py。")
TOOLS = [{"type": "function", "function": {"name": n, "description": d, "parameters": {
    "type": "object", "properties": p, "required": list(p)}}} for n, d, p in [
    ("read_file", "读取工作目录中的一个文件", {"path": {"type": "string"}}),
    ("write_file", "用完整内容覆盖写入工作目录中的一个文件", {"path": {"type": "string"}, "content": {"type": "string"}}),
    ("run_tests", "运行 python test_task.py，返回输出", {}),
    ("done", "任务完成时调用", {"summary": {"type": "string"}})]]


def is_peak(now=None):
    """北京时间工作日 9–12、14–18 点为高峰（不含节假日，此处不判断节假日）。"""
    bj = (now or datetime.datetime.utcnow()) + datetime.timedelta(hours=8)
    return bj.weekday() < 5 and (9 <= bj.hour < 12 or 14 <= bj.hour < 18)


def chat(messages, model):
    body = json.dumps({"model": model, "messages": messages, "tools": TOOLS, "max_tokens": 8192}).encode()
    req = urllib.request.Request(API, data=body, headers={
        "Content-Type": "application/json", "Authorization": "Bearer " + os.environ["DEEPSEEK_API_KEY"]})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < 4:
                time.sleep(2 ** attempt)
                continue
            raise SystemExit(f"API 错误 {e.code}：{e.read().decode(errors='replace')[:300]}")


def run_tests(work):
    try:
        p = subprocess.run([sys.executable, "test_task.py"], cwd=work, capture_output=True, text=True, timeout=30)
        return (p.stdout + p.stderr)[-2000:] or f"(无输出，退出码 {p.returncode})", p.returncode == 0
    except subprocess.TimeoutExpired:
        return "测试超时（30 秒）", False


def run_tool(work, name, args):
    try:
        if name == "run_tests":
            return run_tests(work)[0]
        path = (work / args.get("path", "")).resolve()
        if work not in path.parents:
            return "错误：只能访问工作目录内的文件"
        if name == "read_file":
            return path.read_text()[:20000]
        if name == "write_file":
            if path.name == "test_task.py":
                return "错误：不允许修改测试文件"
            path.write_text(args["content"])
            return f"已写入 {path.name}（{len(args['content'])} 字符）"
        return f"错误：未知工具 {name}"
    except Exception as e:  # 工具错误以文本返回，让模型自己纠正
        return f"错误：{type(e).__name__}: {e}"


def solve(work, prompt, model, max_steps=20):
    files = "、".join(sorted(p.name for p in work.iterdir()))
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": f"{prompt}\n目录中的文件：{files}"}]
    u = {"requests": 0, "hit": 0, "miss": 0, "out": 0}
    for _ in range(max_steps):
        r = chat(messages, model)
        us = r.get("usage", {})
        u["requests"] += 1
        u["hit"] += us.get("prompt_cache_hit_tokens", 0)
        u["miss"] += us.get("prompt_cache_miss_tokens", us.get("prompt_tokens", 0))
        u["out"] += us.get("completion_tokens", 0)
        msg = r["choices"][0]["message"]
        messages.append({k: msg[k] for k in ("role", "content", "tool_calls", "reasoning_content") if msg.get(k) is not None})
        calls = msg.get("tool_calls") or []
        if not calls:
            messages.append({"role": "user", "content": "请继续：用工具完成任务，完成后调用 done。"})
        for c in calls:
            name = c["function"]["name"]
            try:
                args = json.loads(c["function"]["arguments"] or "{}")
            except json.JSONDecodeError:
                args = {}
            print(f"    · {name} {args.get('path', '')}")
            messages.append({"role": "tool", "tool_call_id": c["id"],
                             "content": "好的" if name == "done" else run_tool(work, name, args)})
            if name == "done":
                return u
    return u


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--model", default="deepseek-flash", choices=sorted(PRICES))
    ap.add_argument("--tasks", nargs="*", default=sorted(p.name for p in TASKS.iterdir() if p.is_dir()))
    a = ap.parse_args()
    if not os.environ.get("DEEPSEEK_API_KEY"):
        raise SystemExit("请先设置环境变量 DEEPSEEK_API_KEY（建议为本课程单独创建 key，只充值少量金额）")
    hit_p, miss_p, out_p = [x * (1 if is_peak() else 0.5) for x in PRICES[a.model]]
    rows = []
    for t in a.tasks:
        src = TASKS / t
        with tempfile.TemporaryDirectory(prefix="agentharness-") as d:
            work = Path(d).resolve() / t
            shutil.copytree(src, work, ignore=shutil.ignore_patterns("PROMPT.txt", "__pycache__"))
            print(f"[{t}]")
            t0 = time.time()
            u = solve(work, (src / "PROMPT.txt").read_text().strip(), a.model)
            shutil.copy(src / "test_task.py", work / "test_task.py")  # 用原始测试判分，防止被改
            ok = run_tests(work)[1]
            cny = (u["hit"] * hit_p + u["miss"] * miss_p + u["out"] * out_p) / 1e6
            rows.append((t, ok, u, cny, time.time() - t0))
            print(f"    → {'通过' if ok else '未通过'}  请求 {u['requests']} 次  {cny:.4f} 元")
    n_ok = sum(r[1] for r in rows)
    hit, tot = sum(r[2]["hit"] for r in rows), sum(r[2]["hit"] + r[2]["miss"] for r in rows)
    print(f"\n模型 {a.model}（{'高峰' if is_peak() else '低谷'}价）")
    print(f"解决率 {n_ok}/{len(rows)}   总花费 {sum(r[3] for r in rows):.4f} 元   "
          f"缓存命中率 {hit / tot:.0%}   用时 {sum(r[4] for r in rows):.0f} 秒" if tot else "无请求")
    print("下一步：读 quickstart/README.md 里的“这 150 行在做什么”，再到课程网站看完整版作业 2。")


if __name__ == "__main__":
    main()
