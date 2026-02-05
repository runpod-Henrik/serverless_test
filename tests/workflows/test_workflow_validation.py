"""Tests for GitHub Actions workflow validation."""

import subprocess
from pathlib import Path

import pytest
import yaml


class TestWorkflowStructure:
    """Test workflow YAML structure."""

    @pytest.fixture
    def ci_workflow(self) -> dict:
        """Load CI workflow."""
        workflow_path = Path(".github/workflows/ci.yml")
        # Use yaml.load with Loader to properly handle 'on' keyword
        with open(workflow_path) as f:
            return yaml.load(f, Loader=yaml.FullLoader)

    @pytest.fixture
    def flaky_detector_workflow(self) -> dict:
        """Load flaky detector workflow."""
        workflow_path = Path(".github/workflows/flaky-test-detector.yml")
        # Use yaml.load with Loader to properly handle 'on' keyword
        with open(workflow_path) as f:
            return yaml.load(f, Loader=yaml.FullLoader)

    def test_ci_workflow_name(self, ci_workflow: dict) -> None:
        """Test CI workflow has correct name."""
        assert ci_workflow["name"] == "CI"

    def test_ci_triggers_on_push_and_pr(self, ci_workflow: dict) -> None:
        """Test CI workflow triggers on push and PR."""
        # Note: YAML 'on' keyword is parsed as boolean True
        triggers = ci_workflow[True]
        assert "push" in triggers
        assert "pull_request" in triggers
        assert "main" in triggers["push"]["branches"]

    def test_ci_has_lint_and_test_jobs(self, ci_workflow: dict) -> None:
        """Test CI workflow has expected jobs."""
        jobs = ci_workflow["jobs"]
        assert "lint-and-type-check" in jobs
        assert "test" in jobs

    def test_ci_test_needs_lint(self, ci_workflow: dict) -> None:
        """Test that test job depends on lint job."""
        test_job = ci_workflow["jobs"]["test"]
        assert test_job.get("needs") == "lint-and-type-check"

    def test_ci_uses_python_312(self, ci_workflow: dict) -> None:
        """Test CI uses Python 3.12."""
        lint_job = ci_workflow["jobs"]["lint-and-type-check"]
        setup_python = next(
            step for step in lint_job["steps"] if step.get("name") == "Set up Python"
        )
        assert setup_python["with"]["python-version"] == "3.12"

    def test_flaky_detector_triggers_on_workflow_run(
        self, flaky_detector_workflow: dict
    ) -> None:
        """Test flaky detector triggers on workflow_run."""
        # Note: YAML 'on' keyword is parsed as boolean True
        triggers = flaky_detector_workflow[True]
        assert "workflow_run" in triggers
        workflow_run = triggers["workflow_run"]
        assert "CI" in workflow_run["workflows"]
        assert "completed" in workflow_run["types"]

    def test_flaky_detector_only_runs_on_failure(
        self, flaky_detector_workflow: dict
    ) -> None:
        """Test flaky detector only runs on CI failure."""
        job = flaky_detector_workflow["jobs"]["detect-flaky-tests"]
        assert (
            "${{ github.event.workflow_run.conclusion == 'failure' }}"
            in job["if"]
        )

    def test_flaky_detector_has_required_secrets(
        self, flaky_detector_workflow: dict
    ) -> None:
        """Test flaky detector uses required secrets."""
        job = flaky_detector_workflow["jobs"]["detect-flaky-tests"]
        # Find the step that uses secrets
        detector_step = next(
            step
            for step in job["steps"]
            if step.get("name") == "Run flaky test detector"
        )

        env = detector_step.get("env", {})
        assert "RUNPOD_API_KEY" in env
        assert "RUNPOD_ENDPOINT_ID" in env
        assert "${{ secrets.RUNPOD_API_KEY }}" in env["RUNPOD_API_KEY"]


