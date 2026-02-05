#!/usr/bin/env python3
"""
Validate GitHub Actions workflows and suggest AI-powered fixes.

This script runs actionlint to validate workflows and can use Claude API
to automatically suggest and apply fixes for common issues.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


def run_actionlint(workflow_path: Optional[str] = None) -> tuple[int, str, str]:
    """
    Run actionlint on workflow files.

    Args:
        workflow_path: Specific workflow file to check, or None for all

    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    cmd = ["actionlint", "-color", "-verbose"]
    if workflow_path:
        cmd.append(workflow_path)

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        print("Error: actionlint not found. Install it first:", file=sys.stderr)
        print("  macOS: brew install actionlint", file=sys.stderr)
        print("  Linux: bash <(curl https://raw.githubusercontent.com/rhysd/actionlint/main/scripts/install.sh)", file=sys.stderr)
        sys.exit(1)


def parse_actionlint_output(output: str) -> list[dict]:
    """
    Parse actionlint output into structured errors.

    Args:
        output: Raw actionlint output

    Returns:
        List of error dictionaries with file, line, column, message, etc.
    """
    errors = []
    for line in output.splitlines():
        # Format: file.yml:line:col: message [rule]
        if ".yml:" in line or ".yaml:" in line:
            parts = line.split(":", 4)
            if len(parts) >= 4:
                file_path = parts[0]
                try:
                    line_num = int(parts[1])
                    col_num = int(parts[2])
                    message = parts[3].strip() if len(parts) > 3 else ""

                    # Extract rule name if present
                    rule = None
                    if "[" in message and "]" in message:
                        rule_start = message.rfind("[")
                        rule_end = message.rfind("]")
                        rule = message[rule_start + 1 : rule_end]
                        message = message[:rule_start].strip()

                    errors.append(
                        {
                            "file": file_path,
                            "line": line_num,
                            "column": col_num,
                            "message": message,
                            "rule": rule,
                        }
                    )
                except ValueError:
                    # Skip lines that don't match expected format
                    continue

    return errors


def suggest_fixes_with_ai(errors: list[dict], workflow_content: str) -> Optional[str]:
    """
    Use Claude API to suggest fixes for workflow errors.

    Args:
        errors: List of parsed errors
        workflow_content: Content of the workflow file

    Returns:
        Suggested fixes as a string, or None if API not available
    """
    try:
        import anthropic
    except ImportError:
        print(
            "Warning: anthropic package not installed. Install with: pip install anthropic",
            file=sys.stderr,
        )
        return None

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print(
            "Warning: ANTHROPIC_API_KEY not set. Set it to use AI-powered fix suggestions.",
            file=sys.stderr,
        )
        return None

    client = anthropic.Anthropic(api_key=api_key)

    # Build prompt
    errors_text = "\n".join(
        [
            f"- Line {e['line']}, Col {e['column']}: {e['message']}"
            + (f" [{e['rule']}]" if e["rule"] else "")
            for e in errors
        ]
    )

    prompt = f"""I have a GitHub Actions workflow with the following validation errors from actionlint:

{errors_text}

Here's the workflow file:

```yaml
{workflow_content}
```

Please suggest specific fixes for these errors. For each error, explain:
1. What the issue is
2. How to fix it
3. The corrected code snippet

Focus on practical, working solutions."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )

        return message.content[0].text
    except Exception as e:
        print(f"Error calling Claude API: {e}", file=sys.stderr)
        return None


def format_error_report(errors: list[dict]) -> str:
    """
    Format errors into a readable report.

    Args:
        errors: List of parsed errors

    Returns:
        Formatted error report
    """
    if not errors:
        return "✅ No errors found!"

    report = f"Found {len(errors)} error(s):\n\n"

    # Group by file
    errors_by_file = {}
    for error in errors:
        file = error["file"]
        if file not in errors_by_file:
            errors_by_file[file] = []
        errors_by_file[file].append(error)

    for file, file_errors in errors_by_file.items():
        report += f"📄 {file} ({len(file_errors)} error(s)):\n"
        for err in file_errors:
            report += f"  Line {err['line']}, Col {err['column']}: {err['message']}\n"
            if err["rule"]:
                report += f"    Rule: {err['rule']}\n"
        report += "\n"

    return report


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate GitHub Actions workflows and suggest AI-powered fixes"
    )
    parser.add_argument(
        "workflow",
        nargs="?",
        help="Specific workflow file to check (default: all in .github/workflows/)",
    )
    parser.add_argument(
        "--ai-suggest",
        action="store_true",
        help="Use Claude API to suggest fixes (requires ANTHROPIC_API_KEY)",
    )
    parser.add_argument(
        "--json", action="store_true", help="Output errors in JSON format"
    )
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Exit with non-zero code if errors found",
    )

    args = parser.parse_args()

    # Run actionlint
    print("Running actionlint...", file=sys.stderr)
    exit_code, stdout, stderr = run_actionlint(args.workflow)

    # Parse errors
    errors = parse_actionlint_output(stderr)

    if args.json:
        print(json.dumps(errors, indent=2))
        return exit_code

    # Print error report
    print(format_error_report(errors))

    # Suggest fixes with AI if requested
    if args.ai_suggest and errors:
        print("🤖 Requesting AI-powered fix suggestions...\n", file=sys.stderr)

        # Read workflow file
        workflow_path = (
            args.workflow
            if args.workflow
            else errors[0]["file"]  # Use first error's file
        )
        try:
            with open(workflow_path) as f:
                workflow_content = f.read()

            suggestions = suggest_fixes_with_ai(errors, workflow_content)
            if suggestions:
                print("=" * 80)
                print("AI-SUGGESTED FIXES")
                print("=" * 80)
                print(suggestions)
                print("=" * 80)
        except FileNotFoundError:
            print(f"Error: Workflow file not found: {workflow_path}", file=sys.stderr)

    if args.fail_on_error and errors:
        return 1

    return 0 if exit_code == 0 else exit_code


if __name__ == "__main__":
    sys.exit(main())
