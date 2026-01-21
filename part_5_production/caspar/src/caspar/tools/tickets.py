# From: Zero to AI Agent, Chapter 20, Section 20.4
# File: src/caspar/tools/tickets.py

"""
Ticket Creation Tool

Creates and manages customer support tickets.
In production, this would integrate with your ticketing system.
"""

from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel
import uuid

from caspar.config import get_logger

logger = get_logger(__name__)


class Ticket(BaseModel):
    """A customer support ticket."""
    
    ticket_id: str
    customer_id: str
    conversation_id: str | None = None
    category: Literal["return", "refund", "technical", "billing", "shipping", "general"]
    priority: Literal["low", "medium", "high", "urgent"]
    subject: str
    description: str
    status: Literal["open", "in_progress", "waiting_customer", "resolved", "closed"] = "open"
    created_at: str
    updated_at: str
    assigned_to: str | None = None
    resolution: str | None = None


class TicketTool:
    """
    Tool for creating and managing support tickets.
    
    In production, this would integrate with Zendesk, Freshdesk, etc.
    """
    
    def __init__(self):
        self._tickets: dict[str, Ticket] = {}
    
    def create(
        self,
        customer_id: str,
        category: str,
        subject: str,
        description: str,
        priority: str = "medium",
        conversation_id: str | None = None,
    ) -> Ticket:
        """Create a new support ticket."""
        
        ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc).isoformat()
        
        ticket = Ticket(
            ticket_id=ticket_id,
            customer_id=customer_id,
            conversation_id=conversation_id,
            category=category,
            priority=priority,
            subject=subject,
            description=description,
            created_at=now,
            updated_at=now,
        )
        
        self._tickets[ticket_id] = ticket
        
        logger.info(
            "ticket_created",
            ticket_id=ticket_id,
            customer_id=customer_id,
            category=category,
            priority=priority
        )
        
        return ticket
    
    def get(self, ticket_id: str) -> Ticket | None:
        """Retrieve a ticket by ID."""
        return self._tickets.get(ticket_id)
    
    def get_customer_tickets(self, customer_id: str) -> list[Ticket]:
        """Get all tickets for a customer."""
        return [t for t in self._tickets.values() if t.customer_id == customer_id]
    
    def format_ticket_confirmation(self, ticket: Ticket) -> str:
        """Format ticket info for customer confirmation."""
        
        priority_emoji = {"low": "🟢", "medium": "🟡", "high": "🟠", "urgent": "🔴"}
        
        return f"""**Support Ticket Created**

Ticket ID: {ticket.ticket_id}
Category: {ticket.category.title()}
Priority: {priority_emoji.get(ticket.priority, "⚪")} {ticket.priority.title()}
Subject: {ticket.subject}

Our team will review your ticket and respond within:
- Urgent: 2 hours
- High: 4 hours  
- Medium: 24 hours
- Low: 48 hours

You can reference ticket {ticket.ticket_id} in future conversations."""


# Singleton instance
_ticket_tool: TicketTool | None = None


def get_ticket_tool() -> TicketTool:
    """Get or create the ticket tool instance."""
    global _ticket_tool
    if _ticket_tool is None:
        _ticket_tool = TicketTool()
    return _ticket_tool


def create_ticket(
    customer_id: str,
    category: str,
    subject: str,
    description: str,
    priority: str = "medium",
    conversation_id: str | None = None,
) -> dict:
    """Convenience function to create a ticket."""
    
    tool = get_ticket_tool()
    
    # Validate inputs
    valid_categories = ["return", "refund", "technical", "billing", "shipping", "general"]
    if category.lower() not in valid_categories:
        category = "general"
    
    valid_priorities = ["low", "medium", "high", "urgent"]
    if priority.lower() not in valid_priorities:
        priority = "medium"
    
    ticket = tool.create(
        customer_id=customer_id,
        category=category.lower(),
        subject=subject,
        description=description,
        priority=priority.lower(),
        conversation_id=conversation_id,
    )
    
    return {
        "success": True,
        "ticket": ticket.model_dump(),
        "confirmation": tool.format_ticket_confirmation(ticket)
    }
