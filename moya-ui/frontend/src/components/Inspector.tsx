import { useState } from 'react'
import { X, Info, ChevronDown, Plus, Wrench, Brain, Plug, Trash2 } from 'lucide-react'
import type { Node } from '@xyflow/react'
import { PROVIDER_MODELS, NODE_COLORS, NODE_DESCRIPTIONS } from '../constants'
import { ToolExecEditor, emptyToolExec } from './ToolExecEditor'
import type {
  AgentNodeData, ToolNodeData, SkillNodeData,
  InputNodeData, ParallelNodeData, LoopNodeData, BranchNodeData,
  ToolParameter, UserSkill, RegistryTool, InlineTool, AgentMCP,
} from '../types'

interface Props {
  node: Node | null
  onDataChange: (id: string, data: Record<string, unknown>) => void
  onClose: () => void
  onDelete: () => void
  userSkills: UserSkill[]
  registryTools: RegistryTool[]
}

// ── Shared primitives ────────────────────────────────────────────────────────

function Label({ children }: { children: React.ReactNode }) {
  return <label className="block text-[11px] font-semibold text-slate-500 mb-1 uppercase tracking-wide">{children}</label>
}

function Inp({ value, onChange, placeholder, type = 'text' }: {
  value: string; onChange: (v: string) => void; placeholder?: string; type?: string
}) {
  return (
    <input
      type={type}
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      className="w-full text-xs border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-violet-300 bg-white text-slate-800 placeholder-slate-300 transition-shadow"
    />
  )
}

function Sel({ value, onChange, options }: {
  value: string; onChange: (v: string) => void; options: { value: string; label: string }[]
}) {
  return (
    <select
      value={value}
      onChange={e => onChange(e.target.value)}
      className="w-full text-xs border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-violet-300 bg-white text-slate-800 transition-shadow"
    >
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  )
}

function Txta({ value, onChange, rows = 4, placeholder }: {
  value: string; onChange: (v: string) => void; rows?: number; placeholder?: string
}) {
  return (
    <textarea
      value={value}
      onChange={e => onChange(e.target.value)}
      rows={rows}
      placeholder={placeholder}
      className="w-full text-xs border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-violet-300 bg-white text-slate-800 resize-y placeholder-slate-300 transition-shadow"
    />
  )
}

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div>
      <Label>{label}</Label>
      {hint && <p className="text-[10px] text-slate-400 mb-1.5 leading-snug">{hint}</p>}
      {children}
    </div>
  )
}

// Collapsible capability section (Tools / Memory / MCP) with a count badge.
function Section({ icon, title, count, children }: {
  icon: React.ReactNode; title: string; count?: number; children: React.ReactNode
}) {
  const [open, setOpen] = useState(false)
  return (
    <div className="border-t border-slate-100 pt-3">
      <button onClick={() => setOpen(v => !v)} className="w-full flex items-center gap-2 group">
        <span className="text-slate-400">{icon}</span>
        <span className="text-[11px] font-semibold text-slate-600 uppercase tracking-wide flex-1 text-left">{title}</span>
        {count ? <span className="text-[10px] font-semibold text-white bg-slate-400 rounded-full px-1.5 min-w-[16px] text-center">{count}</span> : null}
        <ChevronDown size={13} className={`text-slate-400 transition-transform ${open ? '' : '-rotate-90'}`} />
      </button>
      {open && <div className="mt-3 space-y-3">{children}</div>}
    </div>
  )
}

function Checkbox({ checked, onChange, label }: { checked: boolean; onChange: (v: boolean) => void; label: React.ReactNode }) {
  return (
    <label className="flex items-center gap-2 cursor-pointer select-none">
      <input
        type="checkbox"
        checked={checked}
        onChange={e => onChange(e.target.checked)}
        className="w-3.5 h-3.5 rounded border-slate-300 text-violet-600 focus:ring-violet-300"
      />
      <span className="text-xs text-slate-700">{label}</span>
    </label>
  )
}

// ── Per-type forms ───────────────────────────────────────────────────────────

