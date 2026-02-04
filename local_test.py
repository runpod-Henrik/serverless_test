#!/usr/bin/env python3
"""
Local testing script for the flaky test detector.
This simulates what RunPod does without needing the RunPod infrastructure.
"""
import json
from worker import handler


def main():
    # Load test input
    try:
        with open("test_input.json", "r") as f:
            test_input = json.load(f)
    except FileNotFoundError:
        print("❌ test_input.json not found")
        print("\nUsing default test configuration instead...")
        test_input = {
            "repo": "https://github.com/runpod-Henrik/serverless_test",
            "test_command": "pytest tests/test_flaky.py",
            "runs": 50,
            "parallelism": 5,
        }

    print("🔍 Running flaky test detector locally...")
    print(f"   Repository: {test_input['repo']}")
    print(f"   Test command: {test_input['test_command']}")
    print(f"   Runs: {test_input['runs']}")
    print(f"   Parallelism: {test_input['parallelism']}")
    print()

    # Simulate RunPod job format
    job = {"input": test_input}

    try:
        # Run the handler
        result = handler(job)

        # Display results
        print("\n" + "=" * 60)
        print("📊 RESULTS")
        print("=" * 60)
        print(f"Total runs:    {result['total_runs']}")
        print(f"Failures:      {result['failures']}")
        print(f"Passes:        {result['total_runs'] - result['failures']}")
        print(f"Repro rate:    {result['repro_rate'] * 100:.1f}%")
        print()

        # Show severity
        repro_rate = result["repro_rate"]
        if repro_rate > 0.9:
            print("🔴 CRITICAL: Very high failure rate (>90%) - likely a real bug!")
        elif repro_rate > 0.5:
            print("🟠 HIGH: Test fails frequently - needs investigation")
        elif repro_rate > 0.1:
            print("🟡 MEDIUM: Clear flaky behavior detected")
        elif repro_rate > 0:
            print("🟢 LOW: Occasional flakiness")
        else:
            print("✅ NONE: No flakiness detected")

        # Save detailed results
        with open("flaky_test_results.json", "w") as f:
            json.dump(result, f, indent=2)
        print("\n📄 Detailed results saved to: flaky_test_results.json")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
