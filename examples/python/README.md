# Python/pytest Flaky Test Example

This example demonstrates flaky tests in Python using pytest.

## Files

- `test_flaky.py` - Example flaky tests with various patterns
- `requirements.txt` - Python dependencies

## Flaky Test Patterns

1. **Random Failure** - Fails ~30% based on random value
2. **Timing Dependent** - Fails when operation takes too long
3. **Order Dependency** - Fails based on execution order/state
4. **Boundary Condition** - Fails at edge cases
5. **Concurrent Access** - Simulates race conditions
6. **Network Simulation** - Simulates network flakiness

## Local Testing

### Install dependencies:
```bash
pip install -r requirements.txt
```

### Run tests normally:
```bash
pytest test_flaky.py -v
```

### Run with specific seed:
```bash
TEST_SEED=12345 pytest test_flaky.py -v
```

### Run multiple times to see flakiness:
```bash
for i in {1..10}; do
    echo "Run $i:"
    TEST_SEED=$RANDOM pytest test_flaky.py -v
done
```

## Expected Results

When running 10 times, you should see some tests fail intermittently:
- `test_random_failure`: Fails ~30% (3/10 runs)
- `test_timing_dependent`: Fails ~20% (2/10 runs)
- `test_order_dependency`: Fails ~50% (5/10 runs)
- `test_boundary_condition`: Fails ~40% (4/10 runs)
- `test_concurrent_access`: Fails ~50% (5/10 runs)
- `test_network_simulation`: Fails ~20% (2/10 runs)

## Using with Flaky Test Detector

### Input configuration:
```json
{
  "repo": "https://github.com/your-fork/serverless_test",
  "test_command": "pytest examples/python/test_flaky.py -v",
  "runs": 100,
  "parallelism": 10
}
```

The detector will automatically:
1. Detect Python/pytest framework
2. Install dependencies from requirements.txt
3. Run tests 100 times with different TEST_SEED values
4. Report flakiness rates for each test

## Sample Output

```
test_random_failure: 32/100 failures (32% flaky) - MEDIUM severity
test_timing_dependent: 18/100 failures (18% flaky) - MEDIUM severity
test_order_dependency: 51/100 failures (51% flaky) - HIGH severity
test_boundary_condition: 42/100 failures (42% flaky) - MEDIUM severity
test_concurrent_access: 49/100 failures (49% flaky) - MEDIUM severity
test_network_simulation: 21/100 failures (21% flaky) - MEDIUM severity
```
