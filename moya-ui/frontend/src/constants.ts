import type { Node, Edge } from '@xyflow/react'

export const PROVIDER_MODELS: Record<string, string[]> = {
  openai:  ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'],
  ollama:  ['llama3.1', 'llama3.2', 'llama3.3', 'mistral', 'mistral-nemo', 'qwen2.5', 'qwen2.5-coder', 'phi3', 'phi4', 'codellama', 'gemma3', 'gemma4', 'deepseek-r1', 'deepseek-coder-v2', 'nomic-embed-text', 'llava'],
  bedrock: [
    'anthropic.claude-3-haiku-20240307-v1:0',
    'anthropic.claude-3-sonnet-20240229-v1:0',
    'meta.llama3-8b-instruct-v1:0',
    'amazon.titan-text-express-v1',
  ],
  azure: ['gpt-4o', 'gpt-4', 'gpt-35-turbo'],
}

export const NODE_COLORS: Record<string, { header: string; headerText: string; ring: string; badge: string; handle: string; accent: string }> = {
  input:    { header: 'bg-blue-50',    headerText: 'text-blue-600',    ring: 'ring-blue-200 border-blue-300',    badge: 'bg-blue-100 text-blue-700',    handle: '!bg-blue-400',    accent: 'bg-blue-500' },
  agent:    { header: 'bg-indigo-50',  headerText: 'text-indigo-600',  ring: 'ring-indigo-200 border-indigo-300',badge: 'bg-indigo-100 text-indigo-700', handle: '!bg-indigo-500',  accent: 'bg-indigo-500' },
  tool:     { header: 'bg-sky-50',     headerText: 'text-sky-600',     ring: 'ring-sky-200 border-sky-300',      badge: 'bg-sky-100 text-sky-700',      handle: '!bg-sky-400',     accent: 'bg-sky-500' },
  skill:    { header: 'bg-violet-50',  headerText: 'text-violet-600',  ring: 'ring-violet-200 border-violet-300',badge: 'bg-violet-100 text-violet-700', handle: '!bg-violet-400',  accent: 'bg-violet-500' },
  output:   { header: 'bg-teal-50',    headerText: 'text-teal-600',    ring: 'ring-teal-200 border-teal-300',    badge: 'bg-teal-100 text-teal-700',    handle: '!bg-teal-400',    accent: 'bg-teal-500' },
  parallel: { header: 'bg-slate-100',  headerText: 'text-slate-600',   ring: 'ring-slate-200 border-slate-300',  badge: 'bg-slate-100 text-slate-600',  handle: '!bg-slate-400',   accent: 'bg-slate-400' },
  loop:     { header: 'bg-blue-50',    headerText: 'text-blue-700',    ring: 'ring-blue-200 border-blue-300',    badge: 'bg-blue-100 text-blue-800',    handle: '!bg-blue-500',    accent: 'bg-blue-600' },
  branch:   { header: 'bg-cyan-50',    headerText: 'text-cyan-600',    ring: 'ring-cyan-200 border-cyan-300',    badge: 'bg-cyan-100 text-cyan-700',    handle: '!bg-cyan-500',    accent: 'bg-cyan-500' },
  mcp:      { header: 'bg-amber-50',   headerText: 'text-amber-600',   ring: 'ring-amber-200 border-amber-300',  badge: 'bg-amber-100 text-amber-700',  handle: '!bg-amber-400',   accent: 'bg-amber-500' },
  a2a:      { header: 'bg-rose-50',    headerText: 'text-rose-600',    ring: 'ring-rose-200 border-rose-300',    badge: 'bg-rose-100 text-rose-700',    handle: '!bg-rose-400',    accent: 'bg-rose-500' },
  validation: { header: 'bg-amber-50', headerText: 'text-amber-600',   ring: 'ring-amber-200 border-amber-300',  badge: 'bg-amber-100 text-amber-700',  handle: '!bg-amber-400',   accent: 'bg-amber-500' },
}

