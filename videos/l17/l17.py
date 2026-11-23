#!/usr/bin/env python3
"""第 17 讲样片：前缀缓存与 request series（无声，画面字幕）。Pillow 逐帧绘制 → ffmpeg 编码。"""
import math, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1920, 1080, 30
import os
FONTDIR = os.environ.get("FONTDIR", os.path.expanduser("~/.fonts"))
FONT = FONTDIR + "/NotoSansSC-Regular.otf"
BOLD = FONTDIR + "/NotoSansSC-Bold.otf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
_fc = {}


def F(size, bold=False, mono=False):
    k = (size, bold, mono)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(MONO if mono else (BOLD if bold else FONT), size)
    return _fc[k]


BG = (18, 20, 28); FG = (232, 234, 240); DIM = (130, 136, 150)
BLUE = (88, 140, 255); GREEN = (70, 200, 120); ORANGE = (255, 150, 60); RED = (240, 80, 80); PURPLE = (170, 120, 255)
GRAY = (60, 64, 78)


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def mix(c, a):
    return tuple(int(BG[i] + (c[i] - BG[i]) * a) for i in range(3))


def text(d, xy, s, size, color=FG, a=1.0, bold=False, mono=False, anchor="la"):
    d.text(xy, s, font=F(size, bold, mono), fill=mix(color, a), anchor=anchor)


def chrome(d, t, title, sub=None):
    text(d, (80, 60), "第 17 讲 · 前缀缓存与 request series", 28, DIM)
    text(d, (W - 80, 60), "AI 合成视频", 24, DIM, anchor="ra")
    text(d, (80, 120), title, 56, FG, ease(t / 0.6), bold=True)
    if sub:
        text(d, (80, 200), sub, 32, DIM, ease((t - 0.3) / 0.6))


def caption(d, t, s, start=0.5):
    a = ease((t - start) / 0.5)
    if a <= 0:
        return
    w = d.textlength(s, font=F(36))
    d.rounded_rectangle((W / 2 - w / 2 - 30, H - 140, W / 2 + w / 2 + 30, H - 70), 16, fill=mix((40, 44, 58), a))
    text(d, (W / 2, H - 105), s, 36, FG, a, anchor="mm")


def block(d, x, y, w, h, color, label, a=1.0, size=26):
    if w <= 1 or a <= 0:
        return
    d.rounded_rectangle((x, y, x + w, y + h), 10, fill=mix(color, a * 0.9))
    if label and w > d.textlength(label, font=F(size)) + 16:
        text(d, (x + w / 2, y + h / 2), label, size, (20, 20, 24), a, bold=True, anchor="mm")


# ---------------------------------------------------------------- scenes  (dur, fn(d, t))
def s_title(d, t):
    a = ease(t / 1.0)
    text(d, (W / 2, 400), "第 17 讲", 48, DIM, a, anchor="mm")
    text(d, (W / 2, 500), "前缀缓存与 request series", 96, FG, a, bold=True, anchor="mm")
    text(d, (W / 2, 620), "为什么同一个 agent，换个写法就贵 7 倍", 44, BLUE, ease((t - 1) / 1), anchor="mm")
    text(d, (W / 2, 900), "AgentHarness · 基于 DeepSeek Harness 的 Agent 系统公开课", 28, DIM, ease((t - 2) / 1), anchor="mm")
    text(d, (W / 2, 950), "本视频由程序合成（画面、字幕与 DeepSeek TTS 配音），数据均为真实运行结果", 24, DIM, ease((t - 2) / 1), anchor="mm")


def s_price(d, t):
    chrome(d, t, "先看价格", "deepseek-flash 官方价格（高峰时段，元 / 百万 token）")
    rows = [("输入 · 缓存命中", 0.04, GREEN), ("输入 · 缓存未命中", 2, ORANGE), ("输出", 8, PURPLE)]
    for i, (name, p, c) in enumerate(rows):
        y = 340 + i * 150
        a = ease((t - 0.8 - i * 0.6) / 0.6)
        text(d, (120, y + 20), name, 40, FG, a)
        bw = 1100 * (p / 8) * ease((t - 1.0 - i * 0.6) / 1.2)
        block(d, 560, y, max(bw, 6 if a > 0 else 0), 70, c, "", a)
        text(d, (580 + max(bw, 6), y + 15), f"{p:g} 元", 40, c, a, bold=True)
    if t > 4.5:
        a = ease((t - 4.5) / 0.8)
        text(d, (W / 2, 830), "命中 vs 未命中：差 50 倍", 64, GREEN, a, bold=True, anchor="mm")
    caption(d, t, "同样的输入 token，能否命中缓存，价格相差 50 倍", 6.5)


