import { Handle, Position, type NodeProps, type Node } from '@xyflow/react'
import { GitFork } from 'lucide-react'
import { NodeWrapper } from './NodeWrapper'
import type { BranchNodeData } from '../../types'

type BranchNodeType = Node<BranchNodeData>

export function BranchNode({ data, selected }: NodeProps<BranchNodeType>) {
  const kw = data.conditionKeyword || 'yes'
  return (
    <div>
      <Handle type="target" position={Position.Left} className="!bg-cyan-500 !border-white !border-2 !w-3 !h-3" />
      <NodeWrapper type="branch" icon={<GitFork size={14} />} title={data.label || 'Branch'} selected={selected}>
        <p className="text-xs text-slate-400">if output contains "{kw}"</p>
      </NodeWrapper>
      <Handle id="true"  type="source" position={Position.Right} style={{ top: '35%' }} className="!bg-teal-500 !border-white !border-2 !w-3 !h-3" />
      <Handle id="false" type="source" position={Position.Right} style={{ top: '65%' }} className="!bg-slate-300 !border-white !border-2 !w-3 !h-3" />
    </div>
  )
}
