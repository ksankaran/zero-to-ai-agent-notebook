"""
Shared test fixtures and utilities.

pytest automatically discovers this file and makes fixtures
available to all tests.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from langchain_core.messages import HumanMessage, AIMessage

from caspar.agent import create_initial_state


@pytest.fixture
def sample_state():
    """Create a sample agent state for testing."""
    return create_initial_state(
        conversation_id="test-conv-001",
        customer_id="CUST-1000"
    )


@pytest.fixture
def sample_state_with_messages():
    """Create a state with some conversation history."""
    state = create_initial_state(
        conversation_id="test-conv-002",
        customer_id="CUST-1000"
    )
    state["messages"] = [
        HumanMessage(content="Hi, I have a question about my order"),
        AIMessage(content="Hello! I'd be happy to help with your order. Could you provide your order number?"),
        HumanMessage(content="It's TF-10001"),
    ]
    return state


@pytest.fixture
def mock_llm():
    """Create a mock LLM for testing without API calls."""
    mock = MagicMock()
    mock.invoke = MagicMock(return_value=MagicMock(content="mocked response"))
    return mock


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
