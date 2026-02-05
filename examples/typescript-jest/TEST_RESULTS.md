# TypeScript/Jest Example Test Results

## Flakiness Analysis (20 runs with different seeds)

| Test Name | Passes | Failures | Flaky % | Severity |
|-----------|--------|----------|---------|----------|
| should fail on random array operations | 1 | 19 | 95.0% | 🔴 HIGH |
| should fail on simulated race condition | 5 | 15 | 75.0% | 🔴 HIGH |
| should fail at edge cases | 10 | 10 | 50.0% | 🟡 MEDIUM |
| should fail on mock timing issues | 10 | 10 | 50.0% | 🟡 MEDIUM |
| should fail based on execution order | 11 | 9 | 45.0% | 🟡 MEDIUM |
| should fail when operation takes too long | 13 | 7 | 35.0% | 🟡 MEDIUM |
| should fail on promise race condition | 14 | 6 | 30.0% | 🟢 LOW |
| should fail randomly ~30% of the time | 15 | 5 | 25.0% | 🟢 LOW |
| should fail on async timing issues | 16 | 4 | 20.0% | 🟢 LOW |
| should fail on simulated network issue | 17 | 3 | 15.0% | 🟢 LOW |

## Summary

- **Total Tests**: 10
- **Tests with Flaky Behavior**: 10/10 (100%)
- **Average Flakiness**: 44.0%

## Key Findings

### Most Flaky Tests
1. **Random Array Operations (95%)** - Array operation ordering with seeded randomness
2. **Simulated Race Condition (75%)** - Concurrent async operation timing
3. **Edge Cases (50%)** - Boundary condition sensitivity
4. **Mock Timing Issues (50%)** - Mock function timing dependencies

### Most Stable Tests
1. **Simulated Network Issue (15%)** - Low failure probability
2. **Async Timing Issues (20%)** - Occasional timing threshold failures
3. **Random Failure (25%)** - Designed to fail ~30% of time
4. **Promise Race Condition (30%)** - Promise.race timing variability

### TypeScript/Jest-Specific Observations

**Array Operations and Randomness:**
The array operations test shows 95% flakiness, demonstrating how seeded randomness in array operations can create highly deterministic but seed-dependent behavior. This is particularly common in TypeScript/Jest tests that use Math.random() for data generation.

**Async/Promise Timing:**
Multiple tests (`TestRaceCondition`, `TestPromiseRace`, `TestAsyncTiming`) show timing-dependent flakiness (75%, 30%, 20%). This represents real-world async issues common in JavaScript/TypeScript applications where promise resolution order affects test outcomes.

**Mock Function Timing:**
The mock timing test (50% flakiness) demonstrates how Jest mocks combined with setTimeout can create unpredictable test behavior, a common source of flakiness in frontend testing.

## Reproducibility Test

Running with the same seed (12345) three times produced identical results:

```
Seed: 12345

Run 1: 1 test suite failed
Run 2: 1 test suite failed
Run 3: 1 test suite failed

Failing tests (consistent):
- "should fail randomly ~30% of the time"

All tests showed consistent pass/fail patterns across runs.
```

✅ **Reproducibility confirmed**: Same seed produces identical results every time.

## Usage with Flaky Test Detector

To use these tests with the flaky test detector:

```json
{
  "repo": "https://github.com/your-fork/testflake",
  "test_command": "npm test -- examples/typescript-jest",
  "runs": 100,
  "parallelism": 10,
  "framework": "typescript-jest"
}
```

Expected output after 100 runs:
- Random Array Operations: ~95% failures (HIGH)
- Simulated Race Condition: ~75% failures (HIGH)
- Edge Cases: ~50% failures (MEDIUM)
- Mock Timing Issues: ~50% failures (MEDIUM)
- Execution Order: ~45% failures (MEDIUM)
- Operation Timeout: ~35% failures (MEDIUM)
- Promise Race Condition: ~30% failures (MEDIUM)
- Random Failure: ~25% failures (MEDIUM)
- Async Timing Issues: ~20% failures (LOW)
- Network Simulation: ~15% failures (LOW)

## Conclusion

✅ TypeScript/Jest example is working correctly
✅ All tests demonstrate realistic flaky patterns
✅ Tests are reproducible with same seed via JEST_SEED
✅ JavaScript/TypeScript-specific patterns (async, promises, mocks) are well represented
✅ Ready to use with flaky test detector

---

**Test Date**: 2026-02-04
**Node Version**: v20.x
**Jest Version**: ^29.7.0
**Test Runs**: 20 iterations with different seeds
