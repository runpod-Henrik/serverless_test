import os
import random
import time


def test_order_processing_is_eventually_consistent():
    """
    This test simulates a classic real-world flake:
    - timing sensitivity
    - randomness
    - implicit assumptions about consistency
    """
    # Seed can be controlled externally (RunPod sets this)
    seed = os.getenv("TEST_SEED")
    if seed:
        random.seed(int(seed))
    # Simulate async / eventual behavior
    processing_time = random.uniform(0.0, 0.3)
    time.sleep(processing_time)
    # Simulate race condition / timing window
    # 15–25% failure rate depending on timing + seed
    success_threshold = 0.18
    assert (
        processing_time < success_threshold
    ), f"Order not processed in time (took {processing_time:.3f}s)"
