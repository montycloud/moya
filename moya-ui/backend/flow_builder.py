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


def build_and_run(
    flow: dict,
    api_config: dict,
    trace_callback: Callable[[str, str, str, str], None],
) -> str:
    """
    Build MOYA objects from the flow graph and execute the pipeline.

    trace_callback(status, node_id, node_name, output)
      status: 'started' | 'completed' | 'error'
    """
    nodes: list[dict] = flow.get('nodes', [])
    edges: list[dict] = flow.get('edges', [])

    node_map = {n['id']: n for n in nodes}

    # Apply API config to environment
    if api_config.get('openaiKey'):
        os.environ['OPENAI_API_KEY'] = api_config['openaiKey']
    if api_config.get('ollamaUrl'):
        os.environ['OLLAMA_HOST'] = api_config['ollamaUrl']
    if api_config.get('awsRegion'):
        os.environ['AWS_DEFAULT_REGION'] = api_config['awsRegion']

    # Separate capability edges (tool/skill → agent) from flow edges
    flow_edges = []
    cap_edges  = []
    for e in edges:
        src = node_map.get(e['source'])
        if src and src.get('type') in ('tool', 'skill'):
            cap_edges.append(e)
        else:
            flow_edges.append(e)

    agent_tools: dict[str, list[str]]  = {}
    agent_skills: dict[str, list[str]] = {}
    for e in cap_edges:
        src = node_map.get(e['source'])
        if not src:
            continue
        if src['type'] == 'tool':
            agent_tools.setdefault(e['target'], []).append(e['source'])
        elif src['type'] == 'skill':
            agent_skills.setdefault(e['target'], []).append(e['source'])

    flow_nodes = [n for n in nodes if n.get('type') not in ('tool', 'skill')]
    sorted_nodes = _topological_sort(flow_nodes, flow_edges)

    succ: dict[str, list[str]] = {}
    for e in flow_edges:
        succ.setdefault(e['source'], []).append(e['target'])

    # Build shared ToolRegistry and mock tool functions
    tool_registry = ToolRegistry()
    for n in nodes:
        if n.get('type') != 'tool':
            continue
        d = n.get('data', {})
        mock_val = d.get('mockReturnValue', 'Tool result')

        def make_fn(val: str) -> Callable:
            def fn(**_kwargs: Any) -> str:
                return val
            return fn

        tool_registry.register_tool(Tool(
            name=d.get('name', 'tool'),
            description=d.get('description', ''),
            function=make_fn(mock_val),
        ))

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

        has_tools = bool(agent_tools.get(n['id']))
        skills    = [skill_map[sid] for sid in agent_skills.get(n['id'], []) if sid in skill_map]

        agent_instances[n['id']] = create_agent(
            provider,
            name=name,
            description=d.get('description') or f'{name} agent',
            model=model,
            system_prompt=d.get('systemPrompt', ''),
            tags=d.get('tags', []),
            tool_registry=tool_registry if has_tools else None,
            skills=skills if skills else None,
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
