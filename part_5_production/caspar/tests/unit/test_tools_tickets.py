"""Unit tests for the ticket creation tool."""

import pytest
from caspar.tools.tickets import (
    TicketTool,
    create_ticket,
    Ticket,
)


class TestTicketTool:
    """Tests for TicketTool class."""
    
    def setup_method(self):
        """Set up a fresh tool instance for each test."""
        self.tool = TicketTool()
    
    def test_create_ticket_returns_ticket(self):
        """Should create and return a ticket."""
        ticket = self.tool.create(
            customer_id="CUST-1000",
            category="technical",
            subject="Test ticket",
            description="This is a test",
        )
        
        assert ticket is not None
        assert ticket.ticket_id.startswith("TKT-")
        assert ticket.customer_id == "CUST-1000"
        assert ticket.category == "technical"
        assert ticket.status == "open"
    
    def test_create_ticket_with_priority(self):
        """Should respect priority setting."""
        ticket = self.tool.create(
            customer_id="CUST-1000",
            category="billing",
            subject="Urgent issue",
            description="Very urgent",
            priority="urgent",
        )
        
        assert ticket.priority == "urgent"
    
    def test_create_ticket_default_priority(self):
        """Should default to medium priority."""
        ticket = self.tool.create(
            customer_id="CUST-1000",
            category="general",
            subject="General question",
            description="Just asking",
        )
        
        assert ticket.priority == "medium"
    
    def test_get_ticket_by_id(self):
        """Should retrieve ticket by ID."""
        created = self.tool.create(
            customer_id="CUST-1000",
            category="return",
            subject="Return request",
            description="Want to return item",
        )
        
        retrieved = self.tool.get(created.ticket_id)
        
        assert retrieved is not None
        assert retrieved.ticket_id == created.ticket_id
    
    def test_get_nonexistent_ticket(self):
        """Should return None for tickets that don't exist."""
        result = self.tool.get("TKT-NONEXISTENT")
        
        assert result is None
    
    def test_get_customer_tickets(self):
        """Should retrieve all tickets for a customer."""
        # Create multiple tickets
        self.tool.create(
            customer_id="CUST-TEST",
            category="technical",
            subject="Issue 1",
            description="First issue",
        )
        self.tool.create(
            customer_id="CUST-TEST",
            category="billing",
            subject="Issue 2",
            description="Second issue",
        )
        self.tool.create(
            customer_id="CUST-OTHER",
            category="general",
            subject="Other customer",
            description="Different customer",
        )
        
        tickets = self.tool.get_customer_tickets("CUST-TEST")
        
        assert len(tickets) == 2
        assert all(t.customer_id == "CUST-TEST" for t in tickets)