export const NODE_DESCRIPTIONS: Record<string, string> = {
  input:    'Starting point of a flow. Holds the user message passed to the first agent.',
  agent:    'An LLM-backed agent. Configure provider, model, and system prompt. MOYA uses create_agent() to build this.',
  tool:     'A callable function an agent can invoke. MOYA auto-builds the schema from docstrings and type hints.',
  skill:    'A reusable capability bundle: a prompt snippet appended to the agent system prompt plus optional tools.',
  output:   'Terminal node. Displays the final pipeline result.',
  parallel: 'Runs multiple branches concurrently using MOYA\'s ParallelStep. Results are merged (default: concatenated).',
  loop:     'Repeats an agent step until a stop keyword appears in the output, up to a maximum number of iterations.',
  branch:   'Routes execution to one of two branches based on a keyword condition — maps to MOYA\'s BranchStep.',
}

export const NODE_DEFAULTS: Record<string, object> = {
  input:    { label: 'Input', message: 'What is artificial intelligence?' },
  agent:    { label: 'Agent', name: 'my_agent', provider: 'openai', model: 'gpt-4o', systemPrompt: 'You are a helpful assistant.', description: '', tags: [], endpointUrl: 'http://localhost:8001', timeoutSeconds: 60, toolIds: [], inlineTools: [], memory: {}, mcpServers: [] },
  tool:     { label: 'Tool', name: 'my_tool', description: 'Does something useful.', parameters: [], kind: 'python', code: '', method: 'GET', url: '', headers: '', body: '', mockReturnValue: 'Tool result' },
  skill:    { label: 'Skill', name: 'my_skill', description: '', promptSnippet: 'Always be concise.', tags: [] },
  output:   { label: 'Output', result: '' },
  parallel: { label: 'Parallel', mergeStrategy: 'concat', branchCount: 2 },
  loop:     { label: 'Loop', stopKeyword: 'DONE', maxIterations: 3 },
  branch:   { label: 'Branch', conditionKeyword: 'yes' },
}

// ─── Templates ───────────────────────────────────────────────────────────────

export const TEMPLATE_SIMPLE: { nodes: Node[]; edges: Edge[]; name: string } = {
  name: 'Simple Chat',
  nodes: [
    { id: 'input-1',  type: 'input',  position: { x: 60,  y: 180 }, data: { label: 'Input',     message: 'What is artificial intelligence?' } },
    { id: 'agent-1',  type: 'agent',  position: { x: 360, y: 120 }, data: { label: 'Assistant', name: 'assistant', provider: 'openai', model: 'gpt-4o', systemPrompt: 'You are a helpful assistant. Explain things clearly and concisely.', description: 'General assistant', tags: [] } },
    { id: 'output-1', type: 'output', position: { x: 660, y: 180 }, data: { label: 'Output',    result: '' } },
  ] as Node[],
  edges: [
    { id: 'e1', source: 'input-1', target: 'agent-1',  animated: true, style: { stroke: '#94a3b8', strokeWidth: 2 } },
    { id: 'e2', source: 'agent-1', target: 'output-1', animated: true, style: { stroke: '#94a3b8', strokeWidth: 2 } },
  ] as Edge[],
}

