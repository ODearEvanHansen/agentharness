#!/usr/bin/env python3
"""把仓库内容组装成课程网站源文件（site_src/），再由 mkdocs-material 构建。

  python scripts/build_site.py && mkdocs build      # 本地预览：mkdocs serve

页面来源：
  index         ← README.md
  syllabus      ← docs/syllabus.md
  assignments/  ← assignmentN/README.md（以及 A2 的 QUESTIONS.md）
  lectures/     ← videos/lectures/lXX.py（讲义正文取自配音讲稿；视频链接见 videos/bilibili.json）
  infra         ← infra/README.md
仓库内相对链接会改写为 GitHub 链接，保证站内站外都能点。
"""
import importlib.util, json, re, shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "site_src"
GH = "https://github.com/ODearEvanHansen/agentharness"
ASSIGN_NAMES = {0: "环境自检", 1: "DSH-Lens", 2: "madsLoop", 3: "DSH-Opt", 4: "DSH-Serve", 5: "DSH-Stack"}


def fix_links(md: str, src: Path) -> str:
    """把指向仓库文件的相对链接改成站内页面或 GitHub 链接。"""
    def repl(m):
        text, target = m.group(1), m.group(2)
        if re.match(r"^(https?:|mailto:|#)", target):
            return m.group(0)
        path, _, frag = target.partition("#")
        p = (src.parent / path).resolve()
        try:
            rel = p.relative_to(REPO)
        except ValueError:
            return m.group(0)
        r = str(rel)
        site_map = {"README.md": "index.md", "docs/syllabus.md": "syllabus.md", "infra/README.md": "infra.md",
                    "assignment2/QUESTIONS.md": "assignments/a2-questions.md"}
        mm = re.match(r"assignment(\d)(/README\.md|/?)$", r)
        if r in site_map or mm:
            page = site_map.get(r) or f"assignments/a{mm.group(1)}.md"
            here = OUT / site_rel(src)
            relp = Path(*([".."] * (len(here.relative_to(OUT).parts) - 1)), page)
            return f"[{text}]({relp.as_posix()}{'#' + frag if frag else ''})"
        kind = "tree" if p.is_dir() else "blob"
        return f"[{text}]({GH}/{kind}/main/{r}{'#' + frag if frag else ''})"
    return re.sub(r"\[([^\]]*)\]\(([^)\s]+)\)", repl, md)


def site_rel(src: Path) -> str:
    r = str(src.relative_to(REPO))
    if r == "README.md":
        return "index.md"
    if r == "docs/syllabus.md":
        return "syllabus.md"
    if r == "infra/README.md":
        return "infra.md"
    if r == "assignment2/QUESTIONS.md":
        return "assignments/a2-questions.md"
    m = re.match(r"assignment(\d)/README\.md", r)
    return f"assignments/a{m.group(1)}.md" if m else r


