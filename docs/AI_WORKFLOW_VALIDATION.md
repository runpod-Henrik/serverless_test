# Workflow Validation with Optional AI

Automatically catch and fix GitHub Actions workflow issues with optional AI-powered suggestions.

## Overview

This project includes automated validation for GitHub Actions workflows with optional AI-powered fix suggestions:

- **Pre-commit hooks** - Catch issues before committing (no API key required)
- **Local validation script** - Validate workflows locally
- **CI validation** - Automatic validation on all PRs
- **AI fix suggestions** *(Optional)* - Claude API suggests fixes when `ANTHROPIC_API_KEY` is configured

**Note:** The validation system works fully without an API key. AI suggestions are an optional enhancement that requires setting up `ANTHROPIC_API_KEY`.

## Quick Start

### 1. Install Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install the hooks
pre-commit install

# Test it
pre-commit run --all-files
```

Now workflow files will be automatically validated before every commit!

### 2. Local Validation

```bash
# Validate all workflows (no API key required)
python scripts/workflow_utils/validate_and_fix.py

# Validate specific workflow
python scripts/workflow_utils/validate_and_fix.py .github/workflows/ci.yml
```

### 3. (Optional) Enable AI Suggestions

To get AI-powered fix suggestions, set up your Anthropic API key:

**For Local Development:**
```bash
export ANTHROPIC_API_KEY="your-api-key"
python scripts/workflow_utils/validate_and_fix.py --ai-suggest
```

**For CI/CD:**
Add `ANTHROPIC_API_KEY` as a repository secret:
1. Go to Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `ANTHROPIC_API_KEY`
4. Value: Your Anthropic API key
5. Click "Add secret"

### 4. CI Validation (Automatic)

When you create a PR that modifies workflow files, the `Workflow Validator` job will:

1. ✅ Run actionlint to validate all workflows
2. 🤖 Generate AI fix suggestions if `ANTHROPIC_API_KEY` is configured *(optional)*
3. 💬 Post results as a PR comment
4. 📊 Create a detailed summary in the job output

## Features

### actionlint Integration

Validates workflows for:

- **YAML syntax errors** - Invalid YAML structure
- **Undefined outputs** - Using step outputs that don't exist
- **Invalid action inputs** - Wrong parameters for actions
- **Shell script issues** - Detected by shellcheck
- **Python script issues** - Detected by pyflakes
- **Type mismatches** - String vs number in API calls
- **Security issues** - Potentially dangerous patterns
- **Deprecated syntax** - Old GitHub Actions features

### AI-Powered Fix Suggestions

When validation fails, Claude API analyzes errors and suggests:

1. **What the issue is** - Clear explanation of the problem
2. **How to fix it** - Step-by-step fix instructions
3. **Corrected code** - Working code snippets you can copy

### Pre-commit Hooks

The pre-commit configuration includes:

- ✅ Ruff linting and formatting
- ✅ GitHub Actions validation (actionlint)
- ✅ YAML/JSON/TOML syntax checking
- ✅ Trailing whitespace removal
- ✅ Large file detection
- ✅ Security scanning (bandit)

## Common Issues Caught

### 1. Unquoted Variables in Shell Scripts

**Error:**
```
SC2086: Double quote to prevent globbing and word splitting
```

**Fix:**
```bash
# ❌ Wrong
git diff --name-only $LAST_SHA HEAD

# ✅ Correct
git diff --name-only "$LAST_SHA" HEAD
```

### 2. Wrong API Parameter Types

**Error:**
```
Type mismatch: run_id expects number but got string
```

**Fix:**
```javascript
// ❌ Wrong
run_id: ${{ steps.last-success.outputs.run_number }}

// ✅ Correct
const runId = parseInt('${{ steps.last-success.outputs.run_id }}', 10);
```

### 3. Incorrect Exit Code Capture

**Error:**
```
Exit code captured from wrong command
```

**Fix:**
```bash
# ❌ Wrong
ruff check . > output.txt 2>&1
echo "exit_code=$?" >> $GITHUB_OUTPUT  # Captures echo's exit code!

# ✅ Correct
set +e
ruff check . > output.txt 2>&1
RESULT=$?
set -e
echo "exit_code=$RESULT" >> $GITHUB_OUTPUT
```

### 4. Missing File Checks

**Error:**
```
cat: file.txt: No such file or directory
```

**Fix:**
```bash
# ❌ Wrong
cat error-log.txt

# ✅ Correct
if [ -f error-log.txt ]; then
  cat error-log.txt
fi
```

### 5. NoneType Errors in Python

**Error:**
```
TypeError: 'NoneType' object is not subscriptable
```

**Fix:**
```python
# ❌ Wrong
result = job.output()
rate = result['repro_rate']  # Crashes if result is None

# ✅ Correct
result = job.output()
if result is None:
    print("Job failed")
    exit(1)
rate = result['repro_rate']
```

## Usage Examples

### Local Validation

```bash
# Basic validation
python scripts/workflow_utils/validate_and_fix.py

# With AI suggestions
python scripts/workflow_utils/validate_and_fix.py --ai-suggest

