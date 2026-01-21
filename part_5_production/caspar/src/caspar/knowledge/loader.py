# From: Zero to AI Agent, Chapter 20, Section 20.3
# File: src/caspar/knowledge/loader.py

"""
Knowledge Base Loader

Loads and processes knowledge base documents from markdown files,
splits them into chunks, and prepares them for embedding.
"""

from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from caspar.config import get_logger

logger = get_logger(__name__)


class KnowledgeLoader:
    """
    Loads knowledge base content from markdown files.
    
    The loader reads all .md files from the knowledge base directory,
    splits them into manageable chunks, and prepares them for embedding.
    """
    
    def __init__(
        self,
        knowledge_dir: str = "data/knowledge_base",
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ):
        """
        Initialize the knowledge loader.
        
        Args:
            knowledge_dir: Path to directory containing .md files
            chunk_size: Maximum size of each text chunk
            chunk_overlap: Overlap between chunks to preserve context
        """
        self.knowledge_dir = Path(knowledge_dir)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""]
        )
    
    def load_documents(self) -> list[Document]:
        """
        Load all markdown files from the knowledge directory.
        
        Returns:
            List of Document objects, each representing a chunk
        """
        if not self.knowledge_dir.exists():
            logger.warning(
                "knowledge_dir_not_found",
                path=str(self.knowledge_dir)
            )
            return []
        
        documents = []
        md_files = list(self.knowledge_dir.glob("*.md"))
        
        logger.info(
            "loading_knowledge_base",
            file_count=len(md_files),
            directory=str(self.knowledge_dir)
        )
        
        for file_path in md_files:
            try:
                content = file_path.read_text(encoding="utf-8")
                
                # Create document with metadata
                doc = Document(
                    page_content=content,
                    metadata={
                        "source": file_path.name,
                        "category": self._extract_category(file_path.name)
                    }
                )
                documents.append(doc)
                
                logger.debug(
                    "loaded_file",
                    file=file_path.name,
                    size=len(content)
                )
                
            except Exception as e:
                logger.error(
                    "file_load_error",
                    file=file_path.name,
                    error=str(e)
                )
        
        return documents
    
    def load_and_split(self) -> list[Document]:
        """
        Load documents and split them into chunks.
        
        Returns:
            List of chunked Document objects
        """
        documents = self.load_documents()
        
        if not documents:
            return []
        
        chunks = self.text_splitter.split_documents(documents)
        
        logger.info(
            "documents_chunked",
            original_docs=len(documents),
            chunks=len(chunks),
            avg_chunk_size=sum(len(c.page_content) for c in chunks) // len(chunks)
        )
        
        return chunks
    
    def _extract_category(self, filename: str) -> str:
        """Extract category from filename for filtering."""
        # Remove .md extension and use as category
        name = filename.replace(".md", "").lower()
        
        category_map = {
            "policies": "policy",
            "products": "product",
            "faq": "faq",
            "troubleshooting": "troubleshooting"
        }
        
        return category_map.get(name, "general")
