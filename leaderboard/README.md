# 排行榜提交

每个提交一个 JSON 文件（由 `assignment3/score.py` 生成），文件名用 `<昵称>-<赛道>.json`。网站构建时会自动汇总，见 [docs/leaderboard.md](../docs/leaderboard.md)。PR 还必须包含 `assignment3/submission/<昵称>/`（含 score.py 复制的 `artifacts/run.jsonl`、`predictions.jsonl`、`report.json`），CI 会重算 sha256 核对；PR 只能改 `leaderboard/` 和 `assignment3/submission/`。
