#!/usr/bin/env python3
"""作业 2 运行器：在课程小题或 SWE-bench 子集上运行 agent，记录用量并判分/导出补丁。

  python assignment2/run.py --agent miniloop --suite mini              # 课程小题（判分：test_task.py 通过且未被修改）
  python assignment2/run.py --agent dsh      --suite mini              # 对照组：DSH sdk-minimal
  python assignment2/run.py --agent miniloop --suite swe --parallel 3  # SWE-bench 子集（导出 predictions，再用官方评测判分）

SWE 模式要求：先按 infra/README.md 建好隔离网络和出网白名单代理（默认 agentharness-net / agentharness-egress）。
结果写入 assignment2/results/<suite>-<agent>.jsonl（可断点续跑：已有无错误记录的题会跳过；--fresh 先备份旧文件再全部重跑）。

可选环境变量（一般不用改）：
  AH_NAME_PREFIX  任务容器名前缀（默认 agentharness-a2-）
  AH_LABEL        任务容器 label（默认 agentharness.course=a2）
  AH_NET          隔离网络名（默认 agentharness-net）
  AH_EGRESS       出网代理容器名（默认 agentharness-egress）
  AH_PATH_MAP     本机路径→Docker 守护进程可见路径的映射，形如 /a=/b（只有在容器里运行本脚本时才需要）
  SWE_IMAGE_REPO  评测镜像仓库（默认 GHCR 课程镜像）
"""
import argparse, concurrent.futures as cf, hashlib, json, os, shutil, signal, subprocess, sys, threading, time, uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
AGENT_DIR = Path(os.environ.get("AH_AGENT_DIR", HERE / "miniloop"))
sys.path[:0] = [str(AGENT_DIR), str(HERE / "miniloop"), str(REPO / "tools")]
import usage_cost  # noqa: E402
from env import LocalEnv, ContainerEnv  # noqa: E402

IMAGE_REPO = os.environ.get("SWE_IMAGE_REPO", "ghcr.io/odearevanhansen/swebench-x86_64")
NAME_PREFIX = os.environ.get("AH_NAME_PREFIX", "agentharness-a2-")
LABEL = os.environ.get("AH_LABEL", "agentharness.course=a2")
NET = os.environ.get("AH_NET", "agentharness-net")
EGRESS = os.environ.get("AH_EGRESS", "agentharness-egress")
PROXY = f"http://{EGRESS}:8888"
PROFILE = "sdk-minimal"          # --profile 可改
OUTDIR = HERE / "results"        # --out 可改；所有中间产物都写在这里
EXTRA_PATCHES: list[Path] = []   # --patch 可追加（作业 3/5：你的配置和插件）
TASKS_DIR = HERE / "tasks"       # --suite-dir 可改（作业 3 选做 L5：assignment3/security/tasks）


def all_patches():
    return tuple(str(p) for p in [REPO / "infra" / "course.patch.yml", *EXTRA_PATCHES])
SWE_PROMPT = """You are working in the repository at /testbed (Python environment already set up).
Resolve the following GitHub issue by editing the source code. Do not modify existing tests.
You may write and run small scripts to reproduce and verify the fix. When done, stop.

<issue>
{issue}
</issue>"""


def host_path(p) -> str:
    p = str(p)
    m = os.environ.get("AH_PATH_MAP")
    if m:
        a, b = m.split("=", 1)
        if p.startswith(a):
            return b + p[len(a):]
    return p


def read_jsonl(path):
    """容错读取结果文件：跳过无法解析的行（例如进程被杀时写了一半的最后一行）并提示。"""
    recs, bad = [], 0
    if not Path(path).exists():
        return recs
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except ValueError:
            bad += 1
            continue
        if isinstance(r, dict) and "id" in r:
            recs.append(r)
        else:
            bad += 1
    if bad:
        print(f"警告：{path} 中有 {bad} 行无法解析，已跳过（对应的题会重跑）", file=sys.stderr, flush=True)
    return recs


