# AGENTS.md：维护本仓库的 agent 先读这里（主线，防跨会话漂移）

最后更新：2026-11-23（依据 Principal 整改令 /agents-shared/elon-review/2026-11-23-elon-remediation-order.md）。改主线须经 Bergwolf（课程 owner）确认，并在此处更新日期。

## 主线（当前唯一主线：轻量入口）
1. 定位：以影响力为目标（外部开发者 star / 转发 / 讨论 / 真实使用反馈），本阶段不做变现、不卖课。
2. 差异化：可复现的"成本 × 效果"实测（例：A5 路由在小任务上云端成本反而 +38%），而不是重复已有的 DSH 源码教程。不做、也不以"开放排行榜 / 外部排行榜提交"作为产品目标或验证判据（A3 作业内的课内排行榜保持现状，不对外宣传）。
3. **唯一最高优先级**：15 分钟轻量入口（pip + DeepSeek API key，无 Docker，支持 macOS，内置 3 道小题，跑完算出个人解决率与花费）。Docker / SWE-bench 全套保留为进阶复现层。
4. **冻结**：37 讲讲稿不再扩写；不做全量 TTS 重配音与视频重渲，不开其他并行分支。轻量入口上线、拿到真实外部反馈后，再向 Bergwolf 另行请示视频与 TTS 预算。现有成片（原 29 讲编号）与 37 讲新讲稿不一致，不得直接发布。
5. 影响力判据：轻量入口发布后看真实外部使用与反馈（外部 issue / 讨论 / star / 转发），不以排行榜提交计。

## 硬规则
- 作业二的 loop 名为 **miniLoop**（目录 assignment2/miniloop）。不要使用源自其他课程的专有命名（旧名已清除）；提交前 `git grep -niI 'm[a]ds'` 必须为空。
- 课程结构参考 Harvard CS2680 并致谢，但与哈佛及其课程团队无关联、未获背书；声明见 README.md / docs/home.md / mkdocs 页脚，不要删。
- 学员可见费用一律用 DeepSeek 官方人民币价格。
- 付费调用（API / TTS）单次复现 >7 元先请示 owner；累计花费用 tools/usage_cost 类脚本按会话日志核算，TTS 以控制台账单为准。
- site/ 与 _site/ 是构建产物，不入库；网站由 GitHub Actions（pages.yml）构建发布。
