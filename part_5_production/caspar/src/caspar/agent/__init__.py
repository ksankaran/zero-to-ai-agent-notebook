# From: Zero to AI Agent, Chapter 20, Section 20.4
# File: src/caspar/agent/__init__.py

"""CASPAR Agent Module - The core intelligence of the customer service system."""

from .state import AgentState, create_initial_state, ConversationMetadata
from .graph import build_graph, create_agent
from .nodes import (
    classify_intent,
    handle_faq,
    handle_order_inquiry,
    handle_account,
    handle_complaint,
    handle_general,
    respond,
)
from .nodes_handoff_update import check_sentiment, human_handoff

__all__ = [
    # State
    "AgentState", 
    "create_initial_state", 
    "ConversationMetadata",
    # Graph
    "build_graph", 
    "create_agent",
    # Nodes
    "classify_intent", 
    "handle_faq", 
    "handle_order_inquiry", 
    "handle_account",
    "handle_complaint", 
    "handle_general", 
    "check_sentiment", 
    "respond", 
    "human_handoff",
]
