# Flaky Test Detector - Documentation

Complete documentation for understanding, installing, and using the flaky test detector.

## 📚 Documentation Index

### Getting Started

| Document | Description | For |
|----------|-------------|-----|
| **[Getting Started](GETTING_STARTED.md)** | Quick setup guide (5 minutes) | New users |
| **[Quick Reference](QUICK_REFERENCE.md)** | Command cheat sheet | Everyone |
| **[Configuration Guide](../TEST_INPUT_FILES.md)** | Complete config reference | Power users |

### Guides

| Document | Description | For |
|----------|-------------|-----|
| **[RunPod Deployment](RUNPOD_TUTORIAL.md)** | Deploy to RunPod serverless platform | RunPod users |
| **[Debugging Test Failures](DEBUGGING_TEST_FAILURES.md)** | Complete workflow for fixing failures | Developers |
| **[CI/CD Integration](CICD_INTEGRATION.md)** | GitHub Actions setup & auto-trigger | DevOps |
| **[Multi-Language Support](MULTI_LANGUAGE.md)** | Supporting different frameworks | Multi-language teams |

### Reference

| Document | Description | For |
|----------|-------------|-----|
| **[Architecture](ARCHITECTURE.md)** | System design & internals | Contributors |
| **[Quality Checks](QUALITY_CHECKS.md)** | Code quality tools | Contributors |
| **[Preventing CI Failures](PREVENTING_CI_FAILURES.md)** | Multi-layer defense system | All developers |

## 🚀 Quick Start

```bash
# 1. Run automated setup
bash setup.sh

# 2. Test it out
python3 local_test.py

# 3. Check results
cat flaky_test_results.json | jq '.repro_rate'
```

**See [Getting Started](GETTING_STARTED.md) for detailed instructions.**

## 📖 Documentation by Use Case

### I want to...

#### ...get started quickly
→ [Getting Started Guide](GETTING_STARTED.md)

#### ...deploy to RunPod serverless
→ [RunPod Deployment Tutorial](RUNPOD_TUTORIAL.md)

#### ...debug a failing CI test
→ [Debugging Test Failures Guide](DEBUGGING_TEST_FAILURES.md)

#### ...set up auto-detection in CI
→ [CI/CD Integration Guide](CICD_INTEGRATION.md)

#### ...configure for my framework
→ [Multi-Language Support](MULTI_LANGUAGE.md)

#### ...understand how it works
→ [Architecture Documentation](ARCHITECTURE.md)

#### ...contribute to the project
→ [Quality Checks](QUALITY_CHECKS.md) + [Architecture](ARCHITECTURE.md)

#### ...prevent CI failures
→ [Preventing CI Failures](PREVENTING_CI_FAILURES.md)

#### ...customize thresholds
→ [Configuration Guide](../TEST_INPUT_FILES.md)

#### ...see all commands
→ [Quick Reference](QUICK_REFERENCE.md)

## 📋 Key Concepts

### Flaky Test
A test that sometimes passes and sometimes fails without code changes. Usually caused by:
- Race conditions
- Timing dependencies
- External state
- Non-deterministic behavior

### Reproduction Rate
Percentage of test runs that fail. Helps distinguish:
- **100% failure** = Real bug, not flaky
- **50-90% failure** = Very unstable
- **10-50% failure** = Clear flakiness
- **<10% failure** = Occasional issues

### Auto-Trigger
Automatically runs flaky detector when PR tests fail, providing immediate feedback on whether the failure is flaky or real.

### Severity Thresholds
Configurable thresholds in `.flaky-detector.yml` that determine severity levels based on reproduction rate.

## 🔧 Configuration Files

### `.flaky-detector.yml`
Repository-specific configuration committed to git. Controls default behavior, thresholds, and CI integration.

**Location**: Repository root
**Documentation**: [Configuration Guide](../TEST_INPUT_FILES.md)

### `test_input.json`
Test run configuration for `local_test.py`. Specifies what tests to run and how many times.

**Location**: Repository root (or custom with `-i` flag)
**Documentation**: [Configuration Guide](../TEST_INPUT_FILES.md)

### `input_schema.json`
JSON schema defining valid input structure. Used for validation.

**Location**: Repository root
**Documentation**: Built-in validation

## 🛠️ Tools & Scripts

### Core Tools

