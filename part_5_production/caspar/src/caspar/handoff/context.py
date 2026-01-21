# From: Zero to AI Agent, Chapter 20, Section 20.5
# File: src/caspar/handoff/context.py

"""
Context Packaging for Human Agents

Prepares comprehensive context to help human agents
quickly understand and resolve customer issues.
"""

from datetime import datetime, timezone
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage

from caspar.config import get_logger

logger = get_logger(__name__)


class ConversationContext(BaseModel):
    """Complete context package for human agent."""
    
    # Identification
    conversation_id: str
    customer_id: str
    request_id: str
    
    # Customer Info
    customer_name: str | None = None
    customer_email: str | None = None
    customer_tier: str | None = None
    customer_history: str | None = None  # Brief history summary
    
    # Conversation Summary
    conversation_summary: str
    message_count: int
    conversation_duration: str | None = None
    
    # Issue Details
    detected_intent: str
    escalation_triggers: list[str]
    escalation_reason: str
    sentiment_score: float
    frustration_level: str
    
    # Relevant Data
    order_info: dict | None = None
    ticket_id: str | None = None
    retrieved_knowledge: str | None = None
    
    # Full Transcript
    transcript: list[dict]
    
    # Recommendations
    suggested_actions: list[str]
    
    # Metadata
    packaged_at: str


def package_context_for_agent(
    state: dict,
    request_id: str,
    customer_info: dict | None = None,
) -> ConversationContext:
    """
    Package all relevant context for a human agent.
    
    Args:
        state: Current agent state
        request_id: The handoff request ID
        customer_info: Optional customer account info
        
    Returns:
        ConversationContext with all relevant information
    """
    messages = state.get("messages") or []
    
    # Build transcript
    transcript = []
    for msg in messages:
        transcript.append({
            "role": "customer" if isinstance(msg, HumanMessage) else "caspar",
            "content": msg.content,
        })
    
    # Generate conversation summary
    summary = _generate_summary(messages)
    
    # Extract customer info if provided
    customer_name = None
    customer_email = None
    customer_tier = None
    customer_history = None
    
    if customer_info:
        customer_name = customer_info.get("name")
        customer_email = customer_info.get("email")
        customer_tier = customer_info.get("loyalty_tier")
        customer_history = f"{customer_info.get('total_orders', 0)} orders, ${customer_info.get('total_spent', 0):,.2f} total"
    
    # Generate suggested actions based on intent and triggers
    suggested_actions = _generate_suggestions(state)
    
    context = ConversationContext(
        conversation_id=state.get("conversation_id") or "unknown",
        customer_id=state.get("customer_id") or "unknown",
        request_id=request_id,
        customer_name=customer_name,
        customer_email=customer_email,
        customer_tier=customer_tier,
        customer_history=customer_history,
        conversation_summary=summary,
        message_count=len(messages),
        detected_intent=state.get("intent") or "unknown",
        escalation_triggers=state.get("escalation_triggers") or [],
        escalation_reason=state.get("escalation_reason") or "Unknown",
        sentiment_score=state.get("sentiment_score") or 0.0,
        frustration_level=state.get("frustration_level") or "unknown",
        order_info=state.get("order_info"),
        ticket_id=state.get("ticket_id"),
        retrieved_knowledge=state.get("retrieved_context"),
        transcript=transcript,
        suggested_actions=suggested_actions,
        packaged_at=datetime.now(timezone.utc).isoformat(),
    )
    
    logger.info(
        "context_packaged",
        conversation_id=context.conversation_id,
        message_count=context.message_count
    )
    
    return context


