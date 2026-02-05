# Test Input Files Guide

This project uses two input configuration files for testing the flaky test detector. This guide clarifies when to use each file.

## Files Overview

| File | Used By | Purpose |
|------|---------|---------|
| `test_input.json` | `local_test.py` | **Primary**: Local testing with moderate runs |
| `input.json` | Manual testing | **Alternative**: Higher run count for thorough testing |

## test_input.json (Recommended)

**Used by:** `local_test.py` script

**Purpose:** Standard local testing with balanced performance

**Default configuration:**
```json
{
  "repo": "https://github.com/runpod-Henrik/serverless_test",
  "test_command": "pytest tests/test_flaky.py",
  "runs": 50,
  "parallelism": 5
}
```

**When to use:**
- Running `python3 local_test.py`
- Quick validation (50 runs, ~30-60 seconds)
- Regular development workflow
- CI/CD testing

**Modify for your test:**
```json
{
  "repo": "https://github.com/your-org/your-repo",
  "test_command": "pytest path/to/failing_test.py::test_function -v",
  "runs": 20,
  "parallelism": 5
}
```

## input.json (Alternative)

**Used by:** Manual testing, custom scripts

**Purpose:** More thorough testing with higher run counts

**Default configuration:**
```json
{
  "repo": "https://github.com/runpod-Henrik/serverless_test",
  "test_command": "pytest tests/test_flaky.py",
  "runs": 100,
  "parallelism": 8
}
```

**When to use:**
- Deep flakiness investigation
- More confidence in results (100+ runs)
- When you have time for longer runs (~2-3 minutes)
- Testing highly intermittent bugs

## Local Path Support (New!)

Both files now support local repository paths for faster development:

```json
{
  "repo": "/Users/you/projects/your-repo",
  "test_command": "pytest tests/test_specific.py -v",
  "runs": 10,
  "parallelism": 3
}
```

**Benefits:**
- No need to commit/push for testing
- Faster iteration
- Test uncommitted changes
- No GitHub required

**Use cases:**
- Debugging locally
- Testing work-in-progress code
- Quick validation before commit

## Configuration Fields

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `repo` | string | Repository URL or local path | `"https://github.com/user/repo"` or `"/path/to/repo"` |
| `test_command` | string | Command to run the test | `"pytest tests/test_file.py -v"` |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `runs` | integer | 10 | Number of times to run the test (1-1000) |
| `parallelism` | integer | 4 | Number of parallel workers (1-50) |
| `framework` | string | auto-detect | Force framework: `"python"`, `"go"`, `"jest"`, etc. |

## Examples

### Example 1: Debug Failing CI Test

```json
{
  "repo": "https://github.com/your-org/your-repo",
  "test_command": "pytest tests/test_auth.py::test_login_flow -v",
  "runs": 20,
  "parallelism": 5
}
```

### Example 2: Local Development

```json
{
  "repo": "/Users/dev/projects/my-app",
  "test_command": "npm test -- tests/flaky.spec.js",
  "runs": 15,
  "parallelism": 3,
  "framework": "jest"
}
```

### Example 3: Thorough Investigation

```json
{
  "repo": "https://github.com/your-org/your-repo",
  "test_command": "go test -v ./pkg/service -run TestConcurrentAccess",
  "runs": 200,
  "parallelism": 10,
  "framework": "go"
}
```

## Quick Reference

### Run with test_input.json
```bash
python3 local_test.py
```

### Run with custom config
```bash
# Edit either file, then:
python3 local_test.py
```

### Check results
```bash
cat flaky_test_results.json | jq '.repro_rate'
```

## Best Practices

1. **Start with fewer runs** (10-20) for quick validation
2. **Increase runs** (50-100) if you see intermittent results
3. **Use local paths** during development for faster iteration
4. **Use GitHub URLs** for CI/CD integration
5. **Keep test commands specific** - target individual failing tests
6. **Match your framework** - use framework-specific test commands

## Troubleshooting

**Q: Which file should I edit?**
A: Edit `test_input.json` for standard use with `local_test.py`

**Q: Can I use both files?**
A: `local_test.py` only reads `test_input.json`. Use `input.json` for custom scripts.

**Q: Can I test without Git?**
A: Yes! Use a local path: `"repo": "/path/to/your/project"`

**Q: What if my test needs environment variables?**
A: Set them before running: `export API_KEY=test && python3 local_test.py`

**Q: How many runs do I need?**
A: Start with 10-20. If you see 0% or 100%, test is not flaky. If you see 10-90%, increase runs for confidence.

## See Also

- [Debugging Test Failures Guide](docs/DEBUGGING_TEST_FAILURES.md) - Complete workflow
- [Quick Reference](docs/QUICK_REFERENCE.md) - Command cheat sheet
- [CICD Integration](docs/CICD_INTEGRATION.md) - Automated testing
