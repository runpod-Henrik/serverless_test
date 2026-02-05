# CI/CD Integration Guide

This guide explains how to automatically run the flaky test detector when tests fail in your CI/CD pipeline.

## Before You Start: Prevent CI Failures

Before integrating flaky test detection, ensure your CI rarely fails in the first place with our multi-layer defense system:

```bash
# Run all CI checks locally before pushing
./scripts/run_all_checks.sh
```

**See:**
- **[Preventing CI Failures →](PREVENTING_CI_FAILURES.md)** - Multi-layer defense system
- **[Quick Reference →](QUICK_REFERENCE.md)** - Developer cheat sheet
- **[Quality Checks →](QUALITY_CHECKS.md)** - Complete tool documentation

With proper prevention in place, CI should pass >90% of the time, reducing the need for flaky test detection.

## Overview

The integration works by:
1. Your normal CI/CD tests run
2. If tests fail, the flaky test detector workflow triggers automatically
3. Failed tests are re-run 20-30 times to determine reproducibility
4. Results are posted to:
   - GitHub PR comments (with severity indicators and recommendations)
   - CI/CD artifacts for detailed analysis

## Auto-Trigger on Test Failures (NEW!)

The flaky detector now automatically runs when tests fail in pull requests. This provides immediate feedback on whether a test failure is flaky or reproducible.

### How It Works

1. **Test Failure**: Your CI tests fail in a pull request
2. **Auto-Detection**: Flaky detector workflow triggers automatically
3. **Analysis**: Test is run 20 times (configurable) to determine reproducibility
4. **PR Comment**: Results are posted with:
   - Reproduction rate (e.g., "18/20 runs failed = 90%")
   - Severity indicator (🔴 CRITICAL, 🟠 HIGH, 🟡 MEDIUM, 🟢 LOW)
   - Recommended next steps
   - Whether it's a flaky test or a real bug

### Configuration

Control auto-trigger behavior in `.flaky-detector.yml`:

```yaml
# CI/CD Integration
auto_trigger_on_failure: true  # Enable/disable auto-trigger (default: true)
auto_trigger_runs: 20          # Number of runs (1-1000, default: 20)
auto_trigger_parallelism: 5    # Parallel workers (1-50, default: 5)
```

**To disable auto-trigger:**
```yaml
auto_trigger_on_failure: false
```

### Example PR Comment

When tests fail, you'll automatically get a comment like:

```
## 🔍 Flaky Test Detector Results

**Test Reproducibility Analysis**

🔴 CRITICAL: Very high failure rate (>90%) - likely a real bug!

### Results
- **Reproduction Rate**: 95.0%
- **Failures**: 19/20 runs
- **Confidence**: High (based on 20 test runs)

### What This Means

This appears to be a **consistent, reproducible failure** rather than flakiness.
The test failed in 19 out of 20 runs.

**Next Steps:**
1. Review the test failure logs in the failed CI run
2. The high reproduction rate suggests a real bug in the code
3. Debug locally using: `python3 local_test.py`
```

### Benefits

- **Immediate Feedback**: Know instantly if a failure is flaky or real
- **Save Time**: Skip lengthy flaky test investigations
- **Better PRs**: Clear guidance on how to fix the issue
- **No Setup**: Works automatically in pull requests
- **Configurable**: Adjust runs/parallelism based on your needs

## GitHub Actions Setup

### Step 1: Set Up Secrets

Add the following secrets to your repository:
- `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

Required secrets:
- `RUNPOD_API_KEY` - Your RunPod API key
- `RUNPOD_ENDPOINT_ID` - Your deployed flaky test detector endpoint ID

Optional secrets (for notifications):
- `SLACK_WEBHOOK_URL` - Slack incoming webhook URL for notifications

### Step 2: Update Workflow Trigger

Edit `.github/workflows/flaky-test-detector.yml` and change line 4:

```yaml
workflows: ["CI"]  # Replace "CI" with your test workflow name
```

To find your workflow name, look at the `name:` field in your existing test workflow file (e.g., `.github/workflows/test.yml`).

### Step 3: Customize Test Detection

The workflow needs to know which tests failed. Edit `scripts/run_flaky_detector.py` if needed to:

1. Parse your test framework's output
2. Extract specific test names
3. Run only the failed tests

Example for pytest with specific test:
```python
# In run_flaky_detector.py, modify the test_command
test_command = os.environ.get("TEST_COMMAND", "pytest tests/test_specific.py::test_function -v")
```

### Step 4: Create Example CI Workflow

If you don't have a CI workflow yet, create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run tests
        run: |
          pytest tests/ -v
```

