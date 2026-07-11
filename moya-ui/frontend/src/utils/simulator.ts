import type { Node, Edge } from '@xyflow/react'
import type {
  AgentNodeData, ToolNodeData, SkillNodeData,
  InputNodeData, LoopNodeData, BranchNodeData, ParallelNodeData,
  TraceEvent,
} from '../types'

function delay(ms: number, signal?: AbortSignal) {
  return new Promise<void>((resolve, reject) => {
    const timer = setTimeout(resolve, ms)
    signal?.addEventListener('abort', () => {
      clearTimeout(timer)
      reject(new DOMException('Simulation stopped', 'AbortError'))
    }, { once: true })
  })
}

function jitter(base: number, spread = 400) {
  return base + Math.random() * spread
}

function topSort(nodes: Node[], succ: Map<string, string[]>, pred: Map<string, string[]>): Node[] {
  const deg = new Map(nodes.map(n => [n.id, pred.get(n.id)?.length ?? 0]))
  const queue = nodes.filter(n => (deg.get(n.id) ?? 0) === 0)
  const result: Node[] = []
  const nm = new Map(nodes.map(n => [n.id, n]))
  while (queue.length) {
    const n = queue.shift()!
    result.push(n)
    for (const sid of succ.get(n.id) ?? []) {
      const d = (deg.get(sid) ?? 1) - 1
      deg.set(sid, d)
      if (d === 0 && nm.has(sid)) queue.push(nm.get(sid)!)
    }
  }
  return result
}

function capabilityLines(data: AgentNodeData): string {
  const lines: string[] = []
  const toolCount = (data.toolIds?.length ?? 0) + (data.inlineTools?.length ?? 0)
  if (toolCount > 0) lines.push(`🔧 ${toolCount} tool${toolCount > 1 ? 's' : ''} available`)

  const mem = data.memory
  if (mem?.shortTerm?.enabled || mem?.longTerm?.enabled) {
    const parts: string[] = []
    if (mem.shortTerm?.enabled) parts.push(`short-term (last ${mem.shortTerm.windowSize ?? 10})`)
    if (mem.longTerm?.enabled)  parts.push(`long-term (${mem.longTerm.path || './moya_memory'})`)
    lines.push(`🧠 Memory ${parts.join(' + ')}: recalled earlier context from this thread, storing this exchange for later turns`)
  }

  const mcpCount = data.mcpServers?.length ?? 0
  if (mcpCount > 0) lines.push(`🔌 ${mcpCount} MCP server${mcpCount > 1 ? 's' : ''} connected`)

  return lines.length ? lines.join('\n') + '\n\n' : ''
}

function simulateAgentOutput(data: AgentNodeData, input: string): string {
  const name  = data.label || data.name || 'Agent'
  const model = `${data.provider}/${data.model}`
  const snip  = data.systemPrompt ? data.systemPrompt.slice(0, 60) + (data.systemPrompt.length > 60 ? '…' : '') : ''
  const preview = input.length > 80 ? input.slice(0, 80) + '…' : input

  return (
    `[${name}] — ${model}\n\n` +
    (snip ? `Role: "${snip}"\n\n` : '') +
    capabilityLines(data) +
    `Processing: "${preview}"\n\n` +
    `This is a simulated response demonstrating how MOYA routes messages through the ` +
    `pipeline. In live mode with a real API key, ${name} would produce actual LLM output here. ` +
    `The agent uses create_agent("${data.provider}", model="${data.model}") under the hood.`
  )
}

interface SimContext {
  output: string
  metadata: Record<string, string>
}

