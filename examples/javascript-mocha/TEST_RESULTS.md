# JavaScript/Mocha Example Test Results

## Flakiness Analysis (20 runs with different seeds)

| Test Name | Passes | Failures | Flaky % | Severity |
|-----------|--------|----------|---------|----------|
| Array Mutation - should fail on random array mutation | 4 | 16 | 80.0% | 🔴 HIGH |
| Concurrent Access - should fail on simulated race condition | 6 | 14 | 70.0% | 🔴 HIGH |
| Object Property - should fail on random object property | 9 | 11 | 55.0% | 🔴 HIGH |
| Promise Rejection - should fail on random promise rejection | 10 | 10 | 50.0% | 🟡 MEDIUM |
| Async/Await Pattern - should fail on async timing issues | 11 | 9 | 45.0% | 🟡 MEDIUM |
| Callback Timing - should fail on callback timing issues | 12 | 8 | 40.0% | 🟡 MEDIUM |
| Retry Logic - should fail on retry logic | 12 | 8 | 40.0% | 🟡 MEDIUM |
| Random Failure - should fail randomly ~30% of the time | 13 | 7 | 35.0% | 🟡 MEDIUM |
| Timing Dependent - should fail when operation takes too long | 13 | 7 | 35.0% | 🟡 MEDIUM |
| Boundary Condition - should fail at edge cases | 13 | 7 | 35.0% | 🟡 MEDIUM |
| Order Dependency - should fail based on execution order | 15 | 5 | 25.0% | 🟢 LOW |
| Network Simulation - should fail on simulated network issue | 17 | 3 | 15.0% | 🟢 LOW |

## Summary

- **Total Tests**: 12
- **Tests with Flaky Behavior**: 12/12 (100%)
- **Average Flakiness**: 43.8%

## Key Findings

### Most Flaky Tests
1. **Array Mutation (80%)** - Random array operations with seeded randomness
2. **Concurrent Access (70%)** - Asynchronous race condition simulation
3. **Object Property (55%)** - Random object property manipulation
4. **Promise Rejection (50%)** - Random promise rejection patterns

### Most Stable Tests
1. **Network Simulation (15%)** - Low simulated network failure rate
2. **Order Dependency (25%)** - Execution order dependencies
3. **Random Failure (35%)** - Designed to fail ~35% of time
4. **Timing Dependent (35%)** - Operation timeout threshold
5. **Boundary Condition (35%)** - Edge case sensitivity

### JavaScript/Mocha-Specific Observations

**Array Mutation Flakiness:**
The array mutation test shows 80% flakiness, the highest in this example. This demonstrates how JavaScript's mutable data structures combined with seeded randomness create highly unpredictable test behavior - a common source of flakiness in Node.js testing.

**Callback and Promise Patterns:**
Multiple tests show callback and promise-related flakiness (`Callback Timing` 40%, `Promise Rejection` 50%, `Async/Await` 45%). These represent realistic async patterns in Node.js where timing and error handling can cause non-deterministic test results.

**Object Property Manipulation:**
The object property test (55% flakiness) demonstrates how dynamic property addition/removal in JavaScript objects can create flaky tests, especially when combined with randomness.

**Concurrent Access:**
With 70% flakiness, the concurrent access test shows how Mocha's async handling combined with setTimeout creates realistic race conditions common in server-side JavaScript applications.

## Reproducibility Test

Running with the same seed (12345) three times produced **identical results**:

```
Seed: 12345

Run 1: 4 passing, 8 failing
Run 2: 4 passing, 8 failing
Run 3: 4 passing, 8 failing

Consistently passing tests:
- Timing Dependent
- Boundary Condition
- Network Simulation
- Retry Logic

Consistently failing tests:
- Random Failure
- Order Dependency
- Concurrent Access
- Promise Rejection
- Async/Await Pattern
- Callback Timing
- Array Mutation
- Object Property
```

✅ **Reproducibility confirmed**: Same seed produces identical results every time.

## Usage with Flaky Test Detector

To use these tests with the flaky test detector:

```json
{
  "repo": "https://github.com/your-fork/testflake",
  "test_command": "npm test -- examples/javascript-mocha",
  "runs": 100,
  "parallelism": 10,
  "framework": "javascript-mocha"
}
```

Expected output after 100 runs:
- Array Mutation: ~80% failures (HIGH)
- Concurrent Access: ~70% failures (HIGH)
- Object Property: ~55% failures (HIGH)
- Promise Rejection: ~50% failures (MEDIUM)
- Async/Await Pattern: ~45% failures (MEDIUM)
- Callback Timing: ~40% failures (MEDIUM)
- Retry Logic: ~40% failures (MEDIUM)
- Random Failure: ~35% failures (MEDIUM)
- Timing Dependent: ~35% failures (MEDIUM)
- Boundary Condition: ~35% failures (MEDIUM)
- Order Dependency: ~25% failures (LOW)
- Network Simulation: ~15% failures (LOW)

## Conclusion

✅ JavaScript/Mocha example is working correctly
✅ All tests demonstrate realistic flaky patterns
✅ Tests are reproducible with same seed via MOCHA_SEED
✅ JavaScript/Node.js-specific patterns (callbacks, promises, array mutations, object properties) are well represented
✅ Ready to use with flaky test detector

**Note**: This example includes the most comprehensive set of flaky patterns (12 tests) compared to other language examples, covering JavaScript-specific async patterns, mutable data structures, and callback-based timing issues common in Node.js applications.

---

**Test Date**: 2026-02-04
**Node Version**: v20.x
**Mocha Version**: ^10.8.2
**Test Runs**: 20 iterations with different seeds