export const TEMPLATE_RESEARCH_WRITE: { nodes: Node[]; edges: Edge[]; name: string } = {
  name: 'Research → Write',
  nodes: [
    { id: 'input-1',  type: 'input',  position: { x: 60,  y: 220 }, data: { label: 'Input',      message: 'Explain quantum computing to a 10-year-old.' } },
    { id: 'agent-1',  type: 'agent',  position: { x: 360, y: 120 }, data: { label: 'Researcher', name: 'researcher', provider: 'openai', model: 'gpt-4o', systemPrompt: 'You are an expert researcher. Gather key facts and distill the core ideas on the given topic.', description: 'Research facts', tags: ['specialist'] } },
    { id: 'agent-2',  type: 'agent',  position: { x: 720, y: 120 }, data: { label: 'Writer',     name: 'writer',     provider: 'openai', model: 'gpt-4o', systemPrompt: 'You are a skilled writer. Transform the research into a clear, engaging explanation suitable for the stated audience.', description: 'Write explanations', tags: ['specialist'] } },
    { id: 'output-1', type: 'output', position: { x: 1030, y: 220 }, data: { label: 'Output',    result: '' } },
  ] as Node[],
  edges: [
    { id: 'e1', source: 'input-1',  target: 'agent-1',  animated: true, style: { stroke: '#94a3b8', strokeWidth: 2 } },
    { id: 'e2', source: 'agent-1',  target: 'agent-2',  animated: true, style: { stroke: '#94a3b8', strokeWidth: 2 } },
    { id: 'e3', source: 'agent-2',  target: 'output-1', animated: true, style: { stroke: '#94a3b8', strokeWidth: 2 } },
  ] as Edge[],
}

export const TEMPLATE_PARALLEL: { nodes: Node[]; edges: Edge[]; name: string } = {
  name: 'Parallel Analysis',
  nodes: [
    { id: 'input-1',    type: 'input',    position: { x: 60,  y: 270 }, data: { label: 'Input',           message: 'Analyse the impact of AI on the education system.' } },
    { id: 'parallel-1', type: 'parallel', position: { x: 340, y: 210 }, data: { label: 'Split',           mergeStrategy: 'concat', branchCount: 2 } },
    { id: 'agent-1',    type: 'agent',    position: { x: 640, y: 80  }, data: { label: 'Benefits',        name: 'benefits_analyst', provider: 'openai', model: 'gpt-4o', systemPrompt: 'Focus exclusively on the opportunities and benefits. Be specific and evidence-based.', description: 'Analyses benefits', tags: [] } },
    { id: 'agent-2',    type: 'agent',    position: { x: 640, y: 340 }, data: { label: 'Risks',           name: 'risks_analyst',    provider: 'openai', model: 'gpt-4o', systemPrompt: 'Focus exclusively on the risks and challenges. Be specific and evidence-based.', description: 'Analyses risks', tags: [] } },
    { id: 'agent-3',    type: 'agent',    position: { x: 960, y: 210 }, data: { label: 'Synthesiser',     name: 'synthesiser',      provider: 'openai', model: 'gpt-4o', systemPrompt: 'You will receive a benefits analysis and a risks analysis. Synthesise them into one balanced, structured report.', description: 'Synthesises findings', tags: [] } },
    { id: 'output-1',   type: 'output',   position: { x: 1260, y: 270 }, data: { label: 'Output',         result: '' } },
  ] as Node[],
  edges: [
    { id: 'e1', source: 'input-1',    target: 'parallel-1',                                        animated: true, style: { stroke: '#94a3b8', strokeWidth: 2 } },
    { id: 'e2', source: 'parallel-1', sourceHandle: 'branch-0', target: 'agent-1',                animated: true, style: { stroke: '#94a3b8', strokeWidth: 2 } },
    { id: 'e3', source: 'parallel-1', sourceHandle: 'branch-1', target: 'agent-2',                animated: true, style: { stroke: '#94a3b8', strokeWidth: 2 } },
    { id: 'e4', source: 'agent-1',    target: 'agent-3',                                           animated: true, style: { stroke: '#94a3b8', strokeWidth: 2 } },
    { id: 'e5', source: 'agent-2',    target: 'agent-3',                                           animated: true, style: { stroke: '#94a3b8', strokeWidth: 2 } },
    { id: 'e6', source: 'agent-3',    target: 'output-1',                                          animated: true, style: { stroke: '#94a3b8', strokeWidth: 2 } },
  ] as Edge[],
}

