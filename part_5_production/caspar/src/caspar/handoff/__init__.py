# From: Zero to AI Agent, Chapter 20, Section 20.5
# File: src/caspar/handoff/__init__.py

"""CASPAR Human Handoff Module

Manages escalation to human agents, including queue management,
context packaging, agent notifications, and approval workflows.
"""

from .triggers import EscalationTrigger, check_escalation_triggers, check_sensitive_topics
from .queue import HandoffQueue, HandoffRequest, get_handoff_queue
from .context import ConversationContext, package_context_for_agent, format_context_for_display
from .notifications import notify_available_agents
from .approval import ApprovalStatus, PendingApproval, needs_approval, get_approval_reason

__all__ = [
    # Escalation triggers
    "EscalationTrigger",
    "check_escalation_triggers",
    "check_sensitive_topics",
    # Queue management
    "HandoffQueue",
    "HandoffRequest",
    "get_handoff_queue",
    # Context packaging
    "ConversationContext",
    "package_context_for_agent",
    "format_context_for_display",
    # Notifications
    "notify_available_agents",
    # HITL Approval
    "ApprovalStatus",
    "PendingApproval",
    "needs_approval",
    "get_approval_reason",
]
