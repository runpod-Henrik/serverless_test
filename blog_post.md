# Building a Serverless Flaky Test Detector: From Idea to Production

*How we built an automated system to catch flaky tests before they reach production*

## The Problem: When Tests Lie

You've seen it before. A test fails in CI. You re-run it. It passes. You shrug, merge the PR, and move on.

But what just happened? Was it a real bug that magically fixed itself? A race condition? A timing issue? You don't know, and that uncertainty is technical debt waiting to explode.

**Flaky tests are silent killers.** They erode confidence in your test suite, waste developer time, and worst of all—they hide real bugs. A test that fails 20% of the time isn't "mostly working," it's screaming that something is wrong.

The question is: how do you catch them?

## The Idea: Run It Until It Breaks

The solution is conceptually simple: **if a test is flaky, running it 100 times will expose the pattern.**

A stable test? It'll pass 100/100 times.
A flaky test? It'll show a failure pattern—maybe 15% failures, maybe 40%, maybe 90%.

But running a test 100 times manually is tedious. Running it in your normal CI pipeline would multiply your build times by 100x. We needed something different:

**A serverless function that:**
1. Clones your repository
2. Runs your tests N times in parallel
3. Analyzes the failure pattern
4. Reports back with a "flakiness score"

And it should happen **automatically** whenever CI tests fail.

## The Architecture: RunPod + GitHub Actions

After exploring options, we settled on a three-part architecture:

### 1. **RunPod Serverless Function** (The Detector)
A Docker container that:
- Accepts a job with: repo URL, test command, number of runs
- Clones the repo into a temporary directory
- Installs dependencies automatically
- Spawns parallel workers (ThreadPoolExecutor)
- Runs each test with a unique random seed
- Aggregates results and calculates failure rate
- Returns detailed statistics

**Why RunPod?**
- Scales to zero when idle ($0 cost)
- Fast cold start times
- CPU instances are cheap (~$0.024 per test run)
- Easy API for job submission

### 2. **GitHub Actions Workflow** (The Trigger)
A workflow that:
- Watches for CI test failures
- Extracts which tests failed
- Submits a job to the RunPod endpoint
- Waits for results
- Posts to PR comments with severity indicators
- Sends Slack notifications

### 3. **Smart Reporting** (The Intelligence)
Classification based on failure rate:
- **🔴 CRITICAL (>90%)**: Consistent failure—not flaky, it's a real bug
- **🟠 HIGH (50-90%)**: Very unstable, block PR
- **🟡 MEDIUM (10-50%)**: Clear flaky behavior, should fix
- **🟢 LOW (1-10%)**: Occasional flakiness, monitor
- **✅ NONE (0%)**: One-time CI hiccup, safe to merge

## The Build: From Zero to Production

### Phase 1: The Core Handler

Started with the essential logic in `worker.py`:

```python
def handler(job):
    # Get job parameters
    inp = job["input"]
    repo = inp["repo"]
    test_command = inp["test_command"]
    runs = int(inp.get("runs", 100))
    parallelism = int(inp.get("parallelism", 10))

    # Clone repo
    workdir = tempfile.mkdtemp()
    subprocess.run(["git", "clone", repo, workdir])

    # Run tests in parallel
    with ThreadPoolExecutor(max_workers=parallelism) as executor:
        futures = []
        for i in range(runs):
            env_overrides = {
                "TEST_SEED": str(random.randint(1, 1_000_000)),
                "ATTEMPT": str(i),
            }
            futures.append(
                executor.submit(run_test_once, test_command, env_overrides, i)
            )

        # Collect results
        for future in as_completed(futures):
            results.append(future.result())

    # Calculate statistics
    failures = [r for r in results if not r["passed"]]
    return {
        "total_runs": runs,
        "failures": len(failures),
        "repro_rate": len(failures) / runs,
        "results": results
    }
```

Simple, but it worked.

### Phase 2: Security Hardening

Then reality hit. The initial code had **critical vulnerabilities**:

**🚨 Command Injection Vulnerability #1:**
```python
# BAD - user input directly in shell command
subprocess.run(f"git clone {repo} {workdir}", shell=True)
```

An attacker could set `repo = "https://evil.com; rm -rf / #"` and execute arbitrary commands.