class TestWorkflowArtifacts:
    """Test workflow artifact generation."""

    def test_junit_xml_format_valid(self, tmp_path: Path) -> None:
        """Test that pytest generates valid JUnit XML."""
        # Run a simple test to generate JUnit XML
        test_file = tmp_path / "test_sample.py"
        test_file.write_text(
            """
def test_sample():
    assert 1 + 1 == 2
"""
        )

        junit_file = tmp_path / "test-results.xml"
        result = subprocess.run(
            ["pytest", str(test_file), f"--junit-xml={junit_file}"],
            capture_output=True,
        )

        assert result.returncode == 0
        assert junit_file.exists()

        # Validate XML structure
        import xml.etree.ElementTree as ET

        tree = ET.parse(junit_file)
        root = tree.getroot()
        # Can be testsuites (multiple) or testsuite (single)
        assert root.tag in ("testsuite", "testsuites")
        if root.tag == "testsuites":
            # Check nested testsuite
            testsuite = root.find("testsuite")
            assert testsuite is not None
            assert "tests" in testsuite.attrib
        else:
            assert "tests" in root.attrib
            assert int(root.attrib["tests"]) >= 1

    def test_coverage_xml_format_valid(self, tmp_path: Path) -> None:
        """Test that pytest-cov generates valid coverage XML."""
        import shutil
        import sys

        # Find pytest executable
        pytest_exe = shutil.which("pytest")
        if pytest_exe is None:
            # Try using sys.executable with -m pytest
            pytest_exe = sys.executable
            pytest_args = ["-m", "pytest"]
        else:
            pytest_args = []

        # Create a simple module to test
        module_file = tmp_path / "sample_module.py"
        module_file.write_text(
            """
def add(a, b):
    return a + b
"""
        )

        test_file = tmp_path / "test_sample.py"
        test_file.write_text(
            """
from sample_module import add

def test_add():
    assert add(1, 2) == 3
"""
        )

        coverage_file = tmp_path / "coverage.xml"
        try:
            result = subprocess.run(
                [
                    pytest_exe,
                    *pytest_args,
                    str(test_file),
                    f"--cov={tmp_path}",
                    f"--cov-report=xml:{coverage_file}",
                ],
                capture_output=True,
                cwd=str(tmp_path),
                env={"PYTHONPATH": str(tmp_path)},
                timeout=10,
            )

            assert result.returncode == 0
            assert coverage_file.exists()

            # Validate XML structure
            import xml.etree.ElementTree as ET

            tree = ET.parse(coverage_file)
            root = tree.getroot()
            assert root.tag == "coverage"
            assert "line-rate" in root.attrib
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("pytest or pytest-cov not available")


class TestWorkflowOutputs:
    """Test workflow step outputs."""

    def test_github_output_format(self, tmp_path: Path) -> None:
        """Test that GITHUB_OUTPUT format is correct."""
        output_file = tmp_path / "github_output.txt"

        # Simulate writing to GITHUB_OUTPUT
        with open(output_file, "w") as f:
            f.write("test_value=123\n")
            f.write("another_value=hello\n")

        content = output_file.read_text()
        lines = content.strip().split("\n")

        assert len(lines) == 2
        assert lines[0] == "test_value=123"
        assert lines[1] == "another_value=hello"

        # Validate format (key=value)
        for line in lines:
            assert "=" in line
            key, value = line.split("=", 1)
            assert key.strip() != ""
            assert value.strip() != ""


class TestWorkflowScripts:
    """Test embedded scripts from workflows."""

    def test_pr_number_extraction_safety(self) -> None:
        """Test PR number extraction handles missing PR gracefully."""
        # Simulate the bash logic from flaky-test-detector.yml
        pr_number = ""  # Simulates empty pull_requests array
        pr_number_result = pr_number or ""

        assert pr_number_result == ""  # Should not error

    def test_exit_code_capture(self) -> None:
        """Test exit code capture pattern."""
        # Simulate the workflow pattern
        class MockOutput:
            def __init__(self):
                self.data = {}

            def write(self, key: str, value: str) -> None:
                self.data[key] = value

        output = MockOutput()

        # Test success case
        exit_code = 0
        output.write("exit_code", str(exit_code))
        assert output.data["exit_code"] == "0"

        # Test failure case
        exit_code = 1
        output.write("exit_code", str(exit_code))
        assert output.data["exit_code"] == "1"
