import { Handle, Position, type NodeProps, type Node } from '@xyflow/react'
import { RefreshCw } from 'lucide-react'
import { NodeWrapper } from './NodeWrapper'
import type { LoopNodeData } from '../../types'

type LoopNodeType = Node<LoopNodeData>

export function LoopNode({ data, selected }: NodeProps<LoopNodeType>) {
  const kw  = data.stopKeyword || 'DONE'
  const max = data.maxIterations ?? 3
  return (
    <div>
      <Handle type="target" position={Position.Left}  className="!bg-blue-600 !border-white !border-2 !w-3 !h-3" />
      <NodeWrapper type="loop" icon={<RefreshCw size={14} />} title={data.label || 'Loop'} selected={selected}>
        <p className="text-xs text-slate-400">until "{kw}" · max {max}×</p>
      </NodeWrapper>
      <Handle type="source" position={Position.Right} className="!bg-blue-600 !border-white !border-2 !w-3 !h-3" />
    </div>
  )
}