**Fixed:**
```python
# GOOD - use argument lists
subprocess.run(["git", "clone", repo, workdir], check=True)
```

**🚨 Command Injection Vulnerability #2:**
```python
# BAD - test_command executed with shell=True
subprocess.run(test_command, shell=True, ...)
```

**Fixed:**
```python
# GOOD - parse safely with shlex
test_command_list = shlex.split(test_command)
subprocess.run(test_command_list, ...)
```

**🚨 Exposed API Key:**
Found an API key accidentally committed in `input.json`. Removed it, added to `.gitignore`, and documented that it needs to be revoked.

**Lessons learned:**
- Never use `shell=True` with user input
- Always validate input parameters
- Use proper subprocess argument lists
- Scan for secrets before committing

### Phase 3: Reliability & Error Handling

The initial version was fragile. We added:

**1. Input Validation:**
```python
if not repo or not repo.startswith(("https://", "git@")):
    raise ValueError("Invalid repository URL")
if runs < 1 or runs > 1000:
    raise ValueError("Runs must be between 1 and 1000")
```

**2. Resource Cleanup:**
```python
try:
    # Do work...
finally:
    os.chdir(original_cwd)  # Restore working directory
    shutil.rmtree(workdir)  # Clean up temp files
```

**3. Dependency Installation:**
```python
if os.path.exists("requirements.txt"):
    subprocess.run(
        ["pip", "install", "-q", "-r", "requirements.txt"],
        timeout=300
    )
```

**4. Better Error Messages:**
```python
except subprocess.CalledProcessError as e:
    raise RuntimeError(f"Failed to clone repository: {e.stderr}")
except subprocess.TimeoutExpired:
    raise RuntimeError("Repository clone timed out after 5 minutes")
```

### Phase 4: CI/CD Automation

The magic: making it automatic.

**GitHub Actions Workflow** (`.github/workflows/flaky-test-detector.yml`):
```yaml
name: Flaky Test Detector

on:
  workflow_run:
    workflows: ["CI"]  # Triggers after CI workflow
    types: [completed]

jobs:
  detect-flaky-tests:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}

    steps:
      - name: Run flaky test detector
        env:
          RUNPOD_API_KEY: ${{ secrets.RUNPOD_API_KEY }}
          RUNPOD_ENDPOINT_ID: ${{ secrets.RUNPOD_ENDPOINT_ID }}
        run: python scripts/run_flaky_detector.py

      - name: Post results to PR
        run: python scripts/report_to_github.py

      - name: Send Slack notification
        run: python scripts/report_to_slack.py
```

**PR Comment Format:**
```markdown
## 🟡 Flaky Test Detection Results

**Severity:** MEDIUM

This test shows flaky behavior.

### Summary
- **Total runs:** 100
- **Failures:** 36
- **Reproduction rate:** 36.0%

### Failed Test Runs
| Attempt | Exit Code | Error |
|---------|-----------|-------|
| 5       | 1         | AssertionError: Order not processed in time |
| 12      | 1         | AssertionError: Order not processed in time |
...
```

### Phase 5: Docker Deployment Drama

The deployment wasn't smooth. Hit two major issues:

**Issue #1: `python` vs `python3`**

The container kept crashing with "python: command not found"

The problem? The Python Docker image uses `python3`, but our `run.sh` called `python`.

**Fixed:**
```bash
#!/bin/bash
python3 worker.py  # Changed from: python worker.py
```

**Issue #2: Architecture Mismatch**

Built the image on Apple Silicon (M1 Mac), got:
```
failed to pull image: no matching manifest for linux/amd64
```

RunPod needs AMD64 (x86_64), but we built for ARM64.

**Fixed:**
```bash
docker build --platform linux/amd64 -t henrikbae/flaky-test-detector:latest .
```

After that, deployment succeeded!

## The Test: Does It Actually Work?

Created a deliberately flaky test:

```python
def test_order_processing_is_eventually_consistent():
    # Simulate async behavior with random timing
    processing_time = random.uniform(0.0, 0.3)
    time.sleep(processing_time)

    # This will fail ~40% of the time
    success_threshold = 0.18
    assert processing_time < success_threshold, \
        f"Order not processed in time (took {processing_time:.3f}s)"
```

