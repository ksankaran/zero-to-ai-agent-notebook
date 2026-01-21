# From: Zero to AI Agent, Chapter 20, Section 20.4
# File: scripts/test_conversation_flow.py

"""Test complete conversation flows through CASPAR."""

import asyncio
from langchain_core.messages import HumanMessage

from caspar.agent import create_agent, create_initial_state
from caspar.config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


async def test_flow(name: str, message: str, customer_id: str = "CUST-1000"):
    """Run a single test flow."""
    print(f"\n{'=' * 60}")
    print(f"🧪 Test: {name}")
    print(f"{'=' * 60}")
    
    agent = await create_agent()
    state = create_initial_state(conversation_id=f"test-{name}", customer_id=customer_id)
    state["messages"] = [HumanMessage(content=message)]
    
    config = {"configurable": {"thread_id": f"test-{name}"}}
    result = await agent.ainvoke(state, config)
    
    print(f"Customer: {message}")
    print(f"Intent: {result['intent']}")
    print(f"Sentiment: {result.get('sentiment_score', 'N/A')}")
    if result.get('ticket_id'):
        print(f"Ticket: {result['ticket_id']}")
    print(f"\nCASPAR: {result['messages'][-1].content}")
    
    return result


async def main():
    """Run all tests."""
    
    # Test FAQ
    await test_flow("FAQ", "What is your return policy?")
    
    # Test Order Inquiry
    await test_flow("Order", "Where is my order TF-10001?")
    
    # Test Account
    await test_flow("Account", "What's my loyalty status?", "CUST-1001")
    
    # Test Complaint
    await test_flow("Complaint", "My laptop arrived damaged! This is unacceptable!")
    
    # Test Handoff
    await test_flow("Handoff", "I want to speak to a human agent please")
    
    print(f"\n{'=' * 60}")
    print("✅ All tests complete!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())
