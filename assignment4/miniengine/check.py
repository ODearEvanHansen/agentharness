#!/usr/bin/env python3
"""L4 自动检查：前向的基本块 → 贪心 token 对齐 → 调度器 → 分页 KV → 测量结果文件。
用法：python assignment4/miniengine/check.py   （没下载权重时，只有贪心对齐这一项判为 ❌，其余照常检查）"""
import json, math, os, sys
from pathlib import Path

os.environ.setdefault("OPENBLAS_NUM_THREADS", "8"); os.environ.setdefault("OMP_NUM_THREADS", "8")
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
MODEL_DIR = Path(os.environ.get("MINI_MODEL_DIR", HERE.parents[1] / "models" / "Qwen3-0.6B"))
ok_all = True


def check(name, fn):
    """fn 返回 (通过?, 说明)；NotImplementedError 和其它异常都记为 ❌，不打印 traceback。"""
    global ok_all
    try:
        cond, msg = fn()
    except NotImplementedError as e:
        cond, msg = False, f"还没实现：{e}"
    except Exception as e:
        cond, msg = False, f"{type(e).__name__}: {e}"
    ok_all &= bool(cond)
    print("✅" if cond else "❌", name, "—", msg)


import model as M  # noqa: E402
import engine as E  # noqa: E402


# ---------- 1. 前向基本块（不需要权重） ----------
def t_rmsnorm():
    x = np.array([[3.0, 4.0]], np.float32)
    y = M.rmsnorm(x, np.array([1.0, 2.0], np.float32), 0.0)
    want = np.array([[3, 8]]) / math.sqrt(12.5)
    return np.allclose(y, want, atol=1e-5) and y.dtype == np.float32, f"rmsnorm([3,4], w=[1,2]) = {[round(float(t), 4) for t in y.ravel()]}（{y.dtype}），应为 [0.8485, 2.2627] 且保持 float32"


def t_rope():
    rng = np.random.default_rng(0)
    x = rng.standard_normal((5, 2, 8)).astype(np.float32)
    y = M.rope(x, np.arange(5), 10000.0)
    same0 = np.allclose(y[0], x[0], atol=1e-6)
    norm = np.allclose(np.linalg.norm(y, axis=-1), np.linalg.norm(x, axis=-1), atol=1e-4)
    # 相对位置性质：<rope(q,m), rope(k,n)> 只取决于 m-n
    q, k = x[:1, :1], x[1:2, :1]
    d = lambda m, n: float((M.rope(q, np.array([m]), 1e4) * M.rope(k, np.array([n]), 1e4)).sum())
    rel = abs(d(3, 1) - d(7, 5)) < 1e-4
    # 旋转配对方式：第 i 维和第 i+hd/2 维一对（rotate-half），位置 1、第 0 对的角度是 1 弧度
    e = np.zeros((1, 1, 8), np.float32); e[0, 0, 0] = 1
    pair = np.allclose(M.rope(e, np.array([1]), 1e4)[0, 0, [0, 4]], [math.cos(1), math.sin(1)], atol=1e-5)
    return same0 and norm and rel and pair, f"位置0不变={same0} 保范数={norm} 只依赖相对位置={rel} rotate-half 配对={pair}"


def t_attention():
    rng = np.random.default_rng(1)
    T, Hq, Hkv, hd = 3, 4, 2, 8
    q = rng.standard_normal((T, Hq, hd)).astype(np.float32)
    k = rng.standard_normal((T + 2, Hkv, hd)).astype(np.float32)
    v = rng.standard_normal((T + 2, Hkv, hd)).astype(np.float32)
    out = M.attention(q, k, v, 2)
    ref = np.zeros((T, Hq, hd))
    for t in range(T):
        for h in range(Hq):
            kh = h // (Hq // Hkv)
            s = k[: 2 + t + 1, kh] @ q[t, h] / math.sqrt(hd)
            p = np.exp(s - s.max()); p /= p.sum()
            ref[t, h] = p @ v[: 2 + t + 1, kh]
    ok = out.shape == (T, Hq * hd) and np.allclose(out, ref.reshape(T, -1), atol=1e-4)
    return ok and out.dtype == np.float32, f"GQA + 因果掩码 + 缓存偏移 start=2：输出形状 {out.shape}，dtype {out.dtype}，" + ("与逐头逐位置的朴素实现一致" if ok else "和朴素实现不一致")