function AgentForm({ data, onChange, registryTools }: {
  data: AgentNodeData; onChange: (f: string, v: unknown) => void; registryTools: RegistryTool[]
}) {
  const models = PROVIDER_MODELS[data.provider] ?? []

  // ── Capability state helpers ──
  const toolIds     = data.toolIds ?? []
  const inlineTools = data.inlineTools ?? []
  const mem         = data.memory ?? {}
  const mcpServers  = data.mcpServers ?? []

  const toolCount = toolIds.length + inlineTools.length
  const memCount  = (mem.shortTerm?.enabled ? 1 : 0) + (mem.longTerm?.enabled ? 1 : 0)
  const isA2A     = data.provider === 'a2a'

  function toggleTool(id: string, on: boolean) {
    onChange('toolIds', on ? [...toolIds, id] : toolIds.filter(t => t !== id))
  }
  function addInlineTool() {
    onChange('inlineTools', [...inlineTools, { name: 'my_tool', description: '', ...emptyToolExec() } as InlineTool])
  }
  function updateInlineTool(i: number, patch: Partial<InlineTool>) {
    onChange('inlineTools', inlineTools.map((t, j) => j === i ? { ...t, ...patch } : t))
  }
  function removeInlineTool(i: number) {
    onChange('inlineTools', inlineTools.filter((_, j) => j !== i))
  }
  function setShortTerm(patch: Partial<{ enabled: boolean; windowSize: number }>) {
    onChange('memory', { ...mem, shortTerm: { enabled: false, windowSize: 10, ...mem.shortTerm, ...patch } })
  }
  function setLongTerm(patch: Partial<{ enabled: boolean; path: string }>) {
    onChange('memory', { ...mem, longTerm: { enabled: false, path: './moya_memory', ...mem.longTerm, ...patch } })
  }
  function addMcp() {
    onChange('mcpServers', [...mcpServers, {
      id: crypto.randomUUID(), name: 'my_mcp', transport: 'http',
      url: 'http://localhost:8080/sse', command: 'python3', args: 'server.py', apiKey: '',
    } as AgentMCP])
  }
  function updateMcp(i: number, patch: Partial<AgentMCP>) {
    onChange('mcpServers', mcpServers.map((m, j) => j === i ? { ...m, ...patch } : m))
  }
  function removeMcp(i: number) {
    onChange('mcpServers', mcpServers.filter((_, j) => j !== i))
  }

  return (
    <div className="space-y-4">
      <Field label="Display Label">
        <Inp value={data.label} onChange={v => onChange('label', v)} placeholder="Agent label" />
      </Field>
      <Field label="Variable Name" hint="Used in generated Python code">
        <Inp value={data.name} onChange={v => onChange('name', v)} placeholder="my_agent" />
      </Field>
      <Field label="Provider">
        <Sel
          value={data.provider}
          onChange={v => { onChange('provider', v); onChange('model', PROVIDER_MODELS[v]?.[0] ?? '') }}
          options={[
            { value: 'openai',  label: 'OpenAI' },
            { value: 'ollama',  label: 'Ollama (Local)' },
            { value: 'bedrock', label: 'AWS Bedrock' },
            { value: 'azure',   label: 'Azure OpenAI' },
            { value: 'a2a',     label: 'A2A / Remote' },
          ]}
        />
      </Field>

      {isA2A ? (
        <>
          <div className="rounded-lg bg-rose-50 p-3 text-[11px] text-rose-700 border border-rose-100">
            A remote agent reached over the A2A protocol. It runs elsewhere, so model, prompt, tools and memory are configured on the remote server — not here.
          </div>
          <Field label="Endpoint URL" hint="Base URL of the remote A2A server">
            <Inp value={data.endpointUrl ?? ''} onChange={v => onChange('endpointUrl', v)} placeholder="http://localhost:8001" />
          </Field>
          <Field label="Timeout (seconds)">
            <Inp
              type="number"
              value={String(data.timeoutSeconds ?? 60)}
              onChange={v => onChange('timeoutSeconds', Math.max(5, parseInt(v) || 60))}
            />
          </Field>
        </>
      ) : (
        <>
          <Field label="Model" hint={data.provider === 'ollama' ? 'Type any model name pulled via ollama pull' : undefined}>
            {data.provider === 'ollama' ? (
              <>
                <input
                  type="text"
                  value={data.model}
                  onChange={e => onChange('model', e.target.value)}
                  list="ollama-model-suggestions"
                  placeholder="llama3.1"
                  className="w-full text-xs border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-violet-300 bg-white text-slate-800 placeholder-slate-300 transition-shadow"
                />
                <datalist id="ollama-model-suggestions">
                  {models.map(m => <option key={m} value={m} />)}
                </datalist>
              </>
            ) : (
              <Sel
                value={data.model}
                onChange={v => onChange('model', v)}
                options={models.map(m => ({ value: m, label: m }))}
              />
            )}
          </Field>
          <Field label="System Prompt" hint="Instructions that shape this agent's behaviour">
            <Txta value={data.systemPrompt} onChange={v => onChange('systemPrompt', v)} rows={5} placeholder="You are a helpful assistant." />
          </Field>
        </>
      )}

      <Field label="Description" hint="Helps the orchestrator route to this agent">
        <Inp value={data.description} onChange={v => onChange('description', v)} placeholder="What does this agent do?" />
      </Field>
      <Field label="Tags" hint="Comma-separated, e.g. specialist, travel">
        <Inp
          value={(data.tags ?? []).join(', ')}
          onChange={v => onChange('tags', v.split(',').map(s => s.trim()).filter(Boolean))}
          placeholder="specialist, coordinator"
        />
      </Field>

      {isA2A ? null : (
      <>
      {/* ── Tools ── */}
      <Section icon={<Wrench size={13} />} title="Tools" count={toolCount}>
        {registryTools.length > 0 ? (
          <div className="space-y-1.5">
            <p className="text-[10px] text-slate-400">From the Tool Registry</p>
            {registryTools.map(t => (
              <Checkbox
                key={t.id}
                checked={toolIds.includes(t.id)}
                onChange={on => toggleTool(t.id, on)}
                label={<span><span className="font-mono">{t.name}</span> <span className="text-slate-400">— {t.description}</span></span>}
              />
            ))}
          </div>
        ) : (
          <div className="text-[11px] text-slate-400 bg-slate-50 rounded-lg px-3 py-2 leading-snug">
            No registry tools yet. Open the <strong className="text-slate-600">Tool Registry</strong> (wrench in toolbar) to define reusable tools.
          </div>
        )}

        <div>
          <div className="flex items-center justify-between mb-1.5">
            <Label>Inline Tools</Label>
            <button onClick={addInlineTool} className="text-[10px] text-sky-600 hover:text-sky-800 font-semibold px-1">+ Add</button>
          </div>
          <div className="space-y-2">
            {inlineTools.map((t, i) => (
              <div key={i} className="bg-slate-50 rounded-lg p-2.5 space-y-2 relative border border-slate-100">
                <button onClick={() => removeInlineTool(i)} className="absolute top-2 right-2 text-slate-300 hover:text-rose-500 transition-colors z-10">
                  <X size={11} />
                </button>
                <Inp value={t.name} onChange={v => updateInlineTool(i, { name: v })} placeholder="tool name" />
                <Inp value={t.description} onChange={v => updateInlineTool(i, { description: v })} placeholder="what it does (the LLM reads this)" />
                <ToolExecEditor name={t.name} value={t} onChange={patch => updateInlineTool(i, patch)} />
              </div>
            ))}
            {inlineTools.length === 0 && (
              <p className="text-[10px] text-slate-400 text-center py-1">No inline tools</p>
            )}
          </div>
        </div>
      </Section>

      {/* ── Memory ── */}
      <Section icon={<Brain size={13} />} title="Memory" count={memCount}>
        <div className="rounded-lg bg-violet-50 border border-violet-100 p-2.5 text-[10px] text-violet-800 leading-relaxed">
          Memory is keyed by conversation <strong>thread</strong>. After every turn the agent
          <strong> stores</strong> the user message and its reply, then on the next turn
          <strong> reads back</strong> earlier context — so it remembers across a conversation.
          Enable either or both (they combine automatically).
        </div>
        <div className="space-y-2">
          <Checkbox
            checked={!!mem.shortTerm?.enabled}
            onChange={on => setShortTerm({ enabled: on })}
            label={<span className="font-medium">Short-term</span>}
          />
          <p className="text-[10px] text-slate-400 pl-6 -mt-1 leading-snug">
            Keeps only the last <em>N</em> messages in context (a sliding window). Fast, in-memory, forgotten when the process stops.
          </p>
          {mem.shortTerm?.enabled && (
            <div className="pl-6">
              <Label>Window size (messages kept)</Label>
              <Inp
                type="number"
                value={String(mem.shortTerm?.windowSize ?? 10)}
                onChange={v => setShortTerm({ windowSize: Math.max(1, parseInt(v) || 10) })}
              />
            </div>
          )}
          <Checkbox
            checked={!!mem.longTerm?.enabled}
            onChange={on => setLongTerm({ enabled: on })}
            label={<span className="font-medium">Long-term</span>}
          />
          <p className="text-[10px] text-slate-400 pl-6 -mt-1 leading-snug">
            Writes the full history to disk and <em>recalls</em> the most relevant past messages by keyword + recency. Survives restarts.
          </p>
          {mem.longTerm?.enabled && (
            <div className="pl-6">
              <Label>Storage folder</Label>
              <Inp
                value={mem.longTerm?.path ?? './moya_memory'}
                onChange={v => setLongTerm({ path: v })}
                placeholder="./moya_memory"
              />
            </div>
          )}
        </div>
      </Section>

      {/* ── MCP Servers ── */}
      <Section icon={<Plug size={13} />} title="MCP Servers" count={mcpServers.length}>
        <div className="flex items-center justify-between">
          <p className="text-[10px] text-slate-400 leading-snug">Each server's tools are discovered and given to this agent.</p>
          <button onClick={addMcp} className="text-[10px] text-amber-600 hover:text-amber-800 font-semibold px-1 flex-shrink-0"><Plus size={11} className="inline" /> Add</button>
        </div>
        <div className="space-y-2">
          {mcpServers.map((m, i) => (
            <div key={m.id} className="bg-slate-50 rounded-lg p-2 space-y-1.5 relative">
              <button onClick={() => removeMcp(i)} className="absolute top-2 right-2 text-slate-300 hover:text-rose-500 transition-colors">
                <X size={11} />
              </button>
              <Inp value={m.name} onChange={v => updateMcp(i, { name: v })} placeholder="server name" />
              <Sel
                value={m.transport}
                onChange={v => updateMcp(i, { transport: v as 'http' | 'stdio' })}
                options={[
                  { value: 'http',  label: 'HTTP / SSE' },
                  { value: 'stdio', label: 'stdio (subprocess)' },
                ]}
              />
              {m.transport === 'http' ? (
                <>
                  <Inp value={m.url} onChange={v => updateMcp(i, { url: v })} placeholder="http://localhost:8080/sse" />
                  <Inp value={m.apiKey} onChange={v => updateMcp(i, { apiKey: v })} placeholder="API key (optional)" />
                </>
              ) : (
                <>
                  <Inp value={m.command} onChange={v => updateMcp(i, { command: v })} placeholder="python3" />
                  <Inp value={m.args} onChange={v => updateMcp(i, { args: v })} placeholder="server.py" />
                </>
              )}
            </div>
          ))}
          {mcpServers.length === 0 && (
            <p className="text-[10px] text-slate-400 text-center py-1">No MCP servers</p>
          )}
        </div>
      </Section>
      </>
      )}
    </div>
  )
}

