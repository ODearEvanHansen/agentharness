# 合成视频

无声样片：画面和字幕全部由程序生成，数据来自真实运行。

- `l12/`：第 12 讲 前缀缓存与 request series（107 秒）。`cache_demo.py` 调用真实 API 生成 `demo_out.txt`，`l12.py` 逐帧绘制并用 ffmpeg 编码。

依赖：Pillow、ffmpeg、Noto Sans SC 字体（放在 ~/.fonts 下，或用环境变量 FONTDIR 指定目录）。

配音：`voice_l12.py` 把讲稿逐段交给 DeepSeek TTS（音色 stella）合成，画面时间轴按配音时长拉伸，同时生成 srt 字幕（内嵌字幕轨，也可单独上传到 B 站）。需要 `DEEPSEEK_API_KEY`；生成一讲约 3 分钟的配音约花 $0.01。
