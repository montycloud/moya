import { Handle, Position, type NodeProps, type Node } from '@xyflow/react'
import { MessageSquare } from 'lucide-react'
import { NodeWrapper } from './NodeWrapper'
import type { InputNodeData } from '../../types'

type InputNodeType = Node<InputNodeData>

export function InputNode({ data, selected }: NodeProps<InputNodeType>) {
  const preview = data.message
    ? (data.message.length > 55 ? data.message.slice(0, 55) + '…' : data.message)
    : null

  return (
    <div>
      <NodeWrapper type="input" icon={<MessageSquare size={14} />} title="Input" selected={selected}>
        {preview && <p className="text-xs text-slate-500 leading-relaxed">{preview}</p>}
      </NodeWrapper>
      <Handle type="source" position={Position.Right} className="!bg-blue-500 !border-white !border-2 !w-3 !h-3" />
    </div>
  )
}
