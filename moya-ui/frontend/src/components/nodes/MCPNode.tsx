import { Handle, Position, type NodeProps, type Node } from '@xyflow/react'
import { Plug } from 'lucide-react'
import { NodeWrapper } from './NodeWrapper'
import type { MCPNodeData } from '../../types'

type MCPNodeType = Node<MCPNodeData>

export function MCPNode({ data, selected }: NodeProps<MCPNodeType>) {
  const transport = data.transport === 'http' ? 'HTTP/SSE' : 'stdio'
  const endpoint  = data.transport === 'http' ? (data.url || '—') : (data.command || '—')
  return (
    <div>
      <Handle type="target" position={Position.Left}  className="!bg-amber-500 !border-white !border-2 !w-3 !h-3" />
      <NodeWrapper type="mcp" icon={<Plug size={14} />} title={data.label || data.name || 'MCP Server'} selected={selected}>
        <p className="text-xs text-slate-400">{transport} · {endpoint}</p>
      </NodeWrapper>
      <Handle type="source" position={Position.Right} className="!bg-amber-500 !border-white !border-2 !w-3 !h-3" />
    </div>
  )
}
