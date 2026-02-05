# GitHub Actions Workflow Testing Guide

This guide explains how to test GitHub Actions workflows locally before pushing to GitHub.

---

## Overview

Testing GitHub Actions workflows is critical for:
- **Faster feedback**: Catch errors in seconds instead of minutes
- **No commit spam**: Test before pushing, avoid "fix CI" commits
- **Better coverage**: Test workflow logic with standard pytest
- **Cost savings**: Reduce GitHub Actions minutes usage

---

## Testing Methods

### 1. Unit Tests (Implemented ✅)

**What**: Test extracted Python scripts from workflows using pytest

**Location**:
- Scripts: `scripts/workflow_utils/test_summary_generator.py`
- Tests: `tests/workflows/test_summary_generator.py`

**Run tests**:
```bash
# Run all workflow tests
pytest tests/workflows/ -v

# Run specific test file
pytest tests/workflows/test_summary_generator.py -v

# Run without coverage warnings
pytest tests/workflows/ --no-cov -v
```

**What's tested**:
- ✅ JUnit XML parsing (test results)
- ✅ Coverage XML parsing
- ✅ Test summary generation
- ✅ Markdown formatting
- ✅ Commit message truncation
- ✅ Change detection logic
- ✅ CLI interface

**Example test**:
```python
def test_parse_test_results():
    """Test parsing JUnit XML test results."""
    xml_content = '''<?xml version="1.0"?>
    <testsuite tests="5" failures="1" errors="0" skipped="1">
      <testcase classname="TestConfig" name="test_default" time="0.5"/>
    </testsuite>'''

    result = parse_test_results(xml_file)

    assert result["tests"] == 5
    assert result["failures"] == 1
```

---

### 2. Workflow Validation (Implemented ✅)

**What**: Test workflow YAML structure and configuration

**Location**: `tests/workflows/test_workflow_validation.py`

**Run tests**:
```bash
pytest tests/workflows/test_workflow_validation.py -v
```

**What's tested**:
- ✅ Workflow triggers (push, PR, workflow_run)
- ✅ Job dependencies
- ✅ Python version requirements
- ✅ Required secrets
- ✅ Step outputs format
- ✅ Artifact generation

**Example test**:
```python
def test_ci_triggers_on_push_and_pr(ci_workflow):
    """Test CI workflow triggers on push and PR."""
    triggers = ci_workflow[True]  # 'on' key parsed as True
    assert "push" in triggers
    assert "pull_request" in triggers
    assert "main" in triggers["push"]["branches"]
```

---

### 3. Actionlint Validation (Implemented ✅)

**What**: Static analysis of workflow YAML files

**Configuration**: `.actionlintrc.yml`

**Run locally**:
```bash
# Install actionlint (macOS)
brew install actionlint

# Install actionlint (Linux)
bash <(curl https://raw.githubusercontent.com/rhysd/actionlint/main/scripts/install.sh)

# Validate all workflows
actionlint

# Validate specific workflow
actionlint .github/workflows/ci.yml

# Verbose output
actionlint -color -verbose
```

**What's checked**:
- ✅ YAML syntax errors
- ✅ Undefined step outputs
- ✅ Invalid action inputs
- ✅ Shell script issues (via shellcheck)
- ✅ Python script issues (via pyflakes)
- ✅ Security vulnerabilities
- ✅ Deprecated commands

**CI Integration**:
```yaml
- name: Validate GitHub Actions workflows
  uses: docker://rhysd/actionlint:latest
  with:
    args: -color -verbose
```

---

### 4. Local Workflow Execution with `act` (Optional)

**What**: Run entire workflows locally using Docker

**Installation**:
```bash
# macOS
brew install act

# Linux
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | bash
```

**Usage**:
```bash
# List available workflows
act --list

# Run CI workflow
act push

# Run specific job
act push -j lint-and-type-check
act push -j test

# Dry run (don't actually run)
act --dryrun

# Verbose mode
act -v

# Reuse containers for faster iteration
act --reuse-containers
```

