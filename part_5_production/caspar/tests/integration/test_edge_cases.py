"""Integration tests for edge cases and unusual inputs."""

import pytest
from langchain_core.messages import HumanMessage

from caspar.agent import create_agent, create_initial_state


@pytest.mark.asyncio
async def test_empty_message():
    """Should handle empty messages gracefully."""
    agent = await create_agent()
    state = create_initial_state(conversation_id="test-empty", customer_id="CUST-1000")
    state["messages"] = [HumanMessage(content="")]
    
    config = {"configurable": {"thread_id": "test-empty"}}
    
    # Should not crash
    result = await agent.ainvoke(state, config)
    assert result is not None
    assert len(result["messages"]) > 0


@pytest.mark.asyncio
async def test_very_long_message():
    """Should handle very long messages."""
    agent = await create_agent()
    state = create_initial_state(conversation_id="test-long", customer_id="CUST-1000")
    
    # Create a long message
    long_message = "I have a question about my order. " * 100
    state["messages"] = [HumanMessage(content=long_message)]
    
    config = {"configurable": {"thread_id": "test-long"}}
    
    result = await agent.ainvoke(state, config)
    assert result is not None


@pytest.mark.asyncio
async def test_special_characters():
    """Should handle special characters in messages."""
    agent = await create_agent()
    state = create_initial_state(conversation_id="test-special", customer_id="CUST-1000")
    state["messages"] = [HumanMessage(content="What's the status of order #TF-10000? 🤔 <test> & more")]
    
    config = {"configurable": {"thread_id": "test-special"}}
    
    result = await agent.ainvoke(state, config)
    assert result is not None


@pytest.mark.asyncio
async def test_multiple_questions_in_one_message():
    """Should handle multiple questions in a single message."""
    agent = await create_agent()
    state = create_initial_state(conversation_id="test-multi-q", customer_id="CUST-1000")
    state["messages"] = [HumanMessage(
        content="Hi! Quick questions: What's your return policy? And do you offer warranties? Thanks!"
    )]
    
    config = {"configurable": {"thread_id": "test-multi-q"}}
    
    result = await agent.ainvoke(state, config)
    response = result["messages"][-1].content.lower()
    
    # Should address at least some of the questions OR escalate for complex request
    addressed_topics = any(word in response for word in ["return", "warranty", "policy", "day"])
    escalated = result.get("needs_escalation", False) or "human" in response or "agent" in response
    
    assert addressed_topics or escalated, \
        f"Should address topics or escalate complex request: {response[:200]}"


@pytest.mark.asyncio
async def test_all_caps_message():
    """Should handle ALL CAPS messages (often indicate frustration)."""
    agent = await create_agent()
    state = create_initial_state(conversation_id="test-caps", customer_id="CUST-1000")
    state["messages"] = [HumanMessage(content="WHERE IS MY ORDER THIS IS TAKING TOO LONG")]
    
    config = {"configurable": {"thread_id": "test-caps"}}
    
    result = await agent.ainvoke(state, config)
    
    # Should recognize as order inquiry or complaint
    assert result["intent"] in ["order_inquiry", "complaint"], \
        f"ALL CAPS should be recognized as order/complaint: {result['intent']}"


@pytest.mark.asyncio
async def test_greeting_only():
    """Should handle simple greetings."""
    agent = await create_agent()
    state = create_initial_state(conversation_id="test-greeting", customer_id="CUST-1000")
    state["messages"] = [HumanMessage(content="Hello!")]
    
    config = {"configurable": {"thread_id": "test-greeting"}}
    
    result = await agent.ainvoke(state, config)
    response = result["messages"][-1].content.lower()
    
    # Should respond with a greeting
    assert any(word in response for word in ["hello", "hi", "help", "welcome"]), \
        f"Should greet the customer: {response}"


@pytest.mark.asyncio
async def test_typos_and_misspellings():
    """Should handle messages with typos."""
    agent = await create_agent()
    state = create_initial_state(conversation_id="test-typos", customer_id="CUST-1000")
    state["messages"] = [HumanMessage(content="waht is ur retrun polcy?")]
    
    config = {"configurable": {"thread_id": "test-typos"}}
    
    result = await agent.ainvoke(state, config)
    
    # Should still classify as FAQ about returns
    assert result["intent"] == "faq", f"Should understand despite typos: {result['intent']}"
