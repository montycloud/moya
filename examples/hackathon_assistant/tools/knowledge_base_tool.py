import logging
from pathlib import Path
from typing import List, Tuple, Dict, Set
from dataclasses import dataclass
import re

from langchain_chroma import Chroma
from moya.tools.base_tool import BaseTool
from langchain_aws import BedrockEmbeddings
from langchain_core.documents import Document

embeddings = BedrockEmbeddings()
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

        # Initialize ChromaDB with better error handling
        try:
            self.vector_store = Chroma(
                collection_name="moya_docs",
                embedding_function=embeddings,
                persist_directory="/tools/chroma_langchain_db",  # Where the data is stored locally
            )

            # Initialize documents
            # self._load_docs()
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise RuntimeError(f"ChromaDB initialization failed: {e}")

    def _extract_keywords(self, content: str) -> Set[str]:
        """Extract keywords from document content."""
        keywords = set()
        
        # Key terms to look for in documentation
        important_terms = {
            'agent', 'tool', 'framework', 'setup', 'install', 'configure',
            'example', 'tutorial', 'guide', 'multi-agent', 'orchestrator',
            'create', 'implement', 'custom', 'class', 'method', 'function',
            'init', 'memory', 'registry', 'system', 'integration'
        }
        
        # Process content line by line
        for line in content.lower().split('\n'):
            # Skip empty lines and code blocks
            if not line.strip() or line.strip().startswith('```'):
                continue
                
            # Extract words and check against important terms
            words = set(re.findall(r'\w+', line))
            keywords.update(words & important_terms)
            
            # Extract method names and class names
            if 'class' in line:
                class_name = re.search(r'class\s+(\w+)', line)
                if class_name:
                    keywords.add(class_name.group(1).lower())
            
            if 'def' in line:
                method_name = re.search(r'def\s+(\w+)', line)
                if method_name:
                    keywords.add(method_name.group(1).lower())
        
        return keywords

    def _process_section_for_embedding(self, section: DocSection) -> Tuple[str, Dict]:
        """Process section content for embedding with improved code handling."""
        # Extract section context
        context_lines = []
        code_blocks = []
        current_context = []
        
        for line in section.content.split('\n'):
            if line.strip().startswith('```python'):
                # Save current context
                if current_context:
                    context_lines.append(' '.join(current_context))
                    current_context = []
                code_blocks.append('')
            elif line.strip().startswith('```') and code_blocks:
                # End of code block
                if current_context:
                    context_lines.append(' '.join(current_context))
                    current_context = []
            elif code_blocks and not line.strip().startswith('```'):
                # Inside code block
                if code_blocks:
                    code_blocks[-1] += line + '\n'
            else:
                # Regular content
                current_context.append(line.strip())
        
        # Add any remaining context
        if current_context:
            context_lines.append(' '.join(current_context))
        
        # Combine title and content with preserved code blocks
        full_content = f"{section.title}\n"
        if context_lines:
            full_content += "\n".join(context_lines)
        
        metadata = {
            "title": section.title,
            "level": section.level,
            "has_code": bool(code_blocks),
            "content_type": self._categorize_section(section, full_content),
            "code_blocks": code_blocks
        }
        
        return full_content, metadata

    def _load_docs(self):
        """Load documents and create embeddings."""
        try:
            doc_files = list(self.docs_path.glob("*.md"))
            logger.info(f"Found {len(doc_files)} documentation files")
            if not doc_files:
                raise ValueError("No documentation files found in specified path")

            # Get existing IDs
            try:
                existing_ids = self.collection.get()["ids"]
                if existing_ids:
                    # Delete existing entries properly
                    self.collection.delete(
                        ids=existing_ids
                    )
                    logger.debug("Cleared existing collection entries")
            except Exception as e:
                logger.warning(f"Error clearing collection: {e}")

            # Process all documents
            all_texts = []
            all_metadata = []
            all_ids = []
            id_counter = 0

            for doc_path in doc_files:
                try:
                    with open(doc_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        sections = self._parse_markdown_sections(content)

                        for section in sections:
                            text, metadata = self._process_section_for_embedding(section)
                            metadata["source_doc"] = doc_path.name

                            all_texts.append(text)
                            all_metadata.append(metadata)
                            all_ids.append(f"section_{id_counter}")
                            id_counter += 1
                except Exception as e:
                    logger.error(f"Error processing {doc_path}: {e}")
                    continue

            if all_texts:  # Only add if we have documents to add
                # Batch add to ChromaDB with chunking to handle large collections
                batch_size = 100
                for i in range(0, len(all_texts), batch_size):
                    end_idx = min(i + batch_size, len(all_texts))
                    self.collection.add(
                        documents=all_texts[i:end_idx],
                        metadatas=all_metadata[i:end_idx],
                        ids=all_ids[i:end_idx]
                    )

                logger.info(f"Loaded {id_counter} sections into vector database")
            else:
                logger.warning("No documents were processed successfully")

        except Exception as e:
            logger.error(f"Error loading documentation: {e}")
            raise

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

    def search_docs(self, query: str):
        """Enhanced semantic search with better code block handling."""
        try:
            
            docs = self.vector_store.similarity_search(query, k=5)
            all_results = []
            for res in docs:
                all_results.append(res.page_content)
            
            print("Documents fetched", all_results)

            return "\n".join(all_results)
            
        except Exception as e:
            logger.error(f"Error during semantic search: {e}")
            return [("Error", "Failed to search documentation")]

    def _extract_code_blocks(self, text: str) -> List[str]:
        """Extract code blocks from text."""
        code_blocks = []
        in_block = False
        current_block = []

        for line in text.split('\n'):
            if line.startswith('```python'):
                in_block = True
            elif line.startswith('```') and in_block:
                in_block = False
                if current_block:
                    code_blocks.append('\n'.join(current_block))
                current_block = []
            elif in_block:
                current_block.append(line)

        return code_blocks
