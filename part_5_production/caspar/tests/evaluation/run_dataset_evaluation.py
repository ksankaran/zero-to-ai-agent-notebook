"""Run evaluation on the full test dataset."""

import asyncio
import json
from datetime import datetime
from langchain_core.messages import HumanMessage

from caspar.agent import create_agent, create_initial_state
from .evaluator import ResponseEvaluator
from .test_dataset import TEST_CASES


async def evaluate_dataset():
    """Run evaluation on all test cases."""
    agent = await create_agent()
    evaluator = ResponseEvaluator()
    
    results = []
    passed = 0
    failed = 0
    
    print(f"\n{'=' * 60}")
    print(f"Running evaluation on {len(TEST_CASES)} test cases")
    print(f"{'=' * 60}\n")
    
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"[{i}/{len(TEST_CASES)}] Testing: {test_case['category']} - {test_case['input'][:40]}...")
        
        # Skip empty input test
        if not test_case["input"]:
            print("  ⏭️  Skipped (empty input)")
            continue
        
        # Run agent
        state = create_initial_state(
            conversation_id=f"eval-{i}",
            customer_id="CUST-1000"
        )
        state["messages"] = [HumanMessage(content=test_case["input"])]
        
        config = {"configurable": {"thread_id": f"eval-{i}"}}
        result = await agent.ainvoke(state, config)
        
        response = result["messages"][-1].content
        
        # Check intent
        intent_correct = result["intent"] == test_case["expected_intent"]
        
        # Evaluate quality
        evaluation = evaluator.evaluate(
            customer_message=test_case["input"],
            agent_response=response,
            expected_topics=test_case.get("expected_topics", []),
        )
        
        quality_passed = evaluation.overall_score >= test_case["min_quality_score"]
        
        # Check special expectations
        escalation_correct = True
        ticket_correct = True
        
        if test_case.get("expect_escalation"):
            escalation_correct = result.get("needs_escalation", False)
        
        if test_case.get("expect_ticket"):
            ticket_correct = result.get("ticket_id") is not None
        
        # Overall pass/fail
        test_passed = intent_correct and quality_passed and escalation_correct and ticket_correct
        
        if test_passed:
            passed += 1
            print(f"  ✅ Passed (score: {evaluation.overall_score:.2f})")
        else:
            failed += 1
            print(f"  ❌ Failed")
            if not intent_correct:
                print(f"     Intent: expected {test_case['expected_intent']}, got {result['intent']}")
            if not quality_passed:
                print(f"     Quality: {evaluation.overall_score:.2f} < {test_case['min_quality_score']}")
            if not escalation_correct:
                print(f"     Escalation: expected but not triggered")
            if not ticket_correct:
                print(f"     Ticket: expected but not created")
        
        results.append({
            "test_case": test_case,
            "intent": result["intent"],
            "intent_correct": intent_correct,
            "evaluation": evaluation.model_dump(),
            "quality_passed": quality_passed,
            "test_passed": test_passed,
        })
    
    # Summary
    print(f"\n{'=' * 60}")
    print(f"EVALUATION SUMMARY")
    print(f"{'=' * 60}")
    print(f"Passed: {passed}/{len(TEST_CASES)} ({100*passed/len(TEST_CASES):.1f}%)")
    print(f"Failed: {failed}/{len(TEST_CASES)}")
    
    # Save results
    output_file = f"evaluation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to: {output_file}")
    
    return results


if __name__ == "__main__":
    asyncio.run(evaluate_dataset())
