"""
Interactive chat example using OpenAI agent with conversation memory.
"""

import os
from moya.tools.tool_registry import ToolRegistry
from moya.registry.agent_registry import AgentRegistry
from moya.orchestrators.simple_orchestrator import SimpleOrchestrator
from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig
from moya.tools.ephemeral_memory import EphemeralMemory
from moya.memory.file_system_repo import FileSystemRepository
import os
from examples.quick_tools import QuickTools
from moya.tools.base_tool import BaseTool


def setup_agent():
    # Set up memory components
    tool_registry = ToolRegistry()

    EphemeralMemory.configure_memory_tools(tool_registry)
    tool_registry.register_tool(BaseTool(name="ConversationContext", function=QuickTools.get_conversation_context))

    config = OpenAIAgentConfig(
        agent_name="chat_agent",
        description="An interactive chat agent",
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="gpt-4o",
        agent_type="ChatAgent",
        tool_registry=tool_registry,
        is_streaming=True,
        system_prompt="You are an interactive chat agent that can remember previous conversations. "
                    "You have access to tools that helps you to store and retrieve conversation history."
                    "Use the conversation history for your reference in answering any ueser query."
                    "Be Helpful and polite in your responses, and be concise and clear."
                     "Be useful but do not provide any information unless asked.",
    )

    # Create OpenAI agent with memory capabilities
    agent = OpenAIAgent(config)

    # Set up registry and orchestrator
    agent_registry = AgentRegistry()
    agent_registry.register_agent(agent)
    orchestrator = SimpleOrchestrator(
        agent_registry=agent_registry,
        default_agent_name="chat_agent"
    )

    return orchestrator, agent


def format_conversation_context(messages):
    context = "\nPrevious conversation:\n"
    for msg in messages:
        # Access Message object attributes properly using dot notation
        sender = "User" if msg.sender == "user" else "Assistant"
        context += f"{sender}: {msg.content}\n"
    return context


def main():
    orchestrator, agent = setup_agent()
    thread_id = QuickTools.get_conversation_context()["thread_id"]
    # EphemeralMemory.store_message(thread_id=thread_id, sender="system", content=f"Starting conversation, thread ID: {thread_id}")

    print("Welcome to Interactive Chat! (Type 'quit' or 'exit' to end)")
    print("-" * 50)

    while True:
        # Get user input
        user_input = input("\nYou: ").strip()

        # Check for exit command
        if user_input.lower() in ['quit', 'exit']:
            print("\nGoodbye!")
            break

        # Store user message
        EphemeralMemory.store_message(thread_id=thread_id, sender="user", content=user_input)
    
        session_summary = EphemeralMemory.get_thread_summary(thread_id)
        enriched_input = f"{session_summary}\nCurrent user message: {user_input}"

        # Print Assistant prompt
        print("\nAssistant: ", end="", flush=True)

        # Define callback for streaming
        def stream_callback(chunk):
            print(chunk, end="", flush=True)

        # Get response using stream_callback
        response = orchestrator.orchestrate(
            thread_id=thread_id,
            user_message=enriched_input,
            stream_callback=stream_callback
        )

        # print(response)

        EphemeralMemory.store_message(thread_id=thread_id, sender="assistant", content=response)
        # Print newline after response
        print()


if __name__ == "__main__":
    main()
