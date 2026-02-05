#!/bin/bash
# Cleanup script for migration to new repository
# Removes temporary files, caches, and redundant documentation

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Flaky Test Detector - Cleanup for Migration       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

print_step() {
    echo -e "${GREEN}▶${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Confirm cleanup
echo -e "${YELLOW}This will remove temporary files and redundant documentation.${NC}"
echo ""
echo "Files that will be removed:"
echo "  • Test scripts: test_runpod_endpoint.py, test_new_features.py"
echo "  • Cache directories: __pycache__/, .ruff_cache/, .pytest_cache/, htmlcov/"
echo "  • Coverage data: .coverage"
echo "  • Local configs: .claude/, uv.lock"
echo "  • Redundant docs: 12 documentation files"
echo ""
read -p "Continue with cleanup? [Y/n] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]] && [[ ! -z $REPLY ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""

# Remove test scripts
print_step "Removing test scripts..."
rm -f test_runpod_endpoint.py test_new_features.py
print_success "Removed test scripts"

# Remove cache directories
print_step "Removing cache directories..."
rm -rf __pycache__/ .ruff_cache/ .pytest_cache/ htmlcov/ .mypy_cache/
print_success "Removed cache directories"

# Remove coverage data
print_step "Removing coverage data..."
rm -f .coverage
print_success "Removed coverage data"

# Remove local configs
print_step "Removing local configurations..."
rm -rf .claude/
rm -f uv.lock
print_success "Removed local configurations"

# Remove generated results
print_step "Removing generated results..."
rm -f flaky_test_results.json flaky_detector.db
print_success "Removed generated results"

# Remove redundant documentation
print_step "Removing redundant documentation..."

DOCS_TO_REMOVE=(
    "docs/blog_post.md"
    "docs/CONFIGURATION.md"
    "docs/DEPENDENCIES.md"
    "docs/DEPLOYMENT.md"
    "docs/DOCUMENTATION_UPDATE_SUMMARY.md"
    "docs/EXPANSION_RECOMMENDATIONS.md"
    "docs/HISTORICAL_TRACKING.md"
    "docs/IMPROVEMENTS_SUMMARY.md"
    "docs/PROJECT_REVIEW.md"
    "docs/SETUP_SECRETS.md"
    "docs/TUTORIAL.md"
    "docs/WORKFLOW_TESTING.md"
    "docs/AI_WORKFLOW_VALIDATION.md"
)

for doc in "${DOCS_TO_REMOVE[@]}"; do
    if [ -f "$doc" ]; then
        rm "$doc"
        echo "  • Removed $(basename $doc)"
    fi
done

print_success "Removed redundant documentation"

# List remaining documentation
echo ""
print_step "Remaining documentation:"
echo ""
echo "Core Documentation:"
ls -1 docs/*.md 2>/dev/null | while read file; do
    echo "  • $(basename $file)"
done

echo ""
echo "Root Documentation:"
ls -1 *.md 2>/dev/null | while read file; do
    echo "  • $(basename $file)"
done

# Create .cleanignore for future reference
print_step "Creating .cleanignore..."
cat > .cleanignore <<EOF
# Files to exclude from clean repository
__pycache__/
.ruff_cache/
.pytest_cache/
htmlcov/
.mypy_cache/
.coverage
.claude/
uv.lock
flaky_test_results.json
flaky_detector.db
test_runpod_endpoint.py
test_new_features.py
EOF
print_success "Created .cleanignore"

# Summary
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}                    Cleanup Complete! ✓                     ${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "1. Review changes: ${BLUE}git status${NC}"
echo "2. Update references: ${BLUE}see MIGRATION.md${NC}"
echo "3. Test locally: ${BLUE}python3 local_test.py${NC}"
echo "4. Run checks: ${BLUE}./scripts/run_all_checks.sh${NC}"
echo ""
