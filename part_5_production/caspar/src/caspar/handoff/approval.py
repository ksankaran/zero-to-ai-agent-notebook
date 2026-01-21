# From: Zero to AI Agent, Chapter 20, Section 20.5
# File: src/caspar/handoff/approval.py

"""
Human-in-the-Loop response approval.

This module enables human review of AI responses before they're sent,
useful for high-stakes or sensitive situations.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from caspar.config import get_logger

logger = get_logger(__name__)


class ApprovalStatus(Enum):
    """Status of a pending approval."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EDITED = "edited"


@dataclass
class PendingApproval:
    """A response waiting for human approval."""
    conversation_id: str
    original_response: str
    reason: str  # Why approval is needed
    created_at: datetime
    status: ApprovalStatus = ApprovalStatus.PENDING
    reviewer_id: str | None = None
    edited_response: str | None = None
    reviewed_at: datetime | None = None


def needs_approval(state: dict) -> bool:
    """
    Determine if a response needs human approval before sending.
    
    This is checked BEFORE the response is sent to the customer.
    """
    # High-value actions need approval
    if state.get("pending_refund_amount", 0) > 100:
        return True
    
    # Policy exceptions need approval
    if state.get("policy_exception_requested"):
        return True
    
    # Very negative sentiment needs human review
    sentiment = state.get("sentiment_score", 0)
    if sentiment < -0.7:
        return True
    
    # New customers with complaints
    if state.get("intent") == "complaint" and state.get("customer_tenure_days", 365) < 30:
        return True
    
    return False


def get_approval_reason(state: dict) -> str:
    """Get a human-readable reason for why approval is needed."""
    reasons = []
    
    if state.get("pending_refund_amount", 0) > 100:
        amount = state.get("pending_refund_amount")
        reasons.append(f"High-value refund: ${amount}")
    
    if state.get("policy_exception_requested"):
        reasons.append("Policy exception requested")
    
    if state.get("sentiment_score", 0) < -0.7:
        reasons.append("Customer appears very upset")
    
    if state.get("intent") == "complaint" and state.get("customer_tenure_days", 365) < 30:
        reasons.append("New customer complaint - retention risk")
    
    return "; ".join(reasons) if reasons else "Manual review requested"