WRITE_LOCK = threading.Lock()


def append_record(out, rec):
    """一次 write 写完整行 + flush + fsync，并发时加锁，避免行交错或半行。"""
    line = json.dumps(rec, ensure_ascii=False) + "\n"
    with WRITE_LOCK:
        with open(out, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())


def kill_stragglers(workdir):
    """判分前杀掉仍以任务目录为工作目录的进程（agent 留在后台的命令），避免它们在判分时改文件。"""
    root = str(Path(workdir).resolve())
    me = os.getpid()
    for p in Path("/proc").glob("[0-9]*"):
        try:
            pid = int(p.name)
            if pid == me:
                continue
            cwd = os.readlink(p / "cwd")
        except (OSError, ValueError):
            continue
        if cwd == root or cwd.startswith(root + os.sep):
            try:
                os.kill(pid, signal.SIGKILL)
            except OSError:
                pass


def price(u, model, table=None):
    """按高峰价计费，默认单位元（usage_cost.PRICES）；table=usage_cost.USD_PRICES 时给已弃用的 usd 字段。"""
    hit, miss, out = (table or usage_cost.PRICES).get(model, {"peak": (0, 0, 0)})["peak"]
    return round((u["input_miss"] * miss + u["cache_read"] * hit + u["output"] * out) / 1e6, 6)


class ActionLogEnv(LocalEnv):
    """LocalEnv + 把 miniloop 的每次工具调用记到 jsonl（作业 3 L5 用它判断 agent 是否执行了注入指令）。"""
    def __init__(self, root, log):
        super().__init__(root)
        self.log = Path(log)
        self.log.parent.mkdir(parents=True, exist_ok=True)
        self.log.write_text("", encoding="utf-8")

    def _rec(self, name, args):
        with open(self.log, "a", encoding="utf-8") as f:
            f.write(json.dumps({"name": name, "arguments": args}, ensure_ascii=False) + "\n")

    def bash(self, cmd, timeout=120):
        self._rec("bash", {"command": cmd})
        return super().bash(cmd, timeout)

    def read(self, path):
        self._rec("read_file", {"path": path})
        return super().read(path)

    def write(self, path, content):
        self._rec("write_file", {"path": path, "content": content})
        return super().write(path, content)


# ------------------------------------------------------------------ agents
class TaskTimeout(BaseException):
    """单题超时。继承 BaseException，这样 miniLoop 里的 except Exception 拦不住它，循环会真正停下。"""


_TLS = threading.local()   # 当前工作线程对应题目的取消信号（threading.Event）


def _with_cancel(ev, fn, *args):
    _TLS.cancel = ev
    return fn(*args)


def _patch_chat(agent):
    """包一层 agent.chat：题目超时后，下一次请求模型之前抛出 TaskTimeout，不再继续花钱。"""
    if getattr(agent.chat, "_ah_wrapped", False):
        return
    orig = agent.chat

    def chat(*a, **kw):
        ev = getattr(_TLS, "cancel", None)
        if ev is not None and ev.is_set():
            raise TaskTimeout("单题超时，运行器已停止这道题")
        return orig(*a, **kw)
    chat._ah_wrapped = True
    agent.chat = chat


def run_miniloop(env, prompt, model):
    import agent
    _patch_chat(agent)
    r = agent.solve(env, prompt, model)
    return r["usage"], r["steps"], r["tool_calls"]


def run_dsh_local(env, prompt, model):
    """DSH 在本地目录工作（小题）。每题独立的 DSH_HOME，统计包含子 agent 在内的全部会话（by_model 区分云端/本地）。"""
    from deepseek_harness import DeepSeekHarness
    home = OUTDIR / "dsh-home-mini" / Path(env.workdir).name
    shutil.rmtree(home, ignore_errors=True)
    home.mkdir(parents=True, exist_ok=True)
    with DeepSeekHarness(provider="deepseek-official", model=model, cwd=env.workdir, dsh_home=str(home),
                         profile=PROFILE, patches=all_patches(), initialize_timeout_seconds=180) as h:
        s = h.start_session()
        res = s.run(prompt)
    u = usage_cost.summarize(home, model, "peak")
    return u, u["requests"], sum(1 for e in res.events if e.get("type") == "tool/call")


