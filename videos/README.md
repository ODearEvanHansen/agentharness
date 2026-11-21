# 合成视频

无声样片：画面和字幕全部由程序生成，数据来自真实运行。

- `l12/`：第 12 讲 前缀缓存与 request series（107 秒）。`cache_demo.py` 调用真实 API 生成 `demo_out.txt`，`l12.py` 逐帧绘制并用 ffmpeg 编码。

依赖：Pillow、ffmpeg、Noto Sans SC 字体（放在 ~/.fonts 下，或用环境变量 FONTDIR 指定目录）。

配音：`voice_l12.py` 把讲稿逐段交给 DeepSeek TTS（音色 stella）合成，画面时间轴按配音时长拉伸，同时生成 srt 字幕（内嵌字幕轨，也可单独上传到 B 站）。需要 `DEEPSEEK_API_KEY`；生成一讲约 3 分钟的配音约花 $0.01。

## 标识与许可
- **AI 生成内容标识**：画面右上角始终显示"AI 合成（含 AI 配音）"，片头有文字说明，mp4 元数据里也写入了 AIGC 说明。上传 B 站时，需要在投稿页勾选"作者声明：使用 AI 生成"，并在简介里注明"画面由程序生成，配音由 DeepSeek TTS 合成"。
- **许可**：讲稿（`lectures/*.py` 中的文字）和生成的视频采用 CC BY-SA 4.0，引擎代码采用 MIT。配音使用 DeepSeek TTS 生成，使用时请遵守 DeepSeek 开放平台的服务条款，视频公开发布前要再确认一遍条款。
- **字体**：Noto Sans SC 和 DejaVu Sans Mono，均为 SIL OFL 1.1 / 自由许可。字体只在渲染时使用，仓库不再分发字体文件。

## 配音写法约定（DeepSeek TTS，Stella 音色实测）
2026-11 用 35 条讲稿原句做过读音抽查（合成后再用 Whisper 转写比对），据此约定：
- 数字一律写汉字（"零点零一八美元""百分之九十五点八"），读得准；`Q 四`、`三十 B A 三 B`、`WSL 二`、`rc 二` 都正常。
- `JSON RPC` 写成 `JSON-RPC`（不加连字符时会连读走音）。
- `zstd` 写成 `Z standard`；`mads loop` 写成 `M A D S loop`。
- 口播里不提"合成/AI 配音"：AIGC 标识由画面角标、片头小字、mp4 元数据和 B 站声明承担。
- 太短的独立句（如"不需要 GPU。"）容易读含糊，并到上下文里或补几个字。
- `llama dot cpp`、`杠 n p`、`K V cache`、`GGUF`、`GPTQ`、`AWQ`、`heredoc`、`PagedAttention` 实测可接受。
