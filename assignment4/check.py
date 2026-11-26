#!/usr/bin/env python3
"""作业 4 自动检查：确认 E1–E5 的结果文件齐全、数据自洽。只检查"实验做了、数据像真的"，结论对错由报告评审。"""
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = HERE / "results"            # 你自己跑出的结果（bench.py 默认写到这里）
REF = HERE / "reference"        # 课程团队的参考结果，只用来对比
ok_all = True


def check(name, fn, msg):
    """fn 返回 (通过?, 附加说明)；任何异常（缺字段、类型不对）都记为 ❌ 并给出原因。"""
    global ok_all
    try:
        cond, extra = fn()
    except Exception as e:
        cond, extra = False, f"（数据格式不对：{type(e).__name__}: {e}）"
    ok_all &= bool(cond)
    print(("✅" if cond else "❌"), name, msg + (extra or ""))


def leaves(x, path=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from leaves(v, f"{path}/{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from leaves(v, f"{path}/{i}")
    elif isinstance(x, (int, float)) and not isinstance(x, bool):
        yield path, x


MEASURED_SUFFIXES = ("_ms", "_s", "_tok_s", "rss_mb", "pp512", "tg128")


def is_measured(path):
    """只有耗时 / 吞吐 / 内存这类随机器和运行而变的字段才用来判断是否复制。
    token 计数（*_n、total_tokens）、草稿计数（draft_n/draft_accepted）、accept_rate、size_gb
    由提示、模型和锁定 commit 决定：任何人用锁定版本诚实重跑都会得到和参考逐位相同的值，不能作为证据。"""
    return path.rsplit("/", 1)[-1].endswith(MEASURED_SUFFIXES)


def looks_copied(d, r):
    """测量值（耗时/吞吐/内存）多数和参考结果完全相同 → 判定为复制参考数据。"""
    mine, ref = dict(leaves(d.get("results"))), dict(leaves(r.get("results")))
    common = [k for k in mine if k in ref and is_measured(k)]
    if len(common) < 2:
        return False
    same = sum(1 for k in common if mine[k] == ref[k])
    return same / len(common) >= 0.5


def load(e):
    f = R / f"{e}.json"
    if not f.exists():
        print(f"   {e}: 没有 results/{e}.json")
        return None
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except (ValueError, UnicodeDecodeError) as ex:
        print(f"   {e}: results/{e}.json 不是合法 JSON（{ex}）")
        return None
    if not isinstance(d, dict) or not isinstance(d.get("results"), dict):
        print(f"   {e}: results/{e}.json 缺少 results 字段（应由 engine/bench.py 生成）")
        return None
    ref = REF / f"{e}.json"
    if ref.exists():
        try:
            r = json.loads(ref.read_text(encoding="utf-8"))
        except ValueError:
            r = {}
        if d == r or looks_copied(d, r):
            print(f"⚠️  {e}: results/{e}.json 的数据和 reference/{e}.json 基本相同，这是课程参考数据，不是你的结果")
            return None
    return d["results"]


def main():
    if not R.exists():
        print(f"⚠️  还没有 {R}：先用 engine/bench.py 跑实验。参考结果在 {REF}")
    e1 = load("E1")
    check("E1", lambda: (e1 and {"np1", "np4"} <= e1.keys() and all(v["total_tokens"] > 0 for v in e1.values()),
                         f"：吞吐 {e1['np1']['agg_tok_s']} → {e1['np4']['agg_tok_s']} tok/s" if e1 else ""), "np1/np4 都有数据")
    e2 = load("E2")
    check("E2", lambda: (e2 and (e2["cache_on"].get("second_cache_n") or 0) > 0
                         and e2["cache_on"]["second_prompt_n"] < e2["cache_off"]["second_prompt_n"],
                         f"：{e2['cache_off']['second_prompt_ms']} → {e2['cache_on']['second_prompt_ms']} ms" if e2 else ""),
          "开启 cache_prompt 后第二次请求确实复用了前缀")
    e3 = load("E3")
    check("E3", lambda: (e3 and {"baseline", "draft_n3", "draft_n16"} <= e3.keys()
                         and all(e3[k]["draft_n"] for k in ("draft_n3", "draft_n16")),
                         f"：接受率 {e3['draft_n3']['accept_rate']} / {e3['draft_n16']['accept_rate']}" if e3 else ""),
          "有基线和两种草稿长度，草稿确实生效")
    e4 = load("E4")
    check("E4", lambda: (e4 and {"kv_f16", "kv_q8_0"} <= e4.keys() and all(v["rss_mb"] for v in e4.values()), ""),
          "f16/q8_0 都有内存和速度数据")
    e5 = load("E5")
    check("E5", lambda: (e5 and len(e5) >= 2 and all("pp512" in v and "tg128" in v for v in e5.values()), ""),
          "至少两个模型的 llama-bench 数据")
    check("报告", lambda: ((HERE / "WRITEUP.md").exists(), ""), "WRITEUP.md 存在")
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
