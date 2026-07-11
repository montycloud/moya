import type { Node, Edge } from '@xyflow/react'
import type {
  AgentNodeData, ToolNodeData, SkillNodeData,
  InputNodeData, ParallelNodeData, LoopNodeData, BranchNodeData,
  ToolParameter, RegistryTool, InlineTool, AgentMCP,
} from '../types'

function toSnakeCase(s: string): string {
  return (s || 'agent')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    || 'agent'
}

// Python double-quoted string literal (JSON escaping is a valid subset of Python's).
function pyStr(s: string): string {
  return JSON.stringify(s ?? '')
}

// Inline escaping for content placed inside an existing "..." literal.
function py(s: string): string {
  return (s || '').replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n')
}

function paramSig(params: ToolParameter[]): string {
  return (params ?? []).map(p => `${p.name}: ${p.type || 'str'}`).join(', ')
}

function parseHeaders(raw: string): [string, string][] {
  return (raw || '').split('\n').map(l => l.trim()).filter(Boolean).map(l => {
    const i = l.indexOf(':')
    if (i < 0) return null
    return [l.slice(0, i).trim(), l.slice(i + 1).trim()] as [string, string]
  }).filter(Boolean) as [string, string][]
}

// Common executable-tool shape (RegistryTool, InlineTool, and ToolNodeData all satisfy this).
interface ToolSpec {
  name: string
  description: string
  parameters: ToolParameter[]
  kind: 'python' | 'api'
  code: string
  method: string
  url: string
  headers: string
  body: string
  mockReturnValue: string
}

function topologicalSort(nodes: Node[], successors: Map<string, string[]>, predecessors: Map<string, string[]>): Node[] {
  const inDegree = new Map<string, number>()
  for (const n of nodes) inDegree.set(n.id, predecessors.get(n.id)?.length ?? 0)

  const queue = nodes.filter(n => (inDegree.get(n.id) ?? 0) === 0)
  const sorted: Node[] = []
  const nodeMap = new Map(nodes.map(n => [n.id, n]))

  while (queue.length > 0) {
    const node = queue.shift()!
    sorted.push(node)
    for (const sid of successors.get(node.id) ?? []) {
      const deg = (inDegree.get(sid) ?? 1) - 1
      inDegree.set(sid, deg)
      if (deg === 0 && nodeMap.has(sid)) queue.push(nodeMap.get(sid)!)
    }
  }
  return sorted
}

