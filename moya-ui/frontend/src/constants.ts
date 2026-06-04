import type { Node, Edge } from '@xyflow/react'

export const PROVIDER_MODELS: Record<string, string[]> = {
  openai:  ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'],
  ollama:  ['llama3.1', 'llama3.2', 'mistral', 'qwen2.5', 'phi3', 'codellama', 'gemma3', 'gemma4'],
  bedrock: [
    'anthropic.claude-3-haiku-20240307-v1:0',
    'anthropic.claude-3-sonnet-20240229-v1:0',
    'meta.llama3-8b-instruct-v1:0',
    'amazon.titan-text-express-v1',
  ],
  azure: ['gpt-4o', 'gpt-4', 'gpt-35-turbo'],
}

export const NODE_COLORS: Record<string, { header: string; headerText: string; ring: string; badge: string; handle: string }> = {
  input:    { header: 'bg-blue-50',    headerText: 'text-blue-700',    ring: 'ring-blue-200 border-blue-300',    badge: 'bg-blue-100 text-blue-700',    handle: '!bg-blue-400' },
  agent:    { header: 'bg-indigo-50',  headerText: 'text-indigo-700',  ring: 'ring-indigo-200 border-indigo-300',badge: 'bg-indigo-100 text-indigo-700', handle: '!bg-indigo-500' },
  tool:     { header: 'bg-sky-50',     headerText: 'text-sky-700',     ring: 'ring-sky-200 border-sky-300',      badge: 'bg-sky-100 text-sky-700',      handle: '!bg-sky-400' },
  skill:    { header: 'bg-violet-50',  headerText: 'text-violet-700',  ring: 'ring-violet-200 border-violet-300',badge: 'bg-violet-100 text-violet-700', handle: '!bg-violet-400' },
  output:   { header: 'bg-teal-50',    headerText: 'text-teal-700',    ring: 'ring-teal-200 border-teal-300',    badge: 'bg-teal-100 text-teal-700',    handle: '!bg-teal-400' },
  parallel: { header: 'bg-slate-100',  headerText: 'text-slate-700',   ring: 'ring-slate-200 border-slate-300',  badge: 'bg-slate-100 text-slate-600',  handle: '!bg-slate-400' },
  loop:     { header: 'bg-blue-50',    headerText: 'text-blue-800',    ring: 'ring-blue-200 border-blue-300',    badge: 'bg-blue-100 text-blue-800',    handle: '!bg-blue-500' },
  branch:   { header: 'bg-cyan-50',    headerText: 'text-cyan-700',    ring: 'ring-cyan-200 border-cyan-300',    badge: 'bg-cyan-100 text-cyan-700',    handle: '!bg-cyan-500' },
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
  agent:    { label: 'Agent', name: 'my_agent', provider: 'openai', model: 'gpt-4o', systemPrompt: 'You are a helpful assistant.', description: '', tags: [] },
  tool:     { label: 'Tool', name: 'my_tool', description: 'Does something useful.', parameters: [], mockReturnValue: 'Tool result' },
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

export const TEMPLATES = [TEMPLATE_SIMPLE, TEMPLATE_RESEARCH_WRITE, TEMPLATE_PARALLEL, TEMPLATE_LOOP]