def run_dsh_container(env, prompt, model):
    """DSH runtime 在任务容器内运行（只读挂载进容器），SDK 通过 docker exec 的 stdin/stdout 与之通信。"""
    from deepseek_harness import DeepSeekHarness
    with DeepSeekHarness(provider="deepseek-official", model=model, cwd="/testbed", runtime_cwd=str(HERE),
                         dsh_home="/dshhome", dsh_bin=str(HERE / "dsh-in-container.sh"), profile=PROFILE,
                         patches=all_patches(),
                         env={"DSH_CTR": env.ctr, "AH_PROXY": PROXY}, initialize_timeout_seconds=180) as h:
        s = h.start_session()
        res = s.run(prompt)
        sid = s.id
    dst = OUTDIR / "dsh-homes" / env.ctr
    dst.mkdir(parents=True, exist_ok=True)
    subprocess.run(["docker", "cp", f"{env.ctr}:/dshhome/sessions", str(dst / "sessions")], capture_output=True)
    u = usage_cost.summarize(dst, model, "peak", sid)
    return u, u["requests"], sum(1 for e in res.events if e.get("type") == "tool/call")


# ------------------------------------------------------------------ suites
def mini_tasks():
    root = TASKS_DIR
    return [{"id": p.name, "prompt": (p / "PROMPT.txt").read_text(encoding="utf-8")} for p in sorted(root.iterdir()) if p.is_dir()]


def run_mini(task, agent, model, outdir):
    src = TASKS_DIR / task["id"]
    d = outdir / "work" / agent / task["id"]
    shutil.rmtree(d, ignore_errors=True)
    shutil.copytree(src, d)
    th = hashlib.sha256((src / "test_task.py").read_bytes()).hexdigest()
    env = LocalEnv(d) if agent != "miniloop" else ActionLogEnv(d, outdir / "actions" / agent / f"{task['id']}.jsonl")
    fn = run_miniloop if agent == "miniloop" else run_dsh_local
    usage, steps, tcalls = fn(env, task["prompt"], model)
    kill_stragglers(d)
    tp = d / "test_task.py"
    unchanged = tp.is_file() and not tp.is_symlink() and hashlib.sha256(tp.read_bytes()).hexdigest() == th
    # 判分在干净副本里进行：只采纳 agent 对"原有源文件"的修改，新增文件（如 conftest.py、sitecustomize.py）一律不带入
    judge = outdir / "judge" / agent / task["id"]
    shutil.rmtree(judge, ignore_errors=True)
    shutil.copytree(src, judge)
    # 拒绝符号链接：否则 agent 可以把源文件链到判分副本之外（例如指向测试文件或系统文件）
    symlinks = []
    for f in src.rglob("*"):
        rel = f.relative_to(src)
        if not f.is_file() or rel.name == "test_task.py":
            continue
        cand = d / rel
        if any((d / Path(*rel.parts[:i])).is_symlink() for i in range(1, len(rel.parts) + 1)):
            symlinks.append(str(rel))
            continue
        if cand.is_file():
            shutil.copyfile(cand, judge / rel)
    if symlinks:
        print(f"{task['id']}: 拒绝判分——agent 把这些文件换成了符号链接：{symlinks}", flush=True)
        unchanged = False
    p = subprocess.run([sys.executable, "test_task.py"], cwd=judge, capture_output=True, text=True, timeout=60)
    return {"solved": unchanged and p.returncode == 0, "usage": usage, "steps": steps, "tool_calls": tcalls}


