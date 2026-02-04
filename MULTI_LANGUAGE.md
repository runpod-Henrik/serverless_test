# Multi-Language Test Framework Support

This guide explains how to extend the flaky test detector to support Go, TypeScript, and other test frameworks beyond Python/pytest.

## Current Architecture

The system is already framework-agnostic in key ways:
- ✅ Clones any Git repository
- ✅ Runs any shell command via `test_command`
- ✅ Uses exit codes to determine pass/fail (universal standard)
- ✅ Captures stdout/stderr (works for all frameworks)

**What needs enhancement:**
- Dependency installation (different per language)
- Seed/randomness injection (different per framework)
- Optional: Framework-specific output parsing

## Supported Frameworks

| Language | Framework | Test Command | Seed Method |
|----------|-----------|--------------|-------------|
| Python | pytest | `pytest tests/` | `TEST_SEED` env var |
| Go | go test | `go test ./...` | `GO_TEST_SEED` env var + code |
| TypeScript | Jest | `npm test` or `jest` | `JEST_SEED` env var + config |
| TypeScript | Vitest | `vitest run` | `VITE_TEST_SEED` env var |
| JavaScript | Mocha | `mocha test/` | `MOCHA_SEED` env var |

## Framework Detection

Detect framework automatically based on repository files:

```python
import os
from typing import Literal

FrameworkType = Literal["python", "go", "typescript-jest", "typescript-vitest", "javascript-mocha", "unknown"]

def detect_framework(repo_path: str) -> FrameworkType:
    """Detect test framework from repository files."""
    # Check for Go
    if os.path.exists(os.path.join(repo_path, "go.mod")):
        return "go"

    # Check for Node.js/TypeScript
    package_json = os.path.join(repo_path, "package.json")
    if os.path.exists(package_json):
        try:
            import json
            with open(package_json) as f:
                pkg = json.load(f)
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

                if "jest" in deps:
                    return "typescript-jest"
                elif "vitest" in deps:
                    return "typescript-vitest"
                elif "mocha" in deps:
                    return "javascript-mocha"
        except Exception:
            pass

    # Check for Python
    if os.path.exists(os.path.join(repo_path, "requirements.txt")) or \
       os.path.exists(os.path.join(repo_path, "pyproject.toml")) or \
       os.path.exists(os.path.join(repo_path, "setup.py")):
        return "python"

    return "unknown"
```

## Dependency Installation

Each framework needs different dependency installation:

```python
def install_dependencies(framework: FrameworkType, repo_path: str) -> None:
    """Install dependencies based on detected framework."""
    install_commands = {
        "python": ["pip", "install", "-q", "-r", "requirements.txt"],
        "go": ["go", "mod", "download"],
        "typescript-jest": ["npm", "install", "--silent"],
        "typescript-vitest": ["npm", "install", "--silent"],
        "javascript-mocha": ["npm", "install", "--silent"],
    }

    # Check if dependency file exists
    dependency_files = {
        "python": "requirements.txt",
        "go": "go.mod",
        "typescript-jest": "package.json",
        "typescript-vitest": "package.json",
        "javascript-mocha": "package.json",
    }

    if framework not in install_commands:
        return

    dep_file = dependency_files[framework]
    if not os.path.exists(os.path.join(repo_path, dep_file)):
        return

    try:
        subprocess.run(
            install_commands[framework],
            check=True,
            capture_output=True,
            timeout=300,
        )
        print(f"✓ Installed {framework} dependencies")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to install dependencies: {e.stderr}")
```

## Seed Injection Strategies

Different frameworks handle randomness differently:

### Python (pytest)

**Current implementation** - Already works:
```python
env_overrides = {
    "TEST_SEED": str(random.randint(1, 1_000_000))
}
```

In test code:
```python
import os
import random

def setup_test_seed():
    seed = int(os.environ.get('TEST_SEED', 42))
    random.seed(seed)

def test_flaky():
    setup_test_seed()
    # Test code here
```

### Go (go test)

**Environment variable approach:**
```python
env_overrides = {
    "GO_TEST_SEED": str(random.randint(1, 1_000_000))
}
```

In Go test code:
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

