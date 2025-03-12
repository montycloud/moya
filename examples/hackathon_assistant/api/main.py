from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from typing import Dict, Any
import asyncio
import json

from ..agents.documentation_agent import DocumentationAgent
from ..tools.knowledge_base_tool import KnowledgeBaseTool
from moya.memory.in_memory_repository import InMemoryRepository
from moya.tools.memory_tool import MemoryTool
from moya.tools.tool_registry import ToolRegistry

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent
memory_repo = InMemoryRepository()
memory_tool = MemoryTool(memory_repository=memory_repo)
tool_registry = ToolRegistry()
tool_registry.register_tool(memory_tool)

# Set up knowledge base
docs_path = "data/documentation"
knowledge_tool = KnowledgeBaseTool(docs_path=docs_path)
tool_registry.register_tool(knowledge_tool)

agent = DocumentationAgent(tool_registry=tool_registry)
agent.setup()

@app.post("/chat")
async def chat_endpoint(request: Request) -> EventSourceResponse:
    data = await request.json()
    message = data.get("message", "")
    
    async def event_generator():
        try:
            for chunk in agent.handle_message_stream(message):
                if await request.is_disconnected():
                    break
                yield {"data": json.dumps({"content": chunk})}
                await asyncio.sleep(0.02)  # Small delay for smooth streaming
        except Exception as e:
            yield {"data": json.dumps({"error": str(e)})}
    
    return EventSourceResponse(event_generator())

@app.get("/starter-prompts")
async def get_starter_prompts():
    return {
        "prompts": [
            {
                "category": "Framework Basics",
                "prompts": [
                    "What is Moya and what problems does it solve?",
                    "How do I get started with Moya?",
                    "What are the core components of Moya?",
                ]
            },
            {
                "category": "Agents",
                "prompts": [
                    "What types of agents are available in Moya?",
                    "How do I create a custom agent?",
                    "How does agent orchestration work?",
                ]
            },
            {
                "category": "Tools and Memory",
                "prompts": [
                    "How does the memory system work?",
                    "What tools are available in Moya?",
                    "How can I create custom tools?",
                ]
            }
        ]
    }