function InputForm({ data, onChange }: { data: InputNodeData; onChange: (f: string, v: unknown) => void }) {
  return (
    <div className="space-y-4">
      <Field label="Initial Message" hint="Passed as the first message to the pipeline">
        <Txta value={data.message} onChange={v => onChange('message', v)} rows={6} placeholder="Ask me anything…" />
      </Field>
    </div>
  )
}

function ToolForm({ data, onChange }: { data: ToolNodeData; onChange: (f: string, v: unknown) => void }) {
  return (
    <div className="space-y-4">
      <Field label="Tool Name" hint="Python function name in generated code">
        <Inp value={data.name} onChange={v => onChange('name', v)} placeholder="my_tool" />
      </Field>
      <Field label="Description" hint="LLM uses this docstring to decide when to call the tool">
        <Txta value={data.description} onChange={v => onChange('description', v)} rows={2} placeholder="Does something useful." />
      </Field>
      <ToolExecEditor
        name={data.name}
        value={{
          parameters: data.parameters ?? [],
          kind: data.kind ?? 'python',
          code: data.code ?? '',
          method: data.method ?? 'GET',
          url: data.url ?? '',
          headers: data.headers ?? '',
          body: data.body ?? '',
          mockReturnValue: data.mockReturnValue ?? '',
        }}
        onChange={patch => { for (const [k, v] of Object.entries(patch)) onChange(k, v) }}
      />
    </div>
  )
}