def t_mlp():
    rng = np.random.default_rng(2)
    x, g, u, d = (rng.standard_normal(s).astype(np.float32) for s in [(2, 4), (4, 6), (4, 6), (6, 4)])
    a = x @ g
    want = (a / (1 + np.exp(-a)) * (x @ u)) @ d
    y = M.mlp(x, g, u, d)
    return np.allclose(y, want, atol=1e-4), "SwiGLU: down(silu(x·gate) * (x·up))"


# ---------- 2. 贪心 token 与参考实现对齐（需要权重） ----------
def t_greedy():
    if not (MODEL_DIR / "model.safetensors").exists():
        return False, f"没找到 {MODEL_DIR}/model.safetensors，先运行 python assignment4/miniengine/download.py"
    exp = json.loads((HERE / "expected" / "greedy.json").read_text())
    m = M.Qwen3(MODEL_DIR)
    eng = E.Engine(m, max_batch=len(exp["cases"]), kv="contiguous", max_len=256)
    reqs = [E.Request(i, c["prompt_ids"], len(c["output_ids"])) for i, c in enumerate(exp["cases"])]
    eng.run(reqs, "continuous")   # 3 条一起跑：顺便验证批处理不会串扰
    msgs, ok = [], True
    for c, r in zip(exp["cases"], reqs):
        n = next((i for i, (a, b) in enumerate(zip(r.out, c["output_ids"])) if a != b), len(c["output_ids"]))
        ok &= n >= exp["min_prefix"]
        msgs.append(f"{n}/{len(c['output_ids'])}")
    return ok, f"3 个提示的贪心输出与参考一致的前缀长度 {msgs}（要求 ≥ {exp['min_prefix']}）"


# ---------- 3. 调度器与分页 KV（用假模型，几秒跑完） ----------
class FakeModel:
    """1 层、1 个 KV 头、head_dim 4。把位置号写进 KV，再读回来核对；永远预测 token 7。"""
    L, Hkv, hd = 1, 1, 4

    def forward(self, kvs, chunks):
        for kv, c in zip(kvs, chunks):
            s = kv.num_tokens
            val = np.repeat(np.arange(s, s + len(c), dtype=np.float32)[:, None, None], 4, axis=2)
            kv.write(0, s, val, -val)
            K, V = kv.read(0, s + len(c))
            if not (np.array_equal(K[:, 0, 0], np.arange(s + len(c))) and np.array_equal(V, -K)):
                raise AssertionError("KV 读回来的内容和写进去的不一致（块表/偏移算错了？）")
            kv.num_tokens += len(c)
        return np.tile(np.eye(10, dtype=np.float32)[7], (len(kvs), 1))


def mixed():
    """8 个请求、长短交替：短的生成 2 个 token，长的 30 个；提示长度 5~40。"""
    return [E.Request(i, list(range(5 + 5 * i)), 30 if i % 2 else 2) for i in range(8)]


def t_sched():
    res = {}
    for mode in ("static", "continuous"):
        eng = E.Engine(FakeModel(), max_batch=4, kv="paged", block_size=4, num_blocks=256)
        reqs = eng.run(mixed(), mode)
        if any(len(r.out) != r.max_new or r.step_done is None for r in reqs):
            return False, f"{mode}：有请求没生成满 max_new_tokens 或没被标记完成"
        res[mode] = (sum(r.step_done for r in reqs) / len(reqs), eng.steps)
    (ls, ss), (lc, sc) = res["static"], res["continuous"]
    ok = lc < ls and sc <= ss
    return ok, f"平均完成步数 静态 {ls:.1f} / 连续 {lc:.1f}，总步数 {ss} / {sc}（连续批处理应更低）"


