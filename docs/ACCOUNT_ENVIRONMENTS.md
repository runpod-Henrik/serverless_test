# Test Account Environments

Guide for using environment-specific test accounts (local, dev, staging, prod, ci).

## Quick Start

```python
# Automatically uses current environment
with checkout_account() as account:
    # Uses TEST_ENVIRONMENT or ENVIRONMENT env var
    run_test(account)

# Explicit environment
with checkout_account(environment="prod") as account:
    run_prod_test(account)
```

## Environment Types

Supported environments:
- **local**: Local development (default)
- **dev**: Development environment
- **staging**: Staging/QA environment
- **prod**: Production environment
- **ci**: Continuous integration

## Environment Detection

The system automatically detects the environment from:

1. `TEST_ENVIRONMENT` environment variable (highest priority)
2. `ENVIRONMENT` environment variable
3. Defaults to `"local"` if neither is set

```bash
# Set environment
export TEST_ENVIRONMENT=dev
pytest tests/

# Or inline
TEST_ENVIRONMENT=prod pytest tests/test_prod.py
```

## Environment-Specific Files

Each environment uses a separate account file:

```
test_accounts.local.json    # Local development accounts
test_accounts.dev.json      # Dev environment accounts
test_accounts.staging.json  # Staging accounts
test_accounts.prod.json     # Production accounts
test_accounts.ci.json       # CI environment accounts
```

**Benefits:**
- Isolated credentials per environment
- No accidental cross-environment usage
- Easy to manage different account sets

## Usage Examples

### Example 1: Auto-Detection

```python
# In conftest.py
import pytest
from test_accounts import checkout_account

@pytest.fixture
def account():
    """Automatically uses current environment."""
    with checkout_account() as acc:
        yield acc

# In tests
def test_login(account):
    # Uses dev account if TEST_ENVIRONMENT=dev
    # Uses prod account if TEST_ENVIRONMENT=prod
    login(account.username, account.password)
    assert is_logged_in()
```

### Example 2: Explicit Environment

```python
def test_dev_feature():
    """Test with dev account explicitly."""
    with checkout_account(environment="dev") as account:
        assert "dev" in account.username
        run_dev_test(account)

def test_prod_behavior():
    """Test with prod account explicitly."""
    with checkout_account(environment="prod") as account:
        assert "prod" in account.username
        run_prod_test(account)
```

### Example 3: Multi-Environment Tests

```python
@pytest.mark.parametrize("environment", ["dev", "staging", "prod"])
def test_all_environments(environment):
    """Run same test across all environments."""
    with checkout_account(environment=environment) as account:
        assert account.environment == environment
        run_test(account)
```

### Example 4: CI-Specific Accounts

```python
# In CI pipeline
def test_ci_integration():
    # TEST_ENVIRONMENT=ci is set in CI
    with checkout_account() as account:
        # Uses CI-specific accounts
        assert account.environment == "ci"
        run_integration_test(account)
```

## Configuration

### Creating Environment Accounts

Accounts are created automatically on first use:

```python
from test_accounts import FileStorage

# Create dev accounts
storage = FileStorage(environment="dev")
accounts = storage.load_accounts()  # Auto-creates test_accounts.dev.json

# Accounts will have dev-specific credentials:
# - username: testuser1-dev
# - email: testuser1@dev.example.com
# - password: TestPass_Dev2026!
```

### Custom Environment Accounts

Edit the JSON files to customize accounts:

```json
{
  "accounts": [
    {
      "id": "test-user-1-prod",
      "username": "produser1",
      "password": "SecureProdPass2026!",
      "email": "produser1@prod.company.com",
      "account_type": "standard",
      "environment": "prod",
      "metadata": {
        "region": "us-east-1",
        "tier": "premium"
      }
    }
  ]
}
```

### Manager Configuration

```python
from test_accounts import AccountManager, FileStorage

# Specific environment
manager = AccountManager(environment="staging")

# Custom storage per environment
dev_storage = FileStorage(environment="dev")
dev_manager = AccountManager(storage=dev_storage)

# Explicit file (bypasses environment)
custom_storage = FileStorage("custom_accounts.json")
custom_manager = AccountManager(storage=custom_storage)
```

## Environment Isolation

Environments are completely isolated:

