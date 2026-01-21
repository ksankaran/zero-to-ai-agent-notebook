"""Unit tests for escalation trigger detection."""

import pytest
from caspar.handoff.triggers import (
    check_escalation_triggers,
    check_sensitive_topics,
    EscalationTrigger,
)


class TestCheckEscalationTriggers:
    """Tests for check_escalation_triggers function."""
    
    def test_explicit_request_triggers_escalation(self):
        """Should trigger on explicit handoff request."""
        state = {"intent": "handoff_request"}
        
        result = check_escalation_triggers(state)
        
        assert result.should_escalate is True
        assert EscalationTrigger.EXPLICIT_REQUEST in result.triggers
        assert result.priority == "urgent"
    
    def test_high_frustration_triggers_escalation(self):
        """Should trigger on high frustration."""
        state = {
            "intent": "complaint",
            "sentiment_score": -0.8,
            "frustration_level": "high",
        }
        
        result = check_escalation_triggers(state)
        
        assert result.should_escalate is True
        assert EscalationTrigger.HIGH_FRUSTRATION in result.triggers
    
    def test_vip_customer_with_complaint_triggers(self):
        """Should trigger for VIP customers with complaints."""
        state = {
            "intent": "complaint",
            "sentiment_score": 0.0,
            "frustration_level": "medium",
        }
        
        result = check_escalation_triggers(state, customer_tier="gold")
        
        assert result.should_escalate is True
        assert EscalationTrigger.VIP_CUSTOMER in result.triggers
    
    def test_no_triggers_when_everything_ok(self):
        """Should not trigger when conversation is normal."""
        state = {
            "intent": "faq",
            "sentiment_score": 0.5,
            "frustration_level": "low",
            "turn_count": 2,
        }
        
        result = check_escalation_triggers(state)
        
        assert result.should_escalate is False
        assert len(result.triggers) == 0


class TestCheckSensitiveTopics:
    """Tests for sensitive topic detection."""
    
    def test_detects_legal_keywords(self):
        """Should detect legal-related keywords."""
        assert check_sensitive_topics("I'm going to sue you") is True
        assert check_sensitive_topics("I'll contact my lawyer") is True
        assert check_sensitive_topics("This is legal action") is True
    
    def test_detects_fraud_keywords(self):
        """Should detect fraud-related keywords."""
        assert check_sensitive_topics("This is fraud!") is True
        assert check_sensitive_topics("Someone scammed me") is True
        assert check_sensitive_topics("My card was stolen") is True
    
    def test_detects_safety_keywords(self):
        """Should detect safety-related keywords."""
        assert check_sensitive_topics("This product is dangerous") is True
        assert check_sensitive_topics("I was injured") is True
    
    def test_ignores_normal_messages(self):
        """Should not trigger on normal messages."""
        assert check_sensitive_topics("Where is my order?") is False
        assert check_sensitive_topics("I want to return this") is False
        assert check_sensitive_topics("What's your return policy?") is False
    
    def test_case_insensitive(self):
        """Should detect keywords regardless of case."""
        assert check_sensitive_topics("FRAUD") is True
        assert check_sensitive_topics("Lawyer") is True
