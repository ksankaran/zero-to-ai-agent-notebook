"""
Test dataset for systematic evaluation.

This dataset covers various scenarios the agent should handle.
"""

TEST_CASES = [
    # FAQ Questions
    {
        "category": "faq",
        "input": "What is your return policy?",
        "expected_intent": "faq",
        "expected_topics": ["return", "30 days"],
        "min_quality_score": 0.7,
    },
    {
        "category": "faq",
        "input": "How long does shipping take?",
        "expected_intent": "faq",
        "expected_topics": ["shipping", "days", "delivery"],
        "min_quality_score": 0.7,
    },
    {
        "category": "faq",
        "input": "Do you offer warranties on laptops?",
        "expected_intent": "faq",
        "expected_topics": ["warranty", "year"],
        "min_quality_score": 0.7,
    },
    
    # Order Inquiries
    {
        "category": "order",
        "input": "Where is my order TF-10000?",
        "expected_intent": "order_inquiry",
        "expected_topics": ["order", "status"],
        "min_quality_score": 0.7,
    },
    {
        "category": "order",
        "input": "I want to track my package",
        "expected_intent": "order_inquiry",
        "expected_topics": ["track", "order"],
        "min_quality_score": 0.6,
    },
    
    # Complaints
    {
        "category": "complaint",
        "input": "This product is defective and I want a refund!",
        "expected_intent": "complaint",
        "expected_topics": ["sorry", "help", "refund"],
        "min_quality_score": 0.7,
        "expect_ticket": True,
    },
    {
        "category": "complaint",
        "input": "I've been waiting 3 weeks for my order. This is ridiculous!",
        "expected_intent": "complaint",
        "expected_topics": ["apologize", "order", "help"],
        "min_quality_score": 0.7,
    },
    
    # Handoff Requests
    {
        "category": "handoff",
        "input": "I want to speak to a human agent",
        "expected_intent": "handoff_request",
        "expected_topics": ["human", "agent", "help"],
        "min_quality_score": 0.7,
        "expect_escalation": True,
    },
    
    # Edge Cases
    {
        "category": "edge",
        "input": "Hi",
        "expected_intent": "general",
        "expected_topics": ["hello", "help"],
        "min_quality_score": 0.6,
    },
    {
        "category": "edge",
        "input": "",
        "expected_intent": "general",
        "min_quality_score": 0.0,  # Empty input, just shouldn't crash
    },
]
