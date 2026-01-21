# From: Zero to AI Agent, Chapter 20, Section 20.5
# File: scripts/test_handoff.py

"""Test the human handoff system."""

import asyncio
from langchain_core.messages import HumanMessage

from caspar.agent import create_agent, create_initial_state
from caspar.handoff import get_handoff_queue, format_context_for_display
from caspar.config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


async def test_explicit_handoff():
    """Test explicit request for human agent."""
    print("\n" + "=" * 60)
    print("🧪 Test: Explicit Handoff Request")
    print("=" * 60)
    
    agent = await create_agent()
    state = create_initial_state(
        conversation_id="test-handoff-explicit",
        customer_id="CUST-1000"
    )
    state["messages"] = [HumanMessage(content="I want to talk to a real person please")]
    
    config = {"configurable": {"thread_id": "test-handoff-explicit"}}
    result = await agent.ainvoke(state, config)
    
    print(f"Intent: {result['intent']}")
    print(f"Escalated: {result.get('needs_escalation')}")
    print(f"Ticket: {result.get('ticket_id')}")
    print(f"\nCASPAR Response:\n{result['messages'][-1].content}")
    
    # Check queue
    queue = get_handoff_queue()
    request = queue.get_by_conversation("test-handoff-explicit")
    if request:
        print(f"\n📋 Queue Position: {queue.get_queue_position(request.request_id)}")
        print(f"   Priority: {request.priority}")
        print(f"   Est. Wait: {request.estimated_wait} minutes")


async def test_frustration_escalation():
    """Test escalation triggered by frustration."""
    print("\n" + "=" * 60)
    print("🧪 Test: Frustration-Triggered Escalation")
    print("=" * 60)
    
    agent = await create_agent()
    state = create_initial_state(
        conversation_id="test-handoff-frustration",
        customer_id="CUST-1001"
    )
    
    # Simulate a frustrated customer
    state["messages"] = [
        HumanMessage(content="Where is my order?! I've been waiting for weeks!"),
    ]
    
    config = {"configurable": {"thread_id": "test-handoff-frustration"}}
    result = await agent.ainvoke(state, config)
    
    print(f"Intent: {result['intent']}")
    print(f"Sentiment: {result.get('sentiment_score')}")
    print(f"Frustration: {result.get('frustration_level')}")
    print(f"Escalated: {result.get('needs_escalation')}")
    print(f"\nCASPAR Response:\n{result['messages'][-1].content[:300]}...")


async def test_vip_customer():
    """Test VIP customer gets priority handling."""
    print("\n" + "=" * 60)
    print("🧪 Test: VIP Customer Handling")
    print("=" * 60)
    
    agent = await create_agent()
    
    # CUST-1003 is a gold tier customer in our mock data
    state = create_initial_state(
        conversation_id="test-handoff-vip",
        customer_id="CUST-1003"
    )
    state["messages"] = [
        HumanMessage(content="I have an issue with my recent order and I'm not happy about it."),
    ]
    
    config = {"configurable": {"thread_id": "test-handoff-vip"}}
    result = await agent.ainvoke(state, config)
    
    print(f"Intent: {result['intent']}")
    print(f"Escalated: {result.get('needs_escalation')}")
    
    queue = get_handoff_queue()
    request = queue.get_by_conversation("test-handoff-vip")
    if request:
        print(f"Priority: {request.priority}")
        print(f"Triggers: {request.triggers}")


async def test_sensitive_topic():
    """Test sensitive topic detection."""
    print("\n" + "=" * 60)
    print("🧪 Test: Sensitive Topic Detection")
    print("=" * 60)
    
    agent = await create_agent()
    state = create_initial_state(
        conversation_id="test-handoff-sensitive",
        customer_id="CUST-1000"
    )
    state["messages"] = [
        HumanMessage(content="I think this might be fraud. Someone used my card without permission."),
    ]
    
    config = {"configurable": {"thread_id": "test-handoff-sensitive"}}
    result = await agent.ainvoke(state, config)
    
    print(f"Intent: {result['intent']}")
    print(f"Escalated: {result.get('needs_escalation')}")
    print(f"Reason: {result.get('escalation_reason', 'N/A')}")
    print(f"\nCASPAR Response:\n{result['messages'][-1].content[:300]}...")


async def test_queue_management():
    """Test queue management with multiple requests."""
    print("\n" + "=" * 60)
    print("🧪 Test: Queue Management")
    print("=" * 60)
    
    queue = get_handoff_queue()
    
    # Add several requests with different priorities
    requests = [
        ("conv-1", "CUST-1000", "medium", ["general"], "General inquiry"),
        ("conv-2", "CUST-1001", "urgent", ["explicit_request"], "Customer requested agent"),
        ("conv-3", "CUST-1002", "high", ["vip_customer"], "VIP with issue"),
        ("conv-4", "CUST-1003", "low", ["general"], "Simple question"),
    ]
    
    for conv_id, cust_id, priority, triggers, reason in requests:
        queue.add(conv_id, cust_id, priority, triggers, reason)
    
    print("\n📊 Queue Status:")
    counts = queue.get_pending_count()
    for priority, count in counts.items():
        print(f"   {priority.upper()}: {count}")
    
    print("\n📋 Queue Order (by priority):")
    for conv_id, _, _, _, _ in requests:
        req = queue.get_by_conversation(conv_id)
        if req:
            pos = queue.get_queue_position(req.request_id)
            print(f"   #{pos}: {req.conversation_id} ({req.priority})")


async def main():
    """Run all handoff tests."""
    
    await test_explicit_handoff()
    await test_frustration_escalation()
    await test_vip_customer()
    await test_sensitive_topic()
    await test_queue_management()
    
    print("\n" + "=" * 60)
    print("✅ All handoff tests complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
