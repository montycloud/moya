"""
Interactive chat example using BedrockAgent with conversation memory.
"""

from moya.memory.in_memory_repository import InMemoryRepository
from moya.tools.tool_registry import ToolRegistry
from moya.registry.agent_registry import AgentRegistry
from moya.orchestrators.simple_orchestrator import SimpleOrchestrator
from moya.agents.bedrock_agent import BedrockAgent, BedrockAgentConfig
from moya.tools.ephemeral_memory import EphemeralMemory
from moya.tools.base_tool import BaseTool


def setup_agent():
    
    # Set up memory components
    tool_registry = ToolRegistry()
    EphemeralMemory.configure_memory_tools(tool_registry)

    # Create Bedrock agent with memory capabilities
    agent_config = BedrockAgentConfig(
        agent_name="bedrock_chat",
        agent_type="ChatAgent",
        description="An interactive chat agent using AWS Bedrock with memory capabilities.",
        system_prompt="You are a helpful AI assistant with memory capabilities.",
        model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
        region="us-east-1",
        tool_registry=tool_registry,
        llm_config={
            'temperature': 0.7,
            'max_tokens': 1000
        }
    )

    agent = BedrockAgent(
        config=agent_config
    )
    agent.setup()

    # Set up registry and orchestrator
    agent_registry = AgentRegistry()
    agent_registry.register_agent(agent)
    orchestrator = SimpleOrchestrator(
        agent_registry=agent_registry,
        default_agent_name="bedrock_chat"
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
    thread_id = "bedrock_chat_001"

    print("Welcome to Bedrock Interactive Chat! (Type 'quit' or 'exit' to end)")
    print("-" * 50)

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() in ['quit', 'exit']:
            print("\nGoodbye!")
            break

        # Store the user message
        EphemeralMemory.store_message(thread_id=thread_id, sender="user", content=user_input)

        # Get conversation context
        previous_messages = agent.get_last_n_messages(thread_id, n=5)

        # Add context to the user's message
        if previous_messages:
            context = format_conversation_context(previous_messages)
            enhanced_input = f"{context}\nCurrent user message: {user_input}"
        else:
            enhanced_input = user_input

        print("\nAssistant: ", end="", flush=True)

        # Get response using streaming
        response = ""
        for chunk in agent.handle_message_stream(enhanced_input):
            print(chunk, end="", flush=True)
            response += chunk
        print()

        # Store the assistant's response
        EphemeralMemory.store_message(thread_id=thread_id, sender="assistant", content=response)


if __name__ == "__main__":
    main()
