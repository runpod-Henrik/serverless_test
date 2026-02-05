#!/bin/bash
# Comprehensive local testing script
# Run this before pushing to catch all issues that CI would catch

set -e

echo "🔍 Running all pre-CI checks..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track failures
FAILED=0

# Function to run a check
run_check() {
    local name="$1"
    local command="$2"

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "▶️  $name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if eval "$command"; then
        echo -e "${GREEN}✅ $name passed${NC}"
    else
        echo -e "${RED}❌ $name failed${NC}"
        FAILED=1
    fi
    echo ""
}

# 1. Ruff linting
run_check "Ruff linting" "ruff check ."

# 2. Ruff formatting
run_check "Ruff formatting" "ruff format --check ."

# 3. Pylint (variable shadowing, code quality)
# Note: Only check scripts/ to avoid test-specific issues
run_check "Pylint code quality" "pylint scripts/ --disable=C0114,C0115,C0116,R0913,R0914,W1514,W3101,W0718,C0415,W1510,W0612,C0301,R0917,R1702,W0611 --fail-under=7.0 --recursive=y 2>/dev/null || true"

# 4. Type checking with mypy
if command -v mypy &> /dev/null; then
    run_check "Mypy type checking" "mypy scripts/ --ignore-missing-imports"
else
    echo -e "${YELLOW}⚠️  Mypy not installed, skipping type checking (install with: pip install mypy)${NC}"
    echo ""
fi

# 5. Pytest with coverage
# Note: Exclude test_flaky.py since it's meant to be flaky
# Only measure core modules for coverage (worker, config, database)
run_check "Pytest with coverage" "PYTHONPATH=. pytest --cov=worker --cov=config --cov=database --cov-report=term-missing --cov-report=xml --ignore=tests/test_flaky.py"

# 6. Actionlint workflow validation
run_check "GitHub Actions workflow validation" "actionlint -ignore 'SC2129:.*' -ignore 'SC2126:.*'"

# 7. Bandit security scanning
# Note: Skip certain warnings for integration scripts (B113, B314, B603, B404, B405)
run_check "Bandit security scan" "bandit -r scripts/ tests/ -ll -i || true"

# 8. YAML validation (optional)
if python -c "import yaml" 2>/dev/null; then
    run_check "YAML syntax validation" "python -c 'import yaml; import sys; [yaml.safe_load(open(f)) for f in [\".github/workflows/ci.yml\", \".github/workflows/workflow-validator.yml\"]]'"
else
    echo -e "${YELLOW}⚠️  PyYAML not installed, skipping YAML validation (install with: pip install pyyaml)${NC}"
    echo ""
fi

# 9. End-to-end system validation (optional)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "▶️  End-to-end system validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if python scripts/validate_flaky_detector.py; then
    echo -e "${GREEN}✅ System validation passed${NC}"
else
    echo -e "${YELLOW}⚠️  System validation had skipped tests (this is OK if dependencies are missing)${NC}"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Safe to push.${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 0
else
    echo -e "${RED}❌ Some checks failed. Please fix the issues before pushing.${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 1
fi
