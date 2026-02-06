"""
Test Account Management System

Provides thread-safe account checkout for parallel test execution with automatic
timeout and cleanup. Designed to be extensible for 1Password integration.

Usage:
    # Simple checkout
    with checkout_account() as account:
        # Use account.username, account.password
        run_test_with_account(account)

    # Specific account type
    with checkout_account(account_type="admin") as account:
        run_admin_test(account)

    # Manual management
    manager = AccountManager()
    account = manager.checkout(timeout=300)
    try:
        run_test(account)
    finally:
        manager.checkin(account.id)
"""

import json
import threading
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class Account:
    """Test account with credentials."""

    id: str
    username: str
    password: str
    email: str
    account_type: str = "standard"
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class AccountCheckout:
    """Record of an account checkout."""

    account_id: str
    checked_out_at: float
    checked_out_by: str
    timeout: int


class AccountStorage:
    """
    Abstract storage interface for account data.

    Can be implemented with different backends:
    - FileStorage (default, for local/CI)
    - OnePasswordStorage (for production-like accounts)
    - DatabaseStorage (for shared test environments)
    """

    def load_accounts(self) -> list[Account]:
        """Load all available accounts."""
        raise NotImplementedError

    def save_accounts(self, accounts: list[Account]) -> None:
        """Save accounts (if mutable storage)."""
        raise NotImplementedError


class FileStorage(AccountStorage):
    """File-based storage for test accounts."""

    def __init__(self, accounts_file: str = "test_accounts.json"):
        self.accounts_file = Path(accounts_file)

    def load_accounts(self) -> list[Account]:
        """Load accounts from JSON file."""
        if not self.accounts_file.exists():
            # Create default accounts if file doesn't exist
            default_accounts = self._create_default_accounts()
            self.save_accounts(default_accounts)
            return default_accounts

        with open(self.accounts_file) as f:
            data = json.load(f)

        return [Account(**acc) for acc in data.get("accounts", [])]

    def save_accounts(self, accounts: list[Account]) -> None:
        """Save accounts to JSON file."""
        data = {
            "accounts": [acc.to_dict() for acc in accounts],
            "last_updated": datetime.now().isoformat(),
        }

        with open(self.accounts_file, "w") as f:
            json.dump(data, f, indent=2)

    def _create_default_accounts(self) -> list[Account]:
        """Create default test accounts."""
        return [
            Account(
                id="test-user-1",
                username="testuser1",
                password="TestPass123!",
                email="testuser1@example.com",
                account_type="standard",
            ),
            Account(
                id="test-user-2",
                username="testuser2",
                password="TestPass123!",
                email="testuser2@example.com",
                account_type="standard",
            ),
            Account(
                id="test-user-3",
                username="testuser3",
                password="TestPass123!",
                email="testuser3@example.com",
                account_type="standard",
            ),
            Account(
                id="test-admin-1",
                username="testadmin1",
                password="AdminPass123!",
                email="testadmin1@example.com",
                account_type="admin",
            ),
            Account(
                id="test-premium-1",
                username="testpremium1",
                password="PremiumPass123!",
                email="testpremium1@example.com",
                account_type="premium",
            ),
        ]


class OnePasswordStorage(AccountStorage):
    """
    1Password integration for production-like test accounts.

    To enable later, install: pip install onepasswordconnectsdk

    Usage:
        storage = OnePasswordStorage(
            vault="Test Accounts",
            connect_host="http://localhost:8080",
            connect_token="your-token"
        )
        manager = AccountManager(storage=storage)
    """

    def __init__(
        self, vault: str, connect_host: str | None = None, connect_token: str | None = None
    ):
        self.vault = vault
        self.connect_host = connect_host
        self.connect_token = connect_token
        self._client = None

    def _get_client(self):
        """Lazy-load 1Password Connect client."""
        if self._client is None:
            try:
                from onepasswordconnectsdk.client import Client

                self._client = Client(url=self.connect_host, token=self.connect_token)
            except ImportError as e:
                raise ImportError(
                    "1Password SDK not installed. Install with: pip install onepasswordconnectsdk"
                ) from e
        return self._client

    def load_accounts(self) -> list[Account]:
        """Load accounts from 1Password vault."""
        # Placeholder for future implementation
        raise NotImplementedError(
            "1Password integration not yet implemented. "
            "This is the extension point for adding 1Password support."
        )

    def save_accounts(self, accounts: list[Account]) -> None:
        """1Password accounts are read-only from the vault."""
        raise NotImplementedError("Cannot save accounts to 1Password vault (read-only)")


