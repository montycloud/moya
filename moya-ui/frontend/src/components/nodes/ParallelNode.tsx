import { Handle, Position, type NodeProps, type Node } from '@xyflow/react'
import { GitBranch } from 'lucide-react'
import { NodeWrapper } from './NodeWrapper'
import type { ParallelNodeData } from '../../types'

type ParallelNodeType = Node<ParallelNodeData>

export function ParallelNode({ data, selected }: NodeProps<ParallelNodeType>) {
  const count = data.branchCount ?? 2
  const handles = Array.from({ length: count }, (_, i) => i)
  const totalSpan = (count - 1) * 28
  const topOffset = 50 - totalSpan / 2

  return (
    <div>
      <Handle type="target" position={Position.Left} className="!bg-slate-400 !border-white !border-2 !w-3 !h-3" />
      <NodeWrapper type="parallel" icon={<GitBranch size={14} />} title={data.label || 'Parallel'} selected={selected}>
        <p className="text-xs text-slate-400">{count} branches · {data.mergeStrategy ?? 'concat'}</p>
      </NodeWrapper>
      {handles.map(i => (
        <Handle
          key={`branch-${i}`}
          id={`branch-${i}`}
          type="source"
          position={Position.Right}
          style={{ top: `${topOffset + i * 28}%` }}
          className="!bg-slate-400 !border-white !border-2 !w-3 !h-3"
        />
      ))}
    </div>
  )
}
