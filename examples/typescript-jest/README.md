# TypeScript/Jest Flaky Test Example

This example demonstrates flaky tests in TypeScript using Jest.

## Files

- `flaky.test.ts` - Example flaky tests with various patterns
- `package.json` - Node.js dependencies
- `jest.config.js` - Jest configuration
- `jest.setup.js` - Seed setup for reproducible randomness
- `tsconfig.json` - TypeScript configuration

## Flaky Test Patterns

1. **Random Failure** - Fails ~30% based on random value
2. **Timing Dependent** - Fails when async operation takes too long
3. **Order Dependency** - Fails based on execution order/state
4. **Boundary Condition** - Fails at edge cases
5. **Concurrent Access** - Simulates race conditions
6. **Network Simulation** - Simulates network flakiness
7. **Async Operation** - Demonstrates async timing issues
8. **Promise Race** - Demonstrates promise race conditions
9. **Array Randomization** - Demonstrates random array operations
10. **Mock Timing** - Demonstrates mock timing issues

## Local Testing

### Install dependencies:
```bash
npm install
```

### Run tests normally:
```bash
npm test
```

### Run with specific seed:
```bash
JEST_SEED=12345 npm test
```

### Run with verbose output:
```bash
npm run test:verbose
```

### Run multiple times to see flakiness:
```bash
for i in {1..10}; do
    echo "Run $i:"
    JEST_SEED=$RANDOM npm test
done
```

## Expected Results

When running 10 times, you should see some tests fail intermittently:
- Random Failure: Fails ~30% (3/10 runs)
- Timing Dependent: Fails ~20% (2/10 runs)
- Order Dependency: Fails ~50% (5/10 runs)
- Boundary Condition: Fails ~40% (4/10 runs)
- Concurrent Access: Fails ~50% (5/10 runs)
- Network Simulation: Fails ~20% (2/10 runs)
- Async Operation: Fails ~30% (3/10 runs)
- Promise Race: Fails ~50% (5/10 runs)
- Array Randomization: Fails ~80% (8/10 runs)
- Mock Timing: Fails ~50% (5/10 runs)

## Using with Flaky Test Detector

### Input configuration:
```json
{
  "repo": "https://github.com/your-fork/serverless_test",
  "test_command": "cd examples/typescript-jest && npm test",
  "runs": 100,
  "parallelism": 10,
  "framework": "typescript-jest"
}
```

The detector will automatically:
1. Detect Jest framework from package.json
2. Run `npm install` to get dependencies
3. Run tests 100 times with different JEST_SEED values
4. Report flakiness rates for each test

## Sample Output

```
Random Failure: 32/100 failures (32% flaky) - MEDIUM severity
Timing Dependent: 19/100 failures (19% flaky) - MEDIUM severity
Order Dependency: 51/100 failures (51% flaky) - HIGH severity
Boundary Condition: 38/100 failures (38% flaky) - MEDIUM severity
Concurrent Access: 48/100 failures (48% flaky) - MEDIUM severity
Network Simulation: 21/100 failures (21% flaky) - MEDIUM severity
Async Operation: 29/100 failures (29% flaky) - MEDIUM severity
Promise Race: 49/100 failures (49% flaky) - MEDIUM severity
Array Randomization: 83/100 failures (83% flaky) - HIGH severity
Mock Timing: 52/100 failures (52% flaky) - HIGH severity
```

## Seed Configuration

The `jest.setup.js` file configures seeded randomness:

```javascript
const seedrandom = require('seedrandom');
const seed = parseInt(process.env.JEST_SEED || '42', 10);
Math.random = seedrandom(seed.toString());
```

This replaces JavaScript's `Math.random()` with a seeded version, making all random operations reproducible.

## TypeScript/Jest Specific Considerations

### Async/Await
Use `async`/`await` for asynchronous tests:
```typescript
test('async test', async () => {
  const result = await asyncOperation();
  expect(result).toBe('expected');
});
```

### Promise Matchers
Jest provides special matchers for promises:
```typescript
await expect(promise).resolves.toBe('value');
await expect(promise).rejects.toThrow('error');
```

### Mock Functions
Jest's mock functions can introduce flakiness:
```typescript
const mock = jest.fn();
// May not be called due to random conditions
expect(mock).toHaveBeenCalled(); // Flaky!
```

### Timers
Use Jest's fake timers for predictable timing:
```typescript
jest.useFakeTimers();
setTimeout(callback, 1000);
jest.runAllTimers();
expect(callback).toHaveBeenCalled();
```
