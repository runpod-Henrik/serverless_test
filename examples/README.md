# Example Input Configurations

This directory contains example input configurations for testing different programming languages and test frameworks with the Serverless Flaky Test Detector.

## Available Examples

### Python (pytest)
**File:** `../input.json` (root directory)

```json
{
  "repo": "https://github.com/runpod-Henrik/serverless_test",
  "test_command": "pytest tests/test_flaky.py",
  "runs": 100,
  "parallelism": 8
}
```

**Framework detection:** Automatic (detects `requirements.txt`)

---

### Go (go test)
**File:** `input_go.json`

```json
{
  "repo": "https://github.com/your-org/go-project",
  "test_command": "go test -v ./...",
  "runs": 100,
  "parallelism": 10,
  "framework": "go"
}
```

**Requirements:**
- Repository must have `go.mod`
- Tests should read `GO_TEST_SEED` environment variable

**Example Go test setup:**
```go
package mypackage

import (
    "math/rand"
    "os"
    "strconv"
    "testing"
)

func init() {
    if seedStr := os.Getenv("GO_TEST_SEED"); seedStr != "" {
        if seed, err := strconv.ParseInt(seedStr, 10, 64); err == nil {
            rand.Seed(seed)
        }
    }
}
```

---

### TypeScript (Jest)
**File:** `input_typescript_jest.json`

```json
{
  "repo": "https://github.com/your-org/typescript-project",
  "test_command": "npm test",
  "runs": 100,
  "parallelism": 10,
  "framework": "typescript-jest"
}
```

**Requirements:**
- Repository must have `package.json` with Jest dependency
- Configure Jest to use seed from `JEST_SEED` environment variable

**Example Jest setup (`jest.setup.js`):**
```javascript
const seed = parseInt(process.env.JEST_SEED || '42');
const seedrandom = require('seedrandom');
Math.random = seedrandom(seed);
```

**Jest config (`jest.config.js`):**
```javascript
module.exports = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  // ... other config
};
```

---

### TypeScript (Vitest)
**File:** `input_typescript_vitest.json`

```json
{
  "repo": "https://github.com/your-org/vite-project",
  "test_command": "vitest run",
  "runs": 100,
  "parallelism": 10,
  "framework": "typescript-vitest"
}
```

**Requirements:**
- Repository must have `package.json` with Vitest dependency
- Configure Vitest to use seed from `VITE_TEST_SEED` environment variable

**Example Vitest config (`vitest.config.ts`):**
```typescript
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    seed: parseInt(process.env.VITE_TEST_SEED || '42'),
    // ... other config
  }
})
```

---

## Usage

### Local Testing

```bash
# Python example (default)
python -c "import json; import runpod; print(runpod.run_sync('endpoint-id', json.load(open('../input.json'))))"

# Go example
python -c "import json; import runpod; print(runpod.run_sync('endpoint-id', json.load(open('examples/input_go.json'))))"

# TypeScript/Jest example
python -c "import json; import runpod; print(runpod.run_sync('endpoint-id', json.load(open('examples/input_typescript_jest.json'))))"
```

### Using RunPod SDK

```python
import runpod
import json

runpod.api_key = "your-api-key"

# Load example config
with open('examples/input_go.json') as f:
    config = json.load(f)

# Run job
job = runpod.Endpoint("your-endpoint-id").run(config)
result = job.output()
print(result)
```

### Using cURL

```bash
# Go example
curl -X POST https://api.runpod.ai/v2/your-endpoint-id/run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-runpod-api-key" \
  -d @examples/input_go.json
```

## Creating Your Own Configuration

1. Copy one of the example files
2. Replace `repo` with your repository URL
3. Update `test_command` to match your test command
4. Adjust `runs` and `parallelism` as needed
5. Optionally specify `framework` (auto-detected if omitted)

## Framework Auto-Detection

If you omit the `framework` parameter, the system will auto-detect based on repository files:

- **Go**: Presence of `go.mod`
- **TypeScript/Jest**: `package.json` with `jest` dependency
- **TypeScript/Vitest**: `package.json` with `vitest` dependency
- **Python**: Presence of `requirements.txt`, `pyproject.toml`, or `setup.py`

## Advanced Configuration

For more advanced configuration options, see:
- [MULTI_LANGUAGE.md](../MULTI_LANGUAGE.md) - Multi-language support guide
- [CONFIGURATION.md](../CONFIGURATION.md) - Configuration file reference
- [README.md](../README.md) - Main documentation

## Troubleshooting

### Tests Not Using Seed

Ensure your tests are configured to read the appropriate environment variable:
- Python: `TEST_SEED`
- Go: `GO_TEST_SEED`
- Jest: `JEST_SEED`
- Vitest: `VITE_TEST_SEED`

### Dependency Installation Fails

Check that your repository has the correct dependency file:
- Python: `requirements.txt`
- Go: `go.mod`
- TypeScript/JavaScript: `package.json`

### Framework Not Detected

Explicitly specify the framework in your input configuration:
```json
{
  "framework": "go"  // or "python", "typescript-jest", etc.
}
```

## Contributing

To add examples for new frameworks:
1. Create a new `input_<framework>.json` file
2. Update this README with setup instructions
3. Submit a pull request
