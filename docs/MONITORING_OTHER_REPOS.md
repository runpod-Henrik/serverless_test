# Monitoring Other Repositories

Guide for setting up testflake to monitor any repository for flaky tests, including auto-detection on CI failures.

## Table of Contents

1. [Overview](#overview)
2. [Quick Setup](#quick-setup)
3. [Configuration Files](#configuration-files)
4. [GitHub Actions Integration](#github-actions-integration)
5. [Examples](#examples)
6. [Advanced Features](#advanced-features)

## Overview

Testflake can monitor any repository by:
- **Auto-triggering**: Automatically runs when CI tests fail
- **Manual runs**: On-demand flakiness detection
- **Scheduled checks**: Nightly or weekly monitoring
- **Historical tracking**: Track flakiness trends over time

**Perfect for:**
- Large codebases with complex test suites
- Projects with intermittent CI failures
- Teams wanting to improve test reliability
- Open source projects with contributor PRs

## Quick Setup

**3 files to add to any repository:**

1. `.flaky-detector.yml` - Configuration
2. `.github/workflows/flaky-detector-auto.yml` - Auto-trigger workflow
3. GitHub Secrets - API credentials

**Time to setup:** 5-10 minutes

## Configuration Files

### 1. Repository Configuration

Create `.flaky-detector.yml` in the repository root:

```yaml
# Flaky Test Detector Configuration
# Add this file to your repository root

# Test execution settings
runs: 100                      # Number of times to run tests (1-1000)
parallelism: 20                # Parallel workers (1-50)
timeout: 600                   # Timeout per test run (seconds)

# Auto-trigger settings
auto_trigger_on_failure: true  # Enable auto-detection on CI failures
auto_trigger_runs: 50          # Runs for auto-triggered checks (faster)
auto_trigger_parallelism: 10   # Workers for auto-trigger

# Severity thresholds (0.0 to 1.0)
severity_thresholds:
  critical: 0.9   # 90%+ failure rate = likely a real bug
  high: 0.5       # 50-90% = very unstable test
  medium: 0.1     # 10-50% = clear flakiness
  low: 0.01       # 1-10% = occasional issues

# Test command
# Customize this based on your project's test setup
test_command: "pytest tests/ -v"

# Optional: Ignore patterns
ignore_patterns:
  - "test_known_flaky_*"    # Skip tests matching pattern
  - "test_wip_*"            # Work in progress tests
  - "test_experimental_*"   # Experimental features

# Optional: Environment variables
environment:
  TEST_ENV: "ci"
  PYTEST_TIMEOUT: "30"
```

**Common test commands by framework:**

```yaml
# Python with pytest
test_command: "pytest tests/ -v"

# Python with pytest and markers
test_command: "pytest tests/ -v -m 'not slow'"

# Python with unittest
test_command: "python -m unittest discover tests"

# Go
test_command: "go test ./... -v"

# Node.js with Jest
test_command: "npm test"

# Node.js with Mocha
test_command: "npm run test"

# Make-based
test_command: "make test"

# Custom script
test_command: "./scripts/run_tests.sh"
```

### 2. Auto-Trigger Workflow

Create `.github/workflows/flaky-detector-auto.yml`:

```yaml
name: Flaky Test Detector

on:
  workflow_run:
    workflows: ["CI"]  # Change to match your CI workflow name
    types: [completed]

permissions:
  contents: read
  pull-requests: write
  issues: write
  actions: read

jobs:
  detect-flaky:
    # Only run if CI failed
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          ref: ${{ github.event.workflow_run.head_branch }}

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install runpod pyyaml requests

      - name: Load configuration
        id: config
        run: |
          if [ -f .flaky-detector.yml ]; then
            python3 << 'EOF'
          import yaml
          with open('.flaky-detector.yml') as f:
              config = yaml.safe_load(f)

          # Set outputs for GitHub Actions
          runs = config.get('auto_trigger_runs', config.get('runs', 50))
          parallelism = config.get('auto_trigger_parallelism', config.get('parallelism', 10))
          test_command = config.get('test_command', 'pytest tests/ -v')

          print(f"runs={runs}")
          print(f"parallelism={parallelism}")
          print(f"test_command={test_command}")
          EOF
          else
            echo "runs=50"
            echo "parallelism=10"
            echo "test_command=pytest tests/ -v"
          fi

      - name: Run flaky test detection
        id: detect
        env:
          RUNPOD_API_KEY: ${{ secrets.RUNPOD_API_KEY }}
          RUNPOD_ENDPOINT_ID: ${{ secrets.RUNPOD_ENDPOINT_ID }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python3 << 'EOF'
          import runpod
          import json
          import os
          import sys

          # Configure RunPod
          runpod.api_key = os.environ['RUNPOD_API_KEY']
          endpoint_id = os.environ['RUNPOD_ENDPOINT_ID']

          # Get configuration
          runs = int(os.environ.get('runs', '50'))
          parallelism = int(os.environ.get('parallelism', '10'))
          test_command = os.environ.get('test_command', 'pytest tests/ -v')

          print(f"🔍 Starting flaky test detection...")
          print(f"   Repository: {os.environ['GITHUB_REPOSITORY']}")
          print(f"   Branch: {os.environ.get('GITHUB_REF_NAME', 'unknown')}")
          print(f"   Runs: {runs}")
          print(f"   Parallelism: {parallelism}")
          print(f"   Command: {test_command}")
          print()

          try:
              # Run detection
              job = runpod.Endpoint(endpoint_id).run({
                  'repo': f"https://github.com/{os.environ['GITHUB_REPOSITORY']}",
                  'test_command': test_command,
                  'runs': runs,
                  'parallelism': parallelism
              })

              result = job.output()

              # Save results
              with open('flaky_results.json', 'w') as f:
                  json.dump(result, f, indent=2)

              # Output summary
              rate = result['repro_rate']
              print(f"✅ Detection complete!")
              print(f"   Reproduction rate: {rate*100:.1f}%")
              print(f"   Total runs: {result['total_runs']}")
              print(f"   Failures: {result['failures']}")
              print(f"   Passed: {result['total_runs'] - result['failures']}")

              # Set output for next step
              with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                  f.write(f"repro_rate={rate}\n")
                  f.write(f"severity={'critical' if rate >= 0.9 else 'high' if rate >= 0.5 else 'medium' if rate >= 0.1 else 'low' if rate > 0 else 'none'}\n")

          except Exception as e:
              print(f"❌ Error running detection: {e}")
              sys.exit(1)
          EOF

      - name: Generate PR comment
        if: github.event.workflow_run.event == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const results = JSON.parse(fs.readFileSync('flaky_results.json', 'utf8'));
            const rate = results.repro_rate;

            // Determine severity
            let severity, emoji, message, recommendation;
            if (rate >= 0.9) {
              severity = 'CRITICAL';
              emoji = '🔴';
              message = 'This appears to be a real bug, not a flaky test.';
              recommendation = '**Do not merge.** Fix the failing test first.';
            } else if (rate >= 0.5) {
              severity = 'HIGH';
              emoji = '🟠';
              message = 'Very unstable test that fails more than half the time.';
              recommendation = '**Should not merge.** Stabilize the test before merging.';
            } else if (rate >= 0.1) {
              severity = 'MEDIUM';
              emoji = '🟡';
              message = 'Clear flaky behavior detected.';
              recommendation = 'Consider stabilizing the test. Review for race conditions or timing issues.';
            } else if (rate > 0) {
              severity = 'LOW';
              emoji = '🟢';
              message = 'Occasional flakiness detected.';
              recommendation = 'Minor flakiness. May be safe to merge but monitor for patterns.';
            } else {
              severity = 'NONE';
              emoji = '✅';
              message = 'No flakiness detected in repeated runs.';
              recommendation = 'This was likely a one-time failure. Safe to merge after fixing.';
            }

            // Build comment
            const comment = `## ${emoji} ${severity}: Flaky Test Analysis

            **Reproduction Rate:** ${(rate * 100).toFixed(1)}%
            - Total Runs: ${results.total_runs}
            - Failed: ${results.failures}
            - Passed: ${results.total_runs - results.failures}
            - Parallelism: ${results.parallelism}

            **Analysis:** ${message}

            **Recommendation:** ${recommendation}

            ### What This Means

            The flaky test detector ran your failing test ${results.total_runs} times in parallel to determine if it's flaky or a real bug:

            - **100% failure** = Real bug that needs fixing
            - **50-90% failure** = Very unstable test
            - **10-50% failure** = Clear flakiness (race conditions, timing issues)
            - **1-10% failure** = Occasional flakiness
            - **0% failure** = One-time glitch

            <details>
            <summary>View detailed results</summary>

            \`\`\`json
            ${JSON.stringify(results, null, 2).slice(0, 5000)}
            \`\`\`
            </details>

            ---

            🤖 Automated flaky test detection by [testflake](https://github.com/runpod/testflake)`;

            // Get PR number from workflow run
            const { data: prs } = await github.rest.pulls.list({
              owner: context.repo.owner,
              repo: context.repo.repo,
              head: `${context.repo.owner}:${context.payload.workflow_run.head_branch}`
            });

            if (prs.length > 0) {
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: prs[0].number,
                body: comment
              });

              console.log(`✅ Posted comment on PR #${prs[0].number}`);
            } else {
              console.log('⚠️  No PR found for this branch');
            }

      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: flaky-test-results
          path: flaky_results.json
          retention-days: 30
```

### 3. GitHub Secrets

Add these secrets to your repository:

**Go to:** `https://github.com/YOUR_ORG/YOUR_REPO/settings/secrets/actions`

**Required secrets:**

```bash
# Using GitHub CLI:
gh secret set RUNPOD_API_KEY --body "your-runpod-api-key" --repo YOUR_ORG/YOUR_REPO
gh secret set RUNPOD_ENDPOINT_ID --body "your-endpoint-id" --repo YOUR_ORG/YOUR_REPO

# Or manually in GitHub web interface:
# 1. Go to repository Settings
# 2. Click "Secrets and variables" → "Actions"
# 3. Click "New repository secret"
# 4. Add RUNPOD_API_KEY with your API key
# 5. Add RUNPOD_ENDPOINT_ID with your endpoint ID
```

**Getting your credentials:**
- **API Key**: https://www.runpod.io/console/user/settings
- **Endpoint ID**: Deploy testflake on RunPod (see [RUNPOD_TUTORIAL.md](RUNPOD_TUTORIAL.md))

## GitHub Actions Integration

### Matching Your CI Workflow Name

The flaky detector triggers when your CI workflow fails. Make sure the workflow name matches:

```yaml
on:
  workflow_run:
    workflows: ["CI"]  # ← Change this to match your workflow name
    types: [completed]
```

**How to find your CI workflow name:**

1. Check `.github/workflows/*.yml` files
2. Look for the `name:` field at the top
3. Update the `workflows:` array to match

**Examples:**

```yaml
# If your CI is named "Tests"
workflows: ["Tests"]

# If you have multiple CI workflows
workflows: ["Tests", "Integration Tests", "E2E"]

# If your CI is named "CI/CD Pipeline"
workflows: ["CI/CD Pipeline"]
```

### Permissions

The workflow needs these permissions to post comments:

```yaml
permissions:
  contents: read          # Read repository code
  pull-requests: write    # Comment on PRs
  issues: write          # Create issues (optional)
  actions: read          # Read workflow status
```

## Examples

### Example 1: Monitoring runpod/runpod Repository

**`.flaky-detector.yml`:**

```yaml
# Flaky detector config for runpod/runpod
runs: 100
parallelism: 20
timeout: 600

auto_trigger_on_failure: true
auto_trigger_runs: 50
auto_trigger_parallelism: 10

severity_thresholds:
  critical: 0.9
  high: 0.5
  medium: 0.1
  low: 0.01

# RunPod test command (adjust based on actual test structure)
test_command: "pytest tests/ -v -m 'not slow'"

ignore_patterns:
  - "test_benchmark_*"
  - "test_performance_*"
```

**Workflow:** Use the standard `.github/workflows/flaky-detector-auto.yml` above

**Secrets:** Add to https://github.com/runpod/runpod/settings/secrets/actions

### Example 2: Large Monorepo

For repositories with multiple test suites:

**`.flaky-detector.yml`:**

```yaml
runs: 200                # More thorough testing
parallelism: 30          # Higher parallelism
timeout: 900             # 15 minute timeout

test_command: "pytest tests/unit/ tests/integration/ -v --maxfail=1"

# Separate configs for different test types
test_suites:
  unit:
    command: "pytest tests/unit/ -v"
    runs: 100
    parallelism: 20

  integration:
    command: "pytest tests/integration/ -v"
    runs: 50
    parallelism: 10

  e2e:
    command: "pytest tests/e2e/ -v"
    runs: 30
    parallelism: 5
```

### Example 3: Go Project

**`.flaky-detector.yml`:**

```yaml
runs: 100
parallelism: 20
timeout: 600

auto_trigger_on_failure: true

test_command: "go test ./... -v -race -count=1"

environment:
  GO_TEST_SEED: "random"
  CGO_ENABLED: "1"
```

### Example 4: Node.js with Jest

**`.flaky-detector.yml`:**

```yaml
runs: 100
parallelism: 15
timeout: 300

test_command: "npm test -- --maxWorkers=1"

environment:
  NODE_ENV: "test"
  JEST_SEED: "random"
```

## Advanced Features

### 1. Nightly Monitoring

Track flakiness trends over time with scheduled checks:

**`.github/workflows/nightly-flakiness.yml`:**

```yaml
name: Nightly Flakiness Check

on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM UTC daily
  workflow_dispatch:     # Manual trigger

jobs:
  comprehensive-check:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install runpod pyyaml

      - name: Run comprehensive flakiness check
        env:
          RUNPOD_API_KEY: ${{ secrets.RUNPOD_API_KEY }}
          RUNPOD_ENDPOINT_ID: ${{ secrets.RUNPOD_ENDPOINT_ID }}
        run: |
          python3 << 'EOF'
          import runpod
          import json
          import os
          from datetime import datetime

          runpod.api_key = os.environ['RUNPOD_API_KEY']

          # Run on entire test suite
          job = runpod.Endpoint(os.environ['RUNPOD_ENDPOINT_ID']).run({
              'repo': f"https://github.com/{os.environ['GITHUB_REPOSITORY']}",
              'test_command': 'pytest tests/ -v',
              'runs': 100,
              'parallelism': 20
          })

          result = job.output()

          # Save with timestamp
          filename = f"flakiness-report-{datetime.now():%Y%m%d}.json"
          with open(filename, 'w') as f:
              json.dump({
                  'timestamp': datetime.now().isoformat(),
                  'results': result
              }, f, indent=2)

          print(f"📊 Flakiness Report: {result['repro_rate']*100:.1f}%")
          EOF

      - name: Upload report
        uses: actions/upload-artifact@v4
        with:
          name: nightly-flakiness-report
          path: flakiness-report-*.json

      - name: Create issue if high flakiness
        if: steps.detect.outputs.severity == 'high' || steps.detect.outputs.severity == 'critical'
        uses: actions/github-script@v7
        with:
          script: |
            await github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: '⚠️ High flakiness detected in nightly check',
              body: 'The nightly flakiness check detected high levels of test instability. Please review the artifacts.',
              labels: ['flaky-tests', 'testing']
            });
```

### 2. Slack Notifications

Get notified about flaky tests in Slack:

**Add to workflow:**

```yaml
      - name: Notify Slack
        if: steps.detect.outputs.severity == 'high' || steps.detect.outputs.severity == 'critical'
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
        run: |
          curl -X POST $SLACK_WEBHOOK_URL \
            -H 'Content-Type: application/json' \
            -d '{
              "text": "🔴 High flakiness detected!",
              "blocks": [{
                "type": "section",
                "text": {
                  "type": "mrkdwn",
                  "text": "*Flaky Test Alert*\nRepository: ${{ github.repository }}\nRate: ${{ steps.detect.outputs.repro_rate }}%"
                }
              }]
            }'
```

**Add secret:**

```bash
gh secret set SLACK_WEBHOOK_URL --body "your-webhook-url" --repo YOUR_ORG/YOUR_REPO
```

### 3. Historical Tracking

Track flakiness over time with a database:

```yaml
      - name: Store in database
        run: |
          python3 << 'EOF'
          import sqlite3
          import json
          from datetime import datetime

          # Load results
          with open('flaky_results.json') as f:
              results = json.load(f)

          # Store in database
          conn = sqlite3.connect('flakiness_history.db')
          c = conn.cursor()

          c.execute('''
              CREATE TABLE IF NOT EXISTS test_runs (
                  id INTEGER PRIMARY KEY,
                  timestamp TEXT,
                  repo TEXT,
                  branch TEXT,
                  test_command TEXT,
                  repro_rate REAL,
                  total_runs INTEGER,
                  failures INTEGER
              )
          ''')

          c.execute('''
              INSERT INTO test_runs VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)
          ''', (
              datetime.now().isoformat(),
              os.environ['GITHUB_REPOSITORY'],
              os.environ.get('GITHUB_REF_NAME', 'unknown'),
              results.get('test_command', 'unknown'),
              results['repro_rate'],
              results['total_runs'],
              results['failures']
          ))

          conn.commit()
          conn.close()
          EOF
```

### 4. Multi-Suite Testing

Test different suites separately:

```yaml
      - name: Test unit tests
        run: |
          # Run flaky detector on unit tests only

      - name: Test integration tests
        run: |
          # Run flaky detector on integration tests only

      - name: Test e2e tests
        run: |
          # Run flaky detector on e2e tests only
```

## Troubleshooting

### Issue: Workflow Not Triggering

**Check:**
1. Workflow name matches your CI workflow
2. Secrets are set correctly
3. Workflow file is in `.github/workflows/`
4. Permissions are configured

**Debug:**
```yaml
      - name: Debug
        run: |
          echo "Workflow run conclusion: ${{ github.event.workflow_run.conclusion }}"
          echo "Event type: ${{ github.event.workflow_run.event }}"
```

### Issue: Detection Takes Too Long

**Solutions:**
1. Reduce `runs` in configuration
2. Increase `parallelism`
3. Use faster test command
4. Split into multiple jobs

### Issue: High Costs

**Solutions:**
1. Use `auto_trigger_runs` (lower than `runs`)
2. Set `auto_trigger_on_failure: true` only
3. Use scheduled checks instead of every failure
4. Optimize parallelism

### Issue: False Positives

**Solutions:**
1. Increase `runs` for more confidence
2. Adjust `severity_thresholds`
3. Add `ignore_patterns` for known issues
4. Investigate and fix actual flakiness

## Best Practices

1. **Start Small**: Begin with 20-50 runs, increase as needed
2. **Target Specific Tests**: Test failing tests, not entire suite
3. **Monitor Costs**: Track RunPod usage and optimize
4. **Fix Issues**: Don't ignore flaky tests - fix them
5. **Share Results**: Post to PRs for team visibility
6. **Track Trends**: Use historical tracking for insights
7. **Automate**: Let it run automatically on CI failures

## Next Steps

- **[RunPod Deployment](RUNPOD_TUTORIAL.md)** - Deploy testflake on RunPod
- **[CI/CD Integration](CICD_INTEGRATION.md)** - Advanced GitHub Actions setup
- **[Configuration Guide](../TEST_INPUT_FILES.md)** - Complete configuration reference
- **[Quick Reference](QUICK_REFERENCE.md)** - Command cheat sheet

---

**Ready to set up monitoring?** Follow the [Quick Setup](#quick-setup) steps above!
