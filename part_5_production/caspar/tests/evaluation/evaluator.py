"""
Response quality evaluation framework.

Uses LLM-as-a-judge to assess agent responses.
"""

from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from caspar.config import settings


class EvaluationResult(BaseModel):
    """Result of evaluating a response."""
    
    relevance_score: float  # 0-1: How relevant is the response?
    accuracy_score: float   # 0-1: Is the information correct?
    helpfulness_score: float  # 0-1: Does it help the customer?
    tone_score: float       # 0-1: Is the tone appropriate?
    overall_score: float    # 0-1: Overall quality
    feedback: str           # Explanation of scores


class ResponseEvaluator:
    """Evaluates agent responses using LLM-as-a-judge."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.smart_model,  # Use better model for evaluation
            api_key=settings.openai_api_key,
            temperature=0,
        )
    
    def evaluate(
        self,
        customer_message: str,
        agent_response: str,
        expected_topics: list[str] | None = None,
        context: str | None = None,
    ) -> EvaluationResult:
        """
        Evaluate an agent response.
        
        Args:
            customer_message: What the customer asked
            agent_response: What the agent responded
            expected_topics: Topics that should be covered
            context: Additional context (e.g., order info, policies)
        """
        eval_prompt = f"""You are evaluating a customer service AI agent's response.

Customer Message: "{customer_message}"

Agent Response: "{agent_response}"

{f'Expected Topics: {", ".join(expected_topics)}' if expected_topics else ''}
{f'Context: {context}' if context else ''}

Evaluate the response on these criteria (0.0 to 1.0):

1. RELEVANCE: Does the response address what the customer asked?
2. ACCURACY: Is the information provided correct and not hallucinated?
3. HELPFULNESS: Does the response help solve the customer's problem?
4. TONE: Is the tone professional, friendly, and appropriate?

Respond in this exact format:
RELEVANCE: [score]
ACCURACY: [score]
HELPFULNESS: [score]
TONE: [score]
FEEDBACK: [1-2 sentence explanation]"""

        response = self.llm.invoke([HumanMessage(content=eval_prompt)])
        
        # Parse response
        scores = {"relevance": 0.5, "accuracy": 0.5, "helpfulness": 0.5, "tone": 0.5}
        feedback = "Unable to parse evaluation"
        
        for line in response.content.strip().split("\n"):
            line = line.strip()
            if line.startswith("RELEVANCE:"):
                scores["relevance"] = self._parse_score(line)
            elif line.startswith("ACCURACY:"):
                scores["accuracy"] = self._parse_score(line)
            elif line.startswith("HELPFULNESS:"):
                scores["helpfulness"] = self._parse_score(line)
            elif line.startswith("TONE:"):
                scores["tone"] = self._parse_score(line)
            elif line.startswith("FEEDBACK:"):
                feedback = line.split(":", 1)[1].strip()
        
        overall = sum(scores.values()) / len(scores)
        
        return EvaluationResult(
            relevance_score=scores["relevance"],
            accuracy_score=scores["accuracy"],
            helpfulness_score=scores["helpfulness"],
            tone_score=scores["tone"],
            overall_score=overall,
            feedback=feedback,
        )
    
    def _parse_score(self, line: str) -> float:
        """Parse a score from an evaluation line."""
        try:
            score_str = line.split(":")[1].strip()
            score = float(score_str)
            return max(0.0, min(1.0, score))
        except (IndexError, ValueError):
            return 0.5