func TestFlaky(t *testing.T) {
    // Test uses seeded random
    value := rand.Intn(100)
    // ...
}
```

**Alternative: -seed flag** (if framework supports):
```bash
go test -seed=${GO_TEST_SEED} ./...
```

### TypeScript (Jest)

**jest.config.js:**
```javascript
module.exports = {
  // ... other config
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
};
```

**jest.setup.js:**
```javascript
// Use seed from environment variable
const seed = parseInt(process.env.JEST_SEED || '42');

// Seed Math.random (if using seedrandom package)
const seedrandom = require('seedrandom');
Math.random = seedrandom(seed);

// Or use Jest's --seed flag
// Command: jest --seed=${JEST_SEED}
```

**Environment variable:**
```python
env_overrides = {
    "JEST_SEED": str(random.randint(1, 1_000_000))
}
```

**Test command with seed flag:**
```json
{
  "test_command": "jest --seed=${JEST_SEED}"
}
```

### TypeScript (Vitest)

**vitest.config.ts:**
```typescript
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    seed: parseInt(process.env.VITE_TEST_SEED || '42'),
    // ... other config
  }
})
```

**Environment variable:**
```python
env_overrides = {
    "VITE_TEST_SEED": str(random.randint(1, 1_000_000))
}
```

### JavaScript (Mocha)

**mocha.opts or .mocharc.json:**
```json
{
  "require": "test/setup.js"
}
```

**test/setup.js:**
```javascript
const seed = parseInt(process.env.MOCHA_SEED || '42');
const seedrandom = require('seedrandom');
Math.random = seedrandom(seed);
```

**Environment variable:**
```python
env_overrides = {
    "MOCHA_SEED": str(random.randint(1, 1_000_000))
}
```

## Enhanced Worker Implementation

Here's the updated `worker.py` with multi-framework support:

```python
import os
import random
import shlex
import shutil
import subprocess
import tempfile
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Literal

import runpod

FrameworkType = Literal["python", "go", "typescript-jest", "typescript-vitest", "javascript-mocha", "unknown"]


def detect_framework(repo_path: str) -> FrameworkType:
    """Detect test framework from repository files."""
    # Check for Go
    if os.path.exists(os.path.join(repo_path, "go.mod")):
        return "go"

    # Check for Node.js/TypeScript
    package_json = os.path.join(repo_path, "package.json")
    if os.path.exists(package_json):
        try:
            with open(package_json) as f:
                pkg = json.load(f)
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

                if "jest" in deps:
                    return "typescript-jest"
                elif "vitest" in deps:
                    return "typescript-vitest"
                elif "mocha" in deps:
                    return "javascript-mocha"
        except Exception:
            pass

    # Check for Python
    if os.path.exists(os.path.join(repo_path, "requirements.txt")) or \
       os.path.exists(os.path.join(repo_path, "pyproject.toml")) or \
       os.path.exists(os.path.join(repo_path, "setup.py")):
        return "python"

    return "unknown"


def install_dependencies(framework: FrameworkType, repo_path: str) -> None:
    """Install dependencies based on detected framework."""
    install_commands = {
        "python": ["pip", "install", "-q", "-r", "requirements.txt"],
        "go": ["go", "mod", "download"],
        "typescript-jest": ["npm", "install", "--silent"],
        "typescript-vitest": ["npm", "install", "--silent"],
        "javascript-mocha": ["npm", "install", "--silent"],
    }

    # Check if dependency file exists
    dependency_files = {
        "python": "requirements.txt",
        "go": "go.mod",
        "typescript-jest": "package.json",
        "typescript-vitest": "package.json",
        "javascript-mocha": "package.json",
    }

    if framework not in install_commands:
        print(f"Framework {framework} detected but no dependency installation configured")
        return

    dep_file = dependency_files[framework]
    if not os.path.exists(os.path.join(repo_path, dep_file)):
        print(f"No {dep_file} found, skipping dependency installation")
        return

    try:
        print(f"Installing {framework} dependencies...")
        subprocess.run(
            install_commands[framework],
            check=True,
            capture_output=True,
            timeout=300,
        )
        print(f"✓ Installed {framework} dependencies")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to install dependencies: {e.stderr}")
    except subprocess.TimeoutExpired:
        print("Warning: Dependency installation timed out")


