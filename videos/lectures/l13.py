LECTURE = {'id': 'l13',
 'no': 13,
 'title': '插件开发',
 'subtitle': 'tools/post-execute、agent/pre-step、agent/request-error；.ts 免编译加载',
 'scenes': [{'type': 'title', 'narration': '第十三讲，插件开发。作业三本周发布，它规定不改 DSH 的源码，所有优化都要通过配置补丁和插件完成。这一讲，我们学会写第一个插件。'},
            {'type': 'code',
             'title': '最小的插件',
             'sub': 'docs/user/develop/basic/index.zh.md',
             'lang': 'ts',
             'code': "import type { Context } from '@deepseek-ai/cordis'\n"
                     '\n'
                     "export const name = 'hello-plugin'\n"
                     '\n'
                     'export function apply(ctx: Context) {\n'
                     '  // Required dependencies are ready before apply runs.\n'
                     "  console.log('[hello-plugin] plugin loaded!')\n"
                     '}',
             'caption': '导出 name 和 apply，就是一个插件',
             'narration': '先看最小的插件，来自 DSH 的开发文档。一个 TypeScript 文件，导出一个名字和一个 apply 函数。apply 拿到上下文对象 ctx，在里面注册你想要的能力。就这么简单。'},
            {'type': 'code',
             'title': '加载：在 patch 里插入，路径必须是绝对路径',
             'sub': 'assignment3/README.md',
             'lang': 'yaml',
             'code': '- id: session-log-deepseek\n'
                     '  config: { enabled: false }\n'
                     '- insert:\n'
                     '    - id: trim-tool-output\n'
                     "      name: '/abs/path/to/assignment3/templates/trim-tool-output.ts'\n"
                     '      config: { maxChars: 2000 }',
             'caption': 'DSH 运行时直接加载 .ts：不需要编译，也不需要 Node',
             'narration': '怎么加载？在 patch 文件里用 insert 插入一项，name 写插件文件的绝对路径，config 传参数。DSH 的运行时可以直接加载点 ts 文件，不需要编译，也不需要装 '
                          'Node。注意别忘了第一项，关闭会话日志上传。'},
            {'type': 'bullets',
             'title': '常用的挂载点',
             'sub': '作业三 README 列出的钩子',
             'items': ['tools/post-execute：工具结果进入上下文之前，替换或裁剪它',
                       'tools/pre-execute：工具调用分发前，拒绝或放行',
                       'agent/pre-step：每一步之前修改或拒绝消息，可声明 startsRequestSeries',
                       'agent/request-error：模型请求失败后，决定是否重试',
                       '⚠️ agent/request 已弃用，不要基于它开发'],
             'caption': '这些都是 waterfall：可以修改，也可以交给下一个',
             'narration': '常用的挂载点有这几个。工具执行之后，可以替换或裁剪结果；工具执行之前，可以拒绝或放行；每一步开始之前，可以修改消息，还能声明开启新的 request series；请求失败时，可以决定是否重试。注意，名叫 agent 斜杠 '
                          'request 的那个钩子已经弃用了，不要基于它开发。'},
            {'type': 'code',
             'title': 'waterfall 的写法：要么返回结果，要么调用 next',
             'sub': 'assignment3/templates/trim-tool-output.ts（节选）',
             'lang': 'ts',
             'code': "ctx.on('tools/post-execute' as any, async (exec: any, result: any, next: () => Promise<any>) => {\n"
                     '  if (result?.isError || !Array.isArray(result?.content)) return next()\n'
                     '  let changed = false\n'
                     '  const content = result.content.map((block: any) => { ... })\n'
                     "  return changed ? { kind: 'accept', content } : next()\n"
                     '})',
             'caption': '不处理就 next()，处理了就返回自己的决定',
             'narration': 'waterfall 钩子的写法有个固定模式。如果这个插件不打算处理，就调用 next，交给后面的监听者；如果要处理，就返回自己的决定。比如这里，输出没有超长就直接 next，超长了就返回 accept 和裁剪后的内容。'},
            {'type': 'quote',
             'title': '请求失败时：插件决定重试',
             'text': "a handling listener returns `{ kind: 'retry' }` without calling `next()`, while an unhandled failure is terminal.",
             'source': 'packages/core/agent-loop/README.md @ dsh-v0.2.2-rc.2',
             'caption': '插件失败会结束这一轮，但不会结束整个 loop',
             'narration': '再看请求失败的钩子。源码文档写道：处理失败的监听者返回 retry，并且不调用 next；没人处理的失败就是终止性的。还有一点要记住：插件自己抛出异常，会结束当前这一轮，但不会让整个 loop 崩掉。'},
            {'type': 'bullets',
             'title': '写插件的规矩',
             'sub': '作业三的方法要求',
             'items': ['每个插件都要有独立的对照实验：只开它，和不开它比', '不能读取题号或 issue 文本走特殊分支', 'patch 和插件放在同一个目录，SWE 模式下只读挂进任务容器', '改动会不会打断前缀缓存？上线前先看命中率'],
             'caption': '插件是实验变量，不是作弊通道',
             'narration': '最后是写插件的规矩。每个插件都要有独立的对照实验。插件不能读取题号或者题目文本来走特殊分支。patch 和插件要放在同一个目录，评测时它会只读挂进任务容器。另外，上线前先看看缓存命中率，确认你的改动没有打断前缀。'},
            {'type': 'summary',
             'items': ['插件 = 导出 name 和 apply 的 .ts 文件', 'patch 里 insert，绝对路径，免编译', 'waterfall：返回决定，或调用 next()', 'agent/request 已弃用'],
             'exercise': '15 分钟：把 hello-plugin 改成挂在 tools/post-execute 上、打印工具名和输出长度后调用 next()；跑一个小任务，预期每次工具调用打印一行，结果不变',
             'narration': '小结一下。插件就是一个导出名字和 apply 的 ts 文件，在 patch 里用绝对路径插入，不用编译；waterfall 钩子要么返回决定，要么调用 '
                          'next。课后小练习：把最小插件改成挂在工具执行之后，打印工具名和输出长度，再交给 next。跑一个小任务，预期每次工具调用都打印一行，而 agent 的结果不变。下一讲，我们讲成本与可靠性。'}]}
