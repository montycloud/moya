import { Play, Trash2, ChevronDown, BookOpen, Cpu, Radio, Code2, Terminal, Upload, X, Save, Download, FolderOpen, FileJson } from 'lucide-react'
import { useState, useRef } from 'react'
import { TEMPLATES } from '../constants'
import type { Node, Edge } from '@xyflow/react'
import type { PublishedAgent, SavedFlow } from '../types'

type RunMode = 'simulation' | 'real'

const PUBLISH_CATEGORIES = ['General', 'Writing', 'Analysis', 'Engineering', 'Travel', 'Research', 'Other']

interface Props {
  onRun: () => void
  onClear: () => void
  onLoadTemplate: (t: { nodes: Node[]; edges: Edge[] }) => void
  onOpenSkillsLibrary: () => void
  onPublishAgent: (agent: PublishedAgent) => void
  isExecuting: boolean
  runMode: RunMode
  onRunModeChange: (m: RunMode) => void
  activePanel: 'code' | 'output' | null
  onTogglePanel: (p: 'code' | 'output') => void
  nodes: Node[]
  edges: Edge[]
  savedFlows: SavedFlow[]
  onSaveFlow: (name: string) => void
  onLoadSavedFlow: (flow: SavedFlow) => void
  onDeleteSavedFlow: (id: string) => void
  onExportFlow: () => void
  onImportFlow: (data: { nodes: Node[]; edges: Edge[] }) => void
}

// ── Save-as modal ─────────────────────────────────────────────────────────────

