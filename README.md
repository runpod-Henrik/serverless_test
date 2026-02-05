# Serverless Flaky Test Detector

A RunPod serverless function that detects flaky tests by running them multiple times in parallel with different random seeds. This tool helps identify non-deterministic test failures that can be difficult to reproduce in normal CI/CD environments.

**📚 New to this project? Start with the [Step-by-Step Tutorial](TUTORIAL.md)** — A comprehensive guide to building this system from scratch, following DigitalOcean's tutorial format with clear instructions, code examples, and troubleshooting tips.

**🌍 Multi-Language Support:** See [MULTI_LANGUAGE.md](MULTI_LANGUAGE.md) for extending support to Go, TypeScript, and other test frameworks beyond Python.

## Features

- **Parallel Test Execution**: Run tests multiple times concurrently to quickly identify flakiness
- **Seed Randomization**: Each test run uses a unique random seed to expose timing-dependent bugs
- **Multi-Language Support**: Python/pytest (built-in), Go, TypeScript/Jest, and more (see [MULTI_LANGUAGE.md](MULTI_LANGUAGE.md))
- **Automatic Dependency Installation**: Installs requirements.txt automatically from cloned repositories
- **CI/CD Integration**: Automatically detect flaky tests when CI/CD tests fail (GitHub Actions, GitLab CI, etc.)
- **Multi-Channel Reporting**: Post results to PR comments, Slack, Discord, or CI/CD logs
- **Configuration File Support**: Customize behavior per-repository with `.flaky-detector.yml`
- **Historical Tracking**: SQLite database tracks test results over time with trend analysis
- **Interactive Dashboard**: Streamlit-based dashboard for visualizing flakiness patterns
- **Comprehensive Error Handling**: Robust error handling for network issues, timeouts, and test failures
- **Resource Cleanup**: Automatic cleanup of temporary directories and working directory restoration
- **Security Hardened**: Protected against command injection with proper input validation
- **Fully Tested**: 40+ tests with 96% code coverage across all main modules
- **Code Quality**: Linting with ruff, type checking with mypy, automated formatting
- **CI/CD Quality Gates**: Automated linting, type checking, and coverage enforcement

## Prerequisites

- Python 3.12 or higher
- Git installed on your system
- RunPod account (for deployment)

## Installation

### Option 1: Using pip

```bash
# Clone the repository
git clone https://github.com/runpod-Henrik/serverless_test.git
cd serverless_test

# Install dependencies
pip install -r requirements.txt
```

### Option 2: Using uv (recommended for faster installation)

```bash
# Clone the repository
git clone https://github.com/runpod-Henrik/serverless_test.git
cd serverless_test

# Install with uv
uv sync
```

**Note on Dependencies:** All package versions are pinned to specific releases (e.g., `pytest==9.0.2`) for reproducibility and stability. See [DEPENDENCIES.md](DEPENDENCIES.md) for version management strategy and update procedures.

## Configuration

Customize flaky test detector behavior per-repository with `.flaky-detector.yml`:

```yaml
# Example configuration
runs: 150                    # More thorough testing
parallelism: 15             # Faster execution
severity_thresholds:
  medium: 0.05              # More sensitive to flakiness
ignore_patterns:
  - "test_known_flaky_*"    # Skip certain tests
```

See [CONFIGURATION.md](CONFIGURATION.md) for full reference.

## Historical Tracking & Dashboard

Track test flakiness trends over time with the interactive dashboard:

```bash
streamlit run dashboard.py
# Opens at http://localhost:8501
```

**Dashboard features:**
- 📊 Overview metrics and statistics
- 📈 Flakiness trend visualization over time
- 🔥 Most flaky test commands
- 🎯 Severity distribution charts
- 📋 Filterable test run history

See [HISTORICAL_TRACKING.md](HISTORICAL_TRACKING.md) for complete guide.

## Local Development

### Running Tests Locally

Test the flaky test detector with the included example:

```bash
# Run the example flaky test
pytest tests/test_flaky.py

# Run with a specific seed
TEST_SEED=12345 pytest tests/test_flaky.py

# Run multiple times to see flakiness
for i in {1..10}; do pytest tests/test_flaky.py; done

# Run all tests (40+ tests)
pytest tests/ -v

# Run with coverage report (only tested modules)
pytest tests/ --cov=worker --cov=config --cov=database --cov-report=term-missing

# Or use pytest built-in settings
pytest tests/  # Uses settings from pyproject.toml

# Run integration tests
python3 test_new_features.py
```

