#!/usr/bin/env python3
"""
Test your RunPod endpoint deployment.
"""
import os
import runpod
import json


def main():
    # Get configuration from environment or prompt
    api_key = os.environ.get("RUNPOD_API_KEY")
    endpoint_id = os.environ.get("RUNPOD_ENDPOINT_ID")

    if not api_key:
        api_key = input("Enter your RunPod API key: ").strip()
    if not endpoint_id:
        endpoint_id = input("Enter your RunPod endpoint ID: ").strip()

    # Configure RunPod
    runpod.api_key = api_key

    print("🚀 Testing RunPod endpoint...")
    print(f"   Endpoint ID: {endpoint_id}")
    print()

    # Load test configuration
    try:
        with open("test_input.json", "r") as f:
            test_input = json.load(f)
    except FileNotFoundError:
        test_input = {
            "repo": "https://github.com/runpod-Henrik/serverless_test",
            "test_command": "pytest tests/test_flaky.py",
            "runs": 50,
            "parallelism": 5,
        }

    print(f"📋 Test configuration:")
    print(f"   Repository: {test_input['repo']}")
    print(f"   Test command: {test_input['test_command']}")
    print(f"   Runs: {test_input['runs']}")
    print(f"   Parallelism: {test_input['parallelism']}")
    print()

    try:
        # Submit job
        endpoint = runpod.Endpoint(endpoint_id)
        print("⏳ Submitting job to RunPod...")
        job = endpoint.run(test_input)

        print(f"✅ Job submitted: {job.job_id}")
        print("⏳ Waiting for results (this may take 2-5 minutes)...")
        print()

        # Wait for results
        result = job.output(timeout=600)

        # Display results
        if result:
            print("=" * 60)
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
                print("🔴 CRITICAL: Very high failure rate (>90%)")
            elif repro_rate > 0.5:
                print("🟠 HIGH: Test fails frequently")
            elif repro_rate > 0.1:
                print("🟡 MEDIUM: Clear flaky behavior")
            elif repro_rate > 0:
                print("🟢 LOW: Occasional flakiness")
            else:
                print("✅ NONE: No flakiness detected")

            # Save results
            with open("runpod_test_results.json", "w") as f:
                json.dump(result, f, indent=2)
            print("\n📄 Results saved to: runpod_test_results.json")
            print("\n✅ RunPod endpoint is working correctly!")
        else:
            print("❌ No results returned from RunPod")
            return 1

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Verify your API key is correct")
        print("2. Check endpoint ID is correct")
        print("3. Ensure endpoint is deployed and active")
        print("4. Check RunPod dashboard for errors")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
