# From: Zero to AI Agent, Chapter 20, Section 20.5
# File: src/caspar/handoff/queue.py

"""
Handoff Queue Management

Manages the queue of conversations waiting for human agents.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field
import uuid

from caspar.config import get_logger

logger = get_logger(__name__)


class HandoffStatus(str, Enum):
    """Status of a handoff request."""
    
    QUEUED = "queued"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ABANDONED = "abandoned"


class HandoffRequest(BaseModel):
    """A request for human agent assistance."""
    
    request_id: str = Field(default_factory=lambda: f"HO-{uuid.uuid4().hex[:8].upper()}")
    conversation_id: str
    customer_id: str
    ticket_id: str | None = None
    
    priority: Literal["low", "medium", "high", "urgent"]
    triggers: list[str]  # EscalationTrigger values
    reason: str
    
    status: HandoffStatus = HandoffStatus.QUEUED
    assigned_agent: str | None = None
    
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    assigned_at: str | None = None
    resolved_at: str | None = None
    
    # Estimated wait time in minutes (calculated based on queue position)
    estimated_wait: int | None = None


class HandoffQueue:
    """
    Manages the queue of pending handoff requests.
    
    In production, this would be backed by Redis or a database.
    For demo purposes, we use in-memory storage.
    """
    
    def __init__(self):
        self._queue: dict[str, HandoffRequest] = {}
        self._by_conversation: dict[str, str] = {}  # conversation_id -> request_id
    
    def add(
        self,
        conversation_id: str,
        customer_id: str,
        priority: str,
        triggers: list[str],
        reason: str,
        ticket_id: str | None = None,
    ) -> HandoffRequest:
        """Add a new handoff request to the queue."""
        
        # Check if conversation already has a pending request
        if conversation_id in self._by_conversation:
            existing_id = self._by_conversation[conversation_id]
            existing = self._queue.get(existing_id)
            if existing and existing.status == HandoffStatus.QUEUED:
                logger.info("handoff_already_queued", conversation_id=conversation_id)
                return existing
        
        request = HandoffRequest(
            conversation_id=conversation_id,
            customer_id=customer_id,
            ticket_id=ticket_id,
            priority=priority,
            triggers=triggers,
            reason=reason,
            estimated_wait=self._estimate_wait_time(priority),
        )
        
        self._queue[request.request_id] = request
        self._by_conversation[conversation_id] = request.request_id
        
        logger.info(
            "handoff_queued",
            request_id=request.request_id,
            conversation_id=conversation_id,
            priority=priority,
            position=self.get_queue_position(request.request_id)
        )
        
        return request
    
    def _estimate_wait_time(self, priority: str) -> int:
        """Estimate wait time based on queue and priority."""
        
        # Count requests ahead in queue by priority
        queued = [r for r in self._queue.values() if r.status == HandoffStatus.QUEUED]
        
        # Priority weights (urgent gets served first)
        priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
        my_priority = priority_order.get(priority, 2)
        
        ahead_count = sum(
            1 for r in queued 
            if priority_order.get(r.priority, 2) <= my_priority
        )
        
        # Assume ~5 minutes per request ahead
        base_wait = ahead_count * 5
        
        # Adjust by priority
        if priority == "urgent":
            return max(2, base_wait // 2)
        elif priority == "high":
            return max(5, base_wait)
        else:
            return base_wait + 5
    
    def get(self, request_id: str) -> HandoffRequest | None:
        """Get a handoff request by ID."""
        return self._queue.get(request_id)
    
    def get_by_conversation(self, conversation_id: str) -> HandoffRequest | None:
        """Get the handoff request for a conversation."""
        request_id = self._by_conversation.get(conversation_id)
        if request_id:
            return self._queue.get(request_id)
        return None
    
    def get_queue_position(self, request_id: str) -> int:
        """Get position in queue (1-indexed)."""
        request = self._queue.get(request_id)
        if not request or request.status != HandoffStatus.QUEUED:
            return 0
        
        # Sort by priority then by created_at
        priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
        
        queued = [
            r for r in self._queue.values() 
            if r.status == HandoffStatus.QUEUED
        ]
        queued.sort(key=lambda r: (priority_order.get(r.priority, 2), r.created_at))
        
        for i, r in enumerate(queued, 1):
            if r.request_id == request_id:
                return i
        
        return 0
    
    def assign(self, request_id: str, agent_id: str) -> HandoffRequest | None:
        """Assign a request to a human agent."""
        request = self._queue.get(request_id)
        if not request:
            return None
        
        request.status = HandoffStatus.ASSIGNED
        request.assigned_agent = agent_id
        request.assigned_at = datetime.now(timezone.utc).isoformat()
        request.updated_at = datetime.now(timezone.utc).isoformat()
        
        logger.info(
            "handoff_assigned",
            request_id=request_id,
            agent_id=agent_id
        )
        
        return request
    
    def resolve(self, request_id: str, resolution: str = "resolved") -> HandoffRequest | None:
        """Mark a handoff request as resolved."""
        request = self._queue.get(request_id)
        if not request:
            return None
        
        request.status = HandoffStatus.RESOLVED
        request.resolved_at = datetime.now(timezone.utc).isoformat()
        request.updated_at = datetime.now(timezone.utc).isoformat()
        
        # Clean up conversation mapping
        if request.conversation_id in self._by_conversation:
            del self._by_conversation[request.conversation_id]
        
        logger.info("handoff_resolved", request_id=request_id)
        
        return request
    
    def get_pending_count(self) -> dict[str, int]:
        """Get count of pending requests by priority."""
        counts = {"urgent": 0, "high": 0, "medium": 0, "low": 0}
        
        for request in self._queue.values():
            if request.status == HandoffStatus.QUEUED:
                counts[request.priority] = counts.get(request.priority, 0) + 1
        
        return counts


# Singleton instance
_handoff_queue: HandoffQueue | None = None


def get_handoff_queue() -> HandoffQueue:
    """Get or create the global handoff queue."""
    global _handoff_queue
    if _handoff_queue is None:
        _handoff_queue = HandoffQueue()
    return _handoff_queue
