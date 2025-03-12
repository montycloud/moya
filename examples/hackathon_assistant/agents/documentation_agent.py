from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig
from typing import Optional, Dict, Any
import logging

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
            Follow these rules strictly:
            1. ONLY use information from the provided documentation
            2. If no relevant documentation is found, say "I don't have documentation about that aspect of Moya yet"
            3. Always cite which documentation file you're using in your response
            4. Never make assumptions or provide general information about Moya without documentation""",
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
            # Search documentation for relevant content
            docs = self.call_tool(
                tool_name="KnowledgeBaseTool",
                method_name="search_docs",
                query=message
            )
            
            if not docs:
                return "I don't have documentation about that aspect of Moya yet. Please check the official documentation or add this topic to our knowledge base."
            
            # Enhance prompt with found documentation
            context = "\n\nRelevant documentation:\n"
            for name, content in docs:
                context += f"\n--- {name} ---\n{content}\n"
            
            enhanced_message = f"{context}\n\nUser query: {message}\nRemember to cite which documentation file you're using in your response."
            
            # Get response using enhanced context
            return super().handle_message(enhanced_message, **kwargs)
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return f"[DocumentationAgent error: {str(e)}]"

    def handle_message_stream(self, message: str, **kwargs):
        # Similar enhancement for streaming responses
        try:
            docs = self.call_tool(
                tool_name="KnowledgeBaseTool",
                method_name="search_docs",
                query=message
            )
            
            if not docs:
                return "I don't have documentation about that aspect of Moya yet. Please check the official documentation or add this topic to our knowledge base."
            
            context = "\n\nRelevant documentation:\n"
            for name, content in docs:
                context += f"\n--- {name} ---\n{content}\n"
            
            enhanced_message = f"{context}\n\nUser query: {message}"
            
            yield from super().handle_message_stream(enhanced_message, **kwargs)
            
        except Exception as e:
            yield f"[DocumentationAgent error: {str(e)}]"
