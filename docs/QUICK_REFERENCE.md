# Developer Quick Reference Card

## Before Every Push

```bash
./scripts/run_all_checks.sh
```

This runs everything CI runs. If it passes locally, CI will pass.

## Common Commands

### Quick Checks
```bash
ruff check .                    # Fast linting
ruff format --check .           # Check formatting
pytest                          # Run tests
```

### Comprehensive Checks
```bash
./scripts/run_all_checks.sh           # All checks (30-60s)
python scripts/validate_flaky_detector.py  # End-to-end system validation
pre-commit run --all-files            # Pre-commit hooks
```

### Specific Tools
```bash
pylint scripts/ tests/          # Deep code analysis
mypy scripts/ tests/            # Type checking
actionlint                      # Workflow validation
bandit -r scripts/ tests/       # Security scan
```

## Setup (One Time)

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Install all dev tools
pip install -e ".[dev]"
```

## Common Issues

### Variable Shadowing
```python
# ❌ Bad
time = float(x)
time = str(y)  # Overwrites!

# ✅ Good
test_time = float(x)
commit_time = str(y)
```

### Shell Quoting
```bash
# ❌ Bad
git diff $SHA

# ✅ Good
git diff "$SHA"
```

### Exit Code Capture
```bash
# ❌ Bad
command
echo "exit=$?" >> $GITHUB_OUTPUT

# ✅ Good
set +e
command
RESULT=$?
set -e
echo "exit=$RESULT" >> $GITHUB_OUTPUT
```

### Type Conversion
```python
# ❌ Bad
x = float(value)

# ✅ Good
try:
    x = float(value)
except ValueError:
    x = 0.0
```

## When CI Fails

### Quick Workflow
```bash
# 1. Check what failed
gh run view --log-failed

# 2. Is it flaky or a real bug?
# Edit test_input.json with failing test
python3 local_test.py

# 3. Analyze the results
cat flaky_test_results.json

# 4. Fix and verify
./scripts/run_all_checks.sh
git commit && git push
```

### Detailed Workflow
1. Check the CI logs: `gh run view --log-failed`
2. Run flaky detector to check reproducibility
3. Use AI to analyze root cause
4. Fix the issue
5. Verify locally: `./scripts/run_all_checks.sh`
6. Push and verify CI passes

**See:** [Debugging Test Failures Guide](DEBUGGING_TEST_FAILURES.md)

## Tool Documentation

- **Preventing Failures:** `docs/PREVENTING_CI_FAILURES.md`
- **Debugging Test Failures:** `docs/DEBUGGING_TEST_FAILURES.md`
- **Quality Checks:** `docs/QUALITY_CHECKS.md`
- **Architecture:** `docs/ARCHITECTURE.md`

## Emergency: Skip Hooks

```bash
git commit --no-verify    # Skip pre-commit (not recommended)
```

**Warning:** Only use this if hooks are broken. Fix hooks instead!

## Update Tools

```bash
pre-commit autoupdate     # Update hook versions
pip install --upgrade -r requirements.txt
```

## Success Checklist

Before pushing:
- [ ] `./scripts/run_all_checks.sh` passes
- [ ] All tests pass
- [ ] No linting errors
- [ ] Changes tested manually
- [ ] Documentation updated if needed

## Need Help?

- CI failures: See `docs/PREVENTING_CI_FAILURES.md`
- Code quality: See `docs/QUALITY_CHECKS.md`
- Team discussion: Ask in team chat

---

**Remember:** CI passes on first try = Happy developer 😊