function SkillForm({ data, onChange, userSkills }: {
  data: SkillNodeData; onChange: (f: string, v: unknown) => void; userSkills: UserSkill[]
}) {
  function applyLibrarySkill(skillId: string) {
    const skill = userSkills.find(s => s.id === skillId)
    if (!skill) return
    onChange('name', skill.name)
    onChange('description', skill.description)
    onChange('promptSnippet', skill.promptSnippet)
    onChange('tags', skill.tools)
  }

  return (
    <div className="space-y-4">
      {userSkills.length > 0 && (
        <Field label="Load from Skills Library">
          <Sel
            value=""
            onChange={applyLibrarySkill}
            options={[
              { value: '', label: '— pick a skill —' },
              ...userSkills.map(s => ({ value: s.id, label: s.name })),
            ]}
          />
        </Field>
      )}
      {userSkills.length === 0 && (
        <div className="text-[11px] text-slate-400 bg-slate-50 rounded-lg px-3 py-2.5 leading-snug">
          No skills defined yet. Open the <strong className="text-slate-600">Skills Library</strong> (⊞ in toolbar) to create one.
        </div>
      )}
      <Field label="Skill Name">
        <Inp value={data.name} onChange={v => onChange('name', v)} placeholder="eco_travel" />
      </Field>
      <Field label="Description">
        <Inp value={data.description} onChange={v => onChange('description', v)} placeholder="What capability does this add?" />
      </Field>
      <Field label="Prompt Snippet" hint="Appended to the agent's system prompt at construction time">
        <Txta value={data.promptSnippet} onChange={v => onChange('promptSnippet', v)} rows={4} placeholder="## My Skill&#10;Always be concise." />
      </Field>
    </div>
  )
}

