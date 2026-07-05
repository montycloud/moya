import { Handle, Position, type NodeProps, type Node } from '@xyflow/react'
import { Bot } from 'lucide-react'
import { NodeWrapper } from './NodeWrapper'
import type { AgentNodeData } from '../../types'

type AgentNodeType = Node<AgentNodeData>

const PROVIDER_LABELS: Record<string, string> = {
  openai: 'OpenAI', ollama: 'Ollama', bedrock: 'Bedrock', azure: 'Azure', a2a: 'A2A',
}

export function AgentNode({ data, selected }: NodeProps<AgentNodeType>) {
  const provider = PROVIDER_LABELS[data.provider] ?? data.provider
  const isA2A = data.provider === 'a2a'

  const toolCount = (data.toolIds?.length ?? 0) + (data.inlineTools?.length ?? 0)
  const memOn     = !!(data.memory?.shortTerm?.enabled || data.memory?.longTerm?.enabled)
  const mcpCount  = data.mcpServers?.length ?? 0

  const chips: { key: string; label: string; cls: string }[] = []
  if (isA2A)     chips.push({ key: 'r', label: 'remote', cls: 'bg-rose-100 text-rose-700' })
  if (toolCount) chips.push({ key: 't', label: `${toolCount} tool${toolCount > 1 ? 's' : ''}`, cls: 'bg-sky-100 text-sky-700' })
  if (memOn)     chips.push({ key: 'm', label: 'memory', cls: 'bg-violet-100 text-violet-700' })
  if (mcpCount)  chips.push({ key: 'p', label: `${mcpCount} mcp`, cls: 'bg-amber-100 text-amber-700' })

  const subtitle = isA2A
    ? `${provider} · ${data.endpointUrl || 'no endpoint'}`
    : `${data.model} · ${provider}`

  return (
    <div>
      <Handle type="target" position={Position.Left}  className="!bg-indigo-500 !border-white !border-2 !w-3 !h-3" />
      <NodeWrapper type="agent" icon={<Bot size={14} />} title={data.label || data.name || 'Agent'} selected={selected}>
        <p className="text-xs text-slate-400 truncate">{subtitle}</p>
        {chips.length > 0 && (
          <div className="flex flex-wrap gap-1 pt-1">
            {chips.map(c => (
              <span key={c.key} className={`text-[9px] font-semibold px-1.5 py-0.5 rounded ${c.cls}`}>{c.label}</span>
            ))}
          </div>
        )}
      </NodeWrapper>
      <Handle type="source" position={Position.Right} className="!bg-indigo-500 !border-white !border-2 !w-3 !h-3" />
    </div>
  )
}
