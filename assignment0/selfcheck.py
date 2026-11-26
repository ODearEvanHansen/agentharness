#!/usr/bin/env python3
"""AgentHarness 课程环境自检（作业 0）。

只读检查，不安装任何东西；每项给出 ✅/⚠️/❌ 和修复建议。
用法：python3 selfcheck.py
"""
import json, os, platform, shutil, subprocess, sys, time, urllib.request

RESULTS = []


def add(level, item, detail, fix=""):
    RESULTS.append((level, item, detail, fix))


def run(cmd, timeout=20):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()
    except Exception as e:
        return -1, str(e)


def http(url, timeout=8):
    t = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "dsh-course-selfcheck"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, round(time.time() - t, 2)
    except urllib.error.HTTPError as e:
        return e.code, round(time.time() - t, 2)
    except Exception as e:
        return None, type(e).__name__


def check_os():
    s, m = platform.system(), platform.machine()
    if s == "Linux":
        wsl = "microsoft" in platform.release().lower()
        if m.lower() in ("x86_64", "amd64"):
            add("✅", "操作系统", f"Linux {m}" + (" (WSL2)" if wsl else ""))
        else:
            add("❌", "操作系统", f"Linux {m}" + (" (WSL2)" if wsl else ""),
                "本课程只支持 x86_64（amd64）Linux：SWE-bench 评测镜像仅有 x86_64 版本；请换用 x86_64 云主机或 Windows+WSL2")
    elif s == "Darwin":
        add("❌", "操作系统", f"macOS {platform.mac_ver()[0]} {m}",
            "本课程不支持 macOS（SWE-bench 镜像仅 x86_64，本地模型实验按 x86 Linux 设计）；请使用 x86_64 Linux 云主机或 Windows+WSL2")
    elif s == "Windows":
        add("⚠️", "操作系统", "Windows 原生", "课程评测依赖 Docker + Linux 容器，请在 WSL2 中完成作业")
    else:
        add("❌", "操作系统", s)


def check_python():
    ok = sys.version_info >= (3, 10)
    add("✅" if ok else "❌", "Python", platform.python_version(), "" if ok else "需要 Python ≥ 3.10")
    if sys.version_info < (3, 14):
        try:
            import zstandard  # noqa: F401
            add("✅", "zstandard", "已安装（读取压缩的 DSH 会话日志）")
        except ImportError:
            add("❌", "zstandard", "未安装", "pip install zstandard（Python < 3.14 读取 .zstd 会话日志需要）")


def check_resources():
    try:
        total = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1024**3
        if total >= 30:
            add("✅", "内存", f"{total:.0f} GB")
        elif total >= 15:
            add("⚠️", "内存", f"{total:.0f} GB", "可完成 A0–A3 和 A4 的 8B 实验；A4 L3 与 A5 的 30B-A3B 需要 32GB（A5 可走 Qwen3-4B 小内存路线）；A2 建议 --parallel 1")
        else:
            wsl = False
            try:
                wsl = "microsoft" in open("/proc/version", encoding="utf-8").read().lower()
            except OSError:
                pass
            if wsl:
                add("⚠️", "内存", f"{total:.0f} GB（WSL2）",
                    "WSL2 默认只分到部分内存。在 Windows 的 %UserProfile%\\.wslconfig 写入 [wsl2] memory=14GB swap=8GB，"
                    "然后在 PowerShell 执行 wsl --shutdown 重启 WSL，再运行本脚本")
            else:
                add("❌", "内存", f"{total:.0f} GB", "至少需要 16GB")
    except (ValueError, OSError, AttributeError):
        add("⚠️", "内存", "无法检测")
    free = shutil.disk_usage(os.path.expanduser("~")).free / 1024**3
    add("✅" if free >= 100 else "⚠️", "磁盘空闲", f"{free:.0f} GB",
        "" if free >= 100 else "SWE-bench 镜像约 3GB/题，全课建议预留 ≥100GB")
    add("✅", "CPU 核数", str(os.cpu_count()))