def _generate_summary(messages: list) -> str:
    """Generate a brief summary of the conversation."""
    
    if not messages:
        return "No messages in conversation."
    
    # Get first customer message (the initial inquiry)
    first_customer_msg = None
    for msg in messages:
        if isinstance(msg, HumanMessage):
            first_customer_msg = msg.content
            break
    
    # Get last customer message (most recent concern)
    last_customer_msg = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_customer_msg = msg.content
            break
    
    summary_parts = []
    
    if first_customer_msg:
        # Truncate if too long
        initial = first_customer_msg[:150] + "..." if len(first_customer_msg) > 150 else first_customer_msg
        summary_parts.append(f"Initial inquiry: {initial}")
    
    if last_customer_msg and last_customer_msg != first_customer_msg:
        recent = last_customer_msg[:150] + "..." if len(last_customer_msg) > 150 else last_customer_msg
        summary_parts.append(f"Most recent message: {recent}")
    
    summary_parts.append(f"Total exchanges: {len(messages)} messages")
    
    return "\n".join(summary_parts)


def _generate_suggestions(state: dict) -> list[str]:
    """Generate suggested actions for the human agent."""
    
    suggestions = []
    intent = state.get("intent") or ""
    triggers = state.get("escalation_triggers") or []
    
    # Intent-based suggestions
    if intent == "complaint":
        suggestions.append("Acknowledge the customer's frustration and apologize for the inconvenience")
        suggestions.append("Review order history for context")
        
    if intent == "order_inquiry":
        suggestions.append("Verify order status in the system")
        suggestions.append("Check for any shipping delays or issues")
    
    # Trigger-based suggestions
    if "high_frustration" in triggers:
        suggestions.append("⚠️ Customer is highly frustrated - prioritize empathy")
        suggestions.append("Consider offering a goodwill gesture (discount, expedited shipping)")
    
    if "vip_customer" in triggers:
        suggestions.append("⭐ VIP Customer - consider premium resolution options")
    
    if "policy_exception" in triggers:
        suggestions.append("This may require manager approval for policy exception")
    
    # Order-specific suggestions
    order_info = state.get("order_info") or {}
    if order_info.get("status") == "processing":
        suggestions.append("Order is still processing - can offer to expedite if needed")
    elif order_info.get("status") == "shipped":
        suggestions.append("Order is in transit - check tracking for delays")
    
    # Default suggestions
    if not suggestions:
        suggestions.append("Review the conversation transcript for context")
        suggestions.append("Ask clarifying questions if needed")
    
    return suggestions


def format_context_for_display(context: ConversationContext) -> str:
    """Format context as readable text for agent interface."""
    
    lines = [
        "=" * 60,
        "🎫 HANDOFF CONTEXT",
        "=" * 60,
        "",
        f"Request ID: {context.request_id}",
        f"Conversation: {context.conversation_id}",
        f"Customer: {context.customer_id}",
        "",
    ]
    
    # Customer info if available
    if context.customer_name:
        lines.append("👤 CUSTOMER INFO")
        lines.append("-" * 40)
        lines.append(f"Name: {context.customer_name}")
        if context.customer_email:
            lines.append(f"Email: {context.customer_email}")
        if context.customer_tier:
            lines.append(f"Tier: {context.customer_tier.upper()}")
        if context.customer_history:
            lines.append(f"History: {context.customer_history}")
        lines.append("")
    
    # Issue summary
    lines.append("📋 ISSUE SUMMARY")
    lines.append("-" * 40)
    lines.append(f"Intent: {context.detected_intent}")
    lines.append(f"Sentiment: {context.sentiment_score:.2f} ({context.frustration_level} frustration)")
    lines.append(f"Reason: {context.escalation_reason}")
    lines.append("")
    
    # Suggested actions
    lines.append("💡 SUGGESTED ACTIONS")
    lines.append("-" * 40)
    for action in context.suggested_actions:
        lines.append(f"  • {action}")
    lines.append("")
    
    # Conversation summary
    lines.append("📝 CONVERSATION SUMMARY")
    lines.append("-" * 40)
    lines.append(context.conversation_summary)
    lines.append("")
    
    # Transcript
    lines.append("💬 TRANSCRIPT")
    lines.append("-" * 40)
    for msg in context.transcript:
        role = "Customer" if msg["role"] == "customer" else "CASPAR"
        content = msg["content"][:200] + "..." if len(msg["content"]) > 200 else msg["content"]
        lines.append(f"{role}: {content}")
        lines.append("")
    
    lines.append("=" * 60)
    
    return "\n".join(lines)
