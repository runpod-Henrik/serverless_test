# Code Quality Checks

This project now includes comprehensive code quality checks with linting, type checking, and coverage requirements.

## Tools Configured

### 1. Ruff (Linting & Formatting)

**Fast Python linter** that replaces flake8, isort, pyupgrade, and more.

**Configuration:** `pyproject.toml`

**Enabled checks:**
- `E`, `W` - pycodestyle (PEP 8 style)
- `F` - Pyflakes (logical errors)
- `I` - isort (import sorting)
- `N` - pep8-naming (naming conventions)
- `UP` - pyupgrade (Python version upgrades)
- `B` - flake8-bugbear (common bugs)
- `C4` - flake8-comprehensions (comprehension improvements)
- `SIM` - flake8-simplify (simplification suggestions)

**Run locally:**
```bash
# Check for linting issues
ruff check .

# Auto-fix issues
ruff check . --fix

# Check formatting
ruff format --check .

# Auto-format code
ruff format .
```

**Exclusions:**
- `dashboard.py` - UI code with different conventions
- `scripts/` - Integration scripts
- `local_test.py` - Local testing script
- `tests/*` - Test files allow some flexibility

### 2. Mypy (Type Checking)

**Static type checker** for Python that ensures type safety.

**Configuration:** `pyproject.toml`

**Strict settings enabled:**
- `disallow_untyped_defs` - All functions must have type hints
- `warn_return_any` - Warn on returning `Any`
- `no_implicit_optional` - Explicit `Optional` required
- `warn_redundant_casts` - Catch unnecessary type casts
- `strict_equality` - Strict type checking in comparisons

**Run locally:**
```bash
# Type check main modules
mypy worker.py config.py database.py

# Type check all Python files
mypy .
```

**Type hints added to:**
- ✅ `worker.py` - Main serverless handler
- ✅ `config.py` - Configuration management
- ✅ `database.py` - Historical tracking database

### 3. Coverage (Test Coverage)

**Measures test coverage** and enforces minimum thresholds.

**Configuration:** `pyproject.toml`

**Requirements:**
- **Minimum coverage:** 90%
- **Current coverage:** 96% across all main modules

**Run locally:**
```bash
# Run tests with coverage
pytest tests/ --cov=. --cov-report=term-missing

# Generate HTML coverage report
pytest tests/ --cov=. --cov-report=html
# Open: htmlcov/index.html

# Check if coverage meets minimum
pytest tests/ --cov-fail-under=90
```

**Coverage by module:**
- `worker.py`: 91%
- `config.py`: 98%
- `database.py`: 100%

**Excluded from coverage:**
- Test files (`tests/*`)
- UI code (`dashboard.py`)
- Integration scripts (`scripts/*`)
- Virtual environments

### 4. Pytest Configuration

**Test runner configuration** with coverage integration.

**Features:**
- Verbose output (`-v`)
- Strict marker checking
- Short tracebacks (`--tb=short`)
- Automatic coverage reporting
- HTML and XML coverage reports
- Minimum 90% coverage enforced

## GitHub Actions CI/CD

The CI workflow now includes **two stages**:

### Stage 1: Lint and Type Check
Runs first to catch style and type errors before testing.

**Steps:**
1. Run ruff linter (`ruff check`)
2. Check code formatting (`ruff format --check`)
3. Run mypy type checking

**Fails if:**
- Linting errors found
- Code not properly formatted
- Type checking errors found

### Stage 2: Test Suite
Runs after lint/type checks pass.

**Steps:**
1. Run full test suite with coverage
2. Generate coverage reports (term, XML, HTML)
3. Upload coverage artifacts
4. Post coverage comment on PRs

**Fails if:**
- Any test fails
- Coverage drops below 90%

## Local Development Workflow

### Before Committing

```bash
# 1. Format code
ruff format .

# 2. Fix linting issues
ruff check . --fix

# 3. Check types
mypy worker.py config.py database.py

# 4. Run tests with coverage
pytest tests/ --cov=. --cov-fail-under=90

# 5. Verify all checks pass
ruff check . && mypy worker.py config.py database.py && pytest tests/
```

### Pre-commit Hook (Optional)

Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
set -e

echo "Running code quality checks..."

# Format check
echo "  Checking formatting..."
ruff format --check . || {
    echo "❌ Code not formatted. Run: ruff format ."
    exit 1
}