def check_container_runtime():
    exe = shutil.which("docker")
    if not exe:
        add("❌", "Docker", "未安装", "安装 Docker Engine（Linux）或 Docker Desktop（Windows+WSL2），见 docs/setup.md")
        return
    rc, out = run([exe, "info", "--format", "{{.ServerVersion}} {{.NCPU}}cpu"])
    if rc != 0:
        add("❌", "Docker", "daemon 不可用：" + out[-120:], "启动 Docker；Linux 下确认当前用户在 docker 组")
        return
    add("✅", "Docker", out)
    probe = [exe, "run", "--rm", "--name", "agentharness-a0-selfcheck", "--label", "agentharness.course=a0",
             "--cpus", "1", "--memory", "256m", "--network", "none", "alpine:3.20", "true"]
    rc, out = run(probe, timeout=180)
    add("✅" if rc == 0 else "⚠️", "Docker 运行容器", "ok" if rc == 0 else out[-160:],
        "" if rc == 0 else "拉取探测镜像 alpine:3.20（Docker Hub）失败；Docker Hub 不通不能忽略：按 infra/README.md 配置镜像加速，或拉 GHCR 预构建镜像后 docker tag 成本地名字")


def check_network():
    targets = [
        ("DeepSeek API", "https://api.deepseek.com/", True),
        ("PyPI", "https://pypi.org/simple/deepseek-harness-sdk/", True),
        ("GHCR（评测镜像）", "https://ghcr.io/v2/", True),
        ("Docker Hub", "https://registry-1.docker.io/v2/", False),
        ("Hugging Face", "https://huggingface.co/api/models?limit=1", False),
        ("GitHub", "https://github.com/", False),
    ]
    for name, url, required in targets:
        code, t = http(url)
        if code is None:
            add("❌" if required else "⚠️", f"网络：{name}", f"不可达 ({t})",
                "配置镜像/代理：pip 用 -i 国内源；Docker 配 registry-mirrors（课程镜像都在 GHCR，见 infra/README.md）；HF 设 HF_ENDPOINT=https://hf-mirror.com")
        else:
            slow = isinstance(t, float) and t > 3
            add("⚠️" if slow else "✅", f"网络：{name}", f"HTTP {code}，{t}s" + ("（能连通；没带凭据所以是 401，正常）" if code == 401 else ""), "较慢，建议配置国内镜像" if slow else "")


def check_key():
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not key:
        add("❌", "DEEPSEEK_API_KEY", "未设置", "在 platform.deepseek.com 创建 key，export DEEPSEEK_API_KEY=...（不要提交到 git）")
        return
    if not key.startswith("sk-"):
        add("⚠️", "DEEPSEEK_API_KEY", "格式不像 DeepSeek 官方 key（应以 sk- 开头）", "确认不是其他平台的 key")
    req = urllib.request.Request("https://api.deepseek.com/user/balance", headers={"Authorization": "Bearer " + key})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            b = json.load(r)["balance_infos"][0]
        add("✅", "DEEPSEEK_API_KEY", "有效，余额充足" if float(b["total_balance"]) >= 1 else f"有效，但余额不足 1 {b['currency']}，请先充值")
        add("⚠️", "API key 安全", "建议为本课程单独创建 key、只充值少量余额，课程结束后删除",
            "agent 在容器里运行不可信代码时可以读到 key；白名单代理也挡不住经 api.deepseek.com 的数据外传")
    except urllib.error.HTTPError as e:
        add("❌", "DEEPSEEK_API_KEY", f"HTTP {e.code}", "key 无效或已删除")
    except Exception as e:
        add("⚠️", "DEEPSEEK_API_KEY", f"无法验证：{type(e).__name__}")


PINS = {"deepseek-harness-sdk": "0.2.2rc2", "swebench": "5.0.2"}


def check_dsh():
    from importlib import metadata
    for pkg, want in PINS.items():
        try:
            v = metadata.version(pkg)
            add("✅" if v == want else "❌", pkg, v, "" if v == want else f"课程锁定版本：pip install {pkg}=={want}")
        except metadata.PackageNotFoundError:
            add("❌", pkg, "未安装", f"pip install {pkg}=={want}")
    try:
        from deepseek_harness_runtime import resolve_bundled_launch_args
        rc, out = run([*resolve_bundled_launch_args(), "--version"])
        add("✅" if rc == 0 else "❌", "DSH 运行时", out if rc == 0 else out[-160:])
    except ImportError:
        pass


if __name__ == "__main__":
    for f in (check_os, check_python, check_resources, check_container_runtime, check_network, check_key, check_dsh):
        try:
            f()
        except Exception as e:
            add("⚠️", f.__name__, f"检查出错：{e}")
    width = max(len(r[1]) for r in RESULTS)
    for lv, item, detail, fix in RESULTS:
        print(f"{lv} {item:<{width}}  {detail}" + (f"\n   ↳ {fix}" if fix and lv != "✅" else ""))
    bad = sum(1 for r in RESULTS if r[0] == "❌")
    print("\n" + ("全部通过" if not bad else f"{bad} 项必须修复"))
    sys.exit(1 if bad else 0)
