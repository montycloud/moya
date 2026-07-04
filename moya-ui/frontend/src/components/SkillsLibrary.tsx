import { useState } from 'react'
import { X, Plus, Trash2, Sparkles, ChevronRight } from 'lucide-react'
import type { UserSkill } from '../types'

interface Props {
  open: boolean
  onClose: () => void
  skills: UserSkill[]
  onSave: (skill: UserSkill) => void
  onDelete: (id: string) => void
}

const EMPTY_FORM = { name: '', description: '', promptSnippet: '', tools: '' }

function SkillCard({ skill, onDelete }: { skill: UserSkill; onDelete: () => void }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="border border-slate-200 rounded-xl overflow-hidden bg-white">
      <button
        onClick={() => setExpanded(v => !v)}
        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-slate-50 transition-colors"
      >
        <div className="w-7 h-7 bg-pink-100 rounded-lg flex items-center justify-center flex-shrink-0">
          <Sparkles size={13} className="text-pink-500" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-slate-800 truncate">{skill.name}</p>
          <p className="text-[11px] text-slate-400 truncate">{skill.description}</p>
        </div>
        <ChevronRight size={13} className={`text-slate-400 flex-shrink-0 transition-transform ${expanded ? 'rotate-90' : ''}`} />
      </button>

      {expanded && (
        <div className="border-t border-slate-100 px-4 py-3 bg-slate-50 space-y-3">
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-1">Prompt Snippet</p>
            <pre className="text-[11px] text-slate-700 whitespace-pre-wrap font-mono bg-white border border-slate-200 rounded-lg p-2.5 leading-relaxed max-h-32 overflow-y-auto">
              {skill.promptSnippet}
            </pre>
          </div>
          {skill.tools.length > 0 && (
            <div>
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-1">Bundled Tools</p>
              <div className="flex flex-wrap gap-1">
                {skill.tools.map(t => (
                  <span key={t} className="text-[10px] bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full font-mono">{t}</span>
                ))}
              </div>
            </div>
          )}
          <button
            onClick={onDelete}
            className="flex items-center gap-1.5 text-[11px] text-rose-500 hover:text-rose-700 font-medium transition-colors"
          >
            <Trash2 size={11} /> Delete skill
          </button>
        </div>
      )}
    </div>
  )
}

function SkillEditor({ onSave, onCancel }: { onSave: (skill: UserSkill) => void; onCancel: () => void }) {
  const [form, setForm] = useState(EMPTY_FORM)
  const [errors, setErrors] = useState<Record<string, string>>({})

  function set(field: string, value: string) {
    setForm(f => ({ ...f, [field]: value }))
    if (errors[field]) setErrors(e => ({ ...e, [field]: '' }))
  }

  function submit() {
    const e: Record<string, string> = {}
    if (!form.name.trim())         e.name = 'Required'
    if (!form.description.trim())  e.description = 'Required'
    if (!form.promptSnippet.trim()) e.promptSnippet = 'Required'
    if (Object.keys(e).length) { setErrors(e); return }

    onSave({
      id: crypto.randomUUID(),
      name: form.name.trim(),
      description: form.description.trim(),
      promptSnippet: form.promptSnippet.trim(),
      tools: form.tools.split(',').map(s => s.trim()).filter(Boolean),
      createdAt: new Date().toISOString(),
    })
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between">
        <h3 className="text-sm font-bold text-slate-800">New Skill</h3>
        <button onClick={onCancel} className="text-slate-400 hover:text-slate-700 transition-colors">
          <X size={15} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
        <FormField label="Name *" error={errors.name}>
          <input
            value={form.name}
            onChange={e => set('name', e.target.value)}
            placeholder="Travel Safety Advisor"
            className={inputCls(!!errors.name)}
          />
        </FormField>

        <FormField label="Description *" error={errors.description}>
          <input
            value={form.description}
            onChange={e => set('description', e.target.value)}
            placeholder="Adds travel safety guidance to any agent"
            className={inputCls(!!errors.description)}
          />
        </FormField>

        <FormField
          label="Prompt Snippet *"
          hint="This text is appended to the agent's system prompt. Markdown is supported."
          error={errors.promptSnippet}
        >
          <textarea
            value={form.promptSnippet}
            onChange={e => set('promptSnippet', e.target.value)}
            rows={6}
            placeholder={'## Travel Safety\nAlways include relevant safety tips for the destination.\nMention emergency contact numbers when relevant.'}
            className={`${inputCls(!!errors.promptSnippet)} resize-y font-mono text-[11px]`}
          />
        </FormField>

        <FormField
          label="Bundled Tools"
          hint="Comma-separated function names this skill bundles (optional)."
        >
          <input
            value={form.tools}
            onChange={e => set('tools', e.target.value)}
            placeholder="get_travel_advisory, get_emergency_contacts"
            className={inputCls(false)}
          />
        </FormField>
      </div>

      <div className="px-5 py-4 border-t border-slate-200 flex gap-2">
        <button
          onClick={submit}
          className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold py-2 rounded-lg transition-colors"
        >
          Save Skill
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

function FormField({ label, hint, error, children }: {
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
  return `w-full text-xs border rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-violet-300 bg-white text-slate-800 placeholder-slate-300 transition-shadow ${
    hasError ? 'border-rose-300' : 'border-slate-200'
  }`
}

// ── Main panel ───────────────────────────────────────────────────────────────

export function SkillsLibrary({ open, onClose, skills, onSave, onDelete }: Props) {
  const [creating, setCreating] = useState(false)

  function handleSave(skill: UserSkill) {
    onSave(skill)
    setCreating(false)
  }

  if (!open) return null

  return (
    <>
      {/* Backdrop */}
      <div
        className="absolute inset-0 z-20 bg-slate-900/20"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="absolute top-0 left-0 h-full w-80 z-30 bg-white border-r border-slate-200 shadow-xl flex flex-col">
        {creating ? (
          <SkillEditor onSave={handleSave} onCancel={() => setCreating(false)} />
        ) : (
          <>
            {/* Header */}
            <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between">
              <div>
                <h2 className="text-sm font-bold text-slate-800">Skills Library</h2>
                <p className="text-[10px] text-slate-400 mt-0.5">Reusable capability bundles</p>
              </div>
              <button onClick={onClose} className="text-slate-400 hover:text-slate-700 transition-colors">
                <X size={15} />
              </button>
            </div>

            {/* Skill list */}
            <div className="flex-1 overflow-y-auto px-4 py-4 space-y-2">
              {skills.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full gap-3 text-center px-4">
                  <div className="w-12 h-12 bg-pink-50 rounded-2xl flex items-center justify-center">
                    <Sparkles size={20} className="text-pink-400" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-700">No skills yet</p>
                    <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                      Create a skill to bundle a prompt snippet and tools that can be attached to any agent.
                    </p>
                  </div>
                </div>
              ) : (
                skills.map(skill => (
                  <SkillCard key={skill.id} skill={skill} onDelete={() => onDelete(skill.id)} />
                ))
              )}
            </div>

            {/* Footer */}
            <div className="px-4 py-4 border-t border-slate-200">
              <button
                onClick={() => setCreating(true)}
                className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold py-2.5 rounded-xl transition-colors shadow-sm"
              >
                <Plus size={14} />
                New Skill
              </button>
            </div>
          </>
        )}
      </div>
    </>
  )
}
