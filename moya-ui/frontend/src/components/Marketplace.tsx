import { useState, useEffect, useRef } from 'react'
import { Bot, Wrench, Sparkles, Search, Download, Play, X, Send, Square, Trash2, User } from 'lucide-react'
import { TEMPLATES } from '../constants'
import { runSimulation } from '../utils/simulator'
import { runReal, checkBackendHealth } from '../utils/runner'
import type { Node, Edge } from '@xyflow/react'
import type { TraceEvent, PublishedAgent, ApiConfig } from '../types'

interface MarketplaceListing {
  id: string
  name: string
  description: string
  tags: string[]
  category: string
  provider: string
  nodeCounts: { agents: number; tools: number; skills: number }
  flow: { nodes: Node[]; edges: Edge[] }
  isUserPublished?: boolean
  publishedAt?: string
}

// ── Flow definitions for demo agents ────────────────────────────────────────

const EDGE_STYLE = { animated: true, style: { stroke: '#94a3b8', strokeWidth: 2 } }

const TRIP_PLANNER_FLOW: { nodes: Node[]; edges: Edge[] } = {
  nodes: [
    { id: 'input-1',       type: 'input',    position: { x: 60,   y: 300 }, data: { label: 'Query',       message: 'Plan a 7-day trip to Tokyo in April' } },
    { id: 'parallel-1',   type: 'parallel', position: { x: 280,  y: 250 }, data: { label: 'Split',       mergeStrategy: 'concat', branchCount: 4 } },
    { id: 'agent-dest',   type: 'agent',    position: { x: 540,  y: 60  }, data: { label: 'Destination', name: 'destination_agent', provider: 'ollama', model: 'llama3.1', systemPrompt: 'You are a destination expert. Provide key highlights, culture, cuisine, and travel tips for the destination.', description: 'Destination info specialist', tags: ['specialist', 'travel'] } },
    { id: 'agent-itin',   type: 'agent',    position: { x: 540,  y: 210 }, data: { label: 'Itinerary',   name: 'itinerary_agent',   provider: 'ollama', model: 'llama3.1', systemPrompt: 'You are a travel itinerary expert. Create a detailed day-by-day plan with activities, restaurants, and local experiences.', description: 'Day-by-day itinerary builder', tags: ['specialist', 'travel'] } },
    { id: 'agent-budget', type: 'agent',    position: { x: 540,  y: 360 }, data: { label: 'Budget',      name: 'budget_agent',      provider: 'ollama', model: 'llama3.1', systemPrompt: 'You are a travel budget advisor. Provide itemised cost estimates for accommodation, food, transport, and activities.', description: 'Budget estimator', tags: ['specialist', 'travel'] } },
    { id: 'agent-pack',   type: 'agent',    position: { x: 540,  y: 510 }, data: { label: 'Packing',     name: 'packing_agent',     provider: 'ollama', model: 'llama3.1', systemPrompt: 'You are a travel packing expert. Create a comprehensive packing checklist based on destination, season, and trip length.', description: 'Packing list generator', tags: ['specialist', 'travel'] } },
    { id: 'agent-synth',  type: 'agent',    position: { x: 840,  y: 290 }, data: { label: 'Synthesizer', name: 'synthesizer',        provider: 'ollama', model: 'llama3.1', systemPrompt: 'You are a travel planner. Combine the destination overview, itinerary, budget, and packing list into a polished travel guide.', description: 'Combines all specialist outputs', tags: [] } },
    { id: 'output-1',     type: 'output',   position: { x: 1100, y: 300 }, data: { label: 'Travel Guide', result: '' } },
  ] as Node[],
  edges: [
    { id: 'e1', source: 'input-1',      target: 'parallel-1',                             ...EDGE_STYLE },
    { id: 'e2', source: 'parallel-1',   sourceHandle: 'branch-0', target: 'agent-dest',   ...EDGE_STYLE },
    { id: 'e3', source: 'parallel-1',   sourceHandle: 'branch-1', target: 'agent-itin',   ...EDGE_STYLE },
    { id: 'e4', source: 'parallel-1',   sourceHandle: 'branch-2', target: 'agent-budget', ...EDGE_STYLE },
    { id: 'e5', source: 'parallel-1',   sourceHandle: 'branch-3', target: 'agent-pack',   ...EDGE_STYLE },
    { id: 'e6', source: 'agent-dest',   target: 'agent-synth',                            ...EDGE_STYLE },
    { id: 'e7', source: 'agent-itin',   target: 'agent-synth',                            ...EDGE_STYLE },
    { id: 'e8', source: 'agent-budget', target: 'agent-synth',                            ...EDGE_STYLE },
    { id: 'e9', source: 'agent-pack',   target: 'agent-synth',                            ...EDGE_STYLE },
    { id: 'e10',source: 'agent-synth',  target: 'output-1',                               ...EDGE_STYLE },
  ] as Edge[],
}

