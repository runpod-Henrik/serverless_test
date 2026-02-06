"""Tests for test account management system."""

import threading
import time

import pytest

from test_accounts import (
    Account,
    AccountManager,
    FileStorage,
    checkout_account,
    get_account_manager,
)


@pytest.fixture
def temp_storage(tmp_path):
    """Create temporary file storage."""
    accounts_file = tmp_path / "test_accounts.json"
    return FileStorage(str(accounts_file))


@pytest.fixture
def manager(temp_storage):
    """Create account manager with temporary storage."""
    return AccountManager(storage=temp_storage, cleanup_interval=1)


def test_account_creation():
    """Test creating an account object."""
    account = Account(
        id="test-1",
        username="testuser",
        password="testpass",
        email="test@example.com",
    )

    assert account.id == "test-1"
    assert account.username == "testuser"
    assert account.account_type == "standard"


def test_file_storage_creates_default_accounts(tmp_path):
    """Test that FileStorage creates default accounts."""
    accounts_file = tmp_path / "accounts.json"
    storage = FileStorage(str(accounts_file))

    accounts = storage.load_accounts()

    assert len(accounts) > 0
    assert accounts_file.exists()
    assert any(acc.account_type == "admin" for acc in accounts)
    assert any(acc.account_type == "standard" for acc in accounts)


def test_checkout_account(manager):
    """Test basic account checkout."""
    account = manager.checkout()

    assert account is not None
    assert account.username
    assert account.password

    # Should be marked as checked out
    status = manager.get_status()
    assert status["checked_out"] == 1
    assert status["available"] == status["total_accounts"] - 1


def test_checkin_account(manager):
    """Test checking in an account."""
    account = manager.checkout()
    account_id = account.id

    # Check in
    manager.checkin(account_id)

    # Should be available again
    status = manager.get_status()
    assert status["checked_out"] == 0
    assert status["available"] == status["total_accounts"]


def test_checkout_by_type(manager):
    """Test checking out specific account type."""
    admin = manager.checkout(account_type="admin")

    assert admin.account_type == "admin"

    standard = manager.checkout(account_type="standard")

    assert standard.account_type == "standard"
    assert standard.id != admin.id


def test_checkout_by_id(manager):
    """Test checking out specific account by ID."""
    # First, get an account ID
    account1 = manager.checkout()
    account_id = account1.id
    manager.checkin(account_id)

    # Now check out by ID
    account2 = manager.checkout(account_id=account_id)

    assert account2.id == account_id


def test_multiple_checkouts(manager):
    """Test checking out multiple accounts in parallel."""
    acc1 = manager.checkout()
    acc2 = manager.checkout()
    acc3 = manager.checkout()

    # All should be different
    assert acc1.id != acc2.id
    assert acc2.id != acc3.id
    assert acc1.id != acc3.id

    status = manager.get_status()
    assert status["checked_out"] == 3


def test_no_available_accounts(manager):
    """Test error when all accounts are checked out."""
    # Check out all accounts
    accounts = []
    try:
        while True:
            accounts.append(manager.checkout())
    except RuntimeError:
        pass

    # Should have checked out all available
    assert len(accounts) > 0

    # Trying to check out one more should fail
    with pytest.raises(RuntimeError, match="No available accounts"):
        manager.checkout()

    # Check in one and try again
    manager.checkin(accounts[0].id)
    account = manager.checkout()
    assert account is not None


def test_timeout_auto_release(manager):
    """Test that accounts are auto-released after timeout."""
    # Check out with short timeout
    _account = manager.checkout(timeout=2)

    # Should be checked out
    status = manager.get_status()
    assert status["checked_out"] == 1

    # Wait for timeout + cleanup interval
    time.sleep(4)

    # Should be auto-released
    status = manager.get_status()
    assert status["checked_out"] == 0


def test_context_manager():
    """Test using checkout_account context manager."""
    initial_status = get_account_manager().get_status()
    initial_checked_out = initial_status["checked_out"]

    with checkout_account() as account:
        assert account is not None
        assert account.username

        # Should be checked out
        status = get_account_manager().get_status()
        assert status["checked_out"] == initial_checked_out + 1

    # Should be auto-checked in
    status = get_account_manager().get_status()
    assert status["checked_out"] == initial_checked_out


def test_context_manager_with_exception():
    """Test that context manager checks in even on exception."""
    initial_status = get_account_manager().get_status()
    initial_checked_out = initial_status["checked_out"]

    try:
        with checkout_account():
            raise ValueError("Test error")
    except ValueError:
        pass

    # Should still be checked in
    status = get_account_manager().get_status()
    assert status["checked_out"] == initial_checked_out


def test_context_manager_by_type():
    """Test context manager with account type filter."""
    with checkout_account(account_type="admin") as admin:
        assert admin.account_type == "admin"

    with checkout_account(account_type="standard") as standard:
        assert standard.account_type == "standard"


def test_parallel_checkouts_thread_safe(manager):
    """Test thread-safe parallel checkouts."""
    checked_out_accounts = []
    errors = []
    lock = threading.Lock()

    def checkout_worker(worker_id):
        try:
            account = manager.checkout()
            with lock:
                checked_out_accounts.append((worker_id, account.id))
            time.sleep(0.1)  # Simulate work
            manager.checkin(account.id)
        except Exception as e:
            with lock:
                errors.append(e)

    # Start multiple threads
    threads = []
    for i in range(3):
        thread = threading.Thread(target=checkout_worker, args=(i,))
        thread.start()
        threads.append(thread)

    # Wait for completion
    for thread in threads:
        thread.join()

    # No errors
    assert len(errors) == 0

    # All checkouts were successful
    assert len(checked_out_accounts) == 3

    # All got different accounts
    account_ids = [acc_id for _, acc_id in checked_out_accounts]
    assert len(set(account_ids)) == 3


def test_status_reporting(manager):
    """Test status reporting."""
    status = manager.get_status()

    assert "total_accounts" in status
    assert "checked_out" in status
    assert "available" in status
    assert "checkouts" in status

    # Check out an account
    account = manager.checkout(requester="test-worker")

    status = manager.get_status()
    assert status["checked_out"] == 1
    assert len(status["checkouts"]) == 1

    checkout_info = status["checkouts"][0]
    assert checkout_info["account_id"] == account.id
    assert checkout_info["checked_out_by"] == "test-worker"
    assert "age_seconds" in checkout_info
    assert "timeout_seconds" in checkout_info


def test_account_metadata():
    """Test storing metadata with accounts."""
    account = Account(
        id="test-meta",
        username="testuser",
        password="testpass",
        email="test@example.com",
        metadata={"role": "tester", "permissions": ["read", "write"]},
    )

    assert account.metadata["role"] == "tester"
    assert "read" in account.metadata["permissions"]


def test_multiple_account_types(manager):
    """Test that different account types are properly separated."""
    # Get count of each type
    all_accounts = manager._accounts.values()
    admin_count = sum(1 for acc in all_accounts if acc.account_type == "admin")
    standard_count = sum(1 for acc in all_accounts if acc.account_type == "standard")

    assert admin_count > 0
    assert standard_count > 0

    # Check out all admins
    admins = []
    for _ in range(admin_count):
        admins.append(manager.checkout(account_type="admin"))

    # Should still be able to check out standard accounts
    standard = manager.checkout(account_type="standard")
    assert standard.account_type == "standard"

    # But no more admins available
    with pytest.raises(RuntimeError):
        manager.checkout(account_type="admin")