export function generateCode(nodes: Node[], edges: Edge[], registryTools: RegistryTool[] = []): string {
  if (nodes.length === 0) {
    return '# Drag nodes onto the canvas to start building your flow.\n# Generated Python code will appear here.'
  }

  const nodeMap = new Map(nodes.map(n => [n.id, n]))
  const toolLib = new Map(registryTools.map(t => [t.id, t]))

  // Classify edges: capability (tool/skill → agent) vs flow.
  const flowEdges = edges.filter(e => {
    const src = nodeMap.get(e.source)
    return src && src.type !== 'tool' && src.type !== 'skill'
  })
  const capEdges = edges.filter(e => {
    const src = nodeMap.get(e.source)
    return src && (src.type === 'tool' || src.type === 'skill')
  })

  const successors = new Map<string, string[]>()
  const predecessors = new Map<string, string[]>()
  for (const e of flowEdges) {
    if (!successors.has(e.source)) successors.set(e.source, [])
    successors.get(e.source)!.push(e.target)
    if (!predecessors.has(e.target)) predecessors.set(e.target, [])
    predecessors.get(e.target)!.push(e.source)
  }

  const flowNodes = nodes.filter(n => n.type !== 'tool' && n.type !== 'skill')
  const sorted = topologicalSort(flowNodes, successors, predecessors)

  // Map agent → attached edge tool/skill node IDs.
  const agentEdgeTools = new Map<string, string[]>()
  const agentSkills    = new Map<string, string[]>()
  for (const e of capEdges) {
    const src = nodeMap.get(e.source)
    if (!src) continue
    if (src.type === 'tool')  (agentEdgeTools.get(e.target) ?? agentEdgeTools.set(e.target, []).get(e.target)!).push(e.source)
    else if (src.type === 'skill') (agentSkills.get(e.target) ?? agentSkills.set(e.target, []).get(e.target)!).push(e.source)
  }

  const agentNodes = nodes.filter(n => n.type === 'agent')

  // ── Per-agent capability inspection ────────────────────────────────────────
  interface AgentCaps {
    edgeToolIds: string[]
    registryToolIds: string[]
    inlineTools: InlineTool[]
    inspectorMcps: AgentMCP[]
    shortTerm?: { enabled: boolean; windowSize: number }
    longTerm?:  { enabled: boolean; path: string }
    isA2A: boolean
  }
  const caps = new Map<string, AgentCaps>()
  for (const an of agentNodes) {
    const d = an.data as unknown as AgentNodeData
    caps.set(an.id, {
      edgeToolIds:     agentEdgeTools.get(an.id) ?? [],
      registryToolIds: (d.toolIds ?? []).filter(id => toolLib.has(id)),
      inlineTools:     d.inlineTools ?? [],
      inspectorMcps:   d.mcpServers ?? [],
      shortTerm:       d.memory?.shortTerm,
      longTerm:        d.memory?.longTerm,
      isA2A:           d.provider === 'a2a',
    })
  }
  const hasTools  = (c: AgentCaps) => !c.isA2A && (c.edgeToolIds.length + c.registryToolIds.length + c.inlineTools.length > 0)
  const hasMcp    = (c: AgentCaps) => !c.isA2A && c.inspectorMcps.length > 0
  const hasMemory = (c: AgentCaps) => !c.isA2A && !!(c.shortTerm?.enabled || c.longTerm?.enabled)
  const needsReg  = (c: AgentCaps) => hasTools(c) || hasMcp(c)

  const allCaps = [...caps.values()]
  const anyTools  = allCaps.some(hasTools)
  const anyMcp    = allCaps.some(hasMcp)
  const anyMemory = allCaps.some(hasMemory)
  const anyA2A    = allCaps.some(c => c.isA2A)

  // ── Import assembly ─────────────────────────────────────────────────────────
  const hasParallel = nodes.some(n => n.type === 'parallel')
  const hasLoop     = nodes.some(n => n.type === 'loop')
  const hasBranch   = nodes.some(n => n.type === 'branch')
  const hasSkills   = nodes.some(n => n.type === 'skill')

  const stepImports = ['Pipeline', 'AgentStep']
  if (hasParallel) stepImports.push('ParallelStep')
  if (hasLoop)     stepImports.push('LoopStep')
  if (hasBranch)   stepImports.push('BranchStep')
  if (anyTools || anyMcp) stepImports.push('ToolRegistry', 'Tool')
  if (hasSkills)   stepImports.push('Skill')

  const lines: string[] = []
  lines.push(`from moya import create_agent, ${stepImports.join(', ')}`)
  if (anyMcp) {
    const usesAuth = allCaps.some(c => c.inspectorMcps.some(m => m.transport === 'http' && m.apiKey))
    lines.push(usesAuth ? 'from moya.mcp import MCPClient, MCPAuthConfig' : 'from moya.mcp import MCPClient')
  }
  if (anyA2A) lines.push('from moya.a2a.client import A2AAgent, A2AAgentConfig')
  if (anyMemory) {
    const memImports: string[] = []
    if (allCaps.some(c => c.shortTerm?.enabled)) memImports.push('ShortTermMemory')
    if (allCaps.some(c => c.longTerm?.enabled))  memImports.push('LongTermMemory')
    if (allCaps.some(c => c.shortTerm?.enabled && c.longTerm?.enabled)) memImports.push('CompositeMemory')
    lines.push(`from moya.memory import ${memImports.join(', ')}`)
  }
  lines.push('')

  // ── Shared tool function definitions (edge-tool nodes + used registry tools) ─
  const edgeToolNodes = nodes.filter(n => n.type === 'tool')
  const usedRegistryIds = new Set<string>()
  for (const c of allCaps) c.registryToolIds.forEach(id => usedRegistryIds.add(id))

  if (edgeToolNodes.length > 0 || usedRegistryIds.size > 0) {
    lines.push('# ── Tool functions ───────────────────────────────────────────────────────')
  }
  for (const tn of edgeToolNodes) {
    emitToolFn(lines, `tool_${toSnakeCase((tn.data as unknown as ToolNodeData).name)}`, tn.data as unknown as ToolSpec)
  }
  for (const id of usedRegistryIds) {
    emitToolFn(lines, `reg_${toSnakeCase(toolLib.get(id)!.name)}`, toolLib.get(id)! as unknown as ToolSpec)
  }

  // ── Skills ──────────────────────────────────────────────────────────────────
  const skillNodes = nodes.filter(n => n.type === 'skill')
  if (skillNodes.length > 0) {
    lines.push('# ── Skills ───────────────────────────────────────────────────────────────')
    for (const sn of skillNodes) {
      const d = sn.data as unknown as SkillNodeData
      lines.push(`${toSnakeCase(d.name)}_skill = Skill(`)
      lines.push(`    name="${py(d.name)}",`)
      lines.push(`    description="${py(d.description || d.name)}",`)
      if (d.promptSnippet) lines.push(`    prompt_snippet="${py(d.promptSnippet)}",`)
      lines.push(`)`)
    }
    lines.push('')
  }

  // ── Agents ────────────────────────────────────────────────────────────────
  if (agentNodes.length > 0) {
    lines.push('# ── Agents ───────────────────────────────────────────────────────────────')
    for (const an of agentNodes) {
      const d = an.data as unknown as AgentNodeData
      const varName = toSnakeCase(d.name || d.label)
      const c = caps.get(an.id)!

      // A2A / remote agent — a thin proxy, no local model/tools/memory.
      if (c.isA2A) {
        lines.push(`${varName} = A2AAgent(A2AAgentConfig(`)
        lines.push(`    agent_name="${py(d.name || d.label)}",`)
        lines.push(`    agent_type="a2a",`)
        lines.push(`    description="${py(d.description || 'Remote A2A agent')}",`)
        lines.push(`    endpoint_url="${py(d.endpointUrl || 'http://localhost:8001')}",`)
        if ((d.timeoutSeconds ?? 60) !== 60) lines.push(`    timeout_seconds=${d.timeoutSeconds},`)
        lines.push(`))`)
        lines.push('')
        continue
      }

      // Per-agent tool registry
      if (needsReg(c)) {
        lines.push(`${varName}_registry = ToolRegistry()`)
        for (const tid of c.edgeToolIds) {
          const td = nodeMap.get(tid)?.data as unknown as ToolNodeData | undefined
          if (!td) continue
          lines.push(`${varName}_registry.register_tool(Tool(name="${py(td.name)}", description="${py(td.description || td.name)}", function=tool_${toSnakeCase(td.name)}))`)
        }
        for (const rid of c.registryToolIds) {
          const t = toolLib.get(rid)!
          lines.push(`${varName}_registry.register_tool(Tool(name="${py(t.name)}", description="${py(t.description || t.name)}", function=reg_${toSnakeCase(t.name)}))`)
        }
        c.inlineTools.forEach((t, i) => {
          const fn = `${varName}_${toSnakeCase(t.name) || `tool_${i}`}`
          emitToolFn(lines, fn, t as unknown as ToolSpec)
          lines.push(`${varName}_registry.register_tool(Tool(name="${py(t.name)}", description="${py(t.description || t.name)}", function=${fn}))`)
        })
        c.inspectorMcps.forEach((m, i) => {
          const clientVar = `${varName}_mcp_${i}`
          lines.push(`${clientVar} = ${mcpExpr(m)}`)
          lines.push(`for _tool in ${clientVar}.get_tools():`)
          lines.push(`    ${varName}_registry.register_tool(_tool)`)
        })
      }

      // Per-agent memory
      if (hasMemory(c)) emitMemory(lines, varName, c)

      lines.push(`${varName} = create_agent(`)
      lines.push(`    "${d.provider}",`)
      lines.push(`    name="${py(d.name || d.label)}",`)
      lines.push(`    description="${py(d.description || `${d.label} agent`)}",`)
      lines.push(`    model="${py(d.model)}",`)
      if (d.systemPrompt) lines.push(`    system_prompt="${py(d.systemPrompt)}",`)
      if ((d.tags ?? []).length > 0) lines.push(`    tags=${JSON.stringify(d.tags)},`)
      const skillVars = (agentSkills.get(an.id) ?? [])
        .map(sid => nodeMap.get(sid))
        .filter(Boolean)
        .map(sn => `${toSnakeCase((sn!.data as unknown as SkillNodeData).name)}_skill`)
      if (needsReg(c))  lines.push(`    tool_registry=${varName}_registry,`)
      if (hasMemory(c)) lines.push(`    memory=${varName}_memory,`)
      if (skillVars.length > 0) lines.push(`    skills=[${skillVars.join(', ')}],`)
      lines.push(`)`)
      lines.push('')
    }
  }

  // ── Pipeline steps (flow logic) ─────────────────────────────────────────────
  const inputNode = sorted.find(n => n.type === 'input')
  const inputMessage = (inputNode?.data as unknown as InputNodeData)?.message || 'Enter your message here'

  const consumed = new Set<string>()
  const steps: string[] = []

  for (const node of sorted) {
    if (consumed.has(node.id)) continue
    if (node.type === 'input' || node.type === 'output') continue
    if (node.type === 'tool' || node.type === 'skill') continue

    if (node.type === 'agent') {
      const d = node.data as unknown as AgentNodeData
      steps.push(`    AgentStep(${toSnakeCase(d.name || d.label)}),`)

    } else if (node.type === 'parallel') {
      const branchTargets = (successors.get(node.id) ?? []).map(sid => nodeMap.get(sid)).filter(Boolean)
      for (const b of branchTargets) consumed.add(b!.id)
      const branchSteps = branchTargets
        .filter(b => b?.type === 'agent')
        .map(b => {
          const d = b!.data as unknown as AgentNodeData
          return `AgentStep(${toSnakeCase(d.name || d.label)})`
        })
      if (branchSteps.length > 0) {
        steps.push(`    ParallelStep([`)
        for (const s of branchSteps) steps.push(`        ${s},`)
        const d = node.data as unknown as ParallelNodeData
        const sep = d.mergeStrategy === 'first' ? 'lambda outs: outs[0]' : 'lambda outs: "\\n\\n---\\n\\n".join(outs)'
        steps.push(`    ], merge=${sep}),`)
      }

    } else if (node.type === 'loop') {
      const d = node.data as unknown as LoopNodeData
      const loopTargets = (successors.get(node.id) ?? []).map(sid => nodeMap.get(sid)).filter(Boolean)
      const loopAgent = loopTargets.find(n => n?.type === 'agent')
      if (loopAgent) {
        consumed.add(loopAgent.id)
        const ad = loopAgent.data as unknown as AgentNodeData
        const kw = py(d.stopKeyword || 'DONE')
        steps.push(`    LoopStep(`)
        steps.push(`        step=AgentStep(${toSnakeCase(ad.name || ad.label)}),`)
        steps.push(`        until=lambda ctx: "${kw}" in ctx.output,`)
        steps.push(`        max_iterations=${d.maxIterations || 3},`)
        steps.push(`    ),`)
      }

    } else if (node.type === 'branch') {
      const d = node.data as unknown as BranchNodeData
      const kw = py((d.conditionKeyword || 'yes').toLowerCase())
      const trueEdge  = flowEdges.find(e => e.source === node.id && e.sourceHandle === 'true')
      const falseEdge = flowEdges.find(e => e.source === node.id && e.sourceHandle === 'false')
      const trueNode  = trueEdge  ? nodeMap.get(trueEdge.target)  : null
      const falseNode = falseEdge ? nodeMap.get(falseEdge.target) : null
      if (trueNode)  consumed.add(trueNode.id)
      if (falseNode) consumed.add(falseNode.id)

      const mkStep = (n: Node | null | undefined) => {
        if (!n || n.type !== 'agent') return 'FunctionStep(lambda ctx: ctx)'
        const ad = n.data as unknown as AgentNodeData
        return `AgentStep(${toSnakeCase(ad.name || ad.label)})`
      }

      steps.push(`    BranchStep(`)
      steps.push(`        condition=lambda ctx: "yes" if "${kw}" in ctx.output.lower() else "no",`)
      steps.push(`        branches={`)
      steps.push(`            "yes": ${mkStep(trueNode)},`)
      steps.push(`            "no":  ${mkStep(falseNode)},`)
      steps.push(`        },`)
      steps.push(`    ),`)
    }
  }

  if (steps.length === 0) {
    lines.push('# ── Connect nodes to build the pipeline ──────────────────────────────────')
    return lines.join('\n')
  }

  lines.push('# ── Pipeline ─────────────────────────────────────────────────────────────')
  lines.push('pipeline = Pipeline([')
  for (const s of steps) lines.push(s)
  lines.push('])')
  lines.push('')
  lines.push('# ── Run ──────────────────────────────────────────────────────────────────')
  lines.push(`result = pipeline.run(`)
  lines.push(`    thread_id="flow-1",`)
  lines.push(`    message="${py(inputMessage)}",`)
  lines.push(`)`)
  lines.push('print(result)')

  return lines.join('\n')
}

