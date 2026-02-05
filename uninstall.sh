#!/bin/bash
# Flaky Test Detector - Uninstall Script
# Removes flaky test detector files from your repository

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Flaky Test Detector - Uninstall                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Confirm uninstall
echo -e "${YELLOW}This will remove flaky test detector files from your repository.${NC}"
echo ""
echo "Files that will be removed:"
echo "  • worker.py"
echo "  • config.py"
echo "  • database.py"
echo "  • validate_input.py"
echo "  • input_schema.json"
echo "  • local_test.py"
echo "  • .flaky-detector.yml"
echo "  • test_input.json"
echo "  • .github/workflows/flaky-detector-auto.yml"
echo "  • flaky_test_results.json (if exists)"
echo "  • flaky_detector.db (if exists)"
echo ""
read -p "Are you sure you want to continue? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstall cancelled."
    exit 0
fi

echo ""

# Remove files
FILES=(
    "worker.py"
    "config.py"
    "database.py"
    "validate_input.py"
    "input_schema.json"
    "local_test.py"
    ".flaky-detector.yml"
    "test_input.json"
    "flaky_test_results.json"
    "flaky_detector.db"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        rm "$file"
        print_success "Removed $file"
    fi
done

# Remove GitHub Actions workflow
if [ -f ".github/workflows/flaky-detector-auto.yml" ]; then
    rm ".github/workflows/flaky-detector-auto.yml"
    print_success "Removed .github/workflows/flaky-detector-auto.yml"
fi

# Clean up .gitignore
if [ -f ".gitignore" ]; then
    if grep -q "# Flaky Test Detector" .gitignore; then
        # Create a temp file without flaky detector entries
        grep -v "# Flaky Test Detector" .gitignore | \
        grep -v "flaky_test_results.json" | \
        grep -v "flaky_detector.db" > .gitignore.tmp
        mv .gitignore.tmp .gitignore
        print_success "Cleaned .gitignore"
    fi
fi

echo ""
echo -e "${GREEN}✓ Flaky test detector has been uninstalled${NC}"
echo ""
print_info "To remove Python dependencies, run:"
echo "  pip3 uninstall runpod pytest pyyaml jsonschema"
echo ""
