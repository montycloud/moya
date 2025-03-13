"""
Interactive chat example using Ollama agent with conversation memory.
"""

import logging
import sys
from moya.memory.in_memory_repository import InMemoryRepository
from moya.tools.tool_registry import ToolRegistry
from moya.tools.memory_tool import MemoryTool
from moya.registry.agent_registry import AgentRegistry
from moya.orchestrators.simple_orchestrator import SimpleOrchestrator
from moya.agents.ollama_agent import OllamaAgent, OllamaAgentConfig

# Set up logging
logging.basicConfig(level=logging.INFO)  # Changed from DEBUG to INFO
logger = logging.getLogger(__name__)


def setup_agent():
    # Set up memory components
    memory_repo = InMemoryRepository()
    memory_tool = MemoryTool(memory_repository=memory_repo)
    tool_registry = ToolRegistry()
    tool_registry.register_tool(memory_tool)

    # Create Ollama agent with memory capabilities and correct configuration
    agent_config = OllamaAgentConfig(
        system_prompt="You are a helpful AI assistant. Be concise and clear.",
        model_name="llama3.1",
        temperature=0.7,
        base_url="http://localhost:11434",
        context_window=4096
    )

    agent = OllamaAgent(
        agent_name="ollama_assistant",
        description="A local AI assistant powered by Ollama with memory",
        agent_config=agent_config,
        tool_registry=tool_registry
    )

    # Verify Ollama connection with simple test request
    try:
        agent.setup()
        # Test connection using handle_message
        test_response = agent.handle_message("test connection")
        if not test_response:
            raise Exception("No response from Ollama test query")
        logger.info("Successfully connected to Ollama")
    except Exception as e:
        logger.error(f"Failed to connect to Ollama: {e}")
        print("\nError: Make sure Ollama is running and the model is downloaded:")
        print("1. Start Ollama: ollama serve")
        print("2. Pull model: ollama pull llama3.1:latest")
        sys.exit(1)

    # Set up registry and orchestrator
    agent_registry = AgentRegistry()
    agent_registry.register_agent(agent)
    orchestrator = SimpleOrchestrator(
        agent_registry=agent_registry,
        default_agent_name="ollama_assistant"
    )

    return orchestrator, agent


def format_conversation_context(messages):
    context = "\nPrevious conversation:\n"
    for msg in messages:
        sender = "User" if msg.sender == "user" else "Assistant"
        context += f"{sender}: {msg.content}\n"
    return context


def main():
    orchestrator, agent = setup_agent()
    thread_id = "interactive_chat_001"

    print("Welcome to Interactive Chat! (Type 'quit' or 'exit' to end)")
    print("-" * 50)

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() in ['quit', 'exit']:
            print("\nGoodbye!")
            break

        logger.debug(f"User input: {user_input}")

        # Store user message
        agent.call_tool(
            tool_name="MemoryTool",
            method_name="store_message",
            thread_id=thread_id,
            sender="user",
            content=user_input
        )

        # Get conversation context
        previous_messages = agent.get_last_n_messages(thread_id, n=5)

        if previous_messages:
            context = format_conversation_context(previous_messages)
            enhanced_input = f"{context}\nCurrent user message: {user_input}"
        else:
            enhanced_input = user_input

        logger.debug(f"Enhanced input: {enhanced_input}")

        try:
            print("\nAssistant: ", end="", flush=True)

            response = ""
            try:
                # Use enhanced_input instead of user_input for context
                for chunk in agent.handle_message_stream(enhanced_input):
                    if chunk:
                        print(chunk, end="", flush=True)
                        response += chunk
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                # Fallback to non-streaming with enhanced input
                response = agent.handle_message(enhanced_input)
                if response:
                    print(response)

            print()

            if not response or response.startswith("[OllamaAgent error"):
                print("\nError: No response received. Please try again.")
                continue

            # Store the assistant's response
            agent.call_tool(
                tool_name="MemoryTool",
                method_name="store_message",
                thread_id=thread_id,
                sender="assistant",
                content=response
            )

        except Exception as e:
            logger.error(f"Error during chat: {e}")
            print("\nAn error occurred. Please try again.")
            continue


if __name__ == "__main__":
    main()
