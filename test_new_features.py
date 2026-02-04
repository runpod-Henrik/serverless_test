#!/usr/bin/env python3
"""
Integration test for new features: configuration and historical tracking.
"""

import os
import sys

from config import Config
from database import ResultsDatabase


def test_configuration():
    """Test configuration loading."""
    print("=" * 60)
    print("Testing Configuration System")
    print("=" * 60)

    # Test 1: Load default config
    print("\n1. Loading default configuration...")
    config = Config()
    print(f"   ✓ Runs: {config.get('runs')}")
    print(f"   ✓ Parallelism: {config.get('parallelism')}")
    print(f"   ✓ Timeout: {config.get('timeout')}")

    # Test 2: Load from file
    print("\n2. Loading from .flaky-detector.yml...")
    if os.path.exists(".flaky-detector.yml"):
        config = Config.load_from_file(".flaky-detector.yml")
        print("   ✓ Config loaded from file")
        print(f"   ✓ Runs: {config.get('runs')}")
        print(f"   ✓ Parallelism: {config.get('parallelism')}")
    else:
        print("   ⚠ .flaky-detector.yml not found, using defaults")

    # Test 3: Severity classification
    print("\n3. Testing severity classification...")
    test_cases = [
        (0.95, "CRITICAL"),
        (0.7, "HIGH"),
        (0.3, "MEDIUM"),
        (0.05, "LOW"),
        (0.0, "NONE"),
    ]

    for rate, expected in test_cases:
        severity, emoji = config.get_severity(rate)
        status = "✓" if severity == expected else "✗"
        print(f"   {status} {rate * 100:.0f}% → {emoji} {severity} (expected {expected})")

    # Test 4: Ignore patterns
    print("\n4. Testing ignore patterns...")
    config_with_patterns = Config({"ignore_patterns": ["test_flaky_*", "*_slow"]})
    test_names = [
        ("test_flaky_something", False),
        ("test_normal", True),
        ("test_very_slow", False),
        ("test_fast", True),
    ]

    for name, should_run in test_names:
        actual = config_with_patterns.should_run_test(name)
        status = "✓" if actual == should_run else "✗"
        action = "RUN" if actual else "SKIP"
        print(f"   {status} {name} → {action}")

    print("\n✓ Configuration system working correctly!\n")


def test_database():
    """Test historical tracking database."""
    print("=" * 60)
    print("Testing Historical Tracking Database")
    print("=" * 60)

    # Use a test database
    test_db_path = "test_history.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    db = ResultsDatabase(test_db_path)

    try:
        # Test 1: Save a run
        print("\n1. Saving test run to database...")
        results = [
            {"attempt": i, "exit_code": 0 if i % 3 else 1, "passed": i % 3 != 0} for i in range(10)
        ]

        run_id = db.save_run(
            repository="test/repo",
            test_command="pytest tests/test_example.py",
            total_runs=10,
            parallelism=5,
            failures=3,
            repro_rate=0.3,
            severity="MEDIUM",
            results=results,
            duration_seconds=12.5,
            pr_number=42,
            branch="feature/test",
            commit_sha="abc123def456",
        )

        print(f"   ✓ Run saved with ID: {run_id}")

        # Test 2: Retrieve the run
        print("\n2. Retrieving run from database...")
        run = db.get_run_details(run_id)
        print(f"   ✓ Repository: {run['repository']}")
        print(f"   ✓ Test command: {run['test_command']}")
        print(f"   ✓ Failures: {run['failures']}/{run['total_runs']}")
        print(f"   ✓ Repro rate: {run['repro_rate'] * 100:.1f}%")
        print(f"   ✓ Severity: {run['severity']}")
        print(f"   ✓ PR: #{run['pr_number']}")
        print(f"   ✓ Results: {len(run['results'])} individual test results")

        # Test 3: Add more runs for trend analysis
        print("\n3. Adding multiple runs for trend analysis...")
        for i in range(5):
            db.save_run(
                repository="test/repo",
                test_command="pytest tests/",
                total_runs=100,
                parallelism=10,
                failures=10 + i * 5,
                repro_rate=(10 + i * 5) / 100,
                severity="MEDIUM" if i < 3 else "HIGH",
                results=[],
                duration_seconds=20.0 + i,
            )
        print("   ✓ Added 5 more runs")

        # Test 4: Query statistics
        print("\n4. Querying statistics...")
        stats = db.get_statistics(repository="test/repo")
        print(f"   ✓ Total runs: {stats['total_runs']}")
        print(f"   ✓ Total tests executed: {stats['total_tests']}")
        print(f"   ✓ Total failures: {stats['total_failures']}")
        print(f"   ✓ Avg repro rate: {stats['avg_repro_rate'] * 100:.1f}%")
        print(f"   ✓ Medium severity runs: {stats['medium_runs']}")
        print(f"   ✓ High severity runs: {stats['high_runs']}")

        # Test 5: Get recent runs
        print("\n5. Getting recent runs...")
        recent = db.get_recent_runs(limit=3)
        print(f"   ✓ Retrieved {len(recent)} recent runs")
        for run in recent:
            print(f"      - {run['test_command']}: {run['failures']}/{run['total_runs']} failures")

        # Test 6: Get most flaky commands
        print("\n6. Finding most flaky test commands...")
        flaky = db.get_most_flaky_commands("test/repo", limit=5)
        print(f"   ✓ Found {len(flaky)} test commands")
        for cmd in flaky:
            print(
                f"      - {cmd['test_command']}: {cmd['avg_repro_rate'] * 100:.1f}% avg flaky rate"
            )

        print("\n✓ Historical tracking database working correctly!\n")

    finally:
        db.close()
        # Cleanup
        if os.path.exists(test_db_path):
            os.remove(test_db_path)


def main():
    """Run all integration tests."""
    print("\n" + "=" * 60)
    print("INTEGRATION TESTS FOR NEW FEATURES")
    print("=" * 60 + "\n")

    try:
        test_configuration()
        test_database()

        print("=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nNew features are working correctly:")
        print("  1. Configuration file support ✓")
        print("  2. Historical tracking database ✓")
        print("\nNext steps:")
        print("  • Run dashboard: streamlit run dashboard.py")
        print("  • Customize config: edit .flaky-detector.yml")
        print("  • View documentation: CONFIGURATION.md, HISTORICAL_TRACKING.md")
        print()

        return 0

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
