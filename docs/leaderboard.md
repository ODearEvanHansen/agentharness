<!-- 本文件由 scripts/build_site.py 用于生成网站，站内链接在 GitHub 仓库里直接浏览会失效，请访问 https://odearevanhansen.github.io/agentharness/ -->
# 排行榜

作业 3 的提交会展示在这里（作业 5 不设排行榜）。参加方法见[作业 3 · 运行与提交排行榜](assignments/a3.md#运行与提交排行榜)：用 `assignment3/score.py` 生成 `leaderboard/<昵称>-<赛道>.json`，然后向课程仓库发起 PR。
两条赛道：解决率赛道用难题集，解决数优先、其次比每题成本；效率赛道用原 20 题，在**解决数 ≥ 17/20** 的前提下比每题成本。
维护者会抽查复现：用你的配置重跑一遍，解决数允许相差 ±2。

所有成本都按 DeepSeek 官方**高峰价**计算。基线由课程团队实测得出。

{{LEADERBOARD}}
