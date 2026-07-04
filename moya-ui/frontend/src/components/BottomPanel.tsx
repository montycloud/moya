import { Code2, Terminal, Copy, CheckCheck, ChevronDown, X, AlertCircle } from 'lucide-react'
import { useState } from 'react'
import type { TraceEvent } from '../types'
import { NODE_COLORS } from '../constants'

interface Props {
  activeTab: 'code' | 'output' | null   // null = closed
  onTabChange: (t: 'code' | 'output' | null) => void
  code: string
  traceEvents: TraceEvent[]
  finalOutput: string
  isExecuting: boolean
  runError: string | null
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  function copy() {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }
  return (
    <button onClick={copy} className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-700 px-2 py-1 rounded transition-colors">
      {copied ? <CheckCheck size={12} className="text-teal-500" /> : <Copy size={12} />}
      {copied ? 'Copied!' : 'Copy'}
    </button>
  )
}

function TraceRow({ event }: { event: TraceEvent }) {
  const c = NODE_COLORS[event.nodeType] ?? NODE_COLORS['agent']
  const [expanded, setExpanded] = useState(false)
  const isWarning = event.status === 'warning'

  const dot = event.status === 'started'
    ? <div className="w-2 h-2 rounded-full bg-blue-400 animate-pulse flex-shrink-0" />
    : event.status === 'error'
    ? <div className="w-2 h-2 rounded-full bg-rose-500 flex-shrink-0" />
    : isWarning
    ? <div className="w-2 h-2 rounded-full bg-amber-400 flex-shrink-0" />
    : <div className="w-2 h-2 rounded-full bg-teal-500 flex-shrink-0" />

  return (
    <div className={`rounded-lg overflow-hidden ${isWarning ? 'border border-amber-200 bg-amber-50' : 'border border-slate-100'}`}>
      <button
        onClick={() => setExpanded(v => !v)}
        className="w-full flex items-center gap-2.5 px-3 py-2 hover:bg-slate-50 transition-colors text-left"
      >
        {dot}
        {isWarning
          ? <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-amber-100 text-amber-700">warn</span>
          : <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${c.badge}`}>{event.nodeType}</span>
        }
        <span className={`text-xs font-medium flex-1 truncate ${isWarning ? 'text-amber-800' : 'text-slate-700'}`}>{event.nodeName}</span>
        {event.status === 'completed' && (
          <span className="text-[10px] text-slate-400">{event.durationMs}ms</span>
        )}
        {event.output && (
          expanded
            ? <ChevronDown size={11} className="text-slate-400 flex-shrink-0 rotate-180" />
            : <ChevronDown size={11} className="text-slate-400 flex-shrink-0" />
        )}
      </button>
      {expanded && event.output && (
        <div className="px-3 pb-2.5 pt-1 border-t border-slate-100 bg-slate-50">
          <p className="text-[10px] text-slate-500 font-mono whitespace-pre-wrap leading-relaxed max-h-40 overflow-y-auto">
            {event.output}
          </p>
        </div>
      )}
    </div>
  )
}

function CodeView({ code }: { code: string }) {
  return (
    <div className="flex-1 overflow-auto relative">
      <div className="absolute top-2 right-3 z-10">
        <CopyButton text={code} />
      </div>
      <pre className="p-4 text-xs font-mono text-slate-100 leading-relaxed whitespace-pre overflow-x-auto min-h-full bg-slate-950">
        {code}
      </pre>
    </div>
  )
}

function OutputView({ traceEvents, finalOutput, isExecuting, runError }: {
  traceEvents: TraceEvent[]; finalOutput: string; isExecuting: boolean; runError: string | null
}) {
  if (runError) {
    return (
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {traceEvents.length > 0 && (
          <div className="space-y-1.5">
            {traceEvents.map((e, i) => <TraceRow key={i} event={e} />)}
          </div>
        )}
        <div className="border border-rose-200 rounded-xl overflow-hidden">
          <div className="bg-rose-50 border-b border-rose-200 px-3 py-2 flex items-center gap-2">
            <AlertCircle size={13} className="text-rose-500 flex-shrink-0" />
            <span className="text-rose-700 text-xs font-semibold">Run failed</span>
          </div>
          <div className="p-3 bg-white">
            <p className="text-xs text-rose-600 font-mono whitespace-pre-wrap leading-relaxed">{runError}</p>
            {runError.toLowerCase().includes('fetch') || runError.toLowerCase().includes('network') || runError.includes('8000') ? (
              <p className="text-[11px] text-slate-500 mt-2">
                Make sure the backend is running: <code className="font-mono bg-slate-100 px-1 rounded">cd moya-ui/backend && python main.py</code>
              </p>
            ) : null}
          </div>
        </div>
      </div>
    )
  }

  if (traceEvents.length === 0 && !isExecuting) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-sm text-slate-400 italic">Run your flow to see the execution trace</p>
      </div>
    )
  }
  return (
    <div className="flex-1 overflow-y-auto p-3 space-y-3">
      <div className="space-y-1.5">
        {traceEvents.map((e, i) => <TraceRow key={i} event={e} />)}
        {isExecuting && (
          <div className="flex items-center gap-2 px-3 py-2">
            <div className="w-2 h-2 rounded-full bg-blue-400 animate-bounce" />
            <span className="text-xs text-slate-500">Executing…</span>
          </div>
        )}
      </div>
      {finalOutput && (
        <div className="border border-teal-200 rounded-xl overflow-hidden">
          <div className="bg-teal-600 px-3 py-2 flex items-center justify-between">
            <span className="text-white text-xs font-bold">Final Output</span>
            <CopyButton text={finalOutput} />
          </div>
          <div className="p-3 bg-teal-50">
            <p className="text-xs text-slate-800 whitespace-pre-wrap font-mono leading-relaxed">{finalOutput}</p>
          </div>
        </div>
      )}
    </div>
  )
}

export function BottomPanel({ activeTab, onTabChange, code, traceEvents, finalOutput, isExecuting, runError }: Props) {
  const open = activeTab !== null

  return (
    <div
      className={[
        'absolute bottom-0 left-0 right-0 z-20 bg-white border-t border-slate-200 shadow-2xl flex flex-col',
        'transition-transform duration-200 ease-out',
        open ? 'translate-y-0' : 'translate-y-full',
      ].join(' ')}
      style={{ height: 300 }}
    >
      {/* Tab bar */}
      <div className="flex items-center border-b border-slate-100 h-9 flex-shrink-0 px-1">
        <PanelTab
          active={activeTab === 'code'}
          icon={<Code2 size={12} />}
          label="Python Code"
          onClick={() => onTabChange(activeTab === 'code' ? null : 'code')}
        />
        <PanelTab
          active={activeTab === 'output'}
          icon={<Terminal size={12} />}
          label="Execution Trace"
          badge={traceEvents.length > 0 ? traceEvents.length : undefined}
          onClick={() => onTabChange(activeTab === 'output' ? null : 'output')}
        />
        <div className="flex-1" />
        <button
          onClick={() => onTabChange(null)}
          className="text-slate-400 hover:text-slate-700 p-1.5 rounded transition-colors mr-1"
          title="Close panel"
        >
          <X size={13} />
        </button>
      </div>

      {/* Content */}
      {activeTab === 'code'
        ? <CodeView code={code} />
        : <OutputView traceEvents={traceEvents} finalOutput={finalOutput} isExecuting={isExecuting} runError={runError} />
      }
    </div>
  )
}

function PanelTab({ active, icon, label, badge, onClick }: {
  active: boolean; icon: React.ReactNode; label: string; badge?: number; onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
        active ? 'text-blue-700 bg-blue-50' : 'text-slate-500 hover:text-slate-700'
      }`}
    >
      {icon}
      {label}
      {badge !== undefined && (
        <span className="ml-0.5 bg-blue-600 text-white text-[9px] px-1.5 py-0.5 rounded-full font-bold">
          {badge}
        </span>
      )}
    </button>
  )
}
