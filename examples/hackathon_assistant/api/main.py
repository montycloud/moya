from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
import logging
from pathlib import Path
from moya.memory.in_memory_repository import InMemoryRepository
from moya.tools.memory_tool import MemoryTool
from moya.tools.tool_registry import ToolRegistry
from ..agents.documentation_agent import DocumentationAgent
from ..tools.knowledge_base_tool import KnowledgeBaseTool
import uuid

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize components with error handling
try:
    memory_repo = InMemoryRepository()
    memory_tool = MemoryTool(memory_repository=memory_repo)
    tool_registry = ToolRegistry()
    tool_registry.register_tool(memory_tool)

    # Set up knowledge base
    docs_path = "examples/hackathon_assistant/data/documentation"
    knowledge_tool = KnowledgeBaseTool(docs_path=docs_path)
    tool_registry.register_tool(knowledge_tool)

    # Initialize agent
    agent = DocumentationAgent(tool_registry=tool_registry)
    agent.setup()
    logger.info("Agent initialization successful")
except Exception as e:
    logger.error(f"Failed to initialize components: {e}")
    raise

# Initialize knowledge base
DOCS_PATH = Path(__file__).parent.parent / "data" / "documentation"
logger.info(f"Loading documentation from: {DOCS_PATH}")

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    logger.debug(f"Received streaming request: {message}")
    
    async def event_generator():
        try:
            # First search relevant documentation
            docs = knowledge_tool.search_docs(message)
            context = ""
            if docs:
                context = "\n\nRelevant documentation:\n"
                for name, content in docs:
                    context += f"\n--- {name} ---\n{content}\n"
                logger.debug(f"Found documentation context: {context}")

            # Enhance prompt with context
            enhanced_message = f"{context}\n\nUser query: {message}\nRemember to cite documentation when possible."
            logger.debug(f"Enhanced message: {enhanced_message}")

            # Stream response
            for chunk in agent.handle_message_stream(enhanced_message):
                if await request.is_disconnected():
                    logger.debug("Client disconnected")
                    break

                logger.debug(f"Sending chunk: {chunk}")
                yield {
                    "event": "message",
                    "data": json.dumps({"content": chunk})
                }
                await asyncio.sleep(0.05)  # Reduced delay

        except Exception as e:
            logger.error(f"Error in stream: {str(e)}")
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }

    return EventSourceResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    status = {
        "status": "healthy",
        "agent": agent is not None,
        "tool_registry": tool_registry is not None
    }
    return status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
