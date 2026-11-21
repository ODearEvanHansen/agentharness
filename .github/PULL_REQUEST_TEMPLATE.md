<!-- 排行榜提交请按下面填写；其他类型的 PR 可以删掉本模板，简单说明改动即可。 -->

## 排行榜提交

- 昵称：
- 赛道：accuracy（难题集） / efficiency（原 20 题）
- 结果：解决 __/20，每题 $____，中位耗时 ____ s，缓存命中率 ____

## 检查清单

- [ ] `leaderboard/<昵称>-<赛道>.json` 由 `assignment3/score.py` 生成，没有手改
- [ ] 文件名形如 `<昵称>-accuracy.json` 或 `<昵称>-efficiency.json`
- [ ] 效率赛道：解决数 ≥ 17
- [ ] 附上了 `assignment3/submission/<昵称>/`（patch、插件、BLOG.md），`--config-dir` 指向的就是这个目录
- [ ] 没有修改 `leaderboard/baseline-*.json` 或其他人的提交
- [ ] 本地运行 `python scripts/validate_leaderboard.py leaderboard/*.json` 通过
- [ ] 提交内容里没有 API key

## 说明（可选）

<!-- 做了哪些优化、复现方式、需要说明的异常 -->
