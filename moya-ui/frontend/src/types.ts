export interface ToolParameter {
  name: string
  type: string
  description: string
}

// How a tool is made executable.
export type ToolKind = 'python' | 'api'

// A tool defined inline on a single agent (not shared).
export interface InlineTool {
  name: string
  description: string
  parameters: ToolParameter[]
  kind: ToolKind
  code: string          // python: the function body (parameters are in scope)
  method: string        // api: GET | POST | PUT | DELETE | PATCH
  url: string           // api: endpoint URL, may contain {param} placeholders
  headers: string       // api: one "Key: Value" per line
  body: string          // api: JSON request body template ({param} substituted); empty = send params as JSON
  mockReturnValue: string  // returned in Simulation mode
}

// A reusable tool stored in the shared Tool Registry library.
export interface RegistryTool extends InlineTool {
  id: string
  createdAt: string
}

// Per-agent memory configuration (composable — any subset may be enabled).
export interface AgentMemoryConfig {
  shortTerm?: { enabled: boolean; windowSize: number }
  longTerm?:  { enabled: boolean; path: string }
}

// An MCP server connection attached to a single agent.
export interface AgentMCP {
  id: string
  name: string
  transport: 'http' | 'stdio'
  url: string
  command: string
  args: string
  apiKey: string
}

// React Flow v12 requires all node data types to extend Record<string, unknown>
export interface AgentNodeData extends Record<string, unknown> {
  label: string
  name: string
  provider: 'openai' | 'ollama' | 'bedrock' | 'azure' | 'a2a'
  model: string
  systemPrompt: string
  description: string
  tags: string[]
  // ── A2A / remote provider only ──
  endpointUrl?: string       // base URL of the remote A2A server
  timeoutSeconds?: number
  // ── Capabilities (all optional, backward-compatible) ──
  toolIds?: string[]          // ids of attached RegistryTools
  inlineTools?: InlineTool[]  // one-off tools defined on this agent
  memory?: AgentMemoryConfig
  mcpServers?: AgentMCP[]
}

export interface ToolNodeData extends Record<string, unknown> {
  label: string
  name: string
  description: string
  parameters: ToolParameter[]
  kind: ToolKind
  code: string
  method: string
  url: string
  headers: string
  body: string
  mockReturnValue: string
}

export interface SkillNodeData extends Record<string, unknown> {
  label: string
  name: string
  description: string
  promptSnippet: string
  tags: string[]
}

export interface InputNodeData extends Record<string, unknown> {
  label: string
  message: string
}

export interface OutputNodeData extends Record<string, unknown> {
  label: string
  result: string
}

export interface ParallelNodeData extends Record<string, unknown> {
  label: string
  mergeStrategy: 'concat' | 'first'
  branchCount: number
}

export interface LoopNodeData extends Record<string, unknown> {
  label: string
  stopKeyword: string
  maxIterations: number
}

export interface BranchNodeData extends Record<string, unknown> {
  label: string
  conditionKeyword: string
}

export interface ApiConfig {
  openaiKey: string
  ollamaUrl: string
  awsRegion: string
  backendUrl: string
}

export interface UserSkill {
  id: string
  name: string
  description: string
  promptSnippet: string
  tools: string[]
  createdAt: string
}

export interface PublishedAgent {
  id: string
  name: string
  description: string
  category: string
  tags: string[]
  flow: { nodes: import('@xyflow/react').Node[]; edges: import('@xyflow/react').Edge[] }
  publishedAt: string
}

export interface SavedFlow {
  id: string
  name: string
  savedAt: string
  nodes: import('@xyflow/react').Node[]
  edges: import('@xyflow/react').Edge[]
}

export interface TraceEvent {
  nodeId: string
  nodeName: string
  nodeType: string
  status: 'started' | 'completed' | 'error' | 'warning'
  input: string
  output: string
  durationMs: number
  timestamp: number
}
