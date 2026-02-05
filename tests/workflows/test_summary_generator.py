"""Tests for workflow test summary generator."""

# Add scripts to path
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from workflow_utils.test_summary_generator import (
    generate_test_summary,
    parse_coverage,
    parse_test_results,
)


class TestParseTestResults:
    """Test parsing JUnit XML test results."""

    def test_parse_valid_results(self, tmp_path: Path) -> None:
        """Test parsing valid JUnit XML."""
        xml_content = """<?xml version="1.0"?>
        <testsuite tests="10" failures="2" errors="1" skipped="1" time="5.5">
          <testcase classname="TestConfig" name="test_default" time="0.5"/>
          <testcase classname="TestConfig" name="test_override" time="0.3">
            <failure message="AssertionError">Expected 200</failure>
          </testcase>
        </testsuite>"""

        xml_file = tmp_path / "test-results.xml"
        xml_file.write_text(xml_content)

        result = parse_test_results(str(xml_file))

        assert result["tests"] == 10
        assert result["failures"] == 2
        assert result["errors"] == 1
        assert result["skipped"] == 1
        assert result["time"] == 5.5
        assert result["passed"] == 6  # 10 - 2 - 1 - 1

    def test_parse_all_passing(self, tmp_path: Path) -> None:
        """Test parsing XML with all tests passing."""
        xml_content = """<?xml version="1.0"?>
        <testsuite tests="5" failures="0" errors="0" skipped="0" time="2.1">
        </testsuite>"""

        xml_file = tmp_path / "test-results.xml"
        xml_file.write_text(xml_content)

        result = parse_test_results(str(xml_file))

        assert result["tests"] == 5
        assert result["failures"] == 0
        assert result["errors"] == 0
        assert result["passed"] == 5

    def test_parse_empty_attributes(self, tmp_path: Path) -> None:
        """Test parsing XML with missing attributes."""
        xml_content = """<?xml version="1.0"?>
        <testsuite>
        </testsuite>"""

        xml_file = tmp_path / "test-results.xml"
        xml_file.write_text(xml_content)

        result = parse_test_results(str(xml_file))

        assert result["tests"] == 0
        assert result["failures"] == 0
        assert result["errors"] == 0
        assert result["skipped"] == 0
        assert result["time"] == 0.0
        assert result["passed"] == 0


class TestParseCoverage:
    """Test parsing coverage XML."""

    def test_parse_valid_coverage(self, tmp_path: Path) -> None:
        """Test parsing valid coverage XML."""
        coverage_xml = """<?xml version="1.0"?>
        <coverage line-rate="0.92" branch-rate="0.85">
          <packages>
            <package name="worker" line-rate="0.95"/>
          </packages>
        </coverage>"""

        coverage_file = tmp_path / "coverage.xml"
        coverage_file.write_text(coverage_xml)

        coverage = parse_coverage(str(coverage_file))

        assert coverage == 92.0

    def test_parse_perfect_coverage(self, tmp_path: Path) -> None:
        """Test parsing 100% coverage."""
        coverage_xml = """<?xml version="1.0"?>
        <coverage line-rate="1.0">
        </coverage>"""

        coverage_file = tmp_path / "coverage.xml"
        coverage_file.write_text(coverage_xml)

        coverage = parse_coverage(str(coverage_file))

        assert coverage == 100.0

    def test_parse_missing_file(self) -> None:
        """Test parsing non-existent coverage file."""
        coverage = parse_coverage("nonexistent.xml")
        assert coverage == 0.0

    def test_parse_invalid_xml(self, tmp_path: Path) -> None:
        """Test parsing invalid XML."""
        coverage_file = tmp_path / "coverage.xml"
        coverage_file.write_text("not valid xml")

        coverage = parse_coverage(str(coverage_file))
        assert coverage == 0.0


