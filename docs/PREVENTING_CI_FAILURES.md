# Preventing CI Failures - Developer Guide

This guide documents common CI failure patterns and how to prevent them before pushing code.

## Quick Start: Run All Checks Locally

Before pushing any changes, run the comprehensive test script:

```bash
./scripts/run_all_checks.sh
```

This runs the same checks that CI runs, catching issues before they reach the remote.

## The Multi-Layer Defense System

We use a multi-layer approach to catch issues:

```
1. IDE/Editor → Real-time linting (LSP, linters)
2. Pre-commit hooks → Automatic checks on git commit
3. Local test script → Manual comprehensive check before push
4. CI pipeline → Final verification on push/PR
```

**Goal:** Catch issues at layer 1-3, so CI always passes.

## Common Failure Patterns

### 1. Variable Shadowing (Caught by Pylint)

**What happened:**
- Variable `time` was used for both test duration and commit timestamp
- Later assignment overwrote earlier value, causing type errors
- Took multiple CI runs to identify and fix

**Example:**
```python
# ❌ Bad: Variable shadowing
time = float(testsuite.attrib.get('time', '0'))  # float
# ... 100 lines later ...
time = parts[3]  # Now it's a string! Overwrites the float

# ✅ Good: Unique names
test_time = float(testsuite.attrib.get('time', '0'))
commit_time = parts[3]
```

**Prevention:**
- Pylint with W0621 (redefined-outer-name) enabled catches this
- Use descriptive variable names instead of generic ones
- Keep functions small so shadowing is obvious

### 2. Shell Variable Quoting (Caught by Shellcheck)

**What happened:**
- 47 instances of unquoted variables in GitHub Actions workflows
- Could cause word splitting and globbing issues
- Required manual fix across entire workflow file

**Example:**
```bash
# ❌ Bad: Unquoted variables
git diff --name-only $LAST_SHA HEAD
if ! git cat-file -e $SHA^{commit}; then

# ✅ Good: Quoted variables
git diff --name-only "$LAST_SHA" HEAD
if ! git cat-file -e "$SHA^{commit}"; then
```

**Prevention:**
- Pre-commit actionlint hook catches this automatically
- Always quote shell variables unless you specifically need word splitting
- Use shellcheck locally: `shellcheck -x .github/workflows/*.yml`

### 3. Exit Code Capture Issues (Shell Logic)

**What happened:**
- Tried to capture exit code but got exit code of `echo` command instead
- Caused false success reports

**Example:**
```bash
# ❌ Bad: Captures echo's exit code
ruff format --check . > output.txt 2>&1
echo "exit_code=$?" >> $GITHUB_OUTPUT  # Always 0!

# ✅ Good: Capture immediately
set +e
ruff format --check . > output.txt 2>&1
RESULT=$?
set -e
echo "exit_code=$RESULT" >> $GITHUB_OUTPUT
```

**Prevention:**
- Use `set +e` / `set -e` pattern for commands that may fail
- Capture exit code to variable immediately after command
- Test locally with `bash -x script.sh` to see execution flow

### 4. XML Parsing Element Selection (Logic Bug)

**What happened:**
- Parsed wrong XML element (`<testsuites>` vs `<testsuite>`)
- Caused type errors when trying to parse attributes

**Example:**
```python
# ❌ Bad: Wrong element
root = ET.fromstring(content)
time = float(root.attrib.get('time', '0'))  # Wrong element!

# ✅ Good: Correct element
root = ET.fromstring(content)
testsuite = root.find('testsuite')
if testsuite is None:
    testsuite = root  # Fallback for single suite
time = float(testsuite.attrib.get('time', '0'))
```

**Prevention:**
- Write unit tests for parsing logic
- Test with actual XML samples
- Add debug logging during development
- Use type hints to catch attribute access errors

### 5. Type Conversion Without Validation

**What happened:**
- Tried to convert string attributes to float without checking format
- Caused ValueError when attribute contained human-readable text

**Example:**
```python
# ❌ Bad: No validation
time = float(testsuite.attrib.get('time'))  # May be "16 minutes ago"!

# ✅ Good: Validation and fallback
time_str = testsuite.attrib.get('time', '0')
try:
    time = float(time_str)
except ValueError:
    print(f"Warning: Could not parse time '{time_str}'")
    time = 0.0
```

**Prevention:**
- Mypy type checking catches missing error handling
- Add try-except for all type conversions of external data
- Validate data format before conversion
- Test with malformed input

## The Complete Pre-Push Checklist

Before pushing code, ensure:

- [ ] **Run local test script**: `./scripts/run_all_checks.sh`
- [ ] **Pre-commit hooks installed**: `pre-commit install`
- [ ] **All tests pass**: `pytest --cov=.`
- [ ] **No linting errors**: `ruff check .`
- [ ] **No type errors**: `mypy scripts/ tests/`
- [ ] **No variable shadowing**: `pylint scripts/ tests/`
- [ ] **Workflows validate**: `actionlint`
- [ ] **Manual testing**: Test the actual feature/fix

