import { Handle, Position, type NodeProps, type Node } from '@xyflow/react'
import { Network } from 'lucide-react'
import { NodeWrapper } from './NodeWrapper'
import type { A2ANodeData } from '../../types'

type A2ANodeType = Node<A2ANodeData>

export function A2ANode({ data, selected }: NodeProps<A2ANodeType>) {
  const endpoint = data.endpointUrl
    ? (data.endpointUrl.length > 30 ? data.endpointUrl.slice(0, 30) + '…' : data.endpointUrl)
    : '—'
  return (
    <div>
      <Handle type="target" position={Position.Left}  className="!bg-rose-500 !border-white !border-2 !w-3 !h-3" />
      <NodeWrapper type="a2a" icon={<Network size={14} />} title={data.label || data.name || 'Remote Agent'} selected={selected}>
        <p className="text-xs text-slate-400">{endpoint}</p>
      </NodeWrapper>
      <Handle type="source" position={Position.Right} className="!bg-rose-500 !border-white !border-2 !w-3 !h-3" />
    </div>
  )
}
