#!/usr/bin/env python3
"""下载 Qwen3-0.6B 的 config / tokenizer / safetensors（约 1.5GB）到仓库根目录 models/Qwen3-0.6B/。
国内可先 export HF_ENDPOINT=https://hf-mirror.com 。已下载且校验通过的文件会跳过。"""
import hashlib, os, sys, urllib.error, urllib.request
from pathlib import Path

REPO = "Qwen/Qwen3-0.6B"
DEST = Path(os.environ.get("MINI_MODEL_DIR", Path(__file__).resolve().parents[2] / "models" / "Qwen3-0.6B"))
FILES = {  # 课程团队所用文件的 sha256（上游更新后可能变化：不一致只警告）
    "config.json": "660db3b73d788119c04535e48cf9be5f55bc3100841a718637ae695b442f27dd",
    "tokenizer.json": "aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4",
    "model.safetensors": "f47f71177f32bcd101b7573ec9171e6a57f4f4d31148d38e382306f42996874b",
}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    base = os.environ.get("HF_ENDPOINT", "https://huggingface.co").rstrip("/")
    DEST.mkdir(parents=True, exist_ok=True)
    for name, want in FILES.items():
        p = DEST / name
        if p.exists() and sha256(p) == want:
            print(f"✓ {name} 已存在"); continue
        url = f"{base}/{REPO}/resolve/main/{name}"
        print(f"↓ {url}")
        tmp = p.with_suffix(p.suffix + ".part")
        # 自带 User-Agent：hf-mirror.com 会拒绝 urllib 默认的 Python-urllib/x.y（HTTP 403）
        req = urllib.request.Request(url, headers={"User-Agent": "agentharness-download/1.0"})
        try:
            r = urllib.request.urlopen(req, timeout=60)
        except (urllib.error.URLError, TimeoutError) as e:
            sys.exit(f"下载失败：{url}\n  {e}\n"
                     f"  国内网络请先执行 export HF_ENDPOINT=https://hf-mirror.com 再重试；\n"
                     f"  或者手动下载 {', '.join(FILES)} 这几个文件到 {DEST}/"
                     f"（例如 pip install huggingface_hub 后运行 hf download {REPO} {' '.join(FILES)} --local-dir {DEST}）。")
        with r, open(tmp, "wb") as f:
            total, done = int(r.headers.get("Content-Length", 0)), 0
            while chunk := r.read(1 << 20):
                f.write(chunk); done += len(chunk)
                if total:
                    print(f"\r  {done >> 20}/{total >> 20} MB", end="", file=sys.stderr)
        print(file=sys.stderr)
        tmp.rename(p)
        if sha256(p) != want:
            print(f"⚠️ {name} 的 sha256 和课程团队的不同（上游可能更新过），check.py 的 token 对比可能不一致")
    print(f"完成：{DEST}")


if __name__ == "__main__":
    main()
