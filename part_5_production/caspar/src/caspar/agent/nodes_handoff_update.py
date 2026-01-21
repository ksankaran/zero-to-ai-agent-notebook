# From: Zero to AI Agent, Chapter 20, Section 20.5
# File: src/caspar/agent/nodes_handoff_update.py

"""
Updated nodes for human handoff functionality.

These functions extend the agent with handoff support:
- check_sentiment: Analyze customer emotion and detect escalation needs
- human_handoff: Handle the transition to a human agent
"""

from datetime import datetime, timezone

from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage

from caspar.config import settings, get_logger
from caspar.handoff import (
    check_escalation_triggers,
    get_handoff_queue,
    package_context_for_agent,
    notify_available_agents,
    format_context_for_display,
    check_sensitive_topics,
)
from caspar.tools import get_account_info, create_ticket

logger = get_logger(__name__)


async def check_sentiment(state: dict) -> dict:
    """
    Analyze customer sentiment and check all escalation triggers.
    
    This node runs after intent handlers to determine if:
    1. The customer is frustrated (sentiment analysis)
    2. Sensitive topics are detected
    3. Escalation to a human is needed
    """
    logger.info("check_sentiment_start", conversation_id=state.get("conversation_id"))
    
    messages = state["messages"]
    if not messages:
        return {
            "sentiment_score": 0.0,
            "frustration_level": "low",
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    
    # Get last few messages for context
    recent_messages = messages[-3:] if len(messages) >= 3 else messages
    conversation_text = "\n".join([
        f"{'Customer' if isinstance(m, HumanMessage) else 'Agent'}: {m.content}"
        for m in recent_messages
    ])
    
    llm = ChatOpenAI(
        model=settings.default_model,
        api_key=settings.openai_api_key,
        temperature=0
    )
    
    sentiment_prompt = f"""Analyze the customer's emotional state in this conversation.

Conversation:
{conversation_text}

Provide your analysis in this exact format:
SENTIMENT: [number from -1.0 to 1.0, where -1 is very negative, 0 is neutral, 1 is very positive]
FRUSTRATION: [low, medium, or high]"""

    response = llm.invoke([HumanMessage(content=sentiment_prompt)])
    
    # Parse response
    sentiment_score = 0.0
    frustration_level = "low"
    
    for line in response.content.strip().split("\n"):
        if line.startswith("SENTIMENT:"):
            try:
                sentiment_score = float(line.split(":")[1].strip())
                sentiment_score = max(-1.0, min(1.0, sentiment_score))
            except ValueError:
                pass
        elif line.startswith("FRUSTRATION:"):
            level = line.split(":")[1].strip().lower()
            if level in ["low", "medium", "high"]:
                frustration_level = level
    
    result = {
        "sentiment_score": sentiment_score,
        "frustration_level": frustration_level,
        "last_updated": datetime.now(timezone.utc).isoformat()
    }
    
    # Check for sensitive topics in the last message
    last_message = messages[-1].content if messages else ""
    if check_sensitive_topics(last_message):
        result["needs_escalation"] = True
        result["escalation_reason"] = "Sensitive topic detected - requires human handling"
        logger.warning("sensitive_topic_detected", conversation_id=state.get("conversation_id"))
    
    # Check if escalation needed based on sentiment
    elif sentiment_score < settings.sentiment_threshold or frustration_level == "high":
        result["needs_escalation"] = True
        result["escalation_reason"] = f"High frustration detected (sentiment: {sentiment_score}, frustration: {frustration_level})"
        logger.warning("escalation_triggered", conversation_id=state.get("conversation_id"))
    
    logger.info(
        "check_sentiment_complete",
        sentiment_score=sentiment_score,
        frustration_level=frustration_level
    )
    
    return result


async def human_handoff(state: dict) -> dict:
    """
    Handle escalation to a human agent.
    
    This node:
    1. Checks escalation triggers
    2. Creates a handoff request
    3. Packages context for the human agent
    4. Notifies available agents
    5. Informs the customer
    """
    logger.info("human_handoff_start", conversation_id=state.get("conversation_id"))
    
    customer_id = state.get("customer_id") or "UNKNOWN"
    conversation_id = state.get("conversation_id")
    
    # Get customer info for context
    customer_info = None
    if customer_id != "UNKNOWN":
        account_result = get_account_info(customer_id)
        if account_result["found"]:
            customer_info = account_result["account"]
    
    # Check escalation triggers
    customer_tier = customer_info.get("loyalty_tier") if customer_info else None
    escalation_result = check_escalation_triggers(state, customer_tier)
    
    # Create ticket for tracking
    ticket_result = create_ticket(
        customer_id=customer_id,
        category="general",
        subject="Human Agent Requested",
        description=escalation_result.reason,
        priority=escalation_result.priority,
        conversation_id=conversation_id,
    )
    
    # Add to handoff queue
    queue = get_handoff_queue()
    handoff_request = queue.add(
        conversation_id=conversation_id,
        customer_id=customer_id,
        priority=escalation_result.priority,
        triggers=[t.value for t in escalation_result.triggers],
        reason=escalation_result.reason,
        ticket_id=ticket_result["ticket"]["ticket_id"],
    )
    
    # Package context for human agent
    state_with_triggers = {
        **state,
        "escalation_triggers": [t.value for t in escalation_result.triggers],
    }
    context = package_context_for_agent(
        state=state_with_triggers,
        request_id=handoff_request.request_id,
        customer_info=customer_info,
    )
    
    # Notify available agents
    notifications = notify_available_agents(handoff_request, context)
    
    # Log the full context (in production, this would go to the agent dashboard)
    context_display = format_context_for_display(context)
    logger.info("handoff_context_prepared", context_length=len(context_display))
    
    # Build customer-facing message
    position = queue.get_queue_position(handoff_request.request_id)
    wait_time = handoff_request.estimated_wait or 5
    
    handoff_message = _build_handoff_message(
        ticket_id=ticket_result["ticket"]["ticket_id"],
        position=position,
        wait_time=wait_time,
        priority=escalation_result.priority,
    )
    
    logger.info(
        "human_handoff_complete",
        request_id=handoff_request.request_id,
        ticket_id=ticket_result["ticket"]["ticket_id"],
        agents_notified=len(notifications)
    )
    
    return {
        "messages": [AIMessage(content=handoff_message)],
        "needs_escalation": True,
        "escalation_reason": escalation_result.reason,
        "ticket_id": ticket_result["ticket"]["ticket_id"],
        "last_updated": datetime.now(timezone.utc).isoformat()
    }


def _build_handoff_message(
    ticket_id: str,
    position: int,
    wait_time: int,
    priority: str,
) -> str:
    """Build the customer-facing handoff message."""
    
    priority_messages = {
        "urgent": "I've flagged this as urgent, and a team member will be with you very shortly.",
        "high": "I've marked this as high priority. A team member will be with you soon.",
        "medium": "A team member will be with you as soon as possible.",
        "low": "A team member will reach out to help you.",
    }
    
    message_parts = [
        "I understand you'd like to speak with a human agent, and I've arranged that for you.",
        "",
        f"**Your Reference Number: {ticket_id}**",
        "",
        priority_messages.get(priority, priority_messages["medium"]),
        "",
    ]
    
    if position > 0:
        message_parts.append(f"You're currently #{position} in our queue.")
    
    message_parts.extend([
        f"Estimated wait time: approximately {wait_time} minutes.",
        "",
        "While you wait:",
        "• You don't need to stay on this chat - we'll reach out to you",
        "• You can reference your ticket number in any follow-up",
        "• Our team has the full context of our conversation",
        "",
        "Is there anything else I can help you with while you wait?",
    ])
    
    return "\n".join(message_parts)
