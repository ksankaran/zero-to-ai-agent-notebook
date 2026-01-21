"""Integration tests for complete conversation flows."""

import pytest
from langchain_core.messages import HumanMessage

from caspar.agent import create_agent, create_initial_state


@pytest.mark.asyncio
async def test_faq_flow_returns_relevant_info():
    """FAQ flow should return relevant policy information."""
    agent = await create_agent()
    state = create_initial_state(conversation_id="test-faq-flow", customer_id="CUST-1000")
    state["messages"] = [HumanMessage(content="What is your return policy?")]
    
    config = {"configurable": {"thread_id": "test-faq-flow"}}
    result = await agent.ainvoke(state, config)
    
    response = result["messages"][-1].content.lower()
    
    # Should mention key return policy details
    assert any(word in response for word in ["return", "30", "day", "refund"]), \
        f"Response should mention return policy details: {response}"


@pytest.mark.asyncio
async def test_order_inquiry_with_valid_order():
    """Order inquiry should return order details for valid orders."""
    agent = await create_agent()
    # Use CUST-1000 with TF-10000 (TF-10000 belongs to CUST-1000)
    state = create_initial_state(conversation_id="test-order-flow", customer_id="CUST-1000")
    # Use polite phrasing to reduce chance of sentiment escalation
    state["messages"] = [HumanMessage(content="Hi! Could you please check the status of order TF-10000? Thanks!")]
    
    config = {"configurable": {"thread_id": "test-order-flow"}}
    result = await agent.ainvoke(state, config)
    
    # The order lookup should have succeeded - check the state
    # Note: Even if sentiment triggers escalation, order_info should be populated
    order_info = result.get("order_info")
    
    # order_info should exist and have status (not error) when order is found
    assert order_info is not None, \
        f"Order info should be in state. Got: {order_info}"
    assert "status" in order_info, \
        f"Order should be found (has status). Got: {order_info}"
    assert "error" not in order_info, \
        f"Order lookup should not have error. Got: {order_info}"


@pytest.mark.asyncio
async def test_order_inquiry_with_invalid_order():
    """Order inquiry should handle invalid orders gracefully."""
    agent = await create_agent()
    state = create_initial_state(conversation_id="test-invalid-order", customer_id="CUST-1000")
    state["messages"] = [HumanMessage(content="Where is my order TF-99999?")]
    
    config = {"configurable": {"thread_id": "test-invalid-order"}}
    result = await agent.ainvoke(state, config)
    
    response = result["messages"][-1].content.lower()
    
    # Should either indicate order not found OR escalate to human
    # (escalation is acceptable when we can't find the order)
    order_not_found = any(phrase in response for phrase in ["not found", "couldn't find", "unable to locate", "check", "verify"])
    escalated = result.get("needs_escalation", False) or "human" in response or "agent" in response
    
    assert order_not_found or escalated, \
        f"Response should indicate order not found or escalate: {response}"


@pytest.mark.asyncio
async def test_complaint_creates_ticket():
    """Complaints should create a support ticket."""
    agent = await create_agent()
    state = create_initial_state(conversation_id="test-complaint-ticket", customer_id="CUST-1000")
    state["messages"] = [HumanMessage(content="My laptop arrived completely broken! This is unacceptable!")]
    
    config = {"configurable": {"thread_id": "test-complaint-ticket"}}
    result = await agent.ainvoke(state, config)
    
    # Should have created a ticket
    assert result.get("ticket_id") is not None, "Complaint should create a ticket"
    assert result["ticket_id"].startswith("TKT-"), f"Invalid ticket ID: {result.get('ticket_id')}"


@pytest.mark.asyncio
async def test_handoff_request_triggers_escalation():
    """Explicit handoff requests should trigger escalation."""
    agent = await create_agent()
    state = create_initial_state(conversation_id="test-explicit-handoff", customer_id="CUST-1000")
    state["messages"] = [HumanMessage(content="I want to speak to a human agent please")]
    
    config = {"configurable": {"thread_id": "test-explicit-handoff"}}
    result = await agent.ainvoke(state, config)
    
    # Should be escalated
    assert result.get("needs_escalation") is True, "Handoff request should trigger escalation"
    assert result.get("ticket_id") is not None, "Handoff should create a ticket"
    
    # Response should acknowledge the handoff
    response = result["messages"][-1].content.lower()
    assert any(word in response for word in ["human", "agent", "team", "reach"]), \
        f"Response should mention human handoff: {response}"
