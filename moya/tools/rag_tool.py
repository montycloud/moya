"""
RAGTool for Moya.

A tool that interacts with a BaseMemoryRepository to store and retrieve
conversation data (threads, messages).
"""

from typing import Optional, List, Dict, Any
from moya.tools.tool_registry import ToolRegistry
from moya.tools.base_tool import BaseTool
from moya.memory.in_memory_repository import InMemoryRepository
from moya.conversation.thread import Thread
from moya.conversation.message import Message
from moya.vectorstore.base_vectorstore import BaseVectorStore
import json


class RAGTool:
    """
    Provides retrieval-augmented generation (RAG) capabilities, including:
      - Searching for relevant documents,
    """

    vector_store: Optional[BaseVectorStore] = None

    def __init__(self, vectordb: BaseVectorStore):
        """
        Initialize the RAGTool with a vector store.

        Parameters:
            - vectordb: The vector store used for document retrieval.
        """
        RAGTool.vector_store = vectordb

    @staticmethod
    def search_documents(
        query_text: str
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents based on the query text.

        Parameters:
            - query_text: The text to search for in the documents.

        Returns:
            A list of dictionaries containing document metadata.
        """
        if RAGTool.vector_store is None:
            raise ValueError("Vector store is not initialized. Please initialize it using the constructor.")

        # Perform the search in the vector store
        search_results = RAGTool.vector_store.search_vectorstore(query_text)
        print(f"[RAGTool] Search results: {search_results}")
        return search_results
    
    @staticmethod
    def configure_tool_registry(tool_registry: ToolRegistry):
        """
        Configure the tool registry with the RAGTool.

        Parameters:
            - tool_registry: The tool registry to configure.
        """
        rag_tool = BaseTool(
            name="RAGTool",
            description="Tool to search for relevant documents",
            function=RAGTool.search_documents,
            parameters={
                "query_text": {
                    "type": "string",
                    "description": "The text to search for in the documents.",
                },
            },
        )
        tool_registry.register_tool(rag_tool)
