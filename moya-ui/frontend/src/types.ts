// React Flow v12 requires all node data types to extend Record<string, unknown>
export interface AgentNodeData extends Record<string, unknown> {
  label: string
  name: string
  provider: 'openai' | 'ollama' | 'bedrock' | 'azure'
  model: string
  systemPrompt: string
  description: string
  tags: string[]
}

export interface ToolParameter {
  name: string
  type: string
  description: string
}

export interface ToolNodeData extends Record<string, unknown> {
  label: string
  name: string
  description: string
  parameters: ToolParameter[]
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
  status: 'started' | 'completed' | 'error'
  input: string
  output: string
  durationMs: number
  timestamp: number
}