const CODE_REVIEWER_FLOW: { nodes: Node[]; edges: Edge[] } = {
  nodes: [
    { id: 'input-1',   type: 'input',  position: { x: 60,  y: 200 }, data: { label: 'Code Input',    message: 'Review this Python function for issues.' } },
    { id: 'agent-syn', type: 'agent',  position: { x: 320, y: 100 }, data: { label: 'Syntax',        name: 'syntax_reviewer',   provider: 'openai', model: 'gpt-4o', systemPrompt: 'You are a syntax and correctness expert. Review code for bugs, anti-patterns, and logic errors. Cite specific issues.', description: 'Syntax & correctness reviewer', tags: ['specialist', 'code'] } },
    { id: 'agent-sec', type: 'agent',  position: { x: 320, y: 300 }, data: { label: 'Security',      name: 'security_reviewer', provider: 'openai', model: 'gpt-4o', systemPrompt: 'You are a security expert. Review code for injection vulnerabilities, unsafe inputs, and OWASP top-10 issues.', description: 'Security vulnerability reviewer', tags: ['specialist', 'security'] } },
    { id: 'tool-1',    type: 'tool',   position: { x: 160, y: 460 }, data: { label: 'Lint Check',    name: 'run_lint', description: 'Runs static analysis on the submitted code', parameters: [{ name: 'code', type: 'str', description: 'Source code to lint' }], mockReturnValue: 'No lint errors found' } },
    { id: 'agent-sum', type: 'agent',  position: { x: 620, y: 200 }, data: { label: 'Summarizer',    name: 'review_summarizer', provider: 'openai', model: 'gpt-4o', systemPrompt: 'Synthesise the syntax and security reviews into a prioritised action list with severity ratings (Critical / High / Medium / Low).', description: 'Combines reviews into a report', tags: [] } },
    { id: 'output-1',  type: 'output', position: { x: 900, y: 200 }, data: { label: 'Review Report', result: '' } },
  ] as Node[],
  edges: [
    { id: 'e1', source: 'input-1',   target: 'agent-syn', ...EDGE_STYLE },
    { id: 'e2', source: 'input-1',   target: 'agent-sec', ...EDGE_STYLE },
    { id: 'e3', source: 'tool-1',    target: 'agent-syn', ...EDGE_STYLE },
    { id: 'e4', source: 'agent-syn', target: 'agent-sum', ...EDGE_STYLE },
    { id: 'e5', source: 'agent-sec', target: 'agent-sum', ...EDGE_STYLE },
    { id: 'e6', source: 'agent-sum', target: 'output-1',  ...EDGE_STYLE },
  ] as Edge[],
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function countNodes(nodes: Node[]) {
  return {
    agents: nodes.filter(n => n.type === 'agent').length,
    tools:  nodes.filter(n => n.type === 'tool').length,
    skills: nodes.filter(n => n.type === 'skill').length,
  }
}

function getTemplateDescription(name: string): string {
  const map: Record<string, string> = {
    'Simple Chat':        'A single-agent conversational pipeline. Great starting point for any LLM-powered assistant.',
    'Research → Write':   'Two-agent pipeline: a researcher gathers facts, a writer turns them into engaging prose.',
    'Parallel Analysis':  'Runs benefits and risk analysis concurrently, then synthesises into a balanced report.',
    'Loop Refinement':    'Iteratively refines text until a completion keyword appears or the iteration limit is reached.',
  }
  return map[name] ?? name
}

function getTemplateTags(name: string): string[] {
  const map: Record<string, string[]> = {
    'Simple Chat':        ['chat', 'beginner', 'single-agent'],
    'Research → Write':   ['research', 'writing', 'pipeline'],
    'Parallel Analysis':  ['parallel', 'analysis', 'synthesis'],
    'Loop Refinement':    ['loop', 'refinement', 'iteration'],
  }
  return map[name] ?? []
}

function getTemplateCategory(name: string): string {
  const map: Record<string, string> = {
    'Simple Chat':        'General',
    'Research → Write':   'Writing',
    'Parallel Analysis':  'Analysis',
    'Loop Refinement':    'Writing',
  }
  return map[name] ?? 'General'
}

// ── Demo listings ─────────────────────────────────────────────────────────────

const DEMO_LISTINGS: MarketplaceListing[] = [
  ...TEMPLATES.map((t, i) => ({
    id: `template-${i}`,
    name: t.name,
    description: getTemplateDescription(t.name),
    tags: getTemplateTags(t.name),
    category: getTemplateCategory(t.name),
    provider: 'openai',
    nodeCounts: countNodes(t.nodes),
    flow: { nodes: t.nodes, edges: t.edges },
  })),
  {
    id: 'trip-planner',
    name: 'Trip Planner',
    description: 'Plans trips using 4 specialist agents: destination info, itinerary, budget, and packing list.',
    tags: ['travel', 'multi-agent', 'ollama'],
    category: 'Travel',
    provider: 'ollama',
    nodeCounts: countNodes(TRIP_PLANNER_FLOW.nodes),
    flow: TRIP_PLANNER_FLOW,
  },
  {
    id: 'code-reviewer',
    name: 'Code Reviewer',
    description: 'Reviews code for correctness and security using parallel specialist agents, then produces a prioritised report.',
    tags: ['code', 'multi-agent', 'engineering'],
    category: 'Engineering',
    provider: 'openai',
    nodeCounts: countNodes(CODE_REVIEWER_FLOW.nodes),
    flow: CODE_REVIEWER_FLOW,
  },
]

const CATEGORIES = ['All', 'General', 'Writing', 'Analysis', 'Engineering', 'Travel', 'My Agents']

// ── Try-it chat modal ─────────────────────────────────────────────────────────

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  agentName?: string
}

