"""
Interactive chat example using OpenAI agent with conversation memory.
"""

import os
import random
from moya.conversation.thread import Thread
from moya.tools.base_tool import BaseTool
from moya.tools.ephemeral_memory import EphemeralMemory
from moya.tools.tool_registry import ToolRegistry
from moya.registry.agent_registry import AgentRegistry
from moya.orchestrators.simple_orchestrator import SimpleOrchestrator
from moya.agents.azure_openai_agent import AzureOpenAIAgent, AzureOpenAIAgentConfig
from moya.conversation.message import Message



def reverse_text(text: str) -> str:
    """
    Reverse the given text.

    Args:
        text (str): The text to reverse.

    Returns:
        str: The reversed text.
    """
    return f"{text[::-1]}"


def fetch_weather_data(location: str) -> str:
    """
    Fetch random weather data for a given location.

    Args:
        location (str): The location to fetch weather data for.

    Returns:
        str: A string describing the weather in the given location.
    """
    weather_list = ["sunny", "rainy", "cloudy", "windy"]
    # Pick a random weather condition
    return f"The weather in {location} is {random.choice(weather_list)}."


def setup_agent():
    """
    Set up the AzureOpenAI agent with memory capabilities and return the orchestrator and agent.

    Returns:
        tuple: A tuple containing the orchestrator and the agent.
    """
    # Set up memory components
    tool_registry = ToolRegistry()
    EphemeralMemory.configure_memory_tools(tool_registry)

    reverse_text_tool = BaseTool(
        name="reverse_text_tool",
        description="Tool to reverse any given text",
        function=reverse_text,
        parameters={
            "text": {
                "type": "string",
                "description": "The input text to reverse"
            }
        },
        required=["text"]
    )
    tool_registry.register_tool(reverse_text_tool)

    fetch_weather_data_tool = BaseTool(
        name="fetch_weather_data_tool",
        description="Tool to fetch weather data for a location",
        function=fetch_weather_data,
        parameters={
            "location": {
                "type": "string",
                "description": "The location to fetch weather data for"
            }
        },
        required=["location"]
    )
    tool_registry.register_tool(fetch_weather_data_tool)


    # Create agent configuration
    agent_config = AzureOpenAIAgentConfig(
        agent_name="chat_agent",
        description="An interactive chat agent",
        model_name="gpt-4o",
        agent_type="ChatAgent",
        tool_registry=tool_registry,
        system_prompt="""
            You are an interactive chat agent that can remember previous conversations.
            You have access to tools that help you store and retrieve conversation history.
            Always begin with storing the message in memory and fetch the conversation summary before generating the final response.
            You have access to reverse_text_tool that reverses the text. Always use this tool to reverse the text.
            You have access to fetch_weather_data_tool that fetches the weather data for a location.
        """,
        # api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        # Use Azure AD token provider instead of API key. Set value to false if you want to use API key
        use_azure_ad_token_provider=True,
        api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),  # Use default OpenAI API base
        api_version=os.getenv("AZURE_OPENAI_API_VERSION") or "2024-12-01-preview",
        organization=None  # Use default organization
    )

    # Create Azure OpenAI agent with memory capabilities
    agent = AzureOpenAIAgent(
        config=agent_config
    )

    # Set up registry and orchestrator
    agent_registry = AgentRegistry()
    agent_registry.register_agent(agent)
    orchestrator = SimpleOrchestrator(
        agent_registry=agent_registry,
        default_agent_name="chat_agent"
    )

    return orchestrator, agent


def format_conversation_context(messages):
    """
    Format the conversation context from a list of messages.

    Args:
        messages (list): A list of message objects.

    Returns:
        str: A formatted string representing the conversation context.
    """
    context = "\nPrevious conversation:\n"
    for msg in messages:
        # Access Message object attributes properly using dot notation
        sender = "User" if msg.sender == "user" else "Assistant"
        context += f"{sender}: {msg.content}\n"
    return context


def main():
    orchestrator, agent = setup_agent()
    thread_id = "interactive_chat_001"
    EphemeralMemory.store_message(thread_id=thread_id, sender="system", content=f"Starting conversation, thread ID = {thread_id}")

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