**Limitations**:
- Requires Docker installed and running
- Some GitHub-specific features may not work
- Secrets are masked by default
- Not all actions are fully supported

---

## Testing Architecture

### Extracted Scripts

Python code embedded in workflows has been extracted to testable modules:

```
scripts/
└── workflow_utils/
    ├── __init__.py
    └── test_summary_generator.py  # 232 lines, extracted from ci.yml
```

**Benefits**:
- Unit testable with pytest
- Type hints and documentation
- Reusable across workflows
- CLI interface for debugging

**CLI Usage**:
```bash
# Generate test summary from results
python scripts/workflow_utils/test_summary_generator.py \
    --test-results test-results.xml \
    --coverage coverage.xml \
    --output summary.md

# View on stdout
python scripts/workflow_utils/test_summary_generator.py \
    --test-results test-results.xml
```

---

## Test Coverage

### Workflow Unit Tests: 28 tests

**test_summary_generator.py (15 tests)**:
- ✅ `test_parse_valid_results` - Parse JUnit XML with failures
- ✅ `test_parse_all_passing` - Parse JUnit XML all passing
- ✅ `test_parse_empty_attributes` - Handle missing XML attributes
- ✅ `test_parse_valid_coverage` - Parse coverage.xml
- ✅ `test_parse_perfect_coverage` - Handle 100% coverage
- ✅ `test_parse_missing_file` - Graceful handling of missing files
- ✅ `test_parse_invalid_xml` - Handle malformed XML
- ✅ `test_generate_summary_all_passing` - Generate passing summary
- ✅ `test_generate_summary_with_failures` - Generate failing summary
- ✅ `test_generate_summary_good_coverage` - Coverage status classification
- ✅ `test_generate_summary_with_changes` - Include change details
- ✅ `test_generate_summary_truncates_long_commits` - Message truncation
- ✅ `test_generate_summary_multiple_commits` - Handle many commits
- ✅ `test_main_with_valid_files` - CLI with valid inputs
- ✅ `test_main_missing_test_results` - CLI error handling

**test_workflow_validation.py (13 tests)**:
- ✅ `test_ci_workflow_name` - Workflow has correct name
- ✅ `test_ci_triggers_on_push_and_pr` - Correct triggers
- ✅ `test_ci_has_lint_and_test_jobs` - Required jobs exist
- ✅ `test_ci_test_needs_lint` - Job dependencies
- ✅ `test_ci_uses_python_312` - Python version requirement
- ✅ `test_flaky_detector_triggers_on_workflow_run` - Workflow trigger
- ✅ `test_flaky_detector_only_runs_on_failure` - Conditional execution
- ✅ `test_flaky_detector_has_required_secrets` - Secret validation
- ✅ `test_junit_xml_format_valid` - JUnit XML generation
- ✅ `test_coverage_xml_format_valid` - Coverage XML generation
- ✅ `test_github_output_format` - GITHUB_OUTPUT format
- ✅ `test_pr_number_extraction_safety` - Handle missing PRs
- ✅ `test_exit_code_capture` - Exit code handling

---

## Running Tests

### Locally

```bash
# All tests including workflows
pytest tests/ -v

# Just workflow tests
pytest tests/workflows/ -v

# With coverage (for workflow utils)
pytest tests/workflows/ --cov=scripts/workflow_utils --cov-report=term-missing

# Fast (no coverage overhead)
pytest tests/workflows/ --no-cov

# Single test
pytest tests/workflows/test_summary_generator.py::TestParseCoverage::test_parse_valid_coverage -v
```

### In CI

Workflow tests run automatically in GitHub Actions:

```yaml
- name: Run tests with coverage
  env:
    PYTHONPATH: ${{ github.workspace }}
  run: |
    pytest tests/ -v --cov=worker --cov=config --cov=database
```

**Note**: Workflow tests (`tests/workflows/`) are included in the standard test run.

---

## Development Workflow

### 1. Modify Workflow
```bash
# Edit workflow file
vim .github/workflows/ci.yml
```

