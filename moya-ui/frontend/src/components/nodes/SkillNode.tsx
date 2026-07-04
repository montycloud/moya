import { Handle, Position, type NodeProps, type Node } from '@xyflow/react'
import { Sparkles } from 'lucide-react'
import { NodeWrapper } from './NodeWrapper'
import type { SkillNodeData } from '../../types'

type SkillNodeType = Node<SkillNodeData>

export function SkillNode({ data, selected }: NodeProps<SkillNodeType>) {
  const snippet = data.promptSnippet
    ? (data.promptSnippet.length > 45 ? data.promptSnippet.slice(0, 45) + '…' : data.promptSnippet)
    : null

  return (
    <div>
      <Handle type="target" position={Position.Left}  className="!bg-violet-500 !border-white !border-2 !w-3 !h-3" />
      <NodeWrapper type="skill" icon={<Sparkles size={14} />} title={data.label || data.name || 'Skill'} selected={selected}>
        {snippet && <p className="text-xs text-slate-400 truncate">{snippet}</p>}
      </NodeWrapper>
      <Handle type="source" position={Position.Right} className="!bg-violet-500 !border-white !border-2 !w-3 !h-3" />
    </div>
  )
}
