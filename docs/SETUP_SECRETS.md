# CI/CD Integration - Final Setup Steps

The CI/CD integration is **almost ready**! The workflows are now active and committed.

## What's Already Done ✓

- ✓ CI workflow activated (.github/workflows/ci.yml)
- ✓ Flaky test detector workflow ready (.github/workflows/flaky-test-detector.yml)
- ✓ Scripts ready (run_flaky_detector.py, report_to_github.py, report_to_slack.py)
- ✓ RunPod endpoint deployed and tested

## Final Step: Add GitHub Secrets

You need to add your RunPod credentials as GitHub secrets so the workflow can access them.

### Option 1: Using GitHub Web UI (Recommended)

1. **Go to your repository secrets page:**
   ```
   https://github.com/runpod-Henrik/serverless_test/settings/secrets/actions
   ```

2. **Click "New repository secret"** and add:

   **Secret 1:**
   - Name: `RUNPOD_API_KEY`
   - Value: `<your RunPod API key from YOUR_CREDENTIALS.txt>`

   **Secret 2:**
   - Name: `RUNPOD_ENDPOINT_ID`
   - Value: `<your endpoint ID from YOUR_CREDENTIALS.txt>`

   **Secret 3 (Optional - for Slack notifications):**
   - Name: `SLACK_WEBHOOK_URL`
   - Value: `<your Slack webhook URL>`

   **Secret 4 (Optional - for AI-powered workflow validation):**
   - Name: `ANTHROPIC_API_KEY`
   - Value: `<your Claude API key from console.anthropic.com>`
   - Note: Enables AI-powered fix suggestions for workflow errors

3. **Done!** The integration is now fully active.

### Option 2: Using GitHub CLI

If you have GitHub CLI installed:

```bash
# Add RunPod API key (get from YOUR_CREDENTIALS.txt)
gh secret set RUNPOD_API_KEY --body "<your-runpod-api-key>"

# Add RunPod endpoint ID (get from YOUR_CREDENTIALS.txt)
gh secret set RUNPOD_ENDPOINT_ID --body "<your-endpoint-id>"

# (Optional) Add Slack webhook
gh secret set SLACK_WEBHOOK_URL --body "<your-slack-webhook-url>"

# (Optional) Add Anthropic API key for AI workflow validation
gh secret set ANTHROPIC_API_KEY --body "<your-anthropic-api-key>"
```

## How It Works

Once secrets are added, **automatically** on every PR:

1. **Push code** → CI runs tests
2. **If tests fail** → Flaky detector triggers
3. **Detector runs tests 100x** on RunPod
4. **Posts PR comment** with severity analysis:
   - 🔴 CRITICAL (>90%) - Real bug
   - 🟠 HIGH (50-90%) - Very unstable
   - 🟡 MEDIUM (10-50%) - Flaky test
   - 🟢 LOW (1-10%) - Occasional flakiness
   - ✅ NONE (0%) - One-time issue
5. **Sends Slack notification** (if configured)

## Test the Integration

After adding secrets, test it:

```bash
# Create a test branch
git checkout -b test-flaky-detection

# Make a test fail intentionally
# Edit tests/test_flaky.py line 22:
# Change success_threshold = 0.18 to success_threshold = 0.01

# Commit and push
git add tests/test_flaky.py
git commit -m "Test flaky detector"
git push -u origin test-flaky-detection

# Create a PR on GitHub
# Wait for CI to fail
# Check for automatic PR comment with flakiness analysis
```

## Configuration

The integration uses these default settings (customizable in .flaky-detector.yml):

- **Runs:** 100 tests per detection
- **Parallelism:** 10 workers
- **Timeout:** 5 minutes per test
- **Cost:** ~$0.024 per detection run

## Troubleshooting

**Workflow doesn't trigger:**
- Check workflow name matches "CI" in .github/workflows/flaky-test-detector.yml line 5
- Verify GitHub Actions are enabled: Settings → Actions → Allow all actions

**No PR comment:**
- Verify secrets are added correctly
- Check workflow run logs in Actions tab
- Ensure GITHUB_TOKEN has write permissions

**Need help?**
- Full guide: CICD_SETUP_STEPS.txt
- Deployment guide: README.md
- Workflow logs: https://github.com/runpod-Henrik/serverless_test/actions

---

**Status:** ✅ GitHub secrets added successfully!
**Integration:** ✅ Fully automated flaky test detection is now ACTIVE!

Secrets added:
- ✓ RUNPOD_API_KEY (added 2026-02-04)
- ✓ RUNPOD_ENDPOINT_ID (added 2026-02-04)
- ✓ ANTHROPIC_API_KEY (optional - for AI workflow validation)
