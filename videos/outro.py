"""课程固定片尾：片头的图标与课程名淡入，下方是"下一讲"（最后一讲为"全课完"）、课程网站和讨论区；
三声提示音倒序（G E C）收尾，Stella 读固定口播。时长随口播长度而定（约 9 秒）。

    python3 videos/outro.py lectures/l01.py --out videos/out    # 单独渲染预览
engine.py 渲染每讲时会自动接在最后（--no-outro 可关闭）。
"""
import argparse
import subprocess
import wave
from pathlib import Path

from PIL import Image, ImageDraw

import engine as E
import intro as I

SR = I.SR
VOICE = "课程网站和讨论区见视频下方。如果你觉得本课程对你有帮助，欢迎点赞、收藏、一键三连，我们下一讲见。"
VOICE_LAST = "课程网站和讨论区见视频下方。如果你觉得本课程对你有帮助，欢迎点赞、收藏、一键三连。感谢你学完整门课。"
VOICE_AT = 0.9
SITE = "odearevanhansen.github.io/agentharness"
DISC = "提问与讨论：GitHub Discussions（github.com/ODearEvanHansen/agentharness）"


def next_title(L):
    """读取下一讲的标题；最后一讲返回 None。"""
    nxt = Path(L["_path"]).with_name(f"l{L['no'] + 1:02d}.py")
    if not nxt.exists():
        return None
    return E.load(str(nxt))["title"]


def frame(t, L, nxt):
    im = Image.new("RGB", (E.W, E.H), E.BG)
    d = ImageDraw.Draw(im)
    a = E.ease(t / 0.6)
    # 图标 + 课程名（与片头定格画面一致，整体上移）
    size, icon_r, gap = 96, 50, 48
    tw = d.textlength(I.TITLE, font=E.F(size, mono=True))
    gx = E.W / 2 - (2 * icon_r + gap + tw) / 2
    cy = 330
    import math
    cx = gx + icon_r
    pts = [(cx + icon_r * math.cos(-math.pi / 2 + 2 * math.pi * k / 120), cy + icon_r * math.sin(-math.pi / 2 + 2 * math.pi * k / 120))
           for k in range(121)]
    d.line(pts, fill=E.mix("gray", a), width=4, joint="curve")
    for i, (_, c) in enumerate(I.NODES):
        ang = -math.pi / 2 + 2 * math.pi * i / 3
        x, y = cx + icon_r * math.cos(ang), cy + icon_r * math.sin(ang)
        d.ellipse((x - 17, y - 17, x + 17, y + 17), fill=E.mix(c, a))
    E.text(d, (gx + 2 * icon_r + gap, cy), I.TITLE, size, "fg", a, mono=True, anchor="lm")
    # 下一讲 / 全课完
    b = E.ease((t - 0.5) / 0.6)
    if nxt:
        E.text(d, (E.W / 2, 520), f"下一讲 · 第 {L['no'] + 1} 讲", 36, "dim", b, anchor="mm")
        E.text(d, (E.W / 2, 590), nxt, 56, "blue", b, bold=True, anchor="mm")
    else:
        E.text(d, (E.W / 2, 560), "全课完 · 感谢学习", 60, "blue", b, bold=True, anchor="mm")
    # 网站与讨论区
    c = E.ease((t - 1.0) / 0.6)
    E.text(d, (E.W / 2, 760), "课程网站：" + SITE, 36, "fg", c, anchor="mm")
    E.text(d, (E.W / 2, 820), DISC, 30, "dim", c, anchor="mm")
    # 高亮："欢迎点赞 · 收藏 · 一键三连"（橙底深色字的胶囊）
    h = E.ease((t - 1.6) / 0.6)
    if h > 0:
        msg, fs = "欢迎点赞 · 收藏 · 一键三连", 40
        w = d.textlength(msg, font=E.F(fs, bold=True))
        y = 930
        d.rounded_rectangle((E.W / 2 - w / 2 - 36, y - 38, E.W / 2 + w / 2 + 36, y + 38), 38, fill=E.mix("orange", h))
        E.text(d, (E.W / 2, y), msg, fs, (20, 20, 24), h, bold=True, anchor="mm")
    return im


def audio(path, cache, last):
    cache = Path(cache)
    text = VOICE_LAST if last else VOICE
    tag = "last" if last else "next"
    raw, trimmed = cache / f"outro_vo_{tag}_raw.wav", cache / f"outro_vo_{tag}.wav"
    E.tts(text, raw)
    if not trimmed.exists():
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(raw), "-af",
                        "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                        "silenceremove=start_periods=1:start_threshold=-45dB,areverse",
                        "-ar", str(SR), "-ac", "1", str(trimmed)], check=True)
    vo = I._read(trimmed)
    dur = round(VOICE_AT + len(vo) / SR + 1.0, 2)
    out = [0.0] * int(dur * SR)

    def put(sig, at):
        i0 = int(at * SR)
        for k, v in enumerate(sig):
            if i0 + k < len(out):
                out[i0 + k] += v

    for i, f in enumerate([783.99, 659.25, 523.25]):        # G5 E5 C5：与片头相反，收尾
        put(I._tone(f, 0.6, 0.16), 0.05 + i * 0.25)
    put(vo, VOICE_AT)
    nf = int(0.4 * SR)
    for i in range(nf):
        out[-nf + i] *= 1 - i / nf
    import struct
    pcm = b"".join(struct.pack("<h", int(max(-1.0, min(1.0, v)) * 32767)) for v in out)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm)
    return dur


def prepare(L, cache):
    """返回 (frame_fn, wav_path, dur)。"""
    nxt = next_title(L)
    cache = Path(cache)
    cache.mkdir(parents=True, exist_ok=True)
    wav = cache / f"outro_{'last' if nxt is None else 'next'}.wav"
    dur = audio(wav, cache, nxt is None)
    return (lambda t: frame(t, L, nxt)), wav, dur


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "out"))
    a = ap.parse_args()
    L = E.load(a.spec)
    L["_path"] = a.spec
    out = Path(a.out)
    fn, wav, dur = prepare(L, out / "build" / "_outro")
    vid = out / f"outro_{L['id']}.mp4"
    ff = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{E.W}x{E.H}",
                           "-r", str(E.FPS), "-i", "-", "-i", str(wav), "-c:v", "libx264", "-crf", "22", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "128k", "-shortest", str(vid)], stdin=subprocess.PIPE)
    for i in range(int(round(dur * E.FPS))):
        ff.stdin.write(fn(i / E.FPS).tobytes())
    ff.stdin.close()
    ff.wait()
    print(vid, dur)
