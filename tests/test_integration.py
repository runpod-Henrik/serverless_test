"""Integration tests for the flaky test detector system.

These tests verify the complete workflow from input to output,
testing the actual system behavior with real test execution.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

# Disable runpod serverless start for integration tests
sys.modules["runpod"] = mock.MagicMock()


class TestIntegrationWorkflow:
    """Test complete end-to-end workflows."""

    def test_local_test_script_execution(self):
        """Test that local_test.py can execute successfully."""
        import subprocess

        # Create a temporary test input
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            test_input = {
                "repo": os.path.abspath("."),  # Use current directory
                "test_command": "python3 -c 'exit(0)'",  # Simple passing command
                "runs": 3,
                "parallelism": 2,
            }
            json.dump(test_input, f)
            input_file = f.name

        try:
            # Run local_test.py with the temp input
            result = subprocess.run(
                ["python3", "local_test.py", "-q", "-i", input_file],
                capture_output=True,
                text=True,
                timeout=60,
            )

            # Should succeed
            assert result.returncode == 0, f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"

            # Check that results file was created
            assert os.path.exists("flaky_test_results.json")

            # Load and verify results
            with open("flaky_test_results.json") as f:
                results = json.load(f)

            assert results["total_runs"] == 3
            assert results["failures"] == 0  # Simple command should pass
            assert results["repro_rate"] == 0.0
        finally:
            # Cleanup
            if os.path.exists(input_file):
                os.unlink(input_file)

    def test_handler_with_local_repository(self):
        """Test handler with a local repository path."""
        from worker import handler

        # Use current directory as test repo
        job = {
            "input": {
                "repo": os.path.abspath("."),
                "test_command": "python3 -c 'import sys; sys.exit(0)'",
                "runs": 5,
                "parallelism": 2,
            }
        }

        result = handler(job)

        assert result["total_runs"] == 5
        assert result["parallelism"] == 2
        assert "results" in result
        assert len(result["results"]) == 5
        assert all(r["passed"] for r in result["results"])
        assert result["repro_rate"] == 0.0

    def test_handler_with_failing_test(self):
        """Test handler with a consistently failing test."""
        from worker import handler

        job = {
            "input": {
                "repo": os.path.abspath("."),
                "test_command": "python3 -c 'import sys; sys.exit(1)'",  # Always fails
                "runs": 5,
                "parallelism": 2,
            }
        }

        result = handler(job)

        assert result["total_runs"] == 5
        assert result["failures"] == 5  # All should fail
        assert result["repro_rate"] == 1.0
        assert all(not r["passed"] for r in result["results"])

    def test_handler_with_random_flaky_test(self):
        """Test handler with a test that randomly passes/fails."""
        from worker import handler

        # Create a Python script that randomly fails
        flaky_script = """
