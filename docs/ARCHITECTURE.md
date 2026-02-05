# Architecture Documentation

This document describes the architecture, design decisions, and component interactions of the Flaky Test Detector system.

## System Overview

The Flaky Test Detector is a serverless application that detects flaky tests by running them multiple times in parallel and analyzing failure patterns. It's designed to run on RunPod's serverless infrastructure but can also execute locally for development and testing.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Entry Points                            │
├─────────────────┬──────────────────┬────────────────────────┤
│  local_test.py  │  RunPod Handler  │  GitHub Actions CI     │
│  (Development)  │  (Production)    │  (Auto-trigger)        │
└────────┬────────┴────────┬─────────┴──────────┬─────────────┘
         │                 │                    │
         └─────────────────┼────────────────────┘
                          ▼
         ┌─────────────────────────────────────┐
         │      worker.py (Core Handler)       │
         │                                     │
         │  • Validate input                   │
         │  • Clone/copy repository            │
         │  • Detect framework                 │
         │  • Install dependencies             │
         │  • Run tests in parallel            │
         │  • Aggregate results                │
         └──────┬──────────────────────────────┘
                │
        ┌───────┴────────┐
        │                │
        ▼                ▼
┌──────────────┐  ┌──────────────┐
│  config.py   │  │ database.py  │
│              │  │              │
│ • Load YAML  │  │ • Store runs │
│ • Thresholds │  │ • Trends     │
│ • Patterns   │  │ • Statistics │
└──────────────┘  └──────────────┘
        │                │
        └────────┬───────┘
                 ▼
      ┌─────────────────────┐
      │   validate_input.py  │
      │                      │
      │  • Schema validation │
      │  • Input sanitization│
      └─────────────────────┘
```

## Core Components

### 1. Worker Module (`worker.py`)

**Purpose**: Main orchestration logic for running tests and detecting flakiness.

**Key Functions**:
- `handler(job)` - Entry point for RunPod serverless invocation
- `run_test_once(cmd, env, attempt)` - Execute a single test run
- `detect_framework(repo_path)` - Auto-detect test framework
- `install_dependencies(framework, repo_path)` - Install required packages
- `get_seed_env_var(framework, seed)` - Generate framework-specific seed variables

**Data Flow**:
```
Input → Validation → Clone/Copy Repo → Detect Framework
  ↓
Install Dependencies → Change Directory → Spawn Thread Pool
  ↓
Run Tests in Parallel → Collect Results → Calculate Statistics
  ↓
Cleanup → Return Summary
```

**Design Decisions**:
- **ThreadPoolExecutor**: Uses threads (not processes) for parallelism because tests run in separate processes anyway
- **Temporary Directories**: Each invocation uses a fresh temp directory to avoid state pollution
- **Working Directory Management**: Saves and restores CWD to ensure cleanup doesn't break
- **Timeout Handling**: 5-minute timeout per test run to prevent hanging
- **Local Path Support**: Can use local directories instead of cloning for faster development iteration

### 2. Configuration Module (`config.py`)

**Purpose**: Manage per-repository configuration and severity thresholds.

**Configuration File** (`.flaky-detector.yml`):
```yaml
# Test execution
runs: 100
parallelism: 10
timeout: 600

# CI Integration
auto_trigger_on_failure: true
auto_trigger_runs: 20
auto_trigger_parallelism: 5

# Severity thresholds (0.0-1.0)
severity_thresholds:
  critical: 0.9   # >90% failure = likely real bug
  high: 0.5       # 50-90% = very unstable
  medium: 0.1     # 10-50% = clear flaky behavior
  low: 0.01       # 1-10% = occasional flakiness
