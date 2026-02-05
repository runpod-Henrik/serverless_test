# Dependency Management

This document explains how dependencies are managed in this project.

## Version Pinning Strategy

All dependencies are **pinned to specific versions** using `==` (exact version matching) rather than `>=` (minimum version) or loose constraints.

### Why Pin Versions?

**Benefits:**
1. ✅ **Reproducibility** - Same code produces same results everywhere
2. ✅ **Stability** - No unexpected breaking changes from package updates
3. ✅ **Consistency** - Identical behavior in local, CI/CD, and production
4. ✅ **Debugging** - Easier to troubleshoot with known versions
5. ✅ **Security** - Controlled updates, review changes before adopting

**Trade-offs:**
- ⚠️ Manual updates required to get bug fixes and security patches
- ⚠️ Need to periodically review and update dependencies

### Our Choice

For a **production-ready serverless application**, stability and reproducibility outweigh the convenience of automatic updates. We prefer:
- Explicit, tested updates
- Known working versions
- No surprises in production

## Current Dependencies

### Core Dependencies (Always Installed)

| Package | Version | Purpose |
|---------|---------|---------|
| `runpod` | 1.8.1+ | RunPod serverless SDK |
| `pytest` | 7.4.0+ | Test framework |
| `PyYAML` | 6.0.0+ | YAML configuration parsing |

**Installation:** `pip install -e .` or `uv sync`

### Optional Dependencies: Dashboard

| Package | Version | Purpose |
|---------|---------|---------|
| `streamlit` | 1.40.2+ | Dashboard UI framework |
| `plotly` | 5.24.1+ | Interactive charts |
| `pandas` | 2.2.3+ | Data analysis for dashboard |

**Installation:** `pip install -e ".[dashboard]"` or `uv sync --extra dashboard`

**When to install:** Only if you plan to use the interactive dashboard (`streamlit run dashboard.py`)

### Optional Dependencies: Development Tools

| Package | Version | Purpose |
|---------|---------|---------|
| `ruff` | 0.8.4+ | Linting and formatting |
| `mypy` | 1.14.0+ | Static type checking |
| `pytest-cov` | 6.0.0+ | Pytest coverage plugin |

**Installation:** `pip install -e ".[dev]"` or `uv sync --extra dev`

**When to install:** Only if you're contributing to the project or running quality checks

### Legacy Dependencies (via requirements.txt)

For backward compatibility, `requirements.txt` includes all dependencies. However, the recommended approach is using `pyproject.toml` with optional extras.

## Updating Dependencies

### 1. Check for Updates

```bash
# See all outdated packages
pip list --outdated

# Check specific package
pip show <package-name>
```

### 2. Update a Single Package

```bash
# Update package
pip install --upgrade <package-name>

# Check new version
pip show <package-name>

# Run full test suite
pytest tests/ -v
ruff check .
mypy worker.py config.py database.py

# If all tests pass, update requirements.txt
pip freeze | grep <package-name>
# Copy the version to requirements.txt
```

### 3. Update Multiple Packages

```bash
# Update all packages (use with caution)
pip install --upgrade -r requirements.txt

# Run comprehensive tests
pytest tests/ --cov=worker --cov=config --cov=database --cov-fail-under=90
ruff check .
mypy worker.py config.py database.py

# Generate new requirements.txt
pip freeze > requirements-new.txt

# Review changes
diff requirements.txt requirements-new.txt

# If satisfied, replace
mv requirements-new.txt requirements.txt
```

### 4. Test in CI Before Merging

Create a PR to test dependency updates:

```bash
git checkout -b update-dependencies
git add requirements.txt
git commit -m "Update dependencies to latest versions"
git push -u origin update-dependencies
```

Create PR → Wait for CI to pass → Merge if green ✅

## Security Updates

### Monitoring

Use tools to check for security vulnerabilities:

```bash
# Using pip-audit (install first: pip install pip-audit)
pip-audit

# Using safety (install first: pip install safety)
safety check
```

### GitHub Dependabot

Consider enabling [Dependabot](https://docs.github.com/en/code-security/dependabot) for automatic security updates:

Create `.github/dependabot.yml`:
```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
```

### When to Update Immediately

Update immediately if:
- 🔴 Security vulnerability discovered (CVE published)
- 🔴 Critical bug fix affecting your use case
- 🟡 Important feature you need

Can wait for:
- 🟢 Minor version updates
- 🟢 Performance improvements
- 🟢 New features you don't use

## Installation

### Fresh Install

```bash
# Clone repository
git clone https://github.com/runpod-Henrik/serverless_test.git
cd serverless_test

# Install exact versions
pip install -r requirements.txt
```

### Verify Installation

```bash
# Check all packages are correct versions
pip freeze | grep -E "runpod|pytest|pyyaml|streamlit|plotly|pandas|ruff|mypy|coverage"

# Run tests to verify everything works
pytest tests/ -v
```

## Virtual Environments

Always use virtual environments to isolate dependencies:

### Using venv

```bash
# Create virtual environment
python3 -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Using uv (faster alternative)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create and activate environment
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
```

## Docker Considerations

The Dockerfile uses the same pinned versions:

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

**Benefits:**
- ✅ Same versions in container as in development
- ✅ Reproducible Docker image builds
- ✅ No layer cache invalidation from version changes

## Troubleshooting

### Dependency Conflicts

**Error:** `ERROR: pip's dependency resolver does not currently take into account all the packages that are installed.`

**Solution:**
```bash
# Start fresh
pip uninstall -y -r requirements.txt
pip install -r requirements.txt
```

### Version Not Available

**Error:** `ERROR: Could not find a version that satisfies the requirement package==1.2.3`

**Possible causes:**
- Package version was yanked/removed
- Typo in version number
- Package renamed

**Solution:**
```bash
# Check available versions
pip index versions <package-name>

# Update to available version
# Edit requirements.txt with available version
pip install -r requirements.txt
```

### Platform-Specific Issues

Some packages have platform-specific wheels:

```bash
# Force reinstall for current platform
pip install --force-reinstall --no-cache-dir -r requirements.txt
```

## Best Practices

1. ✅ **Always pin versions** in requirements.txt
2. ✅ **Test updates** in CI before deploying
3. ✅ **Review changelogs** before updating
4. ✅ **Use virtual environments** to isolate projects
5. ✅ **Document breaking changes** when updating
6. ✅ **Monitor security advisories** for your dependencies
7. ✅ **Update regularly** (don't let dependencies get too stale)
8. ✅ **Keep a changelog** of dependency updates

## Version History

Track major dependency updates:

| Date | Package | Old Version | New Version | Reason |
|------|---------|-------------|-------------|--------|
| 2026-02-04 | Initial | - | All pinned | Production release |

Update this table when making significant dependency changes.

## References

- [pip Documentation](https://pip.pypa.io/en/stable/)
- [Python Packaging Guide](https://packaging.python.org/)
- [Semantic Versioning](https://semver.org/)
- [pip-audit](https://github.com/pypa/pip-audit)
- [Safety](https://github.com/pyupio/safety)

---

**Last Updated:** 2026-02-04
**Python Version:** 3.12+
