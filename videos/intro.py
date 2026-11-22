"""课程固定片头（约 6 秒）：agent loop 环（模型 → 工具 → 结果 → 模型）转一圈，收成"图标 + 打字机课程名"，
课程名出现时 Stella 读固定口播 VOICE。

    python3 videos/intro.py --out videos/out          # 单独渲染 intro.mp4 预览
engine.py 渲染每讲时会自动把片头接在最前面（--no-intro 可关闭）。
提示音是程序合成的正弦波，没有版权问题；口播用 DeepSeek TTS 合成一次后缓存。
"""
import argparse
import math
import random
import struct
import subprocess
import wave
from pathlib import Path

from PIL import Image, ImageDraw

import engine as E

ANIM = 4.0          # 动画时长；之后定格到口播结束
VOICE = "欢迎来到 AgentHarness，Agent 系统公开课。"
VOICE_AT = 2.45
DUR = 6.0           # 实际时长由 audio() 按口播长度更新
SR = 24000
NODES = [("模型", "blue"), ("工具", "orange"), ("结果", "green")]
CX, CY, RAD = E.W / 2, E.H / 2 - 40, 230
TITLE, SUB = "AgentHarness", "Agent 系统公开课 · 基于 DeepSeek Harness"


def _pt(ang, r=RAD, cx=CX, cy=CY):
    return cx + r * math.cos(ang), cy + r * math.sin(ang)


def frame(t):
    t = min(t, ANIM)
    im = Image.new("RGB", (E.W, E.H), E.BG)
    d = ImageDraw.Draw(im)
    size = 120
    tw = d.textlength(TITLE, font=E.F(size, mono=True))
    icon_r, gap = 62, 60
    gx = E.W / 2 - (2 * icon_r + gap + tw) / 2          # 收拢后"环 + 课程名"整体居中
    # 阶段一（0–2.2s）：节点出现，亮点沿环走一圈依次点亮；阶段二（2.2–2.9s）：环缩小并移到课程名左侧，成为图标
    k = E.ease((t - 2.2) / 0.7)
    r = RAD + (icon_r - RAD) * k
    cx = CX + (gx + icon_r - CX) * k
    start = -math.pi / 2
    sweep = 2 * math.pi * E.ease((t - 0.3) / 1.9)
    if sweep > 0.01:
        steps = max(2, int(120 * sweep / (2 * math.pi)))
        pts = [_pt(start + sweep * j / steps, r, cx) for j in range(steps + 1)]
        d.line(pts, fill=E.col("gray"), width=max(3, int(8 * (1 - 0.6 * k))), joint="curve")
        if k < 1:
            hx, hy = pts[-1]
            hr = 14 * (1 - k)
            d.ellipse((hx - hr, hy - hr, hx + hr, hy + hr), fill=E.mix("fg", 1 - k))
    for i, (name, c) in enumerate(NODES):
        x, y = _pt(start + 2 * math.pi * i / 3, r, cx)
        lit = E.ease((t - 0.3 - i * 0.6) / 0.3)
        a = E.ease(t / 0.4)
        rr = 78 + (20 - 78) * k
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=E.mix(c, a * (0.35 + 0.65 * lit)))
        if k < 0.6:
            E.text(d, (x, y), name, 40, (20, 20, 24), a * (1 - k / 0.6), bold=True, anchor="mm")
    # 阶段三（2.6s 起）：打字机打出课程名，光标闪烁；副标题淡入
    if t >= 2.6:
        n = min(len(TITLE), int((t - 2.6) / 0.05) + 1)
        sub = TITLE[:n]
        x0 = gx + 2 * icon_r + gap
        E.text(d, (x0, CY), sub, size, "fg", 1, mono=True, anchor="lm")
        cur = x0 + d.textlength(sub, font=E.F(size, mono=True)) + 8
        if n < len(TITLE) or int(t * 3) % 2 == 0:
            d.rectangle((cur, CY - 55, cur + 26, CY + 55), fill=E.col("blue"))
        E.text(d, (E.W / 2, CY + 140), SUB, 40, "dim", E.ease((t - 3.2) / 0.5), anchor="mm")
    return im


def _tone(f0, dur, amp, f1=None, decay=6.0):
    n = int(dur * SR)
    out, ph = [], 0.0
    for i in range(n):
        t = i / SR
        f = f0 if f1 is None else f0 + (f1 - f0) * t / dur
        ph += 2 * math.pi * f / SR
        env = min(1.0, t / 0.008) * math.exp(-decay * t)
        out.append(amp * env * (math.sin(ph) + 0.3 * math.sin(2 * ph) + 0.1 * math.sin(3 * ph)))
    return out


def _read(path):
    with wave.open(str(path)) as w:
        raw = w.readframes(w.getnframes())
    return [v / 32768 for v in struct.unpack(f"<{len(raw) // 2}h", raw)]


def audio(path, cache):
    """三声提示音（环点亮节点）+ 固定口播；返回总时长。"""
    global DUR
    cache = Path(cache)
    raw, trimmed = cache / "intro_vo_raw.wav", cache / "intro_vo.wav"
    E.tts(VOICE, raw)
    if not trimmed.exists():
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(raw), "-af",
                        "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                        "silenceremove=start_periods=1:start_threshold=-45dB,areverse",
                        "-ar", str(SR), "-ac", "1", str(trimmed)], check=True)
    vo = _read(trimmed)
    DUR = max(ANIM, round(VOICE_AT + len(vo) / SR + 0.5, 2))
    out = [0.0] * int(DUR * SR)

    def put(sig, at):
        i0 = int(at * SR)
        for k, v in enumerate(sig):
            if i0 + k < len(out):
                out[i0 + k] += v

    for i, f in enumerate([523.25, 659.25, 783.99]):        # C5 E5 G5：亮点依次点亮三个节点
        put(_tone(f, 0.6, 0.18), 0.3 + i * 0.6)
    put(vo, VOICE_AT)
    pcm = b"".join(struct.pack("<h", int(max(-1.0, min(1.0, v)) * 32767)) for v in out)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm)
    return DUR


def render(out_dir):
    """渲染 intro_silent.mp4 + intro.wav（缓存）；返回 (视频, 音频, 时长)。"""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    vid, wav = out_dir / "intro_silent.mp4", out_dir / "intro.wav"
    dur = audio(wav, out_dir)
    if not vid.exists():
        ff = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{E.W}x{E.H}",
                               "-r", str(E.FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "22",
                               "-pix_fmt", "yuv420p", str(vid)], stdin=subprocess.PIPE)
        for i in range(int(round(dur * E.FPS))):
            ff.stdin.write(frame(i / E.FPS).tobytes())
        ff.stdin.close()
        ff.wait()
    return vid, wav, dur


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "out"))
    a = ap.parse_args()
    v, w, _ = render(a.out)
    final = Path(a.out) / "intro.mp4"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(v), "-i", str(w), "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "128k", "-shortest", str(final)], check=True)
    print(final)
