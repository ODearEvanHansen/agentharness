#!/usr/bin/env python3
"""课程合成视频引擎：讲稿规格（Python 模块里的 LECTURE 字典）→ 配音（DeepSeek TTS, stella）+ 逐帧画面 + srt。

用法：
  python videos/engine.py videos/lectures/l03.py            # 生成 out/l03.mp4 和 out/l03.srt
  python videos/engine.py videos/lectures/l03.py --preview  # 只出每个场景的末帧拼图 out/l03_preview.png（不调 TTS）

规格格式（见 lectures/_example.py）：
  LECTURE = {"id": "l03", "no": 3, "title": "...", "subtitle": "...",
             "scenes": [ {"type": "...", "narration": "...", ...}, ... ]}
场景类型（type）：
  title    —— 讲次标题页（AI 合成声明只放这一页）
  bullets  —— title, items: [str], (note)
  bars     —— title, sub, rows: [(label, value, color, display)], (unit), (highlight)
  blocks   —— title, sub, rows: [(row_label, [(text, width, color), ...])], (legend: [(color, text)])
  terminal —— title, sub, cmd, lines: [str]（必须是真实输出；可用 color_rules: [(substr, color)]）
  code     —— title, sub, code: str, (lang)
  compare  —— title, left: (head, [items], color), right: (head, [items], color)
  quote    —— title, text, source
  summary  —— items: [str], (exercise)
每个场景都可带 caption（屏幕下方要点条）。颜色用名字：blue green orange red purple gray dim fg。
配音规则：所有数字和英文都按"读出来的样子"写在 narration 里（例如"百分之九十六""SWE bench"）。
"""
import argparse
import hashlib, importlib.util, json, os, re, subprocess, sys, time, urllib.error, urllib.request, wave
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1920, 1080, 30
FONTDIR = os.environ.get("FONTDIR", os.path.expanduser("~/.fonts"))
FONT, BOLD = FONTDIR + "/NotoSansSC-Regular.otf", FONTDIR + "/NotoSansSC-Bold.otf"
MONO = os.environ.get("MONOFONT", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")
BG = (18, 20, 28)
C = {"fg": (232, 234, 240), "dim": (130, 136, 150), "blue": (88, 140, 255), "green": (70, 200, 120),
     "orange": (255, 150, 60), "red": (240, 80, 80), "purple": (170, 120, 255), "gray": (90, 96, 112),
     "panel": (40, 44, 58), "term": (10, 11, 16)}
_fc = {}


def F(size, bold=False, mono=False):
    k = (size, bold, mono)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(MONO if mono else (BOLD if bold else FONT), size)
    return _fc[k]


def col(c):
    return C[c] if isinstance(c, str) else c


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def mix(c, a):
    c = col(c)
    return tuple(int(BG[i] + (c[i] - BG[i]) * a) for i in range(3))


def wrap(d, s, size, maxw, bold=False, mono=False):
    """按像素宽度折行（中文逐字，英文尽量按词）。"""
    out, line = [], ""
    for tok in re.findall(r"[A-Za-z0-9_\-./:%$#@+=<>'\"`()\[\]{}]+|\s+|.", s):
        trial = line + tok
        if d.textlength(trial, font=F(size, bold, mono)) <= maxw or not line:
            line = trial
        else:
            out.append(line.rstrip())
            line = tok.lstrip()
    if line.strip():
        out.append(line.rstrip())
    return out or [""]


CJK = re.compile(r"[\u2e80-\u9fff\uff00-\uffef\u3000-\u303f]")


def text(d, xy, s, size, color="fg", a=1.0, bold=False, mono=False, anchor="la"):
    if mono and CJK.search(s):
        mono = False   # 等宽字体没有中文字形，含中文的行改用中文字体
    if a > 0:
        d.text(xy, s, font=F(size, bold, mono), fill=mix(color, a), anchor=anchor)


def para(d, x, y, s, size, maxw, color="fg", a=1.0, bold=False, mono=False, lh=1.45):
    for ln in wrap(d, s, size, maxw, bold, mono):
        text(d, (x, y), ln, size, color, a, bold, mono)
        y += int(size * lh)
    return y


def box(d, x, y, w, h, color, label="", a=1.0, size=26, tcolor=(20, 20, 24)):
    if w <= 1 or a <= 0:
        return
    d.rounded_rectangle((x, y, x + w, y + h), 10, fill=mix(color, a * 0.9))
    if label and w > d.textlength(label, font=F(size)) + 16:
        text(d, (x + w / 2, y + h / 2), label, size, tcolor, a, bold=True, anchor="mm")


class Ctx:
    def __init__(self, lec):
        self.lec = lec


def chrome(d, t, L, title, sub=None):
    text(d, (80, 56), f"第 {L['no']} 讲 · {L['title']}", 26, "dim")
    if title:
        text(d, (80, 112), title, 54, "fg", ease(t / 0.6), bold=True)
    if sub:
        para(d, 80, 192, sub, 30, W - 160, "dim", ease((t - 0.3) / 0.6))


def caption(d, t, s, start):
    a = ease((t - start) / 0.5)
    if not s or a <= 0:
        return
    lines = wrap(d, s, 34, W - 320)
    hh = 54 * len(lines) + 16
    w = max(d.textlength(l, font=F(34)) for l in lines)
    y0 = H - 70 - hh
    d.rounded_rectangle((W / 2 - w / 2 - 30, y0, W / 2 + w / 2 + 30, H - 70), 16, fill=mix("panel", a))
    for i, l in enumerate(lines):
        text(d, (W / 2, y0 + 8 + 27 + i * 54), l, 34, "fg", a, anchor="mm")


def takeaway(d, t, s, start):
    """本幕要点：左下角、左侧色条 + "要点"标签，和逐句字幕区分开。"""
    a = ease((t - start) / 0.5)
    if not s or a <= 0:
        return
    lines = wrap(d, s, 30, W - 420)
    y0 = H - 80 - 44 * len(lines)
    d.rectangle((80, y0 - 6, 88, H - 74), fill=mix("orange", a))
    text(d, (108, y0), "要点", 26, "orange", a, bold=True)
    for i, ln in enumerate(lines):
        text(d, (180, y0 + i * 44), ln, 30, "fg", a)


# ------------------------------------------------------------------ scene renderers: fn(d, t, S, L) with t in [0, 10]
def r_title(d, t, S, L):
    text(d, (W / 2, 380), f"第 {L['no']} 讲", 48, "dim", ease(t / 1), anchor="mm")
    lines = wrap(d, L["title"], 88, W - 300, bold=True)
    for i, ln in enumerate(lines):
        text(d, (W / 2, 490 + i * 110), ln, 88, "fg", ease(t / 1), bold=True, anchor="mm")
    y = 490 + len(lines) * 110 + 20
    if L.get("subtitle"):
        text(d, (W / 2, y), L["subtitle"], 42, "blue", ease((t - 1) / 1), anchor="mm")
    text(d, (W / 2, 900), "AgentHarness · 基于 DeepSeek Harness 的 Agent 系统公开课", 28, "dim", ease((t - 2) / 1), anchor="mm")
    text(d, (W / 2, 950), "AI 合成：画面由程序生成，配音由 DeepSeek TTS 合成；演示数据均为真实运行结果", 24, "dim", ease((t - 2) / 1), anchor="mm")


def r_bullets(d, t, S, L):
    chrome(d, t, L, S["title"], S.get("sub"))
    items = S["items"]
    y = 300 if S.get("sub") else 250
    step = 7.0 / max(1, len(items))
    for i, it in enumerate(items):
        a = ease((t - 0.8 - i * step) / 0.6)
        d.ellipse((110, y + 16, 130, y + 36), fill=mix("blue", a))
        y = para(d, 160, y, it, 38, W - 320, "fg", a) + 22
    if S.get("note"):
        para(d, 110, y + 20, S["note"], 30, W - 260, "dim", ease((t - 8) / 0.6))


def r_bars(d, t, S, L):
    chrome(d, t, L, S["title"], S.get("sub"))
    rows = S["rows"]
    vmax = max(r[1] for r in rows) or 1
    n = len(rows)
    gap = min(140, 520 // max(1, n))
    y0 = 320
    labw = max(d.textlength(r[0], font=F(36)) for r in rows) + 60
    maxw = W - 200 - labw - 260
    for i, (lab, v, c, disp) in enumerate(rows):
        a = ease((t - 0.8 - i * 0.8) / 0.6)
        y = y0 + i * gap
        text(d, (120, y + 12), lab, 36, "fg", a)
        bw = maxw * (v / vmax) * ease((t - 1.0 - i * 0.8) / 1.2)
        box(d, 120 + labw, y, max(bw, 6 if a > 0 else 0), min(70, gap - 20), c, "", a)
        text(d, (140 + labw + max(bw, 6), y + 10), disp, 38, c, a, bold=True)
    if S.get("highlight"):
        text(d, (W / 2, y0 + n * gap + 60), S["highlight"], 56, S.get("highlight_color", "green"),
             ease((t - 1.5 - n * 0.8) / 0.8), bold=True, anchor="mm")


def r_blocks(d, t, S, L):
    chrome(d, t, L, S["title"], S.get("sub"))
    rows = S["rows"]
    step = 6.0 / max(1, len(rows))
    gap = min(110, 560 // max(1, len(rows)))
    for k, (lab, segs) in enumerate(rows):
        a = ease((t - 0.8 - k * step) / 0.6)
        y = 300 + k * gap
        text(d, (90, y + 20), lab, 30, "dim", a)
        x = 300
        total = sum(s[1] for s in segs) + 8 * len(segs)
        scale = min(1.0, (W - 380) / max(1, total))
        for s in segs:
            box(d, x, y, s[1] * scale, gap - 30, s[2], s[0], a, 24 if s[1] * scale > 150 else 20)
            x += s[1] * scale + 8
    for i, (c, s) in enumerate(S.get("legend", [])):
        a = ease((t - 7) / 0.6)
        y = 300 + len(rows) * gap + 20 + i * 50
        box(d, 300, y, 36, 36, c, "", a)
        text(d, (350, y - 2), s, 28, "fg", a)


def r_terminal(d, t, S, L):
    chrome(d, t, L, S["title"], S.get("sub"))
    top = 280 if S.get("sub") else 230
    bottom = H - 200
    d.rounded_rectangle((80, top, W - 80, bottom), 18, fill=C["term"])
    for i, c in enumerate(("red", "orange", "green")):
        d.ellipse((110 + i * 36, top + 22, 132 + i * 36, top + 44), fill=C[c])
    lines = ["$ " + S["cmd"]] + list(S["lines"])
    size = 24
    lh = 31
    maxl = (bottom - top - 90) // lh
    lines = [ln for l in lines for ln in wrap(d, l, size, W - 260, mono=True)]
    shown = int(max(0, t - 0.5) * max(3.0, len(lines) / 6.0))
    vis = lines[:shown][-maxl:]
    y = top + 70
    rules = S.get("color_rules", [])
    for l in vis:
        cc = "green" if l.startswith("$ ") else "fg"
        for sub, c in rules:
            if sub in l:
                cc = c
                break
        text(d, (120, y), l, size, cc, mono=True)
        y += lh
    if shown < len(lines) and int(t * 2) % 2 == 0:
        d.rectangle((120, y + 4, 134, y + 28), fill=C["fg"])


def r_code(d, t, S, L):
    chrome(d, t, L, S["title"], S.get("sub"))
    top = 280 if S.get("sub") else 230
    d.rounded_rectangle((80, top, W - 80, H - 200), 18, fill=C["term"])
    lines = S["code"].rstrip("\n").split("\n")
    n = int(max(0, t - 0.5) * max(4, len(lines) / 5))
    y = top + 30
    for i, l in enumerate(lines[:n][:22]):
        c = "dim" if l.strip().startswith(("#", "//")) else ("purple" if re.match(r"\s*(def|class|import|from|export|function|return|if|for|async|await)\b", l) else "fg")
        text(d, (110, y), f"{i + 1:>3}  " + l, 25, c, mono=True)
        y += 33


def r_compare(d, t, S, L):
    chrome(d, t, L, S["title"], S.get("sub"))
    top = 300 if S.get("sub") else 250
    for side, (head, items, c) in enumerate((S["left"], S["right"])):
        x = 100 + side * (W - 200) // 2
        w = (W - 240) // 2
        a = ease((t - 0.8 - side * 3.5) / 0.6)
        d.rounded_rectangle((x, top, x + w, H - 200), 20, fill=mix("panel", a))
        text(d, (x + 40, top + 30), head, 40, c, a, bold=True)
        y = top + 110
        for i, it in enumerate(items):
            ai = ease((t - 1.3 - side * 3.5 - i * 0.6) / 0.5)
            text(d, (x + 40, y), "•", 34, c, ai)
            y = para(d, x + 80, y, it, 32, w - 120, "fg", ai) + 16


def r_quote(d, t, S, L):
    chrome(d, t, L, S["title"], None)
    a = ease((t - 0.6) / 0.8)
    d.rectangle((110, 300, 118, 300 + 60 * len(wrap(d, S["text"], 38, W - 400))), fill=mix("blue", a))
    y = para(d, 150, 300, S["text"], 38, W - 400, "fg", a, lh=1.55)
    para(d, 150, y + 30, "出处：" + S["source"], 26, W - 400, "dim", ease((t - 2) / 0.6))


def r_summary(d, t, S, L):
    chrome(d, t, L, "小结", None)
    y = 250
    step = 6.0 / max(1, len(S["items"]))
    for i, p in enumerate(S["items"]):
        a = ease((t - 0.6 - i * step) / 0.6)
        d.ellipse((110, y + 16, 130, y + 36), fill=mix("green", a))
        y = para(d, 160, y, p, 38, W - 320, "fg", a) + 20
    if S.get("exercise"):
        para(d, 110, y + 30, "课后：" + S["exercise"], 32, W - 260, "blue", ease((t - 7) / 0.6))


R = {"title": r_title, "bullets": r_bullets, "bars": r_bars, "blocks": r_blocks, "terminal": r_terminal,
     "code": r_code, "compare": r_compare, "quote": r_quote, "summary": r_summary}


# ------------------------------------------------------------------ build
EXT_SPOKEN = {"md": "M D", "py": "P Y", "json": "jason", "jsonl": "jason L", "yaml": "yaml", "toml": "toml",
              "sh": "S H", "txt": "text", "mp4": "M P 4"}
FILE_RE = re.compile(r"\b([A-Za-z][A-Za-z0-9_]*)\.(md|py|jsonl|json|yaml|toml|sh|txt|mp4)\b")


def spoken(text_):
    """只改送给 TTS 的文本，字幕/画面不变：AGENTS.md → agents dot M D，避免逐字母拼读。"""
    def sub(m):
        stem = m.group(1).replace("_", " ")
        return f" {stem.lower() if stem.isupper() else stem} dot {EXT_SPOKEN[m.group(2)]} "
    return FILE_RE.sub(sub, text_)


def tts(text_, f):
    text_ = spoken(text_)
    if f.exists():
        with wave.open(str(f)) as w:
            return w.getnframes() / w.getframerate()
    body = json.dumps({"text": text_, "voice_id": "stella", "format": "pcm"}).encode()
    req = urllib.request.Request("https://api.deepseek.com/v1/tools/tts", data=body, headers={
        "Authorization": "Bearer " + os.environ["DEEPSEEK_API_KEY"], "Content-Type": "application/json"})
    for attempt in range(4):
        try:
            pcm = urllib.request.urlopen(req, timeout=300).read()
            break
        except urllib.error.HTTPError as e:
            if e.code in (429, 503, 504) and attempt < 3:

                time.sleep(5 * (attempt + 1))
                continue
            raise
    with wave.open(str(f), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(pcm)
    return len(pcm) / 2 / 24000


def frame(S, L, t10, dur, t):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    R[S["type"]](d, t10, S, L)
    # 视频里不放字幕（课程决定）。scene 的 caption 是本幕"要点"，以左下角标签样式出现，不是逐句字幕。
    if S["type"] != "title":
        takeaway(d, t10, S.get("caption"), 8.5)
    fade = min(1.0, t / 0.4, (dur - t) / 0.4)
    if fade < 1:
        img = Image.blend(Image.new("RGB", (W, H), BG), img, max(0.0, fade))
    return img


def fmt(s):
    h, m = divmod(int(s), 3600)
    m, sec = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{sec:02d},{int((s % 1) * 1000):03d}"


def load(path):
    spec = importlib.util.spec_from_file_location("lec", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.LECTURE


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--out", default=os.environ.get("VIDEO_OUT", str(Path(__file__).resolve().parent / "out")))
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--no-intro", action="store_true", help="不加固定片头")
    ap.add_argument("--no-outro", action="store_true", help="不加固定片尾")
    a = ap.parse_args()
    L = load(a.spec)
    L["_path"] = a.spec
    out = Path(a.out)
    build = out / "build" / L["id"]
    build.mkdir(parents=True, exist_ok=True)
    scenes = L["scenes"]
    for S in scenes:
        assert S["type"] in R, S["type"]
    if a.preview:
        thumbs = [frame(S, L, 9.9, 10, 5).resize((640, 360)) for S in scenes]
        cols = 3
        sheet = Image.new("RGB", (640 * cols, 360 * ((len(thumbs) + cols - 1) // cols)), (0, 0, 0))
        for i, th in enumerate(thumbs):
            sheet.paste(th, ((i % cols) * 640, (i // cols) * 360))
        p = out / f"{L['id']}_preview.png"
        sheet.save(p)
        print(p)
        return
    LEAD, TAIL = 0.8, 1.2
    plan, srt, t0 = [], [], 0.0
    intro = None
    if not a.no_intro:
        import intro as I
        _, iwav, idur = I.render(out / "build" / "_intro")
        intro = (I, iwav, idur)
        t0 = idur
    for i, S in enumerate(scenes):
        wav = build / f"n{i}_{hashlib.sha1(S['narration'].encode()).hexdigest()[:10]}.wav"   # 按口播文本缓存，改稿后自动重新合成
        da = tts(S["narration"], wav)
        dur = LEAD + da + TAIL
        plan.append((S, dur, wav))
        sents = [s for s in re.split(r"(?<=[。；？！])", S["narration"]) if s.strip()]
        tot = sum(len(s) for s in sents)
        tt = t0 + LEAD
        for s in sents:
            dd = da * len(s) / tot
            srt.append((tt, tt + dd, s.strip()))
            tt += dd
        t0 += dur
        print(f"  scene {i} {S['type']:8} {dur:5.1f}s", flush=True)
    # 章节时间点（B 站简介里的时间戳可点击跳转）
    chapters, tt = [], (intro[2] if intro else 0.0)
    for S, dur, _ in plan:
        name = S.get("title") or ("开场" if S["type"] == "title" else "小结" if S["type"] == "summary" else "")
        if name:
            chapters.append({"t": round(tt, 1), "title": name})
        tt += dur
    (out / f"{L['id']}.chapters.json").write_text(json.dumps(chapters, ensure_ascii=False, indent=1))
    outro = None
    if not a.no_outro:
        import outro as O
        outro = O.prepare(L, out / "build" / "_outro")
    (out / f"{L['id']}.srt").write_text("".join(f"{k + 1}\n{fmt(x)} --> {fmt(y)}\n{s}\n\n" for k, (x, y, s) in enumerate(srt)))
    parts = [intro[1]] if intro else []
    for k, (S, dur, wav) in enumerate(plan):
        p = build / f"seg{k}.wav"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(wav), "-af",
                        f"adelay={int(LEAD * 1000)}:all=1,apad=whole_dur={dur}", "-ar", "24000", "-ac", "1", str(p)], check=True)
        parts.append(p)
    if outro:
        parts.append(outro[1])
    (build / "list.txt").write_text("".join(f"file '{p}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(build / "list.txt"),
                    "-c", "copy", str(build / "voice.wav")], check=True)
    silent = build / "video.mp4"
    ff = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "22", "-tune", "stillimage",
                           "-pix_fmt", "yuv420p", str(silent)], stdin=subprocess.PIPE)
    if intro:
        for i in range(int(round(intro[2] * FPS))):
            ff.stdin.write(intro[0].frame(i / FPS).tobytes())
    for S, dur, _ in plan:
        n = int(round(dur * FPS))
        for i in range(n):
            t = i / FPS
            ff.stdin.write(frame(S, L, t * 10 / dur, dur, t).tobytes())
    if outro:
        for i in range(int(round(outro[2] * FPS))):
            ff.stdin.write(outro[0](i / FPS).tobytes())
    ff.stdin.close()
    ff.wait()
    final = out / f"{L['id']}.mp4"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(silent), "-i", str(build / "voice.wav"),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
                    "-metadata", "comment=AIGC: 画面由程序生成，配音由 DeepSeek TTS 合成（AgentHarness 公开课）",
                    "-metadata", "description=AI-generated content (synthetic video and voice)",
                    "-shortest", "-movflags", "+faststart", str(final)], check=True)
    print("done", final, f"{t0 + (outro[2] if outro else 0):.0f}s")


if __name__ == "__main__":
    main()