// ── Emit helpers ──────────────────────────────────────────────────────────────

function emitToolFn(lines: string[], fnName: string, spec: ToolSpec) {
  const sig = paramSig(spec.parameters)
  const doc = (spec.description || fnName).replace(/"/g, "'").replace(/\n/g, ' ')
  lines.push(`def ${fnName}(${sig}) -> str:`)
  lines.push(`    """${doc}"""`)

  if ((spec.kind ?? 'python') === 'api') {
    const paramNames = (spec.parameters ?? []).map(p => p.name)
    const argsDict = `{${paramNames.map(n => `"${n}": ${n}`).join(', ')}}`
    const method = (spec.method || 'GET').toLowerCase()
    const hasBody = method !== 'get' && method !== 'delete' && !!(spec.body || '').trim()

    // Headers — default Content-Type to JSON when a body template is provided.
    const hdrs = parseHeaders(spec.headers)
    if (hasBody && !hdrs.some(([k]) => k.toLowerCase() === 'content-type')) {
      hdrs.push(['Content-Type', 'application/json'])
    }
    const hdrDict = `{${hdrs.map(([k, v]) => `${pyStr(k)}: ${pyStr(v)}`).join(', ')}}`

    lines.push(`    import requests`)
    lines.push(`    _args = ${argsDict}`)
    // Substitute {param} placeholders without disturbing literal JSON braces.
    lines.push(`    _url = ${pyStr(spec.url || '')}`)
    for (const n of paramNames) lines.push(`    _url = _url.replace("{${n}}", str(${n}))`)
    if (method === 'get' || method === 'delete') {
      lines.push(`    _resp = requests.${method}(_url, params=_args, headers=${hdrDict})`)
    } else if (hasBody) {
      lines.push(`    _body = ${pyStr(spec.body)}`)
      for (const n of paramNames) lines.push(`    _body = _body.replace("{${n}}", str(${n}))`)
      lines.push(`    _resp = requests.${method}(_url, data=_body, headers=${hdrDict})`)
    } else {
      lines.push(`    _resp = requests.${method}(_url, json=_args, headers=${hdrDict})`)
    }
    lines.push(`    return _resp.text`)
  } else {
    const body = (spec.code || '').replace(/\s+$/, '')
    if (body.trim()) {
      for (const ln of body.split('\n')) lines.push(ln ? `    ${ln}` : '')
    } else {
      lines.push(`    return "${py(spec.mockReturnValue || 'Tool result')}"`)
    }
  }
  lines.push('')
}

function mcpExpr(m: AgentMCP): string {
  if ((m.transport ?? 'http') === 'http') {
    const authArg = m.apiKey ? `, auth=MCPAuthConfig(bearer_token="${py(m.apiKey)}")` : ''
    return `MCPClient.from_url("${py(m.url || 'http://localhost:8080/sse')}", name="${py(m.name || 'mcp')}"${authArg})`
  }
  const rawArgs = (m.args || '').trim()
  const argsArray = rawArgs ? `, args=[${rawArgs.split(/\s+/).map(a => `"${py(a)}"`).join(', ')}]` : ''
  return `MCPClient.from_subprocess("${py(m.command || 'python3')}"${argsArray}, name="${py(m.name || 'mcp')}")`
}

function emitMemory(lines: string[], varName: string, c: { shortTerm?: { enabled: boolean; windowSize: number }; longTerm?: { enabled: boolean; path: string } }) {
  const parts: string[] = []
  if (c.longTerm?.enabled) {
    lines.push(`${varName}_long = LongTermMemory(base_path="${py(c.longTerm.path || './moya_memory')}")`)
    parts.push(`${varName}_long`)
  }
  if (c.shortTerm?.enabled) {
    lines.push(`${varName}_short = ShortTermMemory(window_size=${c.shortTerm.windowSize || 10})`)
    parts.push(`${varName}_short`)
  }
  if (parts.length > 1) {
    lines.push(`${varName}_memory = CompositeMemory([${parts.join(', ')}])`)
  } else {
    lines.push(`${varName}_memory = ${parts[0]}`)
  }
}