```

**Key Features**:
- Default values with override support
- Nested configuration merging
- Pattern-based test filtering
- Severity level calculation based on reproduction rate

**Design Decisions**:
- Uses YAML for human readability
- Optional configuration (works without file)
- Repository-specific settings via committed `.flaky-detector.yml`

### 3. Database Module (`database.py`)

**Purpose**: Track test results over time for trend analysis.

**Schema**:
```sql
CREATE TABLE test_runs (
    id INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    repository TEXT NOT NULL,
    test_command TEXT NOT NULL,
    total_runs INTEGER NOT NULL,
    failures INTEGER NOT NULL,
    repro_rate REAL NOT NULL,
    parallelism INTEGER,
    framework TEXT,
    results_json TEXT  -- Full results for detailed analysis
)
```

**Key Features**:
- Stores complete run history
- Query by repository, date range, or command
- Calculate trends over time
- Find most flaky tests
- Statistics aggregation

**Design Decisions**:
- SQLite for simplicity and portability
- JSON column for detailed results (flexibility)
- Indexed queries for performance
- Context manager for automatic cleanup

### 4. Validation Module (`validate_input.py`)

**Purpose**: Validate and sanitize user input before processing.

**Validation Layers**:
1. **JSON Schema**: Primary validation using jsonschema library
2. **Fallback Validation**: Basic checks when jsonschema unavailable
3. **Runtime Validation**: Additional checks in worker.py

**Schema** (`input_schema.json`):
- Required fields: repo, test_command
- Optional fields: runs (1-1000), parallelism (1-50), framework
- Type checking and range validation
- No additional properties allowed

**Design Decisions**:
- Fail fast with clear error messages
- Dual validation approach (schema + fallback)
- Security-focused: prevents command injection, validates URLs

### 5. Local Test Runner (`local_test.py`)

**Purpose**: Development tool to run flaky detector without RunPod infrastructure.

**Features**:
- Simulates RunPod job format
- Loads configuration from `test_input.json`
- Validates input before execution
- Displays formatted results
- Saves detailed output to JSON

**Design Decisions**:
- Uses `importlib.util` to load worker without starting serverless
- Adds project directory to `sys.path` for import resolution
- Absolute paths for cross-directory invocation

## Framework Support

### Multi-Language Architecture

The system supports multiple test frameworks through:

1. **Auto-Detection** (`detect_framework`)
2. **Dependency Installation** (`install_dependencies`)
3. **Seed Variables** (`get_seed_env_var`)

### Supported Frameworks

| Language   | Framework | Detection          | Seed Variable    |
|------------|-----------|-------------------|------------------|
| Python     | pytest    | requirements.txt   | TEST_SEED        |
| Go         | testing   | go.mod            | GO_TEST_SEED     |
| TypeScript | Jest      | jest in package   | JEST_SEED        |
| TypeScript | Vitest    | vitest in package | VITE_TEST_SEED   |
| JavaScript | Mocha     | mocha in package  | MOCHA_SEED       |

### Adding New Frameworks

To add a new framework:

1. **Update `FrameworkType`** literal in `worker.py`:
```python
FrameworkType = Literal[
    "python", "go", "typescript-jest", "typescript-vitest",
    "javascript-mocha", "rust-cargo", "unknown"  # Add here
]
```

2. **Add detection logic** in `detect_framework()`:
```python
def detect_framework(repo_path: str) -> FrameworkType:
    # Check for Rust
    if os.path.exists(os.path.join(repo_path, "Cargo.toml")):
        return "rust-cargo"
    # ... existing checks ...