function ParallelForm({ data, onChange }: { data: ParallelNodeData; onChange: (f: string, v: unknown) => void }) {
  return (
    <div className="space-y-4">
      <Field label="Number of Branches" hint="Creates one source handle per branch">
        <Inp
          value={String(data.branchCount ?? 2)}
          onChange={v => onChange('branchCount', Math.max(2, Math.min(6, parseInt(v) || 2)))}
          type="number"
        />
      </Field>
      <Field label="Merge Strategy" hint="How parallel outputs are combined">
        <Sel
          value={data.mergeStrategy ?? 'concat'}
          onChange={v => onChange('mergeStrategy', v)}
          options={[
            { value: 'concat', label: 'Concatenate all' },
            { value: 'first',  label: 'First result only' },
          ]}
        />
      </Field>
    </div>
  )
}

function LoopForm({ data, onChange }: { data: LoopNodeData; onChange: (f: string, v: unknown) => void }) {
  return (
    <div className="space-y-4">
      <Field label="Stop Keyword" hint="Loop stops when this appears in the agent's output">
        <Inp value={data.stopKeyword} onChange={v => onChange('stopKeyword', v)} placeholder="DONE" />
      </Field>
      <Field label="Max Iterations" hint="Safety ceiling — loop always stops here">
        <Inp
          value={String(data.maxIterations ?? 3)}
          onChange={v => onChange('maxIterations', Math.max(1, Math.min(20, parseInt(v) || 3)))}
          type="number"
        />
      </Field>
    </div>
  )
}


