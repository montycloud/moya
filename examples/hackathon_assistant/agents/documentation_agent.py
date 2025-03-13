import logging
from typing import Optional, Dict, Any
from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig

logger = logging.getLogger(__name__)

class DocumentationAgent(OpenAIAgent):
    """Agent specialized in handling Moya framework documentation queries."""
    
    def __init__(
        self,
        agent_name: str = "documentation_agent",
        description: str = "Moya framework documentation specialist",
        config: Optional[Dict[str, Any]] = None,
        tool_registry: Optional[Any] = None,
    ):
        agent_config = OpenAIAgentConfig(
            system_prompt="""You are a Documentation Assistant for the Moya framework.
            Your primary goal is to help users understand and use Moya effectively.
            Follow these rules strictly:
            1. When asked about installation or setup, ALWAYS check 'basic_setup.md' and 'installation.md' first
            2. Provide specific, actionable steps from the documentation
            3. Include relevant code examples when available
            4. Cite the documentation files you're using
            5. If multiple docs are relevant, combine information cohesively
            6. For installation queries, always include prerequisites and basic setup steps""",
            model_name="gpt-4",
            temperature=0.7
        )
        
        super().__init__(
            agent_name=agent_name,
            description=description,
            config=config,
            tool_registry=tool_registry,
            agent_config=agent_config
        )

    def handle_message(self, message: str, **kwargs) -> str:
        """Handle user query using knowledge base."""
        try:
            # Log the incoming query
            logger.debug(f"Received query: {message}")
            
            # Search documentation with broader context
            docs = self.call_tool(
                tool_name="KnowledgeBaseTool",
                method_name="search_docs",
                query=message
            )
            
            logger.debug(f"Found {len(docs)} relevant docs")
            for name, _ in docs:
                logger.debug(f"Using doc: {name}")
            
            if not docs:
                logger.warning("No relevant documentation found")
                return "I don't have documentation about that aspect of Moya yet. Please check the official documentation or add this topic to our knowledge base."
            
            # Enhance prompt with found documentation
            context = "\n\nRelevant documentation:\n"
            for name, content in docs:
                context += f"\n--- {name} ---\n{content}\n"
            
            enhanced_message = f"""Based on the following documentation, provide a complete and practical answer to: "{message}"

{context}

Remember to:
1. Include specific steps and commands
2. Show relevant code examples
3. Mention prerequisites
4. Cite which documentation you're using"""
            
            # Get response using enhanced context
            response = super().handle_message(enhanced_message, **kwargs)
            logger.debug(f"Generated response using {len(docs)} docs")
            return response
            
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            return f"[DocumentationAgent error: {str(e)}]"
