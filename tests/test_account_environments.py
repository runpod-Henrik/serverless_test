"""Tests for environment support in test account management system."""

import os

import pytest

from test_accounts import (
    Account,
    AccountManager,
    Environment,
    FileStorage,
    checkout_account,
    get_current_environment,
)


def test_environment_enum():
    """Test Environment enum values."""
    assert Environment.LOCAL == "local"
    assert Environment.DEV == "dev"
    assert Environment.STAGING == "staging"
    assert Environment.PROD == "prod"
    assert Environment.CI == "ci"


def test_get_current_environment_default():
    """Test default environment detection."""
    # Clear env vars
    os.environ.pop("TEST_ENVIRONMENT", None)
    os.environ.pop("ENVIRONMENT", None)

    env = get_current_environment()
    assert env == "local"


def test_get_current_environment_from_test_environment():
    """Test environment detection from TEST_ENVIRONMENT."""
    os.environ["TEST_ENVIRONMENT"] = "dev"

    try:
        env = get_current_environment()
        assert env == "dev"
    finally:
        os.environ.pop("TEST_ENVIRONMENT")


def test_get_current_environment_from_environment():
    """Test environment detection from ENVIRONMENT."""
    os.environ["ENVIRONMENT"] = "prod"

    try:
        env = get_current_environment()
        assert env == "prod"
    finally:
        os.environ.pop("ENVIRONMENT")


def test_file_storage_environment_specific_file(tmp_path):
    """Test FileStorage uses environment-specific files."""
    storage_dev = FileStorage(environment="dev")
    assert storage_dev.accounts_file.name == "test_accounts.dev.json"

    storage_prod = FileStorage(environment="prod")
    assert storage_prod.accounts_file.name == "test_accounts.prod.json"


def test_file_storage_creates_environment_accounts(tmp_path):
    """Test FileStorage creates environment-specific accounts."""
    accounts_file = tmp_path / "test_accounts.dev.json"
    storage = FileStorage(str(accounts_file), environment="dev")

    accounts = storage.load_accounts()

    # All accounts should have dev environment
    assert all(acc.environment == "dev" for acc in accounts)

    # Usernames should include environment
    assert any("dev" in acc.username for acc in accounts)


def test_account_has_environment_field():
    """Test Account dataclass includes environment."""
    account = Account(
        id="test-1",
        username="testuser",
        password="testpass",
        email="test@example.com",
        environment="prod",
    )

    assert account.environment == "prod"


def test_manager_filters_by_environment(tmp_path):
    """Test AccountManager filters accounts by environment."""
    # Create dev accounts
    dev_file = tmp_path / "test_accounts.dev.json"
    dev_storage = FileStorage(str(dev_file), environment="dev")
    dev_manager = AccountManager(storage=dev_storage, environment="dev")

    # Create prod accounts
    prod_file = tmp_path / "test_accounts.prod.json"
    prod_storage = FileStorage(str(prod_file), environment="prod")
    prod_manager = AccountManager(storage=prod_storage, environment="prod")

    # Checkout from dev
    dev_account = dev_manager.checkout()
    assert dev_account.environment == "dev"
    assert "dev" in dev_account.username

    # Checkout from prod
    prod_account = prod_manager.checkout()
    assert prod_account.environment == "prod"
    assert "prod" in prod_account.username


def test_checkout_with_environment_filter(tmp_path):
    """Test checking out account with specific environment."""
    # Create mixed environment accounts
    accounts_file = tmp_path / "mixed.json"
    accounts = [
        Account(
            id="dev-1",
            username="dev-user",
            password="pass",
            email="dev@example.com",
            environment="dev",
        ),
        Account(
            id="prod-1",
            username="prod-user",
            password="pass",
            email="prod@example.com",
            environment="prod",
        ),
    ]

    storage = FileStorage(str(accounts_file))
    storage.save_accounts(accounts)

    manager = AccountManager(storage=storage, environment="dev")

    # Checkout dev account
    dev_acc = manager.checkout(environment="dev")
    assert dev_acc.environment == "dev"

    # Checkout prod account explicitly
    prod_acc = manager.checkout(environment="prod")
    assert prod_acc.environment == "prod"


def test_context_manager_with_environment(tmp_path):
    """Test checkout_account context manager with environment."""
    # Set up environment-specific accounts
    os.environ["TEST_ENVIRONMENT"] = "staging"

    try:
        # Global manager will use staging environment
        from test_accounts import _global_manager, _manager_lock

        # Reset global manager
        with _manager_lock:
            _global_manager = None

        # Now checkout will use staging
        with checkout_account() as account:
            assert account.environment == "staging"
            assert "staging" in account.username
    finally:
        os.environ.pop("TEST_ENVIRONMENT", None)
        # Reset global manager
        with _manager_lock:
            _global_manager = None


def test_environment_isolation(tmp_path):
    """Test that environments are isolated."""
    # Create dev manager
    dev_file = tmp_path / "dev.json"
    dev_storage = FileStorage(str(dev_file), environment="dev")
    dev_manager = AccountManager(storage=dev_storage, environment="dev")

    # Create prod manager
    prod_file = tmp_path / "prod.json"
    prod_storage = FileStorage(str(prod_file), environment="prod")
    prod_manager = AccountManager(storage=prod_storage, environment="prod")

    # Checkout all dev accounts
    dev_accounts = []
    try:
        while True:
            dev_accounts.append(dev_manager.checkout(environment="dev"))
    except RuntimeError:
        pass

    # Prod accounts should still be available
    prod_account = prod_manager.checkout(environment="prod")
    assert prod_account is not None
    assert prod_account.environment == "prod"

    # Dev accounts should be exhausted
    with pytest.raises(RuntimeError, match="No available accounts"):
        dev_manager.checkout(environment="dev")


def test_different_credentials_per_environment(tmp_path):
    """Test that different environments have different credentials."""
    dev_storage = FileStorage(environment="dev")
    prod_storage = FileStorage(environment="prod")

    dev_accounts = dev_storage._create_default_accounts()
    prod_accounts = prod_storage._create_default_accounts()

    # Same account types but different credentials
    dev_user = next(acc for acc in dev_accounts if acc.account_type == "standard")
    prod_user = next(acc for acc in prod_accounts if acc.account_type == "standard")

    assert dev_user.username != prod_user.username
    assert dev_user.password != prod_user.password
    assert dev_user.email != prod_user.email
    assert "dev" in dev_user.username
    assert "prod" in prod_user.username


def test_manager_default_environment():
    """Test that manager uses current environment by default."""
    os.environ["TEST_ENVIRONMENT"] = "ci"

    try:
        manager = AccountManager()
        assert manager.environment == "ci"
    finally:
        os.environ.pop("TEST_ENVIRONMENT", None)


def test_checkout_without_environment_uses_manager_default(tmp_path):
    """Test checkout without environment uses manager's environment."""
    dev_file = tmp_path / "dev.json"
    dev_storage = FileStorage(str(dev_file), environment="dev")
    manager = AccountManager(storage=dev_storage, environment="dev")

    # Checkout without specifying environment
    account = manager.checkout()

    # Should get dev account (manager's default)
    assert account.environment == "dev"