# JSON output for scripting
python scripts/workflow_utils/validate_and_fix.py --json

# Fail CI builds on errors
python scripts/workflow_utils/validate_and_fix.py --fail-on-error
```

### Pre-commit Hooks

```bash
# Run on staged files only
pre-commit run

# Run on all files
pre-commit run --all-files

# Run specific hook
pre-commit run actionlint

# Update hook versions
pre-commit autoupdate

# Skip hooks (not recommended)
git commit --no-verify
```

### CI Integration

The workflow validator runs automatically on:

- All PRs that modify `.github/workflows/**`
- Direct pushes to main that modify workflows

**To add ANTHROPIC_API_KEY for AI suggestions:**

1. Go to repository Settings → Secrets → Actions
2. Click "New repository secret"
3. Name: `ANTHROPIC_API_KEY`
4. Value: Your Claude API key from console.anthropic.com
5. Save

## Configuration

### Pre-commit Hook Configuration

Edit `.pre-commit-config.yaml` to customize:

```yaml
repos:
  - repo: https://github.com/rhysd/actionlint
    rev: v1.7.4
    hooks:
      - id: actionlint
        # Add custom args
        args: [-ignore, 'SC2086:*']
```

### actionlint Configuration

Edit `.actionlintrc.yml` to customize shellcheck/pyflakes rules:

```yaml
self-hosted-runner:
  labels:
    - ubuntu-latest
    - my-custom-runner

shellcheck:
  exclude-rules:
    - SC2086  # Ignore unquoted variables
```

## Troubleshooting

### "actionlint not found"

**Solution:**
```bash
# macOS
brew install actionlint

# Linux
bash <(curl https://raw.githubusercontent.com/rhysd/actionlint/main/scripts/install.sh)
```

### "anthropic package not installed"

**Solution:**
```bash
pip install anthropic
```

### "ANTHROPIC_API_KEY not set"

**Solution:**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."

# Or add to .bashrc/.zshrc
echo 'export ANTHROPIC_API_KEY="sk-ant-..."' >> ~/.bashrc
```

### Pre-commit hooks not running

**Solution:**
```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install

# Check status
pre-commit run --all-files
```

## Best Practices

### 1. Run Validation Before Pushing

```bash
# Quick check
pre-commit run --all-files

# Or with AI suggestions for detailed fixes
python scripts/workflow_utils/validate_and_fix.py --ai-suggest
```

### 2. Keep actionlint Updated

```bash
# Update pre-commit hooks
pre-commit autoupdate

# Or update actionlint directly
brew upgrade actionlint  # macOS
```

### 3. Use AI Suggestions Wisely

- ✅ **Do** review AI suggestions before applying
- ✅ **Do** test changes locally before pushing
- ✅ **Do** understand the fix, don't blindly copy
- ❌ **Don't** trust AI suggestions for security-critical code
- ❌ **Don't** skip testing after applying fixes

### 4. Commit Small Workflow Changes

- Make incremental changes to workflows
- Run validation after each change
- Easier to debug when validation fails

## Performance

- **Pre-commit validation**: ~1-2 seconds per workflow
- **Local AI suggestions**: ~5-10 seconds (depends on file size)
- **CI validation**: ~30-60 seconds (includes setup)
- **AI PR comments**: ~10-15 seconds (after validation)

## Examples

### Example: Fix shellcheck error

```bash
$ python scripts/workflow_utils/validate_and_fix.py --ai-suggest

Running actionlint...
Found 1 error(s):

📄 .github/workflows/ci.yml (1 error(s)):
  Line 255, Col 24: shellcheck reported issue: SC2086:info:2:24: Double quote to prevent globbing
    Rule: shellcheck

🤖 Requesting AI-powered fix suggestions...

================================================================================
AI-SUGGESTED FIXES
================================================================================

## Issue: Unquoted Variable Expansion

The variable $LAST_SHA is used without quotes, which can cause word splitting
and globbing issues if the value contains spaces or special characters.

### Fix:

Quote the variable to prevent these issues:

```bash
# Before
if ! git cat-file -e $LAST_SHA^{commit} 2>/dev/null; then

# After
if ! git cat-file -e "$LAST_SHA^{commit}" 2>/dev/null; then
```

Apply this same fix to all uses of $LAST_SHA in the script.
================================================================================
```

## Summary

This automated validation system helps you:

- ✅ Catch workflow errors before they reach CI
- ✅ Get AI-powered suggestions for fixes
- ✅ Learn from mistakes with detailed explanations
- ✅ Maintain high-quality workflow files
- ✅ Reduce debugging time in CI

**Next Steps:**
1. Install pre-commit hooks: `pre-commit install`
2. Set up ANTHROPIC_API_KEY for AI suggestions
3. Run validation on existing workflows
4. Fix any issues found
5. Enjoy automated validation on every commit!

---

**Resources:**
- [actionlint documentation](https://github.com/rhysd/actionlint)
- [pre-commit documentation](https://pre-commit.com/)
- [Claude API documentation](https://docs.anthropic.com/)
