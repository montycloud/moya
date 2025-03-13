import logging
from pathlib import Path
from typing import List, Tuple
from moya.tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class KnowledgeBaseTool(BaseTool):
    """Tool for searching through Moya documentation."""
    
    def __init__(self, docs_path: str):
        super().__init__(
            name="KnowledgeBaseTool",
            description="Tool for searching Moya documentation"
        )
        self.docs_path = Path(docs_path)
        logger.info(f"Initialized KnowledgeBaseTool with path: {self.docs_path}")
        self._load_docs()

    def _load_docs(self):
        """Pre-load all documentation files."""
        self.docs = {}
        for file_path in self.docs_path.glob("*.md"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.docs[file_path.name] = f.read()
                logger.debug(f"Loaded documentation: {file_path.name}")
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")

    def search_docs(self, query: str) -> List[Tuple[str, str]]:
        """Search documentation for relevant content."""
        query_terms = set(query.lower().split())
        results = []
        
        for name, content in self.docs.items():
            content_lower = content.lower()
            # Simple relevance scoring
            score = sum(1 for term in query_terms if term in content_lower)
            if score > 0:
                results.append((name, content))
                logger.debug(f"Found relevant doc: {name} (score: {score})")
        
        return sorted(results, key=lambda x: len(x[1]))[:3]  # Return top 3 most relevant
