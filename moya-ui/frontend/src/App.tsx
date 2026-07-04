import { useState, useMemo, useCallback, useEffect, useRef } from 'react'
import {
  ReactFlow,
  Background,
  BackgroundVariant,
  Controls,
  useNodesState,
  useEdgesState,
  addEdge,
  useReactFlow,
  MarkerType,
  type Connection,
  type Edge,
  type Node,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

import { InputNode }    from './components/nodes/InputNode'
import { AgentNode }    from './components/nodes/AgentNode'
import { ToolNode }     from './components/nodes/ToolNode'
import { SkillNode }    from './components/nodes/SkillNode'
import { OutputNode }   from './components/nodes/OutputNode'
import { ParallelNode } from './components/nodes/ParallelNode'
import { LoopNode }     from './components/nodes/LoopNode'
import { BranchNode }   from './components/nodes/BranchNode'
import { MCPNode }      from './components/nodes/MCPNode'
import { A2ANode }      from './components/nodes/A2ANode'

import { TopNav }        from './components/TopNav'
import { NodePalette }   from './components/NodePalette'
import { Inspector }     from './components/Inspector'
import { Toolbar }       from './components/Toolbar'
import { BottomPanel }   from './components/BottomPanel'
import { SkillsLibrary } from './components/SkillsLibrary'
import { Marketplace }   from './components/Marketplace'
import { SettingsModal } from './components/SettingsModal'

import { generateCode }  from './utils/codeGenerator'
import { runSimulation } from './utils/simulator'
import { runReal }       from './utils/runner'
import { TEMPLATE_SIMPLE, NODE_DEFAULTS } from './constants'
import type { TraceEvent, UserSkill, PublishedAgent, ApiConfig, SavedFlow } from './types'

// Must be defined OUTSIDE the component — stable reference required by React Flow v12
const nodeTypes = {
  input:    InputNode,
  agent:    AgentNode,
  tool:     ToolNode,
  skill:    SkillNode,
  output:   OutputNode,
  parallel: ParallelNode,
  loop:     LoopNode,
  branch:   BranchNode,
  mcp:      MCPNode,
  a2a:      A2ANode,
} as const

const defaultEdgeOptions = {
  animated: false,
  type: 'smoothstep',
  markerEnd: { type: MarkerType.ArrowClosed, color: '#cbd5e1' },
  style: { stroke: '#cbd5e1', strokeWidth: 1.5 },
}

const DEFAULT_API_CONFIG: ApiConfig = {
  openaiKey: '',
  ollamaUrl: 'http://localhost:11434',
  awsRegion: 'us-east-1',
  backendUrl: 'http://localhost:8000',
}

function loadSkills(): UserSkill[] {
  try { return JSON.parse(localStorage.getItem('moya_skills_library') ?? '[]') }
  catch { return [] }
}

function loadPublishedAgents(): PublishedAgent[] {
  try { return JSON.parse(localStorage.getItem('moya_published_agents') ?? '[]') }
  catch { return [] }
}

function loadRunMode(): 'simulation' | 'real' {
  return localStorage.getItem('moya_run_mode') === 'real' ? 'real' : 'simulation'
}

function loadApiConfig(): ApiConfig {
  try {
    const stored = JSON.parse(localStorage.getItem('moya_api_config') ?? '{}')
    return { ...DEFAULT_API_CONFIG, ...stored }
  } catch { return { ...DEFAULT_API_CONFIG } }
}

function loadSavedFlows(): SavedFlow[] {
  try { return JSON.parse(localStorage.getItem('moya_saved_flows') ?? '[]') }
  catch { return [] }
}

function loadCurrentFlow(): { nodes: Node[]; edges: Edge[] } {
  try {
    const stored = localStorage.getItem('moya_current_flow')
    if (stored) {
      const flow = JSON.parse(stored)
      if (Array.isArray(flow.nodes) && flow.nodes.length > 0) return flow
    }
  } catch {}
  return { nodes: TEMPLATE_SIMPLE.nodes as Node[], edges: TEMPLATE_SIMPLE.edges as Edge[] }
}

const _initialFlow = loadCurrentFlow()

export function App() {
  // ── Navigation ──────────────────────────────────────────────────────────────
  const [activeView, setActiveView] = useState<'builder' | 'marketplace'>('builder')

  // ── Flow state ──────────────────────────────────────────────────────────────
  const [nodes, setNodes, onNodesChange] = useNodesState(_initialFlow.nodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(_initialFlow.edges)
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [traceEvents,    setTraceEvents]    = useState<TraceEvent[]>([])
  const [isExecuting,    setIsExecuting]    = useState(false)
  const [finalOutput,    setFinalOutput]    = useState('')
  const [runError,       setRunError]       = useState<string | null>(null)

  // ── Panel state — null means closed ─────────────────────────────────────────
  const [activePanel, setActivePanel] = useState<'code' | 'output' | null>(null)

  // ── Other UI state ───────────────────────────────────────────────────────────
  const [runMode,           setRunMode]           = useState<'simulation' | 'real'>(loadRunMode)
  const [skillsLibraryOpen, setSkillsLibraryOpen] = useState(false)
  const [settingsOpen,      setSettingsOpen]      = useState(false)
  const [userSkills,        setUserSkills]        = useState<UserSkill[]>(loadSkills)
  const [publishedAgents,   setPublishedAgents]   = useState<PublishedAgent[]>(loadPublishedAgents)
  const [apiConfig,         setApiConfig]         = useState<ApiConfig>(loadApiConfig)
  const [savedFlows,        setSavedFlows]        = useState<SavedFlow[]>(loadSavedFlows)

  const abortRef = useRef<AbortController | null>(null)

  const { screenToFlowPosition, updateNodeData } = useReactFlow()

  const selectedNode  = useMemo(() => nodes.find(n => n.id === selectedNodeId) ?? null, [nodes, selectedNodeId])
  const generatedCode = useMemo(() => generateCode(nodes, edges), [nodes, edges])

  // ── Edge animation — highlight data flow during / after simulation ────────────
  const activeEdgeSourceIds = useMemo(() => {
    const started   = new Set<string>()
    const completed = new Set<string>()
    for (const ev of traceEvents) {
      if (ev.status === 'warning') continue
      if (ev.status === 'started')   started.add(ev.nodeId)
      if (ev.status === 'completed' || ev.status === 'error') {
        started.delete(ev.nodeId)
        completed.add(ev.nodeId)
      }
    }
    return { started, completed }
  }, [traceEvents])

  const displayEdges = useMemo(() => {
    const { started, completed } = activeEdgeSourceIds
    return edges.map(e => {
      // Simulation highlights override the baseline
      if (started.has(e.source)) return {
        ...e, type: 'smoothstep', animated: true,
        style: { stroke: '#f59e0b', strokeWidth: 3 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#f59e0b' },
      }
      if (completed.has(e.source)) return {
        ...e, type: 'smoothstep', animated: true,
        style: { stroke: '#818cf8', strokeWidth: 2.5 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#818cf8' },
      }
      // Baseline: always clean, solid, slate — overrides anything stored in localStorage
      return {
        ...e, type: 'smoothstep', animated: false,
        style: { stroke: '#cbd5e1', strokeWidth: 1.5 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#cbd5e1' },
      }
    })
  }, [edges, activeEdgeSourceIds])

  // ── Sync published agents from backend (fallback: localStorage) ──────────────
  useEffect(() => {
    const url = (apiConfig.backendUrl || 'http://localhost:8000').replace(/\/$/, '')
    fetch(`${url}/api/marketplace`, { signal: AbortSignal.timeout(3000) })
      .then(r => r.ok ? r.json() : Promise.reject())
      .then((data: Record<string, unknown>[]) => {
        setPublishedAgents(data.map(a => ({
          id:          a.id          as string,
          name:        a.name        as string,
          description: a.description as string,
          category:    a.category    as string,
          tags:        a.tags        as string[],
          flow:        a.flow        as { nodes: Node[]; edges: Edge[] },
          publishedAt: a.published_at as string,
        })))
      })
      .catch(() => { /* backend not available — keep localStorage state */ })
  }, [apiConfig.backendUrl])

  // ── Persist run mode ─────────────────────────────────────────────────────────
  function handleRunModeChange(m: 'simulation' | 'real') {
    setRunMode(m)
    localStorage.setItem('moya_run_mode', m)
  }

  function handleSaveApiConfig(cfg: ApiConfig) {
    setApiConfig(cfg)
    localStorage.setItem('moya_api_config', JSON.stringify(cfg))
  }

  // ── Auto-save current flow ───────────────────────────────────────────────────
  useEffect(() => {
    const id = setTimeout(() => {
      localStorage.setItem('moya_current_flow', JSON.stringify({ nodes, edges }))
    }, 500)
    return () => clearTimeout(id)
  }, [nodes, edges])

  // ── Named save / load / export / import ─────────────────────────────────────
  function handleSaveFlow(name: string) {
    const flow: SavedFlow = {
      id: crypto.randomUUID(),
      name: name.trim() || 'Untitled Flow',
      savedAt: new Date().toISOString(),
      nodes,
      edges,
    }
    const next = [flow, ...savedFlows].slice(0, 20)
    setSavedFlows(next)
    localStorage.setItem('moya_saved_flows', JSON.stringify(next))
  }

  function handleLoadSavedFlow(flow: SavedFlow) {
    setNodes(flow.nodes)
    setEdges(flow.edges)
    setSelectedNodeId(null)
    setTraceEvents([])
    setFinalOutput('')
    setRunError(null)
  }

  function handleDeleteSavedFlow(id: string) {
    const next = savedFlows.filter(f => f.id !== id)
    setSavedFlows(next)
    localStorage.setItem('moya_saved_flows', JSON.stringify(next))
  }

  function handleExportFlow() {
    const data = JSON.stringify({ nodes, edges }, null, 2)
    const blob = new Blob([data], { type: 'application/json' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = `moya-flow-${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  function handleImportFlow(data: { nodes: Node[]; edges: Edge[] }) {
    setNodes(data.nodes)
    setEdges(data.edges)
    setSelectedNodeId(null)
    setTraceEvents([])
    setFinalOutput('')
    setRunError(null)
  }

  // ── Toggle panel (clicking active tab closes it) ─────────────────────────────
  function handleTogglePanel(p: 'code' | 'output') {
    setActivePanel(prev => prev === p ? null : p)
  }

  // ── Escape closes inspector ──────────────────────────────────────────────────
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        setSelectedNodeId(null)
        setActivePanel(null)
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  // ── Flow callbacks ────────────────────────────────────────────────────────────
  const onConnect = useCallback(
    (connection: Connection) =>
      setEdges(eds => addEdge({ ...connection, ...defaultEdgeOptions }, eds)),
    [setEdges],
  )

  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }, [])

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    const nodeType = e.dataTransfer.getData('application/reactflow-nodetype')
    if (!nodeType) return
    const position = screenToFlowPosition({ x: e.clientX, y: e.clientY })
    const id = `${nodeType}-${Date.now()}`
    const newNode: Node = {
      id,
      type: nodeType,
      position,
      data: { ...(NODE_DEFAULTS[nodeType] ?? { label: nodeType }) },
    }
    setNodes(nds => [...nds, newNode])
    setSelectedNodeId(id)
  }, [screenToFlowPosition, setNodes])

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNodeId(node.id)
  }, [])

  const onPaneClick = useCallback(() => setSelectedNodeId(null), [])

  const handleNodeDataChange = useCallback((id: string, data: Record<string, unknown>) => {
    updateNodeData(id, data)
  }, [updateNodeData])

  // ── Run ───────────────────────────────────────────────────────────────────────
  const handleRun = useCallback(async () => {
    // Hard errors — block run
    const agentNodes = nodes.filter(n => n.type === 'agent')
    if (nodes.length === 0) {
      setRunError('Canvas is empty — drag some nodes onto the canvas first.')
      setActivePanel('output')
      return
    }
    if (agentNodes.length === 0) {
      setRunError('No Agent nodes found — add at least one Agent to run the flow.')
      setActivePanel('output')
      return
    }
    if (!nodes.find(n => n.type === 'input')) {
      setRunError('No Input node found — add an Input node to set the starting message.')
      setActivePanel('output')
      return
    }

    // Soft warnings — show but continue
    const warnings: TraceEvent[] = []
    const t = Date.now()
    if (!nodes.find(n => n.type === 'output')) {
      warnings.push({ nodeId: 'v1', nodeName: 'No Output node', nodeType: 'validation', status: 'warning', input: '', output: 'Add an Output node to capture the final result on the canvas.', durationMs: 0, timestamp: t })
    }
    const connectedIds = new Set(edges.flatMap(e => [e.source, e.target]))
    const isolated = agentNodes.filter(n => !connectedIds.has(n.id))
    if (isolated.length > 0) {
      const names = isolated.map(n => (n.data as { label?: string }).label || n.id).join(', ')
      warnings.push({ nodeId: 'v2', nodeName: 'Isolated agents', nodeType: 'validation', status: 'warning', input: '', output: `Agent(s) with no connections will be skipped: ${names}`, durationMs: 0, timestamp: t })
    }

    const controller = new AbortController()
    abortRef.current = controller

    setIsExecuting(true)
    setTraceEvents(warnings)
    setFinalOutput('')
    setRunError(null)
    setActivePanel('output')

    try {
      let output: string

      if (runMode === 'real') {
        output = await runReal(nodes, edges, apiConfig, event => {
          setTraceEvents(prev => [...prev, event])
        }, controller.signal)
      } else {
        output = await runSimulation(nodes, edges, event => {
          setTraceEvents(prev => [...prev, event])
        }, controller.signal)
      }

      setFinalOutput(output)
      const outNode = nodes.find(n => n.type === 'output')
      if (outNode) updateNodeData(outNode.id, { result: output })
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') return
      const msg = err instanceof Error ? err.message : String(err)
      setRunError(msg)
    } finally {
      setIsExecuting(false)
      abortRef.current = null
    }
  }, [nodes, edges, runMode, apiConfig, updateNodeData])

  const handleStop = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  // ── Canvas actions ────────────────────────────────────────────────────────────
  const handleClear = useCallback(() => {
    setNodes([])
    setEdges([])
    setSelectedNodeId(null)
    setTraceEvents([])
    setFinalOutput('')
    setRunError(null)
  }, [setNodes, setEdges])

  const handleLoadTemplate = useCallback((template: { nodes: Node[]; edges: Edge[] }) => {
    setNodes(template.nodes)
    setEdges(template.edges)
    setSelectedNodeId(null)
    setTraceEvents([])
    setFinalOutput('')
    setRunError(null)
  }, [setNodes, setEdges])

  // ── Marketplace clone ─────────────────────────────────────────────────────────
  const handleCloneToBuilder = useCallback((flow: { nodes: Node[]; edges: Edge[] }) => {
    setNodes(flow.nodes)
    setEdges(flow.edges)
    setSelectedNodeId(null)
    setTraceEvents([])
    setFinalOutput('')
    setRunError(null)
    setActiveView('builder')
  }, [setNodes, setEdges])

  // ── Skills Library ────────────────────────────────────────────────────────────
  function handleSaveSkill(skill: UserSkill) {
    const next = [...userSkills, skill]
    setUserSkills(next)
    localStorage.setItem('moya_skills_library', JSON.stringify(next))
  }

  function handleDeleteSkill(id: string) {
    const next = userSkills.filter(s => s.id !== id)
    setUserSkills(next)
    localStorage.setItem('moya_skills_library', JSON.stringify(next))
  }

  // ── Publish Agent ─────────────────────────────────────────────────────────────
  async function handlePublishAgent(agent: PublishedAgent) {
    const url = (apiConfig.backendUrl || 'http://localhost:8000').replace(/\/$/, '')
    try {
      const res = await fetch(`${url}/api/marketplace/publish`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(5000),
        body: JSON.stringify({
          id: agent.id,
          name: agent.name,
          description: agent.description,
          category: agent.category,
          tags: agent.tags,
          provider: 'user',
          node_count: {
            agents: agent.flow.nodes.filter(n => n.type === 'agent').length,
            tools:  agent.flow.nodes.filter(n => n.type === 'tool').length,
            skills: agent.flow.nodes.filter(n => n.type === 'skill').length,
          },
          flow: agent.flow,
        }),
      })
      if (res.ok) { setPublishedAgents(prev => [...prev, agent]); return }
    } catch {}
    // Fallback: localStorage
    setPublishedAgents(prev => {
      const next = [...prev, agent]
      localStorage.setItem('moya_published_agents', JSON.stringify(next))
      return next
    })
  }

  async function handleDeletePublishedAgent(id: string) {
    const url = (apiConfig.backendUrl || 'http://localhost:8000').replace(/\/$/, '')
    try {
      await fetch(`${url}/api/marketplace/${id}`, {
        method: 'DELETE',
        signal: AbortSignal.timeout(5000),
      })
    } catch {}
    setPublishedAgents(prev => {
      const next = prev.filter(a => a.id !== id)
      localStorage.setItem('moya_published_agents', JSON.stringify(next))
      return next
    })
  }

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-slate-50">
      <TopNav
        activeView={activeView}
        onViewChange={setActiveView}
        onOpenSettings={() => setSettingsOpen(true)}
      />

      <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
        {activeView === 'builder' ? (
          <>
            <Toolbar
              onRun={handleRun}
              onStop={handleStop}
              onClear={handleClear}
              onLoadTemplate={handleLoadTemplate}
              onOpenSkillsLibrary={() => setSkillsLibraryOpen(true)}
              onPublishAgent={handlePublishAgent}
              isExecuting={isExecuting}
              runMode={runMode}
              onRunModeChange={handleRunModeChange}
              activePanel={activePanel}
              onTogglePanel={handleTogglePanel}
              nodes={nodes}
              edges={edges}
              savedFlows={savedFlows}
              onSaveFlow={handleSaveFlow}
              onLoadSavedFlow={handleLoadSavedFlow}
              onDeleteSavedFlow={handleDeleteSavedFlow}
              onExportFlow={handleExportFlow}
              onImportFlow={handleImportFlow}
            />

            {/*
              Canvas row — takes ALL remaining height.
              `relative` here anchors both Inspector and BottomPanel overlays.
            */}
            <div className="flex-1 min-h-0 relative flex">
              {/* Skills Library left overlay */}
              <SkillsLibrary
                open={skillsLibraryOpen}
                onClose={() => setSkillsLibraryOpen(false)}
                skills={userSkills}
                onSave={handleSaveSkill}
                onDelete={handleDeleteSkill}
              />

              {/* Node palette */}
              <NodePalette />

              {/* React Flow canvas — fills all remaining space */}
              <div
                className="flex-1 relative"
                onDrop={onDrop}
                onDragOver={onDragOver}
              >
                {nodes.length === 0 && (
                  <div className="absolute inset-0 flex items-center justify-center z-10 pointer-events-none">
                    <div className="text-center select-none">
                      <p className="text-base font-medium text-slate-300 mb-1">Canvas is empty</p>
                      <p className="text-sm text-slate-400">Drag a node from the palette, or pick a Template</p>
                    </div>
                  </div>
                )}
                <ReactFlow
                  nodes={nodes}
                  edges={displayEdges}
                  nodeTypes={nodeTypes}
                  onNodesChange={onNodesChange}
                  onEdgesChange={onEdgesChange}
                  onConnect={onConnect}
                  onNodeClick={onNodeClick}
                  onPaneClick={onPaneClick}
                  defaultEdgeOptions={defaultEdgeOptions}
                  fitView
                  fitViewOptions={{ padding: 0.3 }}
                  deleteKeyCode="Delete"
                  className="bg-white"
                  proOptions={{ hideAttribution: true }}
                >
                  <Background
                    variant={BackgroundVariant.Dots}
                    gap={28}
                    size={1}
                    color="#e2e8f0"
                  />
                  <Controls className="!border-slate-200 !shadow-sm !rounded-lg overflow-hidden" />
                </ReactFlow>
              </div>

              {/* Inspector — absolute overlay, right side */}
              <Inspector
                node={selectedNode}
                onDataChange={handleNodeDataChange}
                onClose={() => setSelectedNodeId(null)}
                userSkills={userSkills}
              />

              {/* Bottom panel — absolute overlay, slides up from bottom */}
              <BottomPanel
                activeTab={activePanel}
                onTabChange={setActivePanel}
                code={generatedCode}
                traceEvents={traceEvents}
                finalOutput={finalOutput}
                isExecuting={isExecuting}
                runError={runError}
              />
            </div>
          </>
        ) : (
          <Marketplace
            onCloneToBuilder={handleCloneToBuilder}
            publishedAgents={publishedAgents}
            onDeletePublishedAgent={handleDeletePublishedAgent}
            apiConfig={apiConfig}
          />
        )}
      </div>

      {/* Footer */}
      <footer className="flex-shrink-0 bg-white border-t border-slate-100 py-2 px-6">
        <p className="text-center text-[10px] text-slate-400">
          made with ♥ by team MOYA · 2026
        </p>
      </footer>

      {/* Settings modal */}
      {settingsOpen && (
        <SettingsModal
          config={apiConfig}
          onSave={handleSaveApiConfig}
          onClose={() => setSettingsOpen(false)}
        />
      )}
    </div>
  )
}
