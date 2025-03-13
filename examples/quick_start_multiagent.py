from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig
from moya.agents.remote_agent import RemoteAgent, RemoteAgentConfig
from moya.classifiers.llm_classifier import LLMClassifier
from moya.orchestrators.multi_agent_orchestrator import MultiAgentOrchestrator
from moya.registry.agent_registry import AgentRegistry
from moya.tools.memory_tool import MemoryTool
from moya.memory.in_memory_repository import InMemoryRepository
from moya.tools.tool_registry import ToolRegistry


def setup_memory_components():
    """Set up memory components for the agents."""
    memory_repo = InMemoryRepository()
    memory_tool = MemoryTool(memory_repository=memory_repo)
    tool_registry = ToolRegistry()
    tool_registry.register_tool(memory_tool)
    return tool_registry


def create_english_agent(tool_registry):
    """Create an English-speaking OpenAI agent."""
    agent_config = OpenAIAgentConfig(
        system_prompt="""You are a helpful AI assistant that always responds in English.
        You should be polite, informative, and maintain a professional tone.""",
        model_name="gpt-4o",
        temperature=0.7
    )

    agent = OpenAIAgent(
        agent_name="english_agent",
        description="English language specialist",
        config=None,
        tool_registry=tool_registry,
        agent_config=agent_config
    )
    agent.setup()
    return agent


def create_spanish_agent(tool_registry) -> OpenAIAgent:
    """Create a Spanish-speaking OpenAI agent."""
    agent_config = OpenAIAgentConfig(
        system_prompt="""Eres un asistente de IA servicial que siempre responde en español.
        Debes ser educado, informativo y mantener un tono profesional.
        Si te piden hablar en otro idioma, declina cortésmente y continúa en español.""",
        model_name="gpt-4o",
        temperature=0.7
    )

    agent = OpenAIAgent(
        agent_name="spanish_agent",
        description="Spanish language specialist that provides responses only in Spanish",
        config=None,
        tool_registry=tool_registry,
        agent_config=agent_config
    )
    agent.setup()
    return agent


def create_remote_agent(tool_registry) -> RemoteAgent:
    """Create a remote agent for joke-related queries."""
    agent = RemoteAgent(
        agent_name="joke_agent",
        description="Remote agent specialized in telling jokes",
        agent_config=RemoteAgentConfig(
            base_url="http://localhost:8001",
            verify_ssl=True,
            auth_token="your-secret-token-here"
        )
    )
    agent.setup()
    return agent


def create_classifier_agent() -> OpenAIAgent:
    """Create a classifier agent for language and task detection."""
    agent_config = OpenAIAgentConfig(
        system_prompt="""You are a classifier. Your job is to determine the best agent based on the user's message:
        1. If the message requests or implies a need for a joke, return 'joke_agent'
        2. If the message is in English or requests English response, return 'english_agent'
        3. If the message is in Spanish or requests Spanish response, return 'spanish_agent'
        4. For any other language requests, return null
        
        Analyze both the language and intent of the message.
        Return only the agent name as specified above.""",
        model_name="gpt-4o"
    )

    agent = OpenAIAgent(
        agent_name="classifier",
        description="Language and task classifier for routing messages",
        config=None,
        tool_registry=None,
        agent_config=agent_config
    )
    agent.setup()
    return agent


def setup_orchestrator():
    """Set up the multi-agent orchestrator with all components."""
    # Set up shared components
    tool_registry = setup_memory_components()

    # Create agents
    english_agent = create_english_agent(tool_registry)
    spanish_agent = create_spanish_agent(tool_registry)
    joke_agent = create_remote_agent(tool_registry)
    classifier_agent = create_classifier_agent()

    # Set up agent registry
    registry = AgentRegistry()
    registry.register_agent(english_agent)
    registry.register_agent(spanish_agent)
    registry.register_agent(joke_agent)

    # Create and configure the classifier
    classifier = LLMClassifier(classifier_agent, default_agent="english_agent")

    # Create the orchestrator
    orchestrator = MultiAgentOrchestrator(
        agent_registry=registry,
        classifier=classifier,
        default_agent_name=None
    )

    return orchestrator


def format_conversation_context(messages):
    """Format conversation history for context."""
    context = "\nPrevious conversation:\n"
    for msg in messages:
        sender = "User" if msg.sender == "user" else "Assistant"
        context += f"{sender}: {msg.content}\n"
    return context


def main():
    # Set up the orchestrator and all components
    orchestrator = setup_orchestrator()
    thread_id = "test_conversation"

    print("Starting multi-agent chat (type 'exit' to quit)")
    print("You can chat in English or Spanish, or request responses in either language.")
    print("-" * 50)

    def stream_callback(chunk):
        print(chunk, end="", flush=True)

    while True:
        # Get user input
        user_message = input("\nYou: ").strip()

        # Check for exit condition
        if user_message.lower() == 'exit':
            print("\nGoodbye!")
            break

        # Get available agents
        agents = orchestrator.agent_registry.list_agents()
        if not agents:
            print("\nNo agents available!")
            continue

        # Get the last used agent or default to the first one
        last_agent = orchestrator.agent_registry.get_agent(agents[0].name)

        # Store the user message first
        if last_agent.tool_registry:
            try:
                last_agent.call_tool(
                    tool_name="MemoryTool",
                    method_name="store_message",
                    thread_id=thread_id,
                    sender="user",
                    content=user_message
                )
            except Exception as e:
                print(f"Error storing user message: {e}")

        # Get conversation context
        previous_messages = last_agent.get_last_n_messages(thread_id, n=5)

        # Add context to the user's message if there are previous messages
        if previous_messages:
            context = format_conversation_context(previous_messages)
            enhanced_input = f"{context}\nCurrent user message: {user_message}"
        else:
            enhanced_input = user_message

        # Print Assistant prompt and get response
        print("\nAssistant: ", end="", flush=True)
        response = orchestrator.orchestrate(
            thread_id=thread_id,
            user_message=enhanced_input,
            stream_callback=stream_callback
        )
        print()  # New line after response


if __name__ == "__main__":
    main()
