import React from 'react'
import { NODE_COLORS } from '../../constants'

interface NodeWrapperProps {
  type: string
  icon: React.ReactNode
  title: string
  selected?: boolean
  children?: React.ReactNode
}

export function NodeWrapper({ type, icon, title, selected, children }: NodeWrapperProps) {
  const c = NODE_COLORS[type] ?? NODE_COLORS['agent']
  return (
    <div className={[
      'bg-white rounded-lg flex overflow-hidden transition-all duration-150 min-w-[175px]',
      selected
        ? `shadow-md ring-2 ${c.ring}`
        : 'shadow-sm border border-slate-200 hover:shadow-md hover:border-slate-300',
    ].join(' ')}>
      {/* Colored left accent strip */}
      <div className={`w-[3px] flex-shrink-0 ${c.accent}`} />
      {/* Content */}
      <div className="flex-1 px-3 py-2.5 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className={`${c.headerText} flex-shrink-0`}>{icon}</span>
          <span className="font-semibold text-sm text-slate-800 truncate">{title}</span>
        </div>
        {children && (
          <div className="space-y-1">
            {children}
          </div>
        )}
      </div>
    </div>
  )
}

export function Badge({ text, color }: { text: string; color?: string }) {
  return (
    <span className={`inline-block text-[10px] font-semibold px-1.5 py-0.5 rounded ${color ?? 'bg-slate-100 text-slate-600'}`}>
      {text}
    </span>
  )
}