def t_static_is_static():
    eng = E.Engine(FakeModel(), max_batch=4, kv="paged", block_size=4, num_blocks=256)
    reqs = eng.run(mixed(), "static")
    first_batch_end = max(r.step_done for r in reqs[:4])
    ok = all(r.step_first > first_batch_end for r in reqs[4:])
    return ok, "静态批处理：第二批要等第一批全部结束才开始" + ("" if ok else f"（第 {first_batch_end} 步第一批才结束，但第二批有请求更早开始了）")


def t_paged():
    bs = 4
    eng = E.Engine(FakeModel(), max_batch=4, kv="paged", block_size=bs, num_blocks=64)
    for r in mixed():
        eng.add(r)
    import time; eng.t0 = time.perf_counter()
    worst, n = 0.0, 0
    while eng.waiting or eng.running:
        eng.step("continuous"); n += 1
        live = [r for r in eng.running if not r.done]
        tables = [b for r in live for b in r.kv.block_table]
        if len(tables) != len(set(tables)):
            return False, f"第 {n} 步：两条序列共用了同一个物理块"
        limit = sum(math.ceil(r.kv.num_tokens / bs) * bs for r in live) + bs * len(live)
        used = eng.alloc.num_used() * bs
        if used > limit:
            return False, f"第 {n} 步：占用 {used} 个 token 槽位，超过上限 {limit}（实际长度按块取整 + 每条序列 1 块）"
        if n > 500:
            return False, "500 步还没跑完，调度可能死循环了"
    free_ok = eng.alloc.num_used() == 0
    return free_ok, f"{n} 步内块占用始终不超上限；结束后空闲块全部归还={free_ok}"


def t_paged_full():
    """块池很小：放不下的请求应该排队等待，而不是报错或超额分配。"""
    eng = E.Engine(FakeModel(), max_batch=4, kv="paged", block_size=4, num_blocks=24)
    reqs = eng.run(mixed(), "continuous")
    ok = all(len(r.out) == r.max_new for r in reqs) and eng.alloc.num_used() == 0
    return ok, "只有 24 个块（不够 4 条长序列同时跑）时仍能全部完成"


# ---------- 4. 测量结果 ----------
def t_results():
    R = HERE.parent / "results"
    missing = [e for e in ("M1", "M2", "M3") if not (R / f"{e}.json").exists()]
    if missing:
        return False, f"缺少 results/{'、'.join(missing)}.json，运行 python assignment4/miniengine/bench.py"
    m2 = json.loads((R / "M2.json").read_text())["results"]
    m3 = json.loads((R / "M3.json").read_text())["results"]
    ok = m3["paged"]["peak_reserved_tokens"] < m3["contiguous"]["peak_reserved_tokens"]
    return ok, (f"M2 平均延迟 静态 {m2['static']['mean_latency_s']}s / 连续 {m2['continuous']['mean_latency_s']}s；"
                f"M3 KV 预留 连续 {m3['contiguous']['peak_reserved_MB']}MB / 分页 {m3['paged']['peak_reserved_MB']}MB")


for name, fn in [("rmsnorm", t_rmsnorm), ("rope", t_rope), ("attention", t_attention), ("mlp", t_mlp),
                 ("贪心对齐", t_greedy), ("连续批处理", t_sched), ("静态批处理", t_static_is_static),
                 ("分页 KV", t_paged), ("块池不足时排队", t_paged_full), ("测量结果", t_results)]:
    check(name, fn)
print("\n全部通过 ✅" if ok_all else "\n还有未通过的项 ❌")
sys.exit(0 if ok_all else 1)
