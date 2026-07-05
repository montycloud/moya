import { useState } from 'react'
import { X, Plus, Trash2, Wrench, ChevronRight, Code2, Globe } from 'lucide-react'
import type { RegistryTool } from '../types'
import { ToolExecEditor, emptyToolExec, type ToolExecValue } from './ToolExecEditor'

interface Props {
  open: boolean
  onClose: () => void
  tools: RegistryTool[]
  onSave: (tool: RegistryTool) => void
  onDelete: (id: string) => void
}

function ToolCard({ tool, onDelete }: { tool: RegistryTool; onDelete: () => void }) {
  const [expanded, setExpanded] = useState(false)
  const isApi = tool.kind === 'api'

  return (
    <div className="border border-slate-200 rounded-xl overflow-hidden bg-white">
      <button
        onClick={() => setExpanded(v => !v)}
        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-slate-50 transition-colors"
      >
        <div className="w-7 h-7 bg-sky-100 rounded-lg flex items-center justify-center flex-shrink-0">
          <Wrench size={13} className="text-sky-500" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-slate-800 truncate">{tool.name}</p>
          <p className="text-[11px] text-slate-400 truncate">{tool.description}</p>
        </div>
        <span className={`flex items-center gap-1 text-[9px] font-semibold px-1.5 py-0.5 rounded ${isApi ? 'bg-sky-100 text-sky-700' : 'bg-violet-100 text-violet-700'}`}>
          {isApi ? <Globe size={9} /> : <Code2 size={9} />}{isApi ? 'API' : 'Python'}
        </span>
        <ChevronRight size={13} className={`text-slate-400 flex-shrink-0 transition-transform ${expanded ? 'rotate-90' : ''}`} />
      </button>

      {expanded && (
        <div className="border-t border-slate-100 px-4 py-3 bg-slate-50 space-y-3">
          {tool.parameters.length > 0 && (
            <div>
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-1">Parameters</p>
              <div className="flex flex-wrap gap-1">
                {tool.parameters.map(p => (
                  <span key={p.name} className="text-[10px] bg-sky-100 text-sky-700 px-2 py-0.5 rounded-full font-mono">
                    {p.name}: {p.type}
                  </span>
                ))}
              </div>
            </div>
          )}
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-1">{isApi ? 'Endpoint' : 'Implementation'}</p>
            <pre className="text-[10px] text-slate-600 font-mono bg-white border border-slate-200 rounded-lg p-2 whitespace-pre-wrap max-h-32 overflow-y-auto">
              {isApi ? `${tool.method || 'GET'} ${tool.url || '—'}` : (tool.code || '(empty)')}
            </pre>
          </div>
          <button
            onClick={onDelete}
            className="flex items-center gap-1.5 text-[11px] text-rose-500 hover:text-rose-700 font-medium transition-colors"
          >
            <Trash2 size={11} /> Delete tool
          </button>
        </div>
      )}
    </div>
  )
}

function ToolEditor({ onSave, onCancel }: { onSave: (tool: RegistryTool) => void; onCancel: () => void }) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [exec, setExec] = useState<ToolExecValue>(emptyToolExec)
  const [errors, setErrors] = useState<Record<string, string>>({})

  function submit() {
    const e: Record<string, string> = {}
    if (!name.trim())        e.name = 'Required'
    if (!description.trim()) e.description = 'Required'
    if (Object.keys(e).length) { setErrors(e); return }

    onSave({
      id: crypto.randomUUID(),
      name: name.trim(),
      description: description.trim(),
      createdAt: new Date().toISOString(),
      ...exec,
      mockReturnValue: exec.mockReturnValue.trim() || 'Tool result',
    })
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between">
        <h3 className="text-sm font-bold text-slate-800">New Tool</h3>
        <button onClick={onCancel} className="text-slate-400 hover:text-slate-700 transition-colors">
          <X size={15} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
        <Field label="Name *" error={errors.name}>
          <input
            value={name}
            onChange={e => { setName(e.target.value); setErrors(v => ({ ...v, name: '' })) }}
            placeholder="get_weather"
            className={inputCls(!!errors.name)}
          />
        </Field>

        <Field label="Description *" hint="The LLM reads this to decide when to call the tool." error={errors.description}>
          <textarea
            value={description}
            onChange={e => { setDescription(e.target.value); setErrors(v => ({ ...v, description: '' })) }}
            rows={2}
            placeholder="Return the current weather for a given city."
            className={`${inputCls(!!errors.description)} resize-y`}
          />
        </Field>

        <ToolExecEditor name={name} value={exec} onChange={patch => setExec(v => ({ ...v, ...patch }))} />
      </div>

      <div className="px-5 py-4 border-t border-slate-200 flex gap-2">
        <button
          onClick={submit}
          className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold py-2 rounded-lg transition-colors"
        >
          Save Tool
        </button>
        <button
          onClick={onCancel}
          className="px-4 py-2 text-sm text-slate-600 hover:text-slate-800 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  )
}

function Field({ label, hint, error, children }: {
  label: string; hint?: string; error?: string; children: React.ReactNode
}) {
  return (
    <div>
      <label className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wide mb-1">{label}</label>
      {hint && <p className="text-[10px] text-slate-400 mb-1.5 leading-snug">{hint}</p>}
      {children}
      {error && <p className="text-[10px] text-rose-500 mt-1">{error}</p>}
    </div>
  )
}

function inputCls(hasError: boolean) {
  return `w-full text-xs border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-sky-300 bg-white text-slate-800 placeholder-slate-300 transition-shadow ${
    hasError ? 'border-rose-300' : 'border-slate-200'
  }`
}

export function ToolRegistryLibrary({ open, onClose, tools, onSave, onDelete }: Props) {
  const [creating, setCreating] = useState(false)

  function handleSave(tool: RegistryTool) {
    onSave(tool)
    setCreating(false)
  }

  if (!open) return null

  return (
    <>
      <div className="absolute inset-0 z-20 bg-slate-900/20" onClick={onClose} />

      <div className="absolute top-0 left-0 h-full w-80 z-30 bg-white border-r border-slate-200 shadow-xl flex flex-col">
        {creating ? (
          <ToolEditor onSave={handleSave} onCancel={() => setCreating(false)} />
        ) : (
          <>
            <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between">
              <div>
                <h2 className="text-sm font-bold text-slate-800">Tool Registry</h2>
                <p className="text-[10px] text-slate-400 mt-0.5">Reusable tools any agent can call</p>
              </div>
              <button onClick={onClose} className="text-slate-400 hover:text-slate-700 transition-colors">
                <X size={15} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto px-4 py-4 space-y-2">
              {tools.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full gap-3 text-center px-4">
                  <div className="w-12 h-12 bg-sky-50 rounded-2xl flex items-center justify-center">
                    <Wrench size={20} className="text-sky-400" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-700">No tools yet</p>
                    <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                      Define a tool once here, then attach it to any agent from the agent's inspector.
                    </p>
                  </div>
                </div>
              ) : (
                tools.map(tool => (
                  <ToolCard key={tool.id} tool={tool} onDelete={() => onDelete(tool.id)} />
                ))
              )}
            </div>

            <div className="px-4 py-4 border-t border-slate-200">
              <button
                onClick={() => setCreating(true)}
                className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold py-2.5 rounded-xl transition-colors shadow-sm"
              >
                <Plus size={14} />
                New Tool
              </button>
            </div>
          </>
        )}
      </div>
    </>
  )
}
