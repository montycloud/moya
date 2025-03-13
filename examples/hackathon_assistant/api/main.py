from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
import json
import logging
import asyncio
from pathlib import Path
from typing import AsyncGenerator
from hackathon_assistant.agents.documentation_agent import DocumentationAgent
from hackathon_assistant.tools.knowledge_base_tool import KnowledgeBaseTool
from moya.memory.in_memory_repository import InMemoryRepository
from moya.tools.memory_tool import MemoryTool
from moya.tools.tool_registry import ToolRegistry
import uuid
from mangum import Mangum

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Set up documentation path
DOCS_PATH = Path(__file__).parent.parent / "data" / "documentation"
logger.info(f"Loading documentation from: {DOCS_PATH}")

# Initialize components
try:
    memory_repo = InMemoryRepository()
    memory_tool = MemoryTool(memory_repository=memory_repo)
    tool_registry = ToolRegistry()
    tool_registry.register_tool(memory_tool)

    # Set up knowledge base with proper initialization
    knowledge_tool = KnowledgeBaseTool(
        name="KnowledgeBaseTool",
        description="Tool for searching Moya documentation",
        docs_path=str(DOCS_PATH)
    )
    tool_registry.register_tool(knowledge_tool)

    # Initialize agent
    agent = DocumentationAgent(tool_registry=tool_registry)
    agent.setup()
    logger.info("Agent initialization successful")
except Exception as e:
    logger.error(f"Failed to initialize components: {e}")
    raise

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="/workspaces/moya/examples/hackathon_assistant/web/dist", html=True), name="static")

@app.get("/starter-prompts")
async def get_starter_prompts():
    """Get predefined starter prompts."""
    return {
        "prompts": [
            {
                "title": "Framework Introduction",
                "description": "Learn about the core concepts of Moya",
                "prompts": [
                    {"text": "What is Moya and how does it help with CloudOps automation?"},
                    {"text": "Can you explain Moya's multi-agent architecture?"},
                    {"text": "What are the key components of the Moya framework?"}
                ]
            },
            {
                "title": "Getting Started",
                "description": "Begin your journey with Moya",
                "prompts": [
                    {"text": "How do I install and set up Moya?"},
                    {"text": "What are the prerequisites for using Moya?"},
                    {"text": "Can you show me a basic example of using Moya?"}
                ]
            },
            {
                "title": "Agent System",
                "description": "Explore Moya's agent capabilities",
                "prompts": [
                    {"text": "What types of agents are available in Moya?"},
                    {"text": "How do I configure OpenAI agents in Moya?"},
                    {"text": "How do I create a custom agent?"}
                ]
            }
        ]
    }

@app.get("/chat/stream")
async def chat_stream(message: str, request: Request) -> EventSourceResponse:
    """Stream chat responses."""
    logger.info(f"Received streaming request: {message}")
    
    async def event_generator() -> AsyncGenerator:
        try:
            for chunk in agent.handle_documentation_query(message):
                if await request.is_disconnected():
                    logger.debug("Client disconnected")
                    break
                
                yield {
                    "event": "message",
                    "data": json.dumps({"content": chunk}),
                    "retry": 1000
                }
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error in stream: {str(e)}")
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }
    
    return EventSourceResponse(event_generator())

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    status = {
        "status": "healthy",
        "agent": agent is not None,
        "tool_registry": tool_registry is not None
    }
    return status

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)

handler = Mangum(app)