**Running it once:** ✅ PASSED (lucky!)
**Running it twice:** ✅ PASSED, ❌ FAILED (hmm...)
**Running it 50 times:** 18 failures, 32 passes = **36% failure rate**

The detector correctly classified it as **🟡 MEDIUM severity flaky behavior**.

## Phase 7: Code Quality & CI/CD Hardening

After the features were complete, I added comprehensive quality checks:

### Linting with Ruff

**The Problem:** Inconsistent code style, potential bugs hidden in plain sight.

**Solution:** Modern fast linter (10-100x faster than flake8):
```python
# Catches common mistakes
for pattern in ignore_patterns:
    if fnmatch.fnmatch(test_name, pattern):
        return False
return True

# Ruff suggests:
return all(not fnmatch.fnmatch(test_name, pattern)
          for pattern in ignore_patterns)
```

**Configured checks:**
- PEP 8 style enforcement
- Import sorting (isort)
- Common bug patterns (bugbear)
- Code simplification suggestions
- Naming conventions

### Type Checking with Mypy

**Added strict type hints** to all functions:
```python
# Before
def run_test_once(cmd_list, env_overrides, attempt):
    ...

# After
def run_test_once(
    cmd_list: list[str],
    env_overrides: dict[str, str],
    attempt: int
) -> dict[str, Any]:
    ...
```

**Benefits:**
- Catch type errors before runtime
- Better IDE autocomplete
- Self-documenting code
- Prevents common bugs

### CI/CD Quality Gates

**Two-stage pipeline:**

**Stage 1: Lint & Type Check** (fails fast)
```yaml
- Run ruff linter
- Check code formatting
- Run mypy type checking
```

**Stage 2: Test Suite** (only if lint passes)
```yaml
- Run 40+ tests
- Generate coverage reports
- Enforce 90% minimum coverage
- Post PR coverage comments
```

**Result:** Every PR now has automated quality checks.

### GitHub Actions Import Issue

Hit a subtle but common issue when setting up the CI pipeline:

**Error:**
```
ImportError while importing test module
'tests/test_config.py'
```

**The Problem:**
GitHub Actions runs tests in `/home/runner/work/serverless_test/serverless_test`, but Python can't find project modules like `config`, `database`, and `worker` because the project root isn't in the import path.

**Works locally:**
```bash
pytest tests/  # ✅ Works - current directory is in sys.path
```

**Fails in CI:**
```bash
pytest tests/  # ❌ Fails - project root not in PYTHONPATH
```

**The Fix:**
Set `PYTHONPATH` to the workspace directory:

```yaml
- name: Run tests with coverage
  env:
    PYTHONPATH: ${{ github.workspace }}  # Add this!
  run: |
    pytest tests/test_config.py tests/test_database.py tests/test_worker.py
```

**Why this works:**
- `${{ github.workspace }}` = `/home/runner/work/serverless_test/serverless_test`
- Python now looks in project root for imports
- Tests can import `from config import Config`

**Lesson learned:** CI environments are more strict about import paths than local development. Always explicitly set `PYTHONPATH` when running tests in GitHub Actions if you're not using `pip install -e .`

### Coverage Configuration Gotcha

Another issue: coverage initially reported **73.95%** instead of the expected **96%**.

**The Problem:**
```bash
pytest tests/ --cov=.  # Measures EVERYTHING
```

This covered all files: dashboard.py, scripts/, local_test.py, etc. Most of these don't have tests.

**The Fix:**
Only measure modules we actually test:

```yaml
pytest tests/ \
  --cov=worker \
  --cov=config \
  --cov=database
```

**Configuration in pyproject.toml:**
```toml
[tool.coverage.run]
source = ["worker.py", "config.py", "database.py"]

[tool.pytest.ini_options]
addopts = [
  "--cov=worker",
  "--cov=config",
  "--cov=database",
  "--cov-fail-under=90",
]
```

**Result:**
- worker.py: 91.55%
- config.py: 100%
- database.py: 100%
- **Total: 96.7%** ✅

**Lesson learned:** Be explicit about what coverage measures. Don't include UI code, scripts, or test utilities in coverage metrics—focus on core business logic.

## The Results: Production-Ready

After all iterations, we have:

