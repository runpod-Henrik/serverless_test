# Serverless Flaky Test Detector

A RunPod serverless function that detects flaky tests by running them multiple times in parallel with different random seeds. This tool helps identify non-deterministic test failures that can be difficult to reproduce in normal CI/CD environments.

## Features

- **Parallel Test Execution**: Run tests multiple times concurrently to quickly identify flakiness
- **Seed Randomization**: Each test run uses a unique random seed to expose timing-dependent bugs
- **Automatic Dependency Installation**: Installs requirements.txt automatically from cloned repositories
- **Comprehensive Error Handling**: Robust error handling for network issues, timeouts, and test failures
- **Resource Cleanup**: Automatic cleanup of temporary directories and working directory restoration
- **Security Hardened**: Protected against command injection with proper input validation

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

### Code Formatting

Format code with Black:

```bash
black .
```

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

## Deployment to RunPod

### Step 1: Create a Docker Image

Create a `Dockerfile` in the project root:

```dockerfile
FROM runpod/base:0.4.0-cuda11.8.0

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY worker.py .
COPY run.sh .

# Make run script executable
RUN chmod +x run.sh

# Start the worker
CMD ["bash", "run.sh"]
```

Build and push the image:

```bash
# Build the Docker image
docker build -t your-username/flaky-test-detector:latest .

# Push to Docker Hub
docker push your-username/flaky-test-detector:latest
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
