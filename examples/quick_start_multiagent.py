import os
from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig
from moya.agents.remote_agent import RemoteAgent, RemoteAgentConfig
from moya.classifiers.llm_classifier import LLMClassifier
from moya.orchestrators.multi_agent_orchestrator import MultiAgentOrchestrator
from moya.registry.agent_registry import AgentRegistry
from moya.tools.ephemeral_memory import EphemeralMemory
from moya.memory.in_memory_repository import InMemoryRepository
from moya.tools.tool_registry import ToolRegistry


def setup_memory_components():
    """Set up memory components for the agents."""
    tool_registry = ToolRegistry()
    EphemeralMemory.configure_memory_tools(tool_registry)
    return tool_registry


def create_english_agent(tool_registry):
    """Create an English-speaking OpenAI agent."""
    agent_config = OpenAIAgentConfig(
        agent_name="english_agent",
        agent_type="ChatAgent",
        description="English language specialist",
        system_prompt="""You are a helpful AI assistant that always responds in English.
        You should be polite, informative, and maintain a professional tone.""",
        llm_config={
            'temperature': 0.7,
        },
        model_name="gpt-4o",
        api_key=os.getenv("OPENAI_API_KEY")
    )

    return OpenAIAgent(config=agent_config)


def create_spanish_agent(tool_registry) -> OpenAIAgent:
    """Create a Spanish-speaking OpenAI agent."""
    agent_config = OpenAIAgentConfig(
        agent_name="spanish_agent",
        agent_type="ChatAgent",
        description="Spanish language specialist that provides responses only in Spanish",
        system_prompt="""Eres un asistente de IA servicial que siempre responde en español.
        Debes ser educado, informativo y mantener un tono profesional.
        Si te piden hablar en otro idioma, declina cortésmente y continúa en español.""",
        llm_config={
            'temperature': 0.7
        },
        model_name="gpt-4o",
        api_key=os.getenv("OPENAI_API_KEY")
    )

    return OpenAIAgent(config=agent_config)



def create_remote_agent(tool_registry) -> RemoteAgent:
    """Create a remote agent for joke-related queries."""
    return RemoteAgent(
        config =RemoteAgentConfig(
            agent_name="joke_agent",
            agent_type="RemoteAgent",
            description="Remote agent specialized in telling jokes",
            base_url="http://localhost:8001",
            verify_ssl=True,
            auth_token="your-secret-token-here",
            tool_registry=tool_registry,
        )
    )



def create_classifier_agent() -> OpenAIAgent:
    """Create a classifier agent for language and task detection."""

    system_prompt="""You are a classifier. Your job is to determine the best agent based on the user's message:
        1. If the message requests or implies a need for a joke, return 'joke_agent'
        2. If the message is in English or requests English response, return 'english_agent'
        3. If the message is in Spanish or requests Spanish response, return 'spanish_agent'
        4. For any other language requests, return null
        
        Analyze both the language and intent of the message.
        Return only the agent name as specified above.""",

    agent_config = OpenAIAgentConfig(
        agent_name="classifier",
        agent_type="AgentClassifier",
        description="Language and task classifier for routing messages",
        tool_registry=None,
        model_name="gpt-4o",    
        system_prompt=system_prompt,
        api_key=os.getenv("OPENAI_API_KEY")
    )

    return OpenAIAgent(config=agent_config)



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

    EphemeralMemory.store_message(thread_id=thread_id, sender="system", content=f"thread ID: {thread_id}")

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
        EphemeralMemory.store_message(thread_id=thread_id, sender="user", content=user_message) 

        session_summary = EphemeralMemory.get_thread_summary(thread_id)
        enriched_input = f"{session_summary}\nCurrent user message: {user_message}"

        # Print Assistant prompt and get response
        print("\nAssistant: ", end="", flush=True)
        response = orchestrator.orchestrate(
            thread_id=thread_id,
            user_message=enriched_input,
            stream_callback=stream_callback
        )
        print()  # New line after response
        EphemeralMemory.store_message(thread_id=thread_id, sender="system", content=response)


if __name__ == "__main__":
    main()
