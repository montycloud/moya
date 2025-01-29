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
from moya.tools.memory_tool import MemoryTool
from moya.registry.agent_registry import AgentRegistry
from moya.orchestrators.simple_orchestrator import SimpleOrchestrator
from moya.agents.base_agent import Agent


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

        # Store the incoming message
        self.call_tool(
            tool_name="MemoryTool",
            method_name="store_message",
            thread_id=thread_id,
            sender="user",
            content=message
        )

        # Let's also store the fact that the agent has "seen" this message
        # Or we can read the last 3 messages:
        last_3_msgs = self.call_tool(
            tool_name="MemoryTool",
            method_name="get_last_n_messages",
            thread_id=thread_id,
            n=3
        )

        # Generate a naive response
        response_text = (
            f"[SimpleMemoryAgent responding to: '{message}']\n"
            f"I see {len(last_3_msgs)} recent messages in this thread.\n"
            f"Thanks for sharing!"
        )

        # Store the agent's response in memory
        self.call_tool(
            tool_name="MemoryTool",
            method_name="store_message",
            thread_id=thread_id,
            sender=self.agent_name,
            content=response_text
        )

        return response_text


def main():
    # 2. Create the memory repository and tool
    memory_repo = InMemoryRepository()
    memory_tool = MemoryTool(memory_repository=memory_repo)

    # 3. Create a tool registry, register the memory tool
    tool_registry = ToolRegistry()
    tool_registry.register_tool(memory_tool)

    # 4. Create an agent that uses this tool registry
    agent = SimpleMemoryAgent(
        agent_name="memory_agent",
        agent_type="BaseAgent",
        description="A simple agent that stores conversation in MemoryTool.",
        tool_registry=tool_registry
    )
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
