import { X, Code2, Globe } from 'lucide-react'
import type { ToolParameter, ToolKind } from '../types'

export interface ToolExecValue {
  parameters: ToolParameter[]
  kind: ToolKind
  code: string
  method: string
  url: string
  headers: string
  body: string
  mockReturnValue: string
}

const PARAM_TYPES = ['str', 'int', 'float', 'bool', 'list', 'dict']
const HTTP_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']

const inputCls = 'w-full text-xs border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-violet-300 bg-white text-slate-800 placeholder-slate-300 transition-shadow'

function signature(name: string, params: ToolParameter[]): string {
  const sig = params.map(p => `${p.name}: ${p.type || 'str'}`).join(', ')
  return `def ${name || 'my_tool'}(${sig}) -> str:`
}

/**
 * Renders the *executable* part of a tool definition: parameter schema, the
 * Python | API mode toggle, mode-specific fields, and the simulation return.
 * Shared by the Tool Registry library and inline agent tools so both produce
 * genuinely runnable tools.
 */
export function ToolExecEditor({ name, value, onChange }: {
  name: string
  value: ToolExecValue
  onChange: (patch: Partial<ToolExecValue>) => void
}) {
  const params = value.parameters ?? []
  const kind = value.kind ?? 'python'

  function addParam() {
    onChange({ parameters: [...params, { name: 'param', type: 'str', description: '' }] })
  }
  function removeParam(i: number) {
    onChange({ parameters: params.filter((_, j) => j !== i) })
  }
  function updateParam(i: number, field: keyof ToolParameter, val: string) {
    onChange({ parameters: params.map((p, j) => j === i ? { ...p, [field]: val } : p) })
  }

  return (
    <div className="space-y-3">
      {/* Parameters */}
      <div>
        <div className="flex items-center justify-between mb-1.5">
          <label className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Parameters</label>
          <button onClick={addParam} className="text-[10px] text-violet-600 hover:text-violet-800 font-semibold px-1">+ Add</button>
        </div>
        <div className="space-y-2">
          {params.map((p, i) => (
            <div key={i} className="bg-slate-50 rounded-lg p-2 space-y-1.5 relative">
              <button onClick={() => removeParam(i)} className="absolute top-2 right-2 text-slate-300 hover:text-rose-500 transition-colors">
                <X size={11} />
              </button>
              <input value={p.name} onChange={e => updateParam(i, 'name', e.target.value)} placeholder="name" className={inputCls} />
              <div className="flex gap-1.5">
                <select value={p.type || 'str'} onChange={e => updateParam(i, 'type', e.target.value)} className={inputCls}>
                  {PARAM_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
                <input value={p.description} onChange={e => updateParam(i, 'description', e.target.value)} placeholder="description" className={inputCls} />
              </div>
            </div>
          ))}
          {params.length === 0 && <p className="text-[10px] text-slate-400 text-center py-1">No parameters</p>}
        </div>
      </div>

      {/* Implementation type toggle */}
      <div>
        <label className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wide mb-1.5">Implementation</label>
        <div className="grid grid-cols-2 gap-1.5">
          <button
            onClick={() => onChange({ kind: 'python' })}
            className={`flex items-center justify-center gap-1.5 text-xs font-medium py-2 rounded-lg border transition-colors ${kind === 'python' ? 'bg-violet-50 border-violet-300 text-violet-700' : 'bg-white border-slate-200 text-slate-500 hover:border-slate-300'}`}
          >
            <Code2 size={13} /> Python
          </button>
          <button
            onClick={() => onChange({ kind: 'api' })}
            className={`flex items-center justify-center gap-1.5 text-xs font-medium py-2 rounded-lg border transition-colors ${kind === 'api' ? 'bg-sky-50 border-sky-300 text-sky-700' : 'bg-white border-slate-200 text-slate-500 hover:border-slate-300'}`}
          >
            <Globe size={13} /> API call
          </button>
        </div>
      </div>

      {/* Python body */}
      {kind === 'python' ? (
        <div>
          <label className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wide mb-1">Function body</label>
          <p className="text-[10px] text-slate-400 mb-1.5 leading-snug">
            Parameters are in scope. Return a string. Signature is generated for you:
          </p>
          <pre className="text-[10px] font-mono text-slate-500 bg-slate-100 rounded-t-lg px-3 py-1.5 overflow-x-auto">{signature(name, params)}</pre>
          <textarea
            value={value.code}
            onChange={e => onChange({ code: e.target.value })}
            rows={5}
            spellCheck={false}
            placeholder={'    import requests\n    return requests.get(f"https://api.example.com/{city}").text'}
            className={`${inputCls} rounded-t-none font-mono text-[11px] resize-y leading-relaxed`}
          />
        </div>
      ) : (
        <div className="space-y-2">
          <div className="flex gap-1.5">
            <select
              value={value.method || 'GET'}
              onChange={e => onChange({ method: e.target.value })}
              className={`${inputCls} w-28 flex-shrink-0`}
            >
              {HTTP_METHODS.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
            <input
              value={value.url}
              onChange={e => onChange({ url: e.target.value })}
              placeholder="https://api.example.com/weather/{city}"
              className={inputCls}
            />
          </div>
          <p className="text-[10px] text-slate-400 leading-snug">
            Use <code className="font-mono">{'{param}'}</code> in the URL to inject a parameter. For GET/DELETE the parameters are sent as the query string.
          </p>
          <div>
            <label className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wide mb-1">Headers</label>
            <textarea
              value={value.headers}
              onChange={e => onChange({ headers: e.target.value })}
              rows={2}
              spellCheck={false}
              placeholder={'Authorization: Bearer TOKEN\nContent-Type: application/json'}
              className={`${inputCls} font-mono text-[11px] resize-y`}
            />
          </div>
          {value.method !== 'GET' && value.method !== 'DELETE' && (
            <div>
              <label className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wide mb-1">Request body (JSON)</label>
              <p className="text-[10px] text-slate-400 mb-1.5 leading-snug">
                Inject parameters with <code className="font-mono">{'{param}'}</code>. Leave empty to send all parameters as a JSON object.
              </p>
              <textarea
                value={value.body}
                onChange={e => onChange({ body: e.target.value })}
                rows={4}
                spellCheck={false}
                placeholder={'{\n  "city": "{city}",\n  "units": "metric"\n}'}
                className={`${inputCls} font-mono text-[11px] resize-y leading-relaxed`}
              />
            </div>
          )}
        </div>
      )}

      {/* Simulation return */}
      <div>
        <label className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wide mb-1">Simulated return</label>
        <p className="text-[10px] text-slate-400 mb-1.5 leading-snug">Used in Simulation mode (no real call is made).</p>
        <input
          value={value.mockReturnValue}
          onChange={e => onChange({ mockReturnValue: e.target.value })}
          placeholder="Sunny, 24°C"
          className={inputCls}
        />
      </div>
    </div>
  )
}

export function emptyToolExec(): ToolExecValue {
  return { parameters: [], kind: 'python', code: '', method: 'GET', url: '', headers: '', body: '', mockReturnValue: 'Tool result' }
}
