#!/bin/bash
# Flaky Test Detector - Quick Setup Script
# This script helps you add flaky test detection to your repository

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          Flaky Test Detector - Quick Setup                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to print step
print_step() {
    echo -e "${GREEN}▶${NC} $1"
}

# Function to print info
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Function to print error
print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Check if running in a git repository
check_git_repo() {
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "Not in a git repository!"
        echo "Please run this script from the root of your git repository."
        exit 1
    fi
    print_success "Running in a git repository"
}

# Check Python version
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed!"
        echo "Please install Python 3.8 or later."
        exit 1
    fi

    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_success "Python $PYTHON_VERSION found"

    # Check if version is >= 3.8
    if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'; then
        print_error "Python 3.8 or later is required!"
        exit 1
    fi
}

# Detect test framework
detect_framework() {
    print_step "Detecting test framework..."

    FRAMEWORK=""

    if [ -f "go.mod" ]; then
        FRAMEWORK="go"
        TEST_COMMAND="go test ./..."
    elif [ -f "package.json" ]; then
        if grep -q '"jest"' package.json 2>/dev/null; then
            FRAMEWORK="typescript-jest"
            TEST_COMMAND="npm test"
        elif grep -q '"vitest"' package.json 2>/dev/null; then
            FRAMEWORK="typescript-vitest"
            TEST_COMMAND="npm test"
        elif grep -q '"mocha"' package.json 2>/dev/null; then
            FRAMEWORK="javascript-mocha"
            TEST_COMMAND="npm test"
        else
            FRAMEWORK="javascript"
            TEST_COMMAND="npm test"
        fi
    elif [ -f "requirements.txt" ] || [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
        FRAMEWORK="python"
        TEST_COMMAND="pytest tests/"
    else
        FRAMEWORK="unknown"
        TEST_COMMAND=""
    fi

    if [ "$FRAMEWORK" != "unknown" ]; then
        print_success "Detected framework: $FRAMEWORK"
    else
        print_warning "Could not auto-detect framework"
    fi
}

# Interactive configuration
interactive_config() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}                     Configuration                          ${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""

    # Test command
    echo -e "${GREEN}?${NC} What command runs your tests?"
    echo "  (e.g., pytest tests/, go test ./..., npm test)"
    read -p "  → " -e -i "$TEST_COMMAND" USER_TEST_COMMAND
    TEST_COMMAND="${USER_TEST_COMMAND:-$TEST_COMMAND}"

    # Default runs
    echo ""
    echo -e "${GREEN}?${NC} How many times should tests run to detect flakiness?"
    echo "  (recommended: 20-50 for local, 100+ for CI)"
    read -p "  → " -e -i "50" RUNS

    # Default parallelism
    echo ""
    echo -e "${GREEN}?${NC} How many parallel workers?"
    echo "  (recommended: 4-10 based on CPU cores)"
    read -p "  → " -e -i "5" PARALLELISM

    # Auto-trigger
    echo ""
    echo -e "${GREEN}?${NC} Enable auto-trigger on test failures in CI?"
    echo "  (automatically runs flaky detector when PR tests fail)"
    read -p "  → [Y/n] " -e -i "Y" AUTO_TRIGGER
    AUTO_TRIGGER="${AUTO_TRIGGER:-Y}"
}

# Create .flaky-detector.yml
create_config() {
    print_step "Creating .flaky-detector.yml configuration..."

    AUTO_TRIGGER_VALUE="true"
    if [[ "$AUTO_TRIGGER" =~ ^[Nn] ]]; then
        AUTO_TRIGGER_VALUE="false"
    fi

    cat > .flaky-detector.yml <<EOF
# Flaky Test Detector Configuration
# See: https://github.com/runpod/testflake

# Test execution settings
runs: $RUNS                    # Number of times to run each test (1-1000)
parallelism: $PARALLELISM      # Number of parallel workers (1-50)
timeout: 600                   # Timeout in seconds for entire job

# Test command (override with job input if needed)
test_command: "$TEST_COMMAND"

# CI/CD Integration
auto_trigger_on_failure: $AUTO_TRIGGER_VALUE  # Auto-run on test failures
auto_trigger_runs: 20          # Runs for auto-triggered detection
auto_trigger_parallelism: 5    # Parallelism for auto-trigger

# Severity thresholds (0.0 to 1.0)
severity_thresholds:
  critical: 0.9   # >90% failure rate = likely a real bug
  high: 0.5       # 50-90% failure rate = very unstable
  medium: 0.1     # 10-50% failure rate = clear flaky behavior
  low: 0.01       # 1-10% failure rate = occasional flakiness

# Patterns to ignore (tests that won't be checked for flakiness)
ignore_patterns: []
  # - "test_known_flaky_*"
  # - "*_integration_test"

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
EOF

    print_success "Created .flaky-detector.yml"
}

