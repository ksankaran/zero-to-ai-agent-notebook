"""
Unified test runner for CASPAR.

Run different test suites based on the situation.
"""

import subprocess
import sys
import argparse


def run_unit_tests():
    """Run fast unit tests."""
    print("\n🧪 Running Unit Tests...")
    result = subprocess.run(
        ["pytest", "tests/unit/", "-v", "--tb=short"],
        capture_output=False
    )
    return result.returncode == 0


def run_integration_tests():
    """Run integration tests (requires API key)."""
    print("\n🔗 Running Integration Tests...")
    result = subprocess.run(
        ["pytest", "tests/integration/", "-v", "--tb=short", "--timeout=60"],
        capture_output=False
    )
    return result.returncode == 0


def run_evaluation_tests():
    """Run evaluation tests (slowest, most thorough)."""
    print("\n📊 Running Evaluation Tests...")
    result = subprocess.run(
        ["pytest", "tests/evaluation/", "-v", "--tb=short", "--timeout=120"],
        capture_output=False
    )
    return result.returncode == 0


def run_all_tests():
    """Run all test suites."""
    results = {
        "unit": run_unit_tests(),
        "integration": run_integration_tests(),
        "evaluation": run_evaluation_tests(),
    }
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for suite, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {suite.capitalize()}: {status}")
    
    all_passed = all(results.values())
    print(f"\nOverall: {'✅ ALL PASSED' if all_passed else '❌ SOME FAILED'}")
    
    return all_passed


def main():
    parser = argparse.ArgumentParser(description="Run CASPAR tests")
    parser.add_argument(
        "--suite",
        choices=["unit", "integration", "evaluation", "all"],
        default="unit",
        help="Which test suite to run (default: unit)"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run only unit tests (fastest)"
    )
    
    args = parser.parse_args()
    
    if args.quick:
        success = run_unit_tests()
    elif args.suite == "unit":
        success = run_unit_tests()
    elif args.suite == "integration":
        success = run_integration_tests()
    elif args.suite == "evaluation":
        success = run_evaluation_tests()
    else:
        success = run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
