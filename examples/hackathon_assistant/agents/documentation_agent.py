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
            system_prompt="""You are a Documentation Assistant for the Moya framework, which is a framework for CloudOps automation using AI agents.
            Your primary goal is to help users understand and use Moya effectively.
            
            CORE RULES:
            1. NEVER generate responses without documentation evidence
            2. NEVER mix Moya with other frameworks or projects
            3. ALWAYS include specific examples when they exist in the documentation
            4. Response Format:
               a. Start with clear framework definition from README.md
               b. Give detailed steps/information from primary doc
               c. Show example code blocks from docs if they exist
               d. Add related information from other docs
               e. Cite [filename] for EVERY section
            5. For code examples:
               - Include complete code blocks from docs
               - Keep code formatting intact
               - Show setup AND usage examples
            6. If information is missing, say: "The documentation does not cover [aspect]"
            7. Never infer or add information beyond the docs""",
            model_name="gpt-4o",
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
        """Handle user queries by searching documentation."""
        try:
            logger.info(f"Processing query: {message}")
            docs_to_check = []
            
            # Always get README for framework definition
            readme_content = self.call_tool(
                tool_name="KnowledgeBaseTool",
                method_name="get_doc",
                doc_name="README.md"
            )
            if readme_content:
                docs_to_check.append(("README.md", readme_content))
                logger.debug("Added README.md")
            
            # Search with query type detection
            message_lower = message.lower()
            
            # Installation queries
            if any(term in message_lower for term in ['install', 'setup', 'configure', 'pip']):
                logger.info("Detected installation query")
                install_content = self.call_tool(
                    tool_name="KnowledgeBaseTool",
                    method_name="get_doc",
                    doc_name="installation.md"
                )
                if install_content:
                    docs_to_check.insert(1, ("installation.md", install_content))
                    logger.debug("Added installation.md")
            
            # Get examples from guides
            guides_content = self.call_tool(
                tool_name="KnowledgeBaseTool",
                method_name="get_doc",
                doc_name="guides.md"
            )
            if guides_content:
                docs_to_check.append(("guides.md", guides_content))
                logger.debug("Added guides.md")
            
            # Get remaining relevant docs
            additional_docs = self.call_tool(
                tool_name="KnowledgeBaseTool",
                method_name="search_docs",
                query=message
            )
            
            # Add any new docs not already included
            seen_docs = {doc[0] for doc in docs_to_check}
            for doc_name, content in additional_docs:
                if doc_name not in seen_docs:
                    docs_to_check.append((doc_name, content))
                    seen_docs.add(doc_name)
            
            logger.info(f"Found {len(docs_to_check)} relevant documents")
            
            if not docs_to_check:
                return "I don't have documentation about that aspect of Moya yet."

            # Format documentation context with emphasis on examples
            context = "\n\nRelevant Documentation:\n"
            for name, content in docs_to_check:
                context += f"\n=== {name} ===\n{content}\n"

            enhanced_message = f"""Based STRICTLY on these documentation sections, explain: "{message}"

{context}

RESPONSE REQUIREMENTS:
1. Start with framework definition from README.md
2. Give step-by-step instructions or explanations from the primary relevant doc
3. Include ALL relevant code examples - keep them complete and properly formatted
4. [filename] Citations before EVERY section of information
5. If showing examples, include both setup AND usage code
6. If any aspect is missing in docs, say: "The documentation does not cover [aspect]"
7. NEVER add information beyond what's in the documentation"""

            logger.info("Generating response using documentation context")
            return super().handle_message(enhanced_message, **kwargs)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return f"Error accessing documentation: {str(e)}"
        
    def handle_documentation_query(self, message: str, **kwargs):
        """
        Calls OpenAI ChatCompletion to handle the user's message with streaming support.
        """
        # Starting streaming response from OpenAIAgent
        try:
            # Get documents from the KnowledgeBaseTool
            documents = self.call_tool(
                tool_name="KnowledgeBaseTool",
                method_name="search_docs",
                query=message
            )
            self.system_prompt = self.system_prompt + "\n" + "Here are the documents to refer: \n" + str(documents)
            for chunk in self.handle_message_stream(message):
                yield chunk
        except Exception as e:
            error_message = f"[OpenAIAgent error: {str(e)}]"
            print(error_message)
            yield error_message