### 2. Validate Syntax
```bash
# Run actionlint
actionlint .github/workflows/ci.yml
```

### 3. Test Locally
```bash
# Run workflow tests
pytest tests/workflows/ -v

# If modified Python script, update test_summary_generator.py
vim scripts/workflow_utils/test_summary_generator.py

# Run unit tests
pytest tests/workflows/test_summary_generator.py -v
```

### 4. (Optional) Test with act
```bash
# Run full workflow locally
act push -j lint-and-type-check
```

### 5. Commit and Push
```bash
git add .github/workflows/ci.yml
git commit -m "Update CI workflow"
git push
```

---

## Common Issues

### Issue: YAML `on` Key Error

**Problem**: PyYAML parses `on` as boolean `True`

**Solution**: Access using `workflow[True]` instead of `workflow["on"]`

```python
# ❌ Wrong
triggers = workflow["on"]

# ✅ Correct
triggers = workflow[True]  # YAML 'on' keyword
```

### Issue: Coverage Test Fails

**Problem**: `pytest` not in PATH during test

**Solution**: Test uses fallback to `python -m pytest`

```python
# Test automatically handles this
pytest_exe = shutil.which("pytest") or sys.executable
pytest_args = ["-m", "pytest"] if pytest_exe == sys.executable else []
```

### Issue: Test Results XML Format

**Problem**: Root can be `<testsuites>` or `<testsuite>`

**Solution**: Test checks for both

```python
assert root.tag in ("testsuite", "testsuites")
```

---

## Best Practices

### 1. Extract Large Python Scripts

**❌ Don't**: Keep 200+ line Python scripts embedded in YAML

**✅ Do**: Extract to `scripts/workflow_utils/` and import

```yaml
# Before (embedded)
- name: Generate summary
  run: |
    python << 'EOF'
    # 200 lines of Python...
    EOF

# After (extracted)
- name: Generate summary
  run: |
    python scripts/workflow_utils/test_summary_generator.py \
      --test-results test-results.xml \
      --coverage coverage.xml \
      --output $GITHUB_STEP_SUMMARY
```

### 2. Test Workflow Changes

Always test workflow changes before pushing:
```bash
actionlint .github/workflows/*.yml && pytest tests/workflows/ -v
```

### 3. Use Type Hints

Add type hints to extracted scripts:
```python
def parse_test_results(test_results_file: str) -> dict[str, int | float]:
    """Parse JUnit XML test results."""
    # ...
```

### 4. Document Extracted Scripts

Add docstrings and CLI help:
```python
def main() -> int:
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="Generate test summary from results"
    )
    # ...
```

### 5. Test Edge Cases

Test failure scenarios, not just happy paths:
```python
def test_parse_missing_file():
    """Test parsing non-existent coverage file."""
    coverage = parse_coverage("nonexistent.xml")
    assert coverage == 0.0  # Graceful fallback
```

---

## Resources

- [act - Run GitHub Actions locally](https://github.com/nektos/act)
- [actionlint - Workflow linter](https://github.com/rhysd/actionlint)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Testing Python Code](https://docs.pytest.org/en/stable/)
- [PyYAML Documentation](https://pyyaml.org/wiki/PyYAMLDocumentation)

---

## Summary

| Method | Speed | Coverage | Setup | Best For |
|--------|-------|----------|-------|----------|
| **Unit Tests** | ⚡ Fast (0.5s) | High | None | Workflow Python logic |
| **Actionlint** | ⚡ Fast (1s) | Syntax | Install tool | YAML validation |
| **Workflow Validation** | ⚡ Fast (0.5s) | Structure | None | Workflow config |
| **act** | 🐢 Slow (20s+) | Full | Docker | End-to-end testing |

**Recommendation**: Use unit tests + actionlint for fast, comprehensive validation. Use `act` only when testing full workflow integration.

---

**Last Updated**: 2026-02-05
**Test Coverage**: 28 workflow tests, all passing ✅
