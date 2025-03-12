import click
import logging
import os
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from moya.memory.in_memory_repository import InMemoryRepository
from moya.tools.tool_registry import ToolRegistry
from moya.tools.memory_tool import MemoryTool
from moya.registry.agent_registry import AgentRegistry
from moya.orchestrators.simple_orchestrator import SimpleOrchestrator

from ..agents.documentation_agent import DocumentationAgent
from ..tools.knowledge_base_tool import KnowledgeBaseTool

logger = logging.getLogger(__name__)
console = Console()

def setup_agent():
    """Initialize the documentation agent with memory capabilities."""
    # Get package directory path
    package_dir = Path(__file__).parent.parent
    docs_path = package_dir / "data" / "documentation"
    
    logger.info(f"Setting up agent with docs path: {docs_path}")
    
    # Set up memory components
    memory_repo = InMemoryRepository()
    memory_tool = MemoryTool(memory_repository=memory_repo)
    tool_registry = ToolRegistry()
    tool_registry.register_tool(memory_tool)

    # Set up knowledge base
    knowledge_tool = KnowledgeBaseTool(docs_path=str(docs_path))
    tool_registry.register_tool(knowledge_tool)
    
    # Ensure documentation exists
    if not list(docs_path.rglob("*.md")):
        logger.warning("No documentation files found!")
        default_doc = docs_path / "moya_overview.md"
        if not default_doc.exists():
            logger.info("Creating default documentation...")
            default_doc.parent.mkdir(parents=True, exist_ok=True)
            with open(default_doc, 'w', encoding='utf-8') as f:
                f.write("""# Moya Framework\n\nMOYA is a reference implementation of the research paper titled "Engineering LLM Powered Multi-agent Framework for Autonomous CloudOps". The framework provides a flexible and extensible architecture for creating, managing, and orchestrating multiple AI agents to handle various tasks autonomously.""")

    # Create documentation agent
    agent = DocumentationAgent(tool_registry=tool_registry)
    agent.setup()

    # Set up registry and orchestrator
    registry = AgentRegistry()
    registry.register_agent(agent)
    orchestrator = SimpleOrchestrator(
        agent_registry=registry,
        default_agent_name="documentation_agent"
    )

    return orchestrator, agent

@click.group()
def cli():
    """Moya Hackathon Assistant - Your guide to the framework and hackathon."""
    pass

@cli.command()
def chat():
    """Start an interactive chat session with the assistant."""
    orchestrator, agent = setup_agent()
    thread_id = "hackathon_chat"

    console.print(Panel.fit(
        "[bold green]Welcome to Moya Hackathon Assistant![/]\n"
        "I can help you with:\n"
        "• Framework documentation\n"
        "• Technical questions\n"
        "• Best practices\n"
        "(Type 'exit' to end the session)"
    ))

    while True:
        user_input = console.input("\n[bold blue]You:[/] ").strip()
        
        if user_input.lower() in ['exit', 'quit']:
            console.print("\n[bold green]Goodbye! Happy hacking![/]")
            break

        try:
            # Store user message
            agent.call_tool(
                tool_name="MemoryTool",
                method_name="store_message",
                thread_id=thread_id,
                sender="user",
                content=user_input
            )

            console.print("\n[bold green]Assistant:[/] ", end="")
            
            def stream_callback(chunk):
                console.print(chunk, end="")

            response = orchestrator.orchestrate(
                thread_id=thread_id,
                user_message=user_input,
                stream_callback=stream_callback
            )
            console.print()

        except Exception as e:
            console.print(f"\n[bold red]Error:[/] {str(e)}")

if __name__ == "__main__":
    cli()
