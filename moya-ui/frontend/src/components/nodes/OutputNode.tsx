import { Handle, Position, type NodeProps, type Node } from '@xyflow/react'
import { Monitor } from 'lucide-react'
import { NodeWrapper } from './NodeWrapper'
import type { OutputNodeData } from '../../types'

type OutputNodeType = Node<OutputNodeData>

export function OutputNode({ data, selected }: NodeProps<OutputNodeType>) {
  const preview = data.result
    ? (data.result.length > 60 ? data.result.slice(0, 60) + '…' : data.result)
    : null

  return (
    <div>
      <Handle type="target" position={Position.Left} className="!bg-teal-500 !border-white !border-2 !w-3 !h-3" />
      <NodeWrapper type="output" icon={<Monitor size={14} />} title="Output" selected={selected}>
        {preview
          ? <p className="text-xs text-slate-600 leading-relaxed">{preview}</p>
          : <p className="text-xs text-slate-300">Run to see result</p>
        }
      </NodeWrapper>
    </div>
  )
}
