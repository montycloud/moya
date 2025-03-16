"""
Interactive chat example using GeminiAgent with conversation memory.
"""

import os
import sys
from moya.agents.gemini_agent import GeminiAgent, GeminiAgentConfig
from moya.tools.ephemeral_memory import EphemeralMemory
from moya.memory.in_memory_repository import InMemoryRepository
from moya.tools.tool_registry import ToolRegistry
from moya.registry.agent_registry import AgentRegistry
from moya.orchestrators.simple_orchestrator import SimpleOrchestrator


def setup_agent():
    """Set up memory components and create a Gemini agent."""
    # Memory 
    tool_registry = ToolRegistry()
    EphemeralMemory.configure_memory_tools(tool_registry)

    try:
        agent_config = GeminiAgentConfig(
            agent_name="gemini_assistant",
            agent_type="ChatAgent",
            description="A helpful AI assistant powered by Google Gemini",
            system_prompt="You are a helpful AI assistant. Be concise and clear in your responses.",
            model_name="gemini-1.5-flash",
            api_key=os.getenv("GOOGLE_API_KEY"),
            tool_registry=tool_registry,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 2048
            }
        )

        agent = GeminiAgent(config=agent_config)
        agent.setup()

        # registry and orchestrator
        agent_registry = AgentRegistry()
        agent_registry.register_agent(agent)
        orchestrator = SimpleOrchestrator(
            agent_registry=agent_registry,
            default_agent_name="gemini_assistant"
        )

        return orchestrator, agent
    
    except Exception as e:
        print(f"\nError setting up Gemini agent: {str(e)}")
        print("\nMake sure your Google API key is set in the environment:")
        print("export GOOGLE_API_KEY=your_api_key_here")
        sys.exit(1)


def format_conversation_context(messages):
    """Format conversation history for context."""
    formatted = []
    for msg in messages:
        role = "User" if msg["sender"] == "user" else "Assistant"
        formatted.append(f"{role}: {msg['content']}")
    return "\n".join(formatted)


def main():
    """Run an interactive chat session with the Gemini agent."""
    
    orchestrator, agent = setup_agent()
    thread_id = "gemini_conversation"

    print("Starting Gemini chat (type 'exit' to quit)")
    print("-" * 50)

    def stream_callback(chunk):
        print(chunk, end="", flush=True)

    # Initial Message
    EphemeralMemory.store_message(
        thread_id=thread_id,
        sender="system",
        content="Conversation started with Gemini agent."
    )

    while True:
        user_message = input("\nYou: ").strip()
        
        if user_message.lower() == 'exit':
            print("\nGoodbye!")
            break

        # user 
        EphemeralMemory.store_message(
            thread_id=thread_id,
            sender="user",
            content=user_message
        )

        # context awareness
        previous_messages = agent.get_last_n_messages(thread_id, n=5)
        
        if previous_messages:
            context = format_conversation_context(previous_messages)
            enhanced_input = f"{context}\nCurrent user message: {user_message}"
        else:
            enhanced_input = user_message

        print("\nAssistant: ", end="", flush=True)
        response = orchestrator.orchestrate(
            thread_id=thread_id,
            user_message=enhanced_input,
            stream_callback=stream_callback
        )
        print()  
        
        # assistant
        EphemeralMemory.store_message(
            thread_id=thread_id,
            sender="assistant", 
            content=response
        )


if __name__ == "__main__":
    main()
