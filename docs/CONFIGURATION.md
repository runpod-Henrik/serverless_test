# Configuration Guide

## Configuration File Support

You can customize flaky test detector behavior by adding a `.flaky-detector.yml` file to your repository root.

### Basic Example

```yaml
# .flaky-detector.yml
runs: 150
parallelism: 15
timeout: 900
```

### Full Configuration Reference

```yaml
# Test execution settings
runs: 10                    # Number of times to run each test (default: 10, max: 1000)
parallelism: 4              # Number of parallel workers (default: 4, max: 50)
timeout: 300                # Timeout in seconds for test execution (default: 300)

# Test command configuration
test_command: "pytest tests/ -v"  # Override default test command

# Patterns to ignore (tests that won't be checked for flakiness)
ignore_patterns:
  - "test_known_flaky_*"      # Glob patterns
  - "*_integration_test"
  - "test_slow_*"

# Severity thresholds (0.0 to 1.0)
severity_thresholds:
  critical: 0.9   # >90% failure rate = likely a real bug
  high: 0.5       # 50-90% failure rate = very unstable
  medium: 0.1     # 10-50% failure rate = clear flaky behavior
  low: 0.01       # 1-10% failure rate = occasional flakiness

# Dependency installation
auto_install_dependencies: true
pip_install_timeout: 300

# Resource management
cleanup_on_failure: true
preserve_temp_dir: false    # Keep temp directory for debugging

# Reporting
save_full_output: false      # Save full stdout/stderr for all runs
max_error_length: 200        # Truncate errors longer than this

# Advanced options
random_seed_range:
  min: 1
  max: 1000000
```

## Configuration Options Explained

### Test Execution

- **runs**: How many times to execute the test. Higher numbers = more accurate flakiness detection
- **parallelism**: How many tests to run simultaneously. Higher = faster, but uses more resources
- **timeout**: Maximum time (seconds) for the entire job

### Ignore Patterns

Use glob patterns to skip certain tests:

```yaml
ignore_patterns:
  - "test_known_flaky_*"    # Skip tests starting with test_known_flaky_
  - "*integration*"          # Skip any test with "integration" in the name
  - "test_external_api"      # Skip specific test
```

### Severity Thresholds

Customize when tests are classified as flaky:

```yaml
severity_thresholds:
  critical: 0.9   # Default: >90% failure
  high: 0.5       # Default: 50-90% failure
  medium: 0.1     # Default: 10-50% failure
  low: 0.01       # Default: 1-10% failure
```

**Example:** To be more sensitive to flakiness:
```yaml
severity_thresholds:
  critical: 0.95
  high: 0.7
  medium: 0.05   # Catch tests that fail just 5% of the time
  low: 0.001
```

### Dependency Installation

Control how dependencies are installed:

```yaml
auto_install_dependencies: true   # Automatically pip install requirements.txt
pip_install_timeout: 300          # Max seconds for pip install
```

### Resource Management

```yaml
cleanup_on_failure: true      # Clean up temp files even if job fails
preserve_temp_dir: false      # Set to true for debugging
```

### Reporting Options

```yaml
save_full_output: false       # Save complete stdout/stderr for all runs
max_error_length: 200         # Truncate error messages longer than this
```

**Note:** Setting `save_full_output: true` will significantly increase result size.

## Usage Examples

### Example 1: High-Sensitivity Detection

For catching even rare flakiness:

```yaml
runs: 200
parallelism: 20
severity_thresholds:
  medium: 0.02   # Flag tests that fail just 2% of the time
  low: 0.001
```

### Example 2: Fast Feedback

For quick checks during development:

```yaml
runs: 30
parallelism: 10
timeout: 300
```

### Example 3: Production Verification

For thorough pre-release testing:

```yaml
runs: 500
parallelism: 25
timeout: 1800
save_full_output: true
```

### Example 4: Ignore Known Issues

Skip tests with known flakiness:

```yaml
ignore_patterns:
  - "test_legacy_*"
  - "test_external_api_*"
  - "*_known_flaky"
```

## Per-Repository Configuration

Each repository can have its own `.flaky-detector.yml` with custom settings. The configuration is loaded when the repository is cloned during test execution.

## Priority

Configuration is loaded in this order (later overrides earlier):

1. Default configuration (built-in)
2. Repository `.flaky-detector.yml` file
3. Job input parameters (if provided)

## Validation

Invalid configuration values will fall back to defaults with a warning. Valid ranges:

- `runs`: 1-1000
- `parallelism`: 1-50
- `timeout`: 1-3600 seconds
- `severity_thresholds`: 0.0-1.0

## Best Practices

1. **Start conservative**: Begin with default settings
2. **Tune for your needs**: Adjust based on your test suite characteristics
3. **Document your choices**: Add comments explaining custom thresholds
4. **Version control**: Commit `.flaky-detector.yml` to your repository
5. **Review regularly**: Update thresholds as your test suite improves

## Troubleshooting

### Configuration not loading

- Check file is named exactly `.flaky-detector.yml` (note the leading dot)
- Verify YAML syntax is valid (use a YAML validator)
- Check file is in repository root, not a subdirectory

### Tests still marked as flaky despite ignore patterns

- Verify pattern syntax (use glob patterns, not regex)
- Test pattern matching locally with `fnmatch` in Python
- Check test name matches exactly (case-sensitive)

### Thresholds not working as expected

- Remember thresholds are inclusive (>= operator)
- Values must be between 0.0 and 1.0
- Check repro_rate in results to see actual failure rate

## Support

For questions or issues with configuration:
- Check this guide first
- Review example configurations in repository
- Open an issue on GitHub with your config file
