import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Set
from dataclasses import dataclass
import re
from moya.tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

@dataclass
class DocSection:
    title: str
    content: str
    level: int
    code_blocks: List[str]
    
@dataclass
class DocumentContext:
    filename: str
    content: str
    sections: List[DocSection]
    keywords: Set[str]
    related_docs: Set[str]

@dataclass
class SearchResult:
    title: str
    content: str
    code_examples: List[str]
    source_doc: str
    relevance: float
    section_type: str  # 'definition', 'example', 'guide', 'reference'

class KnowledgeBaseTool(BaseTool):
    """Tool for searching through Moya documentation."""

    def __init__(self, name: str = "KnowledgeBaseTool", description: str = "Tool for searching Moya documentation", docs_path: str = None):
        super().__init__(name=name, description=description)
        self.docs_path = Path(docs_path) if docs_path else None
        logger.info(f"Initializing KnowledgeBaseTool with path: {self.docs_path}")
        if not self.docs_path:
            raise ValueError("docs_path is required")
        self._load_docs()

    def _parse_markdown_sections(self, content: str) -> List[DocSection]:
        sections = []
        current_section = None
        code_blocks = []

        for line in content.split('\n'):
            if line.startswith('#'):
                if current_section:
                    current_section.code_blocks = code_blocks
                    sections.append(current_section)

                level = len(line.split()[0])  # Count #'s
                title = line.lstrip('#').strip()
                current_section = DocSection(title=title, content=line + '\n', level=level, code_blocks=[], code_type=None)
                code_blocks = []
            elif line.startswith('```'):
                if line.startswith('```python'):
                    code_blocks.append('')
                continue
            elif code_blocks and not line.startswith('```'):
                if code_blocks:
                    code_blocks[-1] += line + '\n'
            elif current_section:
                current_section.content += line + '\n'

        if current_section:
            current_section.code_blocks = code_blocks
            sections.append(current_section)

        return sections

    def _build_document_context(self) -> Dict[str, DocumentContext]:
        contexts = {}
        all_keywords = set()

        # First pass: extract sections and keywords
        for doc_path in self.docs_path.glob("*.md"):
            with open(doc_path, 'r', encoding='utf-8') as f:
                content = f.read()
                sections = self._parse_markdown_sections(content)
                keywords = self._extract_keywords(content)
                all_keywords.update(keywords)

                contexts[doc_path.name] = DocumentContext(
                    filename=doc_path.name,
                    content=content,
                    sections=sections,
                    keywords=keywords,
                    related_docs=set()
                )

        # Second pass: establish relationships
        for doc_name, context in contexts.items():
            for other_doc, other_context in contexts.items():
                if doc_name != other_doc:
                    # Find relationships based on shared keywords and content references
                    shared_keywords = context.keywords & other_context.keywords
                    if len(shared_keywords) > 2:  # Arbitrary threshold
                        context.related_docs.add(other_doc)

        return contexts

    def _categorize_section(self, section: DocSection, content: str) -> str:
        """Categorize section type based on content and structure."""
        content_lower = content.lower()
        if any(term in content_lower for term in ['class', 'method', 'function', 'api']):
            return 'reference'
        if section.code_blocks:
            return 'example'
        if any(term in content_lower for term in ['is a', 'framework', 'designed', 'overview']):
            return 'definition'
        return 'guide'

    def format_structured_response(self, results: List[SearchResult]) -> str:
        """Format search results into a structured response."""
        sections = {
            'definition': [],
            'guide': [],
            'example': [],
            'reference': []
        }

        # Group results by type
        for result in results:
            sections[result.section_type].append(result)

        response = []

        # Framework Definition
        if sections['definition']:
            definitions = sections['definition']
            definition_text = "\n".join(f"{r.content}" for r in definitions)
            sources = ", ".join(f"[{r.source_doc}]" for r in definitions)
            response.append(f"a. Framework Definition: {definition_text} {sources}\n")

        # Detailed Steps/Information
        if sections['guide']:
            guides = sections['guide']
            guide_text = "\n".join(f"- {r.content}" for r in guides)
            sources = ", ".join(f"[{r.source_doc}]" for r in guides)
            response.append(f"b. Detailed Steps/Information:\n{guide_text}\n{sources}\n")

        # Code Examples
        if sections['example']:
            examples = sections['example']
            response.append("c. Example Code Blocks:")
            for ex in examples:
                response.append(f"\nFrom {ex.source_doc}:")
                for code in ex.code_examples:
                    response.append("```python\n" + code + "\n```\n")

        # Related Information
        if sections['reference']:
            refs = sections['reference']
            ref_text = "\n".join(f"- {r.content}" for r in refs)
            sources = ", ".join(f"[{r.source_doc}]" for r in refs)
            response.append(f"d. Related Information:\n{ref_text}\n{sources}\n")

        # Citations
        all_sources = set(r.source_doc for result_list in sections.values() for r in result_list)
        response.append(f"e. Citations: {', '.join(sorted(all_sources))}")

        return "\n\n".join(response)

    def search_docs(self, query: str) -> List[Tuple[str, str]]:
        """Enhanced search with cross-document referencing."""
        if not hasattr(self, 'doc_contexts'):
            self.doc_contexts = self._build_document_context()

        query = query.lower()
        query_terms = set(query.split())
        all_results: List[SearchResult] = []

        # Search across all documents
        for doc_name, context in self.doc_contexts.items():
            for section in context.sections:
                relevance = 0
                section_content = section.content.lower()

                # Calculate relevance
                term_matches = sum(term in section_content for term in query_terms)
                heading_matches = sum(term in section.title.lower() for term in query_terms)

                relevance = (term_matches * 0.6) + (heading_matches * 0.4)
                if section.code_blocks and 'example' in query:
                    relevance += 0.5

                if relevance > 0:
                    section_type = self._categorize_section(section, section_content)
                    result = SearchResult(
                        title=section.title,
                        content=section.content.strip(),
                        code_examples=section.code_blocks,
                        source_doc=doc_name,
                        relevance=relevance,
                        section_type=section_type
                    )
                    all_results.append(result)

        # Sort by relevance and format response
        all_results.sort(key=lambda x: x.relevance, reverse=True)
        response = self.format_structured_response(all_results[:10])
        return [("Combined Results", response)]

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
