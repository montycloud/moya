import type { Node, Edge } from '@xyflow/react'
import type {
  AgentNodeData, ToolNodeData, SkillNodeData,
  InputNodeData, ParallelNodeData, LoopNodeData, BranchNodeData,
  MCPNodeData, A2ANodeData,
  ToolParameter,
} from '../types'

function toSnakeCase(s: string): string {
  return (s || 'agent')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    || 'agent'
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

export function generateCode(nodes: Node[], edges: Edge[]): string {
  if (nodes.length === 0) {
    return '# Drag nodes onto the canvas to start building your flow.\n# Generated Python code will appear here.'
  }

  const nodeMap = new Map(nodes.map(n => [n.id, n]))

  // Classify edges: capability (tool/skill/mcp → agent) vs flow
  const flowEdges = edges.filter(e => {
    const src = nodeMap.get(e.source)
    return src && src.type !== 'tool' && src.type !== 'skill' && src.type !== 'mcp'
  })
  const capEdges = edges.filter(e => {
    const src = nodeMap.get(e.source)
    return src && (src.type === 'tool' || src.type === 'skill' || src.type === 'mcp')
  })

  // Build flow adjacency
  const successors = new Map<string, string[]>()
  const predecessors = new Map<string, string[]>()
  for (const e of flowEdges) {
    if (!successors.has(e.source)) successors.set(e.source, [])
    successors.get(e.source)!.push(e.target)
    if (!predecessors.has(e.target)) predecessors.set(e.target, [])
    predecessors.get(e.target)!.push(e.source)
  }

  // Topological sort (flow nodes only — exclude capability nodes)
  const flowNodes = nodes.filter(n => n.type !== 'tool' && n.type !== 'skill' && n.type !== 'mcp')
  const sorted = topologicalSort(flowNodes, successors, predecessors)

  // Map agent → its attached tool/skill/mcp node IDs
  const agentTools  = new Map<string, string[]>()
  const agentSkills = new Map<string, string[]>()
  const agentMCPs   = new Map<string, string[]>()
  for (const e of capEdges) {
    const src = nodeMap.get(e.source)
    if (!src) continue
    if (src.type === 'tool') {
      if (!agentTools.has(e.target)) agentTools.set(e.target, [])
      agentTools.get(e.target)!.push(e.source)
    } else if (src.type === 'skill') {
      if (!agentSkills.has(e.target)) agentSkills.set(e.target, [])
      agentSkills.get(e.target)!.push(e.source)
    } else if (src.type === 'mcp') {
      if (!agentMCPs.has(e.target)) agentMCPs.set(e.target, [])
      agentMCPs.get(e.target)!.push(e.source)
    }
  }

  // Determine which step imports are needed
  const hasParallel = nodes.some(n => n.type === 'parallel')
  const hasLoop     = nodes.some(n => n.type === 'loop')
  const hasBranch   = nodes.some(n => n.type === 'branch')
  const hasTools    = nodes.some(n => n.type === 'tool')
  const hasSkills   = nodes.some(n => n.type === 'skill')
  const hasMCP      = nodes.some(n => n.type === 'mcp')
  const hasA2A      = nodes.some(n => n.type === 'a2a')

  const stepImports = ['Pipeline', 'AgentStep']
  if (hasParallel) stepImports.push('ParallelStep')
  if (hasLoop)     stepImports.push('LoopStep')
  if (hasBranch)   stepImports.push('BranchStep')
  if (hasTools || hasMCP) stepImports.push('ToolRegistry')
  if (hasTools)    stepImports.push('Tool')
  if (hasSkills)   stepImports.push('Skill')

  const lines: string[] = []

  // ── Imports ──────────────────────────────────────────────────────────────
  lines.push(`from moya import create_agent, ${stepImports.join(', ')}`)
  if (hasMCP) lines.push('from moya.mcp import MCPClient')
  if (hasA2A) lines.push('from moya.a2a.client import A2AAgent, A2AAgentConfig')
  lines.push('')

  // ── MCP Servers ───────────────────────────────────────────────────────────
  const mcpNodes = nodes.filter(n => n.type === 'mcp')
  if (mcpNodes.length > 0) {
    lines.push('# ── MCP Servers ──────────────────────────────────────────────────────────')
    lines.push('tool_registry = ToolRegistry()')
    for (const mn of mcpNodes) {
      const d = mn.data as unknown as MCPNodeData
      const varName = `${toSnakeCase(d.name || 'mcp')}_client`
      if ((d.transport ?? 'http') === 'http') {
        const authArg = d.apiKey ? `, auth=MCPClient.MCPAuthConfig(bearer_token="${d.apiKey.replace(/"/g, '\\"')}")` : ''
        lines.push(`${varName} = MCPClient.from_url("${(d.url || 'http://localhost:8080/sse').replace(/"/g, '\\"')}", name="${(d.name || 'mcp').replace(/"/g, '\\"')}"${authArg})`)
      } else {
        const rawArgs = (d.args || '').trim()
        const argsArray = rawArgs ? `, args=[${rawArgs.split(/\s+/).map(a => `"${a.replace(/"/g, '\\"')}"`).join(', ')}]` : ''
        lines.push(`${varName} = MCPClient.from_subprocess("${(d.command || 'python3').replace(/"/g, '\\"')}"${argsArray}, name="${(d.name || 'mcp').replace(/"/g, '\\"')}")`)
      }
      lines.push(`for _tool in ${varName}.get_tools():`)
      lines.push(`    tool_registry.register_tool(_tool)`)
    }
    lines.push('')
  }

  // ── Tools ─────────────────────────────────────────────────────────────────
  const toolNodes = nodes.filter(n => n.type === 'tool')
  if (toolNodes.length > 0) {
    if (mcpNodes.length === 0) {
      lines.push('# ── Tools ────────────────────────────────────────────────────────────────')
      lines.push('tool_registry = ToolRegistry()')
      lines.push('')
    } else {
      lines.push('# ── Additional local tools ───────────────────────────────────────────────')
    }
    for (const tn of toolNodes) {
      const d = tn.data as unknown as ToolNodeData
      const fnName = `mock_${toSnakeCase(d.name)}`
      const paramSig = (d.parameters ?? []).map((p: ToolParameter) => `${p.name}: ${p.type || 'str'}`).join(', ')
      lines.push(`def ${fnName}(${paramSig}) -> str:`)
      lines.push(`    """${d.description || d.name}`)
      if ((d.parameters ?? []).length > 0) {
        lines.push('')
        lines.push('    Parameters:')
        for (const p of d.parameters) {
          lines.push(`    - ${p.name}: ${p.description || p.name}`)
        }
      }
      lines.push('    """')
      lines.push(`    return "${(d.mockReturnValue || 'Tool result').replace(/"/g, '\\"')}"`)
      lines.push('')
      lines.push(`tool_registry.register_tool(Tool(`)
      lines.push(`    name="${d.name}",`)
      lines.push(`    description="${(d.description || d.name).replace(/"/g, '\\"')}",`)
      lines.push(`    function=${fnName},`)
      lines.push(`)`)
      lines.push('')
    }
  }

  // ── Skills ────────────────────────────────────────────────────────────────
  const skillNodes = nodes.filter(n => n.type === 'skill')
  if (skillNodes.length > 0) {
    lines.push('# ── Skills ───────────────────────────────────────────────────────────────')
    for (const sn of skillNodes) {
      const d = sn.data as unknown as SkillNodeData
      const varName = `${toSnakeCase(d.name)}_skill`
      lines.push(`${varName} = Skill(`)
      lines.push(`    name="${d.name}",`)
      lines.push(`    description="${(d.description || d.name).replace(/"/g, '\\"')}",`)
      if (d.promptSnippet) {
        lines.push(`    prompt_snippet="${d.promptSnippet.replace(/"/g, '\\"').replace(/\n/g, '\\n')}",`)
      }
      lines.push(`)`)
    }
    lines.push('')
  }

  // ── Agents ────────────────────────────────────────────────────────────────
  const agentNodes = nodes.filter(n => n.type === 'agent')
  if (agentNodes.length > 0) {
    lines.push('# ── Agents ───────────────────────────────────────────────────────────────')
    for (const an of agentNodes) {
      const d = an.data as unknown as AgentNodeData
      const varName = toSnakeCase(d.name || d.label)
      const toolIds  = agentTools.get(an.id)  ?? []
      const skillIds = agentSkills.get(an.id) ?? []
      const skillVars = skillIds
        .map(sid => nodeMap.get(sid))
        .filter(Boolean)
        .map(sn => `${toSnakeCase((sn!.data as unknown as SkillNodeData).name)}_skill`)

      lines.push(`${varName} = create_agent(`)
      lines.push(`    "${d.provider}",`)
      lines.push(`    name="${d.name || d.label}",`)
      lines.push(`    description="${(d.description || `${d.label} agent`).replace(/"/g, '\\"')}",`)
      lines.push(`    model="${d.model}",`)
      if (d.systemPrompt) {
        lines.push(`    system_prompt="${d.systemPrompt.replace(/"/g, '\\"').replace(/\n/g, '\\n')}",`)
      }
      if ((d.tags ?? []).length > 0) {
        lines.push(`    tags=${JSON.stringify(d.tags)},`)
      }
      const mcpIds = agentMCPs.get(an.id) ?? []
      if (toolIds.length > 0 || mcpIds.length > 0) lines.push(`    tool_registry=tool_registry,`)
      if (skillVars.length > 0)  lines.push(`    skills=[${skillVars.join(', ')}],`)
      lines.push(`)`)
    }
    lines.push('')
  }

  // ── A2A Remote Agents ─────────────────────────────────────────────────────
  const a2aNodes = nodes.filter(n => n.type === 'a2a')
  if (a2aNodes.length > 0) {
    lines.push('# ── A2A Remote Agents ────────────────────────────────────────────────────')
    for (const an of a2aNodes) {
      const d = an.data as unknown as A2ANodeData
      const varName = toSnakeCase(d.name || d.label)
      lines.push(`${varName}_config = A2AAgentConfig(`)
      lines.push(`    agent_name="${(d.name || 'remote_agent').replace(/"/g, '\\"')}",`)
      lines.push(`    agent_type="a2a",`)
      lines.push(`    description="${(d.description || 'Remote A2A agent').replace(/"/g, '\\"')}",`)
      lines.push(`    endpoint_url="${(d.endpointUrl || 'http://localhost:8001').replace(/"/g, '\\"')}",`)
      if ((d.timeoutSeconds ?? 60) !== 60) {
        lines.push(`    timeout_seconds=${d.timeoutSeconds},`)
      }
      lines.push(`)`)
      lines.push(`${varName} = A2AAgent(${varName}_config)`)
    }
    lines.push('')
  }

  // ── Pipeline steps ────────────────────────────────────────────────────────
  const inputNode = sorted.find(n => n.type === 'input')
  const inputMessage = (inputNode?.data as unknown as InputNodeData)?.message || 'Enter your message here'

  const consumed = new Set<string>()
  const steps: string[] = []

  for (const node of sorted) {
    if (consumed.has(node.id)) continue
    if (node.type === 'input' || node.type === 'output') continue
    if (node.type === 'tool' || node.type === 'skill' || node.type === 'mcp') continue

    if (node.type === 'agent') {
      const d = node.data as unknown as AgentNodeData
      steps.push(`    AgentStep(${toSnakeCase(d.name || d.label)}),`)

    } else if (node.type === 'a2a') {
      const d = node.data as unknown as A2ANodeData
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
        const kw = (d.stopKeyword || 'DONE').replace(/"/g, '\\"')
        steps.push(`    LoopStep(`)
        steps.push(`        step=AgentStep(${toSnakeCase(ad.name || ad.label)}),`)
        steps.push(`        until=lambda ctx: "${kw}" in ctx.output,`)
        steps.push(`        max_iterations=${d.maxIterations || 3},`)
        steps.push(`    ),`)
      }

    } else if (node.type === 'branch') {
      const d = node.data as unknown as BranchNodeData
      const kw = (d.conditionKeyword || 'yes').replace(/"/g, '\\"')
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
  lines.push(`    message="${inputMessage.replace(/"/g, '\\"').replace(/\n/g, '\\n')}",`)
  lines.push(`)`)
  lines.push('print(result)')

  return lines.join('\n')
}
