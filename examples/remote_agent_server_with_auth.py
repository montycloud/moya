import asyncio
import uvicorn
import os
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any

from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig
from moya.memory.in_memory_repository import InMemoryRepository
from moya.tools.tool_registry import ToolRegistry
from moya.tools.ephemeral_memory import EphemeralMemory

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
    tool_registry = ToolRegistry()
    EphemeralMemory.configure_memory_tools(tool_registry)

    # Create and setup agent
    agent_config = OpenAIAgentConfig(
        agent_name="remote_joke_agent",
        agent_type="RemoteAgent",
        description="Remote agent specialized in humor",
        system_prompt="You are a remote agent that specializes in telling jokes and being entertaining.",
        api_key=os.getenv("OPENAI_API_KEY"),
        tool_registry=tool_registry,
        model_name="gpt-4o",
        llm_config={
            'temperature':0.8,
            'max_tokens':1000
        }
    )
    return OpenAIAgent(agent_config)
   


# Initialize agent at startup
agent = setup_agent()


@app.get("/health", dependencies=[Depends(verify_token)])
async def health_check():
    """Protected health check endpoint."""
    return {"status": "healthy", "agent": agent.agent_name}


@app.post("/chat", dependencies=[Depends(verify_token)])
async def chat(request: Request):
    """Handle normal chat requests using OpenAI agent."""
    data = await request.json()
    message = data['message']
    thread_id = data.get('thread_id', 'default_thread')

    # Store user message
    EphemeralMemory.store_message(thread_id=thread_id, sender="user", content=message)

    # Get response from agent
    response = agent.handle_message(message, thread_id=thread_id)

    # Store agent response
    EphemeralMemory.store_message(thread_id=thread_id, sender=agent.agent_name, content=response)
    
    return {"response": response}


@app.post("/chat/stream", dependencies=[Depends(verify_token)])
async def chat_stream(request: Request):
    """Handle streaming chat requests using OpenAI agent."""
    data = await request.json()
    message = data['message']
    thread_id = data.get('thread_id', 'default_thread')

    return StreamingResponse(
        stream_response(message, thread_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
            "Transfer-Encoding": "chunked"
        }
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