# Lint check
echo "  Checking linting..."
ruff check . || {
    echo "❌ Linting errors. Run: ruff check . --fix"
    exit 1
}

# Type check
echo "  Checking types..."
mypy worker.py config.py database.py || {
    echo "❌ Type errors found"
    exit 1
}

# Tests
echo "  Running tests..."
pytest tests/ --cov=. --cov-fail-under=90 -q || {
    echo "❌ Tests failed or coverage too low"
    exit 1
}

echo "✅ All checks passed!"
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

## CI Workflow File

Location: `.github/workflows/ci.yml`

**Triggers:**
- Push to `main` branch
- Pull requests to `main`

**Jobs:**
1. **lint-and-type-check** - Runs linting and type checking
2. **test** - Runs test suite with coverage (depends on lint job)

**Artifacts:**
- Coverage reports (HTML, XML)
- Test results (on failure)

**PR Comments:**
- Automatic coverage status comments
- Shows coverage percentage and changes

## Dependencies Added

```txt
# Linting and formatting
ruff>=0.1.0

# Type checking
mypy>=1.8.0
types-PyYAML>=6.0.0
types-requests>=2.31.0

# Coverage
coverage>=7.4.0
pytest-cov>=4.1.0
```

## Benefits

### Code Quality
- ✅ Consistent code style across the project
- ✅ Type safety prevents common bugs
- ✅ High test coverage ensures reliability
- ✅ Automated checks catch issues early

### Developer Experience
- ✅ Fast linting with ruff (10-100x faster than flake8)
- ✅ Auto-fixing for common issues
- ✅ IDE integration (VS Code, PyCharm)
- ✅ Clear error messages

### CI/CD
- ✅ Automated quality gates
- ✅ Prevents bad code from merging
- ✅ Coverage tracking over time
- ✅ Faster feedback on PRs

## IDE Integration

### VS Code

Add to `.vscode/settings.json`:
```json
{
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": true,
      "source.organizeImports": true
    }
  },
  "mypy.runUsingActiveInterpreter": true
}
```

Install extensions:
- Ruff (charliermarsh.ruff)
- Mypy (ms-python.mypy-type-checker)

### PyCharm

1. **Ruff:**
   - Settings → Tools → External Tools
   - Add ruff check and ruff format

2. **Mypy:**
   - Settings → Tools → External Tools
   - Add mypy runner

3. **Coverage:**
   - Run → Edit Configurations → Python tests → pytest
   - Enable "Run with coverage"

## Troubleshooting

### Ruff errors after update
```bash
# Clear cache and re-run
rm -rf .ruff_cache
ruff check . --fix
```

### Mypy errors with imports
```bash
# Install type stubs
pip install types-<package-name>

# Or ignore the module
# Add to pyproject.toml:
[[tool.mypy.overrides]]
module = "package_name.*"
ignore_missing_imports = true
```

### Coverage too low
```bash
# See what's not covered
pytest tests/ --cov=. --cov-report=term-missing

# View detailed HTML report
pytest tests/ --cov=. --cov-report=html
open htmlcov/index.html
```

### GitHub Actions import errors

**Error:**
```
ImportError while importing test module
'tests/test_config.py'
```

**Problem:** Tests can't import project modules in CI because the project root isn't in Python's import path.

**Solution 1: Set PYTHONPATH** (recommended)
```yaml
- name: Run tests
  env:
    PYTHONPATH: ${{ github.workspace }}
  run: |
    pytest tests/
```

**Solution 2: Install as editable package**
```yaml
- name: Install package
  run: pip install -e .

- name: Run tests
  run: pytest tests/
```

**Why this happens:**
- **Locally:** Current directory is automatically in `sys.path` when running pytest
- **GitHub Actions:** Project root must be explicitly added to `PYTHONPATH`
- **The workspace path:** `${{ github.workspace }}` = `/home/runner/work/project/project`

**Testing the fix locally:**
```bash
# Simulate CI environment
cd /tmp
git clone https://github.com/your-user/serverless_test.git
cd serverless_test

# This will fail (like CI)
pytest tests/

# This works (with PYTHONPATH)
PYTHONPATH=. pytest tests/
```

## References

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Mypy Documentation](https://mypy.readthedocs.io/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Pytest-cov Plugin](https://pytest-cov.readthedocs.io/)

---

**Status:** ✅ All quality checks configured and passing
**Coverage:** 96% across all main modules
**CI/CD:** Fully integrated with GitHub Actions
