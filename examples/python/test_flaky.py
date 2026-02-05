"""
Example flaky test for Python/pytest.

This test demonstrates various flaky patterns that can occur in real applications.
It uses the TEST_SEED environment variable for reproducible randomness.
"""

import os
import random
import time


def setup_test_seed():
    """Setup random seed from environment variable."""
    seed = int(os.environ.get("TEST_SEED", "42"))
    random.seed(seed)
    print(f"Running with seed: {seed}")


def test_random_failure():
    """Test that fails randomly based on seed - simulates race condition."""
    setup_test_seed()

    # Simulate a flaky condition (fails ~30% of the time)
    value = random.random()

    # This will fail when value > 0.7
    assert value <= 0.7, f"Random failure: got {value}, expected <= 0.7"


def test_timing_dependent():
    """Test that depends on timing - simulates timeout or async issues."""
    setup_test_seed()

    # Simulate variable processing time
    delay = random.uniform(0.001, 0.005)
    time.sleep(delay)

    # Fails if processing takes "too long" (> 0.004s)
    assert delay < 0.004, f"Operation too slow: {delay}s"


def test_order_dependency():
    """Test that depends on execution order - simulates shared state issues."""
    setup_test_seed()

    # Simulate checking a cache/queue that may or may not have items
    items = []
    if random.random() > 0.5:
        items.append("existing_item")

    # Fails when cache is unexpectedly populated
    assert len(items) == 0, f"Expected empty cache, found {len(items)} items"


def test_boundary_condition():
    """Test at boundary conditions - simulates off-by-one errors."""
    setup_test_seed()

    # Simulate calculating a threshold
    calculated_value = random.randint(98, 102)
    threshold = 100

    # Fails when value exceeds threshold
    assert calculated_value <= threshold, f"Value {calculated_value} exceeds threshold {threshold}"


def test_concurrent_access():
    """Test simulating concurrent access patterns."""
    setup_test_seed()

    # Simulate checking if resource is locked
    is_locked = random.choice([True, False])

    # Fails when resource is locked (race condition)
    assert not is_locked, "Resource is locked by another process"


def test_network_simulation():
    """Test simulating network flakiness."""
    setup_test_seed()

    # Simulate network response
    success_rate = random.random()

    # Fails 20% of the time (simulating network issues)
    assert success_rate > 0.2, f"Network request failed: {success_rate}"


if __name__ == "__main__":
    # Run with pytest: pytest test_flaky.py -v
    # Or with seed: TEST_SEED=12345 pytest test_flaky.py -v
    pass
