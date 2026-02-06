# Test Account Management System

Thread-safe account checkout system for parallel test execution with automatic timeout and 1Password extensibility.

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Features](#features)
4. [Usage Patterns](#usage-patterns)
5. [Configuration](#configuration)
6. [1Password Integration](#1password-integration)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

## Overview

### The Problem

When running tests in parallel, multiple tests trying to use the same test account simultaneously causes:
- Login conflicts
- Session interference
- Rate limiting
- Data corruption
- Flaky test failures

### The Solution

A thread-safe account checkout system that:
- ✅ Prevents multiple tests from using the same account
- ✅ Automatically releases accounts after timeout
- ✅ Supports different account types (standard, admin, premium)
- ✅ Works seamlessly with parallel test execution
- ✅ Extensible for 1Password integration

## Quick Start

### Basic Usage

```python
from test_accounts import checkout_account

def test_login():
    # Checkout account automatically
    with checkout_account() as account:
        # Use the account
        login(account.username, account.password)

        # Account is automatically checked in after test
        assert is_logged_in()
```

### With Pytest

```python
# In conftest.py
import pytest
from test_accounts import checkout_account

@pytest.fixture
def account():
    """Provide a test account for each test."""
    with checkout_account() as acc:
        yield acc

# In your tests
def test_user_dashboard(account):
    login(account.username, account.password)
    dashboard = get_dashboard()
    assert dashboard.user == account.username
```

### Different Account Types

```python
def test_admin_features():
    # Checkout admin account
    with checkout_account(account_type="admin") as admin:
        login(admin.username, admin.password)
        assert has_admin_access()

def test_premium_features():
    # Checkout premium account
    with checkout_account(account_type="premium") as premium:
        login(premium.username, premium.password)
        assert has_premium_features()
```

## Features

### 1. Thread-Safe Checkout

Prevents race conditions when multiple tests run in parallel:

```python
# Multiple tests can run simultaneously
def test_login_user1():
    with checkout_account() as account:  # Gets account A
        login(account.username, account.password)

def test_login_user2():
    with checkout_account() as account:  # Gets account B (different!)
        login(account.username, account.password)
```

### 2. Automatic Timeout

Accounts are automatically released if a test hangs or crashes:

```python
# Check out with custom timeout
with checkout_account(timeout=60) as account:  # 60 second timeout
    # If test takes longer than 60 seconds, account is auto-released
    run_long_test(account)
```

**Default timeout:** 300 seconds (5 minutes)

### 3. Account Type Filtering

Different tests need different account types:

```python
# Standard user account
with checkout_account(account_type="standard") as user:
    test_user_features(user)

# Admin account
with checkout_account(account_type="admin") as admin:
    test_admin_features(admin)

# Premium account
with checkout_account(account_type="premium") as premium:
    test_premium_features(premium)
```

### 4. Status Monitoring

Check current account usage:

```python
from test_accounts import get_account_manager

manager = get_account_manager()
status = manager.get_status()

print(f"Total accounts: {status['total_accounts']}")
print(f"Checked out: {status['checked_out']}")
print(f"Available: {status['available']}")

# View current checkouts
for checkout in status['checkouts']:
    print(f"  {checkout['account_id']}: {checkout['checked_out_by']}")
    print(f"    Age: {checkout['age_seconds']}s / {checkout['timeout_seconds']}s")
```

## Usage Patterns

### Pattern 1: Context Manager (Recommended)

Automatically checks out and checks in:

```python
def test_with_context_manager():
    with checkout_account() as account:
        # Account is checked out
        run_test(account)
    # Account is automatically checked in
```

**Benefits:**
- Automatic cleanup
- Works even if test fails
- Clean syntax

### Pattern 2: Pytest Fixture

Reusable across multiple tests:

```python
# conftest.py
@pytest.fixture
def user_account():
    """Provide standard user account."""
    with checkout_account(account_type="standard") as acc:
        yield acc

@pytest.fixture
def admin_account():
    """Provide admin account."""
    with checkout_account(account_type="admin") as acc:
        yield acc

# test_features.py
def test_user_feature(user_account):
    login(user_account.username, user_account.password)
    assert can_use_feature()

def test_admin_feature(admin_account):
    login(admin_account.username, admin_account.password)
    assert can_use_admin_feature()
```

### Pattern 3: Manual Management

For advanced use cases:

```python
from test_accounts import get_account_manager

def test_with_manual_management():
    manager = get_account_manager()

    # Check out account
    account = manager.checkout(
        account_type="admin",
        timeout=120,
        requester="custom-test"
    )

    try:
        # Use account
        run_test(account)
    finally:
        # Always check in
        manager.checkin(account.id)
```

### Pattern 4: Parallel Execution

Safe for use with pytest-xdist or concurrent.futures:

```python
# pytest with parallel execution
# pytest tests/ -n 4  # Run 4 tests in parallel

def test_parallel_1():
    with checkout_account() as account:
        # Gets unique account
        run_test(account)

def test_parallel_2():
    with checkout_account() as account:
        # Gets different unique account
        run_test(account)

# Or with concurrent.futures
import concurrent.futures

def run_test_with_account(test_id):
    with checkout_account() as account:
        print(f"Test {test_id} using {account.username}")
        run_test(account)

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(run_test_with_account, i) for i in range(10)]
    concurrent.futures.wait(futures)
```

## Configuration

### Account Storage

**File:** `test_accounts.json` (automatically created)

```json
{
  "accounts": [
    {
      "id": "test-user-1",
      "username": "testuser1",
      "password": "TestPass123!",
      "email": "testuser1@example.com",
      "account_type": "standard",
      "metadata": null
    },
    {
      "id": "test-admin-1",
      "username": "testadmin1",
      "password": "AdminPass123!",
      "email": "testadmin1@example.com",
      "account_type": "admin",
      "metadata": {
        "permissions": ["read", "write", "delete", "admin"]
      }
    }
  ],
  "last_updated": "2026-02-06T03:00:00"
}
```

### Adding Custom Accounts

Edit `test_accounts.json` or create programmatically:

```python
from test_accounts import Account, FileStorage

# Load storage
storage = FileStorage("test_accounts.json")
accounts = storage.load_accounts()

# Add new account
new_account = Account(
    id="test-custom-1",
    username="customuser",
    password="CustomPass123!",
    email="custom@example.com",
    account_type="custom",
    metadata={"feature_flags": ["beta", "experimental"]}
)

accounts.append(new_account)
storage.save_accounts(accounts)
```

### Manager Configuration

Customize timeouts and cleanup:

```python
from test_accounts import AccountManager, FileStorage

manager = AccountManager(
    storage=FileStorage("custom_accounts.json"),
    default_timeout=600,      # 10 minute default timeout
    cleanup_interval=30       # Check for expired checkouts every 30s
)
```

## 1Password Integration

### Setup (Future Enhancement)

The system is designed to integrate with 1Password for production-like test accounts:

```python
from test_accounts import AccountManager, OnePasswordStorage

# Configure 1Password storage
storage = OnePasswordStorage(
    vault="Test Accounts",
    connect_host="http://localhost:8080",
    connect_token=os.environ["OP_CONNECT_TOKEN"]
)

# Use with manager
manager = AccountManager(storage=storage)

# Use normally
with checkout_account() as account:
    # Account loaded from 1Password
    login(account.username, account.password)
```

### Benefits of 1Password Integration

- **Secure**: Real credentials stored securely
- **Centralized**: One source of truth
- **Auditable**: Track account usage
- **Rotation**: Easy to rotate passwords
- **Separation**: Different credentials for different environments

### Implementation Notes

The `OnePasswordStorage` class is an extension point:

```python
class OnePasswordStorage(AccountStorage):
    def load_accounts(self) -> List[Account]:
        """
        Load accounts from 1Password vault.

        Implementation steps:
        1. Connect to 1Password using Connect API
        2. List items in specified vault
        3. Parse item fields (username, password, etc.)
        4. Return as Account objects
        """
        # TODO: Implement when needed
        pass
```

**To enable:**
1. Install SDK: `pip install onepasswordconnectsdk`
2. Set up 1Password Connect server
3. Implement `load_accounts()` method
4. Configure vault and credentials

## Best Practices

### 1. Use Context Managers

Always use the context manager to ensure cleanup:

```python
# ✅ GOOD: Automatic cleanup
with checkout_account() as account:
    run_test(account)

# ❌ BAD: Manual cleanup (error-prone)
manager = get_account_manager()
account = manager.checkout()
run_test(account)
manager.checkin(account.id)  # Might not run if exception occurs
```

### 2. Set Appropriate Timeouts

Match timeout to test duration:

```python
# Quick test (30 seconds)
with checkout_account(timeout=60) as account:
    run_quick_test(account)

# Long integration test (10 minutes)
with checkout_account(timeout=900) as account:
    run_integration_test(account)
```

### 3. Use Account Types

Organize by permission level:

```python
# Standard user tests
with checkout_account(account_type="standard") as user:
    test_user_features(user)

# Admin tests
with checkout_account(account_type="admin") as admin:
    test_admin_features(admin)

# Premium tests
with checkout_account(account_type="premium") as premium:
    test_premium_features(premium)
```

### 4. Don't Modify Account State

Tests should leave accounts in clean state:

```python
def test_with_cleanup():
    with checkout_account() as account:
        # Setup
        login(account.username, account.password)
        create_test_data()

        # Test
        run_test()

        # Cleanup (important!)
        delete_test_data()
        logout()
```

### 5. Monitor Account Pool

Ensure enough accounts for parallel execution:

```python
# If running 10 tests in parallel, need at least 10 accounts
# Check status before test run:
status = get_account_manager().get_status()
assert status['total_accounts'] >= 10, "Not enough accounts for parallel execution"
```

### 6. Handle Checkout Failures

Gracefully handle when no accounts available:

```python
from test_accounts import checkout_account
import pytest

def test_with_retry():
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with checkout_account(timeout=30) as account:
                run_test(account)
                break
        except RuntimeError as e:
            if "No available accounts" in str(e) and attempt < max_retries - 1:
                print(f"Retry {attempt + 1}/{max_retries}")
                time.sleep(5)  # Wait for accounts to be released
            else:
                raise
```

## Troubleshooting

### Issue: No Available Accounts

**Error:**
```
RuntimeError: No available accounts (type=None, id=None).
Current checkouts: 5/5
```

**Solutions:**

1. **Add more accounts:**
   ```python
   # Edit test_accounts.json and add more accounts
   ```

2. **Reduce parallel workers:**
   ```bash
   # Instead of: pytest tests/ -n 10
   pytest tests/ -n 5  # Match number of accounts
   ```

3. **Check for stuck checkouts:**
   ```python
   status = get_account_manager().get_status()
   print("Stuck checkouts:", status['checkouts'])
   ```

### Issue: Tests Fail with "Account in use"

**Cause:** Multiple tests using same account simultaneously

**Solution:** Don't hardcode account IDs:

```python
# ❌ BAD: Hardcoded account
def test_with_hardcoded():
    account = manager.checkout(account_id="test-user-1")  # Always same account!

# ✅ GOOD: Let manager assign
def test_with_dynamic():
    with checkout_account() as account:  # Gets any available account
        run_test(account)
```

### Issue: Account Doesn't Get Released

**Cause:** Exception before checkin or test hangs

**Solutions:**

1. **Always use context manager** (auto-cleanup)
2. **Set appropriate timeout** (auto-release)
3. **Check cleanup thread** is running:
   ```python
   manager = get_account_manager()
   # Cleanup thread runs automatically
   ```

### Issue: Slow Test Performance

**Cause:** Waiting for account availability

**Solutions:**

1. **Add more accounts** to the pool
2. **Reduce parallelism** to match account count
3. **Increase cleanup interval** (faster release):
   ```python
   manager = AccountManager(cleanup_interval=10)  # Check every 10s
   ```

### Issue: Can't Run Example

**Error:**
```
FileNotFoundError: test_accounts.json
```

**Solution:** Run once to create default accounts:
```python
from test_accounts import FileStorage

storage = FileStorage("test_accounts.json")
accounts = storage.load_accounts()  # Creates default accounts
```

## Examples

### Example 1: Basic Login Test

```python
def test_login():
    with checkout_account() as account:
        # Login
        response = login(account.username, account.password)

        # Verify
        assert response.status_code == 200
        assert is_logged_in()

        # Cleanup
        logout()
```

### Example 2: Admin Permission Test

```python
def test_admin_permissions():
    with checkout_account(account_type="admin") as admin:
        login(admin.username, admin.password)

        # Test admin-only features
        result = delete_user("test-victim")
        assert result.success

        result = view_audit_logs()
        assert len(result.logs) > 0
```

### Example 3: Parallel Test Execution

```python
@pytest.mark.parametrize("test_data", [
    {"feature": "dashboard", "expected": "Dashboard"},
    {"feature": "profile", "expected": "Profile"},
    {"feature": "settings", "expected": "Settings"},
])
def test_features_parallel(test_data):
    """Each test gets its own account automatically."""
    with checkout_account() as account:
        login(account.username, account.password)
        page = navigate_to(test_data["feature"])
        assert test_data["expected"] in page.title
```

### Example 4: Custom Timeout

```python
@pytest.mark.slow
def test_long_running():
    # Long integration test needs longer timeout
    with checkout_account(timeout=1800) as account:  # 30 minutes
        login(account.username, account.password)

        # Long-running operation
        run_integration_test()

        # Verify results
        results = get_test_results()
        assert results.success
```

### Example 5: Monitoring Usage

```python
def test_with_monitoring():
    manager = get_account_manager()

    # Before test
    initial_status = manager.get_status()
    print(f"Available accounts: {initial_status['available']}")

    # Run test
    with checkout_account() as account:
        print(f"Using account: {account.username}")
        run_test(account)

    # After test
    final_status = manager.get_status()
    assert final_status['available'] == initial_status['available']
```

## Next Steps

- **[Quick Reference](QUICK_REFERENCE.md)** - Command cheat sheet
- **[Architecture](ARCHITECTURE.md)** - System design
- **[CI/CD Integration](CICD_INTEGRATION.md)** - GitHub Actions

---

**Need help?** Open an issue or check the test examples in `tests/test_account_manager.py`
