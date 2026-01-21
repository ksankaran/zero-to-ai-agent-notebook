# From: Zero to AI Agent, Chapter 20, Section 20.3
# File: src/caspar/knowledge/__init__.py

"""CASPAR Knowledge Base Module"""

from .loader import KnowledgeLoader
from .retriever import KnowledgeRetriever, get_retriever

__all__ = ["KnowledgeLoader", "KnowledgeRetriever", "get_retriever"]
