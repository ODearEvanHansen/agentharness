#!/usr/bin/env python3
"""作业 1 自动检查：验证 DSH-Lens 后端契约（GET /api/sessions/{sid}/summary）。

用法（先启动你的服务）：
  python assignment1/check.py --url http://127.0.0.1:8765 --dsh-home assignment1/starter/.dsh-home

会真实调用 DeepSeek API（2 轮对话，约 $0.003）。检查项：
  L1 提交与流式：POST /api/run 返回 session_id；SSE 能收到事件
  L2 工具调用：summary.tool_calls 含 bash 类调用，状态为 ok/error，call_id 唯一
  L3 状态与续聊：同一会话第二轮后 turns 递增、状态回到 idle
  L4 成本：summary.usage 与独立从会话日志重算的值一致（误差 ≤1%）
  L5 子 agent：派出子 agent 后 summary.agents 中出现 parent 指向根会话的节点
"""
import argparse, json, sys, time, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import usage_cost  # noqa: E402

PROMPT1 = ("请完成两件事：1) 用 bash 在当前目录创建 a1_check.py，打印 1 到 3 的平方并运行；"
           "2) 派一个子 agent 统计当前目录有多少个 .py 文件，并把结论告诉我。")
PROMPT2 = "把 a1_check.py 改成打印立方并运行，只告诉我输出。"
RESULTS = []


def ok(level, cond, msg):
    RESULTS.append((level, bool(cond), msg))
    print(("✅" if cond else "❌"), level, msg)
    return cond


def req(url, data=None):
    r = urllib.request.Request(url, data=None if data is None else json.dumps(data).encode(),
                               headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=30) as resp:
        return json.load(resp)


def first_sse_event(url, timeout=60):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        for raw in r:
            line = raw.decode().strip()
            if line.startswith("data:"):
                return json.loads(line[5:])
    return None


def wait_idle(base, sid, turns, timeout=600):
    t = time.time()
    while time.time() - t < timeout:
        s = req(f"{base}/api/sessions/{sid}/summary")
        if s.get("status") == "idle" and len(s.get("turns", [])) >= turns:
            return s
        time.sleep(3)
    raise TimeoutError("session did not become idle")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8765")
    ap.add_argument("--dsh-home", required=True, help="服务使用的 DSH_HOME，用于独立重算用量")
    ap.add_argument("--model", default="deepseek-flash")
    a = ap.parse_args()
    base = a.url.rstrip("/")

    r = req(f"{base}/api/run", {"prompt": PROMPT1})
    sid = r.get("session_id")
    ok("L1", sid, f"POST /api/run 返回 session_id={sid}")
    ev = first_sse_event(f"{base}/api/stream/{sid}")
    ok("L1", ev and "kind" in ev, "SSE 收到事件")

    s = wait_idle(base, sid, 1)
    calls = s.get("tool_calls", [])
    ok("L2", any(c.get("status") in ("ok", "error") for c in calls), f"tool_calls 有已完成的调用（{len(calls)} 个）")
    ok("L2", len({c.get("call_id") for c in calls}) == len(calls) and all(c.get("call_id") for c in calls), "call_id 非空且唯一")
    ok("L2", not any(c.get("status") == "pending" for c in calls), "空闲时没有残留 pending 调用")
    ok("L2", any(c.get("name") == "bash" for c in calls), "tool_calls 中能看到 bash 调用（工具名正确解析）")
    agents = s.get("agents", [])
    ok("L5", any(x.get("parent") == sid for x in agents), f"agents 中有挂在根会话下的子 agent（{len(agents)} 个节点）")
    ok("L5", any(c.get("session_id") not in (None, sid) for c in calls), "存在归属于子 agent 会话的工具调用")

    req(f"{base}/api/run", {"prompt": PROMPT2, "session_id": sid})
    s2 = wait_idle(base, sid, 2)
    ok("L3", len(s2.get("turns", [])) == 2 and s2.get("session_id") == sid, "续聊：同一会话 turns=2")
    ok("L3", all(t.get("status") for t in s2.get("turns", [])), "每轮都有状态")

    u = s2.get("usage", {})
    ids = [sid] + [x["session_id"] for x in s2.get("agents", []) if x.get("session_id") != sid]
    ref = {k: 0 for k in ("requests", "input_miss", "cache_read", "output")}
    for i in ids:
        part = usage_cost.summarize(Path(a.dsh_home), a.model, "peak", i)
        for k in ref:
            ref[k] += part[k]
    close = all(abs(u.get(k, -1) - v) <= max(1, 0.01 * v) for k, v in ref.items())
    ok("L4", close, f"usage 与会话日志一致：你的={ {k: u.get(k) for k in ref} } 参考={ref}")
    hit, miss, out = usage_cost.PRICES[a.model]["peak"]
    usd_ref = (u.get("input_miss", 0) * miss + u.get("cache_read", 0) * hit + u.get("output", 0) * out) / 1e6
    ok("L4", isinstance(u.get("usd"), (int, float)) and u["usd"] > 0 and abs(u["usd"] - usd_ref) <= max(1e-6, 0.01 * usd_ref),
       f"usd={u.get('usd')}，按高峰价由你的 token 数重算应为 {usd_ref:.6f}")

    passed = sum(1 for _, c, _ in RESULTS if c)
    print(f"\n{passed}/{len(RESULTS)} 通过")
    sys.exit(0 if passed == len(RESULTS) else 1)


if __name__ == "__main__":
    main()
