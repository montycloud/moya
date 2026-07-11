import { useState, useEffect } from 'react'
import { X, CheckCircle, XCircle, Loader } from 'lucide-react'
import type { ApiConfig } from '../types'
import { checkBackendHealth } from '../utils/runner'

interface Props {
  config: ApiConfig
  onSave: (config: ApiConfig) => void
  onClose: () => void
}

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-[11px] font-semibold text-slate-500 uppercase tracking-wide mb-1">{label}</label>
      {hint && <p className="text-[10px] text-slate-400 mb-1.5 leading-snug">{hint}</p>}
      {children}
    </div>
  )
}

const inputCls = 'w-full text-xs border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-300 bg-white text-slate-800 placeholder-slate-300 font-mono'

export function SettingsModal({ config, onSave, onClose }: Props) {
  const [form, setForm] = useState<ApiConfig>({ ...config })
  const [healthStatus, setHealthStatus] = useState<'idle' | 'checking' | 'ok' | 'error'>('idle')

  function set(field: keyof ApiConfig, value: string) {
    setForm(f => ({ ...f, [field]: value }))
    if (field === 'backendUrl') setHealthStatus('idle')
  }

  async function testConnection() {
    setHealthStatus('checking')
    const ok = await checkBackendHealth(form.backendUrl)
    setHealthStatus(ok ? 'ok' : 'error')
  }

  // Auto-test on open
  useEffect(() => {
    testConnection()
  }, [])

  function handleSave() {
    onSave(form)
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40">
      <div className="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-md flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Settings</h2>
            <p className="text-xs text-slate-500 mt-0.5">Configure API keys and backend connection</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700 transition-colors">
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="px-5 py-4 space-y-5 overflow-y-auto">

          {/* Backend */}
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">Backend</p>
            <div className="space-y-3">
              <Field label="Backend URL" hint="URL of the running FastAPI server">
                <div className="flex gap-2">
                  <input
                    value={form.backendUrl}
                    onChange={e => set('backendUrl', e.target.value)}
                    placeholder="http://localhost:8000"
                    className={inputCls}
                  />
                  <button
                    onClick={testConnection}
                    disabled={healthStatus === 'checking'}
                    className="flex-shrink-0 text-xs px-3 py-2 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 transition-colors disabled:opacity-50"
                  >
                    {healthStatus === 'checking' ? <Loader size={12} className="animate-spin" /> : 'Test'}
                  </button>
                </div>
                <div className="mt-1.5 flex items-center gap-1.5 text-[11px]">
                  {healthStatus === 'idle' && <span className="text-slate-400">Click Test to verify connection</span>}
                  {healthStatus === 'checking' && <span className="text-slate-400">Connecting…</span>}
                  {healthStatus === 'ok' && <><CheckCircle size={12} className="text-teal-500" /><span className="text-teal-600 font-medium">Backend reachable — Real mode ready</span></>}
                  {healthStatus === 'error' && <><XCircle size={12} className="text-rose-500" /><span className="text-rose-600">Cannot reach backend. Start the server first.</span></>}
                </div>
              </Field>
            </div>
            {healthStatus === 'error' && (
              <div className="mt-3 bg-slate-50 rounded-lg border border-slate-200 px-3 py-2.5 text-[11px] text-slate-600 space-y-1 font-mono">
                <p className="font-sans font-semibold text-slate-500 text-[10px] uppercase tracking-wide mb-1.5">Start the server</p>
                <p>cd moya-ui/backend</p>
                <p>pip install -r requirements.txt</p>
                <p>python main.py</p>
              </div>
            )}
          </div>

          <div className="border-t border-slate-100" />

          {/* OpenAI */}
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">OpenAI</p>
            <Field label="API Key" hint="Required for agents using openai provider">
              <input
                type="password"
                value={form.openaiKey}
                onChange={e => set('openaiKey', e.target.value)}
                placeholder="sk-…"
                className={inputCls}
              />
            </Field>
          </div>

          <div className="border-t border-slate-100" />

          {/* Ollama */}
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">Ollama (Local)</p>
            <Field label="Ollama URL" hint="Ollama server address — default is localhost:11434">
              <input
                value={form.ollamaUrl}
                onChange={e => set('ollamaUrl', e.target.value)}
                placeholder="http://localhost:11434"
                className={inputCls}
              />
            </Field>
          </div>

          <div className="border-t border-slate-100" />

          {/* AWS */}
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">AWS Bedrock</p>
            <Field label="AWS Region" hint="Region for Bedrock API calls">
              <input
                value={form.awsRegion}
                onChange={e => set('awsRegion', e.target.value)}
                placeholder="us-east-1"
                className={inputCls}
              />
            </Field>
          </div>
        </div>

        {/* Footer */}
        <div className="px-5 py-4 border-t border-slate-200 flex gap-2">
          <button
            onClick={handleSave}
            className="flex-1 py-2 rounded-lg text-sm font-semibold bg-blue-600 hover:bg-blue-700 text-white transition-colors"
          >
            Save Settings
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
