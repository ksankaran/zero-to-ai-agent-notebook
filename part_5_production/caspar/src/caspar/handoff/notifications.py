# From: Zero to AI Agent, Chapter 20, Section 20.5
# File: src/caspar/handoff/notifications.py

"""
Agent Notification System

Notifies available human agents about pending handoffs.
In production, this would integrate with Slack, email, or a dashboard.
"""

from datetime import datetime, timezone
from pydantic import BaseModel

from caspar.config import get_logger
from .queue import HandoffRequest
from .context import ConversationContext

logger = get_logger(__name__)


class AgentNotification(BaseModel):
    """A notification sent to human agents."""
    
    notification_id: str
    request_id: str
    priority: str
    customer_id: str
    brief_reason: str
    estimated_wait: int | None
    sent_at: str
    channel: str  # "dashboard", "slack", "email"


# Simulated agent pool
AVAILABLE_AGENTS = [
    {"id": "AGENT-001", "name": "Sarah Johnson", "status": "available", "skills": ["technical", "billing"]},
    {"id": "AGENT-002", "name": "Mike Chen", "status": "available", "skills": ["returns", "shipping"]},
    {"id": "AGENT-003", "name": "Emily Davis", "status": "busy", "skills": ["vip", "complaints"]},
]


def get_available_agents(required_skills: list[str] | None = None) -> list[dict]:
    """Get list of available agents, optionally filtered by skills."""
    
    available = [a for a in AVAILABLE_AGENTS if a["status"] == "available"]
    
    if required_skills:
        available = [
            a for a in available
            if any(skill in a["skills"] for skill in required_skills)
        ]
    
    return available


def notify_available_agents(
    request: HandoffRequest,
    context: ConversationContext | None = None,
) -> list[AgentNotification]:
    """
    Notify available agents about a new handoff request.
    
    In production, this would:
    - Send Slack messages to a support channel
    - Update a real-time dashboard
    - Send push notifications to mobile apps
    - Trigger phone alerts for urgent requests
    
    Args:
        request: The handoff request
        context: Optional conversation context
        
    Returns:
        List of notifications sent
    """
    notifications = []
    
    # Determine required skills based on triggers
    required_skills = []
    if "vip_customer" in request.triggers:
        required_skills.append("vip")
    if "complaint" in str(request.reason).lower():
        required_skills.append("complaints")
    
    # Get available agents
    agents = get_available_agents(required_skills)
    
    if not agents:
        # Fall back to all available agents
        agents = get_available_agents()
    
    # Create notification content
    brief_reason = request.reason[:100] + "..." if len(request.reason) > 100 else request.reason
    
    for agent in agents:
        notification = AgentNotification(
            notification_id=f"NOTIF-{request.request_id}-{agent['id']}",
            request_id=request.request_id,
            priority=request.priority,
            customer_id=request.customer_id,
            brief_reason=brief_reason,
            estimated_wait=request.estimated_wait,
            sent_at=datetime.now(timezone.utc).isoformat(),
            channel="dashboard",
        )
        
        notifications.append(notification)
        
        # Log the "notification" (in production, this would actually send)
        logger.info(
            "agent_notified",
            agent_id=agent["id"],
            agent_name=agent["name"],
            request_id=request.request_id,
            priority=request.priority
        )
        
        # Simulate different notification channels based on priority
        if request.priority == "urgent":
            _send_urgent_notification(agent, request, brief_reason)
        else:
            _send_standard_notification(agent, request, brief_reason)
    
    return notifications


def _send_urgent_notification(agent: dict, request: HandoffRequest, reason: str):
    """Simulate urgent notification (would trigger alerts)."""
    print(f"\n🚨 URGENT HANDOFF ALERT for {agent['name']}!")
    print(f"   Customer: {request.customer_id}")
    print(f"   Reason: {reason}")
    print(f"   → Immediate attention required\n")


def _send_standard_notification(agent: dict, request: HandoffRequest, reason: str):
    """Simulate standard notification (would update dashboard)."""
    print(f"\n📋 New handoff request for {agent['name']}")
    print(f"   Priority: {request.priority.upper()}")
    print(f"   Customer: {request.customer_id}")
    print(f"   Reason: {reason}\n")
