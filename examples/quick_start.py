"""
quick_start.py

A minimal example that demonstrates a working Moya setup:
- An in-memory memory repository,
- A MemoryTool to handle conversation messages,
- A simple agent that uses the MemoryTool,
- An AgentRegistry and SimpleOrchestrator to handle user messages.
"""

from moya.memory.in_memory_repository import InMemoryRepository
from moya.tools.tool_registry import ToolRegistry
from moya.registry.agent_registry import AgentRegistry
from moya.orchestrators.simple_orchestrator import SimpleOrchestrator
from moya.agents.base_agent import Agent, AgentConfig
from moya.tools.ephemeral_memory import EphemeralMemory


# 1. Create a simple Agent that uses the MemoryTool
class SimpleMemoryAgent(Agent):
    def setup(self):
        # Any initialization logic goes here
        pass
    
    def handle_message(self, message: str, **kwargs) -> str:
        """
        When this agent handles a message, it will:
        - Store the user's message in the conversation memory,
        - Possibly retrieve conversation context,
        - Return a basic response.
        """
        thread_id = kwargs.get("thread_id", "default-thread")


        # Generate a naive response
        response_text = (
            f"[SimpleMemoryAgent responding to: '{message}']\n"
        )

        return response_text

    def handle_message_stream(self, message: str, **kwargs) -> str:
        """
        Stream version of handle_message - required by Agent base class.
        Yields the same response as handle_message.
        """
        response = self.handle_message(message, **kwargs)
        yield response


def main():
    # 2. Create the memory repository and tool   
    # 3. Create a tool registry, register the memory tool
    tool_registry = ToolRegistry()
    EphemeralMemory.configure_memory_tools(tool_registry)

    config = AgentConfig(
        agent_name="memory_agent",
        agent_type="BaseAgent",
        description="A simple agent that stores conversation in MemoryTool.",
        tool_registry=tool_registry
    )
    # 4. Create an agent that uses this tool registry
    agent = SimpleMemoryAgent(config=config)
    agent.setup()

    # 5. Create an agent registry and register the agent
    agent_registry = AgentRegistry()
    agent_registry.register_agent(agent)

    # 6. Create a simple orchestrator, set the default agent name
    orchestrator = SimpleOrchestrator(
        agent_registry=agent_registry,
        default_agent_name="memory_agent"
    )

    # 7. Run a quick conversation scenario
    thread_id = "my_thread_001"
    user_msg = "Hello, Moya!"
    response = orchestrator.orchestrate(thread_id=thread_id, user_message=user_msg)
    print("Agent Response 1:\n", response)

    # 8. Send another message to see the memory accumulation
    second_user_msg = "How are you handling memory right now?"
    response2 = orchestrator.orchestrate(thread_id=thread_id, user_message=second_user_msg)
    print("Agent Response 2:\n", response2)

    # 9. (Optional) Show the current conversation summary (if we want)
    summary = agent.call_tool("MemoryTool", "get_thread_summary", thread_id)
    print("\nConversation Summary:\n", summary)


if __name__ == "__main__":
    main()
