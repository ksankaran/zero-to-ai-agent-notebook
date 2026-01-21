# From: Zero to AI Agent, Chapter 20, Section 20.2
# File: src/caspar/agent/state.py

"""
CASPAR Agent State Definition

This module defines the state schema that flows through the LangGraph agent.
Every node reads from and writes to this shared state.
"""

from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from datetime import datetime, timezone


# Message handling - LangGraph's add_messages reducer handles conversation history
class AgentState(TypedDict):
    """
    The state that flows through the CASPAR agent graph.
    
    This is a TypedDict because LangGraph requires it for state management.
    Each field represents a piece of information that nodes can read or update.
    """
    
    # Conversation messages - uses add_messages reducer to append new messages
    messages: Annotated[list, add_messages]
    
    # Customer identification
    customer_id: str | None
    conversation_id: str
    
    # Intent classification results
    intent: str | None  # faq, order_inquiry, account, complaint, general, handoff_request
    confidence: float | None
    
    # Sentiment tracking
    sentiment_score: float | None  # -1.0 (very negative) to 1.0 (very positive)
    frustration_level: Literal["low", "medium", "high"] | None
    
    # Context from tools and knowledge base
    retrieved_context: str | None  # RAG results
    order_info: dict | None  # From order lookup tool
    ticket_id: str | None  # If a support ticket was created
    
    # Routing and flow control
    needs_escalation: bool
    escalation_reason: str | None
    
    # Metadata
    turn_count: int
    created_at: str
    last_updated: str


class ConversationMetadata(BaseModel):
    """Metadata about a conversation for logging and analytics."""
    
    conversation_id: str
    customer_id: str | None = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: datetime | None = None
    total_turns: int = 0
    intents_detected: list[str] = Field(default_factory=list)
    escalated: bool = False
    escalation_reason: str | None = None
    sentiment_trajectory: list[float] = Field(default_factory=list)
    resolution_status: Literal["resolved", "escalated", "abandoned", "ongoing"] = "ongoing"


def create_initial_state(
    conversation_id: str,
    customer_id: str | None = None
) -> AgentState:
    """
    Create a fresh state for a new conversation.
    
    Args:
        conversation_id: Unique identifier for this conversation
        customer_id: Optional customer identifier if known
        
    Returns:
        Initial AgentState with default values
    """
    now = datetime.now(timezone.utc).isoformat()
    
    return AgentState(
        messages=[],
        customer_id=customer_id,
        conversation_id=conversation_id,
        intent=None,
        confidence=None,
        sentiment_score=None,
        frustration_level=None,
        retrieved_context=None,
        order_info=None,
        ticket_id=None,
        needs_escalation=False,
        escalation_reason=None,
        turn_count=0,
        created_at=now,
        last_updated=now,
    )