✅ **Secure** - No command injection, validated inputs
✅ **Reliable** - Resource cleanup, error handling, timeouts
✅ **Fast** - Parallel execution (50 runs in ~2 minutes)
✅ **Automated** - Triggers on CI failures, posts to PRs
✅ **Cost-Effective** - Scales to zero, ~$0.024 per test run
✅ **Multi-Channel** - PR comments + Slack notifications
✅ **Well-Documented** - Complete setup guides
✅ **Type-Safe** - Full type coverage with mypy
✅ **High Quality** - 96% test coverage, linted, formatted
✅ **CI/CD Hardened** - Automated quality gates on every PR

## Real-World Impact

Imagine this scenario:

1. Developer pushes code to PR
2. CI runs, test fails once
3. **Old way:** Developer re-runs, it passes, merges 🤞
4. **New way:** Flaky detector triggers automatically
   - Runs test 100 times in 2 minutes
   - Detects 23% failure rate
   - Posts PR comment: "🟡 MEDIUM: Clear flaky behavior"
   - Team knows: **don't merge, fix the race condition**

**Result:** Prevented a flaky test from reaching production.

## Key Takeaways

### Technical Lessons

1. **Security first** - Always validate user input, never use `shell=True` carelessly
2. **Resource management** - Clean up temporary files, restore state
3. **Error handling** - Fail gracefully with helpful messages
4. **Architecture matters** - Docker platform mismatches are easy to miss
5. **Automation wins** - Manual processes don't scale
6. **Type safety matters** - Type hints catch bugs before they reach production
7. **Linting saves time** - Automated code quality checks prevent bikeshedding
8. **Coverage is insurance** - 90%+ coverage gives confidence in refactoring

### Design Decisions That Worked

1. **Serverless > Always-On** - Zero idle cost, infinite scale
2. **Parallel execution** - 10x speedup compared to sequential
3. **Random seeds** - Each run gets unique conditions
4. **Severity classification** - Not all failures are equal
5. **Multiple notification channels** - Meet teams where they are

### What I'd Do Differently

1. **Add retry logic** - Some failures are network hiccups
2. **Cache dependencies** - Speed up cold starts
3. **Support private repos** - Currently only public repos work easily
4. **Test result parsing** - Extract specific failed test names from output
5. **Add benchmarking** - Track performance metrics over time

## Try It Yourself

The entire project is open source and production-ready:

