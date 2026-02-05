# Python Example Test Results

## Flakiness Analysis (20 runs with different seeds)

| Test Name | Passes | Failures | Flaky % | Severity |
|-----------|--------|----------|---------|----------|
| test_concurrent_access | 11 | 9 | 45.0% | 🟡 MEDIUM |
| test_boundary_condition | 12 | 8 | 40.0% | 🟡 MEDIUM |
| test_network_simulation | 14 | 6 | 30.0% | 🟢 LOW |
| test_order_dependency | 15 | 5 | 25.0% | 🟢 LOW |
| test_random_failure | 18 | 2 | 10.0% | ✅ STABLE |
| test_timing_dependent | 18 | 2 | 10.0% | ✅ STABLE |

## Summary

- **Total Tests**: 6
- **Tests with Flaky Behavior**: 6/6 (100%)
- **Average Flakiness**: 26.7%
- **Perfect Runs**: 3/20 (15%) - All tests passed for seeds 7000, 9000, 18000

## Key Findings

### Most Flaky Tests
1. **Concurrent Access (45%)** - Simulated race condition with resource locking
2. **Boundary Condition (40%)** - Edge case sensitivity with threshold checking
3. **Network Simulation (30%)** - Random network failure simulation
4. **Order Dependency (25%)** - Test execution order dependencies with shared state

### Most Stable Tests
1. **Random Failure (10%)** - Pure random failure based on threshold
2. **Timing Dependent (10%)** - Operation timeout threshold
3. **Network Simulation (30%)** - Moderate simulated network issues
4. **Order Dependency (25%)** - State-based execution order issues

### Python/Pytest-Specific Observations

**Balanced Flakiness:**
The Python example shows the most balanced flakiness profile (26.7% average) compared to other language examples, with no tests showing extreme flakiness (>50%). This demonstrates realistic, moderate flaky patterns common in production Python codebases.

**Concurrent Access Pattern:**
The concurrent access test (45% flakiness) uses Python's threading concepts to simulate race conditions - a common source of flakiness in Python applications dealing with shared resources.

**Boundary Conditions:**
The boundary condition test (40% flakiness) demonstrates Python's precise numeric handling where small variations in seeded random values can cause threshold crossings.

**Perfect Test Runs:**
Uniquely among all examples, the Python tests had 3 complete successful runs (15%) where all tests passed. This shows the tests are well-calibrated and not overly aggressive, making them ideal for demonstrating realistic flakiness detection.

**Module Organization:**
The example uses pytest's fixture system and demonstrates flaky patterns in a clean, Pythonic way with proper test organization using conftest.py for shared fixtures.

## Reproducibility Test

Running with the same seed (12345) three times produced **identical results**:

```
Seed: 12345

Run 1: 5 passing, 1 failing
Run 2: 5 passing, 1 failing
Run 3: 5 passing, 1 failing

Consistently passing tests:
- test_random_failure
- test_timing_dependent
- test_order_dependency
- test_concurrent_access
- test_network_simulation

Consistently failing tests:
- test_boundary_condition
```

✅ **Reproducibility confirmed**: Same seed produces identical results every time.

## Usage with Flaky Test Detector

To use these tests with the flaky test detector:

```json
{
  "repo": "https://github.com/your-fork/testflake",
  "test_command": "pytest examples/python/test_flaky.py -v",
  "runs": 100,
  "parallelism": 10,
  "framework": "python"
}
```

Expected output after 100 runs:
- test_concurrent_access: ~45% failures (MEDIUM)
- test_boundary_condition: ~40% failures (MEDIUM)
- test_network_simulation: ~30% failures (LOW)
- test_order_dependency: ~25% failures (LOW)
- test_random_failure: ~10% failures (STABLE)
- test_timing_dependent: ~10% failures (STABLE)

## Conclusion

✅ Python example is working correctly
✅ All tests demonstrate realistic flaky patterns
✅ Tests are reproducible with same seed via TEST_SEED
✅ Python-specific patterns (threading, fixtures, pytest) are well represented
✅ Most balanced flakiness profile (26.7%) among all examples
✅ 15% of runs had zero failures, demonstrating realistic calibration
✅ Ready to use with flaky test detector

**Note**: The Python example demonstrates the most realistic and balanced flaky test patterns, making it an excellent reference implementation. The moderate flakiness rates (10-45%) and occasional perfect runs reflect real-world production test suites better than highly aggressive patterns.

---

**Test Date**: 2026-02-04
**Python Version**: python3.13
**Pytest Version**: ^9.0.2
**Test Runs**: 20 iterations with different seeds