function SaveModal({ onSave, onClose }: { onSave: (name: string) => void; onClose: () => void }) {
  const [name, setName] = useState(`Flow ${new Date().toLocaleDateString()}`)

  function handleSave() {
    onSave(name)
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40">
      <div className="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-sm">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200">
          <h2 className="text-sm font-semibold text-slate-900">Save Flow</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700 transition-colors">
            <X size={15} />
          </button>
        </div>
        <div className="px-5 py-4 space-y-3">
          <div>
            <label className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wide mb-1">Name</label>
            <input
              autoFocus
              value={name}
              onChange={e => setName(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSave()}
              className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-300 text-slate-800"
            />
          </div>
        </div>
        <div className="px-5 py-4 border-t border-slate-200 flex gap-2">
          <button
            onClick={handleSave}
            disabled={!name.trim()}
            className="flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-semibold bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <Save size={13} />
            Save
          </button>
          <button onClick={onClose} className="px-4 py-2 text-sm text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors">
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Publish modal ─────────────────────────────────────────────────────────────

function PublishModal({
  nodes,
  edges,
  onPublish,
  onClose,
}: {
  nodes: Node[]
  edges: Edge[]
  onPublish: (agent: PublishedAgent) => void
  onClose: () => void
}) {
  const [name,        setName]        = useState('')
  const [description, setDescription] = useState('')
  const [category,    setCategory]    = useState('General')
  const [tags,        setTags]        = useState('')
  const [errors,      setErrors]      = useState<Record<string, string>>({})

  const agentCount = nodes.filter(n => n.type === 'agent').length
  const hasFlow    = nodes.length > 0

  function handlePublish() {
    const e: Record<string, string> = {}
    if (!name.trim())        e.name = 'Required'
    if (!description.trim()) e.description = 'Required'
    if (Object.keys(e).length) { setErrors(e); return }

    onPublish({
      id: `user-${crypto.randomUUID()}`,
      name: name.trim(),
      description: description.trim(),
      category,
      tags: tags.split(',').map(s => s.trim()).filter(Boolean),
      flow: { nodes, edges },
      publishedAt: new Date().toISOString(),
    })
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40">
      <div className="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-md flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Publish to Marketplace</h2>
            <p className="text-xs text-slate-500 mt-0.5">Share your current flow so others can discover and clone it</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700 transition-colors">
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="px-5 py-4 space-y-4 overflow-y-auto">
          {/* Flow snapshot */}
          <div className={`rounded-lg px-3 py-2.5 border text-xs ${hasFlow ? 'bg-blue-50 border-blue-200 text-blue-700' : 'bg-amber-50 border-amber-200 text-amber-700'}`}>
            {hasFlow
              ? <><strong>{nodes.length}</strong> nodes · <strong>{agentCount}</strong> agent{agentCount !== 1 ? 's' : ''} will be published</>
              : 'Your canvas is empty — add some nodes before publishing'}
          </div>

          {/* Name */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wide mb-1">Name *</label>
            <input
              value={name}
              onChange={e => { setName(e.target.value); setErrors(v => ({ ...v, name: '' })) }}
              placeholder="My Awesome Agent"
              className={`w-full text-xs border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-300 bg-white text-slate-800 placeholder-slate-300 ${errors.name ? 'border-rose-300' : 'border-slate-200'}`}
            />
            {errors.name && <p className="text-[10px] text-rose-500 mt-1">{errors.name}</p>}
          </div>

          {/* Description */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wide mb-1">Description *</label>
            <textarea
              value={description}
              onChange={e => { setDescription(e.target.value); setErrors(v => ({ ...v, description: '' })) }}
              rows={3}
              placeholder="What does this agent do? Who is it for?"
              className={`w-full text-xs border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-300 bg-white text-slate-800 placeholder-slate-300 resize-y ${errors.description ? 'border-rose-300' : 'border-slate-200'}`}
            />
            {errors.description && <p className="text-[10px] text-rose-500 mt-1">{errors.description}</p>}
          </div>

          {/* Category */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wide mb-1">Category</label>
            <select
              value={category}
              onChange={e => setCategory(e.target.value)}
              className="w-full text-xs border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-300 bg-white text-slate-800"
            >
              {PUBLISH_CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

          {/* Tags */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wide mb-1">Tags</label>
            <input
              value={tags}
              onChange={e => setTags(e.target.value)}
              placeholder="research, multi-agent, llama"
              className="w-full text-xs border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-300 bg-white text-slate-800 placeholder-slate-300"
            />
            <p className="text-[10px] text-slate-400 mt-1">Comma-separated</p>
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 py-4 border-t border-slate-200 flex gap-2">
          <button
            onClick={handlePublish}
            disabled={!hasFlow}
            className={[
              'flex-1 flex items-center justify-center gap-2 py-2 rounded-lg text-sm font-semibold transition-colors',
              hasFlow
                ? 'bg-blue-600 hover:bg-blue-700 text-white'
                : 'bg-slate-100 text-slate-400 cursor-not-allowed',
            ].join(' ')}
          >
            <Upload size={14} />
            Publish to Marketplace
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-slate-600 hover:text-slate-800 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}

// ── Toolbar ───────────────────────────────────────────────────────────────────

export function Toolbar({
  onRun, onClear, onLoadTemplate, onOpenSkillsLibrary, onPublishAgent,
  isExecuting, runMode, onRunModeChange,
  activePanel, onTogglePanel,
  nodes, edges,
  savedFlows, onSaveFlow, onLoadSavedFlow, onDeleteSavedFlow, onExportFlow, onImportFlow,
}: Props) {
  const [showTemplates,  setShowTemplates]  = useState(false)
  const [showModeMenu,   setShowModeMenu]   = useState(false)
  const [showPublish,    setShowPublish]    = useState(false)
  const [showFlowsMenu,  setShowFlowsMenu]  = useState(false)
  const [showSaveModal,  setShowSaveModal]  = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  function handleImportFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = ev => {
      try {
        const data = JSON.parse(ev.target?.result as string)
        if (Array.isArray(data.nodes) && Array.isArray(data.edges)) {
          onImportFlow(data)
          setShowFlowsMenu(false)
        } else {
          alert('Invalid flow file — expected { nodes, edges }')
        }
      } catch {
        alert('Could not parse JSON file')
      }
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
    reader.readAsText(file)
  }

  const modeLabel = runMode === 'simulation' ? 'Simulation' : 'Real'
  const modeDot   = runMode === 'simulation' ? 'bg-slate-400' : 'bg-emerald-500'

  return (
    <>
      <div className="h-11 bg-white border-b border-slate-200 flex items-center gap-1 px-3 flex-shrink-0 relative z-10">

        {/* Templates */}
        <div className="relative">
          <button
            onClick={() => { setShowTemplates(v => !v); setShowModeMenu(false) }}
            className="flex items-center gap-1.5 text-xs text-slate-600 hover:text-slate-900 px-2.5 py-1.5 rounded-lg hover:bg-slate-100 transition-colors"
          >
            Templates
            <ChevronDown size={12} className={`transition-transform ${showTemplates ? 'rotate-180' : ''}`} />
          </button>
          {showTemplates && (
            <div className="absolute top-full left-0 mt-1 bg-white rounded-xl shadow-lg border border-slate-200 py-1 w-52 z-50">
              {TEMPLATES.map(t => (
                <button
                  key={t.name}
                  onClick={() => { onLoadTemplate(t); setShowTemplates(false) }}
                  className="w-full text-left px-4 py-2 text-xs text-slate-700 hover:bg-slate-50 flex items-center gap-2"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-400 flex-shrink-0" />
                  {t.name}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Divider */}
        <div className="w-px h-5 bg-slate-200 mx-1" />

        {/* Skills Library */}
        <button
          onClick={onOpenSkillsLibrary}
          title="Open Skills Library"
          className="flex items-center gap-1.5 text-xs text-slate-600 hover:text-blue-700 px-2.5 py-1.5 rounded-lg hover:bg-blue-50 transition-colors"
        >
          <BookOpen size={13} />
          Skills
        </button>

        {/* Divider */}
        <div className="w-px h-5 bg-slate-200 mx-1" />

        {/* Publish Agent */}
        <button
          onClick={() => setShowPublish(true)}
          title="Publish your flow to the Marketplace"
          className="flex items-center gap-1.5 text-xs text-slate-600 hover:text-blue-700 px-2.5 py-1.5 rounded-lg hover:bg-blue-50 transition-colors"
        >
          <Upload size={13} />
          Publish
        </button>

        {/* Divider */}
        <div className="w-px h-5 bg-slate-200 mx-1" />

        {/* Flows dropdown */}
        <div className="relative">
          <button
            onClick={() => { setShowFlowsMenu(v => !v); setShowTemplates(false); setShowModeMenu(false) }}
            className="flex items-center gap-1.5 text-xs text-slate-600 hover:text-slate-900 px-2.5 py-1.5 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <FolderOpen size={13} />
            Flows
            <ChevronDown size={11} className={`transition-transform ${showFlowsMenu ? 'rotate-180' : ''}`} />
          </button>
          {showFlowsMenu && (
            <div className="absolute top-full left-0 mt-1 bg-white rounded-xl shadow-lg border border-slate-200 py-1 w-60 z-50">
              {/* Actions */}
              <button
                onClick={() => { setShowSaveModal(true); setShowFlowsMenu(false) }}
                className="w-full flex items-center gap-2.5 px-4 py-2 text-xs text-slate-700 hover:bg-slate-50"
              >
                <Save size={12} className="text-slate-400" />
                Save as…
              </button>
              <button
                onClick={() => { onExportFlow(); setShowFlowsMenu(false) }}
                className="w-full flex items-center gap-2.5 px-4 py-2 text-xs text-slate-700 hover:bg-slate-50"
              >
                <Download size={12} className="text-slate-400" />
                Export JSON
              </button>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="w-full flex items-center gap-2.5 px-4 py-2 text-xs text-slate-700 hover:bg-slate-50"
              >
                <FileJson size={12} className="text-slate-400" />
                Import JSON…
              </button>

              {/* Saved flows */}
              {savedFlows.length > 0 && (
                <>
                  <div className="my-1 border-t border-slate-100" />
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest px-4 py-1">Saved Flows</p>
                  {savedFlows.slice(0, 10).map(flow => (
                    <div key={flow.id} className="flex items-center gap-1 px-2 py-0.5 hover:bg-slate-50 group">
                      <button
                        onClick={() => { onLoadSavedFlow(flow); setShowFlowsMenu(false) }}
                        className="flex-1 flex items-center gap-2 px-2 py-1.5 text-xs text-slate-700 text-left min-w-0"
                      >
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-400 flex-shrink-0" />
                        <span className="truncate font-medium">{flow.name}</span>
                        <span className="text-[10px] text-slate-400 flex-shrink-0 ml-auto">
                          {new Date(flow.savedAt).toLocaleDateString()}
                        </span>
                      </button>
                      <button
                        onClick={() => onDeleteSavedFlow(flow.id)}
                        className="opacity-0 group-hover:opacity-100 text-slate-300 hover:text-rose-500 p-1 transition-all flex-shrink-0"
                        title="Delete"
                      >
                        <Trash2 size={11} />
                      </button>
                    </div>
                  ))}
                </>
              )}

              {savedFlows.length === 0 && (
                <>
                  <div className="my-1 border-t border-slate-100" />
                  <p className="text-[10px] text-slate-400 px-4 py-2">No saved flows yet. Use "Save as…" to save your work.</p>
                </>
              )}
            </div>
          )}
        </div>

        {/* Hidden file input for import */}
        <input ref={fileInputRef} type="file" accept=".json" className="hidden" onChange={handleImportFile} />

        <div className="flex-1" />

        {/* Clear */}
        <button
          onClick={onClear}
          className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-rose-600 px-2.5 py-1.5 rounded-lg hover:bg-rose-50 transition-colors"
        >
          <Trash2 size={12} />
          Clear
        </button>

        {/* Divider */}
        <div className="w-px h-5 bg-slate-200 mx-1" />

        {/* Code / Trace toggles */}
        <button
          onClick={() => onTogglePanel('code')}
          title="Toggle Python code panel"
          className={[
            'flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md border font-medium transition-all',
            activePanel === 'code'
              ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
              : 'bg-white text-slate-600 border-slate-300 hover:border-slate-400 hover:text-slate-800',
          ].join(' ')}
        >
          <Code2 size={13} />
          Code
        </button>
        <button
          onClick={() => onTogglePanel('output')}
          title="Toggle execution trace panel"
          className={[
            'flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md border font-medium transition-all',
            activePanel === 'output'
              ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
              : 'bg-white text-slate-600 border-slate-300 hover:border-slate-400 hover:text-slate-800',
          ].join(' ')}
        >
          <Terminal size={13} />
          Trace
        </button>

        {/* Divider */}
        <div className="w-px h-5 bg-slate-200 mx-1" />

        {/* Run mode selector */}
        <div className="relative">
          <button
            onClick={() => { setShowModeMenu(v => !v); setShowTemplates(false) }}
            title={runMode === 'simulation' ? 'Simulation mode — no LLM calls' : 'Real mode — calls your Ollama/OpenAI backend'}
            className="flex items-center gap-1.5 text-xs text-slate-600 hover:text-slate-900 px-2.5 py-1.5 rounded-lg hover:bg-slate-100 transition-colors border border-slate-200"
          >
            <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${modeDot}`} />
            {modeLabel}
            <ChevronDown size={11} className={`transition-transform ${showModeMenu ? 'rotate-180' : ''}`} />
          </button>
          {showModeMenu && (
            <div className="absolute top-full right-0 mt-1 bg-white rounded-xl shadow-lg border border-slate-200 py-1 w-52 z-50">
              <ModeOption
                active={runMode === 'simulation'}
                icon={<Cpu size={13} className="text-slate-500" />}
                label="Simulation"
                hint="Animates the flow locally — no backend needed"
                dot="bg-slate-400"
                onClick={() => { onRunModeChange('simulation'); setShowModeMenu(false) }}
              />
              <ModeOption
                active={runMode === 'real'}
                icon={<Radio size={13} className="text-emerald-600" />}
                label="Real"
                hint="Streams from FastAPI + Ollama backend"
                dot="bg-emerald-500"
                onClick={() => { onRunModeChange('real'); setShowModeMenu(false) }}
              />
            </div>
          )}
        </div>

        {/* Run button */}
        <button
          onClick={onRun}
          disabled={isExecuting}
          className={[
            'flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ml-1',
            isExecuting
              ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700 text-white shadow-sm hover:shadow-md',
          ].join(' ')}
        >
          {isExecuting ? (
            <>
              <div className="w-3 h-3 border-2 border-slate-300 border-t-slate-500 rounded-full animate-spin" />
              Running…
            </>
          ) : (
            <>
              <Play size={11} fill="currentColor" />
              Run
            </>
          )}
        </button>
      </div>

      {/* Publish modal */}
      {showPublish && (
        <PublishModal
          nodes={nodes}
          edges={edges}
          onPublish={agent => { onPublishAgent(agent); setShowPublish(false) }}
          onClose={() => setShowPublish(false)}
        />
      )}

      {/* Save modal */}
      {showSaveModal && (
        <SaveModal
          onSave={onSaveFlow}
          onClose={() => setShowSaveModal(false)}
        />
      )}
    </>
  )
}

function ModeOption({ active, icon, label, hint, dot, onClick }: {
  active: boolean; icon: React.ReactNode; label: string; hint: string; dot: string; onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className={`w-full text-left px-4 py-2.5 flex items-start gap-2.5 hover:bg-slate-50 transition-colors ${active ? 'bg-blue-50' : ''}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0 ${dot}`} />
      <div>
        <p className={`text-xs font-semibold ${active ? 'text-blue-700' : 'text-slate-700'}`}>{label}</p>
        <p className="text-[10px] text-slate-400 leading-snug mt-0.5">{hint}</p>
      </div>
      {icon}
    </button>
  )
}
