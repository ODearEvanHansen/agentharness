"""DSH-Lens 起始代码（作业 1）。

已经替你写好的"管道"部分：
  - 启动 DSH（Python SDK，课程配置：关闭会话日志上传，在 Docker 中运行时由容器负责隔离）
  - POST /api/run              提交 prompt（新会话或续聊）
  - GET  /api/stream/{sid}     SSE：按顺序推送该会话树的所有原始 notification（可用 ?since=N 断点续传）
你要完成的（搜索 TODO）：
  - GET  /api/sessions/{sid}/summary   按 README 中的"后端契约"返回结构化摘要（自动检查依赖它）
  - static/index.html                   前端：轨迹、工具调用、状态、成本、子 agent 树

运行：
  export DEEPSEEK_API_KEY=...
  python -m uvicorn app:app --port 8765        # 在 assignment1/starter 目录下
"""
import json
import os
import queue
import sys
import threading
import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel

from deepseek_harness import DeepSeekHarness

HERE = Path(__file__).resolve().parent
REPO = Path(os.environ.get("AGENTHARNESS_REPO", HERE.parent.parent)).resolve()
sys.path.insert(0, str(REPO / "tools"))
import usage_cost  # noqa: E402  读取 DSH 会话日志（含 .zstd）统计 token/成本

PROFILE = os.environ.get("LENS_PROFILE", "sdk")             # 完整 profile：有子 agent
MODEL = os.environ.get("LENS_MODEL", "deepseek-flash")
DSH_HOME = Path(os.environ.get("LENS_DSH_HOME", HERE / ".dsh-home")).resolve()
WORKSPACE = Path(os.environ.get("LENS_WORKSPACE", HERE / "workspace")).resolve()
DSH_HOME.mkdir(parents=True, exist_ok=True)
WORKSPACE.mkdir(parents=True, exist_ok=True)

# 完整 profile 的 bash 默认要求 bubblewrap/Landlock 沙箱；课程约定在 Docker 容器里运行，由容器隔离。
# 只有确认在容器里（课程运行器镜像会设置 AH_IN_CONTAINER=1）才放开权限，否则拒绝启动，避免 agent 直接在你的电脑上执行命令。
# 挂进来的 docker.sock 等于把宿主机 Docker 交给 agent，这种"容器"不算隔离。
if Path("/var/run/docker.sock").exists() or not (Path("/.dockerenv").exists() or os.environ.get("AH_IN_CONTAINER") == "1"):
    sys.exit("DSH-Lens 必须在课程运行器容器里运行（见 assignment1/README.md「启动」），且容器内不能挂载 docker.sock。\n"
             "agent 会以完全权限执行 shell 命令。完整启动命令（隔离网络、出网代理、资源限制）见该小节。")
os.environ.setdefault("DSH_PERMISSION_MODE", "danger-full-access")

harness = DeepSeekHarness(
    provider="deepseek-official", model=MODEL, cwd=str(WORKSPACE), dsh_home=str(DSH_HOME), profile=PROFILE,
    patches=(str(REPO / "infra" / "course.patch.yml"),), max_tokens=32768, initialize_timeout_seconds=120,
)


class SessionState:
    """一个根会话的全部状态。events 是推给浏览器的消息序列（可重放）。"""

    def __init__(self, sid=None):
        self.session = harness.start_session(sid) if sid else harness.start_session()
        self.sid = self.session.id
        self.events = []        # [{"kind": "turn"|"note", "ts": float, "data": {...}}]
        self.listeners = []
        self.lock = threading.Lock()
        self.busy = False
        self.turn = 0

    def emit(self, kind, data):
        msg = {"kind": kind, "ts": time.time(), "data": data}
        with self.lock:
            self.events.append(msg)
            for q in list(self.listeners):
                q.put(msg)


sessions: dict[str, SessionState] = {}
registry_lock = threading.Lock()
app = FastAPI()


class RunReq(BaseModel):
    prompt: str
    session_id: str | None = None


def _run_turn(st: SessionState, prompt: str):
    st.busy = True
    st.turn += 1
    n = st.turn
    st.emit("turn", {"status": "running", "n": n, "prompt": prompt})
    t = time.time()
    try:
        r = st.session.run(prompt, on_notification=lambda note: st.emit(
            "note", {"method": note.method, "payload": note.payload if isinstance(note.payload, dict) else {}}))
        status, final = (r.finish_reason or "completed"), r.final_response
    except Exception as e:
        status, final = "error", f"{type(e).__name__}: {e}"
    st.busy = False
    st.emit("turn", {"status": status, "n": n, "final": final, "seconds": round(time.time() - t, 2)})


@app.post("/api/run")
def api_run(req: RunReq):
    with registry_lock:
        st = sessions.get(req.session_id) if req.session_id else None
        if st is None:
            st = SessionState(req.session_id)
            sessions[st.sid] = st
        if st.busy:
            return JSONResponse({"session_id": st.sid, "error": "busy"}, status_code=409)
    threading.Thread(target=_run_turn, args=(st, req.prompt), daemon=True).start()
    return {"session_id": st.sid}


@app.get("/api/stream/{sid}")
def api_stream(sid: str, since: int = 0):
    st = sessions.get(sid)
    if st is None:
        return JSONResponse({"error": "unknown session"}, status_code=404)
    q: queue.Queue = queue.Queue()
    with st.lock:
        backlog = st.events[since:]
        st.listeners.append(q)

    def gen():
        try:
            for m in backlog:
                yield f"data: {json.dumps(m, ensure_ascii=False)}\n\n"
            while True:
                try:
                    yield f"data: {json.dumps(q.get(timeout=15), ensure_ascii=False)}\n\n"
                except queue.Empty:
                    yield ": ping\n\n"
        finally:
            with st.lock:
                st.listeners.remove(q)
    return StreamingResponse(gen(), media_type="text/event-stream")


@app.get("/api/sessions/{sid}/summary")
def api_summary(sid: str):
    st = sessions.get(sid)
    if st is None:
        return JSONResponse({"error": "unknown session"}, status_code=404)
    with st.lock:
        events = list(st.events)
    # TODO(A1-L2/L3/L4/L5): 从 events（以及会话日志）计算并返回 README"后端契约"中的结构。
    #   提示：
    #   - 工具调用：session.event 中 type=tool/call 与 tool/result，用 callId / toolCallId 配对
    #   - 子 agent：notification method=subagent.started 带 parentSessionId / childSessionId
    #   - 用量：notification 不带 token 数；用 usage_cost.summarize(DSH_HOME, MODEL, "peak", session_id)
    #     读会话日志，根会话和所有子会话都要算上
    raise NotImplementedError


@app.get("/", response_class=HTMLResponse)
def index():
    return (HERE / "static" / "index.html").read_text(encoding="utf-8")
