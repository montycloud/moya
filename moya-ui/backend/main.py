"""FastAPI backend for MOYA Agent Studio — real LLM execution via SSE."""

import sys
import pathlib

_repo_root = pathlib.Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

import asyncio
import json
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from flow_builder import build_and_run
from marketplace_store import AgentListing, get_store

app = FastAPI(title="MOYA Agent Studio API")

# Allow CORS_ORIGINS env var for remote/production deployments
_default_origins = [
    "http://localhost:5173", "http://localhost:5174", "http://localhost:4173",
    "http://127.0.0.1:5173", "http://127.0.0.1:5174",
]
_extra_origins = [o.strip() for o in os.environ.get('CORS_ORIGINS', '').split(',') if o.strip()]
_allow_origins = _default_origins + _extra_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ApiConfig(BaseModel):
    openaiKey: str = ''
    ollamaUrl: str = 'http://localhost:11434'
    awsRegion: str = 'us-east-1'
    backendUrl: str = 'http://localhost:8000'


class RunRequest(BaseModel):
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    api_config: ApiConfig = ApiConfig()
    registry_tools: list[dict[str, Any]] = Field(default_factory=list)


@app.get('/health')
def health():
    return {'status': 'ok'}


@app.post('/api/run')
async def run_flow(request: RunRequest):
    """Execute the flow graph and stream trace events back via SSE."""

    event_queue: asyncio.Queue[dict | None] = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def trace_callback(status: str, node_id: str, node_name: str, output: str):
        event = {
            'type': 'trace',
            'nodeId': node_id,
            'nodeName': node_name,
            'status': status,
            'output': output[:2000] if status == 'completed' else '',
            'timestamp': int(time.time() * 1000),
        }
        asyncio.run_coroutine_threadsafe(event_queue.put(event), loop)

    def run_in_thread():
        try:
            result = build_and_run(
                flow={'nodes': request.nodes, 'edges': request.edges},
                api_config=request.api_config.model_dump(),
                trace_callback=trace_callback,
                registry_tools=request.registry_tools,
            )
            asyncio.run_coroutine_threadsafe(
                event_queue.put({'type': 'result', 'output': result}), loop
            )
        except Exception as exc:
            asyncio.run_coroutine_threadsafe(
                event_queue.put({'type': 'error', 'message': str(exc)}), loop
            )
        finally:
            asyncio.run_coroutine_threadsafe(event_queue.put(None), loop)

    import threading
    threading.Thread(target=run_in_thread, daemon=True).start()

    async def stream():
        while True:
            item = await event_queue.get()
            if item is None:
                break
            yield {'data': json.dumps(item)}

    return EventSourceResponse(stream())


# ── Marketplace routes ────────────────────────────────────────────────────────

class PublishRequest(BaseModel):
    id: str = ''
    name: str
    description: str = ''
    category: str = 'General'
    tags: list[str] = Field(default_factory=list)
    provider: str = 'user'
    node_count: dict[str, int] = Field(default_factory=dict)
    flow: dict[str, Any]


@app.get('/api/marketplace')
def list_marketplace():
    return [l.model_dump() for l in get_store().list_agents()]


@app.post('/api/marketplace/publish')
def publish_agent(req: PublishRequest):
    listing = AgentListing(
        id=req.id or str(uuid.uuid4()),
        name=req.name,
        description=req.description,
        category=req.category,
        tags=req.tags,
        provider=req.provider,
        node_count=req.node_count,
        flow=req.flow,
        published_at=datetime.now(timezone.utc).isoformat(),
    )
    get_store().publish_agent(listing)
    return listing.model_dump()


@app.get('/api/marketplace/{agent_id}')
def get_marketplace_agent(agent_id: str):
    listing = get_store().get_agent(agent_id)
    if not listing:
        raise HTTPException(status_code=404, detail='Agent not found')
    return listing.model_dump()


@app.delete('/api/marketplace/{agent_id}')
def delete_marketplace_agent(agent_id: str):
    removed = get_store().delete_agent(agent_id)
    return {'removed': removed}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)
