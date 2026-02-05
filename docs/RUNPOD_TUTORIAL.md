# RunPod Deployment Tutorial

Complete guide to deploying and using the Flaky Test Detector on RunPod's serverless platform.

## Table of Contents

1. [Why RunPod?](#why-runpod)
2. [Quick Start](#quick-start)
3. [Deployment Guide](#deployment-guide)
4. [Use Cases](#use-cases)
5. [Configuration](#configuration)
6. [Cost Optimization](#cost-optimization)
7. [Troubleshooting](#troubleshooting)

## Why RunPod?

**RunPod's serverless platform is ideal for flaky test detection:**

- ⚡ **Instant Scaling**: Spin up 100 workers in seconds
- 💰 **Pay Per Second**: Only pay when tests are running
- 🚀 **High Performance**: GPU or CPU instances based on your needs
- 🌍 **Global**: Low-latency endpoints worldwide
- 🔧 **Easy Integration**: Simple REST API and Python SDK

**Cost Example:**
- 100 test runs in parallel
- 2 minutes execution time
- ~$0.024 per detection run
- Only charged for actual compute time

## Quick Start

### Prerequisites

- RunPod account (free tier available)
- Docker Hub account
- Git and Docker installed locally

### 5-Minute Setup

```bash
# 1. Clone and build
git clone https://github.com/runpod/testflake.git
cd testflake
docker build -t your-dockerhub-username/testflake:latest .

# 2. Push to Docker Hub
docker login
docker push your-dockerhub-username/testflake:latest

# 3. Deploy on RunPod (see Deployment Guide below)

# 4. Test it
python3 local_test.py  # Or use RunPod SDK
```

## Deployment Guide

### Step 1: Build Your Docker Image

Choose the right image for your needs:

#### Option A: Multi-Language Support (Default)

Supports Python, Go, TypeScript, and JavaScript tests.

```bash
# Build
docker build -t your-dockerhub-username/testflake:latest .

# Test locally
docker run -p 8000:8000 your-dockerhub-username/testflake:latest

# Push to registry
docker push your-dockerhub-username/testflake:latest
```

**Image size:** ~2.1 GB
**Supports:** Python, Go, TypeScript/Jest, TypeScript/Vitest, JavaScript/Mocha

#### Option B: Python-Only (Smaller)

For Python/pytest projects only.

```bash
# Build
docker build -f Dockerfile.python-only -t your-dockerhub-username/testflake:python .

# Push
docker push your-dockerhub-username/testflake:python
```

**Image size:** ~1.5 GB
**Supports:** Python/pytest only

### Step 2: Create RunPod Endpoint

1. **Sign up for RunPod**
   - Go to https://runpod.io
   - Create account (free tier available)
   - Add payment method for serverless

2. **Navigate to Serverless**
   - Click "Serverless" in left sidebar
   - Click "+ New Endpoint"

3. **Configure Endpoint**

   **Basic Settings:**
   ```
   Name: testflake
   Docker Image: your-dockerhub-username/testflake:latest
   Container Disk: 10 GB
   ```

   **Container Configuration:**
   ```
   Container Start Command: ./run.sh
   Expose HTTP Ports: 8000
   ```

   **Worker Configuration:**
   ```
   Min Workers: 0  (scale to zero when idle)
   Max Workers: 10 (adjust based on needs)
   GPUs per Worker: 0 (CPU is sufficient)
   Idle Timeout: 30 seconds
   ```

   **Advanced Settings:**
   ```
   Environment Variables:
     PYTHONUNBUFFERED=1
     GIT_TERMINAL_PROMPT=0
   ```

4. **Deploy**
   - Click "Deploy"
   - Wait for deployment (1-2 minutes)
   - Note your endpoint ID (e.g., `tmi5oesd1cmsjw`)

### Step 3: Get Your Credentials

1. **API Key**
   - Go to: https://www.runpod.io/console/user/settings
   - Find "API Keys" section
   - Create new key: "testflake-detector"
   - Copy and save securely

2. **Endpoint ID**
   - Go to "Serverless" dashboard
   - Find your endpoint
   - Copy the endpoint ID from the URL or settings

3. **Save Credentials**
   ```bash
   # Add to your environment
   export RUNPOD_API_KEY="your-api-key-here"
   export RUNPOD_ENDPOINT_ID="your-endpoint-id-here"

   # Or add to ~/.bashrc or ~/.zshrc for persistence
   echo 'export RUNPOD_API_KEY="your-api-key"' >> ~/.bashrc
   echo 'export RUNPOD_ENDPOINT_ID="your-endpoint-id"' >> ~/.bashrc
   ```

### Step 4: Test Your Endpoint

**Using Python SDK:**

```python
import runpod

# Configure
runpod.api_key = "your-api-key"

# Simple test
job = runpod.Endpoint("your-endpoint-id").run(
    {
        "repo": "https://github.com/runpod/testflake",
        "test_command": "pytest tests/test_flaky.py -v",
        "runs": 20,
        "parallelism": 5
    }
)

# Wait for results
result = job.output()
print(f"Failure rate: {result['repro_rate']*100}%")
```

**Using cURL:**

```bash
curl -X POST https://api.runpod.ai/v2/your-endpoint-id/run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "input": {
      "repo": "https://github.com/runpod/testflake",
      "test_command": "pytest tests/test_flaky.py",
      "runs": 20,
      "parallelism": 5
    }
  }'
```

**Expected Response:**

```json
{
  "id": "job-123abc",
  "status": "IN_QUEUE"
}
```

**Check Status:**

```bash
curl https://api.runpod.ai/v2/your-endpoint-id/status/job-123abc \
  -H "Authorization: Bearer your-api-key"
```

## Use Cases

### Use Case 1: CI/CD Pipeline Integration

**Scenario:** Automatically detect flaky tests when CI fails

**Setup:**

1. Add GitHub secrets:
   ```bash
   gh secret set RUNPOD_API_KEY --body "your-api-key"
   gh secret set RUNPOD_ENDPOINT_ID --body "your-endpoint-id"
   ```

2. The `.github/workflows/flaky-detector-auto.yml` workflow will:
   - Trigger when CI tests fail
   - Run failing tests 100x on RunPod
   - Post results to PR with severity
   - Upload detailed artifacts

**Example PR Comment:**

```markdown
## 🟡 MEDIUM: Flaky Test Detected

**Reproduction Rate:** 35.0%
- Total Runs: 100
- Failed: 35
- Passed: 65

**Analysis:**
This test shows intermittent flakiness. Consider:
- Check for race conditions
- Review timing dependencies
- Look for shared state issues

**Recommendation:** Stabilize before merging
```

**Cost:** ~$0.024 per detection (100 runs, 2 min)

### Use Case 2: Pre-Merge Validation

**Scenario:** Validate test stability before merging PRs

**Python Script:**

```python
import runpod
import sys

def validate_tests(repo_url, test_path, threshold=0.05):
    """
    Validate test stability before merge.

    Args:
        repo_url: Repository URL
        test_path: Path to tests
        threshold: Max acceptable failure rate (default 5%)

    Returns:
        bool: True if tests are stable
    """
    runpod.api_key = "your-api-key"

    print(f"🔍 Validating tests: {test_path}")

    job = runpod.Endpoint("your-endpoint-id").run({
        "repo": repo_url,
        "test_command": f"pytest {test_path} -v",
        "runs": 100,
        "parallelism": 20
    })

    result = job.output()
    rate = result['repro_rate']

    print(f"\n📊 Results:")
    print(f"   Runs: {result['total_runs']}")
    print(f"   Failures: {result['failures']}")
    print(f"   Rate: {rate*100:.1f}%")

    if rate > threshold:
        print(f"\n❌ UNSTABLE: {rate*100:.1f}% > {threshold*100}%")
        return False
    else:
        print(f"\n✅ STABLE: {rate*100:.1f}% ≤ {threshold*100}%")
        return True

# Usage
if __name__ == "__main__":
    stable = validate_tests(
        repo_url="https://github.com/your-org/your-repo",
        test_path="tests/integration/",
        threshold=0.05  # 5% max failure rate
    )
    sys.exit(0 if stable else 1)
```

**In CI:**

```yaml
- name: Validate test stability
  run: |
    python scripts/validate_stability.py
  env:
    RUNPOD_API_KEY: ${{ secrets.RUNPOD_API_KEY }}
    RUNPOD_ENDPOINT_ID: ${{ secrets.RUNPOD_ENDPOINT_ID }}
```

### Use Case 3: Nightly Flakiness Reports

**Scenario:** Monitor test suite health over time

**Python Script:**

```python
import runpod
from datetime import datetime
import json

def nightly_flakiness_check():
    """Run comprehensive flakiness check on entire test suite."""
    runpod.api_key = "your-api-key"

    test_suites = [
        "tests/unit/",
        "tests/integration/",
        "tests/e2e/"
    ]

    results = {
        "timestamp": datetime.now().isoformat(),
        "suites": []
    }

    for suite in test_suites:
        print(f"\n🔍 Testing: {suite}")

        job = runpod.Endpoint("your-endpoint-id").run({
            "repo": "https://github.com/your-org/your-repo",
            "test_command": f"pytest {suite} -v",
            "runs": 50,
            "parallelism": 10
        })

        result = job.output()

        suite_result = {
            "suite": suite,
            "repro_rate": result['repro_rate'],
            "failures": result['failures'],
            "total_runs": result['total_runs'],
            "status": get_severity(result['repro_rate'])
        }

        results["suites"].append(suite_result)

        print(f"   Rate: {result['repro_rate']*100:.1f}%")
        print(f"   Status: {suite_result['status']}")

    # Save results
    with open(f"flakiness-report-{datetime.now():%Y%m%d}.json", "w") as f:
        json.dump(results, f, indent=2)

    # Send to monitoring system (optional)
    # send_to_datadog(results)
    # send_to_slack(results)

    return results

def get_severity(rate):
    """Determine severity based on reproduction rate."""
    if rate >= 0.9:
        return "CRITICAL"
    elif rate >= 0.5:
        return "HIGH"
    elif rate >= 0.1:
        return "MEDIUM"
    elif rate >= 0.01:
        return "LOW"
    else:
        return "NONE"

if __name__ == "__main__":
    nightly_flakiness_check()
```

**Schedule in GitHub Actions:**

```yaml
name: Nightly Flakiness Check

on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM UTC daily
  workflow_dispatch:     # Manual trigger

jobs:
  flakiness-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run flakiness check
        run: python scripts/nightly_flakiness.py
        env:
          RUNPOD_API_KEY: ${{ secrets.RUNPOD_API_KEY }}
          RUNPOD_ENDPOINT_ID: ${{ secrets.RUNPOD_ENDPOINT_ID }}

      - name: Upload report
        uses: actions/upload-artifact@v4
        with:
          name: flakiness-report
          path: flakiness-report-*.json
```

### Use Case 4: Race Condition Detection

**Scenario:** Find race conditions in concurrent code

```python
import runpod

def detect_race_conditions(test_file, runs=500):
    """
    Detect race conditions with high-volume testing.

    More runs = higher chance of catching rare race conditions.
    """
    runpod.api_key = "your-api-key"

    print(f"🏁 Testing for race conditions: {test_file}")
    print(f"   Runs: {runs}")
    print(f"   This may take a few minutes...\n")

    job = runpod.Endpoint("your-endpoint-id").run({
        "repo": "https://github.com/your-org/your-repo",
        "test_command": f"pytest {test_file} -v -x",  # Stop on first failure
        "runs": runs,
        "parallelism": 50  # High parallelism to expose race conditions
    })

    result = job.output()

    if result['failures'] > 0:
        print(f"⚠️  RACE CONDITION DETECTED")
        print(f"   Failed: {result['failures']}/{runs}")
        print(f"   Rate: {result['repro_rate']*100:.1f}%")
        print(f"\n🔍 First failure:")

        # Find first failure
        for r in result['results']:
            if not r['passed']:
                print(r['stderr'][:500])  # First 500 chars
                break
    else:
        print(f"✅ No race conditions detected in {runs} runs")

    return result

# Usage
detect_race_conditions(
    "tests/test_concurrent_operations.py",
    runs=500
)
```

### Use Case 5: Load Testing with Different Seeds

**Scenario:** Test behavior under various random conditions

```python
import runpod

def seed_variation_testing():
    """
    Test with multiple seed configurations to find
    seed-dependent flakiness.
    """
    runpod.api_key = "your-api-key"

    seed_ranges = [
        (0, 99),
        (100, 199),
        (200, 299),
        (300, 399),
        (400, 499)
    ]

    results = []

    for start, end in seed_ranges:
        print(f"\n🎲 Testing seeds {start}-{end}")

        job = runpod.Endpoint("your-endpoint-id").run({
            "repo": "https://github.com/your-org/your-repo",
            "test_command": "pytest tests/test_random_behavior.py -v",
            "runs": 100,
            "parallelism": 20
        })

        result = job.output()
        results.append({
            "seed_range": f"{start}-{end}",
            "repro_rate": result['repro_rate'],
            "failures": result['failures']
        })

        print(f"   Rate: {result['repro_rate']*100:.1f}%")

    # Analyze results
    print("\n📊 Seed Variation Analysis:")
    for r in results:
        print(f"   {r['seed_range']}: {r['repro_rate']*100:.1f}% failure")

    avg_rate = sum(r['repro_rate'] for r in results) / len(results)
    print(f"\n   Average: {avg_rate*100:.1f}%")

    return results

# Usage
seed_variation_testing()
```

## Configuration

### Environment Variables

Set these in your RunPod endpoint configuration:

```bash
# Python optimization
PYTHONUNBUFFERED=1

# Git configuration
GIT_TERMINAL_PROMPT=0
GIT_SSH_COMMAND=ssh -o StrictHostKeyChecking=no

# Custom configurations
TEST_TIMEOUT=600          # Max test duration (seconds)
MAX_PARALLELISM=50        # Max parallel workers
```

### Endpoint Settings

**Recommended Configuration:**

```yaml
Min Workers: 0              # Scale to zero when idle
Max Workers: 10-20          # Based on expected load
GPU Type: None (CPU)        # CPU sufficient for most tests
Container Disk: 10-20 GB    # Depends on repo size
Idle Timeout: 30 seconds    # Quick scale down
Max Concurrency: 10         # Requests per worker
```

**Cost Considerations:**

- **Min Workers = 0**: Save costs when idle (recommended)
- **Max Workers**: Higher = faster parallel testing, higher costs
- **Container Disk**: Larger repos need more space
- **Idle Timeout**: Lower = faster scale down, more cold starts

### Input Configuration

**Standard Configuration:**

```json
{
  "repo": "https://github.com/your-org/your-repo",
  "test_command": "pytest tests/",
  "runs": 50,
  "parallelism": 10
}
```

**High-Confidence Configuration:**

```json
{
  "repo": "https://github.com/your-org/your-repo",
  "test_command": "pytest tests/integration/ -v",
  "runs": 200,
  "parallelism": 20
}
```

**Quick Check Configuration:**

```json
{
  "repo": "https://github.com/your-org/your-repo",
  "test_command": "pytest tests/test_specific.py::test_function",
  "runs": 20,
  "parallelism": 5
}
```

## Cost Optimization

### Understanding RunPod Pricing

**Serverless Pricing Model:**
- Charged per second of compute time
- No charge when workers are idle (Min Workers = 0)
- CPU instances: ~$0.0002/second
- GPU instances: More expensive, usually not needed

**Example Costs:**

| Configuration | Duration | Cost |
|--------------|----------|------|
| 100 runs, 10 parallel | 2 min | $0.024 |
| 200 runs, 20 parallel | 2 min | $0.048 |
| 500 runs, 50 parallel | 2 min | $0.120 |

### Cost Optimization Tips

1. **Use Appropriate Parallelism**
   ```python
   # Too low: Slow, but not cheaper (still paying for duration)
   "parallelism": 5   # 100 runs = 4 min

   # Optimal: Fast execution, minimal cost
   "parallelism": 20  # 100 runs = 1 min

   # Too high: Marginal gains, higher overhead
   "parallelism": 50  # 100 runs = 1 min (similar to 20)
   ```

2. **Scale Runs Based on Confidence Needed**
   ```python
   # Quick check (low confidence)
   "runs": 20   # $0.005

   # Standard detection
   "runs": 100  # $0.024

   # High confidence
   "runs": 500  # $0.120
   ```

3. **Set Min Workers = 0**
   - Saves costs during idle periods
   - Only pay when tests are running
   - Slight cold start delay (1-2 seconds)

4. **Use CPU Instances**
   - Sufficient for test execution
   - Much cheaper than GPU
   - Better cost/performance ratio

5. **Optimize Test Command**
   ```python
   # Test specific failing test
   "test_command": "pytest tests/test_checkout.py::test_payment -v"

   # Not entire suite
   # "test_command": "pytest tests/ -v"  # More expensive
   ```

### Cost Monitoring

**Track Spending:**

```python
import runpod

# Get job cost
job = runpod.Endpoint("your-endpoint-id").run(input_data)
result = job.output()

# Estimate cost (approximate)
duration_seconds = 120  # From job metrics
cost_per_second = 0.0002
estimated_cost = duration_seconds * cost_per_second

print(f"Estimated cost: ${estimated_cost:.4f}")
```

## Troubleshooting

### Issue: Endpoint Not Responding

**Symptoms:**
- Requests timeout
- 503 Service Unavailable
- No workers available

**Solutions:**

1. **Check Endpoint Status**
   ```bash
   # View in RunPod dashboard
   # Serverless → Your Endpoint → Status
   ```

2. **Increase Max Workers**
   - Go to endpoint settings
   - Increase "Max Workers" to 10-20

3. **Check Worker Logs**
   - RunPod Dashboard → Logs
   - Look for startup errors

4. **Verify Docker Image**
   ```bash
   # Test locally
   docker run -p 8000:8000 your-image:latest
   curl http://localhost:8000/health
   ```

### Issue: Tests Fail on RunPod But Pass Locally

**Symptoms:**
- All tests fail with same error
- Different behavior than local

**Solutions:**

1. **Check Dependencies**
   ```python
   # Add debug logging to worker.py
   print("Python version:", sys.version)
   print("Installed packages:", subprocess.run(["pip", "list"]))
   ```

2. **Verify Repository Access**
   - Ensure repo is public or SSH keys configured
   - Check git clone works: `git clone <repo-url>`

3. **Check System Dependencies**
   ```dockerfile
   # Add to Dockerfile
   RUN apt-get update && apt-get install -y \
       build-essential \
       libpq-dev \
       # other system deps
   ```

4. **Review Environment Variables**
   - Check if tests need specific env vars
   - Add to RunPod endpoint configuration

### Issue: High Costs

**Symptoms:**
- Unexpected charges
- Workers not scaling down

**Solutions:**

1. **Check Min Workers**
   ```
   Should be: Min Workers = 0
   ```

2. **Verify Idle Timeout**
   ```
   Should be: 30-60 seconds
   ```

3. **Review Request Volume**
   - Check number of runs per request
   - Reduce parallelism if needed

4. **Monitor Usage**
   ```bash
   # Check RunPod dashboard
   # Serverless → Analytics
   ```

### Issue: Slow Execution

**Symptoms:**
- Tests take longer than expected
- Jobs queued for long time

**Solutions:**

1. **Increase Max Workers**
   - More workers = more concurrent execution
   - Settings → Max Workers = 20

2. **Increase Parallelism**
   ```json
   {
     "parallelism": 20  // Up from 10
   }
   ```

3. **Check Container Resources**
   - Increase CPU allocation
   - Increase memory if needed

4. **Optimize Test Command**
   ```bash
   # Add flags for faster execution
   "test_command": "pytest tests/ -n auto --tb=short"
   ```

### Issue: Repository Clone Failures

**Symptoms:**
- "Failed to clone repository"
- Authentication errors

**Solutions:**

1. **For Public Repos:**
   ```bash
   # Verify URL is correct
   "repo": "https://github.com/owner/repo"
   ```

2. **For Private Repos:**
   ```bash
   # Option A: Use personal access token
   "repo": "https://TOKEN@github.com/owner/repo"

   # Option B: Configure SSH keys in Docker image
   # Add to Dockerfile:
   RUN mkdir -p /root/.ssh
   COPY id_rsa /root/.ssh/id_rsa
   RUN chmod 600 /root/.ssh/id_rsa
   ```

3. **Check Git Configuration**
   ```dockerfile
   # Add to Dockerfile
   RUN git config --global user.email "bot@example.com"
   RUN git config --global user.name "Test Bot"
   ```

### Getting Help

**RunPod Support:**
- Documentation: https://docs.runpod.io
- Discord: https://discord.gg/runpod
- Support tickets: support@runpod.io

**Project Issues:**
- GitHub Issues: https://github.com/runpod/testflake/issues
- Documentation: https://github.com/runpod/testflake/docs

## Advanced Topics

### Custom Docker Images

**Add Custom Dependencies:**

```dockerfile
FROM python:3.12-slim

# Your custom system packages
RUN apt-get update && apt-get install -y \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Your custom Python packages
COPY requirements.txt requirements-custom.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements-custom.txt

# Rest of setup
COPY worker.py run.sh .
RUN chmod +x run.sh

CMD ["./run.sh"]
```

### Webhook Integration

**Receive Results via Webhook:**

```python
import runpod

# Start async job with webhook
job = runpod.Endpoint("your-endpoint-id").run_async(
    input_data,
    webhook="https://your-server.com/webhook"
)

# Your webhook endpoint receives:
# POST /webhook
# {
#   "id": "job-123",
#   "status": "COMPLETED",
#   "output": { /* results */ }
# }
```

### Batch Processing

**Process Multiple Repositories:**

```python
import runpod
from concurrent.futures import ThreadPoolExecutor

def test_repo(repo_url):
    """Test a single repository."""
    job = runpod.Endpoint("your-endpoint-id").run({
        "repo": repo_url,
        "test_command": "pytest tests/ -v",
        "runs": 50,
        "parallelism": 10
    })
    return job.output()

# Test multiple repos in parallel
repos = [
    "https://github.com/org/repo1",
    "https://github.com/org/repo2",
    "https://github.com/org/repo3"
]

with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(test_repo, repos))

# Process results
for repo, result in zip(repos, results):
    print(f"{repo}: {result['repro_rate']*100:.1f}% failure")
```

## Best Practices

1. **Start Small**
   - Begin with 20-50 runs
   - Increase based on results

2. **Target Specific Tests**
   - Test failing tests, not entire suite
   - Use pytest markers to filter

3. **Monitor Costs**
   - Check RunPod dashboard regularly
   - Set up billing alerts

4. **Use Configuration Files**
   - Add `.flaky-detector.yml` to repos
   - Standardize settings across team

5. **Automate Detection**
   - Integrate with CI/CD
   - Set up nightly checks

6. **Save Results**
   - Use database for historical tracking
   - Generate trend reports

7. **Share Findings**
   - Post results to PRs
   - Notify team via Slack

## Next Steps

- **[CI/CD Integration](CICD_INTEGRATION.md)** - Automate detection in your pipeline
- **[Configuration Guide](../TEST_INPUT_FILES.md)** - Customize behavior
- **[Multi-Language Support](MULTI_LANGUAGE.md)** - Test Go, TypeScript, JavaScript
- **[Quick Reference](QUICK_REFERENCE.md)** - Command cheat sheet

---

**Ready to deploy?** Follow the [Deployment Guide](#deployment-guide) above to get started!
