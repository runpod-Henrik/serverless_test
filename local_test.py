#!/usr/bin/env python3
"""
Local testing script for the flaky test detector.
This simulates what RunPod does without needing the RunPod infrastructure.
"""
# Import handler directly by loading the module without starting serverless
import importlib.util
import json
import os
import sys

# Add project directory to sys.path to ensure worker.py can import config
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

worker_path = os.path.join(project_dir, "worker.py")
spec = importlib.util.spec_from_file_location("worker_module", worker_path)
worker_module = importlib.util.module_from_spec(spec)
sys.modules["worker_module"] = worker_module

# Temporarily disable runpod.serverless.start
import runpod

original_start = runpod.serverless.start
runpod.serverless.start = lambda x: None

# Now load the worker module
spec.loader.exec_module(worker_module)
handler = worker_module.handler

# Restore original
runpod.serverless.start = original_start


def main():
    # Load test input
    try:
        test_input_path = os.path.join(project_dir, "test_input.json")
        with open(test_input_path) as f:
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

    # Validate input configuration
    try:
        from validate_input import validate_and_report
        if not validate_and_report(test_input, "test_input.json"):
            return 1
    except ImportError:
        # validate_input module not available - skip validation
        pass
    except Exception as e:
        print(f"⚠️  Warning: Could not validate configuration: {e}")
        print("   Proceeding anyway...")

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
        results_path = os.path.join(project_dir, "flaky_test_results.json")
        with open(results_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\n📄 Detailed results saved to: {results_path}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
