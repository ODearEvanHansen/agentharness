/**
 * 作业 3 插件模板：工具输出裁剪（tools/post-execute waterfall）。
 *
 * 当工具返回的文本超过 maxChars 时，只保留开头和结尾，中间替换成一行省略说明。
 * 这能减少后续每一步都要重复发送的上下文 token，但模型可能因此看不到关键信息。
 * 这正是作业 3 要你用数据权衡的地方。
 *
 * 加载：在 profile patch 里插入（路径必须是绝对路径）
 *   - insert:
 *       - id: trim-tool-output
 *         name: '/abs/path/to/trim-tool-output.ts'
 *         config: { maxChars: 2000, headRatio: 0.3 }
 */
import type { Context } from '@deepseek-ai/cordis'

export const name = 'trim-tool-output'

export interface Config {
  maxChars?: number
  headRatio?: number
}

export function apply(ctx: Context, config: Config = {}) {
  const maxChars = config.maxChars ?? 2000
  const headRatio = config.headRatio ?? 0.3

  ctx.on('tools/post-execute' as any, async (exec: any, result: any, next: () => Promise<any>) => {
    if (result?.isError || !Array.isArray(result?.content)) return next()
    let changed = false
    const content = result.content.map((block: any) => {
      if (block?.type !== 'text' || typeof block.text !== 'string' || block.text.length <= maxChars) return block
      changed = true
      const head = Math.floor(maxChars * headRatio)
      const tail = maxChars - head
      const omitted = block.text.length - head - tail
      return {
        ...block,
        text: `${block.text.slice(0, head)}\n…[已省略 ${omitted} 个字符；如需查看，请用更精确的命令（grep/sed -n）]…\n${block.text.slice(-tail)}`,
      }
    })
    // TODO(A3): 你可以按工具名（exec.name）设置不同的阈值，或者把被省略的部分存到文件里，告诉模型路径
    return changed ? { kind: 'accept', content } : next()
  })
}
