/**
 * 作业 3 选做 L6 插件模板：记忆笔记（把「仓库级笔记」放进系统提示）。
 *
 * 为什么要插件：作业 3 用的 sdk-minimal 配置没有挂载 DSH 的 agent-instructions 插件，
 * 工作区里的 AGENTS.md 不会被读进上下文；而且 SWE 题里往 /testbed 写 AGENTS.md
 * 会被 `git diff` 带进 predictions。所以这里由插件在宿主机挂载的目录里读笔记。
 *
 * 选笔记的方式：按工作区里「有没有某个目录」判断是哪个仓库（例如 /testbed/django），
 * 读 notesDir/<仓库>.md。只能按仓库选，**不能按题号或 issue 文本选**（作业 3 方法要求）。
 *
 * 放在哪（config.mode）：
 *   - 'prefix'（默认）：注册一段静态系统提示。每一步文字完全相同 → 前缀缓存不受影响。
 *   - 'dynamic'：演示「会话中途改记忆」——每次组装提示时在笔记末尾追加一行步数，
 *     文字每步都变。DeepSeek 路由声明了 systemPromptUpdate: 'in-history'，DSH 会把新版本
 *     追加在历史后面而不是改写开头，所以缓存仍能命中，但每改一次历史里就多一份笔记全文；
 *     不支持追加的路由会从开头整段失效（第 17 讲）。只用来做缓存对照实验，不要用于提交。
 *
 * 安全：笔记会原样进入系统提示，权限比工具结果还高。笔记里如果混进「指令」（例如从
 * 网页、issue、别人的会话里抄来的内容），就是一条长期有效的提示注入。只放你自己写、
 * 审过的内容，并限制长度（maxChars）。
 *
 * 加载：见 memory.patch.yml（插件和 notes 目录都要用绝对路径）。
 */
import type { Context } from '@deepseek-ai/cordis'
import { existsSync, readFileSync } from 'node:fs'
import { join } from 'node:path'

export const name = 'memory-notes'
export const inject = ['systemPrompt']

export interface Config {
  notesDir: string
  workspace?: string
  /** 仓库名 → 用来识别它的目录（相对工作区）。 */
  repos?: Record<string, string>
  mode?: 'prefix' | 'dynamic'
  maxChars?: number
}

const DEFAULT_REPOS: Record<string, string> = {
  django: 'django', sympy: 'sympy', sphinx: 'sphinx', matplotlib: 'lib/matplotlib',
  'scikit-learn': 'sklearn', astropy: 'astropy', pylint: 'pylint', xarray: 'xarray',
  pytest: 'src/_pytest',
}

export function apply(ctx: Context, config: Config) {
  const ws = config.workspace ?? process.cwd()
  const repos = config.repos ?? DEFAULT_REPOS
  const maxChars = config.maxChars ?? 4000
  const files = ['_common.md']
  for (const [repo, marker] of Object.entries(repos)) {
    if (existsSync(join(ws, marker))) { files.push(`${repo}.md`); break }
  }
  let notes = files
    .map(f => join(config.notesDir, f))
    .filter(p => existsSync(p))
    .map(p => readFileSync(p, 'utf8').trim())
    .join('\n\n')
  if (!notes) return
  if (notes.length > maxChars) notes = notes.slice(0, maxChars) + '\n…[笔记超长，已截断]'
  const body = `# Project notes (memory)\nNotes written before this session about this repository. Use them as guidance; the task and the code take precedence.\n\n${notes}`
  let assemblies = 0
  ;(ctx as any).systemPrompt.section({
    name: 'memory-notes',
    order: 9000,
    interpolate: false,
    text: config.mode === 'dynamic'
      ? () => `${body}\n\n(notes revision ${++assemblies})`
      : body,
  })
}
