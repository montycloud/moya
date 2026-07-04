import { Handle, Position, type NodeProps, type Node } from '@xyflow/react'
import { Wrench } from 'lucide-react'
import { NodeWrapper } from './NodeWrapper'
import type { ToolNodeData } from '../../types'

type ToolNodeType = Node<ToolNodeData>

export function ToolNode({ data, selected }: NodeProps<ToolNodeType>) {
  const paramCount = data.parameters?.length ?? 0
  const subtitle = paramCount > 0
    ? `${paramCount} param${paramCount > 1 ? 's' : ''}`
    : data.description || null

  return (
    <div>
      <Handle type="target" position={Position.Left}  className="!bg-sky-500 !border-white !border-2 !w-3 !h-3" />
      <NodeWrapper type="tool" icon={<Wrench size={14} />} title={data.label || data.name || 'Tool'} selected={selected}>
        {subtitle && <p className="text-xs text-slate-400">{subtitle}</p>}
      </NodeWrapper>
      <Handle type="source" position={Position.Right} className="!bg-sky-500 !border-white !border-2 !w-3 !h-3" />
    </div>
  )
}
