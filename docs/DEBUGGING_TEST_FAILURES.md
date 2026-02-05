# Debugging Test Failures - Complete Workflow

This guide shows you how to investigate and fix test failures using the flaky test detector and AI-assisted root cause analysis.

## Quick Start

When CI fails:

```bash
# 1. Update test_input.json with the failing test
# 2. Run the flaky detector
python3 local_test.py

# 3. Check if it's flaky or a real bug
# 4. Use AI to analyze the root cause
# 5. Fix and verify
```

## Complete Workflow Example

### Scenario: CI Test Failure

You push code and CI fails with:
```
FAILED tests/test_config.py::TestConfig::test_default_config
AssertionError: assert 10 == 11
```

### Step 1: Check the CI Logs

```bash
# View the failure details
gh run view --log-failed

# Or check specific run
gh run view <run-id> --log-failed
```

**What to look for:**
- Which test failed
- The assertion error message
- Any stack traces
- Exit codes

### Step 2: Determine if It's Flaky

Update `test_input.json` to target the failing test:

```json
{
  "repo": "https://github.com/your-org/your-repo",
  "test_command": "pytest tests/test_config.py::TestConfig::test_default_config -v",
  "runs": 10,
  "parallelism": 3
}
```

Run the flaky test detector locally:

```bash
python3 local_test.py
```

**Interpret the results:**

```
Total runs:    10
Failures:      10
Passes:        0
Repro rate:    100.0%

🔴 CRITICAL: Very high failure rate (>90%) - likely a real bug!
```

| Repro Rate | Meaning | Action |
|------------|---------|--------|
| **0-10%** | Very flaky | Investigate timing/race conditions |
| **10-30%** | Moderately flaky | Check randomness, external deps |
| **30-70%** | Intermittent | Environmental issues likely |
| **70-90%** | Mostly failing | Real bug with some conditions |
| **90-100%** | Consistent bug | Direct code/test issue |

### Step 3: AI-Assisted Root Cause Analysis

Read the detailed results:

```bash
cat flaky_test_results.json | jq '.results[0]'
```

**Create an analysis prompt:**

```
I have a test failure with these details:

Test: tests/test_config.py::TestConfig::test_default_config
Error: AssertionError: assert 10 == 11
  where 10 = config.get("runs")

Repro rate: 100% (10/10 runs failed)

The test expects config.get("runs") to equal 11, but it returns 10.

Please analyze:
1. What is the root cause?
2. Is the test wrong or the code wrong?
3. What's the fix?
```

**AI Analysis Response:**
```
Root Cause: Test assertion bug

The default configuration in config.py:12 defines "runs": 10
The test incorrectly expects this to be 11

Type: Test bug (not a code bug)

Fix: Change line 17 in tests/test_config.py from:
  assert config.get("runs") == 11
To:
  assert config.get("runs") == 10
```

### Step 4: Apply the Fix

```bash
# Edit the file
vim tests/test_config.py

# Verify the fix locally
PYTHONPATH=. pytest tests/test_config.py::TestConfig::test_default_config -v

# Run all checks
./scripts/run_all_checks.sh
```

### Step 5: Commit and Verify

```bash
# Commit with detailed message
git add tests/test_config.py
git commit -m "Fix test assertion to match actual default config value

Root cause analysis (AI-assisted):
- Test expected config.get('runs') == 11
- Actual default value is 10 (defined in config.py:12)
- Fixed test to assert correct value

Verified with flaky test detector:
- 100% failure rate confirmed not a flaky test
- Consistent bug in test assertion

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# Push and verify CI
git push

# Monitor CI
gh run watch
```

### Step 6: Verify CI Success

```bash
# Check latest run
gh run list --limit 1

# View full results
gh run view
```

Expected output:
```
✓ Lint and Type Check    - 1m2s  ✅
✓ Test Suite             - 1m3s  ✅ (all tests passing)
✓ System Validation      - 48s   ✅
```

## Common Scenarios

### Scenario A: Intermittent Failure (Flaky Test)

**Symptoms:**
- Repro rate: 15-40%
- Passes sometimes, fails sometimes
- No obvious pattern

**Analysis:**
```bash
# Run with more attempts
# Update test_input.json:
{
  "runs": 50,
  "parallelism": 10
}

# Check for patterns
cat flaky_test_results.json | jq '.results[] | select(.passed == false) | .attempt'
```

**Common causes:**
1. **Timing issues**: `time.sleep()` vs `await` conditions
2. **Random data**: Non-deterministic test data
3. **External dependencies**: API calls, databases
4. **Race conditions**: Parallel execution issues
5. **Shared state**: Tests affecting each other

**Fixes:**
```python
# Bad: Time-based waiting
time.sleep(2)  # Hope it's done...

# Good: Condition-based waiting
for _ in range(50):
    if condition_met():
        break
    time.sleep(0.1)
else:
    raise TimeoutError("Condition not met")

# Bad: Random data without seed
import random
value = random.randint(1, 100)

# Good: Seeded random (use TEST_SEED env var)
import random
import os
seed = int(os.environ.get('TEST_SEED', '12345'))
random.seed(seed)
value = random.randint(1, 100)
```

