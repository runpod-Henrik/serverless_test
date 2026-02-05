# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a RunPod serverless function for detecting flaky tests. It clones a repository, runs a specified test command multiple times in parallel with different seeds, and returns statistics about failure rates.

## Architecture

**Main Components:**
- `worker.py`: RunPod serverless handler that orchestrates the flaky test detection
  - `handler()`: Entry point that receives job configuration via `job["input"]`
  - `run_test_once()`: Executes a single test run with custom environment variables
  - Uses `ThreadPoolExecutor` for parallel test execution

- `config.py`: Configuration management system
  - Loads `.flaky-detector.yml` from repositories
  - Manages severity thresholds and ignore patterns
  - Validates and merges configuration overrides

- `database.py`: Historical tracking database (SQLite)
  - Stores test run results with full metadata
  - Provides query API for trends and statistics
  - Supports repository filtering and date ranges

- `dashboard.py`: Interactive Streamlit dashboard
  - Visualizes flakiness trends over time
  - Shows most flaky test commands
  - Displays severity distributions
  - Filterable by repository and time period

**Job Input Format:**
```json
{
  "repo": "https://github.com/user/repo",
  "test_command": "pytest tests/test_file.py",
  "runs": 50,
  "parallelism": 5
}
```

**Job Output Format:**
Returns a summary with:
- `total_runs`: Number of test executions
- `parallelism`: Parallel worker count
- `failures`: Number of failed runs
- `repro_rate`: Failure rate (0.0 to 1.0)
- `results`: Array of individual run results with exit codes and output

**Test Execution Flow:**
1. Validates input parameters (repo URL, runs, parallelism, test command)
2. Clones the repository into a temporary directory
3. Installs dependencies from requirements.txt if present
4. Changes working directory to the cloned repo
5. Spawns parallel workers (via `ThreadPoolExecutor`)
6. Each worker runs the test command with unique `TEST_SEED` and `ATTEMPT` environment variables
7. Collects all results and calculates failure statistics
8. Cleans up temporary directory and restores working directory

**Input Validation:**
- Repository URL must start with `https://` or `git@`
- Runs must be between 1 and 1000
- Parallelism must be between 1 and 50
- Test command and repo URL are required

## Development Commands

**🛡️ Before every push - Run comprehensive checks:**
```bash
./scripts/run_all_checks.sh  # Runs ALL CI checks locally (30-60s)
python scripts/validate_flaky_detector.py  # End-to-end system validation
```

`run_all_checks.sh` runs:
- Ruff linting & formatting
- Pylint code quality (catches variable shadowing)
- Mypy type checking
- Pytest with coverage (93 tests, 96%+ coverage)
- Actionlint workflow validation
- Bandit security scanning
- End-to-end system validation

`validate_flaky_detector.py` validates:
- Configuration system
- Database system
- Local flaky detector (worker.py)
- RunPod integration (if credentials available)

**Run all tests:**
```bash
pytest tests/ -v  # 93 tests
PYTHONPATH=. pytest --cov=worker --cov=config --cov=database  # With coverage
```

**Run specific test suites:**
```bash
pytest tests/test_config.py -v      # Configuration (15 tests)
pytest tests/test_database.py -v    # Database (10 tests)
pytest tests/test_worker.py -v      # Worker (58 tests)
pytest tests/workflows/ -v          # Workflow tests (22 tests)
pytest tests/test_flaky.py -v       # Example flaky test (excluded from normal runs)
```

**Code quality checks:**
```bash
# Linting
ruff check .                    # Fast linting
pylint scripts/ tests/          # Deep code analysis

# Type checking
mypy scripts/ --ignore-missing-imports

# Formatting
ruff format .                   # Auto-format
ruff format --check .          # Check without modifying

# Security
bandit -r scripts/ tests/      # Security scan
```

