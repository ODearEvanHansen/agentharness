#!/usr/bin/env python3
"""第 13 讲演示：稳定的系统提示 vs 每步写入当前时间，对 DeepSeek 前缀缓存的影响（真实 API 调用）。"""
import json, os, sys, time, urllib.request
from datetime import datetime

API = "https://api.deepseek.com/chat/completions"
KEY = os.environ["DEEPSEEK_API_KEY"]
TOOLS_DOC = "\n".join(f"- tool_{i}(path, pattern): search files for pattern #{i}; returns matching lines with numbers." for i in range(150))
BASE_SYS = "You are a coding agent. Answer in one short sentence.\nAvailable tools:\n" + TOOLS_DOC
QUESTIONS = ["What does tool_3 do?", "And tool_42?", "Which tool number is the largest?",
             "Name any tool that takes a pattern.", "Summarize in five words."]


def chat(messages):
    body = {"model": "deepseek-flash", "messages": messages, "max_tokens": 40, "thinking": {"type": "disabled"}}
    req = urllib.request.Request(API, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + KEY})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def run(variant):
    print(f"\n=== {variant} ===", flush=True)
    hist = []
    for step, q in enumerate(QUESTIONS, 1):
        sys_prompt = BASE_SYS if variant in ("stable", "append") else f"Current time: {datetime.now().isoformat(timespec='microseconds')}\n" + BASE_SYS
        if variant == "append":   # 时间放在最新消息里（追加在历史末尾），系统提示保持不变
            q = f"[time {datetime.now().isoformat(timespec='microseconds')}] " + q
        hist.append({"role": "user", "content": q})
        r = chat([{"role": "system", "content": sys_prompt}] + hist)
        u = r["usage"]
        hist.append({"role": "assistant", "content": r["choices"][0]["message"]["content"]})
        hit, miss = u.get("prompt_cache_hit_tokens", 0), u.get("prompt_cache_miss_tokens", 0)
        print(f"step {step}: prompt={u['prompt_tokens']:5d}  cache_hit={hit:5d}  miss={miss:5d}  hit_rate={hit / (hit + miss):5.1%}", flush=True)
        time.sleep(1)


if __name__ == "__main__":
    for v in sys.argv[1:] or ["stable", "timestamp", "append"]:
        run(v)
