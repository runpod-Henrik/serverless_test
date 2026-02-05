# RunPod Deployment Guide

This guide walks you through deploying the flaky test detector to RunPod.

## Prerequisites

- Docker installed locally
- Docker Hub account (or other container registry)
- RunPod account with credits

## Step 1: Build the Docker Image

Replace `YOUR_DOCKERHUB_USERNAME` with your actual Docker Hub username:

```bash
# Build the image
docker build -t YOUR_DOCKERHUB_USERNAME/flaky-test-detector:latest .

# Test the image locally (optional)
docker run --rm YOUR_DOCKERHUB_USERNAME/flaky-test-detector:latest
```

## Step 2: Push to Docker Hub

```bash
# Login to Docker Hub
docker login

# Push the image
docker push YOUR_DOCKERHUB_USERNAME/flaky-test-detector:latest
```

## Step 3: Deploy on RunPod

### Option A: Using the RunPod Web UI

1. Go to https://www.runpod.io/console/serverless
2. Click **"New Endpoint"**
3. Configure your endpoint:

   **Basic Settings:**
   - Name: `flaky-test-detector`
   - Docker Image: `YOUR_DOCKERHUB_USERNAME/flaky-test-detector:latest`
   - Container Disk: `10 GB`

   **GPU Selection:**
   - For most test suites: Select **CPU** (cheapest option)
   - For GPU-dependent tests: Select appropriate GPU

   **Scaling Configuration:**
   - Workers: `0` (scale to zero when idle)
   - Max Workers: `3-5` (based on expected load)
   - GPU Type: CPU or GPU as needed
   - Idle Timeout: `30 seconds`

   **Advanced Settings (Optional):**
   - Environment Variables: Add any needed env vars
   - Active Workers: Leave at `0` for auto-scaling

4. Click **"Deploy"**

5. Wait for deployment (usually 2-3 minutes)

6. **Copy your Endpoint ID** - you'll need this for CI/CD integration

### Option B: Using the RunPod API

```bash
# Set your RunPod API key
export RUNPOD_API_KEY="your-api-key-here"

# Create endpoint via API
curl -X POST https://api.runpod.io/v2/endpoints \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -d '{
    "name": "flaky-test-detector",
    "image": "YOUR_DOCKERHUB_USERNAME/flaky-test-detector:latest",
    "gpu_type": "CONTAINER",
    "workers_min": 0,
    "workers_max": 5,
    "idle_timeout": 30
  }'
```

## Step 4: Test Your Endpoint

### Using Python

```python
import runpod

runpod.api_key = "your-runpod-api-key"

# Test the endpoint
endpoint = runpod.Endpoint("your-endpoint-id")
job = endpoint.run({
    "repo": "https://github.com/runpod-Henrik/serverless_test",
    "test_command": "pytest tests/test_flaky.py",
    "runs": 50,
    "parallelism": 5
})

# Wait for results
result = job.output(timeout=300)
print(result)
```

### Using cURL

```bash
curl -X POST https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY" \
  -d '{
    "input": {
      "repo": "https://github.com/runpod-Henrik/serverless_test",
      "test_command": "pytest tests/test_flaky.py",
      "runs": 50,
      "parallelism": 5
    }
  }'
```

## Step 5: Configure CI/CD Integration

Once deployed, add these secrets to your GitHub repository:

1. Go to: `Repository Settings` → `Secrets and variables` → `Actions`

2. Add secrets:
   - `RUNPOD_API_KEY`: Your RunPod API key
   - `RUNPOD_ENDPOINT_ID`: The endpoint ID from step 3
   - `SLACK_WEBHOOK_URL`: (Optional) Your Slack webhook URL

3. The GitHub Actions workflow will now automatically trigger on test failures!

## Monitoring and Management

### View Logs

```bash
# Using RunPod CLI
runpod logs YOUR_ENDPOINT_ID

# Or view in the web UI
# https://www.runpod.io/console/serverless/user/endpoints/YOUR_ENDPOINT_ID
```

### Update the Deployment

When you make changes to the code:

```bash
# Rebuild and push
docker build -t YOUR_DOCKERHUB_USERNAME/flaky-test-detector:latest .
docker push YOUR_DOCKERHUB_USERNAME/flaky-test-detector:latest

# RunPod will automatically pull the new image on next cold start
# Or force update in the web UI: Endpoint → Settings → "Update Image"
```

### Cost Optimization

**Current configuration costs:**
- Idle: **$0/hour** (scales to zero)
- Active: ~$0.0002/second per worker on CPU
- Typical test run (100 tests, 2 minutes): ~$0.024

**Optimization tips:**
1. Use CPU instead of GPU for non-GPU tests
2. Set aggressive idle timeout (30 seconds)
3. Limit max workers based on expected concurrent usage
4. Use spot instances if available

### Scaling Recommendations

| Usage Pattern | Min Workers | Max Workers | Idle Timeout |
|---------------|-------------|-------------|--------------|
| Personal/Small Team | 0 | 2 | 30s |
| Medium Team | 0 | 5 | 60s |
| Large Team/Enterprise | 1 | 10+ | 120s |

## Troubleshooting

### Image Build Fails

**Error**: `failed to solve: failed to compute cache key`

**Solution**: Check .dockerignore and ensure requirements.txt exists

### Deployment Fails

**Error**: `Failed to pull image`

**Solutions**:
- Verify image is public on Docker Hub
- Check image name spelling
- Ensure image was successfully pushed

### Endpoint Returns Errors

**Error**: `Repository clone failed`

**Solutions**:
- For private repos: Add deploy keys or use GitHub tokens
- Check repository URL is correct and accessible
- Verify git is installed in the Docker image

### High Costs

**Problem**: Unexpected charges

**Solutions**:
- Check idle timeout is set (prevents workers staying active)
- Verify min workers is 0 (allows scaling to zero)
- Review max workers setting
- Check for stuck jobs in the dashboard

## Getting Your RunPod API Key

1. Go to https://www.runpod.io/console/user/settings
2. Navigate to **API Keys** section
3. Click **"Create API Key"**
4. Name it: `flaky-test-detector`
5. Copy the key (you won't be able to see it again!)
6. Store it securely in GitHub Secrets

## Security Best Practices

1. **Never commit API keys** to git
2. **Use GitHub Secrets** for all credentials
3. **Rotate API keys** periodically
4. **Limit endpoint access** with RunPod's access controls
5. **Review logs regularly** for suspicious activity

## Support

- RunPod Documentation: https://docs.runpod.io/
- RunPod Discord: https://discord.gg/runpod
- Repository Issues: https://github.com/runpod-Henrik/serverless_test/issues

## Next Steps

After deployment:
1. ✅ Test endpoint with sample job
2. ✅ Configure GitHub Actions secrets
3. ✅ Create a test PR to verify CI/CD integration
4. ✅ Monitor costs and adjust scaling
5. ✅ Set up Slack notifications (optional)
