# 作业 2 Part B：阅读 DSH 的 agent loop

**版本锁定**：本题只针对课程使用的 DSH 版本 `dsh-v0.2.2-rc.2`。请阅读这个 tag 下的代码，不要看 main 分支，因为不同版本的行为可能不一样。
- README：<https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.2-rc.2/packages/core/agent-loop/README.md>
- 源码：<https://github.com/deepseek-ai/deepseek-harness/tree/dsh-v0.2.2-rc.2/packages/core/agent-loop/src>（重点看 `agent.ts`，约 750 行）

每题回答 150–300 字，并**注明你依据的文件和行号**。不要求读懂全部 TypeScript，但每个结论都要有出处支撑。

## B1 取消与未完成的工具调用
用户在 agent 执行到一半时取消。此时：(a) 模型已经提出、但还没开始执行的工具调用；(b) 已经发出、但结果还没写入的工具调用，DSH 分别如何处理（错误码分别是什么）？为什么必须给每个 tool call 都补上一个 result，而不能直接丢掉？你的 miniLoop 遇到 Ctrl-C 会怎样？下一次请求还能正常发出吗？

## B2 并行工具调用
模型在一步里返回了 5 个工具调用。DSH 默认最多并行执行几个（哪个配置项控制）？什么叫 exclusive barrier？为什么"一个调用是否安全"只能看它自己（unary classification），而不能比较多个调用之间的关系？你的 miniLoop 是串行执行的，这样做会损失什么、又能避免什么？

## B3 系统提示与前缀缓存
DSH 的 "request series" 是什么？系统提示变化时，DSH 在什么情况下把新提示**追加**到历史末尾，什么情况下**改写**开头的 system 节点？这两种做法对 DeepSeek 前缀缓存的命中分别有什么影响？结合你在作业 1 里观察到的缓存命中率，说说如果你的 miniLoop 每一步都在系统提示里写入"当前时间"，会发生什么。

## B4 失败与重试
模型请求失败（比如 429 或 5xx）后，DSH 在哪里给插件留了决定"是否重试"的机会（hook 名）？哪些失败会直接结束这一轮？对比你的 `chat()` 的重试策略：对 agent 来说，"在请求层重试"和"在 loop 层重试"有什么区别？

## B5（开放题）
从 DSH 的 loop 里挑一个你认为**最值得借鉴到 miniLoop** 的设计，实现它，并用 Part C 的数据说明效果（效果为零或者是负的也可以，只要讲清楚原因）。
