import logging
from pathlib import Path
from typing import List, Tuple
from moya.tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class KnowledgeBaseTool(BaseTool):
    """Tool for searching through Moya documentation."""
    
    def __init__(self, name: str = "KnowledgeBaseTool", description: str = "Tool for searching Moya documentation", docs_path: str = None):
        super().__init__(name=name, description=description)
        self.docs_path = Path(docs_path) if docs_path else None
        logger.info(f"Initializing KnowledgeBaseTool with path: {self.docs_path}")
        if not self.docs_path:
            raise ValueError("docs_path is required")
        self._load_docs()

    def search_docs(self, query: str) -> List[Tuple[str, str]]:
        """Search documentation with improved relevance scoring."""
        query_terms = set(query.lower().split())
        results = []
        
        # Installation-related terms
        install_terms = {'install', 'setup', 'configure', 'prerequisite', 'getting', 'started'}
        
        # Check if this is an installation query
        is_install_query = any(term in query_terms for term in install_terms)
        
        for name, doc_info in self.docs.items():
            content = doc_info['content'].lower()
            priority = doc_info['priority']
            
            # Calculate relevance score
            term_matches = sum(term in content for term in query_terms)
            section_matches = sum(term in content[:500] for term in query_terms)  # Check start of doc
            
            # Boost score for installation queries matching installation docs
            if is_install_query and name in ['basic_setup.md', 'installation.md', 'getting_started.md']:
                term_matches *= 2
            
            score = (term_matches * 0.6) + (section_matches * 0.4) + priority
            
            if score > 0:
                results.append((score, name, doc_info['content']))
                logger.debug(f"Doc {name} scored {score}")
        
        # Sort by score and return content
        results.sort(reverse=True)
        return [(name, content) for _, name, content in results[:3]]

    def _load_docs(self):
        """Pre-load all documentation files."""
        self.docs = {}
        file_priorities = {
            'basic_setup.md': 10,
            'installation.md': 10,
            'getting_started.md': 8,
            'quickstart.md': 8,
            'core_concepts.md': 5
        }

        for file_path in self.docs_path.glob("*.md"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.docs[file_path.name] = {
                        'content': content,
                        'priority': file_priorities.get(file_path.name, 1),
                        'keywords': self._extract_keywords(content)
                    }
                logger.debug(f"Loaded doc: {file_path.name} with priority {file_priorities.get(file_path.name, 1)}")
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")