class AccountManager:
    """
    Thread-safe account checkout manager.

    Handles:
    - Account checkout/checkin
    - Automatic timeout and cleanup
    - Parallel test execution
    - Account type filtering
    """

    def __init__(
        self,
        storage: AccountStorage | None = None,
        default_timeout: int = 300,
        cleanup_interval: int = 60,
    ):
        """
        Initialize account manager.

        Args:
            storage: Storage backend (defaults to FileStorage)
            default_timeout: Default checkout timeout in seconds
            cleanup_interval: How often to check for expired checkouts (seconds)
        """
        self.storage = storage or FileStorage()
        self.default_timeout = default_timeout

        # Load accounts
        self._accounts: dict[str, Account] = {acc.id: acc for acc in self.storage.load_accounts()}

        # Track checkouts
        self._checkouts: dict[str, AccountCheckout] = {}
        self._lock = threading.RLock()

        # Start cleanup thread
        self._cleanup_interval = cleanup_interval
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    def checkout(
        self,
        account_type: str | None = None,
        account_id: str | None = None,
        timeout: int | None = None,
        requester: str | None = None,
    ) -> Account:
        """
        Check out an available account.

        Args:
            account_type: Filter by account type (e.g., "admin", "premium")
            account_id: Request specific account by ID
            timeout: Checkout timeout in seconds
            requester: Identifier for who's checking out (for debugging)

        Returns:
            Account object

        Raises:
            RuntimeError: If no accounts available
        """
        timeout = timeout or self.default_timeout
        requester = requester or threading.current_thread().name

        with self._lock:
            # Find available account
            available = self._find_available_account(account_type, account_id)

            if not available:
                raise RuntimeError(
                    f"No available accounts "
                    f"(type={account_type}, id={account_id}). "
                    f"Current checkouts: {len(self._checkouts)}/{len(self._accounts)}"
                )

            # Check out the account
            checkout = AccountCheckout(
                account_id=available.id,
                checked_out_at=time.time(),
                checked_out_by=requester,
                timeout=timeout,
            )

            self._checkouts[available.id] = checkout

            return available

    def checkin(self, account_id: str) -> None:
        """
        Check in an account, making it available for other tests.

        Args:
            account_id: ID of account to check in
        """
        with self._lock:
            if account_id in self._checkouts:
                del self._checkouts[account_id]

    def _find_available_account(
        self, account_type: str | None, account_id: str | None
    ) -> Account | None:
        """Find an available account matching criteria."""
        for acc_id, account in self._accounts.items():
            # Skip if checked out
            if acc_id in self._checkouts:
                continue

            # Filter by specific ID
            if account_id and acc_id != account_id:
                continue

            # Filter by type
            if account_type and account.account_type != account_type:
                continue

            return account

        return None

    def _cleanup_loop(self) -> None:
        """Background thread to cleanup expired checkouts."""
        while True:
            time.sleep(self._cleanup_interval)
            self._cleanup_expired()

    def _cleanup_expired(self) -> None:
        """Release accounts that have exceeded their timeout."""
        now = time.time()

        with self._lock:
            expired = []

            for account_id, checkout in self._checkouts.items():
                age = now - checkout.checked_out_at

                if age > checkout.timeout:
                    expired.append(account_id)

            for account_id in expired:
                del self._checkouts[account_id]

            if expired:
                print(f"⚠️  Auto-released {len(expired)} expired account(s): {expired}")

    def get_status(self) -> dict[str, Any]:
        """Get current checkout status for monitoring."""
        with self._lock:
            return {
                "total_accounts": len(self._accounts),
                "checked_out": len(self._checkouts),
                "available": len(self._accounts) - len(self._checkouts),
                "checkouts": [
                    {
                        "account_id": checkout.account_id,
                        "checked_out_by": checkout.checked_out_by,
                        "age_seconds": int(time.time() - checkout.checked_out_at),
                        "timeout_seconds": checkout.timeout,
                    }
                    for checkout in self._checkouts.values()
                ],
            }