export const TEMPLATE_LOOP: { nodes: Node[]; edges: Edge[]; name: string } = {
  name: 'Loop Refinement',
  nodes: [
    { id: 'input-1',  type: 'input',  position: { x: 60,  y: 200 }, data: { label: 'Input',   message: 'Write a one-paragraph summary of machine learning.' } },
    { id: 'loop-1',   type: 'loop',   position: { x: 340, y: 150 }, data: { label: 'Loop',    stopKeyword: 'COMPLETE', maxIterations: 3 } },
    { id: 'agent-1',  type: 'agent',  position: { x: 640, y: 150 }, data: { label: 'Refiner', name: 'refiner', provider: 'openai', model: 'gpt-4o', systemPrompt: 'Refine the given text to be clearer and more engaging. When you are satisfied with the result, end your response with the word COMPLETE.', description: 'Iteratively refines text', tags: [] } },
    { id: 'output-1', type: 'output', position: { x: 940, y: 200 }, data: { label: 'Output',  result: '' } },
  ] as Node[],
  edges: [
    { id: 'e1', source: 'input-1', target: 'loop-1',   animated: true, style: { stroke: '#94a3b8', strokeWidth: 2 } },
    { id: 'e2', source: 'loop-1',  target: 'agent-1',  animated: true, style: { stroke: '#94a3b8', strokeWidth: 2 } },
    { id: 'e3', source: 'agent-1', target: 'output-1', animated: true, style: { stroke: '#94a3b8', strokeWidth: 2 } },
  ] as Edge[],
}

// Mirrors examples/research_assistant — 2 agents, an inline tool, and memory.
export const TEMPLATE_RESEARCH_ASSISTANT: { nodes: Node[]; edges: Edge[]; name: string } = {
  name: 'Research Assistant (tools + memory)',
  nodes: [
    { id: 'input-1', type: 'input', position: { x: 40, y: 240 }, data: { label: 'Input', message: 'What is quantum computing?' } },
    { id: 'agent-1', type: 'agent', position: { x: 340, y: 150 }, data: {
        label: 'Researcher', name: 'researcher', provider: 'openai', model: 'gpt-4o',
        systemPrompt: 'You are a meticulous researcher. Always call the search_knowledge tool to gather facts before answering, and mention what you found.',
        description: 'Gathers facts using tools', tags: ['research'],
        inlineTools: [{
          name: 'search_knowledge', description: 'Look up factual notes on a topic.',
          parameters: [{ name: 'topic', type: 'str', description: 'the subject to look up' }],
          kind: 'python',
          code: 'db = {\n    "quantum computing": "Qubits use superposition and entanglement to outperform classical bits on some problems.",\n    "classical computing": "Classical computers store data in bits that are strictly 0 or 1.",\n}\nreturn db.get(topic.lower(), "No entry for " + topic)',
          method: 'GET', url: '', headers: '', body: '', mockReturnValue: 'Qubits use superposition and entanglement.',
        }],
        memory: { shortTerm: { enabled: true, windowSize: 8 }, longTerm: { enabled: true, path: './moya_memory/research' } },
        toolIds: [], mcpServers: [],
    } },
    { id: 'agent-2', type: 'agent', position: { x: 720, y: 150 }, data: {
        label: 'Writer', name: 'writer', provider: 'openai', model: 'gpt-4o',
        systemPrompt: 'You are a clear writer. Rewrite the researcher\'s findings into a concise, friendly explanation for a non-expert.',
        description: 'Turns research into a clear answer', tags: ['writing'],
        memory: { shortTerm: { enabled: true, windowSize: 8 } },
        toolIds: [], inlineTools: [], mcpServers: [],
    } },
    { id: 'output-1', type: 'output', position: { x: 1040, y: 240 }, data: { label: 'Output', result: '' } },
  ] as Node[],
  edges: [
    { id: 'e1', source: 'input-1', target: 'agent-1' },
    { id: 'e2', source: 'agent-1', target: 'agent-2' },
    { id: 'e3', source: 'agent-2', target: 'output-1' },
  ] as Edge[],
}

