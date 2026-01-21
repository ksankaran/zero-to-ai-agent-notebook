"""Evaluation tests for response quality."""

import pytest
from langchain_core.messages import HumanMessage

from caspar.agent import create_agent, create_initial_state
from .evaluator import ResponseEvaluator


@pytest.fixture
def evaluator():
    """Create a response evaluator."""
    return ResponseEvaluator()


@pytest.mark.asyncio
async def test_faq_response_quality(evaluator):
    """FAQ responses should be high quality."""
    agent = await create_agent()
    state = create_initial_state(conversation_id="eval-faq", customer_id="CUST-1000")
    state["messages"] = [HumanMessage(content="What is your return policy?")]
    
    config = {"configurable": {"thread_id": "eval-faq"}}
    result = await agent.ainvoke(state, config)
    
    response = result["messages"][-1].content
    
    evaluation = evaluator.evaluate(
        customer_message="What is your return policy?",
        agent_response=response,
        expected_topics=["return", "30 days", "refund"],
        context="TechFlow has a 30-day return policy for most items.",
    )
    
    assert evaluation.relevance_score >= 0.7, f"Low relevance: {evaluation.feedback}"
    assert evaluation.overall_score >= 0.7, f"Low overall score: {evaluation.feedback}"


@pytest.mark.asyncio
async def test_complaint_response_quality(evaluator):
    """Complaint responses should be empathetic and helpful."""
    agent = await create_agent()
    state = create_initial_state(conversation_id="eval-complaint", customer_id="CUST-1000")
    state["messages"] = [HumanMessage(content="My laptop arrived damaged! I'm very upset!")]
    
    config = {"configurable": {"thread_id": "eval-complaint"}}
    result = await agent.ainvoke(state, config)
    
    response = result["messages"][-1].content
    
    evaluation = evaluator.evaluate(
        customer_message="My laptop arrived damaged! I'm very upset!",
        agent_response=response,
        expected_topics=["apologize", "understand", "help", "ticket"],
    )
    
    assert evaluation.tone_score >= 0.7, f"Tone not empathetic enough: {evaluation.feedback}"
    assert evaluation.helpfulness_score >= 0.6, f"Not helpful enough: {evaluation.feedback}"


@pytest.mark.asyncio
async def test_order_status_response_accuracy(evaluator):
    """Order status responses should be accurate."""
    agent = await create_agent()
    # Use CUST-1000 with TF-10000 (matching ownership)
    state = create_initial_state(conversation_id="eval-order", customer_id="CUST-1000")
    state["messages"] = [HumanMessage(content="Where is my order TF-10000?")]
    
    config = {"configurable": {"thread_id": "eval-order"}}
    result = await agent.ainvoke(state, config)
    
    response = result["messages"][-1].content
    
    evaluation = evaluator.evaluate(
        customer_message="Where is my order TF-10000?",
        agent_response=response,
        expected_topics=["order", "status", "TF-10000"],
    )
    
    assert evaluation.accuracy_score >= 0.7, f"Inaccurate response: {evaluation.feedback}"
