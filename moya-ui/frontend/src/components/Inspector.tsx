import { X, Info } from 'lucide-react'
import type { Node } from '@xyflow/react'
import { PROVIDER_MODELS, NODE_COLORS, NODE_DESCRIPTIONS } from '../constants'
import type {
  AgentNodeData, ToolNodeData, SkillNodeData,
  InputNodeData, ParallelNodeData, LoopNodeData, BranchNodeData,
  MCPNodeData, A2ANodeData,
  ToolParameter, UserSkill,
} from '../types'

interface Props {
  node: Node | null
  onDataChange: (id: string, data: Record<string, unknown>) => void
  onClose: () => void
  userSkills: UserSkill[]
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

// ── Per-type forms ───────────────────────────────────────────────────────────

function AgentForm({ data, onChange }: { data: AgentNodeData; onChange: (f: string, v: unknown) => void }) {
  const models = PROVIDER_MODELS[data.provider] ?? []
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
          ]}
        />
      </Field>
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
  function addParam() {
    onChange('parameters', [...(data.parameters ?? []), { name: 'param', type: 'str', description: '' }])
  }
  function removeParam(i: number) {
    onChange('parameters', (data.parameters ?? []).filter((_, j) => j !== i))
  }
  function updateParam(i: number, field: keyof ToolParameter, val: string) {
    onChange('parameters', (data.parameters ?? []).map((p, j) => j === i ? { ...p, [field]: val } : p))
  }

  return (
    <div className="space-y-4">
      <Field label="Tool Name" hint="Python function name in generated code">
        <Inp value={data.name} onChange={v => onChange('name', v)} placeholder="my_tool" />
      </Field>
      <Field label="Description" hint="LLM uses this docstring to decide when to call the tool">
        <Txta value={data.description} onChange={v => onChange('description', v)} rows={2} placeholder="Does something useful." />
      </Field>
      <Field label="Simulated Return Value" hint="Returned during simulation mode">
        <Inp value={data.mockReturnValue} onChange={v => onChange('mockReturnValue', v)} placeholder="Tool result" />
      </Field>
      <div>
        <div className="flex items-center justify-between mb-2">
          <Label>Parameters</Label>
          <button onClick={addParam} className="text-[10px] text-violet-600 hover:text-violet-800 font-semibold px-1">+ Add</button>
        </div>
        <div className="space-y-2">
          {(data.parameters ?? []).map((p, i) => (
            <div key={i} className="bg-slate-50 rounded-lg p-2 space-y-1.5 relative">
              <button onClick={() => removeParam(i)} className="absolute top-2 right-2 text-slate-300 hover:text-rose-500 transition-colors">
                <X size={11} />
              </button>
              <Inp value={p.name} onChange={v => updateParam(i, 'name', v)} placeholder="name" />
              <div className="flex gap-1.5">
                <Sel
                  value={p.type || 'str'}
                  onChange={v => updateParam(i, 'type', v)}
                  options={['str', 'int', 'float', 'bool', 'list', 'dict'].map(t => ({ value: t, label: t }))}
                />
                <Inp value={p.description} onChange={v => updateParam(i, 'description', v)} placeholder="description" />
              </div>
            </div>
          ))}
          {(data.parameters ?? []).length === 0 && (
            <p className="text-[10px] text-slate-400 text-center py-2">No parameters yet</p>
          )}
        </div>
      </div>
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

function MCPForm({ data, onChange }: { data: MCPNodeData; onChange: (f: string, v: unknown) => void }) {
  return (
    <div className="space-y-4">
      <Field label="Display Label">
        <Inp value={data.label} onChange={v => onChange('label', v)} placeholder="MCP Server" />
      </Field>
      <Field label="Server Name" hint="Used to namespace tool names: name__tool_name">
        <Inp value={data.name} onChange={v => onChange('name', v)} placeholder="my_mcp" />
      </Field>
      <Field label="Transport" hint="How Moya connects to the MCP server">
        <Sel
          value={data.transport ?? 'http'}
          onChange={v => onChange('transport', v)}
          options={[
            { value: 'http',  label: 'HTTP / SSE' },
            { value: 'stdio', label: 'stdio (subprocess)' },
          ]}
        />
      </Field>
      {(data.transport ?? 'http') === 'http' ? (
        <>
          <Field label="SSE URL" hint="Full URL of the /sse endpoint">
            <Inp value={data.url} onChange={v => onChange('url', v)} placeholder="http://localhost:8080/sse" />
          </Field>
          <Field label="API Key" hint="Optional — sent as Bearer token">
            <Inp value={data.apiKey} onChange={v => onChange('apiKey', v)} placeholder="sk-..." />
          </Field>
        </>
      ) : (
        <>
          <Field label="Command" hint="Executable to run (e.g. python3)">
            <Inp value={data.command} onChange={v => onChange('command', v)} placeholder="python3" />
          </Field>
          <Field label="Arguments" hint="Space-separated args passed to the command">
            <Inp value={data.args} onChange={v => onChange('args', v)} placeholder="my_mcp_server.py" />
          </Field>
        </>
      )}
      <div className="rounded-lg bg-amber-50 p-3 text-xs text-amber-700 border border-amber-100 space-y-1">
        <p className="font-semibold text-[11px] uppercase tracking-wide text-amber-600 mb-1">Usage</p>
        <p>Connect this node to an <strong>Agent</strong> with an edge. Moya will discover all tools advertised by the server and register them so the agent can call them.</p>
      </div>
    </div>
  )
}

function A2AForm({ data, onChange }: { data: A2ANodeData; onChange: (f: string, v: unknown) => void }) {
  return (
    <div className="space-y-4">
      <Field label="Display Label">
        <Inp value={data.label} onChange={v => onChange('label', v)} placeholder="Remote Agent" />
      </Field>
      <Field label="Agent Name" hint="Used as the Python variable name">
        <Inp value={data.name} onChange={v => onChange('name', v)} placeholder="remote_agent" />
      </Field>
      <Field label="Endpoint URL" hint="Base URL of the remote A2A server">
        <Inp value={data.endpointUrl} onChange={v => onChange('endpointUrl', v)} placeholder="http://localhost:8001" />
      </Field>
      <Field label="Description" hint="What does this remote agent do?">
        <Inp value={data.description} onChange={v => onChange('description', v)} placeholder="A remote specialist agent" />
      </Field>
      <Field label="Timeout (seconds)" hint="HTTP timeout for each request">
        <Inp
          value={String(data.timeoutSeconds ?? 60)}
          onChange={v => onChange('timeoutSeconds', Math.max(5, parseInt(v) || 60))}
          type="number"
        />
      </Field>
      <div className="rounded-lg bg-rose-50 p-3 text-xs text-rose-700 border border-rose-100 space-y-1">
        <p className="font-semibold text-[11px] uppercase tracking-wide text-rose-600 mb-1">A2A Protocol</p>
        <p>The remote server must expose a <code className="font-mono">/.well-known/agent-card.json</code> endpoint. Moya uses the A2A SDK to send messages and stream responses back.</p>
      </div>
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

export function Inspector({ node, onDataChange, onClose, userSkills }: Props) {
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
      case 'agent':    return <AgentForm    data={node.data as unknown as AgentNodeData}    onChange={onChange} />
      case 'input':    return <InputForm    data={node.data as unknown as InputNodeData}    onChange={onChange} />
      case 'tool':     return <ToolForm     data={node.data as unknown as ToolNodeData}     onChange={onChange} />
      case 'skill':    return <SkillForm    data={node.data as unknown as SkillNodeData}    onChange={onChange} userSkills={userSkills} />
      case 'parallel': return <ParallelForm data={node.data as unknown as ParallelNodeData} onChange={onChange} />
      case 'loop':     return <LoopForm     data={node.data as unknown as LoopNodeData}     onChange={onChange} />
      case 'branch':   return <BranchForm   data={node.data as unknown as BranchNodeData}   onChange={onChange} />
      case 'mcp':      return <MCPForm      data={node.data as unknown as MCPNodeData}      onChange={onChange} />
      case 'a2a':      return <A2AForm      data={node.data as unknown as A2ANodeData}      onChange={onChange} />
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
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700 transition-colors rounded-md p-0.5 hover:bg-black/5">
            <X size={15} />
          </button>
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
