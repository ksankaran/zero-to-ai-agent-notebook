# From: Zero to AI Agent, Chapter 20, Section 20.3
# File: src/caspar/agent/graph.py

"""
CASPAR Agent Graph - The workflow that connects all components.

This module defines the StateGraph that orchestrates the agent's behavior,
routing messages through classification, handling, and response generation.
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from caspar.config import get_logger
from .state import AgentState
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

logger = get_logger(__name__)


# ════════════════════════════════════════════════════════════════════════════
# Routing Functions
# ════════════════════════════════════════════════════════════════════════════

def route_by_intent(state: AgentState) -> str:
    """Route to the appropriate handler based on classified intent."""
    intent = state.get("intent", "general")
    
    routes = {
        "faq": "handle_faq",
        "order_inquiry": "handle_order_inquiry",
        "account": "handle_account",
        "complaint": "handle_complaint",
        "handoff_request": "human_handoff",
        "general": "handle_general",
    }
    
    return routes.get(intent, "handle_general")


def route_after_sentiment(state: AgentState) -> str:
    """Route based on sentiment analysis - escalate if needed."""
    if state.get("needs_escalation") and state.get("intent") != "handoff_request":
        return "human_handoff"
    return "respond"


# ════════════════════════════════════════════════════════════════════════════
# Graph Builder
# ════════════════════════════════════════════════════════════════════════════

def build_graph() -> StateGraph:
    """
    Build the CASPAR agent graph.
    
    The flow is:
    1. classify_intent: Determine what the customer needs
    2. handle_*: Process the specific type of request
    3. check_sentiment: Analyze customer emotion
    4. respond OR human_handoff: Generate response or escalate
    
    Returns:
        StateGraph: The uncompiled graph (call .compile() to use)
    """
    graph = StateGraph(AgentState)
    
    # Add all nodes
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("handle_faq", handle_faq)
    graph.add_node("handle_order_inquiry", handle_order_inquiry)
    graph.add_node("handle_account", handle_account)
    graph.add_node("handle_complaint", handle_complaint)
    graph.add_node("handle_general", handle_general)
    graph.add_node("check_sentiment", check_sentiment)
    graph.add_node("respond", respond)
    graph.add_node("human_handoff", human_handoff)
    
    # Set entry point
    graph.set_entry_point("classify_intent")
    
    # Route by intent after classification
    graph.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            "handle_faq": "handle_faq",
            "handle_order_inquiry": "handle_order_inquiry",
            "handle_account": "handle_account",
            "handle_complaint": "handle_complaint",
            "handle_general": "handle_general",
            "human_handoff": "human_handoff",
        }
    )
    
    # All handlers go to sentiment check
    for handler in ["handle_faq", "handle_order_inquiry", "handle_account", 
                    "handle_complaint", "handle_general"]:
        graph.add_edge(handler, "check_sentiment")
    
    # Sentiment check routes to respond or escalate
    graph.add_conditional_edges(
        "check_sentiment",
        route_after_sentiment,
        {
            "respond": "respond",
            "human_handoff": "human_handoff"
        }
    )
    
    # End nodes
    graph.add_edge("respond", END)
    graph.add_edge("human_handoff", END)
    
    return graph


async def create_agent(checkpointer=None):
    """
    Create a compiled CASPAR agent ready for use.
    
    Args:
        checkpointer: Optional checkpointer for persistence.
                     If None, uses in-memory storage.
    
    Returns:
        Compiled graph ready to process messages.
    """
    graph = build_graph()
    
    if checkpointer is None:
        checkpointer = MemorySaver()
    
    return graph.compile(checkpointer=checkpointer)


# ════════════════════════════════════════════════════════════════════════════
# HITL (Human-in-the-Loop) Extensions
# ════════════════════════════════════════════════════════════════════════════
# These are optional extensions for workflows requiring human approval

from langgraph.types import interrupt, Command
from caspar.handoff.approval import needs_approval, get_approval_reason


async def check_approval_needed(state: AgentState) -> dict:
    """
    Check if the pending response needs human approval.
    
    If approval is needed, interrupts the graph and waits for human decision.
    """
    if not needs_approval(state):
        return {"approval_status": "not_required"}
    
    pending_response = state.get("pending_response", "")
    reason = get_approval_reason(state)
    
    logger.info(
        "approval_required",
        conversation_id=state.get("conversation_id"),
        reason=reason
    )
    
    # Interrupt and wait for human decision
    human_decision = interrupt({
        "type": "approval_required",
        "pending_response": pending_response,
        "reason": reason,
        "conversation_id": state.get("conversation_id"),
        "customer_id": state.get("customer_id"),
    })
    
    if human_decision.get("approved"):
        final_response = human_decision.get("edited_response") or pending_response
        return {
            "approval_status": "approved",
            "pending_response": final_response,
            "reviewed_by": human_decision.get("reviewer_id"),
        }
    else:
        return {
            "approval_status": "rejected",
            "reviewed_by": human_decision.get("reviewer_id"),
            "needs_escalation": True,
        }


def route_after_approval(state: AgentState) -> str:
    """Route after approval check."""
    status = state.get("approval_status", "not_required")
    if status in ["not_required", "approved"]:
        return "send_response"
    return END


async def send_response(state: AgentState) -> dict:
    """Send the final response to the customer."""
    logger.info("send_response", conversation_id=state.get("conversation_id"))
    return {"response_sent": True}


def build_graph_with_approval() -> StateGraph:
    """
    Build agent graph with human approval workflow.
    
    Extends the standard graph to add approval checks for high-stakes responses.
    """
    graph = StateGraph(AgentState)
    
    # Add all standard nodes
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("handle_faq", handle_faq)
    graph.add_node("handle_order_inquiry", handle_order_inquiry)
    graph.add_node("handle_account", handle_account)
    graph.add_node("handle_complaint", handle_complaint)
    graph.add_node("handle_general", handle_general)
    graph.add_node("check_sentiment", check_sentiment)
    graph.add_node("respond", respond)
    graph.add_node("human_handoff", human_handoff)
    
    # Add approval nodes
    graph.add_node("check_approval_needed", check_approval_needed)
    graph.add_node("send_response", send_response)
    
    # Set entry point
    graph.set_entry_point("classify_intent")
    
    # Route by intent
    graph.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            "handle_faq": "handle_faq",
            "handle_order_inquiry": "handle_order_inquiry",
            "handle_account": "handle_account",
            "handle_complaint": "handle_complaint",
            "handle_general": "handle_general",
            "human_handoff": "human_handoff",
        }
    )
    
    # Handlers -> sentiment check
    for handler in ["handle_faq", "handle_order_inquiry", "handle_account", 
                    "handle_complaint", "handle_general"]:
        graph.add_edge(handler, "check_sentiment")
    
    # Sentiment -> respond or escalate
    graph.add_conditional_edges(
        "check_sentiment",
        route_after_sentiment,
        {"respond": "respond", "human_handoff": "human_handoff"}
    )
    
    # Respond -> approval check
    graph.add_edge("respond", "check_approval_needed")
    
    # Approval -> send or end
    graph.add_conditional_edges(
        "check_approval_needed",
        route_after_approval,
        {"send_response": "send_response", END: END}
    )
    
    # End nodes
    graph.add_edge("send_response", END)
    graph.add_edge("human_handoff", END)
    
    return graph


async def create_agent_with_approval(checkpointer=None):
    """
    Create agent with human approval support.
    
    IMPORTANT: A checkpointer is REQUIRED for interrupts to work!
    """
    graph = build_graph_with_approval()
    
    if checkpointer is None:
        raise ValueError(
            "Checkpointer is required for interrupt support. "
            "The graph must persist state to resume after approval."
        )
    
    return graph.compile(checkpointer=checkpointer)