```

3. **Add install command** in `install_dependencies()`:
```python
install_commands = {
    "rust-cargo": ["cargo", "fetch"],
    # ... existing commands ...
}
dependency_files = {
    "rust-cargo": "Cargo.toml",
    # ... existing files ...
}
```

4. **Add seed variable** in `get_seed_env_var()`:
```python
seed_vars = {
    "rust-cargo": {"CARGO_TEST_SEED": str(seed_value)},
    # ... existing vars ...
}
```

5. **Update schema** in `input_schema.json`:
```json
"framework": {
  "enum": [
    "python", "go", "typescript-jest",
    "typescript-vitest", "javascript-mocha",
    "rust-cargo"
  ]
}
```

## Security Architecture

### Input Validation

**Threat Model**:
- Command injection via test_command
- Path traversal via repo path
- Resource exhaustion via runs/parallelism
- Arbitrary code execution via malicious repos

**Mitigations**:
1. **Command Execution**: Uses list arguments (not shell=True)
   ```python
   subprocess.run(["git", "clone", repo, workdir])  # Safe
   subprocess.run(f"git clone {repo} {workdir}", shell=True)  # Dangerous
   ```

2. **Input Sanitization**: JSON schema validates all inputs
   - Runs: 1-1000 (prevents resource exhaustion)
   - Parallelism: 1-50 (prevents fork bombs)
   - Repo: Must be valid URL or local path

3. **Shlex Parsing**: Test commands parsed safely
   ```python
   test_command_list = shlex.split(test_command)  # Handles quotes correctly
   ```

4. **Path Validation**: Repository paths checked before use
   ```python
   if not is_local_path and not (repo.startswith("https://") or repo.startswith("git@")):
       raise ValueError(f"Invalid repository URL or path: {repo}")
   ```

5. **Temporary Directories**: Isolated execution environment
   - Each run gets fresh temp directory
   - Automatic cleanup on completion
   - No persistent state between runs

### CI/CD Integration Security

**Auto-Trigger Workflow** (`.github/workflows/flaky-detector-auto.yml`):

**Security Measures**:
- Runs only on PR test failures (not arbitrary events)
- Limited permissions: `pull-requests: write`, `contents: read`
- No secret exposure in logs
- Rate limiting via workflow concurrency
- Validates config before execution

**Threat Mitigations**:
- **Fork PRs**: Workflow runs in base repo context (secure)
- **Malicious Config**: YAML parsing with safe_load
- **Resource Abuse**: Configurable limits via .flaky-detector.yml

## Performance Considerations

### Parallelism Strategy

**Thread Pool vs Process Pool**:
- Uses `ThreadPoolExecutor` (not `ProcessPoolExecutor`)
- Rationale: Tests spawn their own processes, no CPU-bound work in Python
- Benefits: Lower overhead, faster startup, simpler state management

**Parallelism Limits**:
- Default: 4 workers (balanced for most systems)
- Maximum: 50 workers (prevents resource exhaustion)
- Configurable per repository

### Resource Management

**Memory**:
- Each test run captures stdout/stderr (can be large)
- Mitigated by: Stream capture, not full buffer
- Database: JSON results can be compressed

**Disk**:
- Repository cloning can be large
- Mitigated by: Temp directory cleanup
- Option: Shallow clones for large repos

**Network**:
- Repository cloning is network-intensive
- Mitigated by: Local path support for development
- Future: Cache cloned repositories

### Optimization Opportunities

1. **Repository Caching**: Cache cloned repos between runs
2. **Shallow Clones**: Use `--depth=1` for faster cloning
3. **Result Streaming**: Stream results instead of buffering all
4. **Incremental Testing**: Only re-run changed tests
5. **Distributed Execution**: Scale to multiple workers

## Design Decisions & Trade-offs

### 1. Temporary Directories vs Persistent Workspace

**Decision**: Use temporary directories

**Rationale**:
- ✅ Clean slate each run (no state pollution)
- ✅ Automatic cleanup
- ✅ Multiple runs can execute concurrently
- ❌ Slower (clone every time)
- ❌ Higher disk I/O

**Alternative**: Persistent workspace with git pull
- ✅ Faster (no re-clone)
- ❌ Requires locking
- ❌ Stale dependencies
- ❌ Dirty working directory

### 2. Threads vs Processes

**Decision**: ThreadPoolExecutor

**Rationale**:
- ✅ Lower overhead
- ✅ Faster startup
- ✅ Easier state management
- ✅ Tests run in their own processes anyway
- ❌ GIL limits CPU-bound work (not an issue here)

### 3. SQLite vs Cloud Database

**Decision**: SQLite

**Rationale**:
- ✅ Zero configuration
- ✅ File-based (easy backup)
- ✅ Sufficient performance for use case
- ✅ No external dependencies
- ❌ Not distributed
- ❌ Limited concurrency

**Alternative**: PostgreSQL/MySQL
- ✅ Better concurrency
- ✅ Distributed access
- ❌ Requires separate service
- ❌ More complex setup

### 4. Auto-Detection vs Explicit Framework

**Decision**: Auto-detection with explicit override

**Rationale**:
- ✅ Better UX (less configuration)
- ✅ Works for 90% of cases
- ✅ Override available for edge cases
- ❌ Can detect wrong framework
- ❌ Detection logic requires maintenance

### 5. JSON Schema vs Manual Validation

**Decision**: JSON Schema with fallback

**Rationale**:
- ✅ Declarative and maintainable
- ✅ Self-documenting
- ✅ Fallback for edge cases
- ✅ Better error messages
- ❌ Extra dependency

## Extension Points

### 1. Custom Reporters

Add new output formats by implementing reporter interface:

```python
class Reporter:
    def generate_report(self, results: dict) -> str:
        """Generate report from test results."""
        pass

