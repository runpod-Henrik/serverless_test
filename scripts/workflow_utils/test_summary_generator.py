#!/usr/bin/env python3
"""
Generate GitHub Actions test summary from JUnit XML and coverage reports.

This script is extracted from .github/workflows/ci.yml for testing purposes.
"""

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional


def parse_test_results(test_results_file: str) -> dict[str, int | float]:
    """
    Parse JUnit XML test results.

    Args:
        test_results_file: Path to test-results.xml

    Returns:
        Dictionary with test statistics
    """
    tree = ET.parse(test_results_file)
    root = tree.getroot()

    tests = int(root.attrib.get("tests", 0))
    failures = int(root.attrib.get("failures", 0))
    errors = int(root.attrib.get("errors", 0))
    skipped = int(root.attrib.get("skipped", 0))
    time = float(root.attrib.get("time", 0))
    passed = tests - failures - errors - skipped

    return {
        "tests": tests,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
        "time": time,
        "passed": passed,
    }


def parse_coverage(coverage_file: str) -> float:
    """
    Parse coverage from coverage.xml.

    Args:
        coverage_file: Path to coverage.xml

    Returns:
        Coverage percentage (0-100)
    """
    try:
        cov_tree = ET.parse(coverage_file)
        cov_root = cov_tree.getroot()
        coverage = float(cov_root.attrib.get("line-rate", 0)) * 100
        return coverage
    except Exception:
        return 0.0


def generate_test_summary(
    test_results: dict[str, int | float],
    coverage: float,
    last_success_sha: Optional[str] = None,
    changed_files: Optional[list[str]] = None,
    commits: Optional[list[str]] = None,
    previous_coverage: Optional[float] = None,
) -> str:
    """
    Generate markdown test summary.

    Args:
        test_results: Test statistics from parse_test_results()
        coverage: Coverage percentage
        last_success_sha: SHA of last successful run (optional)
        changed_files: List of changed files (optional)
        commits: List of commit details (optional)
        previous_coverage: Previous coverage percentage for delta calculation (optional)

    Returns:
        Markdown formatted summary
    """
    failures = test_results["failures"]
    errors = test_results["errors"]
    tests = test_results["tests"]
    passed = test_results["passed"]
    skipped = test_results["skipped"]
    time = test_results["time"]

    summary = "## Test Results Summary\n\n"

    # Overall status
    if failures + errors == 0:
        summary += "✅ **All tests passed!**\n\n"
    else:
        summary += f"❌ **{failures + errors} test(s) failed**\n\n"

    # Show changes since last success (if available)
    if last_success_sha and changed_files:
        summary += "### 📝 Changes Since Last Successful Run\n\n"

        python_files = [f for f in changed_files if f.endswith(".py")]
        workflow_files = [f for f in changed_files if ".github/workflows" in f]
        test_files = [
            f for f in changed_files if "test" in f.lower() and f.endswith(".py")
        ]

        # Show commit information
        if commits:
            summary += f"**Commits:** {len(commits)} new commit(s)\n"
            summary += f"**Comparing:** `{last_success_sha[:7]}...HEAD`\n\n"

            if commits:
                summary += "**Recent Commits:**\n\n"
                summary += "| Commit | Author | Message |\n"
                summary += "|--------|--------|----------|\n"
                for commit in commits[:5]:
                    parts = commit.split("|")
                    if len(parts) >= 5:
                        sha, author = parts[0], parts[1]
                        message = "|".join(parts[4:])
                        # Truncate long messages
                        if len(message) > 60:
                            message = message[:57] + "..."
                        summary += f"| `{sha}` | {author} | {message} |\n"
                if len(commits) > 5:
                    summary += f"\n*... and {len(commits) - 5} more commits*\n"
                summary += "\n"

        summary += "| Category | Count |\n"
        summary += "|----------|-------|\n"
        summary += f"| Total Files Changed | {len(changed_files)} |\n"
        summary += f"| Python Files | {len(python_files)} |\n"
        summary += f"| Test Files | {len(test_files)} |\n"
        summary += f"| Workflow Files | {len(workflow_files)} |\n\n"

        # Show Python files changed
        if python_files:
            summary += "**Python Files Changed:**\n"
            for pf in python_files[:10]:
                summary += f"- `{pf}`\n"
            if len(python_files) > 10:
                summary += f"- ... and {len(python_files) - 10} more\n"
            summary += "\n"

    # Calculate coverage delta
    coverage_delta = None
    coverage_delta_str = ""
    if previous_coverage is not None and previous_coverage > 0:
        coverage_delta = coverage - previous_coverage
        if coverage_delta > 0:
            coverage_delta_str = f" (🟢 +{coverage_delta:.1f}%)"
        elif coverage_delta < 0:
            coverage_delta_str = f" (🔴 {coverage_delta:.1f}%)"
        else:
            coverage_delta_str = " (➡️ no change)"

    # Statistics table
    summary += "| Metric | Value |\n"
    summary += "|--------|-------|\n"
    summary += f"| Total Tests | {tests} |\n"
    summary += f"| ✅ Passed | {passed} |\n"
    summary += f"| ❌ Failed | {failures} |\n"
    summary += f"| ⚠️ Errors | {errors} |\n"
    summary += f"| ⏭️ Skipped | {skipped} |\n"
    summary += f"| ⏱️ Duration | {time:.2f}s |\n"
    summary += f"| 📊 Coverage | {coverage:.1f}%{coverage_delta_str} |\n\n"

    # Coverage status with delta warning
    if coverage >= 95:
        summary += "### 🟢 Coverage Status: Excellent (≥95%)\n"
    elif coverage >= 90:
        summary += "### 🟡 Coverage Status: Good (≥90%)\n"
    else:
        summary += "### 🔴 Coverage Status: Needs Improvement (<90%)\n"

    # Highlight negative coverage delta
    if coverage_delta is not None and coverage_delta < 0:
        summary += f"\n⚠️ **Coverage decreased by {abs(coverage_delta):.1f}%** "
        summary += f"(was {previous_coverage:.1f}%, now {coverage:.1f}%)\n"

    return summary


def main() -> int:
    """Main entry point for CLI usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate test summary from results")
    parser.add_argument(
        "--test-results",
        default="test-results.xml",
        help="Path to JUnit XML test results",
    )
    parser.add_argument(
        "--coverage", default="coverage.xml", help="Path to coverage XML report"
    )
    parser.add_argument(
        "--output", default=None, help="Output file (default: stdout)"
    )

    args = parser.parse_args()

    # Validate input files exist
    if not Path(args.test_results).exists():
        print(f"Error: Test results file not found: {args.test_results}", file=sys.stderr)
        return 1

    # Parse results
    test_results = parse_test_results(args.test_results)
    coverage = parse_coverage(args.coverage) if Path(args.coverage).exists() else 0.0

    # Generate summary
    summary = generate_test_summary(test_results, coverage)

    # Write output
    if args.output:
        with open(args.output, "w") as f:
            f.write(summary)
        print(f"Summary written to {args.output}")
    else:
        print(summary)

    return 0


if __name__ == "__main__":
    sys.exit(main())
