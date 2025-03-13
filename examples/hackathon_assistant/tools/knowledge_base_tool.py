import logging
from pathlib import Path
from typing import List, Tuple, Optional
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

    def get_doc(self, doc_name: str) -> Optional[str]:
        """Get specific document content by name."""
        try:
            doc_path = self.docs_path / doc_name
            if doc_path.exists():
                with open(doc_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    logger.debug(f"Successfully read document: {doc_name}")
                    return content
            logger.warning(f"Document not found: {doc_name}")
            return None
        except Exception as e:
            logger.error(f"Error reading document {doc_name}: {e}")
            return None

    def search_docs(self, query: str) -> List[Tuple[str, str]]:
        """Search documentation with improved document mapping."""
        results = []
        query_terms = set(query.lower().split())
        
        # Document mapping for different query types
        doc_mapping = {
            'installation': {
                'primary': ['installation.md'],
                'related': ['README.md'],
                'terms': {'install', 'setup', 'configure', 'pip', 'environment', 'prerequisites'}
            },
            'architecture': {
                'primary': ['core-concepts.md'],
                'related': ['README.md', 'guides.md'],
                'terms': {'architecture', 'component', 'structure', 'design', 'multi-agent'}
            },
            'api': {
                'primary': ['reference.md'],
                'related': ['guides.md'],
                'terms': {'api', 'class', 'method', 'function', 'interface'}
            },
            'usage': {
                'primary': ['guides.md'],
                'related': ['README.md'],
                'terms': {'example', 'usage', 'tutorial', 'how'}
            },
            'cloud': {
                'primary': ['cloudops.md'],
                'related': ['guides.md'],
                'terms': {'cloud', 'aws', 'azure', 'automation'}
            }
        }
        
        # Detect query types
        matched_types = []
        for doc_type, mapping in doc_mapping.items():
            if query_terms & mapping['terms']:
                matched_types.append(doc_type)
                
        try:
            # If no specific type matched, treat as general query
            if not matched_types:
                matched_types = ['general']
            
            # Process each matched type
            for doc_type in matched_types:
                # Add primary docs first
                if doc_type in doc_mapping:
                    for doc_name in doc_mapping[doc_type]['primary']:
                        content = self.get_doc(doc_name)
                        if content:
                            results.append((doc_name, content))
                    
                    # Add related docs
                    for doc_name in doc_mapping[doc_type]['related']:
                        if not any(doc[0] == doc_name for doc in results):  # Avoid duplicates
                            content = self.get_doc(doc_name)
                            if content:
                                results.append((doc_name, content))
                else:
                    # For general queries, search all docs
                    for doc_path in self.docs_path.glob("*.md"):
                        try:
                            with open(doc_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                content_lower = content.lower()
                                if any(term in content_lower for term in query_terms):
                                    results.append((doc_path.name, content))
                        except Exception as e:
                            logger.error(f"Error reading {doc_path.name}: {e}")
                            continue
                            
            logger.info(f"Found {len(results)} relevant documents for query types: {matched_types}")
            return results[:5]  # Limit to top 5 most relevant docs
            
        except Exception as e:
            logger.error(f"Error searching docs: {e}")
            return []

    def _load_docs(self):
        """Pre-load documentation files."""
        try:
            doc_files = list(self.docs_path.glob("*.md"))
            logger.info(f"Found {len(doc_files)} documentation files")
            if not doc_files:
                raise ValueError("No documentation files found in specified path")
            
            # Log available documentation
            for doc_file in doc_files:
                logger.debug(f"Available doc: {doc_file.name}")
        except Exception as e:
            logger.error(f"Error loading documentation: {e}")
            raise
