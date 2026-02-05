#!/usr/bin/env python3
"""
Local testing script for the flaky test detector.
This simulates what RunPod does without needing the RunPod infrastructure.
"""

# Import handler directly by loading the module without starting serverless
import argparse
import importlib.util
import json
import os
import sys
import time
from datetime import datetime

import runpod  # noqa: E402

# Add project directory to sys.path to ensure worker.py can import config
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

worker_path = os.path.join(project_dir, "worker.py")
spec = importlib.util.spec_from_file_location("worker_module", worker_path)
worker_module = importlib.util.module_from_spec(spec)
sys.modules["worker_module"] = worker_module

# Temporarily disable runpod.serverless.start

original_start = runpod.serverless.start
runpod.serverless.start = lambda x: None

# Now load the worker module
spec.loader.exec_module(worker_module)
handler = worker_module.handler

# Restore original
runpod.serverless.start = original_start


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def main():
    parser = argparse.ArgumentParser(description="Run flaky test detector locally")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-q", "--quiet", action="store_true", help="Minimal output")
    parser.add_argument("-i", "--input", default="test_input.json", help="Input configuration file")
    args = parser.parse_args()

    start_time = time.time()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Load test input
    try:
        test_input_path = os.path.join(project_dir, args.input)
        with open(test_input_path) as f:
            test_input = json.load(f)
        if args.verbose:
            print(f"📂 Loaded configuration from: {test_input_path}")
    except FileNotFoundError:
        if not args.quiet:
            print(f"❌ {args.input} not found")
            print("\nUsing default test configuration instead...")
        test_input = {
            "repo": "https://github.com/runpod/testflake",
            "test_command": "pytest tests/test_flaky.py",
            "runs": 50,
            "parallelism": 5,
        }

    # Validate input configuration
    validation_start = time.time()
    try:
        from validate_input import validate_and_report

        if args.verbose:
            print("🔍 Validating input configuration...")
        if not validate_and_report(test_input, args.input):
            return 1
        if args.verbose:
            print(f"✅ Validation passed ({time.time() - validation_start:.2f}s)\n")
    except ImportError:
        # validate_input module not available - skip validation
        if args.verbose:
            print("⚠️  Validation module not available, skipping...\n")
    except Exception as e:
        if not args.quiet:
            print(f"⚠️  Warning: Could not validate configuration: {e}")
            print("   Proceeding anyway...\n")

    if not args.quiet:
        print("=" * 70)
        print(f"🔍 FLAKY TEST DETECTOR - {timestamp}")
        print("=" * 70)
        print(f"📦 Repository:    {test_input['repo']}")
        print(f"🧪 Test command:  {test_input['test_command']}")
        print(f"🔄 Runs:          {test_input['runs']}")
        print(f"⚡ Parallelism:   {test_input['parallelism']}")
        print("=" * 70)
        print()

    # Simulate RunPod job format
    job = {"input": test_input}

    try:
        # Run the handler
        execution_start = time.time()
        if not args.quiet:
            print("⏳ Running tests... (this may take a while)")
        result = handler(job)
        execution_time = time.time() - execution_start

        # Display results
        total_time = time.time() - start_time
        repro_rate = result["repro_rate"]
        failures = result["failures"]
        total_runs = result["total_runs"]
        passes = total_runs - failures

        if not args.quiet:
            print("\n" + "=" * 70)
            print("📊 TEST RESULTS")
            print("=" * 70)
            print(f"Total runs:       {total_runs}")
            print(f"Passed:           {passes} ({passes / total_runs * 100:.1f}%)")
            print(f"Failed:           {failures} ({failures / total_runs * 100:.1f}%)")
            print(f"Reproduction:     {repro_rate * 100:.1f}%")
            print(f"Framework:        {result.get('framework', 'unknown')}")
            print()
            print(f"⏱️  Execution time: {format_duration(execution_time)}")
            print(f"⏱️  Total time:     {format_duration(total_time)}")
            print("=" * 70)
            print()

        # Show severity
        if not args.quiet:
            if repro_rate > 0.9:
                print("🔴 CRITICAL: Very high failure rate (>90%) - likely a real bug!")
                print()
                print("This appears to be a consistent, reproducible failure.")
                print("The high reproduction rate suggests a real bug in the code.")
            elif repro_rate > 0.5:
                print("🟠 HIGH: Test fails frequently - needs investigation")
                print()
                print("This test shows significant instability.")
                print("Investigate timing, concurrency, or state management issues.")
            elif repro_rate > 0.1:
                print("🟡 MEDIUM: Clear flaky behavior detected")
                print()
                print("This test shows intermittent flakiness.")
                print("Consider stabilizing it to improve CI reliability.")
            elif repro_rate > 0:
                print("🟢 LOW: Occasional flakiness")
                print()
                print("This test shows rare flakiness.")
                print("May need more runs for conclusive analysis.")
            else:
                print("✅ NONE: No flakiness detected")
                print()
                if failures == 0:
                    print("All test runs passed successfully!")
                else:
                    print("Test failed consistently (100% reproduction rate).")
                    print("This is a reliable test failure, not flakiness.")

        # Save detailed results
        results_path = os.path.join(project_dir, "flaky_test_results.json")
        result["execution_metadata"] = {
            "timestamp": timestamp,
            "execution_time_seconds": execution_time,
            "total_time_seconds": total_time,
            "input_file": args.input,
        }

        with open(results_path, "w") as f:
            json.dump(result, f, indent=2)

        if not args.quiet:
            print(f"\n📄 Detailed results saved to: {results_path}")
        elif args.verbose:
            print(f"Results: {failures}/{total_runs} failures ({repro_rate * 100:.1f}%)")

    except Exception as e:
        error_time = time.time() - start_time
        print(f"\n❌ Error after {format_duration(error_time)}: {e}")

        if args.verbose:
            import traceback

            print("\n" + "=" * 70)
            print("FULL ERROR TRACEBACK")
            print("=" * 70)
            traceback.print_exc()
        else:
            print("\nRun with --verbose for full traceback")

        return 1

    return 0


if __name__ == "__main__":
    exit(main())