### Step 5: Test the Integration

1. Create a PR with a failing test
2. Wait for CI to fail
3. The flaky test detector should automatically trigger
4. Check for:
   - PR comment with results
   - Slack notification (if configured)
   - Workflow run in Actions tab

## Configuration Options

### Environment Variables

You can customize the flaky test detector behavior with environment variables in the workflow:

```yaml
- name: Run flaky test detector
  env:
    FLAKY_TEST_RUNS: "200"        # Number of test runs (default: 100)
    FLAKY_TEST_PARALLELISM: "20"  # Parallel workers (default: 10)
```

### Adjusting Sensitivity

In `scripts/run_flaky_detector.py`, adjust the thresholds:

```python
# Current thresholds:
if repro_rate > 0.9:  # 90%+ = Consistent failure, not flaky
if repro_rate > 0.05:  # 5%+ = Flaky test detected

# Adjust to be more/less sensitive:
if repro_rate > 0.02:  # 2%+ = More sensitive (catches subtle flakiness)
```

## Slack/Discord Integration

### Slack Setup

1. Go to your Slack workspace
2. Navigate to `Settings & administration` → `Manage apps`
3. Search for "Incoming Webhooks" and add it
4. Click "Add to Slack"
5. Choose a channel and click "Add Incoming WebHooks integration"
6. Copy the Webhook URL
7. Add it as `SLACK_WEBHOOK_URL` secret in GitHub

### Discord Setup

Discord webhooks are compatible with Slack format:

1. Go to your Discord server
2. Navigate to `Server Settings` → `Integrations` → `Webhooks`
3. Click "New Webhook"
4. Name it "Flaky Test Detector"
5. Choose a channel
6. Copy the webhook URL and append `/slack` to the end:
   - `https://discord.com/api/webhooks/xxx/yyy/slack`
7. Add it as `SLACK_WEBHOOK_URL` secret in GitHub

## Interpreting Results

### Severity Levels

| Repro Rate | Severity | Meaning |
|------------|----------|---------|
| > 90% | 🔴 CRITICAL | Consistent failure - likely a real bug, not flaky |
| 50-90% | 🟠 HIGH | Frequent failures - needs investigation |
| 10-50% | 🟡 MEDIUM | Clear flaky behavior - should be fixed |
| 1-10% | 🟢 LOW | Occasional flakiness - monitor |
| 0% | ✅ NONE | No flakiness detected - test appears stable |

### Action Items

**🔴 CRITICAL (>90% failure rate)**
- This is likely a real bug, not flakiness
- Do NOT merge the PR
- Investigate and fix the root cause

**🟠 HIGH (50-90% failure rate)**
- Test is very unstable
- Block PR merge until fixed
- Consider disabling test temporarily if urgent

**🟡 MEDIUM (10-50% failure rate)**
- Definite flaky test
- Should be fixed before merge
- Document known flakiness if must merge

**🟢 LOW (1-10% failure rate)**
- Minor flakiness
- Consider fixing, but may merge with caution
- Add to tech debt backlog

**✅ NONE (0% failure rate)**
- CI failure was likely environmental
- Safe to merge if other checks pass
- May have been a one-time issue

## Advanced Usage

### Run on Specific Test Failures Only

Modify the workflow to only trigger for specific test failures:

```yaml
- name: Check if critical tests failed
  id: check-critical
  run: |
    # Add logic to check if critical tests failed
    if grep -q "test_payment\|test_checkout" test_results.txt; then
      echo "run_detector=true" >> $GITHUB_OUTPUT
    fi

- name: Run flaky test detector
  if: steps.check-critical.outputs.run_detector == 'true'
  # ... rest of the step
```

