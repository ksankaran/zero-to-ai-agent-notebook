"""Integration tests for intent classification."""

import pytest
from langchain_core.messages import HumanMessage

from caspar.agent import create_agent, create_initial_state


@pytest.mark.asyncio
async def test_faq_intent_classification():
    """Should classify FAQ questions correctly."""
    agent = await create_agent()
    state = create_initial_state(conversation_id="test-faq", customer_id="CUST-1000")
    
    test_cases = [
        "What is your return policy?",
        "How long does shipping take?",
        "Do you offer warranties?",
        "What payment methods do you accept?",
    ]
    
    for message in test_cases:
        state["messages"] = [HumanMessage(content=message)]
        config = {"configurable": {"thread_id": f"test-faq-{hash(message)}"}}
        
        result = await agent.ainvoke(state, config)
        
        assert result["intent"] == "faq", f"Expected 'faq' for: {message}, got: {result['intent']}"


@pytest.mark.asyncio
async def test_order_inquiry_intent_classification():
    """Should classify order inquiries correctly."""
    agent = await create_agent()
    # CUST-1000 owns TF-10000, TF-10005, TF-10010, TF-10015
    state = create_initial_state(conversation_id="test-order", customer_id="CUST-1000")
    
    test_cases = [
        "Where is my order TF-10000?",
        "I want to track my order",
        "What's the status of order 10005?",
        "When will my package arrive?",
    ]
    
    for message in test_cases:
        state["messages"] = [HumanMessage(content=message)]
        config = {"configurable": {"thread_id": f"test-order-{hash(message)}"}}
        
        result = await agent.ainvoke(state, config)
        
        assert result["intent"] == "order_inquiry", f"Expected 'order_inquiry' for: {message}, got: {result['intent']}"


@pytest.mark.asyncio
async def test_complaint_intent_classification():
    """Should classify complaints correctly."""
    agent = await create_agent()
    state = create_initial_state(conversation_id="test-complaint", customer_id="CUST-1000")
    
    test_cases = [
        "This product is terrible!",
        "I'm very disappointed with my purchase",
        "Your service is awful",
        "My item arrived damaged and I'm furious",
    ]
    
    for message in test_cases:
        state["messages"] = [HumanMessage(content=message)]
        config = {"configurable": {"thread_id": f"test-complaint-{hash(message)}"}}
        
        result = await agent.ainvoke(state, config)
        
        assert result["intent"] == "complaint", f"Expected 'complaint' for: {message}, got: {result['intent']}"


@pytest.mark.asyncio
async def test_handoff_request_classification():
    """Should classify handoff requests correctly."""
    agent = await create_agent()
    state = create_initial_state(conversation_id="test-handoff", customer_id="CUST-1000")
    
    test_cases = [
        "I want to speak to a human",
        "Let me talk to a real person",
        "Connect me with an agent",
        "I need human support please",
    ]
    
    for message in test_cases:
        state["messages"] = [HumanMessage(content=message)]
        config = {"configurable": {"thread_id": f"test-handoff-{hash(message)}"}}
        
        result = await agent.ainvoke(state, config)
        
        assert result["intent"] == "handoff_request", f"Expected 'handoff_request' for: {message}, got: {result['intent']}"