### Testing the Worker Locally

You can test the worker function locally without deploying to RunPod:

```bash
# Start the worker (it will wait for jobs)
python worker.py
```

To send a test job to the local worker, you'll need to use the RunPod SDK:

```python
import runpod

# Configure for local testing
runpod.api_key = "your-api-key"

# Send a test job
result = runpod.run_sync(
    endpoint_id="your-endpoint-id",
    input={
        "repo": "https://github.com/runpod-Henrik/serverless_test",
        "test_command": "pytest tests/test_flaky.py",
        "runs": 50,
        "parallelism": 5
    }
)

print(result)
```

### Code Quality Checks

This project includes comprehensive quality checks. See [QUALITY_CHECKS.md](QUALITY_CHECKS.md) for full details.

**Run all checks locally:**

```bash
# Lint code
ruff check .

# Auto-fix linting issues
ruff check . --fix

# Format code
ruff format .

# Type check
mypy worker.py config.py database.py

# Run tests with coverage (90% minimum, only tested modules)
pytest tests/ --cov=worker --cov=config --cov=database --cov-fail-under=90

# Run all checks at once
ruff check . && mypy worker.py config.py database.py && pytest tests/ --cov=worker --cov=config --cov=database --cov-fail-under=90
```

**Quality Standards:**
- ✅ Ruff linting (PEP 8, imports, bugbear, simplify)
- ✅ Mypy type checking (strict mode)
- ✅ 90% minimum test coverage (current: 96.7%)
- ✅ Coverage measured on core modules only (worker, config, database)
- ✅ Automated in CI/CD (see CI/CD Integration below)

**Note:** Coverage only measures the core modules we have tests for (worker.py, config.py, database.py), not UI code (dashboard.py) or integration scripts (scripts/).

## Configuration

### Input Parameters

The serverless function accepts the following input parameters:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `repo` | string | Yes | - | Git repository URL (must start with `https://` or `git@`) |
| `test_command` | string | Yes | - | Test command to execute (e.g., `pytest tests/`) |
| `runs` | integer | No | 10 | Number of times to run the test (1-1000) |
| `parallelism` | integer | No | 4 | Number of parallel workers (1-50) |

### Example Configuration Files

**test_input.json** - Simple test configuration:
```json
{
  "repo": "https://github.com/runpod-Henrik/serverless_test",
  "test_command": "pytest tests/test_flaky.py",
  "runs": 50,
  "parallelism": 5
}
```

**input.json** - Production configuration:
```json
{
  "repo": "https://github.com/runpod-Henrik/serverless_test",
  "test_command": "pytest tests/test_flaky.py",
  "runs": 100,
  "parallelism": 8
}
```

## CI/CD Integration

The flaky test detector includes **two automated workflows**:

### 1. Main CI Pipeline (Runs on Every Push/PR)

Ensures code quality with automated checks:

**Stage 1: Lint and Type Check**
- ✅ Ruff linting (code style, imports, common bugs)
- ✅ Code formatting check
- ✅ Mypy type checking (strict mode)

**Stage 2: Test Suite** (runs after lint passes)
- ✅ Full test suite (40+ tests)
- ✅ Coverage reporting (90% minimum required)
- ✅ Coverage reports uploaded as artifacts
- ✅ PR comments with coverage status

**Workflow:** `.github/workflows/ci.yml`

### 2. Flaky Test Detector (Runs on CI Test Failures)

Automatically detects flaky tests when CI fails:

**Setup Steps:**

1. **Add GitHub Secrets**

   Go to: `Settings → Secrets and variables → Actions → New repository secret`

   Add these secrets:
   ```
   RUNPOD_API_KEY = <your RunPod API key>
   RUNPOD_ENDPOINT_ID = <your endpoint ID>
   SLACK_WEBHOOK_URL = <optional, for Slack notifications>
   ```

   Get your RunPod credentials from:
   - API Key: https://www.runpod.io/console/user/settings
   - Endpoint ID: Your RunPod serverless endpoint