| Tool | Purpose | Documentation |
|------|---------|---------------|
| `local_test.py` | Run detector locally | [Getting Started](GETTING_STARTED.md) |
| `worker.py` | Main detection logic | [Architecture](ARCHITECTURE.md) |
| `setup.sh` | Automated installation | [Getting Started](GETTING_STARTED.md) |
| `uninstall.sh` | Remove detector | Built-in help |

### Helper Scripts

| Script | Purpose | Location |
|--------|---------|----------|
| `run_all_checks.sh` | Run all quality checks | `scripts/` |
| `validate_flaky_detector.py` | System validation | `scripts/` |
| Workflow validation | Check GitHub Actions | `scripts/workflow_utils/` |

## 🎯 Workflows

### 1. Debugging Workflow
```
CI Fails → Run Flaky Detector → Check Repro Rate → Fix or Stabilize
```
**Guide**: [Debugging Test Failures](DEBUGGING_TEST_FAILURES.md)

### 2. PR Workflow
```
Submit PR → Tests Fail → Auto-Detector Runs → Comment on PR → Fix
```
**Guide**: [CI/CD Integration](CICD_INTEGRATION.md)

### 3. Development Workflow
```
Write Test → Run Locally → Detect Flakiness → Fix → Commit
```
**Guide**: [Getting Started](GETTING_STARTED.md)

## 💡 Best Practices

### Configuration
1. Start with **20-50 runs** for quick validation
2. Use **100+ runs** for conclusive results
3. Adjust **parallelism** based on CPU cores
4. Enable **auto-trigger** for immediate feedback

### Testing
1. Test **specific failing tests** first, not entire suite
2. Use **local paths** during development for speed
3. Run **comprehensive checks** before pushing
4. Enable **verbose mode** when debugging

### CI Integration
1. Set up **auto-trigger** for automatic analysis
2. Use **PR comments** for team visibility
3. Track **trends** with database
4. Configure **severity thresholds** for your needs

## 📊 Metrics & Analysis

### Key Metrics
- **Reproduction Rate**: % of runs that fail
- **Execution Time**: Time to run all tests
- **Severity Level**: Based on configured thresholds
- **Framework**: Auto-detected test framework

### Viewing Results
```bash
# Summary
cat flaky_test_results.json | jq '{repro_rate, failures, total_runs}'

# All failures
cat flaky_test_results.json | jq '.results[] | select(.passed == false)'

# First failure
cat flaky_test_results.json | jq '.results[] | select(.passed == false) | .stderr' | head -1
```

## 🔗 External Resources

- **GitHub Repository**: https://github.com/runpod/testflake
- **RunPod Documentation**: https://docs.runpod.io/
- **Issue Tracker**: https://github.com/runpod/testflake/issues

## 📝 Contributing

Want to contribute? Great!

1. Read [Architecture](ARCHITECTURE.md) to understand the system
2. Check [Quality Checks](QUALITY_CHECKS.md) for development standards
3. Run `./scripts/run_all_checks.sh` before submitting
4. Follow existing patterns and style

## 🆘 Getting Help

### Quick Help
```bash
# Command help
python3 local_test.py --help

# View configuration
cat .flaky-detector.yml

# Check logs
python3 local_test.py -v
```

### Common Issues
See [Troubleshooting](GETTING_STARTED.md#troubleshooting) in Getting Started

### Support Channels
- **Documentation**: You're reading it!
- **Issues**: GitHub issue tracker
- **Examples**: `tests/` directory

---

## 📑 Document Summaries

### Getting Started (5 min read)
Quick installation and first run. Perfect for new users.

### Quick Reference (2 min read)
Command cheat sheet and common scenarios. Keep it handy!

### Configuration Guide (10 min read)
Complete reference for all configuration options and fields.

### Debugging Guide (15 min read)
Complete workflow from test failure to fix. Includes AI-assisted analysis.

### CI/CD Integration (10 min read)
GitHub Actions setup, auto-trigger configuration, and PR workflows.

### Architecture (30 min read)
Deep dive into system design, security, performance, and extension points.

### Quality Checks (15 min read)
Development tools, pre-commit hooks, and quality standards.

### Multi-Language Support (10 min read)
Framework detection, language-specific configuration, and examples.

### Preventing CI Failures (10 min read)
Multi-layer defense system to catch issues before CI.

---

**Happy testing!** 🎉