// Mirrors examples/support_desk — triage routes to a specialist; tools + memory.
export const TEMPLATE_SUPPORT_DESK: { nodes: Node[]; edges: Edge[]; name: string } = {
  name: 'Support Desk (routing + tools + memory)',
  nodes: [
    { id: 'input-1', type: 'input', position: { x: 40, y: 300 }, data: { label: 'Input', message: 'Where is my order A1001?' } },
    { id: 'agent-1', type: 'agent', position: { x: 320, y: 240 }, data: {
        label: 'Triage', name: 'triage', provider: 'openai', model: 'gpt-4o',
        systemPrompt: 'Classify the customer message. If it is about shipping, tracking or delivery, reply with the word "ship". Otherwise reply with the word "bill". Reply with only that one word.',
        description: 'Routes to the right specialist', tags: ['router'],
        memory: { shortTerm: { enabled: true, windowSize: 10 } },
        toolIds: [], inlineTools: [], mcpServers: [],
    } },
    { id: 'branch-1', type: 'branch', position: { x: 620, y: 250 }, data: { label: 'Ship or bill?', conditionKeyword: 'ship' } },
    { id: 'agent-2', type: 'agent', position: { x: 900, y: 120 }, data: {
        label: 'Shipping', name: 'shipping_agent', provider: 'openai', model: 'gpt-4o',
        systemPrompt: 'You are a shipping specialist. Use lookup_order to check status and ETA. Reuse an order id from the conversation if present.',
        description: 'Delivery & tracking', tags: ['support'],
        inlineTools: [{
          name: 'lookup_order', description: 'Look up an order\'s status and ETA by id.',
          parameters: [{ name: 'order_id', type: 'str', description: 'e.g. A1001' }],
          kind: 'python',
          code: 'orders = {\n    "A1001": "shipped, ETA 2 days",\n    "A1002": "processing, ETA 5 days",\n}\nreturn orders.get(order_id.upper(), "No order found: " + order_id)',
          method: 'GET', url: '', headers: '', body: '', mockReturnValue: 'shipped, ETA 2 days',
        }],
        memory: { shortTerm: { enabled: true, windowSize: 10 }, longTerm: { enabled: true, path: './moya_memory/support' } },
        toolIds: [], mcpServers: [],
    } },
    { id: 'agent-3', type: 'agent', position: { x: 900, y: 380 }, data: {
        label: 'Billing', name: 'billing_agent', provider: 'openai', model: 'gpt-4o',
        systemPrompt: 'You are a billing specialist. Use refund_policy for refund questions. Reuse an order id from the conversation if present.',
        description: 'Refunds & charges', tags: ['support'],
        inlineTools: [{
          name: 'refund_policy', description: 'Return the store refund policy.',
          parameters: [], kind: 'python',
          code: 'return "Refunds within 30 days of delivery for unused items, processed in 5-7 business days."',
          method: 'GET', url: '', headers: '', body: '', mockReturnValue: 'Refunds within 30 days, processed in 5-7 business days.',
        }],
        memory: { shortTerm: { enabled: true, windowSize: 10 }, longTerm: { enabled: true, path: './moya_memory/support' } },
        toolIds: [], mcpServers: [],
    } },
    { id: 'output-1', type: 'output', position: { x: 1220, y: 300 }, data: { label: 'Output', result: '' } },
  ] as Node[],
  edges: [
    { id: 'e1', source: 'input-1', target: 'agent-1' },
    { id: 'e2', source: 'agent-1', target: 'branch-1' },
    { id: 'e3', source: 'branch-1', sourceHandle: 'true',  target: 'agent-2' },
    { id: 'e4', source: 'branch-1', sourceHandle: 'false', target: 'agent-3' },
    { id: 'e5', source: 'agent-2', target: 'output-1' },
    { id: 'e6', source: 'agent-3', target: 'output-1' },
  ] as Edge[],
}

export const TEMPLATES = [
  TEMPLATE_SIMPLE, TEMPLATE_RESEARCH_WRITE, TEMPLATE_PARALLEL, TEMPLATE_LOOP,
  TEMPLATE_RESEARCH_ASSISTANT, TEMPLATE_SUPPORT_DESK,
]