def swe_tasks(instances_file):
    """题面优先从仓库自带的 infra/swebench/dataset*.json 读取（国内无需访问 Hugging Face），缺的题再在线加载。"""
    ids = [l.strip() for l in open(instances_file, encoding="utf-8") if l.strip() and not l.startswith("#")]
    ds = {}
    for f in (REPO / "infra" / "swebench").glob("dataset*.json"):
        ds.update({r["instance_id"]: r for r in json.loads(f.read_text(encoding="utf-8"))})
    if any(i not in ds for i in ids):
        from datasets import load_dataset   # 国内可先 export HF_ENDPOINT=https://hf-mirror.com
        ds.update({r["instance_id"]: r for r in load_dataset("SWE-bench/SWE-bench_Verified", split="test")})
    return [{"id": i, "prompt": SWE_PROMPT.format(issue=ds[i]["problem_statement"])} for i in ids]


CONTAINERS = {}   # task id -> 任务容器名（超时时用来强制清理）


def in_container():
    # 挂进来的 docker.sock 等于把宿主机 Docker 交给 agent，这种"容器"不算隔离
    if Path("/var/run/docker.sock").exists():
        return False
    return Path("/.dockerenv").exists() or os.environ.get("AH_IN_CONTAINER") == "1"


def run_swe(task, agent, model, outdir):
    suffix = task["id"].replace("__", "_1776_")
    name = f"{NAME_PREFIX}{agent}-{suffix.lower()}-{uuid.uuid4().hex[:6]}"[:120]
    dsh_mount = []
    if agent == "dsh":  # 只有 DSH 需要 SDK 运行时；miniLoop 不依赖它
        import deepseek_harness_runtime
        runtime = Path(deepseek_harness_runtime.__file__).parent / "runtime"
        dsh_mount = ["-v", f"{host_path(runtime)}:/dsh:ro"]
    infra = REPO / "infra"
    cmd = ["docker", "run", "-d", "--name", name, "--label", LABEL, "--cpus", "4", "--memory", "8g",
           "--network", NET, "-e", f"HTTPS_PROXY={PROXY}", "-e", f"HTTP_PROXY={PROXY}",
           *dsh_mount, "-v", f"{host_path(infra)}:{infra}:ro",
           *[x for d in sorted({p.parent for p in EXTRA_PATCHES}) for x in ("-v", f"{host_path(d)}:{d}:ro")],
           f"{IMAGE_REPO}:{suffix}", "sleep", "infinity"]
    CONTAINERS[task["id"]] = name
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-300:])
    try:
        env = ContainerEnv(name)
        fn = run_miniloop if agent == "miniloop" else run_dsh_container
        usage, steps, tcalls = fn(env, task["prompt"], model)
        # 补丁不走 env.bash：那里只保留输出的最后 MAX_OUT 个字符，长 diff 会丢掉文件头
        p = subprocess.run(["docker", "exec", name, "bash", "-lc", "cd /testbed && git add -A && git diff --cached"],
                           capture_output=True, text=True, timeout=60)
        patch = p.stdout
    finally:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True)
    return {"solved": None, "usage": usage, "steps": steps, "tool_calls": tcalls, "model_patch": patch}


