import { useState } from 'react'
import { Bot, MessageSquare, Monitor, Wrench, Sparkles, GitBranch, RefreshCw, GitFork, ChevronDown } from 'lucide-react'
import { NODE_COLORS, NODE_DESCRIPTIONS } from '../constants'

interface PaletteItem {
  type: string
  label: string
  icon: React.ReactNode
  description: string
}

const CORE_ITEMS: PaletteItem[] = [
  { type: 'input',  label: 'Input',  icon: <MessageSquare size={15} />, description: NODE_DESCRIPTIONS.input },
  { type: 'agent',  label: 'Agent',  icon: <Bot size={15} />,           description: NODE_DESCRIPTIONS.agent },
  { type: 'output', label: 'Output', icon: <Monitor size={15} />,       description: NODE_DESCRIPTIONS.output },
]

const ADVANCED_ITEMS: PaletteItem[] = [
  { type: 'tool',     label: 'Tool',     icon: <Wrench size={15} />,    description: NODE_DESCRIPTIONS.tool },
  { type: 'skill',    label: 'Skill',    icon: <Sparkles size={15} />,  description: NODE_DESCRIPTIONS.skill },
  { type: 'parallel', label: 'Parallel', icon: <GitBranch size={15} />, description: NODE_DESCRIPTIONS.parallel },
  { type: 'loop',     label: 'Loop',     icon: <RefreshCw size={15} />, description: NODE_DESCRIPTIONS.loop },
  { type: 'branch',   label: 'Branch',   icon: <GitFork size={15} />,   description: NODE_DESCRIPTIONS.branch },
]

function PaletteCard({ item }: { item: PaletteItem }) {
  const c = NODE_COLORS[item.type]

  function onDragStart(e: React.DragEvent) {
    e.dataTransfer.setData('application/reactflow-nodetype', item.type)
    e.dataTransfer.effectAllowed = 'move'
  }

  return (
    <div
      draggable
      onDragStart={onDragStart}
      title={item.description}
      className="flex items-center gap-2.5 px-2.5 py-2 bg-white rounded-lg border border-slate-200 cursor-grab active:cursor-grabbing hover:border-slate-300 hover:shadow-sm transition-all select-none"
    >
      <div className={`${c.accent} w-[3px] self-stretch rounded-full flex-shrink-0`} />
      <span className={`${c.headerText} flex-shrink-0`}>{item.icon}</span>
      <p className="text-xs font-medium text-slate-700">{item.label}</p>
    </div>
  )
}

function SectionHeader({ label, expanded, onToggle }: {
  label: string; expanded: boolean; onToggle: () => void
}) {
  return (
    <button
      onClick={onToggle}
      className="w-full flex items-center justify-between px-0.5 py-1 group"
    >
      <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest group-hover:text-slate-600 transition-colors">
        {label}
      </span>
      <ChevronDown
        size={11}
        className={`text-slate-400 transition-transform duration-150 ${expanded ? '' : '-rotate-90'}`}
      />
    </button>
  )
}

export function NodePalette() {
  const [advancedOpen, setAdvancedOpen] = useState<boolean>(() => {
    return localStorage.getItem('moya_palette_advanced') === 'true'
  })

  function toggleAdvanced() {
    const next = !advancedOpen
    setAdvancedOpen(next)
    localStorage.setItem('moya_palette_advanced', String(next))
  }

  return (
    <div className="w-52 flex-shrink-0 bg-slate-50 border-r border-slate-200 flex flex-col overflow-hidden">
      {/* Items */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-4">
        {/* Core */}
        <div>
          <div className="px-0.5 mb-2">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest">Core</span>
          </div>
          <div className="space-y-1.5">
            {CORE_ITEMS.map(item => <PaletteCard key={item.type} item={item} />)}
          </div>
        </div>

        {/* Advanced */}
        <div>
          <SectionHeader
            label="Advanced"
            expanded={advancedOpen}
            onToggle={toggleAdvanced}
          />
          {advancedOpen && (
            <div className="space-y-1.5 mt-2">
              {ADVANCED_ITEMS.map(item => <PaletteCard key={item.type} item={item} />)}
            </div>
          )}
        </div>
      </div>

    </div>
  )
}