2. **Using GitHub CLI** (alternative):
   ```bash
   gh secret set RUNPOD_API_KEY --body "your-api-key"
   gh secret set RUNPOD_ENDPOINT_ID --body "your-endpoint-id"
   gh secret set SLACK_WEBHOOK_URL --body "your-slack-webhook"  # optional
   ```

3. **Verify Workflow Configuration**

   Edit `.github/workflows/flaky-test-detector.yml` line 5:
   ```yaml
   workflows: ["CI"]  # Match your CI workflow name
   ```

4. **Test the Integration**

   Create a test branch with a failing test:
   ```bash
   git checkout -b test-flaky-detection
   # Make a test fail temporarily
   git commit -am "Test flaky detector"
   git push -u origin test-flaky-detection
   ```

   Create a PR → CI fails → Flaky detector runs automatically → Check PR comments

**What Happens Automatically:**
1. CI tests fail
2. Flaky detector workflow triggers
3. Runs failed test 100x in parallel on RunPod
4. Analyzes failure pattern
5. Posts PR comment with severity:
   - 🔴 CRITICAL (>90%) - Real bug, not flaky
   - 🟠 HIGH (50-90%) - Very unstable, fix before merge
   - 🟡 MEDIUM (10-50%) - Flaky test, should fix
   - 🟢 LOW (1-10%) - Occasional flakiness
   - ✅ NONE (0%) - One-time issue, safe to merge
6. Sends Slack notification (if configured)
7. Uploads detailed results as artifacts

**Workflow:** `.github/workflows/flaky-test-detector.yml`

**Cost:** ~$0.024 per detection run (100 tests, 2 minutes)

## Deployment to RunPod

### Step 1: Choose Your Docker Image

The project includes two Dockerfile options:

#### Option A: Multi-Language Support (Default - `Dockerfile`)
Includes Python, Node.js, and Go runtimes for testing projects in multiple languages.

- **Size**: ~2.1 GB
- **Supports**: Python, Go, TypeScript/Jest, TypeScript/Vitest, JavaScript/Mocha
- **Use when**: You have polyglot projects or need to test multiple languages

```bash
# Build multi-language image
docker build -t your-username/flaky-test-detector:latest .

# Push to Docker Hub
docker push your-username/flaky-test-detector:latest
```

#### Option B: Python-Only (`Dockerfile.python-only`)
Smaller image with only Python runtime for Python/pytest projects.

- **Size**: ~285 MB
- **Supports**: Python/pytest only
- **Use when**: You only need Python test support

```bash
# Build Python-only image
docker build -f Dockerfile.python-only -t your-username/flaky-test-detector:python-only .

# Push to Docker Hub
docker push your-username/flaky-test-detector:python-only
```

**Included Dockerfile** provides the multi-language setup:

```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git curl wget ca-certificates gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20.x for TypeScript/JavaScript
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install Go 1.22
RUN wget -q https://go.dev/dl/go1.22.0.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go1.22.0.linux-amd64.tar.gz && \
    rm go1.22.0.linux-amd64.tar.gz

ENV PATH="/usr/local/go/bin:${PATH}"

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY worker.py run.sh .
RUN chmod +x run.sh

# Verify all runtimes
RUN python --version && node --version && go version

CMD ["./run.sh"]
```

### Step 2: Deploy to RunPod