export async function runSimulation(
  nodes: Node[],
  edges: Edge[],
  onTrace: (event: TraceEvent) => void,
  signal?: AbortSignal,
): Promise<string> {

  const nodeMap = new Map(nodes.map(n => [n.id, n]))

  const flowEdges = edges.filter(e => {
    const src = nodeMap.get(e.source)
    return src && src.type !== 'tool' && src.type !== 'skill'
  })

  const succ = new Map<string, string[]>()
  const pred = new Map<string, string[]>()
  for (const e of flowEdges) {
    if (!succ.has(e.source)) succ.set(e.source, [])
    succ.get(e.source)!.push(e.target)
    if (!pred.has(e.target)) pred.set(e.target, [])
    pred.get(e.target)!.push(e.source)
  }

  const flowNodes = nodes.filter(n => n.type !== 'tool' && n.type !== 'skill')
  const sorted = topSort(flowNodes, succ, pred)

  const ctx: SimContext = { output: '', metadata: {} }
  const consumed = new Set<string>()

  for (const node of sorted) {
    if (signal?.aborted) throw new DOMException('Simulation stopped', 'AbortError')
    if (consumed.has(node.id)) continue

    const t0 = Date.now()
    const name = (node.data as { label?: string }).label || node.type || 'node'

    onTrace({ nodeId: node.id, nodeName: name, nodeType: node.type ?? '', status: 'started', input: ctx.output, output: '', durationMs: 0, timestamp: t0 })

    if (node.type === 'input') {
      ctx.output = (node.data as unknown as InputNodeData).message || ''
      onTrace({ nodeId: node.id, nodeName: name, nodeType: node.type ?? '', status: 'completed', input: '', output: ctx.output, durationMs: Date.now() - t0, timestamp: t0 })
      continue
    }

    if (node.type === 'output') {
      await delay(jitter(200, 100), signal)
      onTrace({ nodeId: node.id, nodeName: name, nodeType: node.type ?? '', status: 'completed', input: ctx.output, output: ctx.output, durationMs: Date.now() - t0, timestamp: t0 })
      continue
    }

    if (node.type === 'agent') {
      await delay(jitter(600, 600), signal)
      const prev = ctx.output
      ctx.output = simulateAgentOutput(node.data as unknown as AgentNodeData, ctx.output)
      onTrace({ nodeId: node.id, nodeName: name, nodeType: node.type ?? '', status: 'completed', input: prev, output: ctx.output, durationMs: Date.now() - t0, timestamp: t0 })
      continue
    }

    if (node.type === 'skill') {
      const d = node.data as unknown as SkillNodeData
      await delay(jitter(100, 100), signal)
      ctx.output = `[Skill applied: ${d.name}]\n${ctx.output}`
      onTrace({ nodeId: node.id, nodeName: name, nodeType: node.type ?? '', status: 'completed', input: ctx.output, output: ctx.output, durationMs: Date.now() - t0, timestamp: t0 })
      continue
    }

    if (node.type === 'tool') {
      const d = node.data as unknown as ToolNodeData
      await delay(jitter(150, 150), signal)
      const result = d.mockReturnValue || 'Tool result'
      ctx.output = `[Tool: ${d.name}] → ${result}\n\n${ctx.output}`
      onTrace({ nodeId: node.id, nodeName: name, nodeType: node.type ?? '', status: 'completed', input: ctx.output, output: ctx.output, durationMs: Date.now() - t0, timestamp: t0 })
      continue
    }

    if (node.type === 'parallel') {
      const d = node.data as unknown as ParallelNodeData
      const branchTargets = (succ.get(node.id) ?? []).map(sid => nodeMap.get(sid)).filter(Boolean) as Node[]
      const agentTargets = branchTargets.filter(b => b.type === 'agent')
      for (const b of branchTargets) consumed.add(b.id)

      const branchOutputs = await Promise.all(
        agentTargets.map(async (b) => {
          const bt0 = Date.now()
          const bName = (b.data as { label?: string }).label || 'Branch'
          onTrace({ nodeId: b.id, nodeName: bName, nodeType: b.type ?? '', status: 'started', input: ctx.output, output: '', durationMs: 0, timestamp: bt0 })
          await delay(jitter(600, 600), signal)
          const out = simulateAgentOutput(b.data as unknown as AgentNodeData, ctx.output)
          onTrace({ nodeId: b.id, nodeName: bName, nodeType: b.type ?? '', status: 'completed', input: ctx.output, output: out, durationMs: Date.now() - bt0, timestamp: bt0 })
          return out
        })
      )

      ctx.output = d.mergeStrategy === 'first'
        ? branchOutputs[0] ?? ''
        : branchOutputs.join('\n\n---\n\n')

      onTrace({ nodeId: node.id, nodeName: name, nodeType: node.type ?? '', status: 'completed', input: '', output: ctx.output, durationMs: Date.now() - t0, timestamp: t0 })
      continue
    }

    if (node.type === 'loop') {
      const d = node.data as unknown as LoopNodeData
      const loopTargets = (succ.get(node.id) ?? []).map(sid => nodeMap.get(sid)).filter(Boolean) as Node[]
      const loopAgent = loopTargets.find(n => n.type === 'agent')
      if (loopAgent) {
        consumed.add(loopAgent.id)
        const kw = d.stopKeyword || 'DONE'
        const maxIter = d.maxIterations || 3
        for (let i = 0; i < maxIter; i++) {
          if (signal?.aborted) throw new DOMException('Simulation stopped', 'AbortError')
          const lt0 = Date.now()
          const lName = (loopAgent.data as { label?: string }).label || 'Loop Agent'
          onTrace({ nodeId: loopAgent.id, nodeName: `${lName} (iter ${i + 1})`, nodeType: loopAgent.type ?? '', status: 'started', input: ctx.output, output: '', durationMs: 0, timestamp: lt0 })
          await delay(jitter(500, 400), signal)
          const prev = ctx.output
          let out = simulateAgentOutput(loopAgent.data as unknown as AgentNodeData, ctx.output)
          if (i === maxIter - 1) out += `\n\n${kw}`
          ctx.output = out
          onTrace({ nodeId: loopAgent.id, nodeName: `${lName} (iter ${i + 1})`, nodeType: loopAgent.type ?? '', status: 'completed', input: prev, output: ctx.output, durationMs: Date.now() - lt0, timestamp: lt0 })
          if (ctx.output.includes(kw)) break
        }
      }
      onTrace({ nodeId: node.id, nodeName: name, nodeType: node.type ?? '', status: 'completed', input: '', output: ctx.output, durationMs: Date.now() - t0, timestamp: t0 })
      continue
    }

    if (node.type === 'branch') {
      const d = node.data as unknown as BranchNodeData
      const kw = (d.conditionKeyword || 'yes').toLowerCase()
      const condition = ctx.output.toLowerCase().includes(kw)
      const handleId = condition ? 'true' : 'false'
      const branchEdge = flowEdges.find(e => e.source === node.id && e.sourceHandle === handleId)
      const branchTarget = branchEdge ? nodeMap.get(branchEdge.target) : null

      const otherHandle = condition ? 'false' : 'true'
      const otherEdge = flowEdges.find(e => e.source === node.id && e.sourceHandle === otherHandle)
      if (otherEdge) consumed.add(otherEdge.target)

      await delay(200, signal)
      const branchLabel = condition ? 'true' : 'false'
      const detail = `Condition: "${kw}" ${condition ? 'found' : 'not found'} → taking "${branchLabel}" branch`
      onTrace({ nodeId: node.id, nodeName: name, nodeType: node.type ?? '', status: 'completed', input: ctx.output, output: detail, durationMs: Date.now() - t0, timestamp: t0 })

      if (branchTarget && branchTarget.type === 'agent') {
        consumed.add(branchTarget.id)
        const bt0 = Date.now()
        const bName = (branchTarget.data as { label?: string }).label || 'Branch Agent'
        onTrace({ nodeId: branchTarget.id, nodeName: bName, nodeType: branchTarget.type ?? '', status: 'started', input: ctx.output, output: '', durationMs: 0, timestamp: bt0 })
        await delay(jitter(500, 400), signal)
        const prev = ctx.output
        ctx.output = simulateAgentOutput(branchTarget.data as unknown as AgentNodeData, ctx.output)
        onTrace({ nodeId: branchTarget.id, nodeName: bName, nodeType: branchTarget.type ?? '', status: 'completed', input: prev, output: ctx.output, durationMs: Date.now() - bt0, timestamp: bt0 })
      }
      continue
    }
  }

  return ctx.output
}