# Create test_input.json template
create_test_input() {
    print_step "Creating test_input.json template..."

    REPO_URL=$(git config --get remote.origin.url 2>/dev/null || echo "https://github.com/your-org/your-repo")

    cat > test_input.json <<EOF
{
  "repo": "$REPO_URL",
  "test_command": "$TEST_COMMAND",
  "runs": $RUNS,
  "parallelism": $PARALLELISM
}
EOF

    print_success "Created test_input.json"
}

# Copy necessary files
copy_files() {
    print_step "Copying flaky detector files..."

    FILES=(
        "worker.py"
        "config.py"
        "database.py"
        "validate_input.py"
        "input_schema.json"
        "local_test.py"
    )

    for file in "${FILES[@]}"; do
        if [ -f "$SCRIPT_DIR/$file" ]; then
            cp "$SCRIPT_DIR/$file" .
            print_success "Copied $file"
        else
            print_warning "File not found: $file (skipping)"
        fi
    done
}

# Setup GitHub Actions
setup_github_actions() {
    echo ""
    echo -e "${GREEN}?${NC} Do you want to set up GitHub Actions integration?"
    read -p "  → [Y/n] " -e -i "Y" SETUP_GHA

    if [[ ! "$SETUP_GHA" =~ ^[Nn] ]]; then
        print_step "Setting up GitHub Actions..."

        mkdir -p .github/workflows

        # Copy auto-trigger workflow
        if [ -f "$SCRIPT_DIR/.github/workflows/flaky-detector-auto.yml" ]; then
            cp "$SCRIPT_DIR/.github/workflows/flaky-detector-auto.yml" .github/workflows/
            print_success "Copied flaky-detector-auto.yml workflow"
        fi

        print_info "GitHub Actions workflow installed!"
        print_info "The flaky detector will automatically run when tests fail in PRs."
    fi
}

# Install Python dependencies
install_dependencies() {
    echo ""
    echo -e "${GREEN}?${NC} Do you want to install Python dependencies now?"
    read -p "  → [Y/n] " -e -i "Y" INSTALL_DEPS

    if [[ ! "$INSTALL_DEPS" =~ ^[Nn] ]]; then
        print_step "Installing dependencies..."

        if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
            pip3 install -q -r "$SCRIPT_DIR/requirements.txt"
            print_success "Dependencies installed"
        else
            print_warning "requirements.txt not found"
            print_info "Install manually: pip install runpod pytest pyyaml jsonschema"
        fi
    fi
}

# Add to .gitignore
update_gitignore() {
    print_step "Updating .gitignore..."

    if [ ! -f ".gitignore" ]; then
        touch .gitignore
    fi

    if ! grep -q "flaky_test_results.json" .gitignore; then
        echo "" >> .gitignore
        echo "# Flaky Test Detector" >> .gitignore
        echo "flaky_test_results.json" >> .gitignore
        echo "flaky_detector.db" >> .gitignore
        print_success "Updated .gitignore"
    else
        print_info ".gitignore already updated"
    fi
}

# Print next steps
print_next_steps() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}                    Setup Complete! 🎉                      ${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${GREEN}Next steps:${NC}"
    echo ""
    echo "1. Test the setup:"
    echo "   ${BLUE}python3 local_test.py${NC}"
    echo ""
    echo "2. Customize configuration:"
    echo "   Edit ${BLUE}.flaky-detector.yml${NC} to adjust settings"
    echo ""
    echo "3. Run on specific tests:"
    echo "   Edit ${BLUE}test_input.json${NC} with your test command"
    echo ""
    echo "4. Commit the configuration:"
    echo "   ${BLUE}git add .flaky-detector.yml test_input.json${NC}"
    echo "   ${BLUE}git commit -m \"Add flaky test detector\"${NC}"
    echo ""
    if [[ ! "$SETUP_GHA" =~ ^[Nn] ]]; then
        echo "5. Push to enable auto-detection:"
        echo "   ${BLUE}git push${NC}"
        echo "   (Flaky detector will auto-run when PR tests fail)"
        echo ""
    fi
    echo -e "${GREEN}Documentation:${NC}"
    echo "  • Getting Started: docs/GETTING_STARTED.md"
    echo "  • Configuration: TEST_INPUT_FILES.md"
    echo "  • CI Integration: docs/CICD_INTEGRATION.md"
    echo ""
    echo -e "${GREEN}Need help?${NC} https://github.com/runpod/testflake"
    echo ""
}

# Main execution
main() {
    check_git_repo
    check_python
    detect_framework
    interactive_config

    echo ""
    print_step "Installing flaky test detector..."
    echo ""

    create_config
    create_test_input
    copy_files
    update_gitignore
    setup_github_actions
    install_dependencies

    print_next_steps
}

# Run main
main
