"""Unit tests for the order lookup tool."""

import pytest
from caspar.tools.orders import (
    OrderLookupTool,
    get_order_status,
    OrderInfo,
)


class TestOrderLookupTool:
    """Tests for OrderLookupTool class."""
    
    def setup_method(self):
        """Set up a fresh tool instance for each test."""
        self.tool = OrderLookupTool()
    
    def test_lookup_existing_order(self):
        """Should find an order that exists."""
        order = self.tool.lookup("TF-10001")
        
        assert order is not None
        assert order.order_id == "TF-10001"
        assert order.status in ["processing", "shipped", "delivered", "cancelled", "returned"]
    
    def test_lookup_nonexistent_order(self):
        """Should return None for orders that don't exist."""
        order = self.tool.lookup("TF-99999")
        
        assert order is None
    
    def test_lookup_normalizes_order_id(self):
        """Should handle order IDs without the TF- prefix."""
        order = self.tool.lookup("10001")
        
        assert order is not None
        assert order.order_id == "TF-10001"
    
    def test_lookup_case_insensitive(self):
        """Should handle lowercase order IDs."""
        order = self.tool.lookup("tf-10001")
        
        assert order is not None
        assert order.order_id == "TF-10001"
    
    def test_lookup_with_customer_verification(self):
        """Should verify customer ownership when customer_id provided."""
        # TF-10001 belongs to CUST-1001 in our mock data
        order = self.tool.lookup("TF-10001", customer_id="CUST-1001")
        
        assert order is not None
    
    def test_lookup_wrong_customer_returns_none(self):
        """Should return None if customer doesn't own the order."""
        # TF-10001 belongs to CUST-1001, not CUST-1002
        order = self.tool.lookup("TF-10001", customer_id="CUST-9999")
        
        assert order is None
