#!/usr/bin/env python3
"""
Send flaky test results to Slack via webhook.
"""
import json
import os
import sys
from typing import Any

import requests


def create_slack_message(result: dict[str, Any]) -> dict[str, Any]:
    """Create Slack message blocks."""
    total_runs = result.get("total_runs", 0)
    failures = result.get("failures", 0)
    repro_rate = result.get("repro_rate", 0)

    # Determine color and emoji
    if repro_rate > 0.9:
        color = "#ff0000"  # Red
        emoji = "🔴"
        severity = "CRITICAL"
    elif repro_rate > 0.5:
        color = "#ff9500"  # Orange
        emoji = "🟠"
        severity = "HIGH"
    elif repro_rate > 0.1:
        color = "#ffcc00"  # Yellow
        emoji = "🟡"
        severity = "MEDIUM"
    elif repro_rate > 0:
        color = "#00ff00"  # Green
        emoji = "🟢"
        severity = "LOW"
    else:
        color = "#00ff00"  # Green
        emoji = "✅"
        severity = "NONE"

    repository = os.environ.get("GITHUB_REPOSITORY", "unknown")
    pr_number = os.environ.get("PR_NUMBER", "")
    run_url = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    run_url += f"/{repository}/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}"

    # Build message
    message = {
        "attachments": [
            {
                "color": color,
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"{emoji} Flaky Test Detection - {severity}",
                        },
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Repository:*\n{repository}",
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*PR:*\n#{pr_number}" if pr_number else "*Branch:*\nmain",
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Total Runs:*\n{total_runs}",
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Failures:*\n{failures}",
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Repro Rate:*\n{repro_rate * 100:.1f}%",
                            },
                        ],
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {"type": "plain_text", "text": "View Run"},
                                "url": run_url,
                            }
                        ],
                    },
                ],
            }
        ]
    }

    return message


def main() -> None:
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")

    if not webhook_url:
        print("WARNING: SLACK_WEBHOOK_URL not set, skipping Slack notification")
        sys.exit(0)

    # Load results
    try:
        with open("flaky_test_results.json") as f:
            result = json.load(f)
    except FileNotFoundError:
        print("ERROR: Results file not found")
        sys.exit(1)

    # Create message
    message = create_slack_message(result)

    # Send to Slack
    try:
        response = requests.post(webhook_url, json=message)
        response.raise_for_status()
        print("✅ Sent notification to Slack")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to send Slack notification: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
