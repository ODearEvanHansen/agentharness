#!/usr/bin/env python3
"""给 L17 样片配音：逐段用 DeepSeek TTS（stella）合成，按音频时长拉伸画面，输出带配音的 mp4 和 srt 字幕。"""
import json, os, re, subprocess, sys, urllib.request, wave
from pathlib import Path
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import l17  # noqa: E402

NARRATION = [
    "这一讲，我们讨论前缀缓存。同样一个 agent，只是换一种写法，成本就可能相差七倍以上。本视频由程序合成，里面的数据都来自真实运行。",
    "先看价格。DeepSeek flash 的输入分两种：命中缓存的部分，每百万 token 只要零点零四元；没有命中的部分是两元，相差整整五十倍。所以输入能不能命中缓存，几乎决定了 agent 的输入成本。",
    "再看 agent 的请求是什么样的。每一步，agent 都要把系统提示、工具定义和之前的全部消息重新发一遍，再加上这一步新增的一小段内容。只要开头的部分和上一步一字不差，这部分就能命中缓存，我们只需要为新增的那一小段付全价。",
    "这是课程实测的数据。DSH 在二十道 SWE bench 题目上，一共读入了七百六十多万个命中缓存的 token，未命中的只有三十万左右，缓存命中率达到百分之九十六。实际花费约二点二七元；如果完全没有缓存，要花约十七点三元，相差七点六倍。",
    "来看一个反面教材：在系统提示的开头写入当前时间。这看起来人畜无害，但时间每一步都在变，请求的第一个 token 就不一样了。缓存是按前缀匹配的，开头一变，后面的内容再相同也没有用，整个请求都会按未命中计费。",
    "我们用真实的 API 做个实验。同一段对话，用三种写法各跑五步。第一种，系统提示保持不变，从第二步起命中率就在百分之九十五左右。第二种，把时间写进系统提示，五步全部是零。第三种，时间信息还在，但放到最新一条消息里，命中率又回到了百分之九十以上。同样的信息，放在开头还是追加在末尾，结果完全不同。",
    "DSH 把这个原则直接做进了 agent loop。系统提示需要更新时，如果还在同一个 request series 里，并且模型路由支持，DSH 会把新的提示追加到历史末尾，前缀照常命中。只有开启新的 series、或者路由不支持时，才会改写开头。具体逻辑可以在 agent loop 的 README 里找到。",
    "总结一下。缓存按前缀匹配；命中和未命中差五十倍；会变化的信息要放在末尾；系统提示和工具定义要保持稳定，能追加就不要改写。课后练习：用作业一的 DSH Lens，观察你自己的 agent 的命中率曲线，找到它下降的那一步，并解释原因。",
]
OUT = HERE / "build"
OUT.mkdir(exist_ok=True)


def tts(i, text):
    f = OUT / f"n{i}.wav"
    if not f.exists():
        body = json.dumps({"text": text, "voice_id": "stella", "format": "pcm"}).encode()
        req = urllib.request.Request("https://api.deepseek.com/v1/tools/tts", data=body, headers={
            "Authorization": "Bearer " + os.environ["DEEPSEEK_API_KEY"], "Content-Type": "application/json"})
        pcm = urllib.request.urlopen(req, timeout=300).read()   # 24 kHz 16-bit mono
        with wave.open(str(f), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes(pcm)
    with wave.open(str(f)) as w:
        return f, w.getnframes() / w.getframerate()


def fmt(s):
    h, m = divmod(int(s), 3600)
    m, sec = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{sec:02d},{int((s % 1) * 1000):03d}"


def main():
    LEAD, TAIL = 0.8, 1.2
    plan, srt, t0 = [], [], 0.0
    for i, ((orig, fn), text) in enumerate(zip(l17.SCENES, NARRATION)):
        wav, dur_a = tts(i, text)
        dur = max(orig, LEAD + dur_a + TAIL)
        plan.append((orig, fn, dur, wav))
        # 字幕：按句切分，按字数比例分配时间
        sents = [s for s in re.split(r"(?<=[。；？！])", text) if s.strip()]
        total = sum(len(s) for s in sents)
        t = t0 + LEAD
        for s in sents:
            d = dur_a * len(s) / total
            srt.append((t, t + d, s.strip()))
            t += d
        t0 += dur
        print(f"scene {i}: audio {dur_a:.1f}s -> scene {dur:.1f}s", flush=True)
    (OUT / "l17.srt").write_text("".join(f"{k + 1}\n{fmt(a)} --> {fmt(b)}\n{s}\n\n" for k, (a, b, s) in enumerate(srt)))
    # 音轨：每段 = 前置静音 + 配音 + 补足到场景长度
    parts = []
    for k, (_, _, dur, wav) in enumerate(plan):
        p = OUT / f"seg{k}.wav"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(wav), "-af",
                        f"adelay={int(LEAD * 1000)}:all=1,apad=whole_dur={dur}", "-ar", "24000", "-ac", "1", str(p)], check=True)
        parts.append(p)
    (OUT / "list.txt").write_text("".join(f"file '{p}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(OUT / "list.txt"),
                    "-c", "copy", str(OUT / "voice.wav")], check=True)
    # 画面：按新时长拉伸动画时间轴
    W, H, FPS = l17.W, l17.H, l17.FPS
    silent = OUT / "video.mp4"
    ff = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                           "-pix_fmt", "yuv420p", str(silent)], stdin=subprocess.PIPE)
    for orig, fn, dur, _ in plan:
        k = orig / dur
        for i in range(int(round(dur * FPS))):
            t = i / FPS
            img = Image.new("RGB", (W, H), l17.BG)
            fn(ImageDraw.Draw(img), t * k)
            fade = min(1.0, t / 0.4, (dur - t) / 0.4)
            if fade < 1:
                img = Image.blend(Image.new("RGB", (W, H), l17.BG), img, max(0.0, fade))
            ff.stdin.write(img.tobytes())
    ff.stdin.close()
    ff.wait()
    final = HERE / "l13_prefix_cache_voiced.mp4"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(silent), "-i", str(OUT / "voice.wav"),
                    "-i", str(OUT / "l17.srt"), "-map", "0:v", "-map", "1:a", "-map", "2:s", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "128k", "-c:s", "mov_text", "-metadata:s:s:0", "language=chi",
                    "-shortest", "-movflags", "+faststart", str(final)], check=True)
    print("done", final, round(t0, 1), "s")


if __name__ == "__main__":
    main()
