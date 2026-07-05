"""Rebuilds a live MOYA pipeline from the JSON flow graph sent by the UI."""

import sys
import pathlib

_repo_root = pathlib.Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

import re
import os
from typing import Any, Callable

from moya import create_agent, Pipeline, AgentStep, ParallelStep, LoopStep, BranchStep
from moya.flows.pipeline import FlowContext
from moya.flows.steps import FunctionStep
from moya.tools.tool import Tool
from moya.tools.tool_registry import ToolRegistry
from moya.skills.skill import Skill
from moya.memory import ShortTermMemory, LongTermMemory, CompositeMemory


def to_snake(s: str) -> str:
    return re.sub(r'[^a-z0-9]+', '_', (s or 'agent').lower()).strip('_') or 'agent'


def _topological_sort(nodes: list[dict], edges: list[dict]) -> list[dict]:
    node_map = {n['id']: n for n in nodes}
    succ: dict[str, list[str]] = {n['id']: [] for n in nodes}
    in_degree: dict[str, int] = {n['id']: 0 for n in nodes}

    for e in edges:
        src, tgt = e.get('source', ''), e.get('target', '')
        if src in succ:
            succ[src].append(tgt)
        if tgt in in_degree:
            in_degree[tgt] += 1

    queue = [n for n in nodes if in_degree[n['id']] == 0]
    result: list[dict] = []
    while queue:
        node = queue.pop(0)
        result.append(node)
        for sid in succ.get(node['id'], []):
            in_degree[sid] -= 1
            if in_degree[sid] == 0 and sid in node_map:
                queue.append(node_map[sid])
    return result


def _parse_headers(raw: str) -> dict:
    headers = {}
    for line in (raw or '').splitlines():
        line = line.strip()
        if not line or ':' not in line:
            continue
        k, v = line.split(':', 1)
        headers[k.strip()] = v.strip()
    return headers


def _build_tool_callable(spec: dict) -> Callable:
    """
    Turn a tool spec (from the registry, an agent's inline tools, or a Tool
    node) into a real callable.

    kind == 'python' → exec the user's function body with the declared signature.
    kind == 'api'    → make a real HTTP request, substituting parameters.
    Falls back to returning the simulated value if execution isn't possible.
    """
    kind = spec.get('kind', 'python')
    name = spec.get('name') or 'tool'
    mock = spec.get('mockReturnValue', 'Tool result')
    params = spec.get('parameters', []) or []
    param_names = [p.get('name') for p in params if p.get('name')]

    if kind == 'api':
        method = (spec.get('method') or 'GET').lower()
        url_tmpl = spec.get('url') or ''
        body_tmpl = (spec.get('body') or '').strip()
        base_headers = _parse_headers(spec.get('headers', ''))

        def api_fn(**kwargs: Any) -> str:
            import requests
            try:
                # Substitute {param} placeholders without disturbing literal JSON braces.
                url = url_tmpl
                for k, v in kwargs.items():
                    url = url.replace('{' + k + '}', str(v))
                headers = dict(base_headers)
                if method in ('get', 'delete'):
                    resp = requests.request(method, url, params=kwargs, headers=headers, timeout=30)
                elif body_tmpl:
                    body = body_tmpl
                    for k, v in kwargs.items():
                        body = body.replace('{' + k + '}', str(v))
                    if not any(h.lower() == 'content-type' for h in headers):
                        headers['Content-Type'] = 'application/json'
                    resp = requests.request(method, url, data=body, headers=headers, timeout=30)
                else:
                    resp = requests.request(method, url, json=kwargs, headers=headers, timeout=30)
                return resp.text
            except Exception as exc:  # noqa: BLE001
                return f"[tool '{name}' error] {exc}"
        return api_fn

    # kind == 'python' — build a def with the real signature and exec the body.
    body = (spec.get('code') or '').strip()
    if not body:
        def mock_fn(**_kwargs: Any) -> str:
            return mock
        return mock_fn

    sig = ', '.join(f"{p.get('name')}: {p.get('type', 'str')}" for p in params if p.get('name'))
    indented = '\n'.join('    ' + ln for ln in body.splitlines())
    src = f"def _tool({sig}):\n{indented}\n"
    ns: dict = {}
    try:
        exec(compile(src, f'<tool:{name}>', 'exec'), {}, ns)  # noqa: S102 — local dev tool execution
        return ns['_tool']
    except Exception as exc:  # noqa: BLE001
        def err_fn(**_kwargs: Any) -> str:
            return f"[tool '{name}' failed to compile] {exc}"
        return err_fn


