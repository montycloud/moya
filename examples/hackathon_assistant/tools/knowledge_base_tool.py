import logging
import json
from typing import List, Optional, Tuple, Dict
from pathlib import Path
from difflib import get_close_matches
from moya.tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class KnowledgeBaseTool(BaseTool):
    def __init__(
        self,
        docs_path: str,
        name: str = "KnowledgeBaseTool",
        description: str = "Access Moya framework documentation and knowledge base."
    ):
        super().__init__(name=name, description=description)
        self.base_path = Path(docs_path)
        self.docs_cache = {}
        self.index = {}  # Search index for document contents
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._initialize_docs()

    def _initialize_docs(self) -> None:
        """Load and index all markdown files."""
        logger.info(f"Loading documentation from: {self.base_path}")
        
        loaded = 0
        for file_path in self.base_path.rglob("*.md"):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                key = file_path.stem
                self.docs_cache[key] = content
                # Create search index by words
                words = set(content.lower().split())
                for word in words:
                    if word not in self.index:
                        self.index[word] = []
                    self.index[word].append(key)
                loaded += 1
        
        logger.info(f"Loaded and indexed {loaded} documentation files")
        logger.debug(f"Available documents: {list(self.docs_cache.keys())}")

    def search_docs(self, query: str) -> List[Tuple[str, str]]:
        """Enhanced search through documentation."""
        results = []
        query = query.lower().strip()
        query_words = query.split()
        
        logger.debug(f"Searching for query: {query}")
        logger.debug(f"Query words: {query_words}")
        
        # Track matching scores for each document
        doc_scores: Dict[str, int] = {}
        
        # Search through index
        for word in query_words:
            # Find similar words in index
            matches = get_close_matches(word, self.index.keys(), n=3, cutoff=0.7)
            for match in matches:
                for doc_key in self.index[match]:
                    doc_scores[doc_key] = doc_scores.get(doc_key, 0) + 1
        
        # Sort documents by score
        matching_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Add matching documents to results
        for doc_key, score in matching_docs:
            if doc_key in self.docs_cache:
                results.append((doc_key, self.docs_cache[doc_key]))
        
        logger.info(f"Found {len(results)} relevant documents")
        if len(results) == 0:
            logger.warning("No matching documents found!")
        else:
            logger.debug(f"Matching docs: {[r[0] for r in results]}")
            
        return results

    def get_document(self, name: str) -> Optional[str]:
        """Retrieve a specific document by name."""
        return self.docs_cache.get(name)

    def list_documents(self) -> List[str]:
        """List all available documentation files."""
        return list(self.docs_cache.keys())

    def refresh(self) -> None:
        """Reload all documentation files."""
        self.docs_cache.clear()
        self._initialize_docs()
