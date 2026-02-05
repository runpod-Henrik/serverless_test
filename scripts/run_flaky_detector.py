#!/usr/bin/env python3
"""
Script to run the flaky test detector on RunPod and save results.
"""
import json
import os
import sys
from typing import Any

import runpod


def main() -> None:
    # Get configuration from environment
    api_key = os.environ.get("RUNPOD_API_KEY")
    endpoint_id = os.environ.get("RUNPOD_ENDPOINT_ID")
    repository = os.environ.get("GITHUB_REPOSITORY")
    test_command = os.environ.get("TEST_COMMAND", "pytest tests/")
    runs = int(os.environ.get("FLAKY_TEST_RUNS", "100"))
    parallelism = int(os.environ.get("FLAKY_TEST_PARALLELISM", "10"))

    if not api_key:
        print("ERROR: RUNPOD_API_KEY environment variable not set")
        sys.exit(1)

    if not endpoint_id:
        print("ERROR: RUNPOD_ENDPOINT_ID environment variable not set")
        sys.exit(1)

    # Configure RunPod
    runpod.api_key = api_key

    # Construct repository URL
    repo_url = f"https://github.com/{repository}"

    print("🔍 Running flaky test detector...")
    print(f"   Repository: {repo_url}")
    print(f"   Test command: {test_command}")
    print(f"   Runs: {runs}")
    print(f"   Parallelism: {parallelism}")

    try:
        # Run the job
        endpoint = runpod.Endpoint(endpoint_id)
        job = endpoint.run(
            {
                "repo": repo_url,
                "test_command": test_command,
                "runs": runs,
                "parallelism": parallelism,
            }
        )

        print(f"📊 Job submitted: {job.job_id}")
        print("⏳ Waiting for results...")

        # Wait for results
        result = job.output(timeout=600)  # 10 minute timeout

        # Save results to file
        with open("flaky_test_results.json", "w") as f:
            json.dump(result, f, indent=2)

        # Print summary
        if result:
            print("\n✅ Flaky test detection complete!")
            print(f"   Total runs: {result.get('total_runs', 0)}")
            print(f"   Failures: {result.get('failures', 0)}")
            print(f"   Repro rate: {result.get('repro_rate', 0) * 100:.1f}%")

            # Exit with error if repro rate is too high (indicates consistent failure)
            repro_rate = result.get("repro_rate", 0)
            if repro_rate > 0.9:
                print(
                    "\n⚠️  WARNING: Very high failure rate (>90%) - this may not be flaky!"
                )
                sys.exit(1)
            elif repro_rate > 0.05:
                print(
                    f"\n⚠️  FLAKY TEST DETECTED: {repro_rate * 100:.1f}% failure rate"
                )
                sys.exit(1)
            else:
                print("\n✅ Test appears stable (low failure rate)")

    except Exception as e:
        print(f"\n❌ Error running flaky test detector: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