```python
# Dev manager only sees dev accounts
dev_manager = AccountManager(environment="dev")
dev_acc = dev_manager.checkout()
assert dev_acc.environment == "dev"

# Prod manager only sees prod accounts
prod_manager = AccountManager(environment="prod")
prod_acc = prod_manager.checkout()
assert prod_acc.environment == "prod"

# Accounts from different environments are independent
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test-dev:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run dev tests
        env:
          TEST_ENVIRONMENT: dev
        run: pytest tests/

  test-staging:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run staging tests
        env:
          TEST_ENVIRONMENT: staging
        run: pytest tests/

  test-prod:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Run prod tests
        env:
          TEST_ENVIRONMENT: prod
        run: pytest tests/test_prod.py
```

### Different Credentials per Environment

```python
# Local: Simple passwords for development
# - testuser1-local / TestPass_Test123!

# Dev: Dev-specific credentials
# - testuser1-dev / TestPass_Dev2026!

# Staging: Staging-like credentials
# - testuser1-staging / TestPass_Stage2026!

# Prod: Should use 1Password (see below)
# - Real production-like credentials
```

## Best Practices

### 1. Use Environment Variables

```bash
# In your shell profile
export TEST_ENVIRONMENT=local

# In CI/CD
TEST_ENVIRONMENT=ci

# For prod tests
TEST_ENVIRONMENT=prod pytest tests/test_critical.py
```

### 2. Separate Prod Accounts

```python
# Use 1Password for prod accounts
from test_accounts import AccountManager, OnePasswordStorage

if os.environ.get("TEST_ENVIRONMENT") == "prod":
    storage = OnePasswordStorage(vault="Prod Test Accounts")
else:
    storage = FileStorage(environment=get_current_environment())

manager = AccountManager(storage=storage)
```

### 3. Document Environment Requirements

```python
@pytest.mark.prod
def test_prod_feature():
    """
    Test prod-specific feature.

    Requires: TEST_ENVIRONMENT=prod
    """
    with checkout_account(environment="prod") as account:
        run_prod_test(account)
```

### 4. Validate Environment

```python
def test_with_validation():
    """Ensure running in correct environment."""
    required_env = "staging"

    with checkout_account(environment=required_env) as account:
        assert account.environment == required_env
        run_test(account)
```

## Troubleshooting

### Issue: Wrong Environment Used

**Problem:** Tests using wrong environment accounts

**Solution:** Check environment detection:
```python
from test_accounts import get_current_environment

print(f"Current environment: {get_current_environment()}")
# Check TEST_ENVIRONMENT and ENVIRONMENT vars
```

### Issue: No Accounts for Environment

**Error:** `No available accounts (env=prod)`

**Solution:** Create environment-specific accounts:
```python
from test_accounts import FileStorage

storage = FileStorage(environment="prod")
accounts = storage.load_accounts()  # Creates default prod accounts
```

### Issue: Mixed Environments

**Problem:** Dev test accidentally using prod account

**Solution:** Use explicit environment filtering:
```python
# Always specify environment for sensitive tests
with checkout_account(environment="dev") as account:
    assert account.environment == "dev"  # Validate
    run_test(account)
```

## Migration from Non-Environment Setup

If you have existing `test_accounts.json`:

1. **Rename for local environment:**
   ```bash
   mv test_accounts.json test_accounts.local.json
   ```

2. **Create other environments:**
   ```python
   from test_accounts import FileStorage

   for env in ["dev", "staging", "prod"]:
       storage = FileStorage(environment=env)
       accounts = storage.load_accounts()  # Creates defaults
   ```

3. **Update tests:**
   ```python
   # Old: No environment awareness
   with checkout_account() as account:
       run_test(account)

   # New: Environment-aware (automatic)
   with checkout_account() as account:
       # Uses TEST_ENVIRONMENT
       run_test(account)
   ```

## Examples

See `tests/test_account_environments.py` for comprehensive examples of:
- Environment detection
- Environment-specific checkout
- Environment isolation
- Multi-environment testing

## Next Steps

- **[Test Account System](TEST_ACCOUNT_SYSTEM.md)** - Main documentation
- **[Quick Reference](QUICK_REFERENCE.md)** - Command cheat sheet
- **[Architecture](ARCHITECTURE.md)** - System design

---

**Environment support ensures test isolation and prevents accidental cross-environment usage!**