def s_agent(d, t):
    chrome(d, t, "agent 的请求长什么样", "每一步都把\"之前的全部内容\"重新发一遍，再加上一点新内容")
    segs = [("system 提示", 260, BLUE), ("工具定义", 420, PURPLE)]
    steps = 5
    for k in range(steps):
        a = ease((t - 1.0 - k * 1.6) / 0.6)
        if a <= 0:
            continue
        y = 300 + k * 110
        text(d, (90, y + 22), f"第 {k + 1} 步", 32, DIM, a)
        x = 260
        reused = k > 0 and t > 1.0 + k * 1.6 + 0.6
        for name, w, c in segs:
            block(d, x, y, w, 70, GREEN if reused else c, name, a)
            x += w + 8
        for j in range(k + 1):
            w = 120
            new = j == k
            block(d, x, y, w, 70, ORANGE if (new or not reused) else GREEN, f"消息{j + 1}", a, 22)
            x += w + 8
    if t > 9.2:
        a = ease((t - 9.2) / 0.6)
        block(d, 1500, 330, 40, 40, GREEN, "", a); text(d, (1560, 330), "与上一步相同 → 命中缓存", 28, FG, a)
        block(d, 1500, 400, 40, 40, ORANGE, "", a); text(d, (1560, 400), "新增内容 → 未命中", 28, FG, a)
    caption(d, t, "只要开头一字不差，前面的部分就能命中缓存：只为新增的一小段付全价", 9.5)


def s_data(d, t):
    chrome(d, t, "真实数据：DSH 跑 20 道 SWE-bench 题", "课程 M0 实测，deepseek-flash，高峰价")
    items = [("缓存命中的输入", "763.7 万 token", GREEN), ("未命中的输入", "30.8 万 token", ORANGE), ("输出", "16.8 万 token", PURPLE)]
    for i, (k, v, c) in enumerate(items):
        a = ease((t - 0.8 - i * 0.5) / 0.5)
        text(d, (160, 320 + i * 90), k, 40, FG, a)
        text(d, (700, 320 + i * 90), v, 40, c, a, bold=True)
    a = ease((t - 3) / 0.6)
    text(d, (160, 640), "缓存命中率 96%", 48, GREEN, a, bold=True)
    for i, (k, v, c, frac) in enumerate([("实际花费", "2.27 元", GREEN, 0.34 / 2.59), ("如果完全没有缓存", "17.3 元", RED, 1.0)]):
        a = ease((t - 4 - i * 1.0) / 0.6)
        y = 760 + i * 100
        text(d, (160, y + 10), k, 36, FG, a)
        block(d, 600, y, 1000 * frac * ease((t - 4.2 - i * 1.0) / 1.0), 64, c, "", a)
        text(d, (620 + 1000 * frac * ease((t - 4.2 - i * 1.0) / 1.0), y + 8), v, 40, c, a, bold=True)
    caption(d, t, "缓存让这 20 道题便宜了 7.6 倍：agent 的成本，主要由命中率决定", 6.5)


def s_anti(d, t):
    chrome(d, t, "反面教材：在系统提示里写入\"当前时间\"", "看起来无害的一行，让第一个 token 每一步都不一样")
    for k in range(4):
        a = ease((t - 0.8 - k * 1.0) / 0.5)
        if a <= 0:
            continue
        y = 320 + k * 110
        text(d, (90, y + 22), f"第 {k + 1} 步", 32, DIM, a)
        block(d, 260, y, 300, 70, RED, f"时间 10:00:0{k}", a, 24)
        block(d, 568, y, 260, 70, ORANGE, "system 提示", a)
        block(d, 836, y, 420, 70, ORANGE, "工具定义", a)
        x = 1264
        for j in range(k + 1):
            block(d, x, y, 110, 70, ORANGE, f"消息{j + 1}", a, 20)
            x += 118
    if t > 5:
        a = ease((t - 5) / 0.6)
        text(d, (W / 2, 820), "从第一个 token 起就对不上 → 整个请求都按未命中计费", 44, RED, a, bold=True, anchor="mm")
    caption(d, t, "缓存按前缀匹配：开头变了，后面再相同也没用", 6.5)


DEMO = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_out.txt")).read().strip().splitlines()


