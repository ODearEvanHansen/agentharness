# 生成 l02_toolcall.txt 的脚本（第 2 讲演示）
import json, os, urllib.request
body = {"model": "deepseek-flash", "messages": [{"role": "user", "content": "北京现在几点？"}],
        "tools": [{"type": "function", "function": {"name": "get_time", "description": "Get current time in a timezone",
                   "parameters": {"type": "object", "properties": {"tz": {"type": "string"}}, "required": ["tz"]}}}],
        "max_tokens": 300}
r = urllib.request.Request("https://api.deepseek.com/chat/completions", data=json.dumps(body).encode(),
                           headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["DEEPSEEK_API_KEY"]})
d = json.load(urllib.request.urlopen(r))
m = d["choices"][0]["message"]
print('finish_reason:', d["choices"][0]["finish_reason"])
print('reasoning_content:', (m.get("reasoning_content") or "")[:70].replace("\n", " ") + "…")
for c in m.get("tool_calls") or []:
    print('tool_call:', c["function"]["name"], c["function"]["arguments"])
u = d["usage"]
print('usage:', json.dumps({k: u[k] for k in ("prompt_tokens", "completion_tokens", "prompt_cache_hit_tokens", "prompt_cache_miss_tokens") if k in u}))
