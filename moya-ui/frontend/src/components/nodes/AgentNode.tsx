import { Handle, Position, type NodeProps, type Node } from '@xyflow/react'
import { Bot } from 'lucide-react'
import { NodeWrapper } from './NodeWrapper'
import type { AgentNodeData } from '../../types'

type AgentNodeType = Node<AgentNodeData>

const PROVIDER_LABELS: Record<string, string> = {
  openai: 'OpenAI', ollama: 'Ollama', bedrock: 'Bedrock', azure: 'Azure',
}

export function AgentNode({ data, selected }: NodeProps<AgentNodeType>) {
  const provider = PROVIDER_LABELS[data.provider] ?? data.provider
  return (
    <div>
      <Handle type="target" position={Position.Left}  className="!bg-indigo-500 !border-white !border-2 !w-3 !h-3" />
      <NodeWrapper type="agent" icon={<Bot size={14} />} title={data.label || data.name || 'Agent'} selected={selected}>
        <p className="text-xs text-slate-400">{data.model} · {provider}</p>
      </NodeWrapper>
      <Handle type="source" position={Position.Right} className="!bg-indigo-500 !border-white !border-2 !w-3 !h-3" />
    </div>
  )
}