### Extract Specific Failed Tests

To run only the specific failed test instead of the entire test suite:

```yaml
- name: Extract failed test information
  id: extract-tests
  run: |
    # Parse pytest output for failed tests
    FAILED_TESTS=$(grep -oP 'FAILED \K[^ ]+' test_output.log | head -1)
    echo "failed_tests=pytest $FAILED_TESTS -v" >> $GITHUB_OUTPUT
```

### Schedule Regular Flakiness Checks

Add a scheduled workflow to periodically check for flakiness:

```yaml
name: Scheduled Flakiness Check

on:
  schedule:
    - cron: '0 2 * * 0'  # Run every Sunday at 2 AM

jobs:
  check-flakiness:
    runs-on: ubuntu-latest
    steps:
      # ... run all tests through flaky detector
```

## Troubleshooting

### Workflow Not Triggering

**Problem**: Flaky test detector doesn't run after test failures

**Solutions**:
1. Check workflow name matches: `.github/workflows/flaky-test-detector.yml` line 4
2. Verify the CI workflow has completed (not just failed)
3. Check GitHub Actions permissions: `Settings` → `Actions` → `General` → Allow workflows to trigger other workflows

### No PR Comment Posted

**Problem**: Results don't appear as PR comment

**Solutions**:
1. Verify `GITHUB_TOKEN` has `pull-requests: write` permission
2. Check that `PR_NUMBER` is being extracted correctly
3. Look for errors in the "Post results to PR" step logs

### Slack Notifications Not Sending

**Problem**: No Slack notifications received

**Solutions**:
1. Verify `SLACK_WEBHOOK_URL` secret is set correctly
2. Test the webhook URL with curl:
   ```bash
   curl -X POST -H 'Content-type: application/json' \
     --data '{"text":"Test message"}' \
     YOUR_WEBHOOK_URL
   ```
3. Check Slack app permissions

### RunPod Job Fails

**Problem**: Flaky detector job fails on RunPod

**Solutions**:
1. Verify `RUNPOD_API_KEY` and `RUNPOD_ENDPOINT_ID` are correct
2. Check RunPod endpoint is deployed and active
3. Verify repository is accessible (not private, or use deploy keys)
4. Check RunPod endpoint logs for errors

## Cost Optimization

Running 100+ test executions on every failure can add up. Consider:

1. **Limit to critical tests**: Only check tests marked as critical
2. **Reduce runs for low-priority PRs**: Use 50 runs for draft PRs, 100 for ready PRs
3. **Use cheaper compute**: Configure RunPod endpoint with CPU instead of GPU if tests don't need it
4. **Rate limiting**: Only run once per PR, not on every push

Example rate limiting:

```yaml
- name: Check if already ran
  run: |
    # Check if we already commented on this PR
    COMMENTS=$(gh pr view $PR_NUMBER --json comments -q '.comments[].body' | grep "Flaky Test Detection Results")
    if [ ! -z "$COMMENTS" ]; then
      echo "Already ran flaky detection on this PR"
      exit 0
    fi
```

## Best Practices

### 1. Prevent Failures First
Use the multi-layer defense system to catch issues before CI:
- ✅ Enable pre-commit hooks: `pre-commit install`
- ✅ Run local checks: `./scripts/run_all_checks.sh`
- ✅ Follow the prevention guide: `docs/PREVENTING_CI_FAILURES.md`

### 2. Use Flaky Detection Wisely
Only run flaky detection when:
- Tests fail in CI despite passing locally
- Suspected flakiness (intermittent failures)
- After prevention checks have passed

### 3. Track Metrics
Monitor your CI health:
- CI first-pass rate (goal: >90%)
- Number of flaky tests detected per month
- Time saved by catching issues locally

## Support

For issues with the integration:
- Check workflow logs in GitHub Actions
- Review RunPod endpoint logs
- See [Preventing CI Failures](PREVENTING_CI_FAILURES.md) for common issues
- See [Quality Checks](QUALITY_CHECKS.md) for tool configuration
- Open an issue on the repository
- See main README.md for general troubleshooting