import random
import sys
# Use seed from environment if provided
seed = int(__import__('os').environ.get('TEST_SEED', 42))
random.seed(seed)
# Fail ~50% of the time
sys.exit(1 if random.random() < 0.5 else 0)
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(flaky_script)
            script_path = f.name

        try:
            job = {
                "input": {
                    "repo": os.path.abspath("."),
                    "test_command": f"python3 {script_path}",
                    "runs": 20,
                    "parallelism": 5,
                }
            }

            result = handler(job)

            assert result["total_runs"] == 20
            # Should have some failures but not all
            assert 0 < result["failures"] < 20, "Expected some but not all tests to fail"
            assert 0 < result["repro_rate"] < 1.0
        finally:
            if os.path.exists(script_path):
                os.unlink(script_path)

    def test_framework_detection_python(self):
        """Test Python framework detection."""
        from worker import detect_framework

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create requirements.txt
            requirements_path = os.path.join(tmpdir, "requirements.txt")
            Path(requirements_path).write_text("pytest==7.0.0\n")

            framework = detect_framework(tmpdir)
            assert framework == "python"

    def test_framework_detection_go(self):
        """Test Go framework detection."""
        from worker import detect_framework

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create go.mod
            go_mod_path = os.path.join(tmpdir, "go.mod")
            Path(go_mod_path).write_text("module example.com/test\n\ngo 1.20\n")

            framework = detect_framework(tmpdir)
            assert framework == "go"

    def test_framework_detection_typescript_jest(self):
        """Test TypeScript Jest framework detection."""
        from worker import detect_framework

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create package.json with jest
            package_json = os.path.join(tmpdir, "package.json")
            Path(package_json).write_text(json.dumps({"devDependencies": {"jest": "^29.0.0"}}))

            framework = detect_framework(tmpdir)
            assert framework == "typescript-jest"

    def test_dependency_installation_python(self):
        """Test Python dependency installation."""
        from worker import install_dependencies

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple requirements.txt
            requirements_path = os.path.join(tmpdir, "requirements.txt")
            Path(requirements_path).write_text("# No actual dependencies\n")

            # Should not raise an error
            install_dependencies("python", tmpdir)

    def test_seed_environment_variables(self):
        """Test that seed environment variables are properly set."""
        from worker import get_seed_env_var

        # Test Python
        env_vars = get_seed_env_var("python", 12345)
        assert env_vars == {"TEST_SEED": "12345"}

        # Test Go
        env_vars = get_seed_env_var("go", 67890)
        assert env_vars == {"GO_TEST_SEED": "67890"}

        # Test Jest
        env_vars = get_seed_env_var("typescript-jest", 111)
        assert env_vars == {"JEST_SEED": "111"}

    def test_handler_with_timeout(self):
        """Test that handler handles test timeouts correctly."""
        from worker import handler

        # Create a script that sleeps longer than timeout
        sleep_script = """
import time
time.sleep(400)  # Sleep longer than 5 minute timeout
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(sleep_script)
            script_path = f.name

        try:
            job = {
                "input": {
                    "repo": os.path.abspath("."),
                    "test_command": f"python3 {script_path}",
                    "runs": 2,
                    "parallelism": 1,
                }
            }

            result = handler(job)

            # Should handle timeout gracefully
            assert result["total_runs"] == 2
            assert all(not r["passed"] for r in result["results"])
            assert all("TIMEOUT" in r.get("stderr", "") for r in result["results"])
        finally:
            if os.path.exists(script_path):
                os.unlink(script_path)

    def test_handler_cleanup_on_success(self):
        """Test that handler cleans up temporary directories on success."""
        # Get current temp dir count
        import tempfile as tmp

        from worker import handler

        temp_root = tmp.gettempdir()
        before_count = len(os.listdir(temp_root))

        job = {
            "input": {
                "repo": os.path.abspath("."),
                "test_command": "python3 -c 'exit(0)'",
                "runs": 2,
                "parallelism": 1,
            }
        }

        handler(job)

        # Temp dir should be cleaned up
        after_count = len(os.listdir(temp_root))
        # Allow some variance for system temp files
        assert abs(after_count - before_count) <= 5

    def test_handler_cleanup_on_error(self):
        """Test that handler cleans up even when tests fail."""
        import tempfile as tmp

        from worker import handler

        temp_root = tmp.gettempdir()
        before_count = len(os.listdir(temp_root))

        job = {
            "input": {
                "repo": os.path.abspath("."),
                "test_command": "python3 -c 'exit(1)'",  # Failing test
                "runs": 2,
                "parallelism": 1,
            }
        }

        handler(job)

        # Temp dir should still be cleaned up
        after_count = len(os.listdir(temp_root))
        assert abs(after_count - before_count) <= 5

    def test_config_integration_with_handler(self):
        """Test that handler respects .flaky-detector.yml configuration."""
        from worker import handler

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a .flaky-detector.yml
            config_path = os.path.join(tmpdir, ".flaky-detector.yml")
            Path(config_path).write_text(
                """
runs: 25
parallelism: 6
severity_thresholds:
  critical: 0.95
  high: 0.6
"""
            )

            # Create a simple test script
            test_script = os.path.join(tmpdir, "test.py")
            Path(test_script).write_text("exit(0)")

            job = {
                "input": {
                    "repo": tmpdir,
                    "test_command": f"python3 {test_script}",
                    # Don't specify runs/parallelism - should use from config
                }
            }

            result = handler(job)

            # Should use values from config file
            assert result["total_runs"] == 25
            assert result["parallelism"] == 6

    def test_validation_integration(self):
        """Test that validation catches invalid inputs."""
        from validate_input import validate_input

        # Invalid: runs too high
        config = {
            "repo": "https://github.com/user/repo",
            "test_command": "pytest",
            "runs": 2000,  # > 1000 max
        }
        is_valid, errors = validate_input(config)
        assert not is_valid
        assert any("runs" in err.lower() for err in errors)

        # Invalid: parallelism too high
        config = {
            "repo": "https://github.com/user/repo",
            "test_command": "pytest",
            "parallelism": 100,  # > 50 max
        }
        is_valid, errors = validate_input(config)
        assert not is_valid
        assert any("parallelism" in err.lower() for err in errors)

        # Valid configuration
        config = {
            "repo": "https://github.com/user/repo",
            "test_command": "pytest",
            "runs": 50,
            "parallelism": 5,
        }
        is_valid, errors = validate_input(config)
        assert is_valid
        assert len(errors) == 0


class TestDatabaseIntegration:
    """Test database integration with the system."""

    def test_database_stores_run_results(self):
        """Test that database can store and retrieve run results."""
        from database import ResultsDatabase

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            with ResultsDatabase(db_path) as db:
                # Save a run
                run_id = db.save_run(
                    repository="test/repo",
                    test_command="pytest tests/",
                    total_runs=10,
                    parallelism=5,
                    failures=3,
                    repro_rate=0.3,
                    severity="medium",
                    results=[{"attempt": i, "passed": i % 3 != 0} for i in range(10)],
                )

                assert run_id is not None

                # Retrieve the run
                run = db.get_run_details(run_id)
                assert run is not None
                assert run["repository"] == "test/repo"
                assert run["total_runs"] == 10
                assert run["failures"] == 3
                assert run["repro_rate"] == 0.3

                # Get recent runs
                recent = db.get_recent_runs(limit=5)
                assert len(recent) >= 1
                assert recent[0]["id"] == run_id
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