1. Log in to [RunPod](https://runpod.io)
2. Navigate to "Serverless" section
3. Click "New Endpoint"
4. Configure your endpoint:
   - **Name**: Flaky Test Detector
   - **Docker Image**: `your-username/flaky-test-detector:latest`
   - **Container Disk**: 10 GB (adjust based on your needs)
   - **GPU Type**: CPU or GPU based on your test requirements
5. Click "Deploy"

### Step 3: Get Your Endpoint ID

After deployment, note your endpoint ID from the RunPod dashboard. You'll use this to send jobs.

## Usage

### Running a Job

Using the RunPod Python SDK:

```python
import runpod

runpod.api_key = "your-runpod-api-key"

# Run a flaky test detection job
job = runpod.Endpoint("your-endpoint-id").run(
    {
        "repo": "https://github.com/your-org/your-repo",
        "test_command": "pytest tests/test_checkout.py::test_payment_processing",
        "runs": 100,
        "parallelism": 10
    }
)

# Wait for results
result = job.output()
print(result)
```

Using cURL:

```bash
curl -X POST https://api.runpod.ai/v2/your-endpoint-id/run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-runpod-api-key" \
  -d '{
    "input": {
      "repo": "https://github.com/your-org/your-repo",
      "test_command": "pytest tests/test_checkout.py",
      "runs": 100,
      "parallelism": 10
    }
  }'
```

### Output Format

The function returns a summary of test results:

```json
{
  "total_runs": 100,
  "parallelism": 10,
  "failures": 23,
  "repro_rate": 0.23,
  "results": [
    {
      "attempt": 0,
      "exit_code": 0,
      "stdout": "test output...",
      "stderr": "",
      "passed": true
    },
    {
      "attempt": 1,
      "exit_code": 1,
      "stdout": "test output...",
      "stderr": "assertion error...",
      "passed": false
    }
  ]
}
```

**Output Fields:**
- `total_runs`: Total number of test executions
- `parallelism`: Number of parallel workers used
- `failures`: Number of failed test runs
- `repro_rate`: Failure rate as a decimal (0.23 = 23% failure rate)
- `results`: Array of individual test run results, sorted by attempt number

## Example Use Cases

### Detect Race Conditions

```python
# Test for race conditions in concurrent operations
runpod.Endpoint("your-endpoint-id").run({
    "repo": "https://github.com/your-org/api-service",
    "test_command": "pytest tests/test_concurrent_api.py -v",
    "runs": 200,
    "parallelism": 20
})
```

### Find Timing-Dependent Bugs

```python
# Run tests with different random seeds
runpod.Endpoint("your-endpoint-id").run({
    "repo": "https://github.com/your-org/game-engine",
    "test_command": "pytest tests/test_game_logic.py",
    "runs": 500,
    "parallelism": 25
})
```

### Validate CI/CD Reliability

```python
# Ensure tests are stable before merging
runpod.Endpoint("your-endpoint-id").run({
    "repo": "https://github.com/your-org/web-app",
    "test_command": "pytest tests/integration/",
    "runs": 50,
    "parallelism": 10
})
```

## Troubleshooting

### Repository Clone Fails

**Error**: `Failed to clone repository`

**Solutions**:
- Verify the repository URL is correct and accessible
- For private repositories, ensure authentication is configured
- Check if the repository requires SSH keys or tokens

### Dependency Installation Fails

**Error**: `Warning: Failed to install dependencies`

**Solutions**:
- Check that `requirements.txt` is valid
- Verify all package names and versions are correct
- Ensure compatible Python version (3.12+)

### Tests Timeout

**Error**: `TIMEOUT`

**Solutions**:
- Individual test runs have a 5-minute timeout
- Consider splitting long-running tests into smaller units
- Reduce the number of parallel workers if system resources are limited

### High Memory Usage

**Solutions**:
- Reduce the `parallelism` parameter
- Increase the container memory allocation in RunPod settings
- Check for memory leaks in your test suite

### Command Injection Errors

**Error**: `Invalid repository URL` or `ValueError`

**Solutions**:
- Ensure repository URLs start with `https://` or `git@`
- Avoid special characters in test commands
- Use proper quoting for complex test commands

### GitHub Actions Import Errors

**Error**: `ImportError while importing test module 'tests/test_config.py'`

**Problem**: Tests can't find project modules (`config`, `database`, `worker`) because the project root isn't in Python's import path in GitHub Actions.

**Solution**: Add `PYTHONPATH` environment variable to your test job:

```yaml
- name: Run tests
  env:
    PYTHONPATH: ${{ github.workspace }}
  run: |
    pytest tests/
```

**Why this happens**:
- Locally: Current directory is automatically in `sys.path`
- GitHub Actions: Project root must be explicitly added to `PYTHONPATH`
- The fix ensures Python looks in the workspace root for imports

**Alternative solution**: Install as editable package:
```yaml
- name: Install package
  run: pip install -e .
```

## Security Considerations

- Repository URLs are validated to prevent command injection
- Test commands are parsed with `shlex.split()` for safe execution
- Input parameters have strict bounds checking
- Temporary directories are automatically cleaned up

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Format code with Black
6. Submit a pull request

## License

This project is provided as-is for detecting flaky tests in your codebase.

## Support

For issues or questions:
- Open an issue on GitHub
- Check the [RunPod documentation](https://docs.runpod.io/)
- Review the `CLAUDE.md` file for development guidance