def s_demo(d, t):
    chrome(d, t, "实测：同一段对话，三种写法", "真实调用 DeepSeek API（cache_demo.py），每种写法 5 步，系统提示约 3k token")
    d.rounded_rectangle((80, 260, W - 80, 920), 18, fill=(10, 11, 16))
    for i, c in enumerate((RED, ORANGE, GREEN)):
        d.ellipse((110 + i * 36, 285, 132 + i * 36, 307), fill=c)
    lines = ["$ python cache_demo.py stable timestamp append"] + [l for l in DEMO if l.strip()]
    shown = int(max(0, t - 0.8) * 4.2)
    y = 340
    for i, l in enumerate(lines[:shown]):
        color = FG
        if l.startswith("==="):
            color = {"stable": GREEN, "timestamp": RED, "append": BLUE}.get(l.split()[1], FG)
        elif "hit_rate=" in l:
            r = float(l.split("hit_rate=")[1].strip().rstrip("%"))
            color = GREEN if r > 50 else (RED if "step 1" not in l else DIM)
        text(d, (120, y), l, 23, color, mono=True)
        y += 29
    if shown < len(lines) and int(t * 2) % 2 == 0:
        d.rectangle((120, y + 4, 136, y + 30), fill=FG)
    if t > 7.5:
        a = ease((t - 7.5) / 0.6)
        x0 = 1260
        text(d, (x0, 360), "stable：系统提示不变", 30, GREEN, a, bold=True)
        text(d, (x0, 400), "第 2 步起命中 ~95%", 28, FG, a)
        text(d, (x0, 480), "timestamp：时间写进系统提示", 30, RED, ease((t - 8.3) / 0.6), bold=True)
        text(d, (x0, 520), "5 步全部 0% 命中", 28, FG, ease((t - 8.3) / 0.6))
        text(d, (x0, 600), "append：时间放进最新消息", 30, BLUE, ease((t - 9.1) / 0.6), bold=True)
        text(d, (x0, 640), "92–95%，和 stable 几乎一样", 28, FG, ease((t - 9.1) / 0.6))
    caption(d, t, "同样的信息，放在开头还是追加在末尾，结果天差地别", 10)


def s_dsh(d, t):
    chrome(d, t, "DSH 的做法：request series", "系统提示要变时，DSH 会判断：追加，还是改写开头？")
    # lane 1: append
    a1 = ease((t - 0.8) / 0.6)
    text(d, (100, 320), "同一个 series 内，路由支持 in-history 更新", 34, GREEN, a1, bold=True)
    x = 100
    for name, w, c in (("system v1", 260, GREEN), ("工具定义", 360, GREEN), ("历史消息…", 420, GREEN)):
        block(d, x, 380, w, 70, c, name, a1); x += w + 8
    a2 = ease((t - 2.2) / 0.6)
    block(d, x, 380, 260, 70, ORANGE, "system v2（追加）", a2, 24)
    text(d, (100, 470), "→ 新提示追加在已缓存的历史之后，前缀照常命中", 30, FG, a2)
    # lane 2: consolidate
    a3 = ease((t - 4.0) / 0.6)
    text(d, (100, 580), "开启新 series 且文本变化，或路由不支持", 34, RED, a3, bold=True)
    x = 100
    for name, w, c in (("system v2（改写开头）", 360, ORANGE), ("工具定义", 360, ORANGE), ("历史消息…", 420, ORANGE)):
        block(d, x, 640, w, 70, c, name, a3, 24); x += w + 8
    text(d, (100, 730), "→ 从第一个 token 起不同，整段未命中；只在必要时（如压缩后）才这么做", 30, FG, a3)
    a4 = ease((t - 6.0) / 0.6)
    text(d, (100, 850), "出处：packages/core/agent-loop/README.md（dsh-v0.2.2-rc.2）第 122、166 行", 26, DIM, a4, mono=False)
    caption(d, t, "DSH 把\"保持前缀稳定\"做进了 loop：能追加就不改写", 7)


def s_summary(d, t):
    chrome(d, t, "小结", None)
    pts = ["缓存按前缀匹配：开头一个 token 不同，后面全部未命中",
           "命中与未命中差 50 倍；真实 agent 命中率 96% → 成本降 7.6 倍",
           "会变化的信息（时间、状态）放在末尾，不要放进 system 开头",
           "工具定义、系统提示保持字节级稳定；改动尽量\"追加\"而非\"改写\""]
    for i, p in enumerate(pts):
        a = ease((t - 0.6 - i * 0.9) / 0.6)
        d.ellipse((110, 330 + i * 110 + 14, 130, 330 + i * 110 + 34), fill=mix(GREEN, a))
        text(d, (160, 330 + i * 110), p, 40, FG, a)
    a = ease((t - 5) / 0.6)
    text(d, (110, 820), "课后练习：用 A1 的 DSH-Lens 观察你自己 agent 的命中率曲线，找出它下降的那一步，并解释原因", 32, BLUE, a)


SCENES = [(8, s_title), (12, s_price), (17, s_agent), (14, s_data), (11, s_anti), (19, s_demo), (14, s_dsh), (12, s_summary)]


def main(out):
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                           "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for dur, fn in SCENES:
        n = int(dur * FPS)
        for i in range(n):
            t = i / FPS
            img = Image.new("RGB", (W, H), BG)
            d = ImageDraw.Draw(img)
            fn(d, t)
            fade = min(1.0, t / 0.4, (dur - t) / 0.4)
            if fade < 1:
                img = Image.blend(Image.new("RGB", (W, H), BG), img, max(0.0, fade))
            ff.stdin.write(img.tobytes())
    ff.stdin.close()
    ff.wait()
    print("done", out, sum(s[0] for s in SCENES), "s")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "l13_prefix_cache.mp4")
