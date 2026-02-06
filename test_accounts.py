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

    # Specific environment
    with checkout_account(environment="prod") as account:
        run_prod_test(account)

    # Manual management
    manager = AccountManager()
    account = manager.checkout(timeout=300)
    try:
        run_test(account)
    finally:
        manager.checkin(account.id)
"""

import json
import os
import threading
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any


class Environment(StrEnum):
    """Test environment types."""

    LOCAL = "local"
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"
    CI = "ci"


def get_current_environment() -> str:
    """
    Get current environment from environment variable.

    Checks TEST_ENVIRONMENT or ENVIRONMENT variable.
    Defaults to "local" if not set.

    Returns:
        Environment name as string
    """
    return os.environ.get("TEST_ENVIRONMENT", os.environ.get("ENVIRONMENT", "local"))


@dataclass
class Account:
    """Test account with credentials."""

    id: str
    username: str
    password: str
    email: str
    account_type: str = "standard"
    environment: str = "local"
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
    """
    File-based storage for test accounts.

    Supports environment-specific account files:
    - test_accounts.local.json
    - test_accounts.dev.json
    - test_accounts.prod.json
    """

    def __init__(
        self,
        accounts_file: str | None = None,
        environment: str | None = None,
        auto_env: bool = True,
    ):
        """
        Initialize file storage.

        Args:
            accounts_file: Specific file path (overrides environment)
            environment: Environment name (local, dev, prod, etc.)
            auto_env: Automatically use environment-specific files
        """
        self.environment = environment or get_current_environment()
        self.auto_env = auto_env

        if accounts_file:
            # Use specific file
            self.accounts_file = Path(accounts_file)
        elif auto_env:
            # Use environment-specific file
            self.accounts_file = Path(f"test_accounts.{self.environment}.json")
        else:
            # Use default file
            self.accounts_file = Path("test_accounts.json")

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
        """Create default test accounts for current environment."""
        env = self.environment

        # Customize credentials based on environment
        if env == "prod":
            # Prod accounts should use real/1Password credentials
            # These are just placeholders
            password_suffix = "_Prod2026!"
            email_domain = "prod.example.com"
        elif env == "staging":
            password_suffix = "_Stage2026!"
            email_domain = "staging.example.com"
        elif env == "dev":
            password_suffix = "_Dev2026!"
            email_domain = "dev.example.com"
        else:  # local, ci, etc.
            password_suffix = "_Test123!"
            email_domain = "example.com"

        return [
            Account(
                id=f"test-user-1-{env}",
                username=f"testuser1-{env}",
                password=f"TestPass{password_suffix}",
                email=f"testuser1@{email_domain}",
                account_type="standard",
                environment=env,
            ),
            Account(
                id=f"test-user-2-{env}",
                username=f"testuser2-{env}",
                password=f"TestPass{password_suffix}",
                email=f"testuser2@{email_domain}",
                account_type="standard",
                environment=env,
            ),
            Account(
                id=f"test-user-3-{env}",
                username=f"testuser3-{env}",
                password=f"TestPass{password_suffix}",
                email=f"testuser3@{email_domain}",
                account_type="standard",
                environment=env,
            ),
            Account(
                id=f"test-admin-1-{env}",
                username=f"testadmin1-{env}",
                password=f"AdminPass{password_suffix}",
                email=f"testadmin1@{email_domain}",
                account_type="admin",
                environment=env,
            ),
            Account(
                id=f"test-premium-1-{env}",
                username=f"testpremium1-{env}",
                password=f"PremiumPass{password_suffix}",
                email=f"testpremium1@{email_domain}",
                account_type="premium",
                environment=env,
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
    - Environment isolation
    """

    def __init__(
        self,
        storage: AccountStorage | None = None,
        environment: str | None = None,
        default_timeout: int = 300,
        cleanup_interval: int = 60,
    ):
        """
        Initialize account manager.

        Args:
            storage: Storage backend (defaults to FileStorage with environment)
            environment: Environment name (auto-detected if None)
            default_timeout: Default checkout timeout in seconds
            cleanup_interval: How often to check for expired checkouts (seconds)
        """
        self.environment = environment or get_current_environment()
        self.storage = storage or FileStorage(environment=self.environment)
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
        environment: str | None = None,
        timeout: int | None = None,
        requester: str | None = None,
    ) -> Account:
        """
        Check out an available account.

        Args:
            account_type: Filter by account type (e.g., "admin", "premium")
            account_id: Request specific account by ID
            environment: Filter by environment (defaults to manager's environment)
            timeout: Checkout timeout in seconds
            requester: Identifier for who's checking out (for debugging)

        Returns:
            Account object

        Raises:
            RuntimeError: If no accounts available
        """
        timeout = timeout or self.default_timeout
        requester = requester or threading.current_thread().name
        environment = environment or self.environment

        with self._lock:
            # Find available account
            available = self._find_available_account(account_type, account_id, environment)

            if not available:
                raise RuntimeError(
                    f"No available accounts "
                    f"(type={account_type}, id={account_id}, env={environment}). "
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
        self, account_type: str | None, account_id: str | None, environment: str | None
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

            # Filter by environment
            if environment and account.environment != environment:
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
    environment: str | None = None,
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

        with checkout_account(environment="prod") as prod_account:
            run_prod_test(prod_account)

    Args:
        account_type: Filter by account type
        account_id: Request specific account
        environment: Filter by environment (defaults to current environment)
        timeout: Checkout timeout in seconds

    Yields:
        Account object
    """
    manager = get_account_manager()
    account = manager.checkout(
        account_type=account_type,
        account_id=account_id,
        environment=environment,
        timeout=timeout,
    )

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
