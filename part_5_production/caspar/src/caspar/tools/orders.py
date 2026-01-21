# From: Zero to AI Agent, Chapter 20, Section 20.4
# File: src/caspar/tools/orders.py

"""
Order Lookup Tool

Provides order status and tracking information.
In production, this would connect to your order management system.
"""

from datetime import datetime, timedelta, timezone
from typing import Literal
from pydantic import BaseModel, Field
import random

from caspar.config import get_logger

logger = get_logger(__name__)


class OrderInfo(BaseModel):
    """Information about a customer order."""
    
    order_id: str
    customer_id: str
    status: Literal["processing", "shipped", "delivered", "cancelled", "returned"]
    items: list[dict]
    total: float
    order_date: str
    shipping_method: str
    tracking_number: str | None = None
    estimated_delivery: str | None = None
    delivery_date: str | None = None


class OrderLookupTool:
    """
    Tool for looking up order information.
    
    In production, this would query your order management system.
    For demo purposes, we use mock data.
    """
    
    def __init__(self):
        self._mock_orders = self._generate_mock_orders()
    
    def _generate_mock_orders(self) -> dict[str, OrderInfo]:
        """Generate mock order data for testing."""
        
        products = [
            {"name": "TechFlow Pro 15 Laptop", "price": 1299.00, "quantity": 1},
            {"name": "TechFlow Wireless Earbuds", "price": 129.00, "quantity": 1},
            {"name": "TechFlow USB-C Hub", "price": 79.00, "quantity": 2},
            {"name": "TechFlow Phone 12", "price": 799.00, "quantity": 1},
            {"name": "TechFlow Tab 10", "price": 449.00, "quantity": 1},
        ]
        
        statuses = ["processing", "shipped", "delivered", "shipped", "delivered"]
        shipping_methods = ["standard", "express", "overnight"]
        
        orders = {}
        base_date = datetime.now()
        
        # Generate 20 mock orders
        for i in range(20):
            order_id = f"TF-{10000 + i}"
            customer_id = f"CUST-{1000 + (i % 5)}"
            
            num_items = random.randint(1, 3)
            order_items = random.sample(products, num_items)
            total = sum(item["price"] * item["quantity"] for item in order_items)
            
            status = statuses[i % len(statuses)]
            shipping = shipping_methods[i % len(shipping_methods)]
            order_date = base_date - timedelta(days=random.randint(1, 30))
            
            # Add tracking for shipped/delivered orders
            tracking = None
            estimated_delivery = None
            delivery_date = None
            
            if status in ["shipped", "delivered"]:
                tracking = f"1Z999AA{10000000 + i}"
                est_days = {"standard": 7, "express": 3, "overnight": 1}[shipping]
                estimated_delivery = (order_date + timedelta(days=est_days)).strftime("%Y-%m-%d")
                
                if status == "delivered":
                    delivery_date = estimated_delivery
            
            orders[order_id] = OrderInfo(
                order_id=order_id,
                customer_id=customer_id,
                status=status,
                items=order_items,
                total=total,
                order_date=order_date.strftime("%Y-%m-%d"),
                shipping_method=shipping,
                tracking_number=tracking,
                estimated_delivery=estimated_delivery,
                delivery_date=delivery_date,
            )
        
        return orders
    
    def lookup(self, order_id: str, customer_id: str | None = None) -> OrderInfo | None:
        """
        Look up an order by ID.
        
        Args:
            order_id: The order ID to look up
            customer_id: Optional customer ID for verification
            
        Returns:
            OrderInfo if found, None otherwise
        """
        logger.info("order_lookup", order_id=order_id, customer_id=customer_id)
        
        # Normalize order ID (accept "10001" or "TF-10001")
        order_id = order_id.upper().strip()
        if not order_id.startswith("TF-"):
            order_id = f"TF-{order_id}"
        
        order = self._mock_orders.get(order_id)
        
        if order is None:
            logger.warning("order_not_found", order_id=order_id)
            return None
        
        # Security: verify customer owns this order
        if customer_id and order.customer_id != customer_id:
            logger.warning("order_customer_mismatch", order_id=order_id)
            return None
        
        logger.info("order_found", order_id=order_id, status=order.status)
        return order
    
    def get_tracking_url(self, tracking_number: str) -> str:
        """Generate a tracking URL for a shipment."""
        return f"https://track.techflow.com/{tracking_number}"
    
    def format_order_summary(self, order: OrderInfo) -> str:
        """Format order information for display to customer."""
        
        lines = [
            f"**Order {order.order_id}**",
            f"Status: {order.status.upper()}",
            f"Order Date: {order.order_date}",
            f"Shipping: {order.shipping_method.title()}",
            "",
            "Items:",
        ]
        
        for item in order.items:
            lines.append(f"  • {item['name']} (x{item['quantity']}) - ${item['price']:.2f}")
        
        lines.append(f"\nTotal: ${order.total:.2f}")
        
        if order.tracking_number:
            lines.append(f"\nTracking: {order.tracking_number}")
            lines.append(f"Track at: {self.get_tracking_url(order.tracking_number)}")
        
        if order.status == "shipped" and order.estimated_delivery:
            lines.append(f"Expected Delivery: {order.estimated_delivery}")
        elif order.status == "delivered" and order.delivery_date:
            lines.append(f"Delivered: {order.delivery_date}")
        
        return "\n".join(lines)


# Singleton instance
_order_tool: OrderLookupTool | None = None


def get_order_tool() -> OrderLookupTool:
    """Get or create the order lookup tool instance."""
    global _order_tool
    if _order_tool is None:
        _order_tool = OrderLookupTool()
    return _order_tool


def get_order_status(order_id: str, customer_id: str | None = None) -> dict:
    """
    Convenience function to look up order status.
    
    Returns a dict with order info or error message.
    """
    tool = get_order_tool()
    order = tool.lookup(order_id, customer_id)
    
    if order is None:
        return {
            "found": False,
            "error": f"Order {order_id} not found. Please check the order number and try again."
        }
    
    return {
        "found": True,
        "order": order.model_dump(),
        "summary": tool.format_order_summary(order)
    }