function BranchForm({ data, onChange }: { data: BranchNodeData; onChange: (f: string, v: unknown) => void }) {
  return (
    <div className="space-y-4">
      <Field label="Condition Keyword" hint='Found in output (case-insensitive) → true branch, otherwise → false branch'>
        <Inp value={data.conditionKeyword} onChange={v => onChange('conditionKeyword', v)} placeholder="yes" />
      </Field>
      <div className="rounded-lg bg-slate-50 p-3 text-xs text-slate-600 space-y-1 border border-slate-100">
        <p className="font-semibold text-slate-500 text-[11px] uppercase tracking-wide mb-1.5">Routing</p>
        <p>✅ Output contains "<span className="font-mono text-violet-700">{data.conditionKeyword || 'yes'}</span>" → upper handle</p>
        <p>❌ Otherwise → lower handle</p>
      </div>
    </div>
  )
}

// ── Inspector overlay ────────────────────────────────────────────────────────

export function Inspector({ node, onDataChange, onClose, onDelete, userSkills, registryTools }: Props) {
  const open = node !== null
  const c = NODE_COLORS[node?.type ?? 'agent']
  const description = NODE_DESCRIPTIONS[node?.type ?? ''] ?? ''

  function onChange(field: string, value: unknown) {
    if (!node) return
    onDataChange(node.id, { [field]: value })
  }

  function renderForm() {
    if (!node) return null
    switch (node.type) {
      case 'agent':    return <AgentForm    data={node.data as unknown as AgentNodeData}    onChange={onChange} registryTools={registryTools} />
      case 'input':    return <InputForm    data={node.data as unknown as InputNodeData}    onChange={onChange} />
      case 'tool':     return <ToolForm     data={node.data as unknown as ToolNodeData}     onChange={onChange} />
      case 'skill':    return <SkillForm    data={node.data as unknown as SkillNodeData}    onChange={onChange} userSkills={userSkills} />
      case 'parallel': return <ParallelForm data={node.data as unknown as ParallelNodeData} onChange={onChange} />
      case 'loop':     return <LoopForm     data={node.data as unknown as LoopNodeData}     onChange={onChange} />
      case 'branch':   return <BranchForm   data={node.data as unknown as BranchNodeData}   onChange={onChange} />
      case 'output':   return <p className="text-xs text-slate-400 italic">Displays the final pipeline result. No configuration needed.</p>
      default:         return null
    }
  }

  return (
    <div
      className={[
        'absolute top-4 right-4 z-20 w-80 bg-white rounded-2xl shadow-2xl border border-slate-200 flex flex-col overflow-hidden',
        'transition-all duration-200 ease-out',
        open ? 'opacity-100 translate-x-0 pointer-events-auto' : 'opacity-0 translate-x-6 pointer-events-none',
      ].join(' ')}
      style={{ maxHeight: 'calc(100% - 2rem)' }}
    >
      {/* Coloured header */}
      {node && (
        <div className={`${c.header} border-b border-slate-100 px-4 py-3 flex items-center justify-between flex-shrink-0`}>
          <span className={`${c.headerText} font-semibold text-sm capitalize`}>{node.type} Properties</span>
          <div className="flex items-center gap-0.5">
            <button onClick={onDelete} title="Delete node (Del / Backspace)" className="text-slate-400 hover:text-rose-600 transition-colors rounded-md p-0.5 hover:bg-black/5">
              <Trash2 size={14} />
            </button>
            <button onClick={onClose} title="Close" className="text-slate-400 hover:text-slate-700 transition-colors rounded-md p-0.5 hover:bg-black/5">
              <X size={15} />
            </button>
          </div>
        </div>
      )}

      {/* Scrollable form */}
      <div className="flex-1 overflow-y-auto p-4 min-h-0">
        {renderForm()}
      </div>

      {/* Concept hint */}
      {description && (
        <div className="border-t border-slate-100 px-4 py-3 bg-slate-50 flex gap-2 flex-shrink-0">
          <Info size={13} className="text-slate-400 flex-shrink-0 mt-0.5" />
          <p className="text-[10px] text-slate-500 leading-relaxed">{description}</p>
        </div>
      )}
    </div>
  )
}
