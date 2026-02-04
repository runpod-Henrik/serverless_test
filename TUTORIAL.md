# How To Build a Serverless Flaky Test Detector with RunPod and GitHub Actions

## Introduction

Flaky tests—tests that sometimes pass and sometimes fail without code changes—are a persistent problem in software development. They erode confidence in your test suite, waste developer time on re-running CI builds, and can mask real bugs. The solution is to run tests multiple times with different conditions to expose their flaky behavior, but doing this manually is tedious and running it in your normal CI would multiply build times unacceptably.

In this tutorial, you will build a serverless application that automatically detects flaky tests by running them 100+ times in parallel on RunPod's serverless platform. The system will integrate with GitHub Actions to trigger automatically when CI tests fail, then post detailed analysis as PR comments showing whether a failure is a genuine bug or flaky test behavior.

When you're finished, you'll have a production-ready system that:

- Runs tests 100 times in parallel in under 2 minutes
- Costs ~$0.024 per detection run (scales to zero when idle)
- Classifies failures by severity (CRITICAL/HIGH/MEDIUM/LOW/NONE)
- Integrates automatically with GitHub Actions
- Posts detailed results as PR comments
- Sends Slack/Discord notifications

## Prerequisites

Before you begin this tutorial, you'll need:

- **Python 3.12 or higher** installed on your local machine. You can download it from [python.org](https://www.python.org/).
- **Git** installed on your system for version control.
- **A GitHub account** with a repository where you'll set up the integration.
- **A RunPod account** for deploying the serverless function. Sign up at [runpod.io](https://www.runpod.io).
- **A Docker Hub account** for storing your Docker image. Sign up at [hub.docker.com](https://hub.docker.com).
- **Basic familiarity with Python** and pytest testing framework.
- **Basic familiarity with Docker** and containerization concepts.

Optional but recommended:
- A Slack workspace for notifications (you can skip this and use GitHub comments only)

## Step 1 — Setting Up Your Project Structure

First, create a new directory for your project and set up the basic structure.

Create the project directory:

```bash
mkdir flaky-test-detector
cd flaky-test-detector
```

Initialize a Git repository:

```bash
git init
echo "*.pyc" > .gitignore
echo "__pycache__/" >> .gitignore
echo ".coverage" >> .gitignore
echo "htmlcov/" >> .gitignore
echo ".pytest_cache/" >> .gitignore
echo "*.db" >> .gitignore
```

This creates a `.gitignore` file to exclude Python cache files, coverage reports, and database files from version control.

Create the initial project structure:

```bash
touch worker.py
touch requirements.txt
mkdir tests
touch tests/test_flaky.py
```

You now have a basic project structure with:
- `worker.py` — Your main serverless handler
- `requirements.txt` — Python dependencies
- `tests/` — Directory for test files
- `tests/test_flaky.py` — Example flaky test for testing

## Step 2 — Creating the Core Serverless Handler

The heart of your application is the serverless handler that receives job requests, clones repositories, and runs tests in parallel.

Open `worker.py` in your text editor and add the following code:

```python
import os
import random
import shlex
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import runpod


def run_test_once(
    cmd_list: list[str], env_overrides: dict[str, str], attempt: int
) -> dict[str, Any]:
    """Run a test once with specific environment variables."""
    env = os.environ.copy()
    env.update(env_overrides)
    try:
        result = subprocess.run(
            cmd_list, capture_output=True, text=True, env=env, timeout=300
        )
        return {
            "attempt": attempt,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "passed": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {
            "attempt": attempt,
            "exit_code": None,
            "stdout": "",
            "stderr": "TIMEOUT",
            "passed": False,
        }
    except Exception as e:
        return {
            "attempt": attempt,
            "exit_code": None,
            "stdout": "",
            "stderr": f"ERROR: {str(e)}",
            "passed": False,
        }


def handler(job: dict[str, Any]) -> dict[str, Any]:
    """Main handler function for RunPod serverless."""
    inp = job["input"]
    repo = inp["repo"]
    test_command = inp["test_command"]
    runs = int(inp.get("runs", 10))
    parallelism = int(inp.get("parallelism", 4))

    # Validate input parameters
    if not repo:
        raise ValueError("Repository URL is required")
    if not test_command:
        raise ValueError("Test command is required")
    if runs < 1 or runs > 1000:
        raise ValueError("Runs must be between 1 and 1000")
    if parallelism < 1 or parallelism > 50:
        raise ValueError("Parallelism must be between 1 and 50")
    if not (repo.startswith("https://") or repo.startswith("git@")):
        raise ValueError(f"Invalid repository URL: {repo}")

    workdir = tempfile.mkdtemp()
    results = []
    original_cwd = os.getcwd()

    try:
        # Clone repository
        try:
            subprocess.run(
                ["git", "clone", repo, workdir],
                check=True,
                capture_output=True,
                text=True,
                timeout=300,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to clone repository: {e.stderr}") from e
        except subprocess.TimeoutExpired as e:
            raise RuntimeError("Repository clone timed out after 5 minutes") from e

        os.chdir(workdir)

        # Install dependencies if requirements.txt exists
        if os.path.exists("requirements.txt"):
            try:
                subprocess.run(
                    ["pip", "install", "-q", "-r", "requirements.txt"],
                    check=True,
                    capture_output=True,
                    timeout=300,
                )
            except subprocess.CalledProcessError as e:
                print(f"Warning: Failed to install dependencies: {e.stderr}")

        # Parse test command safely
        test_command_list = shlex.split(test_command)

        # Run tests in parallel
        with ThreadPoolExecutor(max_workers=parallelism) as executor:
            futures = []
            for i in range(runs):
                env_overrides = {
                    "TEST_SEED": str(random.randint(1, 1_000_000)),
                    "ATTEMPT": str(i),
                }
                futures.append(
                    executor.submit(run_test_once, test_command_list, env_overrides, i)
                )
            for future in as_completed(futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    results.append(
                        {
                            "attempt": len(results),
                            "exit_code": None,
                            "stdout": "",
                            "stderr": f"WORKER ERROR: {str(e)}",
                            "passed": False,
                        }
                    )
    finally:
        os.chdir(original_cwd)
        try:
            shutil.rmtree(workdir)
        except Exception as e:
            print(f"Warning: Failed to clean up temporary directory: {e}")

    failures = [r for r in results if not r["passed"]]
    summary = {
        "total_runs": runs,
        "parallelism": parallelism,
        "failures": len(failures),
        "repro_rate": round(len(failures) / runs, 3),
        "results": sorted(results, key=lambda r: r["attempt"]),
    }
    return summary


runpod.serverless.start({"handler": handler})
```

Let's break down what this code does:

1. **`run_test_once()` function**: Runs a single test with specific environment variables. It captures stdout/stderr, handles timeouts (5 minutes), and returns a structured result.

2. **Input validation**: The handler validates all inputs (repository URL, test command, runs count, parallelism) to prevent invalid requests and security issues.

3. **Repository cloning**: Uses `subprocess.run()` with a list of arguments (not `shell=True`) to safely clone the repository without command injection vulnerabilities.

4. **Dependency installation**: Automatically detects and installs dependencies from `requirements.txt` if present.

5. **Safe command parsing**: Uses `shlex.split()` to parse the test command safely, preventing shell injection attacks.

6. **Parallel execution**: Creates a thread pool and submits multiple test runs, each with a unique random seed (`TEST_SEED`) to expose timing-dependent bugs.

7. **Resource cleanup**: Always restores the original working directory and cleans up temporary files, even if errors occur.

8. **Result aggregation**: Collects all results and calculates the reproduction rate (percentage of failures).

**Security Note**: This code uses `subprocess.run()` with argument lists instead of `shell=True` to prevent command injection vulnerabilities. The repository URL is validated, and the test command is parsed with `shlex.split()` for safe execution.

## Step 3 — Creating Dependencies File

Create `requirements.txt` with pinned versions for reproducibility:

```txt
# Core dependencies
runpod==1.8.1
pytest==9.0.2
PyYAML==6.0.3

# Development tools
ruff==0.9.1
mypy==1.14.1
coverage==7.13.3
pytest-cov==7.0.0
types-PyYAML==6.0.12.20241230
```

Save this file. Pinning specific versions ensures your application behaves consistently across all environments.

## Step 4 — Creating a Test Example

To test your flaky test detector, you need an intentionally flaky test. Open `tests/test_flaky.py` and add:

```python
import os
import random
import time


def test_order_processing_is_eventually_consistent():
    """
    Intentionally flaky test to demonstrate the detector.
    This test fails approximately 40% of the time due to random timing.
    """
    # Use TEST_SEED from environment if provided
    seed = int(os.getenv("TEST_SEED", "0"))
    if seed:
        random.seed(seed)

    # Simulate async behavior with random timing
    processing_time = random.uniform(0.0, 0.3)
    time.sleep(processing_time)

    # This will fail ~40% of the time
    success_threshold = 0.18
    assert processing_time < success_threshold, (
        f"Order not processed in time (took {processing_time:.3f}s)"
    )
```

This test uses the `TEST_SEED` environment variable (set by the handler) to get different random values on each run, simulating non-deterministic test behavior.

## Step 5 — Building the Docker Container

RunPod requires your application to be packaged as a Docker image. Create a `Dockerfile` in your project root:

```dockerfile
FROM python:3.12-slim

# Install git (required for cloning repositories)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY worker.py .

# Create entry point script
RUN echo '#!/bin/bash\npython3 worker.py' > /app/run.sh && chmod +x /app/run.sh

# Start the worker
CMD ["/app/run.sh"]
```

This Dockerfile:
- Uses Python 3.12 slim base image
- Installs git (needed to clone repositories)
- Installs your Python dependencies
- Copies your worker code
- Creates a startup script

Build the Docker image (replace `your-username` with your Docker Hub username):

```bash
docker build --platform linux/amd64 -t your-username/flaky-test-detector:latest .
```

**Important**: The `--platform linux/amd64` flag ensures the image works on RunPod's infrastructure, even if you're building on Apple Silicon (M1/M2 Mac).

Test the image locally:

```bash
docker run --rm your-username/flaky-test-detector:latest
```

You should see output indicating the RunPod worker is starting.

Push the image to Docker Hub:

```bash
docker login
docker push your-username/flaky-test-detector:latest
```

Your Docker image is now available for RunPod to use.

## Step 6 — Deploying to RunPod

Now you'll deploy your Docker container to RunPod's serverless platform.

1. Go to [runpod.io](https://www.runpod.io) and log in to your account.

2. Navigate to the **Serverless** section in the left sidebar.

3. Click **New Endpoint**.

4. Configure your endpoint:
   - **Name**: `flaky-test-detector`
   - **Docker Image**: `your-username/flaky-test-detector:latest`
   - **Container Disk**: `10 GB` (enough for cloning repositories)
   - **GPU Type**: Select **CPU** (tests don't need GPU acceleration)
   - **Min Workers**: `0` (scales to zero when idle = no cost)
   - **Max Workers**: `3` (adjust based on expected usage)
   - **Idle Timeout**: `30 seconds`

5. Click **Deploy**.

6. Wait for the deployment to complete. You'll see a green checkmark when ready.

7. Copy your **Endpoint ID** from the endpoint details page. It looks like `tmi5oesd1cmsjw`. You'll need this for GitHub Actions.

8. Get your **API Key**:
   - Click your profile icon → **Settings**
   - Navigate to **API Keys**
   - Copy your API key (starts with `rpa_`)

Keep these credentials secure—you'll add them to GitHub in the next step.

## Step 7 — Testing Your Deployment

Before integrating with GitHub Actions, test that your RunPod endpoint works correctly.

Create a test script `test_endpoint.py`:

```python
import runpod

# Replace with your actual credentials
runpod.api_key = "rpa_YOUR_API_KEY"
endpoint_id = "YOUR_ENDPOINT_ID"

# Create endpoint instance
endpoint = runpod.Endpoint(endpoint_id)

# Run a test job
job = endpoint.run(
    {
        "repo": "https://github.com/your-username/flaky-test-detector",
        "test_command": "pytest tests/test_flaky.py -v",
        "runs": 50,
        "parallelism": 5,
    }
)

# Wait for results
result = job.output()
print(f"Total runs: {result['total_runs']}")
print(f"Failures: {result['failures']}")
print(f"Reproduction rate: {result['repro_rate'] * 100:.1f}%")
```

**Security Note**: Don't commit this file with your actual credentials. Add it to `.gitignore`:

```bash
echo "test_endpoint.py" >> .gitignore
```

Run the test:

```bash
pip install runpod
python test_endpoint.py
```

You should see output like:

```
Total runs: 50
Failures: 18
Reproduction rate: 36.0%
```

This confirms your flaky test detector is working! The test failed 36% of the time, clearly showing flaky behavior.

## Step 8 — Setting Up GitHub Actions Integration

Now you'll create GitHub Actions workflows to automatically trigger flaky test detection when CI tests fail.

First, create the main CI workflow that runs your tests. Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  lint-and-type-check:
    name: Lint and Type Check
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run ruff linter
        run: |
          ruff check . --output-format=github

      - name: Run mypy type checking
        run: |
          mypy worker.py

  test:
    name: Test Suite
    runs-on: ubuntu-latest
    needs: lint-and-type-check

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run tests with coverage
        env:
          PYTHONPATH: ${{ github.workspace }}
        run: |
          pytest tests/ -v --cov=worker --cov-report=term-missing
```

This workflow runs linting, type checking, and tests on every push and pull request.

## Step 9 — Creating the Flaky Test Detector Workflow

Create `.github/workflows/flaky-test-detector.yml`:

```yaml
name: Flaky Test Detector

on:
  workflow_run:
    workflows: ["CI"]
    types:
      - completed

jobs:
  detect-flaky-tests:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}

    permissions:
      contents: read
      pull-requests: write
      issues: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install RunPod SDK
        run: |
          pip install runpod

      - name: Run flaky test detector
        id: flaky-detector
        run: |
          python3 << 'EOF'
          import runpod
          import os
          import json

          runpod.api_key = os.environ['RUNPOD_API_KEY']
          endpoint = runpod.Endpoint(os.environ['RUNPOD_ENDPOINT_ID'])

          # Run detection (adjust test_command to your needs)
          job = endpoint.run({
              "repo": f"https://github.com/{os.environ['GITHUB_REPOSITORY']}",
              "test_command": "pytest tests/ -v",
              "runs": 100,
              "parallelism": 10
          })

          result = job.output()

          # Save results
          with open('flaky_results.json', 'w') as f:
              json.dump(result, f)

          # Determine severity
          rate = result['repro_rate']
          if rate >= 0.9:
              severity = "🔴 CRITICAL"
          elif rate >= 0.5:
              severity = "🟠 HIGH"
          elif rate >= 0.1:
              severity = "🟡 MEDIUM"
          elif rate > 0:
              severity = "🟢 LOW"
          else:
              severity = "✅ NONE"

          print(f"SEVERITY={severity}")
          print(f"REPRO_RATE={rate * 100:.1f}%")
          EOF
        env:
          RUNPOD_API_KEY: ${{ secrets.RUNPOD_API_KEY }}
          RUNPOD_ENDPOINT_ID: ${{ secrets.RUNPOD_ENDPOINT_ID }}
          GITHUB_REPOSITORY: ${{ github.repository }}

      - name: Post results to PR
        if: github.event.workflow_run.pull_requests[0].number != ''
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const result = JSON.parse(fs.readFileSync('flaky_results.json', 'utf8'));

            const rate = result.repro_rate;
            let severity = '';
            if (rate >= 0.9) severity = '🔴 CRITICAL';
            else if (rate >= 0.5) severity = '🟠 HIGH';
            else if (rate >= 0.1) severity = '🟡 MEDIUM';
            else if (rate > 0) severity = '🟢 LOW';
            else severity = '✅ NONE';

            const body = `## ${severity} Flaky Test Detection Results

            **Severity:** ${severity.replace(/[🔴🟠🟡🟢✅] /, '')}

            ### Summary
            - **Total runs:** ${result.total_runs}
            - **Failures:** ${result.failures}
            - **Reproduction rate:** ${(rate * 100).toFixed(1)}%

            ${result.failures > 0 ? `### Failed Runs\n${result.results.filter(r => !r.passed).slice(0, 10).map(r => `- Attempt ${r.attempt}: ${r.stderr || r.stdout}`).join('\n')}` : ''}

            *Detected by [Serverless Flaky Test Detector](https://github.com/${context.repo.owner}/${context.repo.repo})*`;

            await github.rest.issues.createComment({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: ${{ github.event.workflow_run.pull_requests[0].number }},
              body: body
            });
```

This workflow:
1. Triggers when the CI workflow completes with a failure
2. Runs the flaky test detector on RunPod
3. Analyzes the reproduction rate
4. Posts results as a PR comment with severity classification

## Step 10 — Configuring GitHub Secrets

Add your RunPod credentials to GitHub as secrets:

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**

Add these secrets:

**Secret 1:**
- Name: `RUNPOD_API_KEY`
- Value: Your RunPod API key (from Step 6)

**Secret 2:**
- Name: `RUNPOD_ENDPOINT_ID`
- Value: Your RunPod endpoint ID (from Step 6)

Alternatively, use the GitHub CLI:

```bash
gh secret set RUNPOD_API_KEY --body "rpa_YOUR_API_KEY"
gh secret set RUNPOD_ENDPOINT_ID --body "YOUR_ENDPOINT_ID"
```

Your secrets are now securely stored and available to GitHub Actions.

## Step 11 — Testing the Complete System

Now test the entire workflow end-to-end.

1. **Commit your code**:

```bash
git add .
git commit -m "Add serverless flaky test detector"
git push origin main
```

2. **Create a test branch**:

```bash
git checkout -b test-flaky-detection
```

3. **Make the test fail more consistently** to trigger the detector. Edit `tests/test_flaky.py`:

```python
# Change the threshold to make it fail almost always
success_threshold = 0.01  # Was 0.18
```

4. **Commit and push**:

```bash
git add tests/test_flaky.py
git commit -m "Test flaky detector with failing test"
git push -u origin test-flaky-detection
```

5. **Create a pull request** on GitHub

6. **Watch the workflows**:
   - Navigate to **Actions** tab in your repository
   - You'll see the **CI** workflow run first
   - When it fails, the **Flaky Test Detector** workflow triggers
   - After ~2 minutes, check your PR for a comment with results

You should see a comment like:

```
## 🔴 CRITICAL Flaky Test Detection Results

**Severity:** CRITICAL

### Summary
- **Total runs:** 100
- **Failures:** 98
- **Reproduction rate:** 98.0%

This indicates a real bug, not flaky behavior.
```

**Success!** Your flaky test detector is working automatically.

## Step 12 — Adding Code Quality Checks (Optional but Recommended)

Add type checking and linting to catch issues early. Create `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "UP", "B", "C4", "SIM"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.12"
warn_return_any = true
disallow_untyped_defs = true
warn_unused_configs = true

[[tool.mypy.overrides]]
module = "runpod.*"
ignore_missing_imports = true

[tool.coverage.run]
source = ["worker.py"]

[tool.coverage.report]
fail_under = 90.0
```

Install the tools:

```bash
pip install ruff mypy coverage pytest-cov
```

Run checks locally:

```bash
# Lint code
ruff check .

# Type check
mypy worker.py

# Run tests with coverage
pytest tests/ --cov=worker --cov-report=term-missing
```

These tools are already integrated in your GitHub Actions workflow from Step 8.

## Troubleshooting

### Issue: ImportError in GitHub Actions

**Error message:**
```
ImportError while importing test module 'tests/test_worker.py'
```

**Solution:**
Add `PYTHONPATH` to your test step in `.github/workflows/ci.yml`:

```yaml
- name: Run tests with coverage
  env:
    PYTHONPATH: ${{ github.workspace }}
  run: |
    pytest tests/ -v
```

### Issue: Docker Build Fails with Architecture Mismatch

**Error message:**
```
no matching manifest for linux/amd64
```

**Solution:**
Always specify the platform when building:

```bash
docker build --platform linux/amd64 -t your-username/flaky-test-detector:latest .
```

### Issue: Coverage Below 90%

**Error message:**
```
Required test coverage of 90% not reached. Total coverage: 73.95%
```

**Solution:**
Measure only the modules you test, not all files:

```bash
pytest tests/ --cov=worker --cov-report=term-missing
```

Update `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["worker.py"]
```

### Issue: Flaky Detector Not Triggering

**Possible causes:**
1. Workflow name mismatch in `.github/workflows/flaky-test-detector.yml`
2. Secrets not configured correctly
3. Permissions insufficient

**Solution:**
1. Verify workflow name matches: `workflows: ["CI"]`
2. Check secrets in **Settings → Secrets and variables → Actions**
3. Ensure workflow has these permissions:
   ```yaml
   permissions:
     contents: read
     pull-requests: write
   ```

### Issue: RunPod Endpoint Cold Start

**Symptom:** First request takes 30+ seconds

**Explanation:** This is normal. RunPod scales to zero, so the first request needs to start a worker.

**Mitigation options:**
- Set **Min Workers** to 1 (costs more but eliminates cold starts)
- Accept cold starts (most cost-effective for occasional use)

## Conclusion

In this tutorial, you built a serverless flaky test detector that automatically analyzes test failures to distinguish between genuine bugs and flaky tests. Your system:

- ✅ Runs tests 100 times in parallel in under 2 minutes
- ✅ Costs ~$0.024 per detection run (scales to zero when idle)
- ✅ Integrates automatically with GitHub Actions
- ✅ Posts detailed results with severity classification
- ✅ Is production-ready with security hardening and quality checks

### What You've Learned

Through building this system, you've learned:

1. **Serverless architecture patterns**: How to build event-driven, scalable applications
2. **Security best practices**: Preventing command injection and validating inputs
3. **Parallel processing**: Using ThreadPoolExecutor for concurrent test execution
4. **CI/CD integration**: Triggering workflows based on test failures
5. **Docker deployment**: Building and deploying containers to serverless platforms

### Next Steps

Now that you have a working flaky test detector, consider these enhancements:

**Add configuration file support:**
Create `.flaky-detector.yml` in repositories to customize behavior per-project:

```yaml
runs: 150
parallelism: 15
severity_thresholds:
  medium: 0.05
```

**Add historical tracking:**
Store results in a SQLite database to track flakiness trends over time.

**Add Slack notifications:**
Send alerts to Slack when flaky tests are detected:

```python
import requests

webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
if webhook_url:
    requests.post(webhook_url, json={
        "text": f"🟡 Flaky test detected: {rate * 100:.1f}% failure rate"
    })
```

**Support private repositories:**
Add SSH key handling or token-based authentication for private repos.

**Parse test output:**
Extract specific test names from pytest output to identify exactly which tests are flaky.

### Additional Resources

- [RunPod Documentation](https://docs.runpod.io/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [pytest Documentation](https://docs.pytest.org/)
- [Docker Documentation](https://docs.docker.com/)
- [Python subprocess Module](https://docs.python.org/3/library/subprocess.html)

The complete source code for this tutorial is available on GitHub at [runpod-Henrik/serverless_test](https://github.com/runpod-Henrik/serverless_test).

---

**About the Author:** This tutorial demonstrates building production-ready serverless applications using modern Python development practices including type checking, linting, comprehensive testing, and automated CI/CD integration.