### Scenario B: Consistent Failure (Real Bug)

**Symptoms:**
- Repro rate: 90-100%
- Always fails
- Clear error message

**Analysis:**
```bash
# Single run is enough
python3 local_test.py

# Check the error
cat flaky_test_results.json | jq '.results[0] | {exit_code, stdout, stderr}'
```

**Common causes:**
1. **Assertion errors**: Test expectations don't match reality
2. **Import errors**: Missing dependencies, wrong paths
3. **Type errors**: Wrong types passed to functions
4. **Logic errors**: Incorrect implementation

**Fix approach:**
1. Read the error message carefully
2. Check if test or code is wrong
3. Look at recent changes (git diff)
4. Fix the root cause
5. Verify locally before pushing

### Scenario C: Environment-Specific Failure

**Symptoms:**
- Fails in CI, passes locally (or vice versa)
- Different behavior on different machines
- Depends on Python version, OS, etc.

**Analysis:**
```bash
# Check environment differences
python --version
pip list

# Compare with CI environment
# (check .github/workflows/ci.yml for CI Python version)
```

**Common causes:**
1. **Different Python versions**: 3.11 vs 3.12 behavior
2. **Missing environment variables**: Needed in CI
3. **File paths**: Absolute vs relative paths
4. **PYTHONPATH**: Module import issues
5. **OS differences**: macOS vs Linux

**Fixes:**
```python
# Bad: Hardcoded paths
config_path = "/Users/me/project/config.yml"

# Good: Relative paths
import os
config_path = os.path.join(os.path.dirname(__file__), "config.yml")

# Bad: Assuming env var exists
api_key = os.environ["API_KEY"]

# Good: Provide defaults or skip
api_key = os.environ.get("API_KEY")
if not api_key:
    pytest.skip("API_KEY not set")
```

## AI-Assisted Analysis Tips

### What to Include in Your Prompt

1. **The error message**:
   ```
   AssertionError: assert 10 == 11
   ```

2. **The test code**:
   ```python
   def test_default_config(self):
       config = Config()
       assert config.get("runs") == 11
   ```

3. **Relevant implementation**:
   ```python
   DEFAULT_CONFIG = {
       "runs": 10,
       ...
   }
   ```

4. **Repro rate**:
   ```
   100% failure (10/10 runs)
   ```

5. **Recent changes** (if relevant):
   ```bash
   git log --oneline -5
   git diff HEAD~1
   ```

### Sample Prompts

**For assertion errors:**
```
I have a test that expects X but gets Y.
Test code: [paste code]
Implementation: [paste code]
Error: [paste error]

Is the test wrong or the implementation wrong?
What should the expected value be and why?
```

**For flaky tests:**
```
This test passes 60% of the time and fails 40%.
Test code: [paste code]
Error when it fails: [paste error]

What could cause intermittent failures?
How can I make this test deterministic?
```

**For import errors:**
```
Test fails with ModuleNotFoundError: No module named 'X'
The module exists in the project.
Directory structure: [paste tree output]
Test file location: [path]

Why can't it find the module?
How should I fix the imports or PYTHONPATH?
```

## Metrics and Benchmarks

**Time to resolution (with this workflow):**
- Detection: < 2 minutes (CI)
- Analysis: < 1 minute (flaky detector)
- Root cause: < 1 minute (AI analysis)
- Fix: 1-5 minutes (depending on complexity)
- Verify: < 4 minutes (CI)

**Total: 8-13 minutes** from failure to verified fix

**Traditional debugging:**
- Detection: < 2 minutes (CI)
- Reproduce locally: 5-15 minutes
- Investigation: 10-60 minutes
- Fix: 5-30 minutes
- Verify: < 4 minutes (CI)

**Total: 22-111 minutes** (median: ~45 minutes)

**Improvement: 70-85% faster** with automated analysis

## Troubleshooting

### Flaky Detector Won't Run

```bash
# Check if dependencies are installed
pip install -r requirements.txt

# Check if test_input.json is valid
cat test_input.json | jq .

# Run with verbose output
python3 local_test.py 2>&1 | tee debug.log
```

### Results File Missing

```bash
# Check if it was created
ls -la flaky_test_results.json

# Check write permissions
touch flaky_test_results.json
rm flaky_test_results.json
```

### AI Analysis Not Helpful

**Improve your prompt:**
- Include more context (related code, error traces)
- Ask specific questions
- Provide recent git changes if relevant
- Include environment details (Python version, OS)

## Best Practices

1. **Always run flaky detector first** before assuming it's a real bug
2. **Document the root cause** in commit messages
3. **Update tests when fixing** to prevent regression
4. **Use semantic commit messages** for better git history
5. **Verify locally before pushing** with `./scripts/run_all_checks.sh`

## See Also

- [PREVENTING_CI_FAILURES.md](PREVENTING_CI_FAILURES.md) - How to avoid failures
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Command cheat sheet
- [CICD_INTEGRATION.md](CICD_INTEGRATION.md) - Automated workflow setup
- [HISTORICAL_TRACKING.md](HISTORICAL_TRACKING.md) - Track flakiness trends