class TestGenerateTestSummary:
    """Test test summary generation."""

    def test_generate_summary_all_passing(self) -> None:
        """Test summary generation for all passing tests."""
        test_results = {
            "tests": 10,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "time": 5.5,
            "passed": 10,
        }

        summary = generate_test_summary(test_results, 95.5)

        assert "✅ **All tests passed!**" in summary
        assert "Total Tests | 10" in summary
        assert "✅ Passed | 10" in summary
        assert "❌ Failed | 0" in summary
        assert "5.50s" in summary
        assert "95.5%" in summary
        assert "🟢 Coverage Status: Excellent" in summary

    def test_generate_summary_with_failures(self) -> None:
        """Test summary generation with failures."""
        test_results = {
            "tests": 10,
            "failures": 2,
            "errors": 1,
            "skipped": 0,
            "time": 5.5,
            "passed": 7,
        }

        summary = generate_test_summary(test_results, 88.0)

        assert "❌ **3 test(s) failed**" in summary
        assert "❌ Failed | 2" in summary
        assert "⚠️ Errors | 1" in summary
        assert "🔴 Coverage Status: Needs Improvement" in summary

    def test_generate_summary_good_coverage(self) -> None:
        """Test coverage status classification."""
        test_results = {
            "tests": 10,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "time": 5.5,
            "passed": 10,
        }

        summary = generate_test_summary(test_results, 92.0)

        assert "🟡 Coverage Status: Good" in summary

    def test_generate_summary_with_changes(self) -> None:
        """Test summary with change information."""
        test_results = {
            "tests": 10,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "time": 5.5,
            "passed": 10,
        }

        changed_files = [
            "worker.py",
            "config.py",
            "tests/test_worker.py",
            ".github/workflows/ci.yml",
        ]

        commits = [
            "abc123|John Doe|john@example.com|2 hours ago|Fix worker validation",
            "def456|Jane Smith|jane@example.com|1 hour ago|Update config defaults",
        ]

        summary = generate_test_summary(
            test_results,
            95.0,
            last_success_sha="abc1234567890",
            changed_files=changed_files,
            commits=commits,
        )

        assert "📝 Changes Since Last Successful Run" in summary
        assert "Total Files Changed | 4" in summary
        assert "Python Files | 3" in summary  # worker.py, config.py, tests/test_worker.py
        assert "Test Files | 1" in summary
        assert "Workflow Files | 1" in summary
        assert "**Commits:** 2 new commit(s)" in summary
        assert "`abc1234...HEAD`" in summary
        assert "John Doe" in summary
        assert "Fix worker validation" in summary

    def test_generate_summary_truncates_long_commits(self) -> None:
        """Test that long commit messages are truncated."""
        test_results = {
            "tests": 10,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "time": 5.5,
            "passed": 10,
        }

        long_message = "A" * 100  # 100 character message
        commits = [f"abc123|Author|email|time|{long_message}"]

        summary = generate_test_summary(
            test_results,
            95.0,
            last_success_sha="abc1234567890",
            changed_files=["file.py"],
            commits=commits,
        )

        # Should be truncated to 57 chars + "..."
        assert "AAA..." in summary
        assert len(long_message) > 60  # Verify it was long
        assert long_message not in summary  # Full message shouldn't be there

    def test_generate_summary_multiple_commits(self) -> None:
        """Test summary with many commits shows only top 5."""
        test_results = {
            "tests": 10,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "time": 5.5,
            "passed": 10,
        }

        commits = [f"commit{i}|Author{i}|email|time|Message {i}" for i in range(10)]

        summary = generate_test_summary(
            test_results,
            95.0,
            last_success_sha="abc1234567890",
            changed_files=["file.py"],
            commits=commits,
        )

        assert "commit0" in summary  # First commit shown
        assert "commit4" in summary  # Fifth commit shown
        assert "... and 5 more commits" in summary

    def test_generate_summary_coverage_increased(self) -> None:
        """Test summary shows positive coverage delta."""
        test_results = {
            "tests": 10,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "time": 5.5,
            "passed": 10,
        }

        summary = generate_test_summary(
            test_results,
            95.0,
            previous_coverage=90.0,
        )

        assert "95.0%" in summary
        assert "🟢 +5.0%" in summary

    def test_generate_summary_coverage_decreased(self) -> None:
        """Test summary shows negative coverage delta with warning."""
        test_results = {
            "tests": 10,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "time": 5.5,
            "passed": 10,
        }

        summary = generate_test_summary(
            test_results,
            85.0,
            previous_coverage=92.0,
        )

        assert "85.0%" in summary
        assert "🔴 -7.0%" in summary
        assert "⚠️ **Coverage decreased by 7.0%**" in summary
        assert "(was 92.0%, now 85.0%)" in summary

    def test_generate_summary_coverage_unchanged(self) -> None:
        """Test summary shows no change when coverage is same."""
        test_results = {
            "tests": 10,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "time": 5.5,
            "passed": 10,
        }

        summary = generate_test_summary(
            test_results,
            90.0,
            previous_coverage=90.0,
        )

        assert "90.0%" in summary
        assert "➡️ no change" in summary

    def test_generate_summary_no_previous_coverage(self) -> None:
        """Test summary without previous coverage (first run)."""
        test_results = {
            "tests": 10,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "time": 5.5,
            "passed": 10,
        }

        summary = generate_test_summary(
            test_results,
            90.0,
            previous_coverage=None,
        )

        assert "90.0%" in summary
        assert "🟢" not in summary or "Coverage Status" in summary  # Only status emoji, not delta
        assert "🔴 -" not in summary  # No negative delta
        assert "➡️ no change" not in summary


class TestMainFunction:
    """Test CLI main function."""

    def test_main_with_valid_files(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test main function with valid input files."""
        # Create test files
        test_xml = tmp_path / "test-results.xml"
        test_xml.write_text(
            """<?xml version="1.0"?>
        <testsuite tests="5" failures="0" errors="0" skipped="0" time="2.0">
        </testsuite>"""
        )

        coverage_xml = tmp_path / "coverage.xml"
        coverage_xml.write_text(
            """<?xml version="1.0"?>
        <coverage line-rate="0.95">
        </coverage>"""
        )

        output_file = tmp_path / "summary.md"

        # Mock command line arguments
        monkeypatch.setattr(
            "sys.argv",
            [
                "test_summary_generator.py",
                "--test-results",
                str(test_xml),
                "--coverage",
                str(coverage_xml),
                "--output",
                str(output_file),
            ],
        )

        from workflow_utils.test_summary_generator import main

        result = main()

        assert result == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "Test Results Summary" in content
        assert "95.0%" in content

    def test_main_missing_test_results(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        """Test main function with missing test results file."""
        monkeypatch.setattr(
            "sys.argv",
            [
                "test_summary_generator.py",
                "--test-results",
                "nonexistent.xml",
            ],
        )

        from workflow_utils.test_summary_generator import main

        result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "Error: Test results file not found" in captured.err
