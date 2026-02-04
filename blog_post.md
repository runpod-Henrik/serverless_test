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

## The Results: Production-Ready

After all iterations, we have:

✅ **Secure** - No command injection, validated inputs
✅ **Reliable** - Resource cleanup, error handling, timeouts
✅ **Fast** - Parallel execution (50 runs in ~2 minutes)
✅ **Automated** - Triggers on CI failures, posts to PRs
✅ **Cost-Effective** - Scales to zero, ~$0.024 per test run
✅ **Multi-Channel** - PR comments + Slack notifications
✅ **Well-Documented** - Complete setup guides

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
4. **Test result parsing** - Extract specific failed test names
5. **Historical tracking** - Store results to track flakiness over time

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

- **Lines of Code:** ~1,000 (including scripts and workflows)
- **Docker Image Size:** 285 MB
- **Cold Start Time:** ~15 seconds
- **Test Execution:** 50 tests in ~2 minutes (5 parallel workers)
- **Cost per Run:** ~$0.024 (100 tests, CPU instance)
- **Development Time:** 1 day (from idea to production)

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

## About the Author

This project was built collaboratively using Claude Code, demonstrating how AI-assisted development can accelerate the journey from concept to production-ready code while maintaining security and best practices.