def copy_md(src: Path):
    dst = OUT / site_rel(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(fix_links(src.read_text(encoding="utf-8"), src))


def load_lecture(p: Path):
    spec = importlib.util.spec_from_file_location(p.stem, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.LECTURE


def lecture_page(L, videos):
    lines = [f"# 第 {L['no']} 讲 · {L['title']}", ""]
    if L.get("subtitle"):
        lines += [f"*{L['subtitle']}*", ""]
    v = videos.get(L["id"])
    if v:
        lines += [f'<div class="video"><iframe src="https://player.bilibili.com/player.html?bvid={v}&autoplay=0&high_quality=1" '
                  'allowfullscreen="true" frameborder="0"></iframe></div>', "",
                  f"[在 B 站观看](https://www.bilibili.com/video/{v})", ""]
    else:
        lines += ['!!! info "视频制作中"', "    本讲视频将发布在 B 站，届时在这里嵌入播放。下面是讲稿正文。", ""]
    for i, S in enumerate(L["scenes"]):
        t = S["type"]
        if t == "title":
            lines += [S["narration"], ""]
            continue
        head = S.get("title") or ("小结" if t == "summary" else "")
        if head:
            lines += [f"## {head}", ""]
        if S.get("sub"):
            lines += [f"*{S['sub']}*", ""]
        if t in ("bullets", "summary"):
            lines += [f"- {it}" for it in S["items"]] + [""]
        elif t == "bars":
            lines += ["| 项目 | 数值 |", "|---|---|"] + [f"| {r[0]} | {r[3]} |" for r in S["rows"]] + [""]
        elif t == "terminal":
            lines += ["```console", "$ " + S["cmd"], *S["lines"], "```", ""]
        elif t == "code":
            lines += [f"```{S.get('lang', '')}", S["code"].rstrip("\n"), "```", ""]
        elif t == "compare":
            for head2, items, _ in (S["left"], S["right"]):
                lines += [f"**{head2}**", ""] + [f"- {it}" for it in items] + [""]
        elif t == "quote":
            lines += [f"> {S['text']}", ">", f"> —— {S['source']}", ""]
        elif t == "blocks":
            lines += ["```text"] + [f"{lab:<8} " + " | ".join(s[0] for s in segs) for lab, segs in S["rows"]] + ["```", ""]
        lines += [S["narration"], ""]
        if S.get("caption"):
            lines += [f'!!! tip "要点"', f"    {S['caption']}", ""]
        if t == "summary" and S.get("exercise"):
            lines += ['!!! example "课后练习"', f"    {S['exercise']}", ""]
    lines += ["---", "", "*本讲视频由程序合成（画面、字幕与 DeepSeek TTS 配音），演示数据均为真实运行结果。"
              f"讲稿源文件：[videos/lectures/{L['id']}.py]({GH}/blob/main/videos/lectures/{L['id']}.py)*"]
    return "\n".join(lines) + "\n"


def leaderboard_md():
    rows = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((REPO / "leaderboard").glob("*.json"))]
    out = []
    for track, title, key in (("accuracy", "解决率赛道（难题集 20 题）", lambda r: (-r["resolved"], r["usd_per_task"])),
                              ("efficiency", "效率赛道（20 题；解决率不低于基线时按每题成本排名）", lambda r: (r["usd_per_task"], -r["resolved"]))):
        rs = sorted((r for r in rows if r["track"] == track), key=key)
        out += [f"## {title}", "", "| # | 名称 | 解决 | 每题成本 | 中位耗时 | 缓存命中 | 模型 | 备注 |", "|---|---|---|---|---|---|---|---|"]
        for i, r in enumerate(rs, 1):
            med = f"{r['median_seconds']:.0f}s" if r.get("median_seconds") else "—"
            hit = f"{r['cache_hit_rate']:.1%}" if r.get("cache_hit_rate") else "—"
            name = r["name"] + (" 🔖" if r.get("baseline") else "")
            out.append(f"| {i} | {name} | {r['resolved']}/{r['n']} | ${r['usd_per_task']:.4f} | {med} | {hit} | {', '.join(r.get('models', []))} | {r.get('note', '')} |")
        out.append("")
    out.append("🔖 = 课程团队提供的基线或示例。")
    return "\n".join(out)


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir()
    for name in ("home", "project", "leaderboard", "faq", "grading"):   # 站点原生页面（链接按站内路径写）
        src = (REPO / "docs" / f"{name}.md").read_text(encoding="utf-8")
        if name == "leaderboard":
            src = src.replace("{{LEADERBOARD}}", leaderboard_md())
        (OUT / ("index.md" if name == "home" else f"{name}.md")).write_text(src, encoding="utf-8")
    copy_md(REPO / "docs/syllabus.md")
    copy_md(REPO / "infra/README.md")
    for n in range(6):
        p = REPO / f"assignment{n}/README.md"
        if p.exists():
            copy_md(p)
    copy_md(REPO / "assignment2/QUESTIONS.md")
    vids = json.loads((REPO / "videos/bilibili.json").read_text(encoding="utf-8")) if (REPO / "videos/bilibili.json").exists() else {}
    lecs = sorted((REPO / "videos/lectures").glob("l[0-9][0-9].py"))
    (OUT / "lectures").mkdir()
    idx = ["# 讲座", "", "每讲 3–5 分钟，配有讲稿全文。周次安排见[课程大纲](../syllabus.md)。", "",
           "| 讲次 | 主题 | 视频 |", "|---|---|---|"]
    nav_lec = []
    for p in lecs:
        L = load_lecture(p)
        (OUT / "lectures" / f"{L['id']}.md").write_text(lecture_page(L, vids), encoding="utf-8")
        idx.append(f"| 第 {L['no']} 讲 | [{L['title']}]({L['id']}.md) | {'▶️' if L['id'] in vids else '制作中'} |")
        nav_lec.append((L["no"], L["title"], L["id"]))
    (OUT / "lectures/index.md").write_text("\n".join(idx) + "\n", encoding="utf-8")
    (OUT / "assets").mkdir()
    (OUT / "assets/extra.css").write_text(
        ".video{position:relative;padding-top:56.25%;margin:1em 0}"
        ".video iframe{position:absolute;inset:0;width:100%;height:100%;border-radius:8px}\n", encoding="utf-8")
    # 导航
    nav = ["nav:", "  - 首页: index.md", "  - 课程大纲: syllabus.md", "  - 讲座:", "      - lectures/index.md"]
    nav += [f"      - '{n:02d} {t}': lectures/{i}.md" for n, t, i in nav_lec]
    nav += ["  - 作业:"]
    for n in range(6):
        if (OUT / f"assignments/a{n}.md").exists():
            nav.append(f"      - 'A{n} {ASSIGN_NAMES[n]}': assignments/a{n}.md")
    nav += ["      - 'A2 源码阅读题': assignments/a2-questions.md", "  - 期末项目: project.md", "  - 评分说明: grading.md", "  - 排行榜: leaderboard.md", "  - 基础设施: infra.md", "  - 常见问题: faq.md"]
    base = (REPO / "mkdocs.base.yml").read_text(encoding="utf-8")
    (REPO / "mkdocs.yml").write_text("# 由 scripts/build_site.py 生成，请修改 mkdocs.base.yml\n" + base.rstrip() + "\n" + "\n".join(nav) + "\n", encoding="utf-8")
    print(f"site_src: {sum(1 for _ in OUT.rglob('*.md'))} pages")


if __name__ == "__main__":
    main()