def _make_mock_fn(val: str) -> Callable:
    def fn(**_kwargs: Any) -> str:
        return val
    return fn


def _build_memory(mem_cfg: dict) -> Any:
    """Compose ShortTermMemory / LongTermMemory from an agent's memory config."""
    if not mem_cfg:
        return None
    stores: list = []
    long_cfg = mem_cfg.get('longTerm') or {}
    if long_cfg.get('enabled'):
        stores.append(LongTermMemory(base_path=long_cfg.get('path') or './moya_memory'))
    short_cfg = mem_cfg.get('shortTerm') or {}
    if short_cfg.get('enabled'):
        stores.append(ShortTermMemory(window_size=int(short_cfg.get('windowSize') or 10)))
    if not stores:
        return None
    return stores[0] if len(stores) == 1 else CompositeMemory(stores)


def build_and_run(
    flow: dict,
    api_config: dict,
    trace_callback: Callable[[str, str, str, str], None],
    registry_tools: list[dict] | None = None,
) -> str:
    """
    Build MOYA objects from the flow graph and execute the pipeline.

    trace_callback(status, node_id, node_name, output)
      status: 'started' | 'completed' | 'error'
    """
    nodes: list[dict] = flow.get('nodes', [])
    edges: list[dict] = flow.get('edges', [])
    tool_lib = {t['id']: t for t in (registry_tools or []) if t.get('id')}

    node_map = {n['id']: n for n in nodes}

    # Apply API config to environment
    if api_config.get('openaiKey'):
        os.environ['OPENAI_API_KEY'] = api_config['openaiKey']
    if api_config.get('ollamaUrl'):
        os.environ['OLLAMA_HOST'] = api_config['ollamaUrl']
    if api_config.get('awsRegion'):
        os.environ['AWS_DEFAULT_REGION'] = api_config['awsRegion']

    # Separate capability edges (tool/skill/mcp → agent) from flow edges
    flow_edges = []
    cap_edges  = []
    for e in edges:
        src = node_map.get(e['source'])
        if src and src.get('type') in ('tool', 'skill', 'mcp'):
            cap_edges.append(e)
        else:
            flow_edges.append(e)

    agent_tools: dict[str, list[str]]     = {}
    agent_skills: dict[str, list[str]]    = {}
    agent_mcp_edges: dict[str, list[str]] = {}
    for e in cap_edges:
        src = node_map.get(e['source'])
        if not src:
            continue
        if src['type'] == 'tool':
            agent_tools.setdefault(e['target'], []).append(e['source'])
        elif src['type'] == 'skill':
            agent_skills.setdefault(e['target'], []).append(e['source'])
        elif src['type'] == 'mcp':
            agent_mcp_edges.setdefault(e['target'], []).append(e['source'])

    flow_nodes = [n for n in nodes if n.get('type') not in ('tool', 'skill', 'mcp')]
    sorted_nodes = _topological_sort(flow_nodes, flow_edges)

    succ: dict[str, list[str]] = {}
    for e in flow_edges:
        succ.setdefault(e['source'], []).append(e['target'])

    # Build Skill objects
    skill_map: dict[str, Skill] = {}
    for n in nodes:
        if n.get('type') != 'skill':
            continue
        d = n.get('data', {})
        skill_map[n['id']] = Skill(
            name=d.get('name', 'skill'),
            description=d.get('description', ''),
            prompt_snippet=d.get('promptSnippet', ''),
        )

    def _connect_mcp(mcp_cfg: dict, registry: ToolRegistry, agent_label: str) -> None:
        """Connect one MCP server and register its tools. Degrades gracefully."""
        try:
            from moya.mcp import MCPClient, MCPAuthConfig
            transport = mcp_cfg.get('transport', 'http')
            if transport == 'http':
                auth = MCPAuthConfig(bearer_token=mcp_cfg['apiKey']) if mcp_cfg.get('apiKey') else None
                client = MCPClient.from_url(
                    mcp_cfg.get('url', 'http://localhost:8080/sse'),
                    name=mcp_cfg.get('name', 'mcp'), auth=auth,
                )
            else:
                raw_args = (mcp_cfg.get('args') or '').split()
                client = MCPClient.from_subprocess(
                    mcp_cfg.get('command', 'python3'), args=raw_args,
                    name=mcp_cfg.get('name', 'mcp'),
                )
            for _tool in client.get_tools():
                registry.register_tool(_tool)
        except Exception as exc:  # noqa: BLE001 — surface as a trace warning, keep running
            trace_callback('completed', 'mcp-warn', f'⚠ MCP {mcp_cfg.get("name", "server")}',
                           f'Could not connect to MCP server: {exc}')

    def _build_registry(node: dict, d: dict, agent_label: str) -> ToolRegistry | None:
        """Assemble a per-agent ToolRegistry from edge tools, registry tools,
        inline tools, and MCP servers (edge-based + inspector-configured)."""
        registry = ToolRegistry()
        used = False

        # Edge-connected tool nodes
        for tid in agent_tools.get(node['id'], []):
            td = node_map.get(tid, {}).get('data', {})
            registry.register_tool(Tool(
                name=td.get('name', 'tool'),
                description=td.get('description', ''),
                function=_build_tool_callable(td),
            ))
            used = True

        # Registry-library tools referenced by id
        for rid in d.get('toolIds', []) or []:
            t = tool_lib.get(rid)
            if not t:
                continue
            registry.register_tool(Tool(
                name=t.get('name', 'tool'),
                description=t.get('description', ''),
                function=_build_tool_callable(t),
            ))
            used = True

        # Inline tools defined on the agent
        for t in d.get('inlineTools', []) or []:
            registry.register_tool(Tool(
                name=t.get('name', 'tool'),
                description=t.get('description', ''),
                function=_build_tool_callable(t),
            ))
            used = True

        # MCP servers — edge-connected nodes + inspector-configured list
        for mid in agent_mcp_edges.get(node['id'], []):
            _connect_mcp(node_map.get(mid, {}).get('data', {}), registry, agent_label)
            used = True
        for mcp_cfg in d.get('mcpServers', []) or []:
            _connect_mcp(mcp_cfg, registry, agent_label)
            used = True

        return registry if used else None

    # Build Agent objects — deduplicate names with a counter
    agent_instances: dict[str, Any] = {}
    seen_names: dict[str, int] = {}
    for n in nodes:
        if n.get('type') != 'agent':
            continue
        d = n.get('data', {})
        provider = d.get('provider', 'openai')
        model    = d.get('model', 'gpt-4o')
        base_name = to_snake(d.get('name') or d.get('label') or 'agent')

        # Deduplicate agent variable names
        if base_name in seen_names:
            seen_names[base_name] += 1
            name = f'{base_name}_{seen_names[base_name]}'
        else:
            seen_names[base_name] = 0
            name = base_name

        # A2A / remote agent — a thin proxy to a remote server.
        if provider == 'a2a':
            from moya.a2a.client import A2AAgent, A2AAgentConfig
            agent_instances[n['id']] = A2AAgent(A2AAgentConfig(
                agent_name=name,
                agent_type='a2a',
                description=d.get('description') or f'{name} (remote)',
                endpoint_url=d.get('endpointUrl') or 'http://localhost:8001',
                timeout_seconds=int(d.get('timeoutSeconds') or 60),
            ))
            continue

        registry = _build_registry(n, d, name)
        skills   = [skill_map[sid] for sid in agent_skills.get(n['id'], []) if sid in skill_map]
        memory   = _build_memory(d.get('memory') or {})

        agent_instances[n['id']] = create_agent(
            provider,
            name=name,
            description=d.get('description') or f'{name} agent',
            model=model,
            system_prompt=d.get('systemPrompt', ''),
            tags=d.get('tags', []),
            tool_registry=registry,
            skills=skills if skills else None,
            memory=memory,
        )

    # Build pipeline steps (with trace wrappers)
    consumed: set[str] = set()
    steps: list[Any]   = []

    def wrap(step: Any, node_id: str, node_name: str) -> FunctionStep:
        """Wraps a step to emit trace events before and after execution."""
        def traced(ctx: FlowContext) -> FlowContext:
            trace_callback('started', node_id, node_name, ctx.output)
            new_ctx = step.run(ctx)
            trace_callback('completed', node_id, node_name, new_ctx.output)
            return new_ctx
        return FunctionStep(traced)

    for node in sorted_nodes:
        nid   = node['id']
        ntype = node.get('type')
        nname = node.get('data', {}).get('label') or ntype or nid

        if nid in consumed or ntype in ('input', 'output', 'tool', 'skill'):
            continue

        if ntype == 'agent':
            agent = agent_instances.get(nid)
            if agent:
                steps.append(wrap(AgentStep(agent), nid, nname))

        elif ntype == 'parallel':
            branch_ids   = succ.get(nid, [])
            branch_steps = []
            for bid in branch_ids:
                bnode = node_map.get(bid)
                if bnode and bnode.get('type') == 'agent':
                    consumed.add(bid)
                    ba = agent_instances.get(bid)
                    bn = bnode.get('data', {}).get('label') or bid
                    if ba:
                        branch_steps.append(wrap(AgentStep(ba), bid, bn))
            if branch_steps:
                d = node.get('data', {})
                if d.get('mergeStrategy') == 'first':
                    merge_fn = lambda outs: outs[0] if outs else ''
                else:
                    merge_fn = lambda outs: '\n\n---\n\n'.join(outs)
                pstep = ParallelStep(branch_steps, merge=merge_fn)
                steps.append(wrap(pstep, nid, nname))

        elif ntype == 'loop':
            loop_targets = [node_map[sid] for sid in succ.get(nid, []) if sid in node_map]
            loop_agent_node = next((n for n in loop_targets if n.get('type') == 'agent'), None)
            if loop_agent_node:
                consumed.add(loop_agent_node['id'])
                la = agent_instances.get(loop_agent_node['id'])
                if la:
                    d  = node.get('data', {})
                    kw = d.get('stopKeyword') or 'DONE'
                    mx = int(d.get('maxIterations') or 3)
                    inner = wrap(AgentStep(la), loop_agent_node['id'], loop_agent_node.get('data', {}).get('label', 'loop_agent'))
                    lstep = LoopStep(
                        step=inner,
                        until=lambda ctx, k=kw: k in ctx.output,
                        max_iterations=mx,
                    )
                    steps.append(wrap(lstep, nid, nname))

        elif ntype == 'branch':
            d  = node.get('data', {})
            kw = (d.get('conditionKeyword') or 'yes').lower()
            true_edge  = next((e for e in flow_edges if e['source'] == nid and e.get('sourceHandle') == 'true'),  None)
            false_edge = next((e for e in flow_edges if e['source'] == nid and e.get('sourceHandle') == 'false'), None)

            def make_branch_step(edge: dict | None) -> Any:
                if not edge:
                    return FunctionStep(lambda ctx: ctx)
                bn = node_map.get(edge['target'])
                if bn and bn.get('type') == 'agent':
                    consumed.add(bn['id'])
                    ba = agent_instances.get(bn['id'])
                    if ba:
                        return AgentStep(ba)
                return FunctionStep(lambda ctx: ctx)

            bstep = BranchStep(
                condition=lambda ctx, k=kw: 'yes' if k in ctx.output.lower() else 'no',
                branches={
                    'yes': make_branch_step(true_edge),
                    'no':  make_branch_step(false_edge),
                },
            )
            steps.append(wrap(bstep, nid, nname))

    if not steps:
        raise ValueError(
            'No executable steps found — connect agents to the flow and try again.'
        )

    input_node = next((n for n in nodes if n.get('type') == 'input'), None)
    message = (input_node or {}).get('data', {}).get('message') or 'Hello!'

    pipeline = Pipeline(steps)
    return pipeline.run(thread_id='ui-run', message=message)