function TryItModal({ listing, onClose, apiConfig }: {
  listing: MarketplaceListing
  onClose: () => void
  apiConfig: ApiConfig
}) {
  const [messages,          setMessages]          = useState<ChatMessage[]>([])
  const [input,             setInput]             = useState('')
  const [isStreaming,       setIsStreaming]        = useState(false)
  const [liveTrace,         setLiveTrace]         = useState<TraceEvent[]>([])
  const [backendAvailable,  setBackendAvailable]  = useState<boolean | null>(null)
  const abortRef   = useRef<AbortController | null>(null)
  const traceRef   = useRef<TraceEvent[]>([])
  const bottomRef  = useRef<HTMLDivElement>(null)

  useEffect(() => {
    checkBackendHealth(apiConfig.backendUrl).then(setBackendAvailable)
  }, [apiConfig.backendUrl])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, liveTrace])

  async function handleSend() {
    if (!input.trim() || isStreaming) return

    const userMsg = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMsg }])
    setIsStreaming(true)
    setLiveTrace([])
    traceRef.current = []

    // Inject conversation history into the input node message
    const historyLines = messages.map(m =>
      `${m.role === 'user' ? 'User' : 'Assistant'}: ${m.content}`
    )
    const fullMessage = historyLines.length
      ? `${historyLines.join('\n')}\n\nUser: ${userMsg}`
      : userMsg

    const updatedNodes = listing.flow.nodes.map(n =>
      n.type === 'input' ? { ...n, data: { ...n.data, message: fullMessage } } : n
    )

    const onTrace = (event: TraceEvent) => {
      traceRef.current = [...traceRef.current, event]
      setLiveTrace(prev => [...prev, event])
    }

    try {
      let output: string

      if (backendAvailable) {
        const controller = new AbortController()
        abortRef.current = controller
        output = await runReal(
          updatedNodes, listing.flow.edges, apiConfig, onTrace, controller.signal,
        )
      } else {
        output = await runSimulation(updatedNodes, listing.flow.edges, onTrace)
      }

      const lastAgent = [...traceRef.current]
        .reverse()
        .find(e => e.status === 'completed' && e.nodeType === 'agent')

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: output,
        agentName: lastAgent?.nodeName,
      }])
    } catch (err) {
      if (!(err instanceof DOMException && err.name === 'AbortError')) {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `Error: ${err instanceof Error ? err.message : String(err)}`,
        }])
      }
    } finally {
      setIsStreaming(false)
      setLiveTrace([])
      abortRef.current = null
    }
  }

  function handleStop() { abortRef.current?.abort() }

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  const modeDot   = backendAvailable === null ? 'bg-slate-300 animate-pulse' : backendAvailable ? 'bg-emerald-500' : 'bg-slate-400'
  const modeLabel = backendAvailable === null ? 'Detecting…' : backendAvailable ? 'Real' : 'Simulation'

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50">
      <div
        className="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-2xl flex flex-col"
        style={{ height: '85vh' }}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-4 px-5 py-4 border-b border-slate-200 flex-shrink-0">
          <div>
            <div className="flex items-center gap-2 mb-0.5">
              <span className="text-xs font-medium text-slate-500">Try it</span>
              <span className="text-slate-300">·</span>
              <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${modeDot}`} />
              <span className="text-xs text-slate-400">{modeLabel}</span>
            </div>
            <h2 className="text-base font-semibold text-slate-900">{listing.name}</h2>
            <p className="text-xs text-slate-500 mt-0.5">{listing.description}</p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-700 transition-colors mt-0.5 flex-shrink-0"
          >
            <X size={16} />
          </button>
        </div>

        {/* Message thread */}
        <div className="flex-1 overflow-y-auto min-h-0 px-5 py-4 space-y-4">
          {messages.length === 0 && !isStreaming && (
            <p className="text-xs text-slate-400 bg-slate-50 rounded-lg px-3 py-2.5 border border-slate-100">
              {backendAvailable === false
                ? 'Backend not reachable — running in simulation mode. Type a message to try this agent.'
                : 'Type a message below and press Send to try this agent.'}
            </p>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              {msg.role === 'user' ? (
                <div className="max-w-[80%] bg-blue-600 text-white rounded-xl rounded-tr-sm px-4 py-2.5 text-sm leading-relaxed">
                  {msg.content}
                </div>
              ) : (
                <div className="max-w-[80%] space-y-1.5">
                  {msg.agentName && (
                    <div className="flex items-center gap-1.5 px-1">
                      <Bot size={10} className="text-slate-400" />
                      <span className="text-[10px] text-slate-400 font-medium">{msg.agentName}</span>
                    </div>
                  )}
                  <div className="bg-white border border-slate-200 rounded-xl rounded-tl-sm px-4 py-2.5 text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">
                    {msg.content}
                  </div>
                </div>
              )}
            </div>
          ))}

          {/* Live step indicators while streaming */}
          {isStreaming && (
            <div className="space-y-1">
              {liveTrace.map((e, i) => (
                <div key={i} className="flex items-center gap-2 px-1 py-0.5">
                  {e.status === 'started'
                    ? <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse flex-shrink-0" />
                    : <span className="w-1.5 h-1.5 rounded-full bg-teal-400 flex-shrink-0" />
                  }
                  <span className="text-[10px] text-slate-500 font-medium">{e.nodeName}</span>
                  {e.status === 'completed' && e.durationMs > 0 && (
                    <span className="text-[10px] text-slate-400">{e.durationMs}ms</span>
                  )}
                </div>
              ))}
              <div className="flex items-center gap-2 px-1 py-0.5">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-300 animate-bounce flex-shrink-0" />
                <span className="text-[10px] text-slate-400">Processing…</span>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input footer */}
        <div className="px-5 py-4 border-t border-slate-200 flex-shrink-0">
          <div className="flex gap-2 items-end">
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKey}
              placeholder={`Ask ${listing.name}…`}
              rows={2}
              disabled={isStreaming}
              className="flex-1 text-sm border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-300 text-slate-800 placeholder-slate-400 resize-none disabled:bg-slate-50 disabled:text-slate-400"
            />
            {isStreaming ? (
              <button
                onClick={handleStop}
                className="flex items-center gap-1.5 px-4 py-2.5 rounded-lg text-sm font-medium bg-rose-500 hover:bg-rose-600 text-white transition-all flex-shrink-0 shadow-sm"
              >
                <Square size={12} fill="currentColor" />
                Stop
              </button>
            ) : (
              <button
                onClick={handleSend}
                disabled={!input.trim()}
                className={[
                  'flex items-center gap-1.5 px-4 py-2.5 rounded-lg text-sm font-medium transition-all flex-shrink-0',
                  input.trim()
                    ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-sm'
                    : 'bg-slate-100 text-slate-400 cursor-not-allowed',
                ].join(' ')}
              >
                <Send size={13} />
                Send
              </button>
            )}
          </div>
          <p className="text-[10px] text-slate-400 mt-1.5">Enter to send · Shift+Enter for new line</p>
        </div>
      </div>
    </div>
  )
}

// ── Card sub-components ───────────────────────────────────────────────────────

function NodeCountBadge({ icon, count, color }: { icon: React.ReactNode; count: number; color: string }) {
  if (count === 0) return null
  return (
    <span className={`flex items-center gap-1 text-[10px] font-medium px-1.5 py-0.5 rounded-md ${color}`}>
      {icon}{count}
    </span>
  )
}

function ProviderBadge({ provider }: { provider: string }) {
  const styles: Record<string, string> = {
    ollama:  'bg-teal-50 text-teal-700 border border-teal-200',
    openai:  'bg-blue-50 text-blue-700 border border-blue-200',
    bedrock: 'bg-sky-50 text-sky-700 border border-sky-200',
    azure:   'bg-indigo-50 text-indigo-700 border border-indigo-200',
  }
  return (
    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-md ${styles[provider] ?? 'bg-slate-100 text-slate-600'}`}>
      {provider}
    </span>
  )
}

