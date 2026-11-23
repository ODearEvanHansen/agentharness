"""生成 B 站视频简介：本讲一句话 + 本讲看点（meta.json 的 highlights）+ 课程介绍 + 相关链接 + 声明（不列章节时间戳）。

    python3 videos/bilibili/make_desc.py lectures/l02.py

简介长度上限按 B 站 2000 字检查。
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import engine as E  # noqa: E402

SITE = "https://odearevanhansen.github.io/agentharness"
REPO = "https://github.com/ODearEvanHansen/agentharness"
INTRO = ("AgentHarness 是一门免费的中文 Agent 系统公开课：以 DeepSeek Harness（DSH）为底座，"
         "从调用 API、拆解 agent loop、做评测，到上下文与缓存、推理服务、多模型路由和安全，"
         "37 讲 + 6 个动手作业，全部用真实运行数据讲解。只需要一台 Linux 或 WSL2 电脑和自己的 DeepSeek API key，不需要 GPU。")
NOTES = ("说明：画面由程序生成，配音为 AI 合成（DeepSeek TTS）；演示数据均来自课程团队的真实运行。"
         "本课程参考了哈佛 CS2680 的结构，与哈佛大学及 CS2680 课程团队没有任何关联。讲稿与视频采用 CC BY-SA 4.0 许可。")


def mmss(t):
    t = int(round(t))
    return f"{t // 60:02d}:{t % 60:02d}"


def build(spec, chapters_path=None):
    L = E.load(spec)
    lid = Path(spec).stem
    meta = json.loads((HERE / "meta.json").read_text(encoding="utf-8"))
    pts = next((m.get("highlights") or [] for m in meta["lectures"] if m["id"] == lid), [])
    lines = [f"第 {L['no']} 讲：{L['title']}" + (f"——{L['subtitle']}" if L.get("subtitle") else ""), ""]
    if pts:
        lines.append("本讲看点：")
        lines += [f"· {p}" for p in pts]
        lines.append("")
    lines += ["关于课程：", INTRO, "",
              "链接：",
              f"· 本讲讲稿与练习：{SITE}/lectures/{lid}/",
              f"· 课程网站（大纲、作业、环境搭建指南）：{SITE}/",
              f"· 代码与作业仓库：{REPO}",
              f"· 提问与讨论：{REPO}/discussions",
              "", NOTES]
    return "\n".join(lines)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--chapters")
    a = ap.parse_args()
    d = build(a.spec, a.chapters)
    print(d)
    print(f"\n[{len(d)} 字]", file=sys.stderr)
    if len(d) > 2000:
        sys.exit("简介超过 2000 字")
