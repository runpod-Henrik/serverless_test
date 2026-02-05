# Go Test Flaky Example

This example demonstrates flaky tests in Go using the standard `testing` package.

## Files

- `flaky_test.go` - Example flaky tests with various patterns
- `go.mod` - Go module definition

## Flaky Test Patterns

1. **TestRandomFailure** - Fails ~30% based on random value
2. **TestTimingDependent** - Fails when operation takes too long
3. **TestOrderDependency** - Fails based on execution order/state
4. **TestBoundaryCondition** - Fails at edge cases
5. **TestConcurrentAccess** - Simulates race conditions
6. **TestNetworkSimulation** - Simulates network flakiness
7. **TestMapIteration** - Demonstrates non-deterministic map iteration
8. **TestChannelRace** - Demonstrates goroutine timing issues

## Local Testing

### Run tests normally:
```bash
go test -v
```

### Run with specific seed:
```bash
GO_TEST_SEED=12345 go test -v
```

### Run multiple times to see flakiness:
```bash
for i in {1..10}; do
    echo "Run $i:"
    GO_TEST_SEED=$RANDOM go test -v
done
```

### Run with race detector:
```bash
GO_TEST_SEED=12345 go test -v -race
```

## Expected Results

When running 10 times, you should see some tests fail intermittently:
- `TestRandomFailure`: Fails ~30% (3/10 runs)
- `TestTimingDependent`: Fails ~20% (2/10 runs)
- `TestOrderDependency`: Fails ~50% (5/10 runs)
- `TestBoundaryCondition`: Fails ~40% (4/10 runs)
- `TestConcurrentAccess`: Fails ~50% (5/10 runs)
- `TestNetworkSimulation`: Fails ~20% (2/10 runs)
- `TestMapIteration`: Fails ~66% (varies with map iteration)
- `TestChannelRace`: Fails ~50% (5/10 runs)

## Using with Flaky Test Detector

### Input configuration:
```json
{
  "repo": "https://github.com/your-fork/testflake",
  "test_command": "go test ./examples/go/... -v",
  "runs": 100,
  "parallelism": 10,
  "framework": "go"
}
```

The detector will automatically:
1. Detect Go framework from go.mod
2. Run `go mod download` to get dependencies
3. Run tests 100 times with different GO_TEST_SEED values
4. Report flakiness rates for each test

## Sample Output

```
TestRandomFailure: 28/100 failures (28% flaky) - MEDIUM severity
TestTimingDependent: 22/100 failures (22% flaky) - MEDIUM severity
TestOrderDependency: 48/100 failures (48% flaky) - MEDIUM severity
TestBoundaryCondition: 39/100 failures (39% flaky) - MEDIUM severity
TestConcurrentAccess: 51/100 failures (51% flaky) - HIGH severity
TestNetworkSimulation: 19/100 failures (19% flaky) - MEDIUM severity
TestMapIteration: 65/100 failures (65% flaky) - HIGH severity
TestChannelRace: 52/100 failures (52% flaky) - HIGH severity
```

## Go-Specific Considerations

### Random Seed Setup
Go's `init()` function is called before tests run, making it ideal for seed initialization:

```go
func init() {
    if seedStr := os.Getenv("GO_TEST_SEED"); seedStr != "" {
        if seed, err := strconv.ParseInt(seedStr, 10, 64); err == nil {
            rand.Seed(seed)
        }
    }
}
```

### Map Iteration
Go deliberately randomizes map iteration order to prevent code from depending on it. This can cause flaky tests if you rely on iteration order.

### Goroutines and Channels
Tests involving goroutines and channels are prone to timing issues. Use proper synchronization or buffered channels to avoid flakiness.

### Race Detector
Use `-race` flag to detect data races:
```bash
go test -race
```