def get_seed_env_var(framework: FrameworkType, seed_value: int) -> dict[str, str]:
    """Get appropriate environment variable for seeding tests."""
    seed_vars = {
        "python": {"TEST_SEED": str(seed_value)},
        "go": {"GO_TEST_SEED": str(seed_value)},
        "typescript-jest": {"JEST_SEED": str(seed_value)},
        "typescript-vitest": {"VITE_TEST_SEED": str(seed_value)},
        "javascript-mocha": {"MOCHA_SEED": str(seed_value)},
        "unknown": {"TEST_SEED": str(seed_value)},  # Fallback
    }
    return seed_vars.get(framework, {"TEST_SEED": str(seed_value)})


def run_test_once(
    cmd_list: list[str], env_overrides: dict[str, str], attempt: int
) -> dict[str, Any]:
    """Run a single test execution."""
    env = os.environ.copy()
    env.update(env_overrides)
    try:
        result = subprocess.run(cmd_list, capture_output=True, text=True, env=env, timeout=300)
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
    """
    Expected input:
    {
      "repo": "https://github.com/org/repo",
      "test_command": "pytest tests/test_flaky.py",
      "runs": 50,
      "parallelism": 5,
      "framework": "python"  # Optional: auto-detect if not provided
    }
    """
    inp = job["input"]
    repo = inp["repo"]
    test_command = inp["test_command"]
    runs = int(inp.get("runs", 10))
    parallelism = int(inp.get("parallelism", 4))
    framework_override = inp.get("framework")  # Optional explicit framework

    # Validate input parameters
    if not repo:
        raise ValueError("Repository URL is required")
    if not test_command:
        raise ValueError("Test command is required")
    if runs < 1 or runs > 1000:
        raise ValueError("Runs must be between 1 and 1000")
    if parallelism < 1 or parallelism > 50:
        raise ValueError("Parallelism must be between 1 and 50")

    # Validate repo URL (basic check for https:// or git@)
    if not (repo.startswith("https://") or repo.startswith("git@")):
        raise ValueError(f"Invalid repository URL: {repo}")

    workdir = tempfile.mkdtemp()
    results = []
    original_cwd = os.getcwd()
    detected_framework: FrameworkType = "unknown"

    try:
        # Clone repo
        try:
            print(f"Cloning repository: {repo}")
            subprocess.run(
                ["git", "clone", repo, workdir],
                check=True,
                capture_output=True,
                text=True,
                timeout=300,
            )
            print("✓ Repository cloned successfully")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to clone repository: {e.stderr}") from e
        except subprocess.TimeoutExpired as e:
            raise RuntimeError("Repository clone timed out after 5 minutes") from e

        os.chdir(workdir)

        # Detect or use explicit framework
        if framework_override:
            detected_framework = framework_override  # type: ignore
            print(f"Using explicit framework: {detected_framework}")
        else:
            detected_framework = detect_framework(workdir)
            print(f"Detected framework: {detected_framework}")

        # Install dependencies
        install_dependencies(detected_framework, workdir)

        # Parse test command safely
        test_command_list = shlex.split(test_command)

        print(f"Running {runs} tests with parallelism {parallelism}...")

        # Run tests in parallel
        with ThreadPoolExecutor(max_workers=parallelism) as executor:
            futures = []
            for i in range(runs):
                seed = random.randint(1, 1_000_000)
                env_overrides = get_seed_env_var(detected_framework, seed)
                env_overrides["ATTEMPT"] = str(i)

                futures.append(executor.submit(run_test_once, test_command_list, env_overrides, i))

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

        print(f"✓ Completed all test runs")

    finally:
        # Restore original working directory
        os.chdir(original_cwd)
        # Clean up temporary directory
        try:
            shutil.rmtree(workdir)
        except Exception as e:
            print(f"Warning: Failed to clean up temporary directory: {e}")

    # Calculate summary
    failures = [r for r in results if not r["passed"]]
    summary = {
        "total_runs": runs,
        "parallelism": parallelism,
        "framework": detected_framework,
        "failures": len(failures),
        "repro_rate": round(len(failures) / runs, 3),
        "results": sorted(results, key=lambda r: r["attempt"]),
    }

    return summary


