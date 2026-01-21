# From: Zero to AI Agent, Chapter 20, Section 20.5
# File: src/caspar/handoff/triggers.py

"""
Escalation Trigger Detection

Identifies situations that require human intervention.
"""

from enum import Enum
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from caspar.config import settings, get_logger

logger = get_logger(__name__)


class EscalationTrigger(str, Enum):
    """Types of escalation triggers."""
    
    EXPLICIT_REQUEST = "explicit_request"
    HIGH_FRUSTRATION = "high_frustration"
    REPEATED_FAILURES = "repeated_failures"
    POLICY_EXCEPTION = "policy_exception"
    VIP_CUSTOMER = "vip_customer"
    SENSITIVE_TOPIC = "sensitive_topic"
    COMPLEX_ISSUE = "complex_issue"
    MAX_TURNS_REACHED = "max_turns_reached"


class EscalationResult(BaseModel):
    """Result of escalation check."""
    
    should_escalate: bool
    triggers: list[EscalationTrigger]
    priority: str  # "low", "medium", "high", "urgent"
    reason: str


def check_escalation_triggers(
    state: dict,
    customer_tier: str | None = None,
) -> EscalationResult:
    """
    Check all escalation triggers against current state.
    
    Args:
        state: Current agent state
        customer_tier: Customer's loyalty tier (if known)
        
    Returns:
        EscalationResult with triggers found and recommended priority
    """
    triggers = []
    reasons = []
    
    # Check explicit request (already classified as handoff_request)
    if state.get("intent") == "handoff_request":
        triggers.append(EscalationTrigger.EXPLICIT_REQUEST)
        reasons.append("Customer requested human agent")
    
    # Check frustration level (handle None values)
    sentiment = state.get("sentiment_score")
    if sentiment is None:
        sentiment = 0.0
    frustration = state.get("frustration_level") or "low"
    
    if sentiment < settings.sentiment_threshold or frustration == "high":
        triggers.append(EscalationTrigger.HIGH_FRUSTRATION)
        reasons.append(f"High frustration detected (sentiment: {sentiment})")
    
    # Check turn count
    turn_count = state.get("turn_count") or 0
    if turn_count >= settings.max_conversation_turns:
        triggers.append(EscalationTrigger.MAX_TURNS_REACHED)
        reasons.append(f"Conversation exceeded {settings.max_conversation_turns} turns")
    
    # Check for VIP customer
    if customer_tier in ["gold", "platinum"]:
        # VIP customers get faster escalation on any issue
        if state.get("intent") == "complaint" or frustration in ["medium", "high"]:
            triggers.append(EscalationTrigger.VIP_CUSTOMER)
            reasons.append(f"VIP customer ({customer_tier} tier) with issue")
    
    # Check for policy exceptions (would need order info)
    order_info = state.get("order_info") or {}
    if order_info.get("full_order"):
        order_total = order_info["full_order"].get("total", 0)
        if order_total > 500 and state.get("intent") == "complaint":
            triggers.append(EscalationTrigger.POLICY_EXCEPTION)
            reasons.append(f"High-value order (${order_total}) with complaint")
    
    # Determine priority based on triggers
    priority = _calculate_priority(triggers)
    
    result = EscalationResult(
        should_escalate=len(triggers) > 0,
        triggers=triggers,
        priority=priority,
        reason="; ".join(reasons) if reasons else "No escalation needed"
    )
    
    if result.should_escalate:
        logger.info(
            "escalation_triggers_detected",
            triggers=[t.value for t in triggers],
            priority=priority
        )
    
    return result


def _calculate_priority(triggers: list[EscalationTrigger]) -> str:
    """Calculate escalation priority based on triggers."""
    
    if not triggers:
        return "low"
    
    # Urgent triggers
    urgent_triggers = {
        EscalationTrigger.EXPLICIT_REQUEST,
        EscalationTrigger.HIGH_FRUSTRATION,
        EscalationTrigger.SENSITIVE_TOPIC,
    }
    
    # High priority triggers
    high_triggers = {
        EscalationTrigger.VIP_CUSTOMER,
        EscalationTrigger.POLICY_EXCEPTION,
        EscalationTrigger.REPEATED_FAILURES,
    }
    
    if any(t in urgent_triggers for t in triggers):
        return "urgent"
    elif any(t in high_triggers for t in triggers):
        return "high"
    elif len(triggers) >= 2:
        # Multiple medium triggers escalate to high
        return "high"
    else:
        return "medium"


def check_sensitive_topics(message: str) -> bool:
    """Check if message contains sensitive topics requiring human handling."""
    
    sensitive_keywords = [
        "lawyer", "lawsuit", "legal action", "sue",
        "police", "fraud", "scam", "stolen",
        "safety", "dangerous", "injury", "injured", "hurt",
        "discrimination", "harassment",
        "cancel account", "delete my data", "gdpr",
    ]
    
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in sensitive_keywords)