# Global manager instance
_global_manager: AccountManager | None = None
_manager_lock = threading.Lock()


def get_account_manager() -> AccountManager:
    """Get or create global account manager singleton."""
    global _global_manager

    if _global_manager is None:
        with _manager_lock:
            if _global_manager is None:
                _global_manager = AccountManager()

    return _global_manager


@contextmanager
def checkout_account(
    account_type: str | None = None,
    account_id: str | None = None,
    timeout: int | None = None,
):
    """
    Context manager for checking out a test account.

    Automatically checks in the account when done, even if test fails.

    Usage:
        with checkout_account() as account:
            # Use account.username, account.password
            login(account.username, account.password)
            run_test()

        with checkout_account(account_type="admin") as admin:
            run_admin_test(admin)

    Args:
        account_type: Filter by account type
        account_id: Request specific account
        timeout: Checkout timeout in seconds

    Yields:
        Account object
    """
    manager = get_account_manager()
    account = manager.checkout(account_type=account_type, account_id=account_id, timeout=timeout)

    try:
        yield account
    finally:
        manager.checkin(account.id)


# Pytest fixture for easy integration
def pytest_account(account_type: str | None = None):
    """
    Create a pytest fixture for account checkout.

    Usage in conftest.py:
        from test_accounts import pytest_account

        @pytest.fixture
        def account():
            return pytest_account()

        @pytest.fixture
        def admin_account():
            return pytest_account(account_type="admin")

    Then in tests:
        def test_login(account):
            login(account.username, account.password)
            assert is_logged_in()
    """
    import pytest

    @pytest.fixture
    def _account():
        with checkout_account(account_type=account_type) as acc:
            yield acc

    return _account


if __name__ == "__main__":
    # Example usage
    print("Test Account Manager - Example Usage\n")

    # Create manager
    manager = AccountManager()

    print(f"Status: {manager.get_status()}\n")

    # Example 1: Context manager (recommended)
    print("Example 1: Context manager")
    with checkout_account() as account:
        print(f"  Checked out: {account.username}")
        print(f"  Type: {account.account_type}")
        time.sleep(1)
    print("  ✓ Auto-checked in\n")

    # Example 2: Specific account type
    print("Example 2: Admin account")
    with checkout_account(account_type="admin") as admin:
        print(f"  Checked out: {admin.username}")
        print(f"  Type: {admin.account_type}")
    print("  ✓ Auto-checked in\n")

    # Example 3: Manual checkout
    print("Example 3: Manual management")
    account = manager.checkout(timeout=60)
    print(f"  Checked out: {account.username}")
    manager.checkin(account.id)
    print("  ✓ Manually checked in\n")

    # Example 4: Parallel checkouts
    print("Example 4: Parallel checkouts")

    def worker(worker_id: int):
        with checkout_account() as acc:
            print(f"  Worker {worker_id}: using {acc.username}")
            time.sleep(0.5)

    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(worker, i) for i in range(3)]
        concurrent.futures.wait(futures)

    print("\n" + "=" * 60)
    print(f"Final status: {manager.get_status()}")