function AgentCard({ listing, onClone, onTryIt, onDelete }: {
  listing: MarketplaceListing
  onClone: () => void
  onTryIt: () => void
  onDelete?: () => void
}) {
  return (
    <div className={`bg-white border rounded-xl p-5 flex flex-col gap-3 hover:shadow-md transition-all ${listing.isUserPublished ? 'border-blue-200 hover:border-blue-300' : 'border-slate-200 hover:border-slate-300'}`}>
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          {listing.isUserPublished
            ? <span className="flex items-center gap-1 text-[10px] font-semibold bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded-md"><User size={9} />My Agent</span>
            : <ProviderBadge provider={listing.provider} />
          }
          <span className="text-[10px] text-slate-400">{listing.category}</span>
        </div>
        {onDelete && (
          <button
            onClick={onDelete}
            title="Remove from Marketplace"
            className="text-slate-300 hover:text-rose-500 transition-colors"
          >
            <Trash2 size={13} />
          </button>
        )}
      </div>

      <h3 className="text-sm font-semibold text-slate-900 leading-snug">{listing.name}</h3>
      <p className="text-xs text-slate-500 leading-relaxed flex-1">{listing.description}</p>

      <div className="flex items-center gap-1.5 flex-wrap">
        <NodeCountBadge icon={<Bot size={10} />}      count={listing.nodeCounts.agents} color="bg-indigo-50 text-indigo-600" />
        <NodeCountBadge icon={<Wrench size={10} />}   count={listing.nodeCounts.tools}  color="bg-sky-50 text-sky-600" />
        <NodeCountBadge icon={<Sparkles size={10} />} count={listing.nodeCounts.skills} color="bg-violet-50 text-violet-600" />
      </div>

      <div className="flex flex-wrap gap-1">
        {listing.tags.map(tag => (
          <span key={tag} className="text-[10px] bg-slate-100 text-slate-500 px-2 py-0.5 rounded-md">{tag}</span>
        ))}
      </div>

      <div className="flex gap-2 pt-2 border-t border-slate-100">
        <button
          onClick={onClone}
          className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-medium bg-blue-600 hover:bg-blue-700 text-white transition-colors shadow-sm"
        >
          <Download size={12} />
          Clone to Builder
        </button>
        <button
          onClick={onTryIt}
          className="flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium border border-slate-200 text-slate-600 hover:bg-slate-50 hover:border-slate-300 transition-colors"
        >
          <Play size={12} />
          Try it
        </button>
      </div>
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────

interface Props {
  onCloneToBuilder: (flow: { nodes: Node[]; edges: Edge[] }) => void
  publishedAgents: PublishedAgent[]
  onDeletePublishedAgent: (id: string) => void
  apiConfig: ApiConfig
}

export function Marketplace({ onCloneToBuilder, publishedAgents, onDeletePublishedAgent, apiConfig }: Props) {
  const [search,         setSearch]         = useState('')
  const [activeCategory, setActiveCategory] = useState('All')
  const [tryItListing,   setTryItListing]   = useState<MarketplaceListing | null>(null)

  const userListings: MarketplaceListing[] = publishedAgents.map(a => ({
    id: a.id,
    name: a.name,
    description: a.description,
    tags: a.tags,
    category: a.category,
    provider: 'user',
    nodeCounts: countNodes(a.flow.nodes),
    flow: a.flow,
    isUserPublished: true,
    publishedAt: a.publishedAt,
  }))

  const allListings = [...DEMO_LISTINGS, ...userListings]

  const filtered = allListings.filter(l => {
    const matchesCategory = activeCategory === 'All'
      || (activeCategory === 'My Agents' ? l.isUserPublished : l.category === activeCategory)
    const q = search.toLowerCase()
    const matchesSearch = !q ||
      l.name.toLowerCase().includes(q) ||
      l.description.toLowerCase().includes(q) ||
      l.tags.some(t => t.includes(q))
    return matchesCategory && matchesSearch
  })

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-8 py-5">
        <div className="mb-5">
          <h1 className="text-lg font-semibold text-slate-900">Agent Marketplace</h1>
          <p className="text-sm text-slate-500 mt-0.5">Discover and clone agents built with Moya · Publish yours from the Builder</p>
        </div>

        <div className="relative max-w-sm">
          <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search agents or tags…"
            className="w-full pl-9 pr-4 py-2 text-sm border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-300 bg-white text-slate-800 placeholder-slate-400"
          />
        </div>

        <div className="flex items-center gap-1.5 mt-4 flex-wrap">
          {CATEGORIES.map(cat => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={[
                'text-xs font-medium px-3 py-1 rounded-md border transition-all',
                activeCategory === cat
                  ? 'bg-blue-600 text-white border-blue-600'
                  : 'bg-white text-slate-600 border-slate-200 hover:border-slate-400 hover:text-slate-800',
              ].join(' ')}
            >
              {cat}
              {cat === 'My Agents' && publishedAgents.length > 0 && (
                <span className="ml-1.5 bg-blue-100 text-blue-700 rounded-full px-1.5 py-px text-[9px] font-bold">{publishedAgents.length}</span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Grid */}
      <div className="flex-1 overflow-y-auto px-8 py-6">
        {filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 gap-2 text-center">
            <p className="text-sm font-medium text-slate-600">
              {activeCategory === 'My Agents' ? 'You haven\'t published any agents yet' : 'No agents match your search'}
            </p>
            {activeCategory === 'My Agents' ? (
              <p className="text-xs text-slate-400">Use the <strong className="text-slate-600">Publish</strong> button in the Builder to share your first agent</p>
            ) : (
              <button
                onClick={() => { setSearch(''); setActiveCategory('All') }}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Clear filters
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filtered.map(listing => (
              <AgentCard
                key={listing.id}
                listing={listing}
                onClone={() => onCloneToBuilder(listing.flow)}
                onTryIt={() => setTryItListing(listing)}
                onDelete={listing.isUserPublished ? () => onDeletePublishedAgent(listing.id) : undefined}
              />
            ))}
          </div>
        )}
        <p className="text-center text-[11px] text-slate-400 mt-8">
          Published agents are saved to the backend. Try it uses real mode when backend is reachable.
        </p>
      </div>

      {/* Try it modal */}
      {tryItListing && (
        <TryItModal
          listing={tryItListing}
          onClose={() => setTryItListing(null)}
          apiConfig={apiConfig}
        />
      )}
    </div>
  )
}
