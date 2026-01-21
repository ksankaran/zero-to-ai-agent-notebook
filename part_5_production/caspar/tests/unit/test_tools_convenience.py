"""Unit tests for tool convenience functions."""

import pytest
from caspar.tools import get_order_status, create_ticket, get_account_info


class TestGetOrderStatus:
    """Tests for get_order_status convenience function."""
    
    def test_found_order_returns_success(self):
        """Should return found=True with order details."""
        result = get_order_status("TF-10001")
        
        assert result["found"] is True
        assert "order" in result
        assert "summary" in result
    
    def test_not_found_returns_error(self):
        """Should return found=False with error message."""
        result = get_order_status("TF-99999")
        
        assert result["found"] is False
        assert "error" in result
        assert "not found" in result["error"].lower()


class TestCreateTicket:
    """Tests for create_ticket convenience function."""
    
    def test_creates_ticket_successfully(self):
        """Should create ticket and return success."""
        result = create_ticket(
            customer_id="CUST-1000",
            category="technical",
            subject="Test",
            description="Test description",
        )
        
        assert result["success"] is True
        assert "ticket" in result
        assert "confirmation" in result
    
    def test_invalid_category_defaults_to_general(self):
        """Should use 'general' for invalid categories."""
        result = create_ticket(
            customer_id="CUST-1000",
            category="invalid_category",
            subject="Test",
            description="Test",
        )
        
        assert result["ticket"]["category"] == "general"
    
    def test_invalid_priority_defaults_to_medium(self):
        """Should use 'medium' for invalid priorities."""
        result = create_ticket(
            customer_id="CUST-1000",
            category="technical",
            subject="Test",
            description="Test",
            priority="super_urgent",  # Invalid
        )
        
        assert result["ticket"]["priority"] == "medium"


class TestGetAccountInfo:
    """Tests for get_account_info convenience function."""
    
    def test_found_account_returns_success(self):
        """Should return found=True with account details."""
        result = get_account_info("CUST-1000")
        
        assert result["found"] is True
        assert "account" in result
        assert "summary" in result
    
    def test_not_found_returns_error(self):
        """Should return found=False with error message."""
        result = get_account_info("CUST-99999")
        
        assert result["found"] is False
        assert "error" in result