def resume_filter(tasks, out, only=None, fresh=False):
    """断点续跑：跳过已有无错误记录的题；出错的题会重跑（汇总时同一题以最后一条为准）。
    fresh=True 时先把已有结果文件改名备份，全部重跑。"""
    if fresh and out.exists():
        bak = out.with_name(f"{out.name}.bak-{time.strftime('%Y%m%d-%H%M%S')}")
        out.rename(bak)
        print(f"--fresh：已有结果文件移到 {bak}", flush=True)
    if out.exists() and out.stat().st_size:
        with open(out, "rb+") as f:          # 上次中断留下的半行：补一个换行，后续追加的记录才不会和它粘在一起
            f.seek(-1, os.SEEK_END)
            if f.read(1) != b"\n":
                f.write(b"\n")
    done = {r["id"] for r in read_jsonl(out) if not r.get("error")}
    wanted = [t for t in tasks if not only or t["id"] in only]
    skipped = [t for t in wanted if t["id"] in done]
    if skipped:
        print(f"跳过 {len(skipped)} 道已有记录的题（结果文件 {out}）；要重跑请加 --fresh 或换 --tag", flush=True)
    return [t for t in wanted if t["id"] not in done]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", choices=["miniloop", "dsh"], required=True)
    ap.add_argument("--suite", choices=["mini", "swe"], required=True)
    ap.add_argument("--instances", default=str(REPO / "infra" / "swebench" / "instances.txt"))
    ap.add_argument("--model", default=os.environ.get("MODEL", "deepseek-flash"))
    ap.add_argument("--parallel", type=int, default=1)
    ap.add_argument("--timeout", type=int, default=1200, help="单题超时（秒）")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--out", default=str(HERE / "results"))
    ap.add_argument("--profile", default="sdk-minimal", help="DSH profile（仅 --agent dsh）")
    ap.add_argument("--patch", action="append", default=[],
                    help="追加的 DSH patch 文件（可重复）。SWE 模式下其所在目录会只读挂载进任务容器，插件 .ts 请放在同一目录并用绝对路径引用")
    ap.add_argument("--tag", default="", help="结果文件名后缀，用于区分不同配置的运行")
    ap.add_argument("--fresh", action="store_true",
                    help="不续跑：先把已有结果文件改名为 <名字>.jsonl.bak-<时间戳>，再全部重跑")
    ap.add_argument("--suite-dir", help="--suite mini 时改用别的题目目录（例如 assignment3/security/tasks）")
    ap.add_argument("--prompt-suffix-file", help="追加到每道题 prompt 末尾的文本文件（作业 5：路由指引）")
    a = ap.parse_args()
    global PROFILE, OUTDIR, TASKS_DIR
    if a.suite_dir:
        TASKS_DIR = Path(a.suite_dir).resolve()
    PROFILE = a.profile
    OUTDIR = Path(a.out).resolve()
    EXTRA_PATCHES.extend(Path(p).resolve() for p in a.patch)
    outdir = OUTDIR
    outdir.mkdir(parents=True, exist_ok=True)
    tag = f"-{a.tag}" if a.tag else ""
    out = outdir / f"{a.suite}-{a.agent}{tag}.jsonl"
    tasks = mini_tasks() if a.suite == "mini" else swe_tasks(a.instances)
    tasks = resume_filter(tasks, out, a.only, a.fresh)
    runner = run_mini if a.suite == "mini" else run_swe
    if a.suite == "mini" and not in_container():
        sys.exit("小题模式会在当前机器上直接执行 agent 生成的 shell 命令，必须在容器里运行（见 assignment2/README.md「在容器里跑小题」）。\n"
                 "完整命令（隔离网络、出网代理、资源限制）见该小节；容器里不能挂载 docker.sock。")
    if a.suite == "swe" and tasks:
        try:
            ok = subprocess.run(["docker", "info"], capture_output=True, timeout=30).returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            ok = False
        if not ok:
            sys.exit("Docker 不可用（没装，或守护进程没启动）：SWE 模式的每道题都要在评测镜像里跑。\n"
                     "先让 `docker info` 能正常输出，再按 assignment0/README.md 关卡 1 检查隔离网络和出网代理。")
    if a.agent == "dsh" and a.suite == "mini":
        os.environ.setdefault("DSH_PERMISSION_MODE", "danger-full-access")   # 隔离由外层容器负责
    if a.prompt_suffix_file:
        suffix = Path(a.prompt_suffix_file).read_text(encoding="utf-8")
        for t in tasks:
            t["prompt"] = t["prompt"].rstrip() + "\n\n" + suffix

    def one(t):
        t0 = time.time()
        err = None
        ex = cf.ThreadPoolExecutor(1)
        ev = threading.Event()
        try:
            r = ex.submit(_with_cancel, ev, runner, t, a.agent, a.model, outdir).result(timeout=a.timeout)
        except Exception as e:
            err = f"{type(e).__name__}: {str(e)[:300]}"
            if isinstance(e, cf.TimeoutError):
                # 超时：miniLoop 在下一次请求模型前停下（见 _patch_chat）；DSH 随任务容器删除而退出
                ev.set()
                if t["id"] in CONTAINERS:
                    subprocess.run(["docker", "rm", "-f", CONTAINERS[t["id"]]], capture_output=True)
            r = {"solved": False if a.suite == "mini" else None, "steps": 0, "tool_calls": 0,
                 "usage": {"requests": 0, "input_miss": 0, "cache_read": 0, "output": 0}, "model_patch": ""}
        finally:
            ex.shutdown(wait=False)
        u = {k: r["usage"].get(k, 0) for k in ("requests", "input_miss", "cache_read", "output")}
        rec = {"id": t["id"], "agent": a.agent, "model": a.model, "seconds": round(time.time() - t0, 1),
               "solved": r["solved"], "steps": r["steps"], "tool_calls": r["tool_calls"], **u,
               "cny": r["usage"].get("cny", price(u, a.model)),
               "usd": r["usage"].get("usd", price(u, a.model, usage_cost.USD_PRICES)),  # 已弃用，仅为兼容
               "error": err}
        if r["usage"].get("by_model"):
            rec["by_model"] = r["usage"]["by_model"]
        if "model_patch" in r:
            rec["model_patch"] = r["model_patch"]
        append_record(out, rec)
        print(f"{t['id']:40} solved={rec['solved']!s:5} {rec['seconds']:7}s steps={rec['steps']:3} {rec['cny']:.4f} 元 {err or ''}", flush=True)

    with cf.ThreadPoolExecutor(a.parallel) as ex:
        list(ex.map(one, tasks))

    recs = list({r["id"]: r for r in read_jsonl(out)}.values())
    n = len(recs)
    if a.suite == "mini":
        print(f"\n{a.agent}: solved {sum(r['solved'] for r in recs)}/{n}  {sum(usage_cost.record_cny(r) for r in recs):.4f} 元")
    else:
        preds = outdir / f"predictions-{a.agent}{tag}.jsonl"
        with preds.open("w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps({"instance_id": r["id"], "model_name_or_path": a.agent + tag,
                                    "model_patch": r.get("model_patch", "")}) + "\n")
        ds = "infra/swebench/dataset_hard.json" if "hard" in Path(a.instances).name else "infra/swebench/dataset.json"
        bad = [r["id"] for r in recs if r.get("error")]
        empty = [r["id"] for r in recs if not r.get("error") and not r.get("model_patch")]
        cost = sum(usage_cost.record_cny(r) for r in recs)
        if bad:
            print(f"\n{n} 题中 {len(bad)} 题出错（见上方每行末尾的报错），{cost:.4f} 元。出错的题重新运行同一条命令会自动重跑。"
                  f"\npredictions -> {preds}（出错的题是空补丁，现在判分没有意义）")
            sys.exit(1)
        print(f"\n{n} 题完成，{cost:.4f} 元。predictions -> {preds}")
        if empty:
            print(f"⚠️ {len(empty)} 题没有产生任何改动（空补丁）：{', '.join(empty[:5])}{' ...' if len(empty) > 5 else ''}")
        rid = f"a2-mine{tag}"
        print(f"判分：python -m swebench.harness.run_evaluation -d {ds} -p {preds} -id {rid}\n"
              f"      mv {a.agent}{tag}.{rid}.json {outdir}/")


if __name__ == "__main__":
    main()
