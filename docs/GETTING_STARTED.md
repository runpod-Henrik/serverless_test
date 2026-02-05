# Getting Started with Flaky Test Detector

Get up and running with flaky test detection in under 5 minutes!

## Table of Contents

1. [Quick Install](#quick-install)
2. [Manual Setup](#manual-setup)
3. [First Run](#first-run)
4. [Common Scenarios](#common-scenarios)
5. [Next Steps](#next-steps)

## Quick Install

### Automated Setup (Recommended)

Run the interactive setup script in your repository:

```bash
# Clone or download the flaky test detector
git clone https://github.com/runpod-Henrik/serverless_test.git flaky-detector
cd your-repository

# Run setup
bash ../flaky-detector/setup.sh
```

The setup script will:
- ✅ Detect your test framework automatically
- ✅ Generate configuration files
- ✅ Set up GitHub Actions (optional)
- ✅ Install dependencies
- ✅ Configure .gitignore

**That's it!** Skip to [First Run](#first-run).

## Manual Setup

If you prefer manual setup or the automated script doesn't work:

### 1. Install Dependencies

```bash
pip install runpod pytest pyyaml jsonschema
```

### 2. Copy Core Files

Copy these files to your repository root:

```
your-repo/
├── worker.py              # Main detector logic
├── config.py              # Configuration management
├── database.py            # Results tracking
├── validate_input.py      # Input validation
├── input_schema.json      # JSON schema
└── local_test.py          # Local testing script
```

### 3. Create Configuration

Create `.flaky-detector.yml`:

```yaml
# Flaky Test Detector Configuration
runs: 50
parallelism: 5
timeout: 600

# Your test command
test_command: "pytest tests/"  # Change this!

# CI Integration
auto_trigger_on_failure: true
auto_trigger_runs: 20
auto_trigger_parallelism: 5

# Severity thresholds
severity_thresholds:
  critical: 0.9
  high: 0.5
  medium: 0.1
  low: 0.01
```

### 4. Create Test Input Template

Create `test_input.json`:

```json
{
  "repo": "https://github.com/your-org/your-repo",
  "test_command": "pytest tests/",
  "runs": 50,
  "parallelism": 5
}
```

### 5. Update .gitignore

Add to `.gitignore`:

```
# Flaky Test Detector
flaky_test_results.json
flaky_detector.db
```

### 6. Optional: GitHub Actions

Copy `.github/workflows/flaky-detector-auto.yml` to enable automatic detection on PR test failures.

## First Run

### Test Local Execution

```bash
python3 local_test.py
```

This will:
1. Read configuration from `test_input.json`
2. Run your tests multiple times
3. Analyze failure patterns
4. Generate `flaky_test_results.json`

### Understanding the Output

```
══════════════════════════════════════════════════════════════════
🔍 FLAKY TEST DETECTOR - 2026-02-05 14:30:00
══════════════════════════════════════════════════════════════════
📦 Repository:    /path/to/your/repo
🧪 Test command:  pytest tests/
🔄 Runs:          50
⚡ Parallelism:   5
══════════════════════════════════════════════════════════════════

⏳ Running tests... (this may take a while)

══════════════════════════════════════════════════════════════════
📊 TEST RESULTS
══════════════════════════════════════════════════════════════════
Total runs:       50
Passed:           45 (90.0%)
Failed:           5 (10.0%)
Reproduction:     10.0%
Framework:        python

⏱️  Execution time: 2m 15s
⏱️  Total time:     2m 18s
══════════════════════════════════════════════════════════════════

🟡 MEDIUM: Clear flaky behavior detected

This test shows intermittent flakiness.
Consider stabilizing it to improve CI reliability.

📄 Detailed results saved to: flaky_test_results.json
```

### Interpreting Results

| Repro Rate | Severity | Meaning |
|------------|----------|---------|
| > 90%      | 🔴 CRITICAL | Likely a real bug, not flaky |
| 50-90%     | 🟠 HIGH | Very unstable, needs fixing |
| 10-50%     | 🟡 MEDIUM | Clear flakiness |
| 1-10%      | 🟢 LOW | Occasional issues |
| 0%         | ✅ NONE | No flakiness detected |

## Common Scenarios

### Scenario 1: CI Test Fails, Need to Know if Flaky

```bash
# 1. Update test_input.json with the failing test
cat > test_input.json <<EOF
{
  "repo": ".",
  "test_command": "pytest tests/test_auth.py::test_login -v",
  "runs": 20,
  "parallelism": 5
}
EOF

# 2. Run locally
python3 local_test.py

# 3. Check results
cat flaky_test_results.json | jq '.repro_rate'
```

**If repro rate is 100%**: It's a real bug, not flaky
**If repro rate is 10-90%**: It's flaky, investigate race conditions/timing

### Scenario 2: Want to Check All Tests for Flakiness

```bash
# Run entire test suite multiple times
cat > test_input.json <<EOF
{
  "repo": ".",
  "test_command": "pytest tests/",
  "runs": 50,
  "parallelism": 10
}
EOF

python3 local_test.py
```

### Scenario 3: Debugging a Specific Flaky Test

```bash
# Run with verbose output
python3 local_test.py -v

# Or target specific test with more runs
cat > test_input.json <<EOF
{
  "repo": ".",
  "test_command": "pytest tests/test_flaky.py -v",
  "runs": 100,
  "parallelism": 10
}
EOF

python3 local_test.py
```

### Scenario 4: Using Local Repository for Faster Iteration

```json
{
  "repo": "/path/to/local/repo",
  "test_command": "pytest tests/",
  "runs": 10,
  "parallelism": 3
}
```

No need to push to GitHub - test uncommitted changes directly!

## Next Steps

### Enable Auto-Detection in CI

Copy `.github/workflows/flaky-detector-auto.yml` to your repo to automatically run flaky detection when PR tests fail.

**Result**: Get immediate feedback on whether test failures are flaky!

### Customize Configuration

Edit `.flaky-detector.yml` to:
- Adjust default runs/parallelism
- Set repository-specific test commands
- Configure severity thresholds
- Add test patterns to ignore

See [Configuration Guide](../TEST_INPUT_FILES.md)

### Integrate with Your Workflow

1. **Pre-commit**: Run flaky detector on changed tests
2. **PR checks**: Auto-detect flakiness on failures
3. **Nightly builds**: Check entire suite for new flakiness
4. **Dashboard**: View trends over time (use `database.py`)

See [CI/CD Integration](CICD_INTEGRATION.md)

### Learn More

- **[Configuration Guide](../TEST_INPUT_FILES.md)** - Complete config reference
- **[CI/CD Integration](CICD_INTEGRATION.md)** - GitHub Actions setup
- **[Debugging Guide](DEBUGGING_TEST_FAILURES.md)** - Complete workflow
- **[Architecture](ARCHITECTURE.md)** - System design
- **[Quick Reference](QUICK_REFERENCE.md)** - Command cheat sheet

## Troubleshooting

### "Module 'runpod' not found"

```bash
pip install runpod
```

### "test_input.json not found"

Create it:
```bash
cat > test_input.json <<EOF
{
  "repo": ".",
  "test_command": "pytest tests/",
  "runs": 10,
  "parallelism": 3
}
EOF
```

### Tests taking too long

Reduce runs or increase parallelism:
```json
{
  "runs": 10,
  "parallelism": 10
}
```

### "Invalid repository URL or path"

Use local path instead:
```json
{
  "repo": ".",
  "test_command": "..."
}
```

## Quick Commands

```bash
# Run with defaults
python3 local_test.py

# Run with custom input
python3 local_test.py -i my_test.json

# Verbose output
python3 local_test.py -v

# Quiet mode (for scripts)
python3 local_test.py -q

# Check results
cat flaky_test_results.json | jq

# View repro rate
cat flaky_test_results.json | jq '.repro_rate'

# Count failures
cat flaky_test_results.json | jq '.failures'
```

## Support

- **Issues**: https://github.com/runpod-Henrik/serverless_test/issues
- **Documentation**: See `docs/` directory
- **Examples**: See `tests/` directory

---

🎉 **You're all set!** Start detecting flaky tests and improving your CI reliability.