## Tool-Specific Prevention

### Ruff (Fast Linting)
```bash
# Check for issues
ruff check .

# Auto-fix issues
ruff check . --fix

# Check formatting
ruff format --check .

# Apply formatting
ruff format .
```

### Pylint (Deep Code Analysis)
```bash
# Check all Python files
pylint scripts/ tests/

# Check specific file
pylint scripts/workflow_utils/validate_and_fix.py

# Show only errors (no warnings)
pylint scripts/ tests/ --errors-only
```

### Mypy (Type Checking)
```bash
# Check all Python files
mypy scripts/ tests/ --ignore-missing-imports

# Check specific file
mypy scripts/workflow_utils/validate_and_fix.py

# Strict mode (catches more issues)
mypy scripts/ tests/ --strict --ignore-missing-imports
```

### Actionlint (Workflow Validation)
```bash
# Check all workflows
actionlint

# With style warning suppression
actionlint -ignore 'SC2129:.*' -ignore 'SC2126:.*'

# Verbose output
actionlint -color -verbose

# With AI suggestions (requires ANTHROPIC_API_KEY)
python scripts/workflow_utils/validate_and_fix.py --ai-suggest
```

### Pytest (Testing)
```bash
# Run all tests
pytest

# With coverage
pytest --cov=. --cov-report=term-missing

# Specific test file
pytest tests/test_flaky.py

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

## IDE Integration

### VS Code

Install extensions:
- Python (microsoft.python)
- Pylint (ms-python.pylint)
- Ruff (charliermarsh.ruff)
- actionlint (toba)

Settings (`.vscode/settings.json`):
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "ruff",
  "editor.formatOnSave": true,
  "python.analysis.typeCheckingMode": "basic"
}
```

### PyCharm

1. Enable inspections:
   - Settings → Editor → Inspections
   - Enable "Shadowing names from outer scopes"
   - Enable "Type checker" inspections

2. Configure external tools:
   - Settings → Tools → External Tools
   - Add actionlint, ruff, pylint as external tools

3. Enable pre-commit:
   - Settings → Version Control → Commit
   - Enable "Run pre-commit hooks"

## Debugging CI Failures

When CI fails despite passing locally:

### 1. Check exact CI environment
```bash
# See what CI is running
gh run view <run-id> --log

# Download artifacts
gh run download <run-id>
```

### 2. Reproduce locally
```bash
# Use same Python version as CI
pyenv install 3.12.0
pyenv local 3.12.0

# Run in fresh environment
python -m venv .venv-test
source .venv-test/bin/activate
pip install -r requirements.txt
./scripts/run_all_checks.sh
```

### 3. Check for environment-specific issues
- File paths (Windows vs Unix)
- Line endings (CRLF vs LF)
- Environment variables
- Dependency versions

## Maintenance

### Update Pre-commit Hooks
```bash
# Update to latest versions
pre-commit autoupdate

# Test updated hooks
pre-commit run --all-files
```

### Update Actionlint
```bash
# macOS
brew upgrade actionlint

# Linux
bash <(curl https://raw.githubusercontent.com/rhysd/actionlint/main/scripts/install.sh)
```

### Update Python Dependencies
```bash
# Update all dependencies
pip install --upgrade pip
pip install --upgrade -r requirements.txt

# Check for outdated packages
pip list --outdated
```

## Cost of Failure

Understanding why prevention matters:

| Stage | Time to Fix | Context Switch Cost | Total Cost |
|-------|-------------|---------------------|------------|
| IDE | 10 seconds | None (immediate) | ~10s |
| Pre-commit | 1 minute | Minimal (still coding) | ~2m |
| Local test | 2 minutes | Low (before push) | ~5m |
| **CI failure** | **5-15 minutes** | **High (context switch)** | **20-60m** |

**A CI failure costs 10-100x more than catching the issue locally!**

## Success Metrics

Track your prevention success:

```bash
# Count CI runs per push
git log --oneline | wc -l  # Number of commits
gh run list --limit 1000 | wc -l  # Number of CI runs

# Goal: ~1.0 CI runs per commit (first run passes)
```

## Summary

**The Golden Rule:** If CI caught it, add a check to catch it earlier next time.

**Prevention Priority:**
1. ✅ Run `./scripts/run_all_checks.sh` before every push
2. ✅ Keep pre-commit hooks installed and updated
3. ✅ Enable IDE linting and type checking
4. ✅ Write tests for new functionality
5. ✅ Review this guide when adding new code patterns

**Remember:**
- Pre-commit hooks are your first line of defense
- Local test script should match CI exactly
- When in doubt, test it locally first
- Every CI failure is a learning opportunity to improve prevention

---

**Quick Reference:**
- Local test script: `./scripts/run_all_checks.sh`
- Pre-commit install: `pre-commit install`
- Update hooks: `pre-commit autoupdate`
- Workflow validation: `actionlint`
- AI suggestions: `python scripts/workflow_utils/validate_and_fix.py --ai-suggest`
