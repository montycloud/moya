/**
 * Real-mode runner: POSTs the flow to the FastAPI backend and streams
 * SSE trace events back. Falls back gracefully on network errors.
 */
import type { Node, Edge } from '@xyflow/react'
import type { TraceEvent, ApiConfig } from '../types'

export async function runReal(
  nodes: Node[],
  edges: Edge[],
  apiConfig: ApiConfig,
  onTrace: (event: TraceEvent) => void,
  signal?: AbortSignal,
): Promise<string> {
  const backendUrl = (apiConfig.backendUrl || 'http://localhost:8000').replace(/\/$/, '')
  const nodeMap    = new Map(nodes.map(n => [n.id, n]))
  const startTimes = new Map<string, number>()

  const response = await fetch(`${backendUrl}/api/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    signal,
    body: JSON.stringify({
      nodes: nodes.map(n => ({ id: n.id, type: n.type, data: n.data, position: n.position })),
      edges: edges.map(e => ({
        id: e.id,
        source: e.source,
        target: e.target,
        sourceHandle: e.sourceHandle ?? null,
        targetHandle: e.targetHandle ?? null,
      })),
      api_config: {
        openaiKey: apiConfig.openaiKey ?? '',
        ollamaUrl: apiConfig.ollamaUrl ?? 'http://localhost:11434',
        awsRegion: apiConfig.awsRegion ?? 'us-east-1',
        backendUrl,
      },
    }),
  })

  if (!response.ok || !response.body) {
    const text = await response.text().catch(() => response.statusText)
    throw new Error(`Backend error ${response.status}: ${text}`)
  }

  return new Promise<string>((resolve, reject) => {
    const reader  = response.body!.getReader()
    const decoder = new TextDecoder()
    let buffer      = ''
    let finalOutput = ''

    // Abort: close the reader so the async read loop exits
    signal?.addEventListener('abort', () => {
      reader.cancel().catch(() => {})
      reject(new DOMException('Run stopped', 'AbortError'))
    }, { once: true })

    function processLine(line: string) {
      if (!line.startsWith('data: ')) return
      const raw = line.slice(6).trim()
      if (!raw) return

      let msg: Record<string, unknown>
      try { msg = JSON.parse(raw) } catch { return }

      if (msg.type === 'trace') {
        const node     = nodeMap.get(msg.nodeId as string)
        const nodeType = node?.type ?? 'agent'
        const ts       = (msg.timestamp as number) || Date.now()

        if (msg.status === 'started') {
          startTimes.set(msg.nodeId as string, ts)
          onTrace({
            nodeId:    msg.nodeId   as string,
            nodeName:  msg.nodeName as string,
            nodeType,
            status:    'started',
            input:     '',
            output:    '',
            durationMs: 0,
            timestamp:  ts,
          })
        } else {
          const t0 = startTimes.get(msg.nodeId as string) ?? ts
          onTrace({
            nodeId:    msg.nodeId   as string,
            nodeName:  msg.nodeName as string,
            nodeType,
            status:    msg.status === 'error' ? 'error' : 'completed',
            input:     '',
            output:    (msg.output as string) ?? '',
            durationMs: ts - t0,
            timestamp:  ts,
          })
        }
      } else if (msg.type === 'result') {
        finalOutput = (msg.output as string) ?? ''
      } else if (msg.type === 'error') {
        reject(new Error((msg.message as string) ?? 'Unknown backend error'))
      }
    }

    async function read() {
      try {
        while (true) {
          const { done, value } = await reader.read()
          if (done) { resolve(finalOutput); break }
          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() ?? ''
          for (const line of lines) processLine(line)
        }
      } catch (err) {
        // AbortError is handled above via signal listener; swallow here
        if (err instanceof DOMException && err.name === 'AbortError') return
        reject(err)
      }
    }

    read()
  })
}

export async function checkBackendHealth(backendUrl: string): Promise<boolean> {
  try {
    const url = (backendUrl || 'http://localhost:8000').replace(/\/$/, '')
    const res = await fetch(`${url}/health`, { signal: AbortSignal.timeout(3000) })
    return res.ok
  } catch {
    return false
  }
}