runpod.serverless.start({"handler": handler})
```

## Usage Examples

### Python (pytest)
```json
{
  "repo": "https://github.com/runpod-Henrik/serverless_test",
  "test_command": "pytest tests/test_flaky.py",
  "runs": 100,
  "parallelism": 10
}
```

### Go (go test)
```json
{
  "repo": "https://github.com/your-org/go-project",
  "test_command": "go test -v ./...",
  "runs": 100,
  "parallelism": 10,
  "framework": "go"
}
```

### TypeScript (Jest)
```json
{
  "repo": "https://github.com/your-org/typescript-project",
  "test_command": "npm test",
  "runs": 100,
  "parallelism": 10,
  "framework": "typescript-jest"
}
```

### TypeScript (Vitest)
```json
{
  "repo": "https://github.com/your-org/vite-project",
  "test_command": "vitest run",
  "runs": 100,
  "parallelism": 10,
  "framework": "typescript-vitest"
}
```

### JavaScript (Mocha)
```json
{
  "repo": "https://github.com/your-org/mocha-project",
  "test_command": "mocha test/",
  "runs": 100,
  "parallelism": 10,
  "framework": "javascript-mocha"
}
```

## Docker Image Updates

Update the Dockerfile to include multiple language runtimes:

```dockerfile
FROM runpod/base:0.4.0-cuda11.8.0

# Install Python
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for TypeScript/JavaScript tests
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install Go
RUN wget https://go.dev/dl/go1.22.0.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go1.22.0.linux-amd64.tar.gz && \
    rm go1.22.0.linux-amd64.tar.gz

ENV PATH="/usr/local/go/bin:${PATH}"

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY worker.py .
COPY run.sh .

# Make run script executable
RUN chmod +x run.sh

# Verify installations
RUN python3 --version && node --version && npm --version && go version

# Start the worker
CMD ["bash", "run.sh"]
```

## Configuration File Extension

Add framework-specific settings to `.flaky-detector.yml`:

```yaml
# Framework-specific configuration
framework:
  type: "auto"  # auto, python, go, typescript-jest, typescript-vitest, javascript-mocha

  # Framework-specific settings
  python:
    requirements_file: "requirements.txt"
    install_command: "pip install -r requirements.txt"

  go:
    install_command: "go mod download"

  typescript:
    install_command: "npm install"

  javascript:
    install_command: "npm install"

# Seed configuration
seed:
  env_var: "TEST_SEED"  # Override default seed variable name
  range: [1, 1000000]   # Seed value range

# Test execution
runs: 100
parallelism: 10
timeout: 300  # seconds per test run
```

## Benefits

✅ **Language Agnostic**: Support any test framework with exit-code-based pass/fail
✅ **Automatic Detection**: Detects framework from repository structure
✅ **Manual Override**: Explicitly specify framework if needed
✅ **Consistent Interface**: Same API for all languages
✅ **Parallel Execution**: Run tests concurrently regardless of language
✅ **Seed Injection**: Proper randomness seeding for each framework

## Limitations

⚠️ **Setup Required**: Test repositories must be configured to read seed environment variables
⚠️ **Framework Coverage**: Only common frameworks supported initially (extensible)
⚠️ **Build Time**: Docker image is larger with multiple runtimes (~2GB vs ~500MB)

## Next Steps

1. **Add Language Detection**: Implement framework detection logic
2. **Update Worker**: Integrate multi-framework support into worker.py
3. **Update Docker**: Build multi-language Docker image
4. **Test Each Framework**: Verify with example repos for Python, Go, TypeScript
5. **Document Per-Language**: Create setup guides for each language
6. **Add Examples**: Provide sample test repositories for each framework

## Testing Multi-Language Support

Create test repositories for each framework:

```bash
# Python example (already exists)
pytest tests/test_flaky.py

# Go example
# Create flaky_test.go
go test -v ./...

# TypeScript/Jest example
# Create __tests__/flaky.test.ts
npm test

# TypeScript/Vitest example
# Create tests/flaky.test.ts
vitest run
```

## Cost Considerations

**Docker Image Size Impact:**
- Python only: ~500MB
- Python + Node.js: ~800MB
- Python + Node.js + Go: ~1.2GB

**RunPod Storage Costs:**
- Larger images take longer to load (cold start latency)
- More disk space usage

**Recommendation**: Create separate endpoints per language if cold start is critical, or use one multi-language endpoint for simplicity.

---

**Implementation Status:** 📝 Design Complete - Ready for Implementation
**Estimated Effort:** 4-6 hours (coding) + 2-3 hours (testing each framework)
**Breaking Changes:** None - backward compatible with existing Python-only usage