# Example: Markdown reporter
class MarkdownReporter(Reporter):
    def generate_report(self, results: dict) -> str:
        total = results["total_runs"]
        failures = results["failures"]
        rate = results["repro_rate"]

        return f"""
## Test Results
- Total Runs: {total}
- Failures: {failures}
- Reproduction Rate: {rate:.1%}
        """
```

### 2. Custom Frameworks

Add support for new frameworks by extending the framework detection system (see "Adding New Frameworks" above).

### 3. Custom Notifications

Integrate with notification services:

```python
def send_notification(results: dict, webhook_url: str):
    """Send results to external service."""
    import requests

    severity = get_severity(results["repro_rate"])
    message = format_notification(results, severity)

    requests.post(webhook_url, json={"text": message})
```

### 4. Result Analyzers

Add custom analysis of test results:

```python
def analyze_pattern(results: list[dict]) -> dict:
    """Analyze test failure patterns."""
    # Look for timing patterns
    # Identify flaky vs deterministic failures
    # Suggest root causes
    return {
        "pattern": "timing-dependent",
        "confidence": 0.85,
        "suggestion": "Check for race conditions"
    }
```

## Deployment Architecture

### Local Development

```
Developer Machine
├── local_test.py (entry point)
├── worker.py (business logic)
└── test_input.json (configuration)
```

### RunPod Serverless

```
RunPod Pod
├── Docker Container
│   ├── worker.py (handler)
│   ├── requirements.txt
│   └── Python 3.12+
├── Temp Storage (ephemeral)
└── Network Access (git clone)
```

### GitHub Actions CI

```
GitHub Runner
├── Workflow: ci.yml
│   ├── Lint and Type Check
│   ├── Test Suite
│   └── System Validation
├── Workflow: flaky-detector-auto.yml
│   ├── Trigger on test failure
│   ├── Run flaky detector
│   └── Post PR comment
└── Artifacts (coverage, results)
```

## Future Architecture Considerations

### Potential Enhancements

1. **Distributed Execution**
   - Run tests across multiple workers
   - Coordinate via message queue
   - Aggregate results centrally

2. **Smart Test Selection**
   - Only run tests affected by changes
   - Prioritize historically flaky tests
   - Skip deterministic passing tests

3. **Result Caching**
   - Cache results by git commit hash
   - Skip re-running identical tests
   - Invalidate on dependency changes

4. **Real-time Monitoring**
   - WebSocket-based progress updates
   - Live result streaming
   - Dashboard integration

5. **ML-based Analysis**
   - Predict flakiness likelihood
   - Identify root cause patterns
   - Suggest fixes automatically

## Conclusion

The Flaky Test Detector is designed for:
- **Simplicity**: Minimal dependencies, easy setup
- **Reliability**: Defensive coding, comprehensive testing
- **Extensibility**: Clear extension points
- **Performance**: Parallel execution, efficient resource use
- **Security**: Input validation, safe command execution

The architecture balances these concerns while maintaining a clean, maintainable codebase suitable for both local development and production deployment.
