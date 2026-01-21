# From: Zero to AI Agent, Chapter 20, Section 20.3
# File: src/caspar/knowledge/retriever.py

"""
Knowledge Base Retriever

Handles embedding, storage, and retrieval of knowledge base content
using ChromaDB for vector similarity search.
"""

from pathlib import Path
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from caspar.config import settings, get_logger
from .loader import KnowledgeLoader

logger = get_logger(__name__)


class KnowledgeRetriever:
    """
    Retrieves relevant knowledge for customer queries.
    
    Uses ChromaDB for vector storage and OpenAI embeddings for
    semantic similarity search.
    """
    
    def __init__(
        self,
        persist_directory: str | None = None,
        collection_name: str = "techflow_knowledge"
    ):
        """
        Initialize the knowledge retriever.
        
        Args:
            persist_directory: Where to store ChromaDB data (None for in-memory)
            collection_name: Name of the ChromaDB collection
        """
        self.persist_directory = persist_directory or settings.chroma_persist_directory
        self.collection_name = collection_name
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            api_key=settings.openai_api_key,
            model="text-embedding-3-small"  # Fast and cost-effective
        )
        
        self.vectorstore: Chroma | None = None
        self._initialized = False
    
    def initialize(self, force_reload: bool = False) -> None:
        """
        Initialize the vector store, loading documents if needed.
        
        Args:
            force_reload: If True, reload documents even if store exists
        """
        persist_path = Path(self.persist_directory)
        
        # Check if we already have a persisted store
        if persist_path.exists() and not force_reload:
            logger.info(
                "loading_existing_vectorstore",
                path=str(persist_path)
            )
            self.vectorstore = Chroma(
                persist_directory=str(persist_path),
                collection_name=self.collection_name,
                embedding_function=self.embeddings
            )
            self._initialized = True
            
            # Log collection stats
            collection = self.vectorstore._collection
            count = collection.count()
            logger.info("vectorstore_loaded", document_count=count)
            return
        
        # Load and embed documents
        logger.info("creating_new_vectorstore")
        
        loader = KnowledgeLoader()
        documents = loader.load_and_split()
        
        if not documents:
            logger.warning("no_documents_to_embed")
            # Create empty store
            self.vectorstore = Chroma(
                persist_directory=str(persist_path),
                collection_name=self.collection_name,
                embedding_function=self.embeddings
            )
            self._initialized = True
            return
        
        # Create vectorstore with documents
        self.vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=self.embeddings,
            persist_directory=str(persist_path),
            collection_name=self.collection_name
        )
        
        self._initialized = True
        logger.info(
            "vectorstore_created",
            document_count=len(documents),
            path=str(persist_path)
        )
    
    def retrieve(
        self,
        query: str,
        k: int | None = None,
        category_filter: str | None = None
    ) -> list[Document]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: The search query
            k: Number of documents to retrieve (default from settings)
            category_filter: Optional category to filter by
            
        Returns:
            List of relevant Document objects
        """
        if not self._initialized:
            self.initialize()
        
        if not self.vectorstore:
            logger.warning("vectorstore_not_available")
            return []
        
        k = k or settings.retrieval_k
        
        # Build filter if category specified
        where_filter = None
        if category_filter:
            where_filter = {"category": category_filter}
        
        logger.debug(
            "retrieving_documents",
            query=query[:50],
            k=k,
            filter=category_filter
        )
        
        # Perform similarity search
        if where_filter:
            docs = self.vectorstore.similarity_search(
                query=query,
                k=k,
                filter=where_filter
            )
        else:
            docs = self.vectorstore.similarity_search(
                query=query,
                k=k
            )
        
        logger.info(
            "documents_retrieved",
            query=query[:50],
            count=len(docs)
        )
        
        return docs
    
    def retrieve_with_scores(
        self,
        query: str,
        k: int | None = None
    ) -> list[tuple[Document, float]]:
        """
        Retrieve documents with similarity scores.
        
        Useful for debugging and understanding retrieval quality.
        
        Args:
            query: The search query
            k: Number of documents to retrieve
            
        Returns:
            List of (Document, score) tuples, lower score = more similar
        """
        if not self._initialized:
            self.initialize()
        
        if not self.vectorstore:
            return []
        
        k = k or settings.retrieval_k
        
        results = self.vectorstore.similarity_search_with_score(
            query=query,
            k=k
        )
        
        return results
    
    def format_context(self, documents: list[Document]) -> str:
        """
        Format retrieved documents into a context string for the LLM.
        
        Args:
            documents: List of retrieved documents
            
        Returns:
            Formatted context string
        """
        if not documents:
            return "No relevant information found in knowledge base."
        
        context_parts = []
        
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get("source", "unknown")
            category = doc.metadata.get("category", "general")
            
            context_parts.append(
                f"[Source {i}: {source} ({category})]\n{doc.page_content}"
            )
        
        return "\n\n---\n\n".join(context_parts)


# Singleton instance for easy access
_retriever_instance: KnowledgeRetriever | None = None


def get_retriever() -> KnowledgeRetriever:
    """Get or create the global knowledge retriever instance."""
    global _retriever_instance
    
    if _retriever_instance is None:
        _retriever_instance = KnowledgeRetriever()
    
    return _retriever_instance