**Workflow validation:**
```bash
actionlint                                              # Validate workflows
python scripts/workflow_utils/validate_and_fix.py      # With detailed output
python scripts/workflow_utils/validate_and_fix.py --ai-suggest  # With AI fixes (requires ANTHROPIC_API_KEY)
```

**Start the dashboard:**
```bash
streamlit run dashboard.py
```

**Test locally:**
```bash
python3 local_test.py  # Test without RunPod
```

**Test with sample input:**
The `test_input.json` file contains example job configuration for testing the handler.

## Dependencies

**Core:**
- Python 3.12+
- `runpod`: Serverless framework
- `pytest`: Test framework
- `pyyaml`: Configuration parsing

**Quality & Development:**
- `ruff`: Fast linting and formatting
- `pylint`: Deep code analysis (catches variable shadowing)
- `mypy`: Type checking
- `bandit`: Security scanning
- `pytest-cov`: Coverage reporting
- `pre-commit`: Git hooks for automated checks

**Dashboard (optional):**
- `streamlit`: Dashboard framework
- `plotly`: Interactive charts
- `pandas`: Data manipulation

**Workflow Validation (optional):**
- `anthropic`: AI-powered workflow fix suggestions

Install with:
```bash
pip install -r requirements.txt
# or for faster installation:
uv sync --all-extras
```

## Testing

**93 tests covering all functionality:**
- Configuration system (15 tests)
- Database operations (10 tests)
- Worker functionality (58 tests)
- Workflow validation (22 tests)
- Example flaky test (1 test, excluded from normal runs)

**Coverage:** 96.71% on core modules (worker, config, database)

All tests passing ✓

## Code Quality Standards

This project uses a **multi-layer defense system** to prevent CI failures:

**Layer 1: IDE/Editor** - Real-time linting with LSP
**Layer 2: Pre-commit Hooks** - Automatic validation on commit
**Layer 3: Local Test Script** - `./scripts/run_all_checks.sh`
**Layer 4: CI Pipeline** - Final verification

**Quality Requirements:**
- ✅ Ruff linting must pass
- ✅ Pylint score ≥ 8.0/10
- ✅ Mypy type checking must pass (scripts only)
- ✅ All tests must pass
- ✅ Coverage must be ≥ 90%
- ✅ Actionlint workflow validation must pass
- ✅ Bandit security scan must pass

**See:** [PREVENTING_CI_FAILURES.md](PREVENTING_CI_FAILURES.md) for complete guide

## Type Annotations

All scripts have full type annotations for mypy compliance:

```python
from typing import Any, Optional

def function_name(arg: str, count: int = 10) -> dict[str, Any]:
    """Function with type hints."""
    return {"result": arg * count}
```

**Type checking:**
- Scripts in `scripts/` are fully type-annotated
- Test files have relaxed type requirements (fixtures/mocks)
- Use `mypy scripts/ --ignore-missing-imports` to verify

**Common patterns:**
- Return types: `-> None`, `-> str`, `-> dict[str, Any]`
- Optional values: `Optional[str]` or `str | None`
- Collections: `list[dict[str, Any]]`, `dict[str, list[str]]`

## Coding Conventions

**When adding new code:**

1. **Run comprehensive checks before committing:**
   ```bash
   ./scripts/run_all_checks.sh
   ```

2. **Add type annotations to new functions:**
   ```python
   def new_function(param: str) -> None:
       pass
   ```

3. **Follow existing patterns:**
   - Use `ruff format` for consistent formatting
   - Keep functions focused and small
   - Add docstrings for complex logic
   - Write tests for new functionality

4. **Common pitfalls to avoid:**
   - Variable shadowing (pylint catches this)
   - Unquoted shell variables
   - Missing type conversions
   - Incorrect XML element parsing

**Pre-commit hooks:**
Run automatically on `git commit`. Install with:
```bash
pre-commit install
```

Hooks validate: ruff, pylint, mypy, actionlint, bandit, YAML syntax
