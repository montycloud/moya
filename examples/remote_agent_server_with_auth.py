from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import uvicorn
from asyncio import CancelledError

from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig
from moya.memory.in_memory_repository import InMemoryRepository
from moya.tools.tool_registry import ToolRegistry
from moya.tools.memory_tool import MemoryTool

app = FastAPI()
security = HTTPBearer()

# Configure your bearer token
VALID_TOKEN = "your-secret-token-here"

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != VALID_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

class Message(BaseModel):
    content: str
    thread_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

def setup_agent():
    """Set up OpenAI agent with memory capabilities."""
    # Set up memory components
    memory_repo = InMemoryRepository()
    memory_tool = MemoryTool(memory_repository=memory_repo)
    tool_registry = ToolRegistry()
    tool_registry.register_tool(memory_tool)

    # Create and setup agent
    agent_config = OpenAIAgentConfig(
        system_prompt="You are a secure remote agent that requires authentication.",
        model_name="gpt-4o"
    )

    agent = OpenAIAgent(
        agent_name="secure_remote_agent",
        description="Authenticated remote agent",
        agent_config=agent_config,
        tool_registry=tool_registry
    )
    agent.setup()
    return agent

# Initialize agent at startup
agent = setup_agent()

@app.get("/health", dependencies=[Depends(verify_token)])
async def health_check():
    """Protected health check endpoint."""
    return {"status": "healthy", "agent": agent.agent_name}

@app.post("/chat", dependencies=[Depends(verify_token)])
async def chat(request: Request):
    """Protected chat endpoint."""
    data = await request.json()
    message = data['message']
    thread_id = data.get('thread_id', 'default_thread')
    
    response = agent.handle_message(message, thread_id=thread_id)
    return {"response": response}

@app.post("/chat/stream", dependencies=[Depends(verify_token)])
async def chat_stream(request: Request):
    """Protected streaming chat endpoint."""
    data = await request.json()
    message = data['message']
    thread_id = data.get('thread_id', 'default_thread')
    
    return StreamingResponse(
        stream_response(message, thread_id),
        media_type="text/event-stream"
    )

async def stream_response(message: str, thread_id: str):
    """Stream response from OpenAI agent."""
    try:
        for chunk in agent.handle_message_stream(message, thread_id=thread_id):
            if chunk:
                yield f"data: {chunk}\n\n"
                await asyncio.sleep(0.01)
    except Exception as e:
        yield f"data: [Error: {str(e)}]\n\n"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)  # Note different port
