# From: Zero to AI Agent, Chapter 20, Section 20.3
# File: scripts/build_knowledge_base.py

"""
Build and test the CASPAR knowledge base.

This script:
1. Loads all knowledge documents
2. Creates embeddings and stores in ChromaDB
3. Tests retrieval with sample queries

Note: Make sure you've run 'pip install -e .' from the project root first!
"""

import sys
from pathlib import Path

from caspar.config import setup_logging, get_logger
from caspar.knowledge import KnowledgeLoader, KnowledgeRetriever

setup_logging()
logger = get_logger(__name__)


def build_knowledge_base():
    """Build the ChromaDB knowledge base from markdown files."""
    
    print("=" * 60)
    print("📚 Building CASPAR Knowledge Base")
    print("=" * 60)
    
    # Check that knowledge files exist
    kb_path = Path("data/knowledge_base")
    if not kb_path.exists():
        print(f"❌ Knowledge base directory not found: {kb_path}")
        print("   Create the directory and add your .md files")
        return False
    
    md_files = list(kb_path.glob("*.md"))
    print(f"\n📄 Found {len(md_files)} markdown files:")
    for f in md_files:
        size = f.stat().st_size / 1024
        print(f"   • {f.name} ({size:.1f} KB)")
    
    if not md_files:
        print("❌ No .md files found in knowledge base directory")
        return False
    
    # Load and preview documents
    print("\n📖 Loading documents...")
    loader = KnowledgeLoader()
    chunks = loader.load_and_split()
    
    print(f"✅ Created {len(chunks)} chunks")
    print(f"   Average chunk size: {sum(len(c.page_content) for c in chunks) // len(chunks)} characters")
    
    # Build vector store
    print("\n🔨 Building vector store...")
    retriever = KnowledgeRetriever()
    retriever.initialize(force_reload=True)
    
    print("✅ Vector store created and persisted")
    
    return True


def test_retrieval():
    """Test retrieval with sample queries."""
    
    print("\n" + "=" * 60)
    print("🧪 Testing Knowledge Retrieval")
    print("=" * 60)
    
    retriever = KnowledgeRetriever()
    retriever.initialize()
    
    test_queries = [
        "What is your return policy?",
        "How do I track my order?",
        "My laptop won't turn on, what should I do?",
        "What laptops do you sell?",
        "How long does shipping take?",
        "Can I pay with PayPal?",
        "My earbuds won't connect to my phone",
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        print("-" * 50)
        
        results = retriever.retrieve_with_scores(query, k=2)
        
        for doc, score in results:
            source = doc.metadata.get("source", "unknown")
            preview = doc.page_content[:100].replace("\n", " ")
            print(f"   📄 [{source}] (score: {score:.3f})")
            print(f"      {preview}...")
    
    print("\n✅ Retrieval tests complete!")


def interactive_test():
    """Interactive mode for testing queries."""
    
    print("\n" + "=" * 60)
    print("🔍 Interactive Knowledge Search")
    print("=" * 60)
    print("Type your questions to test retrieval. Type 'quit' to exit.\n")
    
    retriever = KnowledgeRetriever()
    retriever.initialize()
    
    while True:
        query = input("Your question: ").strip()
        
        if query.lower() == "quit":
            break
        
        if not query:
            continue
        
        results = retriever.retrieve_with_scores(query, k=3)
        
        print(f"\n📚 Top {len(results)} results:\n")
        
        for i, (doc, score) in enumerate(results, 1):
            source = doc.metadata.get("source", "unknown")
            category = doc.metadata.get("category", "general")
            print(f"Result {i} [{source} - {category}] (score: {score:.3f}):")
            print("-" * 40)
            print(doc.page_content[:300])
            print("..." if len(doc.page_content) > 300 else "")
            print()


def main():
    """Run all knowledge base operations."""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Build and test CASPAR knowledge base")
    parser.add_argument("--build", action="store_true", help="Build the vector store")
    parser.add_argument("--test", action="store_true", help="Run retrieval tests")
    parser.add_argument("--interactive", action="store_true", help="Interactive query mode")
    
    args = parser.parse_args()
    
    # Default to build + test if no args
    if not any([args.build, args.test, args.interactive]):
        args.build = True
        args.test = True
    
    if args.build:
        success = build_knowledge_base()
        if not success:
            sys.exit(1)
    
    if args.test:
        test_retrieval()
    
    if args.interactive:
        interactive_test()
    
    print("\n🎉 Done!")


if __name__ == "__main__":
    main()
