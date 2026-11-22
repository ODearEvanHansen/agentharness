"""miniLoop：你的最小 agent loop（作业 2 Part A）。

约束：只用标准库 + 本文件里的 chat()；不要用 DSH、LangChain 等框架。参考实现约 110 行。
接口（run.py 会调用）：
    solve(env, prompt, model="deepseek-flash", max_steps=50) -> dict
    返回 {"steps": 请求次数, "tool_calls": 工具调用次数,
          "usage": {"requests", "input_miss", "cache_read", "output"}, "finished": 是否调用了 done}
"""
import json
import os
import time
import urllib.error
import urllib.request

from env import Env

API = os.environ.get("MINI_API", "https://api.deepseek.com/chat/completions")

SYSTEM = "You are a coding agent. ..."   # TODO(A2-L1): 写你的系统提示

TOOLS = [
    # TODO(A2-L1): 定义 4 个工具（OpenAI function calling 格式）：
    #   bash(command)            在任务目录执行 shell 命令
    #   read_file(path)          读文件
    #   edit_file(path, old, new) 精确替换一处；old="" 表示新建/覆盖
    #   done(summary)            结束任务
]


def chat(messages, model, tools, max_tokens=8192):
    """调用 DeepSeek（OpenAI 格式）。已提供：含 429/5xx 重试。返回原始 JSON。"""
    body = {"model": model, "messages": messages, "tools": tools, "max_tokens": max_tokens}
    req = urllib.request.Request(API, data=json.dumps(body).encode(), headers={
        "Content-Type": "application/json", "Authorization": "Bearer " + os.environ["DEEPSEEK_API_KEY"]})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < 4:
                time.sleep(2 ** attempt)
                continue
            raise


def run_tool(env: Env, name: str, args: dict) -> str:
    """执行一个工具调用，返回给模型看的文本。错误也要以文本返回，而不是抛异常。"""
    # TODO(A2-L1): 用 env.bash / env.read / env.write 实现 bash、read_file、edit_file
    #   edit_file 的 old 必须恰好出现一次，否则返回错误说明（让模型自己纠正）
    raise NotImplementedError


def solve(env: Env, prompt: str, model: str = "deepseek-flash", max_steps: int = 50) -> dict:
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]
    usage = {"requests": 0, "input_miss": 0, "cache_read": 0, "output": 0}
    steps = tool_calls = 0
    finished = False
    # TODO(A2-L2): 主循环
    #   1. chat() → 累加 usage：prompt_cache_hit_tokens → cache_read，prompt_cache_miss_tokens → input_miss，
    #      completion_tokens → output
    #   2. 把 assistant 消息追加进 messages。⚠️ 思考模式下，带 tool_calls 的 assistant 消息必须原样带回
    #      reasoning_content，否则下一次请求会报 400
    #   3. 对每个 tool_call 执行 run_tool，追加 {"role": "tool", "tool_call_id": ..., "content": ...}
    #   4. 遇到 done 或达到 max_steps 时结束；模型没有调用工具时怎么办？（想清楚，写进报告）
    return {"steps": steps, "tool_calls": tool_calls, "usage": usage, "finished": finished}