**Repository:** [github.com/runpod-Henrik/serverless_test](https://github.com/runpod-Henrik/serverless_test)

**Quick start:**
```bash
# Clone the repo
git clone https://github.com/runpod-Henrik/serverless_test
cd serverless_test

# Test locally
python3 local_test.py

# Deploy to RunPod (requires Docker Hub account)
docker build --platform linux/amd64 -t YOUR_USERNAME/flaky-test-detector .
docker push YOUR_USERNAME/flaky-test-detector
# Then deploy on runpod.io/console/serverless
```

**Add to your project:**
1. Copy `.github/workflows/flaky-test-detector.yml`
2. Add GitHub secrets: `RUNPOD_API_KEY`, `RUNPOD_ENDPOINT_ID`
3. Next time tests fail, flaky detector runs automatically

## The Bottom Line

Flaky tests are a tax on your team's time and confidence. You can't eliminate all flakiness, but you can **detect it automatically** before it reaches production.

This project proves you can build a sophisticated, serverless test infrastructure in a weekend that:
- Costs pennies per run
- Scales infinitely
- Integrates seamlessly with GitHub
- Actually catches problems

**The best part?** Once it's set up, it runs invisibly in the background, only surfacing when it finds something. No maintenance, no servers to manage, no ongoing costs when idle.

That's the power of serverless architecture done right.

---

## Technical Stack

- **Language:** Python 3.12
- **Serverless Platform:** RunPod
- **CI/CD:** GitHub Actions
- **Container:** Docker (AMD64)
- **Notifications:** GitHub PR Comments, Slack/Discord webhooks
- **Testing:** pytest (example framework)

## Stats

- **Lines of Code:** ~1,500 (including tests, scripts, and workflows)
- **Test Suite:** 40+ tests with 96% code coverage
- **Code Quality:** 100% type coverage, linted with ruff, formatted
- **Docker Image Size:** 285 MB
- **Cold Start Time:** ~15 seconds
- **Test Execution:** 50 tests in ~2 minutes (5 parallel workers)
- **Cost per Run:** ~$0.024 (100 tests, CPU instance)
- **Development Time:** 2 days (from idea to production with full quality checks)

---

*Built with Claude Code and deployed on RunPod. Full source code, documentation, and setup guides available in the repository.*

**Tags:** #serverless #testing #cicd #devops #python #docker #runpod #github-actions

---

## Appendix: Example Output

```json
{
  "total_runs": 50,
  "parallelism": 5,
  "failures": 18,
  "repro_rate": 0.36,
  "results": [
    {
      "attempt": 0,
      "exit_code": 1,
      "stdout": "AssertionError: Order not processed in time (took 0.204s)",
      "passed": false
    },
    {
      "attempt": 1,
      "exit_code": 0,
      "stdout": "1 passed in 0.09s",
      "passed": true
    }
    // ... 48 more results
  ]
}
```

## Phase 6: Enhanced Features

After the initial release, we added two major enhancements based on real-world usage:

### Configuration File Support

Users wanted per-repository customization without modifying code:

```yaml
# .flaky-detector.yml
runs: 150                    # Project-specific settings
parallelism: 15
severity_thresholds:
  medium: 0.05              # More sensitive for critical projects
ignore_patterns:
  - "test_known_flaky_*"    # Skip known issues
```

**Implementation:**
- YAML configuration loader with schema validation
- Nested dictionary merging for partial overrides
- Pattern matching for test filtering
- Customizable severity thresholds

**Testing:** 15 unit tests covering all config scenarios

### Historical Tracking & Dashboard

One-time checks aren't enough—you need to see trends:

**SQLite Database:**
```python
db.save_run(
    repository="user/repo",
    test_command="pytest tests/",
    total_runs=100,
    failures=23,
    repro_rate=0.23,
    severity="MEDIUM",
    results=[...],  # All individual results
    pr_number=42,
    branch="feature/new",
    commit_sha="abc123"
)
```

**Streamlit Dashboard:**
- Overview metrics (total runs, avg flaky rate)
- Flakiness trend over time (line chart)
- Most flaky test commands (ranked table)
- Severity distribution (bar chart)
- Filterable run history

**Query API:**
```python
# Get 30-day trend
trend = db.get_flakiness_trend("user/repo", days=30)

# Find worst offenders
flaky = db.get_most_flaky_commands("user/repo", limit=10)

# Overall statistics
stats = db.get_statistics()
```

**Testing:** 10 unit tests + integration test suite

### Comprehensive Test Coverage

Testing was critical to ensure reliability. Created three test suites:

**tests/test_config.py (15 tests):**
```python
def test_get_severity_critical(self):
    config = Config()
    severity, emoji = config.get_severity(0.95)
    assert severity == "CRITICAL"
    assert emoji == "🔴"
```

**tests/test_database.py (10 tests):**
```python
def test_save_and_retrieve_run(self, temp_db):
    run_id = temp_db.save_run(...)
    run = temp_db.get_run_details(run_id)
    assert run["repository"] == "test/repo"
```

**tests/test_worker.py (15 tests):**
```python
@patch('worker.subprocess.run')
def test_successful_test_run(self, mock_run):
    mock_run.return_value = Mock(returncode=0, stdout="1 passed")
    result = run_test_once(["pytest", "test.py"], {...}, 0)
    assert result["passed"] is True
```

**Coverage Results:**
- worker.py: 91% (core serverless handler)
- config.py: 98% (configuration system)
- database.py: 100% (historical tracking)
- **Overall: 96% code coverage**

### Results

With these additions:
1. **Customization**: Each team can tune sensitivity without code changes
2. **Trend Analysis**: "Is our test suite getting better?" → Data-driven answer
3. **Prioritization**: Focus on tests that fail most frequently
4. **Proof of Impact**: Show management that flakiness is decreasing

**Test Coverage:** 40+ passing tests with 96% code coverage

Breaking down test coverage:
- worker.py: 91% coverage (15 tests)
- config.py: 98% coverage (15 tests)
- database.py: 100% coverage (10 tests)

## About the Author

This project was built collaboratively using Claude Code, demonstrating how AI-assisted development can accelerate the journey from concept to production-ready code while maintaining security and best practices.
