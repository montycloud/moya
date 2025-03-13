"""
Interactive chat example using OpenAI agent with conversation memory.
"""

import os
from moya.memory.in_memory_repository import InMemoryRepository
from moya.tools.tool_registry import ToolRegistry
from moya.tools.memory_tool import MemoryTool
from moya.registry.agent_registry import AgentRegistry
from moya.orchestrators.simple_orchestrator import SimpleOrchestrator
from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig
from moya.tools.ephemeral_memory import EphemeralMemory
import os
import sys
import logging

def setup_agent():
    # Set up memory components
    tool_registry = ToolRegistry()
    EphemeralMemory.configure_memory_tools(tool_registry)

    config = OpenAIAgentConfig(
        agent_name="chat_agent",
        description="An interactive chat agent",
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="gpt-4o",
        agent_type="ChatAgent",
        tool_registry=tool_registry,
        system_prompt="You are an interactive chat agent that can remember previous conversations. "
                    "You have access to tools that helps you to store and retrieve conversation history. "
                    "Always begin with storing the message in memory and fetch the conversation summary before generating final response."
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
    # logging.basicConfig(level=logging.INFO) # Set logging level to INFO
    orchestrator, agent = setup_agent()
    thread_id = "interactive_chat_001"

    print("Welcome to Interactive Chat! (Type 'quit' or 'exit' to end)")
    print("-" * 50)

    while True:
        # Get user input
        user_input = input("\nYou: ").strip()

        # Check for exit command
        if user_input.lower() in ['quit', 'exit']:
            print("\nGoodbye!")
            break

        # Print Assistant prompt
        print("\nAssistant: ", end="", flush=True)

        # Define callback for streaming
        def stream_callback(chunk):
            print(chunk, end="", flush=True)

        # Get response using stream_callback
        response = orchestrator.orchestrate(
            thread_id=thread_id,
            user_message=user_input
            # stream_callback=stream_callback
        )
        print(response)
        # Print newline after response
        print()




if __name__ == "__main__":
    main()
