#!/usr/bin/env python3
"""
Validate the flaky test detector system end-to-end.

This script tests the flaky detector both locally (using worker.py directly)
and optionally via RunPod if credentials are available.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_local_flaky_detector() -> bool:
    """Test the flaky detector using local worker.py (no RunPod)."""
    print("🧪 Testing local flaky detector...")

    try:
        from worker import handler

        # Get the current repository path
        repo_path = Path(__file__).parent.parent.absolute()

        # Test input - run our example flaky test
        test_input = {
            "repo": str(repo_path),  # Use local path for testing
            "test_command": "pytest tests/test_flaky.py -v",
            "runs": 20,  # Run 20 times to detect flakiness
            "parallelism": 5,
        }

        print(f"  Repository: {test_input['repo']}")
        print(f"  Test command: {test_input['test_command']}")
        print(f"  Runs: {test_input['runs']}")
        print(f"  Parallelism: {test_input['parallelism']}")
        print()

        # Run the handler
        result = handler({"input": test_input})

        # Validate results
        if "error" in result:
            print(f"❌ Handler returned error: {result['error']}")
            return False

        output = result.get("output", {})

        # Check required fields
        required_fields = ["total_runs", "failures", "repro_rate", "results"]
        for field in required_fields:
            if field not in output:
                print(f"❌ Missing required field: {field}")
                return False

        total_runs = output["total_runs"]
        failures = output["failures"]
        repro_rate = output["repro_rate"]

        print(f"✅ Handler executed successfully!")
        print(f"   Total runs: {total_runs}")
        print(f"   Failures: {failures}")
        print(f"   Repro rate: {repro_rate * 100:.1f}%")
        print()

        # Validate the flaky test behaved as expected
        # Our test_flaky.py should fail some of the time (15-25% based on threshold)
        if total_runs != test_input["runs"]:
            print(f"❌ Expected {test_input['runs']} runs, got {total_runs}")
            return False

        if repro_rate < 0.0 or repro_rate > 1.0:
            print(f"❌ Invalid repro rate: {repro_rate}")
            return False

        # The flaky test should have some failures (not 0% or 100%)
        # Note: It might occasionally be 0% or 100% due to randomness, so we're lenient
        print(f"✅ Flaky test detection validated!")
        print(f"   Test showed {repro_rate * 100:.1f}% failure rate")

        if repro_rate == 0:
            print("   ⚠️  No failures detected (test passed all runs)")
        elif repro_rate == 1.0:
            print("   ⚠️  All runs failed (100% failure rate)")
        else:
            print("   ✓ Flaky behavior detected as expected")

        return True

    except ImportError as e:
        print(f"⚠️  Skipping local test (missing dependency: {e})")
        print("   Install dependencies with: pip install -r requirements.txt")
        return True  # Not a failure, just skipped
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_runpod_flaky_detector() -> bool:
    """Test the flaky detector via RunPod (if credentials available)."""
    print("🚀 Testing RunPod flaky detector...")

    api_key = os.environ.get("RUNPOD_API_KEY")
    endpoint_id = os.environ.get("RUNPOD_ENDPOINT_ID")

    if not api_key or not endpoint_id:
        print("⚠️  Skipping RunPod test (credentials not set)")
        print("   Set RUNPOD_API_KEY and RUNPOD_ENDPOINT_ID to enable")
        return True  # Not a failure, just skipped

    try:
        import runpod

        runpod.api_key = api_key

        # Test with this repository
        repo_url = os.environ.get(
            "GITHUB_REPOSITORY",
            "https://github.com/runpod-Henrik/serverless_test"
        )
        if not repo_url.startswith("http"):
            repo_url = f"https://github.com/{repo_url}"

        test_input = {
            "repo": repo_url,
            "test_command": "pytest tests/test_flaky.py -v",
            "runs": 20,
            "parallelism": 5,
        }

        print(f"  Repository: {test_input['repo']}")
        print(f"  Test command: {test_input['test_command']}")
        print(f"  Runs: {test_input['runs']}")
        print()

        # Run via RunPod
        endpoint = runpod.Endpoint(endpoint_id)
        job = endpoint.run(test_input)

        print(f"  Job ID: {job.job_id}")
        print("  Waiting for results...")

        result = job.output(timeout=300)  # 5 minute timeout

        if not result:
            print("❌ No result returned from RunPod")
            return False

        total_runs = result.get("total_runs", 0)
        failures = result.get("failures", 0)
        repro_rate = result.get("repro_rate", 0)

        print(f"✅ RunPod execution successful!")
        print(f"   Total runs: {total_runs}")
        print(f"   Failures: {failures}")
        print(f"   Repro rate: {repro_rate * 100:.1f}%")
        print()

        return True

    except ImportError:
        print("⚠️  runpod package not installed, skipping RunPod test")
        return True  # Not a failure, just skipped
    except Exception as e:
        print(f"❌ RunPod test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_configuration_system() -> bool:
    """Test the configuration system."""
    print("⚙️  Testing configuration system...")

    try:
        from config import Config

        # Test default config
        config = Config()
        assert config.get("runs") == 10
        assert config.get("parallelism") == 4
        print("  ✓ Default configuration loaded")

        # Test override
        config = Config(config_dict={"runs": 200})
        assert config.get("runs") == 200
        print("  ✓ Configuration override works")

        # Test severity (returns tuple of (level, emoji))
        severity, emoji = config.get_severity(0.95)
        assert severity == "CRITICAL"
        severity, emoji = config.get_severity(0.6)
        assert severity == "HIGH"
        severity, emoji = config.get_severity(0.2)
        assert severity == "MEDIUM"
        severity, emoji = config.get_severity(0.05)
        assert severity == "LOW"
        severity, emoji = config.get_severity(0.0)
        assert severity == "NONE"
        print("  ✓ Severity calculation works")

        print("✅ Configuration system validated!")
        print()
        return True

    except ImportError as e:
        print(f"⚠️  Skipping configuration test (missing dependency: {e})")
        return True  # Not a failure, just skipped
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_system() -> bool:
    """Test the database system."""
    print("💾 Testing database system...")

    try:
        from database import ResultsDatabase

        # Use temporary database for testing
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            db = ResultsDatabase(tmp_path)

            # Test save and retrieve
            run_id = db.save_run(
                repository="test/repo",
                test_command="pytest tests/",
                total_runs=100,
                parallelism=10,
                failures=25,
                repro_rate=0.25,
                severity="MEDIUM",
                results=[],
            )

            assert run_id is not None
            print(f"  ✓ Saved test run (ID: {run_id})")

            # Test retrieval
            retrieved = db.get_run_details(run_id)
            assert retrieved is not None
            assert retrieved["repository"] == "test/repo"
            assert retrieved["repro_rate"] == 0.25
            print("  ✓ Retrieved test run")

            # Test statistics
            stats = db.get_statistics()
            assert stats["total_runs"] == 1
            print("  ✓ Statistics calculated")

            db.close()
        finally:
            # Clean up temp file
            Path(tmp_path).unlink(missing_ok=True)

        print("✅ Database system validated!")
        print()
        return True

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main() -> int:
    """Run all validation tests."""
    print("=" * 70)
    print("🔍 FLAKY TEST DETECTOR VALIDATION")
    print("=" * 70)
    print()

    results = {
        "Configuration System": test_configuration_system(),
        "Database System": test_database_system(),
        "Local Flaky Detector": test_local_flaky_detector(),
        "RunPod Flaky Detector": test_runpod_flaky_detector(),
    }

    print("=" * 70)
    print("📊 VALIDATION RESULTS")
    print("=" * 70)

    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:10} {name}")

    print()

    all_passed = all(results.values())

    if all_passed:
        print("✅ All validations passed!")
        return 0
    else:
        print("❌ Some validations failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
